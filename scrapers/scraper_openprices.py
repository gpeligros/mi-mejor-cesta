"""
scraper_openprices.py — Open Prices (OpenFoodFacts) → Supabase
Filtra por país España y nombre de cadena.
API docs: https://prices.openfoodfacts.org/api/docs
"""

import argparse
import logging
import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE   = "https://prices.openfoodfacts.org/api/v1"
TABLE_NAME = "precios_openprices"
PAGE_SIZE  = 100
DELAY      = 0.4
MAX_PAGES  = 500  # tope de seguridad

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Nombre exacto como aparece en OpenStreetMap para cada cadena en España
# Si no da resultados, probar sin tilde o en inglés
SUPERMERCADOS = {
    "carrefour":  "Carrefour",
    "lidl":       "Lidl",
    "mercadona":  "Mercadona",
    "alcampo":    "Alcampo",
    "dia":        "Dia",
    "eroski":     "Eroski",
    "aldi":       "Aldi",
    "ahorramas":  "Ahorramás",
    "hipercor":   "Hipercor",
    "consum":     "Consum",
}

HEADERS = {
    "User-Agent": "MiMejorCesta/1.0 (contacto@mimejorcesta.es)",
    "Accept": "application/json",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("openprices")


def get_json(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=20)
            if r.status_code == 200:
                return r.json()
            log.warning(f"HTTP {r.status_code}: {url}")
        except Exception as e:
            log.warning(f"Error ({attempt+1}/{retries}): {e}")
        time.sleep(DELAY * (attempt + 1))
    return None


def fetch_prices(osm_name: str, country_code: str = "ES") -> list[dict]:
    """
    Descarga precios de una cadena en España.
    Usa location__osm_name__icontains para búsqueda parcial de nombre.
    """
    all_items: list[dict] = []
    page = 1
    total_pages = None

    while True:
        params = {
            "location__osm_name__icontains": osm_name,
            "location__osm_address_country_code": country_code,
            "currency": "EUR",
            "page": page,
            "size": PAGE_SIZE,
        }

        data = get_json(f"{API_BASE}/prices", params)
        if not data:
            break

        items      = data.get("items", [])
        total      = data.get("total", 0)
        total_pages = data.get("pages", 1)

        if not items:
            break

        all_items.extend(items)
        log.info(f"    Página {page}/{total_pages}: {len(items)} precios (total: {len(all_items)}/{total})")

        if page >= total_pages or page >= MAX_PAGES:
            break

        page += 1
        time.sleep(DELAY)

    return all_items


def normalize(item: dict, supermarket_key: str) -> dict | None:
    barcode = item.get("product_code", "")
    precio  = item.get("price")

    if not barcode or precio is None:
        return None

    try:
        precio = float(precio)
    except (TypeError, ValueError):
        return None

    # Nombre del producto
    nombre = (item.get("product_name") or
              (item.get("product") or {}).get("product_name") or
              barcode)

    # Marca
    prod   = item.get("product") or {}
    brands = prod.get("brands") or ""
    marca  = brands.split(",")[0].strip() if brands else ""

    # Imagen
    imagen = prod.get("image_url", "")

    # Categoría
    cats     = prod.get("categories_tags") or []
    categoria = cats[0].replace("en:", "").replace("-", " ").title() if cats else ""

    # Formato/cantidad
    formato = str(prod.get("product_quantity") or "")
    if formato and prod.get("product_quantity_unit"):
        formato = f"{formato} {prod['product_quantity_unit']}"

    # Localización
    loc   = item.get("location") or {}
    tienda = loc.get("osm_name", "") or loc.get("osm_display_name", "")

    # Fecha
    date_str = item.get("date") or datetime.utcnow().date().isoformat()

    return {
        "id":               f"OP-{supermarket_key[:3].upper()}-{barcode}",
        "id_api":           f"{supermarket_key}-{barcode}",
        "barcode":          barcode,
        "nombre_comercial": nombre.strip(),
        "precio":           precio,
        "marca":            marca,
        "supermercado":     supermarket_key,
        "tienda":           tienda[:200] if tienda else "",
        "url":              f"https://prices.openfoodfacts.org/product/{barcode}",
        "imagen":           imagen,
        "disponible":       True,
        "categoria":        categoria,
        "formato":          formato,
        "fecha_precio":     date_str,
    }


def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en el .env")
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert(client, prices: list[dict]) -> int:
    now = datetime.utcnow().isoformat()
    for p in prices:
        p["actualizado"] = now
    # Lotes de 200 (más pequeños = menos riesgo de timeout)
    total = 0
    for i in range(0, len(prices), 200):
        batch = prices[i:i+200]
        # Reintentos ante desconexiones de red (WinError 10054)
        for attempt in range(4):
            try:
                res = client.table(TABLE_NAME).upsert(batch, on_conflict="id_api").execute()
                total += len(res.data) if res.data else len(batch)
                break
            except Exception as e:
                if attempt < 3:
                    wait = 5 * (attempt + 1)
                    log.warning(f"Upsert error (intento {attempt+1}/4), reintentando en {wait}s: {e}")
                    time.sleep(wait)
                else:
                    log.error(f"Upsert fallido tras 4 intentos: {e}")
        time.sleep(0.2)  # pausa entre lotes
    return total


def main(dry_run=False, only_super=None):
    log.info("━" * 55)
    log.info("  SCRAPER OPEN PRICES")
    log.info("━" * 55)

    db = None
    if not dry_run:
        try:
            db = get_supabase()
            log.info("✅ Supabase conectado")
        except Exception as e:
            log.warning(f"⚠️  {e} → dry_run")
            dry_run = True

    supers = {only_super: SUPERMERCADOS[only_super]} \
             if only_super and only_super in SUPERMERCADOS \
             else SUPERMERCADOS

    log.info(f"📋 {len(supers)} supermercados\n")

    total_p = total_u = 0

    for key, osm_name in supers.items():
        log.info(f"🏪  {osm_name} [{key}]")

        raw_items = fetch_prices(osm_name)

        if not raw_items:
            # Intentar con nombre en inglés / sin tilde
            alt = osm_name.replace("á", "a").replace("é", "e").replace("ó", "o")
            if alt != osm_name:
                log.info(f"    Reintentando con '{alt}'...")
                raw_items = fetch_prices(alt)

        if not raw_items:
            log.info(f"    Sin datos para {osm_name} en Open Prices España\n")
            continue

        # Normalizar y filtrar duplicados por barcode (quedarse con precio más reciente)
        by_barcode: dict[str, dict] = {}
        for item in raw_items:
            p = normalize(item, key)
            if not p:
                continue
            existing = by_barcode.get(p["barcode"])
            if not existing or p["fecha_precio"] > existing["fecha_precio"]:
                by_barcode[p["barcode"]] = p

        prices = list(by_barcode.values())
        log.info(f"    {len(raw_items)} precios → {len(prices)} productos únicos")
        total_p += len(prices)

        if not dry_run and db:
            n = upsert(db, prices)
            total_u += n
            log.info(f"    ✅ {n} upserted\n")
        else:
            log.info("    [dry-run] muestra:")
            for p in prices[:5]:
                log.info(f"      {p['barcode']} | {p['nombre_comercial'][:35]} | {p['precio']}€ | {p['fecha_precio']}")
            log.info("")

    log.info("━" * 55)
    log.info(f"  Total productos : {total_p}")
    log.info(f"  Total upserted  : {total_u}")
    log.info("━" * 55)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--super", help="carrefour, lidl, mercadona...")
    args = ap.parse_args()
    main(dry_run=args.dry_run, only_super=args.super)
