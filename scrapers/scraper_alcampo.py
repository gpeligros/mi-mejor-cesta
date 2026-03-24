"""
scraper_alcampo.py  —  Scraper Alcampo → Supabase

Estrategia:
  1. HTML de categoría → JSON-LD → lista de URLs de producto (slug + ID)
  2. HTML de cada producto → precio, marca, imagen, formato
  3. Upsert en Supabase tabla precios_alcampo
"""

import argparse
import json
import logging
import math
import os
import re
import time
from itertools import islice
from typing import Generator

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL   = "https://www.compraonline.alcampo.es"
TABLE_NAME = "precios_alcampo"

PRODUCTS_PER_PAGE = 50    # productos por página de categoría (vimos 50 en el log)
MAX_PAGES         = 100   # tope de seguridad
DELAY_CAT         = 1.0   # pausa entre páginas de categoría
DELAY_PROD        = 0.4   # pausa entre páginas de producto

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# {cat_id: (nombre, slug)}
# Slug = path de la URL de Alcampo después de /categories/
CATEGORIES = {
    # Alimentación
    "OC10":       ("Desayuno y merienda",         "desayuno-y-merienda"),
    "OC16":       ("Lácteos y bebidas vegetales", "leche-huevos-lacteos-yogures-y-bebidas-vegetales"),
    "OC2112":     ("Frescos",                     "frescos"),
    "OC20022018": ("Comida preparada",            "comida-preparada"),
    "OC1102":     ("Zumos",                       "bebidas/zumos-de-frutas"),
    "OC1101":     ("Agua y refrescos",            "bebidas/agua-y-refrescos"),
    "OC1701":     ("Fruta fresca",                "frutas-y-verduras/fruta-fresca"),
    "OC1401":     ("Pescado fresco",              "pescado-y-marisco/pescado-fresco"),
    "OC100302":   ("Frutos secos",                "alimentacion/frutos-secos-y-snacks"),
    "OC1001":     ("Leche",                       "leche-huevos-lacteos-yogures-y-bebidas-vegetales/leche"),
    "OCSINGSINL": ("Sin gluten / Sin lactosa",    "sin-gluten-sin-lactosa-nutricion-deportiva-y-funcional"),
    # Droguería, perfumería y bebé
    "OCC14":      ("Droguería",                   "drogueria"),
    "OC70":       ("Perfumería",                  "perfumeria"),
    "OCC13":      ("Bebé",                        "bebe"),
    "OC69":       ("Parafarmacia",                "parafarmacia"),
    "OC062":      ("Mascotas",                    "mascotas"),
}

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer":         BASE_URL + "/",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("alcampo")


# ── HTTP ──────────────────────────────────────────────────────────────────────

