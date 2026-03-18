"""
matching_automatico.py
Compara nombres de productos Mercadona vs DIA y crea matches automáticos.
Usa similitud de texto (rapidfuzz) para encontrar productos equivalentes.

Instalar: pip install rapidfuzz requests
"""

import json
import urllib.request
import urllib.error
import csv
import os
from rapidfuzz import fuzz, process

# ── CONFIGURACIÓN ─────────────────────────────────────────────
SUPABASE_URL = "https://scpuriaofisssalsbzqv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcHVyaWFvZmlzc3NhbHNienF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjgwNDksImV4cCI6MjA4NTkwNDA0OX0.oMYR_aV0SgMplBURwSESe8kLCWTl4QfQyOXsDfmBRfo"

UMBRAL_AUTO   = 88   # % similitud → match automático seguro
UMBRAL_MANUAL = 70   # % similitud → guardar para revisión manual
# ─────────────────────────────────────────────────────────────

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
}


def supabase_get(tabla, filtro=""):
    url = f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}&limit=10000"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def supabase_patch(tabla, filtro, datos):
    url = f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}"
    data = json.dumps(datos).encode()
    req  = urllib.request.Request(url, data=data, headers={**HEADERS, "Prefer": "return=minimal"}, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        print(f"  ❌ PATCH error {e.code}: {e.read().decode()[:100]}")
        return e.code


def normalizar(nombre):
    """Normaliza nombre para comparar: minúsculas, sin tildes, sin plurales simples"""
    import unicodedata
    n = nombre.lower().strip()
    n = ''.join(c for c in unicodedata.normalize('NFD', n) if unicodedata.category(c) != 'Mn')
    # Quitar marca/peso al final para comparar solo el nombre genérico
    # Ej: "Leche entera Dia Láctea pack 6 x 1 L" → "leche entera"
    # Eliminar palabras de marca comunes
    marcas = ['hacendado', 'dia lactea', 'dia', 'carrefour', 'aldi', 'lidl',
              'pack', 'botella', 'brik', 'lata', 'bote', 'bolsa', 'caja',
              'x 1 l', 'x 2 l', '1 l', '2 l', '1l', '500 ml', '250 ml',
              '200 g', '500 g', '1 kg', '250 g', '100 g', 'kg', ' ml', ' g', ' l',
              'sin gluten', 'bio', 'ecologico', 'light', '0%']
    for m in marcas:
        n = n.replace(m, '')
    # Limpiar espacios dobles
    while '  ' in n:
        n = n.replace('  ', ' ')
    return n.strip()


def cargar_productos():
    print("📥 Cargando productos de Supabase...")

    # Productos Mercadona (tienen id_producto_maestro real P-XXXX)
    mercadona = supabase_get(
        "productos_supermercados",
        "supermercado=eq.Mercadona&select=id,nombre_comercial,id_producto_maestro,precio"
    )
    print(f"  Mercadona: {len(mercadona)} productos")

    # Productos DIA
    dia = supabase_get(
        "productos_supermercados",
        "supermercado=eq.DIA&select=id,nombre_comercial,id_producto_maestro,id_externo,precio"
    )
    print(f"  DIA: {len(dia)} productos")

    # Productos maestros (para actualizar categorías luego)
    maestros = supabase_get(
        "productos_maestros",
        "select=id_producto,nombre,categoria"
    )
    print(f"  Maestros: {len(maestros)} productos")

    return mercadona, dia, maestros


def hacer_matching(mercadona, dia):
    print("\n🔍 Calculando similitudes...")

    # Crear índice de Mercadona: nombre_normalizado → datos
    idx_mercadona = {}
    for p in mercadona:
        if not p.get('nombre_comercial') or not p.get('id_producto_maestro'):
            continue
        norm = normalizar(p['nombre_comercial'])
        if norm:
            idx_mercadona[norm] = p

    nombres_mercadona = list(idx_mercadona.keys())
    print(f"  Índice Mercadona: {len(nombres_mercadona)} nombres únicos")

    matches_auto   = []  # Matches seguros → aplicar directo
    matches_manual = []  # Matches dudosos → CSV para revisar
    sin_match      = []  # Sin equivalente

    for i, prod_dia in enumerate(dia):
        if not prod_dia.get('nombre_comercial'):
            continue

        nombre_dia  = prod_dia['nombre_comercial']
        norm_dia    = normalizar(nombre_dia)

        if not norm_dia:
            continue

        # Buscar mejor coincidencia en Mercadona
        resultado = process.extractOne(
            norm_dia,
            nombres_mercadona,
            scorer=fuzz.token_sort_ratio
        )

        if resultado:
            mejor_nombre, score, _ = resultado
            prod_mercadona = idx_mercadona[mejor_nombre]

            if score >= UMBRAL_AUTO:
                matches_auto.append({
                    'id_dia':            prod_dia['id'],
                    'id_externo_dia':    prod_dia.get('id_externo', ''),
                    'nombre_dia':        nombre_dia,
                    'nombre_mercadona':  prod_mercadona['nombre_comercial'],
                    'id_maestro':        prod_mercadona['id_producto_maestro'],
                    'score':             score,
                })
            elif score >= UMBRAL_MANUAL:
                matches_manual.append({
                    'id_dia':            prod_dia['id'],
                    'id_externo_dia':    prod_dia.get('id_externo', ''),
                    'nombre_dia':        nombre_dia,
                    'nombre_mercadona':  prod_mercadona['nombre_comercial'],
                    'id_maestro':        prod_mercadona['id_producto_maestro'],
                    'score':             score,
                })
            else:
                sin_match.append(prod_dia)
        else:
            sin_match.append(prod_dia)

        if (i + 1) % 500 == 0:
            print(f"  Procesados {i+1}/{len(dia)}...")

    print(f"\n📊 Resultados matching:")
    print(f"  ✅ Matches automáticos (≥{UMBRAL_AUTO}%): {len(matches_auto)}")
    print(f"  ⚠️  Para revisión ({UMBRAL_MANUAL}-{UMBRAL_AUTO}%):  {len(matches_manual)}")
    print(f"  ❌ Sin match (<{UMBRAL_MANUAL}%):          {len(sin_match)}")

    return matches_auto, matches_manual, sin_match


def aplicar_matches(matches_auto):
    """Actualiza id_producto_maestro en productos_supermercados para los matches automáticos"""
    print(f"\n🔄 Aplicando {len(matches_auto)} matches automáticos...")

    ok = 0
    for m in matches_auto:
        status = supabase_patch(
            "productos_supermercados",
            f"id=eq.{m['id_dia']}",
            {"id_producto_maestro": m['id_maestro']}
        )
        if status in (200, 204):
            ok += 1
        if ok % 100 == 0 and ok > 0:
            print(f"  Actualizados {ok}/{len(matches_auto)}...")

    print(f"  ✅ {ok} productos DIA vinculados a productos maestros de Mercadona")
    return ok


def guardar_csvs(matches_manual, sin_match):
    """Guarda los matches dudosos y sin match para revisión manual"""
    
    # CSV para revisión manual
    if matches_manual:
        f_manual = "matches_revisar.csv"
        with open(f_manual, 'w', newline='', encoding='utf-8') as f:
            campos = ['score', 'nombre_dia', 'nombre_mercadona', 'id_maestro', 'id_dia']
            w = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore')
            w.writeheader()
            w.writerows(sorted(matches_manual, key=lambda x: -x['score']))
        print(f"\n📄 Matches para revisar: {f_manual} ({len(matches_manual)} filas)")
        print(f"   → Abre el CSV, comprueba los que son correctos y ejecuta aplicar_manual.py")

    # CSV sin match (productos DIA sin equivalente en Mercadona)
    if sin_match:
        f_sin = "productos_dia_sin_match.csv"
        with open(f_sin, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=['id', 'nombre_comercial', 'id_externo', 'precio'])
            w.writeheader()
            for p in sin_match:
                w.writerow({k: p.get(k, '') for k in ['id', 'nombre_comercial', 'id_externo', 'precio']})
        print(f"📄 Sin match: {f_sin} ({len(sin_match)} productos solo en DIA)")


def main():
    print("=" * 55)
    print("  🔗 MATCHING AUTOMÁTICO Mercadona ↔ DIA")
    print("=" * 55)

    if "PEGA_AQUI" in SUPABASE_KEY:
        print("❌ Falta la SUPABASE_KEY — édita el script")
        input("ENTER para salir...")
        return

    mercadona, dia, maestros = cargar_productos()
    matches_auto, matches_manual, sin_match = hacer_matching(mercadona, dia)

    if not matches_auto:
        print("\n⚠️  No se encontraron matches automáticos")
        guardar_csvs(matches_manual, sin_match)
        return

    print(f"\n¿Aplicar los {len(matches_auto)} matches automáticos a Supabase? (s/n): ", end="")
    resp = input().strip().lower()

    if resp == 's':
        aplicar_matches(matches_auto)
    else:
        # Guardar también los automáticos para revisión
        matches_manual = matches_auto + matches_manual
        print("  → Guardados en CSV para revisión manual")

    guardar_csvs(matches_manual, sin_match)

    print("\n✅ Matching completado.")
    print("   Siguiente paso: reinicia la app y verás los precios comparados.")
    input("\nENTER para salir...")


if __name__ == "__main__":
    main()
