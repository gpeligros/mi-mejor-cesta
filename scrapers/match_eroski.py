"""
match_eroski.py  —  Mi Mejor Cesta
=====================================
Vincula productos_catalogo con precios_eroski.

Algoritmo idéntico a match_alcampo.py v4.

PREREQUISITO: ejecutar en Supabase SQL Editor:
  ALTER TABLE productos_match ADD COLUMN id_eroski TEXT;

Uso:
  python scrapers/match_eroski.py --dry-run
  python scrapers/match_eroski.py
  python scrapers/match_eroski.py --umbral 83
"""

import os, re, csv, argparse, unicodedata
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
    print("ERROR: SUPABASE_KEY no encontrada en .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

UMBRAL_AUTO   = 85
UMBRAL_DUDOSO = 60

# Marcas blancas de Eroski
MARCAS_EROSKI = {'eroski', 'belnia', 'eroski basic', 'natur'}

# ── Filtro 1: Variantes ───────────────────────────────────────────────────────

def marcadores_variante(nombre):
    t = nombre.lower()
    tags = set()
    if re.search(r'\b0[,.]0\b|\b00\b', t) or 'sin alcohol' in t:
        tags.add('sin_alcohol')
    if re.search(r'\bzero\b', t):
        tags.add('zero')
    if 'light' in t:
        tags.add('light')
    if re.search(r'\bdesnatad', t):
        tags.add('desnatado')
    if re.search(r'\bsemidesnatad', t):
        tags.add('semidesnatado')
    if 'sin lactosa' in t:
        tags.add('sin_lactosa')
    return tags


def variantes_incompatibles(nombre_er, nombre_cat):
    tags_er  = marcadores_variante(nombre_er)
    tags_cat = marcadores_variante(nombre_cat)
    if not tags_er and not tags_cat:
        return False
    if bool(tags_er) != bool(tags_cat):
        return True
    return tags_er != tags_cat


# ── Filtro 2: Pares incompatibles ─────────────────────────────────────────────

PARES_INCOMPATIBLES = {
    frozenset({'jamon',   'lomo'}),
    frozenset({'jamon',   'chorizo'}),
    frozenset({'jamon',   'panceta'}),
    frozenset({'jamon',   'salchichon'}),
    frozenset({'jamon',   'morcilla'}),
    frozenset({'lomo',    'chorizo'}),
    frozenset({'lomo',    'panceta'}),
    frozenset({'chorizo', 'salchichon'}),
    frozenset({'carne',   'atun'}),
    frozenset({'carne',   'bonito'}),
    frozenset({'carne',   'salmon'}),
    frozenset({'carne',   'bacalao'}),
    frozenset({'pollo',   'salmon'}),
    frozenset({'pollo',   'atun'}),
    frozenset({'pollo',   'ternera'}),
    frozenset({'ternera', 'cerdo'}),
    frozenset({'ricota',  'carne'}),
    frozenset({'ajo',     'clavo'}),
    frozenset({'ajo',     'canela'}),
    frozenset({'ajo',     'comino'}),
    frozenset({'naranja', 'limon'}),
    frozenset({'naranja', 'manzana'}),
    frozenset({'manzana', 'pera'}),
    frozenset({'salmon',  'merluza'}),
    frozenset({'salmon',  'bacalao'}),
    frozenset({'atun',    'sardina'}),
    frozenset({'atun',    'anchoa'}),
    frozenset({'atun',    'mejillon'}),
}


def tiene_par_incompatible(norm_er, norm_cat):
    palabras_er  = set(norm_er.split())
    palabras_cat = set(norm_cat.split())
    for par in PARES_INCOMPATIBLES:
        p1, p2 = tuple(par)
        if (p1 in palabras_er  and p2 in palabras_cat) or \
           (p2 in palabras_er  and p1 in palabras_cat):
            return True
    return False


# ── Normalización ─────────────────────────────────────────────────────────────

def normalizar(texto, es_eroski=False):
    if not texto:
        return ""
    t = texto.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r'\d+[\.,]?\d*\s*(g|kg|ml|l|cl|ud|uds|unidades?)', '', t)
    t = re.sub(r'\d+\s*x\s*\d+', '', t)
    t = re.sub(r'\b\d+\b', '', t)
    if es_eroski:
        for marca in MARCAS_EROSKI:
            t = t.replace(marca, '')
    t = re.sub(r'[^a-z\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


# ── Supabase ──────────────────────────────────────────────────────────────────

def fetch_all(tabla, columnas="*"):
    rows, offset = [], 0
    while True:
        res = supabase.table(tabla).select(columnas).range(offset, offset + 999).execute()
        rows.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    return rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main(dry_run=False, umbral_auto=UMBRAL_AUTO):
    print("=" * 60)
    print("  MATCHING EROSKI — Mi Mejor Cesta")
    print(f"  Umbral auto: {umbral_auto}%  |  Dudosos: {UMBRAL_DUDOSO}%")
    print(f"  Modo: {'DRY-RUN' if dry_run else 'PRODUCCION'}")
    print("=" * 60)

    print("\nCargando datos...")
    eroski   = fetch_all("precios_eroski", "id, nombre_comercial, marca")
    print(f"  Eroski:   {len(eroski)} productos")
    catalogo = fetch_all("productos_catalogo", "id, nombre_generico, tipo")
    print(f"  Catálogo: {len(catalogo)} productos")
    matches_ex = fetch_all("productos_match", "id_catalogo, id_eroski")
    ya_er  = {m['id_eroski']   for m in matches_ex if m.get('id_eroski')}
    ya_cat = {m['id_catalogo'] for m in matches_ex if m.get('id_eroski')}
    print(f"  Matches Eroski existentes: {len(ya_er)}")

    if not eroski:
        print("\nNo hay productos en precios_eroski. Ejecuta scraper_eroski.py primero.")
        return

    print("\nPreparando índice...")
    idx = []
    for c in catalogo:
        norm = normalizar(c['nombre_generico'])
        if norm:
            idx.append({
                'id':     c['id'],
                'nombre': c['nombre_generico'],
                'norm':   norm,
                'tipo':   c.get('tipo') or '',
            })
    nombres_norm = [c['norm'] for c in idx]
    print(f"  {len(nombres_norm)} entradas en índice")

    pendientes = [p for p in eroski if p['id'] not in ya_er]
    print(f"\n{len(pendientes)} productos Eroski a procesar...")

    todos = []
    filtrados_variante = 0
    filtrados_tipo     = 0

    for i, prod in enumerate(pendientes):
        nombre_er = prod.get('nombre_comercial', '') or ''
        es_marca_blanca = any(m in nombre_er.lower() for m in MARCAS_EROSKI)
        norm_er = normalizar(nombre_er, es_eroski=True)
        if not norm_er or len(norm_er) < 3:
            continue

        kw_er = {w for w in norm_er.split() if len(w) > 4}

        resultados = process.extract(
            norm_er,
            nombres_norm,
            scorer=fuzz.token_sort_ratio,
            limit=10,
            score_cutoff=UMBRAL_DUDOSO,
        )

        for _, score_int, idx_cat in resultados:
            cat = idx[idx_cat]
            if es_marca_blanca and cat['tipo'] == 'marca_fabricante':
                continue
            if variantes_incompatibles(nombre_er, cat['nombre']):
                filtrados_variante += 1
                continue
            if tiene_par_incompatible(norm_er, cat['norm']):
                filtrados_tipo += 1
                continue
            kw_cat = {w for w in cat['norm'].split() if len(w) > 4}
            if kw_er and kw_cat and not (kw_er & kw_cat):
                continue
            todos.append((score_int, prod['id'], cat['id'], nombre_er, cat['nombre']))

        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(pendientes)} procesados...")

    print(f"  {len(todos)} pares candidatos")
    print(f"  (filtrados: {filtrados_variante} por variante, {filtrados_tipo} por tipo)")

    todos.sort(key=lambda x: -x[0])
    usados_er  = set(ya_er)
    usados_cat = set(ya_cat)
    automaticos, dudosos_list = [], []

    for score_int, id_er, id_cat, nombre_er, nombre_cat in todos:
        if id_er in usados_er or id_cat in usados_cat:
            continue
        entry = {
            'id_eroski':   id_er,
            'id_catalogo': id_cat,
            'score':       score_int,
            'nombre_er':   nombre_er,
            'nombre_cat':  nombre_cat,
        }
        if score_int >= umbral_auto:
            automaticos.append(entry)
        else:
            dudosos_list.append(entry)
        usados_er.add(id_er)
        usados_cat.add(id_cat)

    sin_match = len(pendientes) - len(automaticos) - len(dudosos_list)

    print(f"\n{'='*60}")
    print(f"  Automáticos (>={umbral_auto}%): {len(automaticos)}")
    print(f"  Dudosos ({UMBRAL_DUDOSO}-{umbral_auto-1}%):    {len(dudosos_list)}")
    print(f"  Sin match (<{UMBRAL_DUDOSO}%):      {sin_match}")
    print(f"  Total procesados:       {len(pendientes)}")

    print("\nMuestra automáticos (primeros 20):")
    for m in sorted(automaticos, key=lambda x: -x['score'])[:20]:
        print(f"  [{int(m['score']):3d}%] {m['nombre_er'][:45]:<45} -> {m['nombre_cat'][:35]}")

    if dudosos_list:
        print(f"\nMuestra dudosos (primeros 5):")
        for m in sorted(dudosos_list, key=lambda x: -x['score'])[:5]:
            print(f"  [{int(m['score']):3d}%] {m['nombre_er'][:45]:<45} -> {m['nombre_cat'][:35]}")

    if dry_run:
        print("\n[dry-run] No se guarda nada.")
        return

    csv_path = None
    if dudosos_list:
        fecha = datetime.now().strftime('%Y%m%d_%H%M')
        csv_path = f"eroski_dudosos_{fecha}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            campos = ['score', 'id_eroski', 'nombre_er', 'id_catalogo', 'nombre_cat']
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            for d in sorted(dudosos_list, key=lambda x: -x['score']):
                w.writerow({k: d[k] for k in campos})
        print(f"\nDudosos -> {csv_path} ({len(dudosos_list)} filas)")

    if not automaticos:
        print("\nNo hay matches automáticos.")
        return

    print(f"\nAplicar {len(automaticos)} matches automáticos (>={umbral_auto}%)? (s/n): ", end="")
    if input().strip().lower() != 's':
        print("Cancelado.")
        return

    print("\nAplicando matches...")
    ok = err = 0
    for m in automaticos:
        try:
            supabase.table("productos_match").update(
                {"id_eroski": m['id_eroski']}
            ).eq("id_catalogo", m['id_catalogo']).execute()
            ok += 1
        except Exception as e:
            err += 1
            if err <= 3:
                print(f"  Error: {e}")
        if ok % 100 == 0 and ok > 0:
            print(f"  {ok}/{len(automaticos)} aplicados...")

    print(f"\nAplicados: {ok} | Errores: {err}")
    if csv_path:
        print(f"Dudosos: {csv_path}")
    print("Matching completado.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--umbral", type=int, default=UMBRAL_AUTO)
    args = ap.parse_args()
    main(dry_run=args.dry_run, umbral_auto=args.umbral)
