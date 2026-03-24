"""
matching_alcampo.py
Cruza productos_catalogo con precios_alcampo por similitud de nombre
y rellena la columna id_alcampo en productos_match.

Uso:
    python matching_alcampo.py --dry-run   # ver matches sin guardar
    python matching_alcampo.py             # guardar matches en Supabase

Pasos SQL previos en Supabase:
    ALTER TABLE productos_match ADD COLUMN IF NOT EXISTS id_alcampo TEXT;
    ALTER TABLE productos_match ADD COLUMN IF NOT EXISTS id_alcampo_score FLOAT;
"""

import argparse
import logging
import os
import re
import unicodedata
from difflib import SequenceMatcher
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("matching")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SCORE_MIN    = 0.72   # umbral mínimo para considerar un match válido
SCORE_AUTO   = 0.88   # por encima de esto se guarda automáticamente
BATCH_SIZE   = 50


def normalizar(texto: str) -> str:
    """Limpia y normaliza un nombre para comparación."""
    if not texto:
        return ""
    t = texto.lower()
    # Quitar acentos
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    # Quitar unidades y formatos comunes
    t = re.sub(r"\b(\d+[\.,]?\d*)\s*(g|kg|ml|l|cl|ud|uds|unidades?|pack|lata|bote|sobre|bolsa|caja|tarro)\b", "", t)
    # Quitar caracteres especiales
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    # Normalizar espacios
    t = re.sub(r"\s+", " ", t).strip()
    return t


def score(a: str, b: str) -> float:
    """Calcula similitud entre dos nombres normalizados."""
    na, nb = normalizar(a), normalizar(b)
    if not na or not nb:
        return 0.0
    # Similitud de secuencia
    seq = SequenceMatcher(None, na, nb).ratio()
    # Bonus si las palabras principales coinciden
    words_a = set(na.split())
    words_b = set(nb.split())
    if len(words_a) > 0 and len(words_b) > 0:
        overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
        return (seq * 0.6) + (overlap * 0.4)
    return seq


def get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def cargar_datos(client):
    log.info("Cargando catálogo...")
    catalogo = []
    offset = 0
    while True:
        res = client.table("vista_productos") \
            .select("id, nombre_generico, categoria, subcategoria") \
            .range(offset, offset + 999).execute()
        if not res.data:
            break
        catalogo.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    log.info(f"  {len(catalogo)} productos en catálogo")

    log.info("Cargando precios_alcampo...")
    alcampo = []
    offset = 0
    while True:
        res = client.table("precios_alcampo") \
            .select("id, nombre_comercial, categoria, marca") \
            .range(offset, offset + 999).execute()
        if not res.data:
            break
        alcampo.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    log.info(f"  {len(alcampo)} productos en precios_alcampo")

    log.info("Cargando matches existentes...")
    matches = []
    offset = 0
    while True:
        res = client.table("productos_match") \
            .select("id_catalogo, id_alcampo") \
            .range(offset, offset + 999).execute()
        if not res.data:
            break
        matches.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    ya_matched = {m["id_catalogo"] for m in matches if m.get("id_alcampo")}
    log.info(f"  {len(ya_matched)} productos ya tienen match con Alcampo")

    return catalogo, alcampo, ya_matched


