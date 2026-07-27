"""
match_carrefour.py  —  Mi Mejor Cesta (v6)
==========================================
Vincula productos_catalogo con precios_carrefour.

Algoritmo idéntico a match_alcampo.py v4 / match_dia.py v4:
- process.extract con token_sort_ratio ÚNICAMENTE (sin partial_ratio ni token_set_ratio)
- Filtro variantes: zero/sin alcohol/0,0/light/desnatado
- Filtro pares incompatibles: jamon/lomo, carne/atun, ajo/clavo...
- Requisito palabra clave: al menos una >4 letras en común
- 1-a-1 greedy por score descendente

v5 sobre v4:
- Elimina partial_ratio y token_set_ratio (causaban matches falsos)
- Elimina penalización por longitud relativa (incompatible con process.extract)
- Normalización simplificada: solo elimina marcas Carrefour propias, no terceros

v6 sobre v5:
- Nuevo filtro de FORMATO: descarta pares cuyo tamaño/cantidad no coincide
  (p.ej. "Donuts 4 Ud" vs "Donuts 6 Ud"). Compara masa/volumen/unidades tras
  normalizar a una base común (g, ml, ud) y teniendo en cuenta packs.
  Solo bloquea cuando AMBOS nombres tienen una cantidad clara de la misma
  familia y difieren >5%. Si uno no tiene cantidad, no bloquea (conserva el
  comportamiento anterior para nombres de catálogo sin unidad).

Uso:
  python scrapers/match_carrefour.py --dry-run
  python scrapers/match_carrefour.py
  python scrapers/match_carrefour.py --umbral 83
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

UMBRAL_AUTO   = 83
UMBRAL_DUDOSO = 60

MARCAS_CARREFOUR = {'carrefour', 'carrefour bio', 'reflets de france', 'tex', 'simpl', 'mmm'}

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


def variantes_incompatibles(nombre_cr, nombre_cat):
    tags_cr  = marcadores_variante(nombre_cr)
    tags_cat = marcadores_variante(nombre_cat)
    if not tags_cr and not tags_cat:
        return False
    if bool(tags_cr) != bool(tags_cat):
        return True
    return tags_cr != tags_cat


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


def tiene_par_incompatible(norm_cr, norm_cat):
    palabras_cr  = set(norm_cr.split())
    palabras_cat = set(norm_cat.split())
    for par in PARES_INCOMPATIBLES:
        p1, p2 = tuple(par)
        if (p1 in palabras_cr and p2 in palabras_cat) or \
           (p2 in palabras_cr and p1 in palabras_cat):
            return True
    return False


# ── Normalización ─────────────────────────────────────────────────────────────

def normalizar(texto, es_carrefour=False):
    if not texto:
        return ""
    t = texto.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r'\d+[\.,]?\d*\s*(g|kg|ml|l|cl|ud|uds|unidades?)', '', t)
    t = re.sub(r'\d+\s*x\s*\d+', '', t)
    t = re.sub(r'\b\d+\b', '', t)
    if es_carrefour:
        for marca in MARCAS_CARREFOUR:
            t = re.sub(rf'\b{re.escape(marca)}\b', '', t)
    t = re.sub(r'[^a-z\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


# ── Filtro 3: Formato / cantidad ──────────────────────────────────────────────

_UNID_BASE = {'kg': 1000, 'gr': 1, 'g': 1, 'l': 1000, 'cl': 10, 'ml': 1}

def extraer_formato(texto):
    """Devuelve (familia, valor_en_base) o None si el nombre no tiene una
    cantidad clara. Familias: 'masa' (base g), 'vol' (base ml), 'cant' (base ud).
    Tiene en cuenta packs: 'pack de 6', '6 x 200 ml' -> multiplica."""
    if not texto:
        return None
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace(",", ".")

    # multiplicador de pack: "6 x ...", "pack de 6", "pack 6"
    mult = 1
    mp = re.search(r'(\d+)\s*x\b', t) or re.search(r'pack\s*(?:de\s*)?(\d+)', t)
    if mp:
        try:
            mult = int(mp.group(1))
        except (TypeError, ValueError):
            mult = 1

    # medida principal: masa o volumen
    mm = re.search(r'(\d+(?:\.\d+)?)\s*(kg|gr|g|l|cl|ml)\b', t)
    if mm:
        val = float(mm.group(1)) * _UNID_BASE[mm.group(2)] * mult
        familia = 'masa' if mm.group(2) in ('kg', 'gr', 'g') else 'vol'
        return (familia, val)

    # medida por unidades sueltas: "6 ud", "12 uds", "4 unidades"
    mc = re.search(r'(\d+)\s*(?:uds?|unidad|unidades|u)\b', t)
    if mc:
        return ('cant', float(mc.group(1)))

    # pack sin medida por unidad -> contamos el pack como unidades
    if mult > 1:
        return ('cant', float(mult))

    return None


def formatos_compatibles(nombre_cr, nombre_cat):
    """True si los formatos son compatibles o no se pueden comparar.
    False solo si ambos tienen cantidad de la MISMA familia y difieren >5%."""
    fa = extraer_formato(nombre_cr)
    fb = extraer_formato(nombre_cat)
    if fa is None or fb is None:
        return True            # sin dato comparable -> no bloquear
    if fa[0] != fb[0]:
        return True            # familias distintas -> ambiguo -> no bloquear
    a, b = fa[1], fb[1]
    if a <= 0 or b <= 0:
        return True
    return max(a, b) / min(a, b) <= 1.05


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
    print("  MATCHING CARREFOUR v6 -- Mi Mejor Cesta")
    print(f"  Umbral auto: {umbral_auto}%  |  Dudosos: {UMBRAL_DUDOSO}%")
    print(f"  Modo: {'DRY-RUN' if dry_run else 'PRODUCCION'}")
    print("=" * 60)

    print("\nCargando datos...")
    carrefour = fetch_all("precios_carrefour", "id, nombre_comercial, marca")
    print(f"  Carrefour: {len(carrefour)} productos")
    catalogo  = fetch_all("productos_catalogo", "id, nombre_generico, tipo")
    print(f"  Catalogo:  {len(catalogo)} productos")
    matches_ex = fetch_all("productos_match", "id_catalogo, id_carrefour")
    ya_cr  = {m['id_carrefour']  for m in matches_ex if m.get('id_carrefour')}
    ya_cat = {m['id_catalogo']   for m in matches_ex if m.get('id_carrefour')}
    print(f"  Matches Carrefour existentes: {len(ya_cr)}")

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

    pendientes = [p for p in carrefour if p['id'] not in ya_cr]
    print(f"\n{len(pendientes)} productos Carrefour a procesar...")

    todos = []
    filtrados_variante = 0
    filtrados_tipo     = 0
    filtrados_formato  = 0

    for i, prod in enumerate(pendientes):
        nombre_cr = prod.get('nombre_comercial', '') or ''
        es_marca_blanca = any(m in nombre_cr.lower() for m in MARCAS_CARREFOUR)
        norm_cr = normalizar(nombre_cr, es_carrefour=True)
        if not norm_cr or len(norm_cr) < 3:
            continue

        kw_cr = {w for w in norm_cr.split() if len(w) > 4}

        resultados = process.extract(
            norm_cr,
            nombres_norm,
            scorer=fuzz.token_sort_ratio,
            limit=10,
            score_cutoff=UMBRAL_DUDOSO,
        )

        for _, score_int, idx_cat in resultados:
            cat = idx[idx_cat]
            if es_marca_blanca and cat['tipo'] == 'marca_fabricante':
                continue
            if variantes_incompatibles(nombre_cr, cat['nombre']):
                filtrados_variante += 1
                continue
            if tiene_par_incompatible(norm_cr, cat['norm']):
                filtrados_tipo += 1
                continue
            if not formatos_compatibles(nombre_cr, cat['nombre']):
                filtrados_formato += 1
                continue
            kw_cat = {w for w in cat['norm'].split() if len(w) > 4}
            if kw_cr and kw_cat and not (kw_cr & kw_cat):
                continue
            todos.append((score_int, prod['id'], cat['id'], nombre_cr, cat['nombre']))

        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(pendientes)} procesados...")

    print(f"  {len(todos)} pares candidatos")
    print(f"  (filtrados: {filtrados_variante} por variante, {filtrados_tipo} por tipo, {filtrados_formato} por formato)")

    todos.sort(key=lambda x: -x[0])
    usados_cr  = set(ya_cr)
    usados_cat = set(ya_cat)
    automaticos, dudosos_list = [], []

    for score_int, id_cr, id_cat, nombre_cr, nombre_cat in todos:
        if id_cr in usados_cr or id_cat in usados_cat:
            continue
        entry = {
            'id_carrefour': id_cr,
            'id_catalogo':  id_cat,
            'score':        score_int,
            'nombre_cr':    nombre_cr,
            'nombre_cat':   nombre_cat,
        }
        if score_int >= umbral_auto:
            automaticos.append(entry)
        else:
            dudosos_list.append(entry)
        usados_cr.add(id_cr)
        usados_cat.add(id_cat)

    sin_match = len(pendientes) - len(automaticos) - len(dudosos_list)

    print(f"\n{'='*60}")
    print(f"  Automáticos (>={umbral_auto}%): {len(automaticos)}")
    print(f"  Dudosos ({UMBRAL_DUDOSO}-{umbral_auto-1}%):    {len(dudosos_list)}")
    print(f"  Sin match (<{UMBRAL_DUDOSO}%):      {sin_match}")
    print(f"  Total procesados:        {len(pendientes)}")

    print("\nMuestra automáticos (primeros 20):")
    for m in sorted(automaticos, key=lambda x: -x['score'])[:20]:
        print(f"  [{int(m['score']):3d}%] {m['nombre_cr'][:45]:<45} -> {m['nombre_cat'][:35]}")

    if dudosos_list:
        print(f"\nMuestra dudosos (primeros 5):")
        for m in sorted(dudosos_list, key=lambda x: -x['score'])[:5]:
            print(f"  [{int(m['score']):3d}%] {m['nombre_cr'][:45]:<45} -> {m['nombre_cat'][:35]}")

    if dry_run:
        print("\n[dry-run] No se guarda nada.")
        return

    csv_path = None
    if dudosos_list:
        fecha = datetime.now().strftime('%Y%m%d_%H%M')
        csv_path = f"carrefour_dudosos_{fecha}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            campos = ['score', 'id_carrefour', 'nombre_cr', 'id_catalogo', 'nombre_cat']
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
                {"id_carrefour": m['id_carrefour']}
            ).eq("id_catalogo", m['id_catalogo']).execute()
            ok += 1
        except Exception as e:
            err += 1
            if err <= 3:
                print(f"  Error: {e}")
        if ok % 200 == 0 and ok > 0:
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
