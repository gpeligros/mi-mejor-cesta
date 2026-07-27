"""
revisar_matches_ahorramas.py
============================
Puntúa la calidad de los matches de AhorraMas usando Claude API (haiku).
Compara el nombre del catálogo vs el nombre_comercial de AhorraMas y asigna
un score de 0 a 10 + motivo.

Sirve para cazar los matches semánticamente FALSOS que el matching por texto
no distingue: mismo tipo pero distinto subtipo (vinos de bodegas distintas,
sabores distintos del mismo helado, cerdo vs pavo, etc.).

El filtro de FORMATO ya lo hace match_ahorramas.py (v4), así que aquí la IA
solo juzga si es el MISMO producto, no el tamaño.

USO:
  python scrapers/revisar_matches_ahorramas.py --dry-run   # solo los primeros 30, sin CSV ni SQL
  python scrapers/revisar_matches_ahorramas.py             # revisa todos, genera CSV + SQL de limpieza
  python scrapers/revisar_matches_ahorramas.py --umbral 5  # score < 5 = incorrecto (default: 5)

SALIDA (NO escribe en Supabase):
  matches_ahorramas_revisados_<fecha>.csv    -> todos los matches con su score
  matches_ahorramas_incorrectos_<fecha>.csv  -> solo los malos (score < umbral)
  limpiar_ahorramas_<fecha>.sql              -> SQL listo para anular los malos

Para limpiar: revisa el CSV de incorrectos y, si estás de acuerdo, ejecuta el
.sql en el SQL Editor de Supabase. NADA se borra automáticamente.

REQUISITOS:
  - pip install anthropic supabase python-dotenv
  - .env con SUPABASE_URL, SUPABASE_KEY (service_role), ANTHROPIC_API_KEY
"""

import argparse
import csv
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime

from dotenv import load_dotenv
import anthropic
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

BATCH_SIZE = 20
SLEEP_ENTRE_LOTES = 1.5
MODEL = "claude-haiku-4-5-20251001"
UMBRAL_DEFAULT = 5  # score < 5 -> match incorrecto

SYSTEM_PROMPT = """Eres un experto en productos de supermercado español.
Tu tarea es evaluar si dos nombres de producto se refieren al MISMO producto.

Para cada par debes devolver un score de 0 a 10:
  10 = mismo producto exacto (misma categoría, mismo tipo, misma marca si aplica)
   8 = mismo producto con pequeñas diferencias (variante muy similar)
   6 = producto muy similar pero no idéntico (misma categoría, distinto subtipo)
   4 = relación lejana (misma categoría amplia pero producto diferente)
   2 = categorías distintas pero alguna palabra en común
   0 = productos completamente distintos

Reglas importantes:
- Si el catálogo es marca_blanca, compara solo el TIPO de producto e ignora la
  marca del supermercado (en AhorraMas la marca blanca es "Alipende").
- Si el catálogo es marca_fabricante, la marca debe coincidir para score > 6.
- El TAMAÑO/FORMATO ya está verificado aparte: NO bajes el score por diferencias
  de tamaño o cantidad.
- Fíjate especialmente en el SUBTIPO. Son productos DIFERENTES (score bajo) aunque
  compartan muchas palabras: dos vinos de bodegas o añadas distintas, dos sabores
  distintos del mismo helado/yogur, cerdo vs pavo, con cafeína vs sin cafeína, etc.
- Diferente categoría (ej: champú vs agua) = score 0 siempre.

Devuelve ÚNICAMENTE un array JSON, sin texto adicional:
[
  {"id_catalogo": "CAT-xxxx", "id_ahorramas": "AH-xxxx", "score": 8, "motivo": "mismo producto"},
  ...
]"""


