"""
match_alcampo_ia.py — Matching inteligente con Claude API
Cruza productos_catalogo con precios_alcampo usando IA.

Uso:
    python match_alcampo_ia.py --dry-run    # ver matches sin guardar
    python match_alcampo_ia.py              # guardar en Supabase
"""

import argparse, json, logging, os, time
import requests
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("match_ia")

SUPABASE_URL    = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY", "")
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
BATCH_CATALOGO  = 30   # productos del catálogo por llamada a la IA
MODEL           = "claude-sonnet-4-20250514"


def get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def cargar_datos(client):
    log.info("Cargando catálogo...")
    catalogo, offset = [], 0
    while True:
        res = client.table("vista_productos") \
            .select("id, nombre_generico, categoria, subcategoria") \
            .range(offset, offset + 999).execute()
        if not res.data: break
        catalogo.extend(res.data)
        if len(res.data) < 1000: break
        offset += 1000
    log.info(f"  {len(catalogo)} productos en catálogo")

    log.info("Cargando precios_alcampo...")
    alcampo, offset = [], 0
    while True:
        res = client.table("precios_alcampo") \
            .select("id, nombre_comercial, marca, categoria") \
            .range(offset, offset + 999).execute()
        if not res.data: break
        alcampo.extend(res.data)
        if len(res.data) < 1000: break
        offset += 1000
    log.info(f"  {len(alcampo)} productos en Alcampo")

    log.info("Cargando matches existentes...")
    matches, offset = [], 0
    while True:
        res = client.table("productos_match") \
            .select("id_catalogo, id_alcampo") \
            .range(offset, offset + 999).execute()
        if not res.data: break
        matches.extend(res.data)
        if len(res.data) < 1000: break
        offset += 1000
    ya_matched = {str(m["id_catalogo"]) for m in matches if m.get("id_alcampo")}
    log.info(f"  {len(ya_matched)} ya tienen match con Alcampo")

    return catalogo, alcampo, ya_matched


def match_con_ia(batch_catalogo, alcampo_list):
    """
    Llama a Claude con un lote de productos del catálogo y la lista completa
    de Alcampo para que encuentre los mejores matches.
    Devuelve: [{id_catalogo, id_alcampo, confianza, razon}]
    """
    # Preparar listas compactas para el prompt
    cat_txt = "\n".join(
        f"{p['id']}|{p['nombre_generico']}|{p.get('categoria','')}"
        for p in batch_catalogo
    )
    alc_txt = "\n".join(
        f"{p['id']}|{p['nombre_comercial']}|{p.get('marca','')}"
        for p in alcampo_list
    )

    prompt = f"""Eres un sistema de matching de productos de supermercado.

CATÁLOGO (formato: id|nombre_generico|categoria):
{cat_txt}

PRODUCTOS ALCAMPO (formato: id|nombre_comercial|marca):
{alc_txt}

TAREA: Para cada producto del CATÁLOGO, encuentra el producto de ALCAMPO que sea el mismo producto.

REGLAS:
- Solo hacer match si estás seguro de que es el mismo producto (mismo tipo, misma marca si aplica, mismo formato si es relevante)
- Si no hay match claro, devuelve id_alcampo: null
- No hagas match si el nombre es ambiguo o podría ser otro producto
- Ignora diferencias de capitalización y acentos

Responde SOLO con JSON válido, sin texto adicional, sin markdown:
[
  {{"id_catalogo": "X", "id_alcampo": "Y_o_null", "confianza": 0.0-1.0, "razon": "breve explicacion"}},
  ...
]"""

    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    body = {
        "model": MODEL,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}]
    }

    for attempt in range(3):
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers, json=body, timeout=60
            )
            if r.status_code == 200:
                content = r.json()["content"][0]["text"].strip()
                # Limpiar posibles backticks
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                return json.loads(content)
            else:
                log.warning(f"API error {r.status_code}: {r.text[:200]}")
        except Exception as e:
            log.warning(f"Error intento {attempt+1}: {e}")
        time.sleep(3 * (attempt + 1))
    return []


