"""
revisar_matches_alcampo.py
======================
Puntúa la calidad de los matches ALCAMPO restantes usando Claude API.
Compara nombre_normalizado del catálogo vs nombre_comercial de ALCAMPO
y asigna un score de 0 a 10 + motivo.

USO:
  python scrapers/revisar_matches_alcampo.py              # analiza todos y genera CSV
  python scrapers/revisar_matches_alcampo.py --dry-run    # solo muestra los primeros 30
  python scrapers/revisar_matches_alcampo.py --umbral 5   # marca como incorrectos score < 5 (default: 5)

SALIDA:
  matches_alcampo_revisados.csv  → todos los matches con su score
  matches_alcampo_incorrectos.csv → solo los que están por debajo del umbral

REQUISITOS:
  - pip install anthropic supabase python-dotenv pandas
  - .env con SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
import anthropic
from supabase import create_client, Client
import pandas as pd

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

BATCH_SIZE = 20
SLEEP_ENTRE_LOTES = 1.5
MODEL = "claude-haiku-4-5-20251001"
UMBRAL_DEFAULT = 5  # score < 5 → match incorrecto

SYSTEM_PROMPT = """Eres un experto en productos de supermercado español.
Tu tarea es evaluar si dos nombres de producto se refieren al MISMO tipo de producto.

Para cada par debes devolver un score de 0 a 10:
  10 = mismo producto exacto (misma categoría, mismo tipo, misma marca si aplica)
   8 = mismo producto con pequeñas diferencias (formato distinto, variante similar)
   6 = producto muy similar pero no idéntico (misma categoría, distinto subtipo)
   4 = relación lejana (misma categoría amplia pero producto diferente)
   2 = categorías distintas pero alguna palabra en común
   0 = productos completamente distintos

Reglas importantes:
- Si el catálogo es marca_blanca, compara solo el tipo de producto, ignora la marca ALCAMPO
- Si el catálogo es marca_fabricante, la marca debe coincidir para score > 6
- Diferente formato/tamaño NO baja el score si el producto es el mismo
- Diferente categoría (ej: champú vs agua) = score 0 siempre

