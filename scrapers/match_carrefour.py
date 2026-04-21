"""
match_carrefour.py  —  Mi Mejor Cesta
=================================
Vincula productos_catalogo (CAT-xxxx) con precios_carrefour (CF-xxxx)
usando similitud de nombres con normalización agresiva (rapidfuzz).

Mejoras v3:
- Matching 1-a-1: cada producto Carrefour solo puede asignarse una vez
- Normalización agresiva: elimina marca, gramaje, descriptores
- Requiere coincidencia de al menos una palabra clave (>4 letras)
- Penalización por palabras ambiguas sin contexto adicional
- Score mínimo 85 para evitar falsos positivos

Uso:
  python match_carrefour.py --dry-run   # ver matches sin guardar
  python match_carrefour.py             # guardar matches en Supabase
"""

import argparse
import logging
import os
import re
import unicodedata
from dotenv import load_dotenv
from rapidfuzz import fuzz

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("matching")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SCORE_MIN  = 85   # umbral mínimo
SCORE_AUTO = 90   # match seguro
BATCH_SIZE = 50

PALABRAS_ELIMINAR = {
    "producto", "carrefour", "seleccion", "selección", "especial",
    "clasico", "clásico", "premium", "original", "nuevo", "nueva",
    "pack", "formato", "familiar", "ahorro", "oferta",
    "uds", "unidades", "unidad", "bolsa", "bote", "tarro", "lata",
    "caja", "sobre", "botella", "frasco", "tubo", "brik", "brick",
    "envase", "bandeja", "paquete", "sachet", "dosis",
    "con", "sin", "para", "del", "los", "las", "una", "unos",
    "este", "esta", "tipo", "sabor", "estilo",
}

MARCAS_CONOCIDAS = {
    "pompadour", "nestle", "nestlé", "danone", "activia", "actimel",
    "pascual", "puleva", "president", "président", "flora", "tulipan",
    "nutella", "nocilla", "cola cao", "nescafe", "lavazza",
    "bimbo", "buitoni", "barilla", "gallo", "hero", "knorr", "maggi",
    "heinz", "hellmanns", "calvé", "calve", "carbonell", "borges",
    "coca cola", "pepsi", "fanta", "sprite", "aquarius", "powerade",
    "font vella", "fontvella", "bezoya", "lanjaron", "evian",
    "mahou", "estrella", "cruzcampo", "moritz",
    "pringles", "lays", "doritos", "cheetos",
    "chips ahoy", "oreo", "principe", "fontaneda", "cuetara", "gullon",
    "colgate", "oral-b", "sensodyne", "listerine",
    "pantene", "garnier", "loreal", "nivea", "dove", "rexona", "sanex",
    "dodot", "pampers", "huggies",
    "ariel", "persil", "skip", "wipp", "fairy", "vim", "ajax", "domestos",
    "scottex", "kleenex", "renova",
    "almiron", "almirón", "nutriben",
    "grefusa", "chovi", "solis",
    "dani", "calvo", "isabel", "ortiz",
    "campofrio", "oscar mayer", "argal", "navidul",
    "palacios", "tarradellas", "findus", "pescanova",
    "waterwipes", "kandoo", "johnson", "nenuco", "denenes", "mustela",
    "hansaplast", "compeed", "santiveri", "bicentury",
    "mimosin", "lenor", "comfort", "lindt", "marbu", "fortaleza",
}

# Palabras ambiguas: si solo coincide esta palabra, no es match suficiente
AMBIGUAS = {
    "lomo", "filete", "agua", "leche", "yogur", "queso", "pan",
    "aceite", "zumo", "cerveza", "vino", "cafe", "chocolate",
    "galleta", "cereal", "pasta", "arroz", "atun", "salmon",
}


