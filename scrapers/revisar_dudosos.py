"""
revisar_dudosos.py  —  Mi Mejor Cesta
======================================
Clasifica con IA los pares dudosos (60-82%) generados por los matchers
y aplica a la BD los que Claude valida como correctos.

Uso:
  python scrapers/revisar_dudosos.py dia_dudosos_20260505_1254.csv --super dia
  python scrapers/revisar_dudosos.py alcampo_dudosos_20260505_1259.csv --super alcampo
  python scrapers/revisar_dudosos.py ahorramas_dudosos_20260505_1633.csv --super ahorramas

Opciones:
  --min-score N   Solo procesar dudosos con fuzzy score >= N (default: 70)
  --dry-run       Solo muestra resultados sin aplicar a BD
"""

import os, csv, json, time, argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
except ImportError:
    pass

import anthropic
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

MODEL      = "claude-haiku-4-5-20251001"
BATCH_SIZE = 20
SLEEP_S    = 1.0

COLUMNA_ID = {
    "dia":       "id_dia",
    "alcampo":   "id_alcampo",
    "ahorramas": "id_ahorramas",
    "carrefour": "id_carrefour",
}

COLUMNA_CSV = {
    "dia":       ("id_dia",       "nombre_dia"),
    "alcampo":   ("id_alcampo",   "nombre_alc"),
    "ahorramas": ("id_ahorramas", "nombre_ah"),
    "carrefour": ("id_carrefour", "nombre_cr"),
}

SYSTEM_PROMPT = """\
Eres un experto en productos de supermercado español.
Evalúa si dos nombres de producto se refieren al MISMO producto.

Score de 0 a 10:
  10 = mismo producto exacto (marca, tipo y formato compatibles)
   8 = mismo producto, pequeña diferencia de tamaño o variante similar
   6 = misma categoría y tipo, variante distinta pero válida como sustituto
   4 = relación lejana, misma categoría amplia pero producto diferente
   0 = productos distintos o marcas incompatibles

Reglas:
- Distinto tamaño/formato NO penaliza si el producto es el mismo
- Si hay marca en ambos nombres, deben coincidir para score > 6
- Categorías distintas (ej: champú vs agua) → score 0 siempre

Devuelve ÚNICAMENTE un array JSON sin texto extra:
[{"idx": 0, "score": 8, "motivo": "mismo producto, distinto formato"}, ...]
"""


def leer_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def puntuar_lote(cliente, lote, col_id, col_nombre):
    lineas = []
    for i, row in enumerate(lote):
        lineas.append(
            f"{i}. SUPER: {row[col_nombre]!r}  |  CATÁLOGO: {row['nombre_cat']!r}"
        )

    resp = cliente.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Evalúa estos {len(lote)} pares:\n\n" + "\n".join(lineas),
        }],
    )
    texto = resp.content[0].text.strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(texto)


