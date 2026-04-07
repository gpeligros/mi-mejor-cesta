"""
match_ahorramas.py  —  Mi Mejor Cesta
=======================================
Vincula precios_ahorramas con productos_catalogo usando fuzzy matching.

Estrategia:
  - Score >= 85 → match automático
  - Score 60-84 → dudoso (se guarda en CSV para revisión)
  - Score < 60  → sin match

Uso:
  python scrapers/match_ahorramas.py --dry-run   # muestra stats, no guarda
  python scrapers/match_ahorramas.py             # aplica matches automáticos
  python scrapers/match_ahorramas.py --umbral 80 # cambia umbral automático
"""

import os, re, csv, json, argparse, unicodedata
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
except ImportError:
    pass

from rapidfuzz import fuzz, process
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY no encontrada en .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

UMBRAL_AUTO   = 85   # >= este score → match automático
UMBRAL_DUDOSO = 60   # >= este score → guardar como dudoso

# ══════════════════════════════════════════════════════════════════════════════
# NORMALIZACIÓN
# ══════════════════════════════════════════════════════════════════════════════

# Palabras a eliminar antes de comparar (formatos, unidades, stopwords)
STOP = {
    'sin', 'con', 'de', 'del', 'la', 'el', 'los', 'las', 'un', 'una',
    'pack', 'paquete', 'envase', 'bote', 'botella', 'lata', 'tarro',
    'bolsa', 'caja', 'sobre', 'garrafa', 'brick', 'brik', 'frasco',
    'unidades', 'unidad', 'uds', 'ud',
    'g', 'kg', 'ml', 'l', 'cl', 'gr',
    'natural', 'clásico', 'clasico', 'original', 'tradicional',
    'sin gluten', 'ecologico', 'ecológico', 'bio',
}

MARCAS_BLANCAS_AH = {'alipende'}

def normalizar(texto):
    if not texto:
        return ""
    t = texto.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    # Quitar cantidades y formatos (250g, 1l, 3x100ml...)
    t = re.sub(r'\d+[\.,]?\d*\s*(g|kg|ml|l|cl|ud|uds|unidades?|x\d+)', '', t)
    t = re.sub(r'\d+\s*x\s*\d+', '', t)
    t = re.sub(r'\b\d+\b', '', t)
    # Quitar marca blanca Ahorramas
    for mb in MARCAS_BLANCAS_AH:
        t = t.replace(mb, '')
    # Normalizar espacios
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def fetch_all(tabla, columnas="*", filtros=None):
    rows, offset = [], 0
    while True:
        q = supabase.table(tabla).select(columnas)
        if filtros:
            for k, v in filtros.items():
                q = q.eq(k, v)
        res = q.range(offset, offset + 999).execute()
        rows.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    return rows

# ══════════════════════════════════════════════════════════════════════════════
# MATCHING
# ══════════════════════════════════════════════════════════════════════════════

