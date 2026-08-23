"""
construir_catalogo_v2.py — Mi Mejor Cesta — FASE 5
=====================================================
La ÚNICA fase de la reconstrucción del catálogo que toca la BBDD real.
Todo lo anterior (Fases 1-4b) vive en CSVs locales dentro de old/.

Qué hace:
  1. Lee miembros_finales_<fecha>.csv (Fase 4) + categorias_asignadas_<fecha>.csv (Fase 4b)
  2. Construye productos_catalogo (1 fila por cluster) + productos_match
     (id_mercadona/id_dia/id_alcampo/id_ahorramas/id_carrefour por cluster)
  3. Hace backup CSV de lo que hay actualmente en productos_catalogo/
     productos_match ANTES de tocar nada (regla de oro del proyecto)
  4. TRUNCATE de compras_detalle, compras, productos_match, productos_catalogo
     (se borra compras/compras_detalle porque sus id_catalogo dejarían de
     tener sentido con el catálogo nuevo — confirmado con David que no hay
     usuarios reales con compras guardadas todavía, 10/08/2026)
  5. Inserta el catálogo y los matches nuevos

USO:
  python scrapers/construir_catalogo_v2.py --dry-run   # solo muestra, no toca nada
  python scrapers/construir_catalogo_v2.py             # construye de verdad (pide
                                                          confirmación escrita "SI")

NUNCA ejecutar sin --dry-run primero.
"""
import argparse
import csv
import glob
import os
import re
import sys
import unicodedata
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
except ImportError:
    pass

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_OLD = RAIZ / "old"

# Reutilizamos quitar_marca()/extraer_formato() de normalizar_productos.py
# (Fase 2) en vez de reinventar la limpieza de nombre aquí — ver el porqué
# justo encima de elegir_nombre_representativo().
sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalizar_productos import quitar_marca, extraer_formato  # noqa: E402

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

BATCH = 200

MARCAS_BLANCAS_CONOCIDAS = [
    "hacendado", "deliplus", "bosque verde", "compy", "baysi",
    "alvita", "granja penate", "casa tarradellas",
]


def normalizar(t):
    if not t:
        return ""
    t = t.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t).strip()


def mas_reciente(patron):
    candidatos = sorted(glob.glob(str(CARPETA_OLD / patron)))
    return candidatos[-1] if candidatos else None


def elegir_nombre_limpio(fila):
    """Construye el nombre_generico final a partir de UNA fila de
    miembros_finales_*.csv: quita marca y formato del nombre_original,
    y vuelve a añadir la marca al final (mismo patrón que ya usa
    clasificar_categoria.py en su columna 'nombre_representativo': 'Aceite
    de oliva 0,4º Hacendado').

    BUG corregido 23/08/2026 (David, sesión "fallos tras la Fase 5"): antes
    esta función devolvía directamente nombre_original SIN LIMPIAR cuando
    el cluster no tenía ningún miembro de Mercadona — es decir, para la
    mayoría del catálogo (los clusters de solo DIA/Alcampo/Carrefour/
    AhorraMas), el nombre que veía el usuario en la app arrastraba el
    formato/cantidad tal cual lo escribió cada super ("Leche Desnatada
    Carrefour Botella 1,5 L" en vez de "Leche Desnatada Carrefour").
    Verificado con los CSV reales de la Fase 5 del 20/08/2026
    (miembros_finales_20260820_1345.csv + categorias_asignadas_20260820_1346.csv):
    12.021 de 16.727 productos (71,9%) tenían el nombre sucio. Con este
    fix, sobre el mismo dataset, bajan a 11 (0,1%), sin ninguna regresión
    en los ~4.230 clusters que sí tenían Mercadona (esos ya salían limpios).
    """
    marca = (fila.get("marca_detectada") or "").strip()
    sin_marca, _ = quitar_marca(fila["nombre_original"], marca)
    nombre_limpio, _ = extraer_formato(sin_marca)
    nombre_limpio = nombre_limpio.strip()
    if not nombre_limpio:
        nombre_limpio = fila["nombre_original"]
    if marca and marca.lower() not in nombre_limpio.lower():
        return f"{nombre_limpio} {marca}".strip()
    return nombre_limpio