def get_html(url: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.text
            log.warning(f"HTTP {r.status_code}: {url}")
        except Exception as e:
            log.warning(f"Error ({attempt+1}/{retries}): {e}")
        time.sleep(1.5 * (attempt + 1))
    return None


# ── Parseo de página de categoría → URLs de producto ─────────────────────────

def get_product_urls_from_category(html: str) -> tuple[list[tuple[str,str]], int | None]:
    """
    Extrae lista de (slug_completo, id) desde el JSON-LD de la página de categoría.
    También devuelve el total de productos si está disponible.
    Formato URL: /products/nombre-del-producto/12345
    """
    soup  = BeautifulSoup(html, "html.parser")
    items: list[tuple[str, str]] = []

    # Total de productos para calcular páginas
    total: int | None = None
    for pat in [r'"totalResults"\s*:\s*(\d+)', r'"total"\s*:\s*(\d+)',
                r'"totalProducts"\s*:\s*(\d+)', r'"numberOfResults"\s*:\s*(\d+)']:
        m = re.search(pat, html)
        if m:
            total = int(m.group(1))
            break

    # JSON-LD con el listado de productos
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue

        if data.get("@type") != "ItemList":
            continue

        for item in data.get("itemListElement", []):
            url = item.get("url", "")
            # Formato: .../products/slug-del-producto/12345
            m = re.search(r"/products/([^/]+)/(\d+)$", url)
            if m:
                slug, pid = m.group(1), m.group(2)
                items.append((slug, pid))

    return items, total


def slug_to_name(slug: str) -> str:
    """Convierte 'don-simon-zumo-de-naranja-100-1-l' → 'Don Simon Zumo De Naranja 100 1 L'"""
    return " ".join(w.capitalize() for w in slug.replace("-", " ").split())


def get_subcategories(cat_id: str, slug: str) -> list[tuple[str, str]]:
    """
    Descubre subcategorías desde la página de una categoría.
    Devuelve lista de (subcat_id, subcat_slug).
    Si la categoría tiene productos directos, devuelve la propia categoría.
    """
    url  = f"{BASE_URL}/categories/{slug}/{cat_id}"
    html = get_html(url)
    if not html:
        return [(cat_id, slug)]

    # Ver si tiene productos directos (JSON-LD ItemList con productos)
    items, _ = get_product_urls_from_category(html)
    if items:
        return [(cat_id, slug)]  # tiene productos propios, no necesita subcategorías

    # Buscar links a subcategorías en el HTML
    # Formato: /categories/slug-padre/slug-hijo/OCXXXX
    soup = BeautifulSoup(html, "html.parser")
    subcats: list[tuple[str, str]] = []
    seen: set[str] = set()

    cat_re = re.compile(r"^/categories/(.+)/(OC[^/?#]+|OCSINGSINL)$")
    for a in soup.find_all("a", href=True):
        href = a["href"].rstrip("/").split("?")[0]
        m    = cat_re.match(href)
        if m:
            subslug, subid = m.group(1), m.group(2)
            if subid not in seen and subid != cat_id:
                seen.add(subid)
                subcats.append((subid, subslug))

    if subcats:
        log.info(f"    → {len(subcats)} subcategorías encontradas en {cat_id}")
        return subcats

    # Sin subcategorías ni productos — devolver la propia por si acaso
    return [(cat_id, slug)]


# ── Parseo de página de producto → precio, marca, etc. ───────────────────────

def parse_product_page(html: str, pid: str, slug: str, cat_id: str) -> dict:
    """
    Extrae precio, marca, imagen y formato de la página individual del producto.
    """
    # Nombre desde el slug como base (se sobreescribe si hay mejor fuente)
    name = slug_to_name(slug)

    price    = 0.0
    brand    = ""
    imagen   = ""
    formato  = ""
    disponible = True

    # ── Precio ────────────────────────────────────────────────────────────────
    # Buscar en JSON embebido primero (más fiable)
    price_patterns = [
        r'"amount"\s*:\s*"?([\d]+[.,][\d]{1,2})"?',
        r'"price"\s*:\s*"?([\d]+[.,][\d]{1,2})"?',
        r'"currentPrice"\s*:\s*"?([\d]+[.,][\d]{1,2})"?',
        r'([\d]+[.,][\d]{2})\s*€',
    ]
    for pat in price_patterns:
        m = re.search(pat, html)
        if m:
            try:
                price = float(m.group(1).replace(",", "."))
                if price > 0:
                    break
            except Exception:
                pass

    # ── Marca ─────────────────────────────────────────────────────────────────
    brand_patterns = [
        r'"brand"\s*:\s*["{](?:"name"\s*:\s*)?"([^"]+)"',
        r'"manufacturer"\s*:\s*"([^"]+)"',
        r'"brand"\s*:\s*\{\s*"name"\s*:\s*"([^"]+)"',
    ]
    for pat in brand_patterns:
        m = re.search(pat, html)
        if m:
            brand = m.group(1).strip()
            break

    # ── Nombre más preciso desde JSON-LD de producto ──────────────────────────
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        if data.get("@type") in ("Product", "IndividualProduct"):
            name    = data.get("name", name)
            raw_brand = data.get("brand") or {}
            if isinstance(raw_brand, dict):
                brand = raw_brand.get("name", brand) or brand
            elif isinstance(raw_brand, str):
                brand = raw_brand or brand
            imagen  = data.get("image", imagen)
            # Precio desde offers
            offers  = data.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            p = offers.get("price") or offers.get("lowPrice")
            if p:
                try:
                    price = float(str(p).replace(",", "."))
                except Exception:
                    pass
            disponible = offers.get("availability", "").endswith("InStock") if offers else True
            break

    # ── Imagen ────────────────────────────────────────────────────────────────
    if not imagen:
        m = re.search(r'"image"\s*:\s*"(https?://[^"]+)"', html)
        if m:
            imagen = m.group(1)

    # ── Formato ───────────────────────────────────────────────────────────────
    # Extraer de la última parte del nombre: "1 L", "400 g", "6 x 200 ml", etc.
    fmt_m = re.search(r'(\d+[\s,.]?\d*\s*(?:ml|l|g|kg|cl|ud|uds|x\s*\d+)[\w\s]*?)(?:\s*[/,]|$)',
                      name, re.IGNORECASE)
    if fmt_m:
        formato = fmt_m.group(1).strip()

    return {
        "id":               f"AL-{pid}",
        "id_api":           pid,
        "nombre_comercial": name.strip(),
        "precio":           price,
        "marca":            brand.strip(),
        "url":              f"{BASE_URL}/products/{slug}/{pid}",
        "imagen":           imagen,
        "disponible":       disponible,
        "categoria":        cat_id,
        "formato":          formato,
    }


# ── Scraping de categoría ─────────────────────────────────────────────────────

def scrape_category(cat_id: str, cat_name: str, slug: str) -> list[dict]:
    # Descubrir subcategorías automáticamente si la categoría es top-level
    subcats = get_subcategories(cat_id, slug)

    # Paso 1: recopilar todas las URLs de producto de todas las subcategorías
    all_items: dict[str, str] = {}  # {pid: slug_producto}

    for subcat_id, subcat_slug in subcats:
        max_pages = MAX_PAGES

        for page in range(max_pages):
            url  = f"{BASE_URL}/categories/{subcat_slug}/{subcat_id}?currentPage={page}"
            html = get_html(url)
            if not html:
                break

            items, total = get_product_urls_from_category(html)

            if page == 0:
                if not items:
                    break
                if total:
                    max_pages = min(math.ceil(total / PRODUCTS_PER_PAGE), MAX_PAGES)
                    if len(subcats) == 1:
                        log.info(f"    {total} productos → {max_pages} páginas")
                    else:
                        log.info(f"    [{subcat_id}] {total} productos → {max_pages} páginas")

            new_items = {pid: s for s, pid in items if pid not in all_items}
            if not new_items:
                break

            all_items.update(new_items)
            time.sleep(DELAY_CAT)

    log.info(f"    {len(all_items)} productos únicos encontrados")

    if not all_items:
        return []

    # Paso 2: scraping de cada página de producto para obtener precio y marca
    log.info(f"    Scrapeando {len(all_items)} páginas de producto...")
    products: list[dict] = []
    total_items = len(all_items)

    for i, (pid, prod_slug) in enumerate(all_items.items(), 1):
        prod_url  = f"{BASE_URL}/products/{prod_slug}/{pid}"
        prod_html = get_html(prod_url)

        if prod_html:
            p = parse_product_page(prod_html, pid, prod_slug, cat_id)
            products.append(p)
            if i % 10 == 0 or i == total_items:
                log.info(f"    {i}/{total_items} productos procesados")
        else:
            # Sin HTML: guardamos con nombre del slug al menos
            products.append({
                "id":               f"AL-{pid}",
                "id_api":           pid,
                "nombre_comercial": slug_to_name(prod_slug),
                "precio":           0.0,
                "marca":            "",
                "url":              f"{BASE_URL}/products/{prod_slug}/{pid}",
                "imagen":           "",
                "disponible":       True,
                "categoria":        cat_id,
                "formato":          "",
            })

        time.sleep(DELAY_PROD)

    return products


# ── Supabase ──────────────────────────────────────────────────────────────────

def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en el .env")
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert(client, products: list[dict]) -> int:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    for p in products:
        p["actualizado"] = now
    res = client.table(TABLE_NAME).upsert(products, on_conflict="id_api").execute()
    return len(res.data) if res.data else len(products)


# ── Main ──────────────────────────────────────────────────────────────────────

def main(dry_run: bool = False, only_cat: str | None = None):
    log.info("━" * 55)
    log.info("  SCRAPER ALCAMPO")
    log.info("━" * 55)

    db = None
    if not dry_run:
        try:
            db = get_supabase()
            log.info("✅ Supabase conectado")
        except Exception as e:
            log.warning(f"⚠️  Supabase no disponible ({e}) → dry_run activado")
            dry_run = True

    categories = CATEGORIES
    if only_cat:
        categories = {only_cat: CATEGORIES.get(only_cat, (only_cat, ""))}

    log.info(f"📋 {len(categories)} categorías\n")

    total_productos = 0
    total_upserted  = 0

    for cat_id, (cat_name, slug) in categories.items():
        log.info(f"📦  {cat_name}  [{cat_id}]")

        if not slug:
            log.warning(f"    Sin slug — añádelo en CATEGORIES")
            continue

        products = scrape_category(cat_id, cat_name, slug)

        if not products:
            log.info("    Sin productos.\n")
            continue

        log.info(f"    {len(products)} productos listos")
        total_productos += len(products)

        if not dry_run and db:
            n = upsert(db, products)
            total_upserted += n
            log.info(f"    ✅ {n} filas upserted\n")
        else:
            log.info(f"    [dry-run] muestra:")
            for p in products[:5]:
                log.info(f"      {p['id']} | {p['nombre_comercial'][:45]} | {p['precio']}€ | {p['marca']}")
            log.info("")

    log.info("━" * 55)
    log.info(f"  Total productos : {total_productos}")
    log.info(f"  Total upserted  : {total_upserted}")
    log.info("━" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--cat", help="Ej: OC1102")
    args = parser.parse_args()
    main(dry_run=args.dry_run, only_cat=args.cat)