def quitar_acentos(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto)
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def normalizar(texto: str, es_carrefour: bool = False, marca: str = "") -> str:
    if not texto:
        return ""
    t = texto.lower()
    t = quitar_acentos(t)

    if es_carrefour:
        if marca:
            marca_norm = quitar_acentos(marca.lower())
            if t.startswith(marca_norm):
                t = t[len(marca_norm):].strip()
            t = t.replace(marca_norm, " ")
        for m in MARCAS_CONOCIDAS:
            t = re.sub(r'\b' + re.escape(m) + r'\b', ' ', t)

    # Eliminar gramajes
    t = re.sub(r"\b\d+\s*[xX×]\s*\d+[\.,]?\d*\s*(g|kg|ml|l|cl|ud|uds|unidades?)\b", "", t)
    t = re.sub(r"\b\d+[\.,]?\d*\s*(g|kg|ml|l|cl|ud|uds|unidades?)\b", "", t)
    t = re.sub(r"\b\d+\s*[xX×]\s*\d+\b", "", t)
    t = re.sub(r"\b\d+\b", "", t)

    palabras = t.split()
    palabras = [p for p in palabras if p not in PALABRAS_ELIMINAR and len(p) > 2]
    t = " ".join(palabras)
    t = re.sub(r"[^a-z\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def calcular_score(nombre_cat: str, nombre_cf: str, marca_cf: str = "") -> float:
    norm_cat = normalizar(nombre_cat)
    norm_cf  = normalizar(nombre_cf, es_carrefour=True, marca=marca_cf)

    if not norm_cat or not norm_cf:
        return 0.0

    palabras_cat = set(w for w in norm_cat.split() if len(w) > 4)
    palabras_cf  = set(w for w in norm_cf.split() if len(w) > 4)

    # REQUISITO: al menos una palabra clave debe coincidir
    if palabras_cat and palabras_cf:
        if not (palabras_cat & palabras_cf):
            return 0.0

    # PENALIZACIÓN: palabras ambiguas sin contexto adicional
    palabras_cat_todas = set(norm_cat.split())
    palabras_cf_todas  = set(norm_cf.split())
    ambiguas_cat = palabras_cat_todas & AMBIGUAS
    if ambiguas_cat:
        no_ambiguas_cat = {p for p in palabras_cat_todas if p not in AMBIGUAS and len(p) > 3}
        no_ambiguas_cf  = {p for p in palabras_cf_todas  if p not in AMBIGUAS and len(p) > 3}
        if no_ambiguas_cat and not (no_ambiguas_cat & no_ambiguas_cf):
            return 0.0

    score_set  = fuzz.token_set_ratio(norm_cat, norm_cf) / 100
    score_sort = fuzz.token_sort_ratio(norm_cat, norm_cf) / 100
    score_part = fuzz.partial_ratio(norm_cat, norm_cf) / 100

    return round(max(score_set, score_sort, score_part), 3)


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

    log.info("Cargando precios_carrefour...")
    carrefour, offset = [], 0
    while True:
        res = client.table("precios_carrefour") \
            .select("id, nombre_comercial, marca") \
            .range(offset, offset + 999).execute()
        if not res.data: break
        carrefour.extend(res.data)
        if len(res.data) < 1000: break
        offset += 1000
    log.info(f"  {len(carrefour)} productos en precios_carrefour")

    log.info("Cargando matches existentes...")
    matches, offset = [], 0
    while True:
        res = client.table("productos_match") \
            .select("id_catalogo, id_carrefour") \
            .range(offset, offset + 999).execute()
        if not res.data: break
        matches.extend(res.data)
        if len(res.data) < 1000: break
        offset += 1000
    ya_matched_cat = {m["id_catalogo"] for m in matches if m.get("id_carrefour")}
    ya_matched_cf  = {m["id_carrefour"] for m in matches if m.get("id_carrefour")}
    log.info(f"  {len(ya_matched_cat)} productos ya tienen match con Carrefour")

    return catalogo, carrefour, ya_matched_cat, ya_matched_cf


def hacer_matching(catalogo, carrefour, ya_matched_cat, ya_matched_cf):
    """Matching 1-a-1: primero todos los scores, luego asigna sin duplicados."""
    pendientes          = [p for p in catalogo  if str(p["id"]) not in ya_matched_cat]
    carrefour_disponible = [c for c in carrefour if c["id"] not in ya_matched_cf]

    log.info(f"\nCalculando scores: {len(pendientes)} catálogo vs {len(carrefour_disponible)} CF-...")

    todos_scores = []
    for i, prod in enumerate(pendientes, 1):
        nombre_cat = prod.get("nombre_generico", "") or ""
        for cf in carrefour_disponible:
            s = calcular_score(nombre_cat, cf.get("nombre_comercial", ""), cf.get("marca", ""))
            if s >= SCORE_MIN / 100:
                todos_scores.append({
                    "id_catalogo":      str(prod["id"]),
                    "id_carrefour":     cf["id"],
                    "score":            s,
                    "nombre_catalogo":  nombre_cat,
                    "nombre_carrefour": cf.get("nombre_comercial", ""),
                    "marca_carrefour":  cf.get("marca", ""),
                })
        if i % 200 == 0:
            log.info(f"  {i}/{len(pendientes)} procesados...")

    log.info(f"  {len(todos_scores)} pares candidatos")

    # Ordenar por score y asignar 1-a-1
    todos_scores.sort(key=lambda x: -x["score"])
    usados_cat, usados_cf = set(), set()
    resultados = []

    for par in todos_scores:
        if par["id_catalogo"] in usados_cat or par["id_carrefour"] in usados_cf:
            continue
        resultados.append({**par, "auto": par["score"] >= SCORE_AUTO / 100})
        usados_cat.add(par["id_catalogo"])
        usados_cf.add(par["id_carrefour"])

    auto    = sum(1 for r in resultados if r["auto"])
    revisar = len(resultados) - auto
    log.info(f"\n✅ Matches únicos: {len(resultados)}")
    log.info(f"  Auto (≥{SCORE_AUTO}):         {auto}")
    log.info(f"  Revisar ({SCORE_MIN}-{SCORE_AUTO}): {revisar}")
    log.info(f"  Sin match:             {len(pendientes) - len(resultados)}")

    return resultados


def guardar_matches(client, resultados, solo_auto=False):
    a_guardar = [r for r in resultados if not solo_auto or r["auto"]]
    log.info(f"\nGuardando {len(a_guardar)} matches...")
    guardados = 0
    for i in range(0, len(a_guardar), BATCH_SIZE):
        batch = a_guardar[i:i + BATCH_SIZE]
        updates = [{"id_catalogo": r["id_catalogo"], "id_carrefour": r["id_carrefour"]} for r in batch]
        try:
            client.table("productos_match").upsert(updates, on_conflict="id_catalogo").execute()
            guardados += len(batch)
        except Exception as e:
            log.error(f"Error: {e}")
    log.info(f"✅ {guardados} matches guardados")
    return guardados


def main(dry_run=False):
    log.info("━" * 55)
    log.info("  MATCHING CARREFOUR v1 → productos_match")
    log.info("━" * 55)

    client = get_supabase()
    catalogo, carrefour, ya_matched_cat, ya_matched_cf = cargar_datos(client)
    resultados = hacer_matching(catalogo, carrefour, ya_matched_cat, ya_matched_cf)

    log.info("\n📋 Top 30 mejores matches:")
    for r in sorted(resultados, key=lambda x: -x["score"])[:30]:
        tag = "✅ AUTO " if r["auto"] else "⚠️  REVISAR"
        log.info(f"  {tag} [{r['score']:.2f}] {r['nombre_catalogo'][:35]:<35} → {r['nombre_carrefour'][:45]}")

    log.info("\n📋 Matches con score más bajo (últimos 20):")
    for r in sorted(resultados, key=lambda x: x["score"])[:20]:
        log.info(f"  ⚠️  [{r['score']:.2f}] {r['nombre_catalogo'][:35]:<35} → {r['nombre_carrefour'][:45]}")

    if dry_run:
        log.info("\n[dry-run] No se guarda nada.")
        return

    auto_count = len([r for r in resultados if r["auto"]])
    resp = input(f"\n¿Guardar {auto_count} matches automáticos (score ≥{SCORE_AUTO})? (s/n): ")
    if resp.lower() == "s":
        guardar_matches(client, resultados, solo_auto=True)
        log.info(f"\n💡 {len(resultados) - auto_count} matches de score medio pendientes de revisión.")
    log.info("━" * 55)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    main(dry_run=args.dry_run)