def elegir_nombre_representativo(filas_cluster):
    mercadona = [f for f in filas_cluster if f["super"] == "Mercadona"]
    if mercadona:
        fila = mercadona[0]
    else:
        nombres = Counter(f["nombre_original"] for f in filas_cluster)
        nombre_top = nombres.most_common(1)[0][0]
        fila = next(f for f in filas_cluster if f["nombre_original"] == nombre_top)
    return elegir_nombre_limpio(fila)


def elegir_marca(filas_cluster):
    for f in filas_cluster:
        m = (f.get("marca_detectada") or "").strip()
        if m:
            return m
    return ""


def determinar_tipo(marca):
    if not marca:
        return "marca_fabricante"
    return "marca_blanca" if normalizar(marca) in MARCAS_BLANCAS_CONOCIDAS else "marca_fabricante"


SUPER_A_COLUMNA = {
    "Mercadona": "id_mercadona",
    "DIA": "id_dia",
    "Alcampo": "id_alcampo",
    "AhorraMas": "id_ahorramas",
    "Carrefour": "id_carrefour",
}


def construir_datos():
    ruta_miembros = mas_reciente("miembros_finales_*.csv")
    ruta_categorias = mas_reciente("categorias_asignadas_*.csv")

    if not ruta_miembros:
        print("❌ No se encontró miembros_finales_*.csv — ejecuta construir_propuesta_final.py primero")
        return None
    if not ruta_categorias:
        print("❌ No se encontró categorias_asignadas_*.csv — ejecuta clasificar_categoria.py primero")
        return None

    print(f"📥 Miembros:    {ruta_miembros}")
    print(f"📥 Categorías:  {ruta_categorias}")

    with open(ruta_miembros, encoding="utf-8") as f:
        miembros = list(csv.DictReader(f))
    with open(ruta_categorias, encoding="utf-8") as f:
        categorias_rows = list(csv.DictReader(f))

    cat_por_cluster = {r["cluster_id"]: r for r in categorias_rows}

    por_cluster = defaultdict(list)
    for m in miembros:
        por_cluster[m["cluster_id"]].append(m)

    catalogo = []
    matches = []
    sin_categoria = 0

    for i, (cid, filas_cluster) in enumerate(sorted(por_cluster.items(), key=lambda x: int(x[0])), 1):
        cat_row = cat_por_cluster.get(cid)
        if not cat_row or not cat_row.get("id_categoria"):
            sin_categoria += 1
            continue

        cat_id_final = f"CAT-{i:05d}"
        nombre = elegir_nombre_representativo(filas_cluster)
        marca = elegir_marca(filas_cluster)
        tipo = determinar_tipo(marca)

        catalogo.append({
            "id": cat_id_final,
            "nombre_generico": nombre[:250],
            "marca": marca or None,
            "id_categoria": int(cat_row["id_categoria"]),
            "tipo": tipo,
            "activo": True,
            "orden": i,
        })

        match_row = {"id_catalogo": cat_id_final}
        supers_vistos = set()
        for f in filas_cluster:
            col = SUPER_A_COLUMNA.get(f["super"])
            if col and f["super"] not in supers_vistos:
                match_row[col] = f["id_super"]
                supers_vistos.add(f["super"])
        matches.append(match_row)

    if sin_categoria:
        print(f"⚠️  {sin_categoria} clusters sin categoría asignada — excluidos (no debería pasar)")

    return catalogo, matches


