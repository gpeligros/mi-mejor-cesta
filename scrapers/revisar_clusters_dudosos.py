"""
revisar_clusters_dudosos.py — Mi Mejor Cesta
==============================================
FASE 3b de la reconstrucción del catálogo.

Puntúa con Claude Haiku los bridges "dudosos" generados por
agrupar_productos.py (banda de score fuzzy 75-87) para decidir cuáles son
el MISMO producto de verdad y cuáles son falsos positivos (mismo texto
parecido pero producto distinto: sabor, marca o subtipo diferente).

Mismo patrón que revisar_matches_ahorramas.py: lotes de 20, modelo Haiku,
score 0-10, sin tocar la BBDD — solo lee el CSV de dudosos y escribe CSVs
de resultado.

USO:
  python scrapers/revisar_clusters_dudosos.py --dry-run   # solo 30, sin CSV final
  python scrapers/revisar_clusters_dudosos.py             # revisa todos
  python scrapers/revisar_clusters_dudosos.py --umbral 6  # score < 6 = incorrecto (default: 6)

Requiere que ya hayas ejecutado agrupar_productos.py (lee el
clusters_dudosos_<fecha>.csv más reciente en old/).

SALIDA (en old/, nada se escribe en Supabase):
  clusters_dudosos_revisados_<fecha>.csv   -> todos, con score + motivo
  bridges_aceptados_<fecha>.csv            -> solo score >= umbral (para Fase 5)
  bridges_rechazados_<fecha>.csv           -> solo score < umbral (quedan como
                                               clusters separados, no se fusionan)

REQUISITOS:
  - pip install anthropic python-dotenv
  - .env con ANTHROPIC_API_KEY
"""

import argparse
import csv
import glob
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from dotenv import load_dotenv
import anthropic

load_dotenv()

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_OLD = RAIZ / "old"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

BATCH_SIZE = 20
SLEEP_ENTRE_LOTES = 1.5
MODEL = "claude-haiku-4-5-20251001"
UMBRAL_DEFAULT = 6  # score < 6 -> NO es el mismo producto, no se fusiona

SYSTEM_PROMPT = """Eres un experto en productos de supermercado español.
Tu tarea es evaluar si dos nombres de producto (de dos supermercados
distintos) se refieren al MISMO producto genérico, para poder compararlos
de precio en una app de comparación de supermercados.

Para cada par debes devolver un score de 0 a 10:
  10 = mismo producto exacto (misma marca, mismo tipo)
   8 = mismo producto con pequeñas diferencias de redacción
   6 = mismo producto genérico, marca equivalente o sin marca relevante
   4 = relación cercana pero distinto subtipo (ej. mismo producto, sabor distinto)
   2 = misma categoría amplia pero producto claramente distinto
   0 = productos completamente distintos

Reglas importantes:
- Si las marcas son DISTINTAS y ambas son marcas de fabricante reales
  (ej. Mahou vs Steinburg, Pepsi vs Coca-Cola), el score debe ser bajo
  (<=4) aunque el resto del texto sea parecido — son productos distintos
  que compiten entre sí, no el mismo producto en dos tiendas.
- Si uno es marca blanca de un supermercado (Hacendado, Alipende, Dia,
  Bosque Verde, etc.) y el otro también es marca blanca (de otro
  supermercado) del MISMO tipo de producto, es aceptable score alto (8-10)
  porque para el usuario son equivalentes a efectos de comparar precio.
- El SABOR o VARIANTE importa: "con miel" vs "con cacao", "chocolate" vs
  "menta", son productos DISTINTOS (score <=4) aunque compartan casi todo
  el texto.
- El FORMATO/CANTIDAD ya se ignoró antes de llegar aquí — no lo tengas en
  cuenta, juzga solo si es el mismo producto en esencia.
- Categorías distintas (ej. pizza vs mini pizzas, licor vs queso) = score 0-2.

Devuelve ÚNICAMENTE un array JSON, sin texto adicional:
[
  {"cluster_id": "123", "score": 8, "motivo": "mismo producto, misma marca"},
  ...
]"""


def csv_dudosos_mas_reciente():
    candidatos = sorted(glob.glob(str(CARPETA_OLD / "clusters_dudosos_*.csv")))
    # Excluir los "revisados" si por error coincidieran con el patrón
    candidatos = [c for c in candidatos if "revisado" not in c]
    return candidatos[-1] if candidatos else None


def construir_cliente():
    if not ANTHROPIC_API_KEY:
        print("ERROR: falta ANTHROPIC_API_KEY en el .env")
        sys.exit(1)
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def es_numero(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def puntuar_lote(cliente, filas):
    lineas = []
    for f in filas:
        lineas.append(
            f"{f['cluster_id']} | "
            f"CLUSTER: {f['nombre_canonico_cluster']} [marca: {f['marca']}] | "
            f"CANDIDATO ({f['super_candidato']}): {f['nombre_candidato']}"
        )

    mensaje = cliente.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Puntúa estos {len(filas)} pares de productos:\n\n" + "\n".join(lineas),
        }],
    )

    texto = mensaje.content[0].text.strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(texto)