def hacer_matching(catalogo, alcampo, ya_matched):
    """
    Para cada producto del catálogo sin match en Alcampo,
    busca el mejor candidato en precios_alcampo.
    """
    resultados = []
    sin_match  = 0

    pendientes = [p for p in catalogo if str(p["id"]) not in ya_matched]
    log.info(f"\nBuscando matches para {len(pendientes)} productos sin match...")

    for i, prod in enumerate(pendientes, 1):
        nombre_cat = prod.get("nombre_generico", "") or ""
        cat        = (prod.get("categoria") or "").lower()

        mejor_score = 0.0
        mejor_id    = None
        mejor_nombre = None

        for alc in alcampo:
            # Filtro rápido por categoría si está disponible
            if cat and alc.get("categoria"):
                cat_alc = alc["categoria"].lower()
                # Si las categorías son muy distintas, saltar
                palabras_cat = set(cat.split())
                palabras_alc = set(cat_alc.split())
                if not (palabras_cat & palabras_alc) and len(palabras_cat) > 1:
                    continue

            s = score(nombre_cat, alc.get("nombre_comercial", ""))
            if s > mejor_score:
                mejor_score = s
                mejor_id    = alc["id"]
                mejor_nombre = alc.get("nombre_comercial", "")

        if mejor_score >= SCORE_MIN:
            resultados.append({
                "id_catalogo":       str(prod["id"]),
                "id_alcampo":        mejor_id,
                "id_alcampo_score":  round(mejor_score, 3),
                "nombre_catalogo":   nombre_cat,
                "nombre_alcampo":    mejor_nombre,
                "auto":              mejor_score >= SCORE_AUTO,
            })
        else:
            sin_match += 1

        if i % 200 == 0:
            log.info(f"  {i}/{len(pendientes)} procesados...")

    auto    = sum(1 for r in resultados if r["auto"])
    revisar = len(resultados) - auto
    log.info(f"\n✅ Matches encontrados: {len(resultados)}")
    log.info(f"  Auto (≥{SCORE_AUTO}): {auto}")
    log.info(f"  Revisar ({SCORE_MIN}–{SCORE_AUTO}): {revisar}")
    log.info(f"  Sin match (<{SCORE_MIN}): {sin_match}")

    return resultados


def guardar_matches(client, resultados, solo_auto=False):
    """Guarda los matches en productos_match."""
    a_guardar = [r for r in resultados if not solo_auto or r["auto"]]
    log.info(f"\nGuardando {len(a_guardar)} matches en productos_match...")

    guardados = 0
    for i in range(0, len(a_guardar), BATCH_SIZE):
        batch = a_guardar[i:i + BATCH_SIZE]
        updates = [
            {
                "id_catalogo":      r["id_catalogo"],
                "id_alcampo":       r["id_alcampo"],
                "id_alcampo_score": r["id_alcampo_score"],
            }
            for r in batch
        ]
        try:
            client.table("productos_match") \
                .upsert(updates, on_conflict="id_catalogo").execute()
            guardados += len(batch)
        except Exception as e:
            log.error(f"Error guardando batch: {e}")

    log.info(f"✅ {guardados} matches guardados")
    return guardados


def main(dry_run=False, solo_auto=False):
    log.info("━" * 55)
    log.info("  MATCHING ALCAMPO → productos_match")
    log.info("━" * 55)

    client = get_supabase()
    catalogo, alcampo, ya_matched = cargar_datos(client)
    resultados = hacer_matching(catalogo, alcampo, ya_matched)

    # Mostrar muestra
    log.info("\n📋 Muestra de matches (top 20 por score):")
    for r in sorted(resultados, key=lambda x: -x["id_alcampo_score"])[:20]:
        tag = "✅ AUTO " if r["auto"] else "⚠️  REVISAR"
        log.info(f"  {tag} [{r['id_alcampo_score']:.2f}] "
                 f"{r['nombre_catalogo'][:35]:<35} → {r['nombre_alcampo'][:35]}")

    log.info("\n📋 Matches con score más bajo (últimos 10):")
    for r in sorted(resultados, key=lambda x: x["id_alcampo_score"])[:10]:
        log.info(f"  ⚠️  [{r['id_alcampo_score']:.2f}] "
                 f"{r['nombre_catalogo'][:35]:<35} → {r['nombre_alcampo'][:35]}")

    if dry_run:
        log.info("\n[dry-run] No se guarda nada.")
        return

    resp = input(f"\n¿Guardar {len([r for r in resultados if r['auto']])} matches automáticos? (s/n): ")
    if resp.lower() == "s":
        guardar_matches(client, resultados, solo_auto=True)
        log.info("\n💡 Los matches con score bajo quedan pendientes.")
        log.info("   Revísalos desde el panel admin y acepta/rechaza manualmente.")

    log.info("━" * 55)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Ver resultados sin guardar")
    ap.add_argument("--solo-auto", action="store_true", help="Guardar solo matches con score alto")
    args = ap.parse_args()
    main(dry_run=args.dry_run, solo_auto=args.solo_auto)
