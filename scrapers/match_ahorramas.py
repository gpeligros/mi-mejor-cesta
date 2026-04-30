"""
match_ahorramas.py  —  Mi Mejor Cesta (v3)
==========================================
Vincula precios_ahorramas con productos_catalogo.

Mejoras v3 sobre v2:
- Filtro variantes: zero/sin alcohol/0,0/light/desnatado — si uno los
  tiene y el otro no, se rechaza el match
- Filtro tipo de producto: pares de palabras incompatibles (jamon/lomo,
  carne/atun, ajo/clavo…) detectan productos distintos del mismo formato

Estrategia:
  - Score >= 83 -> match automatico  (umbral por defecto)
  - Score 60-82 -> dudoso (CSV para revision)
  - Score < 60  -> sin match

Uso:
  python scrapers/match_ahorramas.py --dry-run
  python scrapers/match_ahorramas.py
  python scrapers/match_ahorramas.py --umbral 85
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

# ── Filtro 1: Marcadores de variante ──────────────────────────────────────────
# Si un producto los tiene y el otro no, son variantes distintas → rechazar

def marcadores_variante(nombre):
    """Extrae etiquetas de variante del nombre original (sin normalizar)."""
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


def variantes_incompatibles(nombre_ah, nombre_cat):
    """True si los marcadores de variante de ambos productos son incompatibles."""
    tags_ah  = marcadores_variante(nombre_ah)
    tags_cat = marcadores_variante(nombre_cat)
    if not tags_ah and not tags_cat:
        return False
    # Uno tiene marcador y el otro no → variantes distintas
    if bool(tags_ah) != bool(tags_cat):
        return True
    # Ambos tienen marcadores: deben ser exactamente los mismos
    return tags_ah != tags_cat


# ── Filtro 2: Pares de tipo de producto incompatibles ─────────────────────────
# Palabras que indican categorías de producto mutuamente excluyentes

PARES_INCOMPATIBLES = {
    # Embutidos y charcutería
    frozenset({'jamon',     'lomo'}),
    frozenset({'jamon',     'chorizo'}),
    frozenset({'jamon',     'panceta'}),
    frozenset({'jamon',     'salchichon'}),
    frozenset({'jamon',     'morcilla'}),
    frozenset({'lomo',      'chorizo'}),
    frozenset({'lomo',      'panceta'}),
    frozenset({'lomo',      'morcilla'}),
    frozenset({'chorizo',   'salchichon'}),
    # Rellenos / ingredientes
    frozenset({'carne',     'atun'}),
    frozenset({'carne',     'bonito'}),
    frozenset({'carne',     'salmon'}),
    frozenset({'carne',     'bacalao'}),
    frozenset({'pollo',     'salmon'}),
    frozenset({'pollo',     'atun'}),
    frozenset({'pollo',     'ternera'}),
    frozenset({'ternera',   'cerdo'}),
    frozenset({'ricota',    'carne'}),
    frozenset({'ricota',    'espinacas'}),
    # Especias / condimentos
    frozenset({'ajo',       'clavo'}),
    frozenset({'ajo',       'canela'}),
    frozenset({'ajo',       'comino'}),
    frozenset({'ajo',       'oregano'}),
    frozenset({'pimienta',  'canela'}),
    # Frutas
    frozenset({'naranja',   'limon'}),
    frozenset({'naranja',   'manzana'}),
    frozenset({'manzana',   'pera'}),
    frozenset({'fresa',     'mango'}),
    # Pescados
    frozenset({'salmon',    'merluza'}),
    frozenset({'salmon',    'bacalao'}),
    frozenset({'atun',      'sardina'}),
    frozenset({'atun',      'anchoa'}),
    frozenset({'atun',      'mejillon'}),
}


def tiene_par_incompatible(norm_ah, norm_cat):
    """True si los nombres normalizados contienen un par de tipos incompatibles."""
    palabras_ah  = set(norm_ah.split())
    palabras_cat = set(norm_cat.split())
    for par in PARES_INCOMPATIBLES:
        p1, p2 = tuple(par)
        if (p1 in palabras_ah and p2 in palabras_cat) or \
           (p2 in palabras_ah and p1 in palabras_cat):
            return True
    return False


# ── Normalización ─────────────────────────────────────────────────────────────

def normalizar(texto, es_ahorramas=False):
    if not texto:
        return ""
    t = texto.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r'\d+[\.,]?\d*\s*(g|kg|ml|l|cl|ud|uds|unidades?)', '', t)
    t = re.sub(r'\d+\s*x\s*\d+', '', t)
    t = re.sub(r'\b\d+\b', '', t)
    if es_ahorramas:
        t = t.replace('alipende', '')
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
    print("  MATCHING AHORRAMAS v3 -- Mi Mejor Cesta")
    print(f"  Umbral auto: {umbral_auto}%  |  Dudosos: {UMBRAL_DUDOSO}%")
    print(f"  Modo: {'DRY-RUN' if dry_run else 'PRODUCCION'}")
    print("=" * 60)

    # Cargar datos
    print("\nCargando datos...")
    ahorramas = fetch_all("precios_ahorramas", "id, nombre_comercial, categoria_ahorramas")
    print(f"  AhorraMas: {len(ahorramas)} productos")
    catalogo  = fetch_all("productos_catalogo", "id, nombre_generico, tipo")
    print(f"  Catalogo:  {len(catalogo)} productos")
    matches_existentes = fetch_all("productos_match", "id_catalogo, id_ahorramas")
    ya_ah  = {m['id_ahorramas'] for m in matches_existentes if m.get('id_ahorramas')}
    ya_cat = {m['id_catalogo']  for m in matches_existentes if m.get('id_ahorramas')}
    print(f"  Matches AhorraMas existentes: {len(ya_ah)}")

    # Preparar indice
    print("\nPreparando indice...")
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
    print(f"  {len(nombres_norm)} productos en indice")

    # Calcular scores
    pendientes = [p for p in ahorramas if p['id'] not in ya_ah]
    print(f"\n{len(pendientes)} productos a procesar (sin match previo)...")

    todos = []  # (score_int, id_ah, id_cat, nombre_ah, nombre_cat)
    filtrados_variante = 0
    filtrados_tipo     = 0

    for i, prod in enumerate(pendientes):
        nombre_ah = prod.get('nombre_comercial', '') or ''
        es_alipende = 'alipende' in nombre_ah.lower()
        norm_ah = normalizar(nombre_ah, es_ahorramas=True)
        if not norm_ah or len(norm_ah) < 3:
            continue

        kw_ah = {w for w in norm_ah.split() if len(w) > 4}

        resultados = process.extract(
            norm_ah,
            nombres_norm,
            scorer=fuzz.token_sort_ratio,
            limit=10,
            score_cutoff=UMBRAL_DUDOSO,
        )

        for _, score_int, idx_cat in resultados:
            cat = idx[idx_cat]

            # Filtro anti-marca-cruzada (Alipende no matchea con marca_fabricante)
            if es_alipende and cat['tipo'] == 'marca_fabricante':
                continue

            # Filtro 1: variantes incompatibles (zero, sin alcohol, light…)
            if variantes_incompatibles(nombre_ah, cat['nombre']):
                filtrados_variante += 1
                continue

            # Filtro 2: pares de tipo incompatible (jamon/lomo, carne/atun…)
            if tiene_par_incompatible(norm_ah, cat['norm']):
                filtrados_tipo += 1
                continue

            # Requisito de palabra clave: al menos una >4 letras en comun
            kw_cat = {w for w in cat['norm'].split() if len(w) > 4}
            if kw_ah and kw_cat and not (kw_ah & kw_cat):
                continue

            todos.append((score_int, prod['id'], cat['id'], nombre_ah, cat['nombre']))

        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(pendientes)} procesados...")

    print(f"  {len(todos)} pares candidatos")
    print(f"  (filtrados: {filtrados_variante} por variante, {filtrados_tipo} por tipo)")

    # Asignacion 1-a-1 (greedy por score desc)
    todos.sort(key=lambda x: -x[0])
    usados_ah  = set(ya_ah)
    usados_cat = set(ya_cat)
    automaticos, dudosos_list = [], []

    for score_int, id_ah, id_cat, nombre_ah, nombre_cat in todos:
        if id_ah in usados_ah or id_cat in usados_cat:
            continue
        entry = {
            'id_ahorramas': id_ah,
            'id_catalogo':  id_cat,
            'score':        score_int,
            'nombre_ah':    nombre_ah,
            'nombre_cat':   nombre_cat,
        }
        if score_int >= umbral_auto:
            automaticos.append(entry)
        else:
            dudosos_list.append(entry)
        usados_ah.add(id_ah)
        usados_cat.add(id_cat)

    sin_match = len(pendientes) - len(automaticos) - len(dudosos_list)

    print(f"\n{'='*60}")
    print(f"  Automaticos (>={umbral_auto}%): {len(automaticos)}")
    print(f"  Dudosos ({UMBRAL_DUDOSO}-{umbral_auto-1}%):    {len(dudosos_list)}")
    print(f"  Sin match (<{UMBRAL_DUDOSO}%):      {sin_match}")
    print(f"  Total procesados:       {len(pendientes)}")

    print("\nMuestra automaticos (primeros 20):")
    for m in sorted(automaticos, key=lambda x: -x['score'])[:20]:
        print(f"  [{int(m['score']):3d}%] {m['nombre_ah'][:45]:<45} -> {m['nombre_cat'][:35]}")

    if dudosos_list:
        print(f"\nMuestra dudosos (primeros 5):")
        for m in sorted(dudosos_list, key=lambda x: -x['score'])[:5]:
            print(f"  [{int(m['score']):3d}%] {m['nombre_ah'][:45]:<45} -> {m['nombre_cat'][:35]}")

    if dry_run:
        print("\n[dry-run] No se guarda nada en Supabase.")
        return

    # Exportar dudosos a CSV
    csv_path = None
    if dudosos_list:
        fecha = datetime.now().strftime('%Y%m%d_%H%M')
        csv_path = f"ahorramas_dudosos_{fecha}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            campos = ['score', 'id_ahorramas', 'nombre_ah', 'id_catalogo', 'nombre_cat']
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            for d in sorted(dudosos_list, key=lambda x: -x['score']):
                w.writerow({k: d[k] for k in campos})
        print(f"\nDudosos -> {csv_path} ({len(dudosos_list)} filas)")

    if not automaticos:
        print("\nNo hay matches automaticos que aplicar.")
        return

    # Confirmar y aplicar
    print(f"\nAplicar {len(automaticos)} matches automaticos (>={umbral_auto}%)? (s/n): ", end="")
    if input().strip().lower() != 's':
        print("Cancelado.")
        return

    print("\nAplicando matches en productos_match...")
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
                print(f"  Error: {e}")
        if ok % 50 == 0 and ok > 0:
            print(f"  {ok}/{len(automaticos)} aplicados...")

    print(f"\nAplicados: {ok} | Errores: {err}")
    if csv_path:
        print(f"Dudosos pendientes de revision: {csv_path}")
    print("Matching completado.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--umbral", type=int, default=UMBRAL_AUTO)
    args = ap.parse_args()
    main(dry_run=args.dry_run, umbral_auto=args.umbral)