def main(dry_run=False, umbral_auto=UMBRAL_AUTO):
    print("=" * 60)
    print("  🔗 MATCHING AHORRAMAS — Mi Mejor Cesta")
    print(f"  Umbral automático: {umbral_auto}%  |  Dudosos: {UMBRAL_DUDOSO}%")
    print(f"  Modo: {'DRY-RUN' if dry_run else '⚠️  PRODUCCIÓN'}")
    print("=" * 60)

    # ── 1. Cargar datos ────────────────────────────────────────────
    print("\n📥 Cargando datos...")

    ahorramas = fetch_all("precios_ahorramas", "id, nombre_comercial, categoria_ahorramas")
    print(f"  Ahorramas: {len(ahorramas)} productos")

    catalogo = fetch_all("productos_catalogo", "id, nombre_generico, id_categoria, tipo")
    print(f"  Catálogo:  {len(catalogo)} productos")

    matches_existentes = fetch_all("productos_match", "id_catalogo, id_ahorramas")
    ya_matcheados_ah = {m['id_ahorramas'] for m in matches_existentes if m.get('id_ahorramas')}
    print(f"  Matches Ahorramas existentes: {len(ya_matcheados_ah)}")

    # ── 2. Preparar índice del catálogo ───────────────────────────
    print("\n🔧 Preparando índice fuzzy...")
    idx_catalogo = []
    for c in catalogo:
        nombre_norm = normalizar(c['nombre_generico'])
        if nombre_norm:
            idx_catalogo.append({
                'id':     c['id'],
                'nombre': c['nombre_generico'],
                'norm':   nombre_norm,
                'tipo':   c.get('tipo', ''),
            })

    nombres_norm = [c['norm'] for c in idx_catalogo]
    print(f"  {len(nombres_norm)} productos en índice")

    # ── 3. Matching ────────────────────────────────────────────────
    print("\n🔍 Calculando matches...")

    automaticos = []   # (id_ahorramas, id_catalogo, score)
    dudosos     = []   # para CSV de revisión
    sin_match   = []

    pendientes = [p for p in ahorramas if p['id'] not in ya_matcheados_ah]
    print(f"  {len(pendientes)} productos a procesar (sin match previo)")

    for i, prod in enumerate(pendientes):
        nombre_ah = prod.get('nombre_comercial', '')
        if not nombre_ah:
            continue

        nombre_norm = normalizar(nombre_ah)
        if not nombre_norm or len(nombre_norm) < 3:
            continue

        # Buscar los 3 mejores matches
        resultados = process.extract(
            nombre_norm,
            nombres_norm,
            scorer=fuzz.token_sort_ratio,
            limit=3,
        )

        if not resultados:
            sin_match.append(prod)
            continue

        mejor_norm, mejor_score, mejor_idx = resultados[0]
        mejor_cat = idx_catalogo[mejor_idx]

        if mejor_score >= umbral_auto:
            automaticos.append({
                'id_ahorramas': prod['id'],
                'id_catalogo':  mejor_cat['id'],
                'score':        mejor_score,
                'nombre_ah':    nombre_ah,
                'nombre_cat':   mejor_cat['nombre'],
            })
        elif mejor_score >= UMBRAL_DUDOSO:
            dudosos.append({
                'id_ahorramas':    prod['id'],
                'nombre_ahorramas': nombre_ah,
                'id_catalogo':     mejor_cat['id'],
                'nombre_catalogo': mejor_cat['nombre'],
                'score':           mejor_score,
                'alt1_id':         idx_catalogo[resultados[1][2]]['id'] if len(resultados) > 1 else '',
                'alt1_nombre':     idx_catalogo[resultados[1][2]]['nombre'] if len(resultados) > 1 else '',
                'alt1_score':      resultados[1][1] if len(resultados) > 1 else 0,
                'alt2_id':         idx_catalogo[resultados[2][2]]['id'] if len(resultados) > 2 else '',
                'alt2_nombre':     idx_catalogo[resultados[2][2]]['nombre'] if len(resultados) > 2 else '',
                'alt2_score':      resultados[2][1] if len(resultados) > 2 else 0,
                'categoria_ah':    prod.get('categoria_ahorramas', ''),
            })
        else:
            sin_match.append(prod)

        if (i + 1) % 100 == 0:
            print(f"  Procesados {i+1}/{len(pendientes)}...", end='\r')

    print(f"\n{'='*60}")
    print(f"  ✅ Automáticos (>={umbral_auto}%):  {len(automaticos)}")
    print(f"  ⚠️  Dudosos ({UMBRAL_DUDOSO}-{umbral_auto-1}%):       {len(dudosos)}")
    print(f"  ❌ Sin match (<{UMBRAL_DUDOSO}%):      {len(sin_match)}")
    print(f"  📊 Total procesados:     {len(pendientes)}")

    # ── 4. Muestra de automáticos ──────────────────────────────────
    print("\n📋 Muestra matches automáticos (primeros 15):")
    for m in automaticos[:15]:
        print(f"  [{int(m['score']):3d}%] {m['nombre_ah'][:40]:<40} → {m['nombre_cat'][:35]}")

    # ── 5. Guardar CSV de dudosos ──────────────────────────────────
    fecha = datetime.now().strftime('%Y%m%d_%H%M')
    csv_dudosos = f"ahorramas_dudosos_{fecha}.csv"
    if dudosos:
        with open(csv_dudosos, 'w', newline='', encoding='utf-8') as f:
            campos = ['id_ahorramas', 'nombre_ahorramas', 'id_catalogo', 'nombre_catalogo',
                      'score', 'alt1_id', 'alt1_nombre', 'alt1_score',
                      'alt2_id', 'alt2_nombre', 'alt2_score', 'categoria_ah']
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(dudosos)
        print(f"\n  📄 Dudosos guardados en: {csv_dudosos}")

    if dry_run:
        print("\n[dry-run] No se guarda nada en Supabase.")
        return

    if not automaticos:
        print("\nNo hay matches automáticos que aplicar.")
        return

    # ── 6. Confirmar y aplicar ─────────────────────────────────────
    print(f"\n¿Aplicar {len(automaticos)} matches automáticos? (s/n): ", end="")
    if input().strip().lower() != 's':
        print("Cancelado.")
        return

    print("\n📤 Aplicando matches en productos_match...")
    ok = err = 0
    for m in automaticos:
        try:
            supabase.table("productos_match").update(
                {"id_ahorramas": m['id_ahorramas']}
            ).eq("id_catalogo", m['id_catalogo']).execute()
            ok += 1
        except Exception as e:
            err += 1
            if err <= 3:
                print(f"  ❌ Error: {e}")

    print(f"  ✅ Aplicados: {ok} | ❌ Errores: {err}")
    print("\n✅ Matching completado.")
    if dudosos:
        print(f"  Revisa {csv_dudosos} para los casos dudosos.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--umbral", type=int, default=UMBRAL_AUTO)
    args = ap.parse_args()
    main(dry_run=args.dry_run, umbral_auto=args.umbral)
