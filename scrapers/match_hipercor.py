"""
match_hipercor.py  —  Mi Mejor Cesta
======================================
Vincula productos_catalogo con precios_hipercor.

Algoritmo idéntico a match_alcampo.py v4:
- Pre-normaliza todos los nombres en un índice
- Usa process.extract (rapidfuzz ~100x más rápido que bucle manual)
- Matching 1-a-1 greedy por score descendente
- Filtro variantes: zero/sin alcohol/0,0/light/desnatado
- Filtro pares incompatibles: jamon/lomo, carne/atun, ajo/clavo...
- Requisito palabra clave: al menos una >4 letras en común

PREREQUISITO: ejecutar en Supabase SQL Editor:
  ALTER TABLE productos_match ADD COLUMN id_hipercor TEXT;

Uso:
  python scrapers/match_hipercor.py --dry-run
  python scrapers/match_hipercor.py
  python scrapers/match_hipercor.py --umbral 83
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

MARCAS_HIPERCOR = {'hipercor', 'el corte ingles', 'el corte inglés', 'aliada'}

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


def variantes_incompatibles(nombre_hc, nombre_cat):
    tags_hc  = marcadores_variante(nombre_hc)
    tags_cat = marcadores_variante(nombre_cat)
    if not tags_hc and not tags_cat:
        return False
    if bool(tags_hc) != bool(tags_cat):
        return True
    return tags_hc != tags_cat


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


def tiene_par_incompatible(norm_hc, norm_cat):
    palabras_hc  = set(norm_hc.split())
    palabras_cat = set(norm_cat.split())
    for par in PARES_INCOMPATIBLES:
        p1, p2 = tuple(par)
        if (p1 in palabras_hc  and p2 in palabras_cat) or \
           (p2 in palabras_hc  and p1 in palabras_cat):
            return True
    return False


# ── Normalización ─────────────────────────────────────────────────────────────

def normalizar(texto, es_hipercor=False):
    if not texto:
        return ""
    t = texto.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r'\d+[\.,]?\d*\s*(g|kg|ml|l|cl|ud|uds|unidades?)', '', t)
    t = re.sub(r'\d+\s*x\s*\d+', '', t)
    t = re.sub(r'\b\d+\b', '', t)
    if es_hipercor:
        for marca in MARCAS_HIPERCOR:
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
    print("  MATCHING HIPERCOR — Mi Mejor Cesta")
    print(f"  Umbral auto: {umbral_auto}%  |  Dudosos: {UMBRAL_DUDOSO}%")
    print(f"  Modo: {'DRY-RUN' if dry_run else 'PRODUCCION'}")
    print("=" * 60)

    print("\nCargando datos...")
    hipercor = fetch_all("precios_hipercor", "id, nombre_comercial, marca")
    print(f"  Hipercor: {len(hipercor)} productos")
    catalogo = fetch_all("productos_catalogo", "id, nombre_generico, tipo")
    print(f"  Catálogo: {len(catalogo)} productos")
    matches_ex = fetch_all("productos_match", "id_catalogo, id_hipercor")
    ya_hc  = {m['id_hipercor']  for m in matches_ex if m.get('id_hipercor')}
    ya_cat = {m['id_catalogo']  for m in matches_ex if m.get('id_hipercor')}
    print(f"  Matches Hipercor existentes: {len(ya_hc)}")

    if not hipercor:
        print("\nNo hay productos en precios_hipercor. Ejecuta scraper_hipercor.py primero.")
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

    pendientes = [p for p in hipercor if p['id'] not in ya_hc]
    print(f"\n{len(pendientes)} productos Hipercor a procesar...")

    todos = []
    filtrados_variante = 0
    filtrados_tipo     = 0

    for i, prod in enumerate(pendientes):
        nombre_hc = prod.get('nombre_comercial', '') or ''
        es_marca_blanca = any(m in nombre_hc.lower() for m in MARCAS_HIPERCOR)
        norm_hc = normalizar(nombre_hc, es_hipercor=True)
        if not norm_hc or len(norm_hc) < 3:
            continue

        kw_hc = {w for w in norm_hc.split() if len(w) > 4}

        resultados = process.extract(
            norm_hc,
            nombres_norm,
            scorer=fuzz.token_sort_ratio,
            limit=10,
            score_cutoff=UMBRAL_DUDOSO,
        )

        for _, score_int, idx_cat in resultados:
            cat = idx[idx_cat]
            if es_marca_blanca and cat['tipo'] == 'marca_fabricante':
                continue
            if variantes_incompatibles(nombre_hc, cat['nombre']):
                filtrados_variante += 1
                continue
            if tiene_par_incompatible(norm_hc, cat['norm']):
                filtrados_tipo += 1
                continue
            kw_cat = {w for w in cat['norm'].split() if len(w) > 4}
            if kw_hc and kw_cat and not (kw_hc & kw_cat):
                continue
            todos.append((score_int, prod['id'], cat['id'], nombre_hc, cat['nombre']))

        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(pendientes)} procesados...")

    print(f"  {len(todos)} pares candidatos")
    print(f"  (filtrados: {filtrados_variante} por variante, {filtrados_tipo} por tipo)")

    todos.sort(key=lambda x: -x[0])
    usados_hc  = set(ya_hc)
    usados_cat = set(ya_cat)
    automaticos, dudosos_list = [], []

    for score_int, id_hc, id_cat, nombre_hc, nombre_cat in todos:
        if id_hc in usados_hc or id_cat in usados_cat:
            continue
        entry = {
            'id_hipercor': id_hc,
            'id_catalogo': id_cat,
            'score':       score_int,
            'nombre_hc':   nombre_hc,
            'nombre_cat':  nombre_cat,
        }
        if score_int >= umbral_auto:
            automaticos.append(entry)
        else:
            dudosos_list.append(entry)
        usados_hc.add(id_hc)
        usados_cat.add(id_cat)

    sin_match = len(pendientes) - len(automaticos) - len(dudosos_list)

    print(f"\n{'='*60}")
    print(f"  Automáticos (>={umbral_auto}%): {len(automaticos)}")
    print(f"  Dudosos ({UMBRAL_DUDOSO}-{umbral_auto-1}%):    {len(dudosos_list)}")
    print(f"  Sin match (<{UMBRAL_DUDOSO}%):      {sin_match}")
    print(f"  Total procesados:       {len(pendientes)}")

    print("\nMuestra automáticos (primeros 20):")
    for m in sorted(automaticos, key=lambda x: -x['score'])[:20]:
        print(f"  [{int(m['score']):3d}%] {m['nombre_hc'][:45]:<45} -> {m['nombre_cat'][:35]}")

    if dudosos_list:
        print(f"\nMuestra dudosos (primeros 5):")
        for m in sorted(dudosos_list, key=lambda x: -x['score'])[:5]:
            print(f"  [{int(m['score']):3d}%] {m['nombre_hc'][:45]:<45} -> {m['nombre_cat'][:35]}")

    if dry_run:
        print("\n[dry-run] No se guarda nada.")
        return

    csv_path = None
    if dudosos_list:
        fecha = datetime.now().strftime('%Y%m%d_%H%M')
        csv_path = f"hipercor_dudosos_{fecha}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            campos = ['score', 'id_hipercor', 'nombre_hc', 'id_catalogo', 'nombre_cat']
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
                {"id_hipercor": m['id_hipercor']}
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