def aplicar_matches(sb, matches_ok, col_db):
    ok = err = 0
    for m in matches_ok:
        try:
            sb.table("productos_match").update(
                {col_db: m["id_super"]}
            ).eq("id_catalogo", m["id_catalogo"]).execute()
            ok += 1
        except Exception as e:
            err += 1
            if err <= 3:
                print(f"  Error: {e}")
        if ok % 50 == 0 and ok > 0:
            print(f"  {ok}/{len(matches_ok)} aplicados...")
    return ok, err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="Fichero CSV de dudosos")
    ap.add_argument("--super", required=True, choices=["dia", "alcampo", "ahorramas", "carrefour"])
    ap.add_argument("--min-score", type=float, default=70.0,
                    help="Solo procesar filas con fuzzy score >= N (default: 70)")
    ap.add_argument("--umbral-ia", type=int, default=7,
                    help="Score IA mínimo para aplicar match (default: 7)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not SUPABASE_KEY:
        print("ERROR: SUPABASE_KEY no encontrada"); exit(1)
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY no encontrada"); exit(1)

    col_db  = COLUMNA_ID[args.super]
    col_id, col_nombre = COLUMNA_CSV[args.super]

    sb  = create_client(SUPABASE_URL, SUPABASE_KEY)
    ai  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print("=" * 60)
    print(f"  REVISAR DUDOSOS — {args.super.upper()}")
    print(f"  Modelo: {MODEL}")
    print(f"  Min fuzzy score: {args.min_score}%  |  Umbral IA: {args.umbral_ia}/10")
    print(f"  Modo: {'DRY-RUN' if args.dry_run else 'PRODUCCION'}")
    print("=" * 60)

    filas = leer_csv(args.csv)
    print(f"\nFichero: {args.csv}  ({len(filas)} filas)")

    # Filtrar por score mínimo y por productos que ya tienen match en BD
    ya_match = set()
    rows_pm, offset = [], 0
    while True:
        res = sb.table("productos_match").select(f"id_catalogo,{col_db}") \
                .not_.is_(col_db, "null").range(offset, offset+999).execute()
        rows_pm.extend(res.data)
        if len(res.data) < 1000: break
        offset += 1000
    ya_cat  = {r["id_catalogo"] for r in rows_pm}
    ya_super = {r[col_db] for r in rows_pm}

    pendientes = [
        r for r in filas
        if float(r["score"]) >= args.min_score
        and r["id_catalogo"] not in ya_cat
        and r[col_id] not in ya_super
    ]
    print(f"Pendientes tras filtro (score>={args.min_score}%, sin match existente): {len(pendientes)}")

    if not pendientes:
        print("Nada que revisar.")
        return

    # Procesar en lotes
    resultados = []
    for i in range(0, len(pendientes), BATCH_SIZE):
        lote = pendientes[i:i+BATCH_SIZE]
        num  = i // BATCH_SIZE + 1
        tot  = (len(pendientes) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Lote {num}/{tot}...", end=" ", flush=True)
        try:
            punts = puntuar_lote(ai, lote, col_id, col_nombre)
            idx_map = {p["idx"]: p for p in punts}
            for j, row in enumerate(lote):
                p = idx_map.get(j, {})
                resultados.append({
                    "id_super":    row[col_id],
                    "id_catalogo": row["id_catalogo"],
                    "nombre_super": row[col_nombre],
                    "nombre_cat":  row["nombre_cat"],
                    "fuzzy":       float(row["score"]),
                    "score_ia":    p.get("score", -1),
                    "motivo":      p.get("motivo", "?"),
                })
            buenos = sum(1 for p in punts if p.get("score", 0) >= args.umbral_ia)
            print(f"ok — {buenos}/{len(lote)} válidos")
        except Exception as e:
            print(f"ERROR: {e}")
            for row in lote:
                resultados.append({
                    "id_super": row[col_id], "id_catalogo": row["id_catalogo"],
                    "nombre_super": row[col_nombre], "nombre_cat": row["nombre_cat"],
                    "fuzzy": float(row["score"]), "score_ia": -1, "motivo": str(e),
                })
            time.sleep(5)
        if i + BATCH_SIZE < len(pendientes):
            time.sleep(SLEEP_S)

    # Separar válidos / inválidos
    validos   = [r for r in resultados if r["score_ia"] >= args.umbral_ia]
    invalidos = [r for r in resultados if r["score_ia"] >= 0 and r["score_ia"] < args.umbral_ia]
    errores   = [r for r in resultados if r["score_ia"] < 0]

    print(f"\n{'='*60}")
    print(f"  Revisados:  {len(resultados)}")
    print(f"  Válidos (score_ia>={args.umbral_ia}):  {len(validos)}")
    print(f"  Inválidos:  {len(invalidos)}")
    print(f"  Errores:    {len(errores)}")

    print("\nMuestra válidos (primeros 15):")
    for r in sorted(validos, key=lambda x: -x["score_ia"])[:15]:
        print(f"  [IA:{r['score_ia']} fuz:{r['fuzzy']:.0f}%] "
              f"{r['nombre_super'][:42]:<42} -> {r['nombre_cat'][:32]}")

    if invalidos:
        print("\nMuestra inválidos (primeros 5):")
        for r in sorted(invalidos, key=lambda x: -x["fuzzy"])[:5]:
            print(f"  [IA:{r['score_ia']} fuz:{r['fuzzy']:.0f}%] "
                  f"{r['nombre_super'][:42]:<42} -> {r['nombre_cat'][:32]}  ({r['motivo']})")

    if dry_run := args.dry_run:
        print("\n[dry-run] No se aplica nada.")
        return

    if not validos:
        print("\nNo hay válidos que aplicar.")
        return

    print(f"\n¿Aplicar {len(validos)} matches válidos a productos_match.{col_db}? (s/n): ", end="")
    if input().strip().lower() != "s":
        print("Cancelado.")
        return

    # Deduplicar (1-a-1 greedy por score_ia desc)
    usados_super = set(ya_super)
    usados_cat   = set(ya_cat)
    a_aplicar = []
    for r in sorted(validos, key=lambda x: -x["score_ia"]):
        if r["id_super"] in usados_super or r["id_catalogo"] in usados_cat:
            continue
        a_aplicar.append(r)
        usados_super.add(r["id_super"])
        usados_cat.add(r["id_catalogo"])

    print(f"\nAplicando {len(a_aplicar)} matches (tras dedup 1-a-1)...")
    ok, err = aplicar_matches(sb, a_aplicar, col_db)
    print(f"\nAplicados: {ok} | Errores: {err}")
    print("Revisión completada.")


if __name__ == "__main__":
    main()