Devuelve ÚNICAMENTE un array JSON, sin texto adicional:
[
  {"id_catalogo": "CAT-xxxx", "id_alcampo": "AL-xxxx", "score": 8, "motivo": "mismo producto, distinto formato"},
  ...
]"""


def construir_clientes():
    if not all([SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY]):
        print("❌ ERROR: Faltan variables de entorno en .env")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY), anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def fetch_matches(supabase: Client) -> list:
    """Obtiene todos los matches ALCAMPO activos con sus nombres."""
    resultado = supabase.rpc("get_matches_alcampo_para_revision", {}).execute()
    
    # Si no existe la función RPC, usamos query directa paginada
    if hasattr(resultado, 'error') and resultado.error:
        return fetch_matches_paginado(supabase)
    
    return resultado.data


def fetch_matches_paginado(supabase: Client) -> list:
    """Obtiene matches haciendo tres queries separadas y cruzando los datos."""
    
    # 1. Obtener todos los matches activos
    print("  → Cargando productos_match...")
    matches_raw = []
    offset = 0
    while True:
        res = (
            supabase.table("productos_match")
            .select("id_catalogo, id_alcampo")
            .not_.is_("id_alcampo", "null")
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
    ids_alcampo = list({m["id_alcampo"] for m in matches_raw})

    # 2. Obtener datos del catálogo
    print("  → Cargando productos_catalogo...")
    catalogo = {}
    for i in range(0, len(ids_catalogo), 500):
        res = (
            supabase.table("productos_catalogo")
            .select("id, nombre_normalizado, tipo, marca")
            .in_("id", ids_catalogo[i:i+500])
            .execute()
        )
        for r in res.data:
            catalogo[r["id"]] = r

    # 3. Obtener datos de precios_alcampo
    print("  → Cargando precios_alcampo...")
    precios = {}
    for i in range(0, len(ids_alcampo), 500):
        res = (
            supabase.table("precios_alcampo")
            .select("id, nombre_comercial, marca, precio")
            .in_("id", ids_alcampo[i:i+500])
            .execute()
        )
        for r in res.data:
            precios[r["id"]] = r

    # 4. Cruzar todo
    resultado = []
    for m in matches_raw:
        cat = catalogo.get(m["id_catalogo"], {})
        alcampo = precios.get(m["id_alcampo"], {})
        resultado.append({
            "id_catalogo": m["id_catalogo"],
            "id_alcampo": m["id_alcampo"],
            "productos_catalogo": cat,
            "precios_alcampo": alcampo,
        })
    
    return resultado


def normalizar_matches(raw: list) -> list:
    """Aplana la estructura anidada de Supabase."""
    resultado = []
    for r in raw:
        cat = r.get("productos_catalogo") or {}
        alcampo = r.get("precios_alcampo") or {}
        
        # Supabase devuelve lista cuando hay JOIN, coger primer elemento
        if isinstance(cat, list):
            cat = cat[0] if cat else {}
        if isinstance(alcampo, list):
            alcampo = alcampo[0] if alcampo else {}
            
        resultado.append({
            "id_catalogo": r["id_catalogo"],
            "id_alcampo": r["id_alcampo"],
            "nombre_catalogo": cat.get("nombre_normalizado", ""),
            "tipo": cat.get("tipo", ""),
            "marca_catalogo": cat.get("marca", ""),
            "nombre_alcampo": alcampo.get("nombre_comercial", ""),
            "marca_alcampo": alcampo.get("marca", ""),
            "precio_alcampo": alcampo.get("precio", ""),
        })
    return resultado


def puntuar_lote(cliente: anthropic.Anthropic, matches: list) -> list:
    """Envía un lote a Claude para puntuar."""
    lineas = []
    for m in matches:
        marca_info = f" [marca catálogo: {m['marca_catalogo']}]" if m['marca_catalogo'] else ""
        lineas.append(
            f"{m['id_catalogo']} | {m['id_alcampo']} | "
            f"CATÁLOGO ({m['tipo']}): {m['nombre_catalogo']}{marca_info} | "
            f"ALCAMPO: {m['nombre_alcampo']} (marca: {m['marca_alcampo']})"
        )
    
    mensaje = cliente.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Puntúa estos {len(matches)} pares de productos:\n\n" + "\n".join(lineas)
        }]
    )
    
    texto = mensaje.content[0].text.strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1].rsplit("```", 1)[0]
    
    return json.loads(texto)


def main():
    parser = argparse.ArgumentParser(description="Puntúa matches ALCAMPO con IA")
    parser.add_argument("--dry-run", action="store_true", help="Solo procesa los primeros 30")
    parser.add_argument("--umbral", type=int, default=UMBRAL_DEFAULT,
                        help=f"Score mínimo para considerar correcto (default: {UMBRAL_DEFAULT})")
    args = parser.parse_args()

    modo = "🔍 DRY-RUN" if args.dry_run else "🤖 PRODUCCIÓN"
    print(f"\n{'='*60}")
    print(f"  revisar_matches_alcampo.py — {modo}")
    print(f"  Umbral de calidad: {args.umbral}/10")
    print(f"{'='*60}\n")

    supabase, cliente_ai = construir_clientes()

    print("🔎 Cargando matches ALCAMPO activos...")
    raw = fetch_matches_paginado(supabase)
    matches = normalizar_matches(raw)
    
    if args.dry_run:
        matches = matches[:30]
    
    total = len(matches)
    print(f"📦 Matches a revisar: {total}\n")

    # Procesar en lotes
    resultados = []
    procesados = 0

    for i in range(0, total, BATCH_SIZE):
        lote = matches[i:i + BATCH_SIZE]
        num_lote = (i // BATCH_SIZE) + 1
        total_lotes = (total + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"📤 Lote {num_lote}/{total_lotes}...", end=" ", flush=True)

        try:
            puntuaciones = puntuar_lote(cliente_ai, lote)
            
            # Combinar puntuaciones con datos originales
            puntuaciones_idx = {p["id_catalogo"]: p for p in puntuaciones}
            
            for m in lote:
                p = puntuaciones_idx.get(m["id_catalogo"], {})
                score = p.get("score", -1)
                motivo = p.get("motivo", "sin datos")
                
                resultados.append({**m, "score": score, "motivo": motivo})
                procesados += 1
            
            incorrectos_lote = sum(1 for p in puntuaciones if p.get("score", 10) < args.umbral)
            print(f"✅ ({procesados}/{total}) — incorrectos: {incorrectos_lote}")

        except json.JSONDecodeError as e:
            print(f"\n❌ Error JSON lote {num_lote}: {e}")
            for m in lote:
                resultados.append({**m, "score": -1, "motivo": "error_json"})
        except Exception as e:
            print(f"\n❌ Error lote {num_lote}: {e}")
            for m in lote:
                resultados.append({**m, "score": -1, "motivo": f"error: {str(e)}"})
            time.sleep(10)

        if i + BATCH_SIZE < total:
            time.sleep(SLEEP_ENTRE_LOTES)

    # Generar CSVs
    df = pd.DataFrame(resultados)
    df_sorted = df.sort_values("score")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    fichero_todos = f"matches_alcampo_revisados_{timestamp}.csv"
    fichero_malos = f"matches_alcampo_incorrectos_{timestamp}.csv"
    
    df_sorted.to_csv(fichero_todos, index=False)
    
    df_malos = df_sorted[df_sorted["score"] < args.umbral]
    df_malos.to_csv(fichero_malos, index=False)

    # Resumen
    print(f"\n{'='*60}")
    print(f"  RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"  Total revisados:     {len(df)}")
    print(f"  Score >= {args.umbral} (OK):     {len(df[df['score'] >= args.umbral])}")
    print(f"  Score <  {args.umbral} (MAL):    {len(df_malos)}")
    print(f"  Score -1 (error):    {len(df[df['score'] == -1])}")
    print(f"\n  Distribución de scores:")
    for score in sorted(df['score'].unique()):
        count = len(df[df['score'] == score])
        bar = '█' * (count // 5)
        print(f"    Score {score:2d}: {count:4d} {bar}")
    print(f"\n  📄 Todos los matches: {fichero_todos}")
    print(f"  ❌ Incorrectos:       {fichero_malos}")
    if args.dry_run:
        print(f"\n  ⚠️  DRY-RUN: ejecuta sin --dry-run para procesar los {207} matches completos.")
    else:
        print(f"\n  ➡️  Revisa {fichero_malos} y ejecuta el SQL de limpieza cuando estés listo.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