def construir_clientes():
    if not all([SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY]):
        print("ERROR: Faltan variables en .env (SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY)")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY), anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def fetch_matches(supabase: Client) -> list:
    """Carga los matches AhorraMas y cruza catálogo + precios (3 queries paginadas)."""
    print("  -> Cargando productos_match (AhorraMas)...")
    matches_raw, offset = [], 0
    while True:
        res = (
            supabase.table("productos_match")
            .select("id_catalogo, id_ahorramas")
            .not_.is_("id_ahorramas", "null")
            .range(offset, offset + 999)
            .execute()
        )
        lote = res.data
        if not lote:
            break
        matches_raw.extend(lote)
        if len(lote) < 1000:
            break
        offset += 1000

    if not matches_raw:
        return []

    ids_catalogo = list({m["id_catalogo"] for m in matches_raw})
    ids_ah = list({m["id_ahorramas"] for m in matches_raw})

    print("  -> Cargando productos_catalogo...")
    catalogo = {}
    for i in range(0, len(ids_catalogo), 500):
        res = (
            supabase.table("productos_catalogo")
            .select("id, nombre_normalizado, nombre_generico, tipo, marca")
            .in_("id", ids_catalogo[i:i + 500])
            .execute()
        )
        for r in res.data:
            catalogo[r["id"]] = r

    print("  -> Cargando precios_ahorramas...")
    precios = {}
    for i in range(0, len(ids_ah), 500):
        res = (
            supabase.table("precios_ahorramas")
            .select("id, nombre_comercial, precio")
            .in_("id", ids_ah[i:i + 500])
            .execute()
        )
        for r in res.data:
            precios[r["id"]] = r

    resultado = []
    for m in matches_raw:
        cat = catalogo.get(m["id_catalogo"], {})
        ah = precios.get(m["id_ahorramas"], {})
        nombre_cat = cat.get("nombre_generico") or cat.get("nombre_normalizado") or ""
        resultado.append({
            "id_catalogo":      m["id_catalogo"],
            "id_ahorramas":     m["id_ahorramas"],
            "nombre_catalogo":  nombre_cat,
            "tipo":             cat.get("tipo", "") or "",
            "marca_catalogo":   cat.get("marca", "") or "",
            "nombre_ahorramas": ah.get("nombre_comercial", "") or "",
            "precio_ahorramas": ah.get("precio", "") or "",
        })
    return resultado


def es_numero(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def puntuar_lote(cliente, matches):
    """Envía un lote a Claude para puntuar y devuelve la lista JSON."""
    lineas = []
    for m in matches:
        marca_info = f" [marca catalogo: {m['marca_catalogo']}]" if m["marca_catalogo"] else ""
        lineas.append(
            f"{m['id_catalogo']} | {m['id_ahorramas']} | "
            f"CATALOGO ({m['tipo']}): {m['nombre_catalogo']}{marca_info} | "
            f"AHORRAMAS: {m['nombre_ahorramas']}"
        )

    mensaje = cliente.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Puntua estos {len(matches)} pares de productos:\n\n" + "\n".join(lineas),
        }],
    )

    texto = mensaje.content[0].text.strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(texto)