def hacer_backup(supabase):
    print("\n💾 Haciendo backup de productos_catalogo y productos_match actuales...")
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    CARPETA_OLD.mkdir(parents=True, exist_ok=True)

    for tabla in ["productos_catalogo", "productos_match"]:
        filas, offset = [], 0
        while True:
            res = supabase.table(tabla).select("*").range(offset, offset + 999).execute()
            filas.extend(res.data)
            if len(res.data) < 1000:
                break
            offset += 1000
        if filas:
            ruta = CARPETA_OLD / f"backup_{tabla}_{fecha}.csv"
            with open(ruta, "w", newline="", encoding="utf-8") as f:
                cols = list(filas[0].keys())
                w = csv.DictWriter(f, fieldnames=cols)
                w.writeheader()
                w.writerows(filas)
            print(f"  ✅ {tabla}: {len(filas)} filas → {ruta}")
        else:
            print(f"  ⚠️  {tabla} estaba vacía, no se generó backup")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("=" * 60)
    print("  CONSTRUIR CATALOGO — FASE 5 (la unica que toca la BBDD)")
    print(f"  Modo: {'DRY-RUN (no se guarda nada)' if args.dry_run else 'REAL'}")
    print("=" * 60)

    datos = construir_datos()
    if not datos:
        return
    catalogo, matches = datos

    print(f"\n✅ Catálogo construido: {len(catalogo):,} productos")
    print(f"   Marca blanca:     {sum(1 for c in catalogo if c['tipo']=='marca_blanca'):,}")
    print(f"   Marca fabricante: {sum(1 for c in catalogo if c['tipo']=='marca_fabricante'):,}")
    con_2mas = sum(1 for m in matches if sum(1 for k in m if k != 'id_catalogo' and m[k]) >= 2)
    print(f"   Con ≥2 supers (comparan precio): {con_2mas:,}")

    print("\n📋 Muestra de los primeros 15:")
    abrev = {"marca_blanca": "MB", "marca_fabricante": "MF"}
    for c in catalogo[:15]:
        print(f"  {c['id']} | {abrev.get(c['tipo'], '??')} | cat:{c['id_categoria']:3d} | {c['nombre_generico'][:55]}")

    if args.dry_run:
        print("\n[dry-run] No se ha tocado la BBDD. Ejecuta sin --dry-run para construir de verdad.")
        return

    if not SUPABASE_KEY:
        print("❌ SUPABASE_KEY no encontrada en .env")
        return

    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    hacer_backup(supabase)

    print(f"\n⚠️  Esto va a BORRAR y RECONSTRUIR:")
    print(f"   - productos_catalogo ({len(catalogo):,} filas nuevas)")
    print(f"   - productos_match ({len(matches):,} filas nuevas)")
    print(f"   - compras y compras_detalle (VACÍAS — confirmado sin usuarios reales, 10/08/2026)")
    print(f"\n   Backup ya guardado en {CARPETA_OLD} por si hace falta revertir.")
    resp = input("\n¿Continuar? Escribe 'SI' (mayúsculas) para confirmar: ")
    if resp.strip() != "SI":
        print("Cancelado. No se ha tocado nada.")
        return

    print("\n🗑️  Vaciando tablas...")
    try:
        supabase.table("compras_detalle").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("compras").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("productos_match").delete().neq("id_catalogo", "").execute()
        supabase.table("productos_catalogo").delete().neq("id", "").execute()
        print("  ✅ Tablas vaciadas")
    except Exception as e:
        print(f"  ❌ Error al vaciar: {e}")
        print("  Backup a salvo, nada más se ha tocado. Revisa el error antes de reintentar.")
        return

    print(f"\n📤 Insertando {len(catalogo):,} productos en productos_catalogo...")
    ok = err = 0
    for i in range(0, len(catalogo), BATCH):
        lote = catalogo[i:i + BATCH]
        try:
            supabase.table("productos_catalogo").insert(lote).execute()
            ok += len(lote)
            print(f"  Lote {i//BATCH+1}/{(len(catalogo)+BATCH-1)//BATCH} ({ok} OK)", end="\r")
        except Exception as e:
            err += len(lote)
            print(f"\n  ❌ Error lote {i//BATCH+1}: {e}")
    print(f"\n  ✅ Catálogo: {ok} OK | ❌ {err} errores")

    print(f"\n📤 Insertando {len(matches):,} matches...")
    ok = err = 0
    for i in range(0, len(matches), BATCH):
        lote = matches[i:i + BATCH]
        try:
            supabase.table("productos_match").insert(lote).execute()
            ok += len(lote)
            print(f"  Lote {i//BATCH+1}/{(len(matches)+BATCH-1)//BATCH} ({ok} OK)", end="\r")
        except Exception as e:
            err += len(lote)
            print(f"\n  ❌ Error lote {i//BATCH+1}: {e}")
    print(f"\n  ✅ Matches: {ok} OK | ❌ {err} errores")

    print("\n" + "=" * 60)
    print(f"  ✅ CATÁLOGO NUEVO EN PRODUCCIÓN")
    print("  Siguiente paso: re-ejecutar matching de los supers no cubiertos")
    print("  todavía y verificar la app en producción.")
    print("=" * 60)


if __name__ == "__main__":
    main()