def guardar_matches(client, resultados):
    total = 0
    for i in range(0, len(resultados), 50):
        batch = resultados[i:i+50]
        updates = [
            {"id_catalogo": r["id_catalogo"], "id_alcampo": r["id_alcampo"]}
            for r in batch if r.get("id_alcampo")
        ]
        if not updates:
            continue
        for attempt in range(4):
            try:
                client.table("productos_match") \
                    .upsert(updates, on_conflict="id_catalogo").execute()
                total += len(updates)
                break
            except Exception as e:
                if attempt < 3:
                    time.sleep(5 * (attempt + 1))
                else:
                    log.error(f"Error guardando: {e}")
        time.sleep(0.3)
    return total


def main(dry_run=False, umbral=0.75):
    log.info("━" * 55)
    log.info(f"  MATCH ALCAMPO — IA (Claude) | umbral: {umbral}")
    log.info("━" * 55)

    if not ANTHROPIC_KEY:
        log.error("❌ Falta ANTHROPIC_API_KEY en el .env")
        return

    client = get_supabase()
    catalogo, alcampo, ya_matched = cargar_datos(client)

    # IDs de alcampo ya matcheados
    res = client.table("productos_match").select("id_alcampo").not_.is_("id_alcampo", "null").execute()
    alcampo_ya_matcheados = {r["id_alcampo"] for r in (res.data or [])}

    # Solo alcampo sin match — invertir la búsqueda
    alcampo_sin_match = [a for a in alcampo if a["id"] not in alcampo_ya_matcheados]
    log.info(f"{len(alcampo_sin_match)} productos Alcampo sin match")

    # Solo catálogo sin match en Alcampo
    pendientes = [p for p in catalogo if str(p["id"]) not in ya_matched]
    log.info(f"\n{len(pendientes)} productos pendientes de match")
    log.info(f"Procesando en lotes de {BATCH_CATALOGO}...\n")

    todos_resultados = []
    total_lotes = (len(pendientes) + BATCH_CATALOGO - 1) // BATCH_CATALOGO

    for i in range(0, len(pendientes), BATCH_CATALOGO):
        lote_num = i // BATCH_CATALOGO + 1
        batch    = pendientes[i:i + BATCH_CATALOGO]
        log.info(f"Lote {lote_num}/{total_lotes} ({len(batch)} productos)...")

        resultados = match_con_ia(batch, alcampo)

        con_match = [r for r in resultados if r.get("id_alcampo")]
        sin_match = [r for r in resultados if not r.get("id_alcampo")]

        log.info(f"  → {len(con_match)} matches / {len(sin_match)} sin match")

        # Mostrar los matches de este lote
        for r in con_match:
            # Buscar nombre en catálogo y alcampo
            nom_cat = next((p["nombre_generico"] for p in batch
                           if str(p["id"]) == str(r["id_catalogo"])), r["id_catalogo"])
            nom_alc = next((p["nombre_comercial"] for p in alcampo
                           if str(p["id"]) == str(r["id_alcampo"])), r["id_alcampo"])
            log.info(f"  ✅ [{r.get('confianza', 0):.2f}] {nom_cat[:35]:<35} → {nom_alc[:35]}")

        todos_resultados.extend(resultados)
        time.sleep(1)  # respetar rate limit

    # Resumen
    total_match    = len([r for r in todos_resultados if r.get("id_alcampo")])
    total_sin      = len([r for r in todos_resultados if not r.get("id_alcampo")])
    alta_confianza = len([r for r in todos_resultados
                         if r.get("id_alcampo") and r.get("confianza", 0) >= 0.85])

    log.info(f"\n{'━'*55}")
    log.info(f"  RESUMEN FINAL")
    log.info(f"{'━'*55}")
    log.info(f"  Total matches: {total_match}")
    log.info(f"  Alta confianza (≥0.85): {alta_confianza}")
    log.info(f"  Sin match: {total_sin}")

    if dry_run:
        log.info("\n[dry-run] No se guarda nada.")
        return

    if total_match == 0:
        log.info("Sin matches que guardar.")
        return

    resp = input(f"\n¿Guardar {total_match} matches en Supabase? (s/n): ")
    if resp.lower() == "s":
        n = guardar_matches(client, todos_resultados)
        log.info(f"✅ {n} matches guardados en productos_match")
    log.info("━" * 55)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--umbral", type=float, default=0.75, help="Umbral mínimo de confianza (0-1)")
    args = ap.parse_args()
    main(dry_run=args.dry_run, umbral=args.umbral)