def main():
    parser = argparse.ArgumentParser(description="Puntua matches AhorraMas con IA")
    parser.add_argument("--dry-run", action="store_true", help="Solo procesa los primeros 30, sin CSV ni SQL")
    parser.add_argument("--umbral", type=int, default=UMBRAL_DEFAULT,
                        help=f"Score minimo para considerar correcto (default: {UMBRAL_DEFAULT})")
    args = parser.parse_args()

    modo = "DRY-RUN" if args.dry_run else "PRODUCCION"
    print(f"\n{'='*60}")
    print(f"  revisar_matches_ahorramas.py -- {modo}")
    print(f"  Umbral de calidad: {args.umbral}/10  |  Modelo: {MODEL}")
    print(f"{'='*60}\n")

    supabase, cliente_ai = construir_clientes()

    print("Cargando matches AhorraMas activos...")
    todos_matches = fetch_matches(supabase)
    total_all = len(todos_matches)
    matches = todos_matches[:30] if args.dry_run else todos_matches

    total = len(matches)
    if total == 0:
        print("No hay matches de AhorraMas que revisar.")
        return
    print(f"Matches a revisar: {total}"
          f"{'  (de %d, modo dry-run)' % total_all if args.dry_run else ''}\n")

    resultados = []
    procesados = 0
    for i in range(0, total, BATCH_SIZE):
        lote = matches[i:i + BATCH_SIZE]
        num_lote = (i // BATCH_SIZE) + 1
        total_lotes = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Lote {num_lote}/{total_lotes}...", end=" ", flush=True)

        try:
            puntuaciones = puntuar_lote(cliente_ai, lote)
            idx = {p.get("id_catalogo"): p for p in puntuaciones}
            for m in lote:
                p = idx.get(m["id_catalogo"], {})
                sc = p.get("score", -1)
                resultados.append({**m, "score": sc, "motivo": p.get("motivo", "sin datos")})
                procesados += 1
            malos_lote = sum(1 for p in puntuaciones if es_numero(p.get("score")) and p["score"] < args.umbral)
            print(f"OK ({procesados}/{total}) -- incorrectos: {malos_lote}")
        except json.JSONDecodeError as e:
            print(f"\n  Error JSON lote {num_lote}: {e}")
            for m in lote:
                resultados.append({**m, "score": -1, "motivo": "error_json"})
        except Exception as e:
            print(f"\n  Error lote {num_lote}: {e}")
            for m in lote:
                resultados.append({**m, "score": -1, "motivo": f"error: {e}"})
            time.sleep(10)

        if i + BATCH_SIZE < total:
            time.sleep(SLEEP_ENTRE_LOTES)

    # ── Resumen ───────────────────────────────────────────────────────────────
    ok    = sum(1 for r in resultados if es_numero(r["score"]) and r["score"] >= args.umbral)
    malos = [r for r in resultados if es_numero(r["score"]) and 0 <= r["score"] < args.umbral]
    errores = sum(1 for r in resultados if r["score"] == -1)

    print(f"\n{'='*60}")
    print(f"  RESUMEN")
    print(f"{'='*60}")
    print(f"  Total revisados:      {len(resultados)}")
    print(f"  Score >= {args.umbral} (OK):      {ok}")
    print(f"  Score <  {args.umbral} (MAL):     {len(malos)}")
    print(f"  Score -1 (error):     {errores}")

    print(f"\n  Distribucion de scores:")
    dist = Counter(r["score"] for r in resultados)
    for score in sorted(dist, key=lambda s: (s if es_numero(s) else -99)):
        c = dist[score]
        print(f"    Score {str(score):>3}: {c:4d} {'#' * (c // 3)}")

    peores = sorted(malos, key=lambda r: r["score"])[:20]
    if peores:
        print(f"\n  Peores matches (los que se anularian):")
        for r in peores:
            print(f"    [{r['score']}] {r['nombre_ahorramas'][:36]:<36} -> "
                  f"{r['nombre_catalogo'][:28]:<28} ({str(r['motivo'])[:28]})")

    if args.dry_run:
        print(f"\n  DRY-RUN: no se ha generado CSV ni SQL.")
        print(f"  Ejecuta SIN --dry-run para procesar los {total_all} matches y generar los ficheros.")
        print(f"{'='*60}\n")
        return

    # ── Ficheros de salida (NO escribe en Supabase) ───────────────────────────
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    campos = ["id_catalogo", "id_ahorramas", "score", "motivo",
              "nombre_ahorramas", "nombre_catalogo", "tipo", "marca_catalogo", "precio_ahorramas"]

    def ordenar(rs):
        return sorted(rs, key=lambda x: (x["score"] if es_numero(x["score"]) else -1))

    f_todos = f"matches_ahorramas_revisados_{ts}.csv"
    with open(f_todos, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for r in ordenar(resultados):
            w.writerow({k: r.get(k, "") for k in campos})

    f_malos = f"matches_ahorramas_incorrectos_{ts}.csv"
    with open(f_malos, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for r in ordenar(malos):
            w.writerow({k: r.get(k, "") for k in campos})

    f_sql = f"limpiar_ahorramas_{ts}.sql"
    with open(f_sql, "w", encoding="utf-8") as f:
        f.write("-- Limpieza AhorraMas generada por revisar_matches_ahorramas.py\n")
        f.write(f"-- Fecha: {ts}  |  Umbral: score < {args.umbral}  |  Matches a anular: {len(malos)}\n")
        f.write(f"-- Revisa {f_malos} antes de ejecutar.\n")
        f.write("-- Esto NO borra productos ni precios: solo rompe el vinculo catalogo<->AhorraMas\n")
        f.write("-- de los matches que la IA marco como malos.\n\n")
        if malos:
            ids = ",\n  ".join(f"'{r['id_catalogo']}'" for r in sorted(malos, key=lambda x: x["id_catalogo"]))
            f.write("UPDATE productos_match SET id_ahorramas = NULL\n")
            f.write(f"WHERE id_catalogo IN (\n  {ids}\n);\n")
        else:
            f.write("-- No hay matches por debajo del umbral. Nada que limpiar.\n")

    print(f"\n  Ficheros generados (NADA escrito en Supabase todavia):")
    print(f"    - {f_todos}")
    print(f"    - {f_malos}  ({len(malos)} incorrectos)")
    print(f"    - {f_sql}  (SQL listo para anularlos)")
    print(f"\n  SIGUIENTE PASO: abre {f_malos}, comprueba que son malos de verdad,")
    print(f"  y si estas de acuerdo ejecuta {f_sql} en el SQL Editor de Supabase.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