def main():
    parser = argparse.ArgumentParser(description="Revisa bridges dudosos con IA (Fase 3b)")
    parser.add_argument("--dry-run", action="store_true", help="Solo procesa los primeros 30")
    parser.add_argument("--umbral", type=int, default=UMBRAL_DEFAULT,
                         help=f"Score mínimo para aceptar el bridge (default: {UMBRAL_DEFAULT})")
    args = parser.parse_args()

    modo = "DRY-RUN" if args.dry_run else "COMPLETO"
    print("=" * 60)
    print(f"  🤖 REVISAR CLUSTERS DUDOSOS — Fase 3b — {modo}")
    print(f"  Umbral de aceptación: {args.umbral}/10  |  Modelo: {MODEL}")
    print("=" * 60)

    ruta = csv_dudosos_mas_reciente()
    if not ruta:
        print(f"\n❌ No se encontró ningún clusters_dudosos_*.csv en {CARPETA_OLD}")
        print("   Ejecuta primero: python scrapers/agrupar_productos.py")
        return

    with open(ruta, encoding="utf-8") as f:
        todas_filas = list(csv.DictReader(f))

    print(f"\n📥 {ruta}")
    print(f"  {len(todas_filas):,} bridges dudosos cargados")

    cliente = construir_cliente()

    filas = todas_filas[:30] if args.dry_run else todas_filas
    total = len(filas)
    if total == 0:
        print("No hay nada que revisar.")
        return

    print(f"\nProcesando {total}"
          f"{f' (de {len(todas_filas)}, modo dry-run)' if args.dry_run else ''}...\n")

    resultados = []
    procesados = 0
    for i in range(0, total, BATCH_SIZE):
        lote = filas[i:i + BATCH_SIZE]
        num_lote = (i // BATCH_SIZE) + 1
        total_lotes = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Lote {num_lote}/{total_lotes}...", end=" ", flush=True)

        try:
            puntuaciones = puntuar_lote(cliente, lote)
            idx = defaultdict(list)
            for p in puntuaciones:
                idx[str(p.get("cluster_id"))].append(p)

            for f in lote:
                candidatos_p = idx.get(str(f["cluster_id"]), [])
                p = candidatos_p.pop(0) if candidatos_p else {}
                sc = p.get("score", -1)
                resultados.append({**f, "score": sc, "motivo": p.get("motivo", "sin datos")})
                procesados += 1

            malos_lote = sum(1 for p in puntuaciones
                              if es_numero(p.get("score")) and p["score"] < args.umbral)
            print(f"OK ({procesados}/{total}) -- rechazados: {malos_lote}")

        except json.JSONDecodeError as e:
            print(f"\n  Error JSON lote {num_lote}: {e}")
            for f in lote:
                resultados.append({**f, "score": -1, "motivo": "error_json"})
        except Exception as e:
            print(f"\n  Error lote {num_lote}: {e}")
            for f in lote:
                resultados.append({**f, "score": -1, "motivo": f"error: {e}"})
            time.sleep(10)

        if i + BATCH_SIZE < total:
            time.sleep(SLEEP_ENTRE_LOTES)

    aceptados = [r for r in resultados if es_numero(r["score"]) and r["score"] >= args.umbral]
    rechazados = [r for r in resultados if es_numero(r["score"]) and r["score"] < args.umbral]
    errores = sum(1 for r in resultados if r["score"] == -1)

    print(f"\n{'='*60}")
    print("  RESUMEN")
    print(f"{'='*60}")
    print(f"  Total revisados:        {len(resultados)}")
    print(f"  Aceptados (>= {args.umbral}):      {len(aceptados)}")
    print(f"  Rechazados (< {args.umbral}):      {len(rechazados)}")
    print(f"  Errores:                {errores}")

    if args.dry_run:
        print("\n[dry-run] No se genera CSV final. Ejecuta sin --dry-run para procesarlo todo.")
        print("\nMuestra de rechazados (para verificar que el criterio es razonable):")
        for r in rechazados[:10]:
            print(f"  [{r['score']}] {r['nombre_canonico_cluster'][:35]:<35} <-> {r['nombre_candidato'][:35]:<35}  ({r['motivo']})")
        return

    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    cols = list(todas_filas[0].keys()) + ["score", "motivo"]

    ruta_todos = CARPETA_OLD / f"clusters_dudosos_revisados_{fecha}.csv"
    with open(ruta_todos, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(resultados)

    ruta_aceptados = CARPETA_OLD / f"bridges_aceptados_{fecha}.csv"
    with open(ruta_aceptados, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(aceptados)

    ruta_rechazados = CARPETA_OLD / f"bridges_rechazados_{fecha}.csv"
    with open(ruta_rechazados, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rechazados)

    print(f"\n✅ CSVs generados en {CARPETA_OLD}:")
    print(f"  {ruta_todos.name}")
    print(f"  {ruta_aceptados.name}  ({len(aceptados)} bridges confirmados)")
    print(f"  {ruta_rechazados.name}  ({len(rechazados)} bridges descartados)")
    print(f"\nSiguiente paso: Fase 4 — te enseño una muestra del catálogo propuesto")
    print(f"final (automáticos + aceptados) antes de tocar la BBDD.")


if __name__ == "__main__":
    main()
