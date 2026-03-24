"""
scraper_carrefour.py  —  Scraper Carrefour España → Supabase

Carrefour usa SAP Commerce (hybris) que tiene una API REST pública.
Endpoint base: https://www.carrefour.es/api/rest/v2/carrefouronline/

Estrategia:
  1. API de categorías → árbol completo con IDs
  2. API de productos por categoría → datos completos paginados
  3. Upsert en Supabase tabla precios_carrefour

Si la API falla → fallback a JSON-LD del HTML (igual que Alcampo)
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

from curl_cffi import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL   = "https://www.carrefour.es"
API_BASE   = f"{BASE_URL}/api/rest/v2/carrefouronline"
TABLE_NAME = "precios_carrefour"

PAGE_SIZE  = 48    # productos por página en la API de Carrefour
MAX_PAGES  = 200   # tope de seguridad
DELAY      = 0.6   # pausa entre peticiones

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Categorías principales con sus IDs y slugs
# Formato URL: /supermercado/{slug}/{cat_id}/c
CATEGORIES = {
    "cat20001":    ("La despensa",          "la-despensa"),
    "cat20002":    ("Frescos",              "frescos"),
    "cat20003":    ("Bebidas",              "bebidas"),
    "cat20004":    ("Perfumería e higiene", "perfumeria-e-higiene"),
    "cat20005":    ("Droguería y limpieza", "drogueria-y-limpieza"),
    "cat21449123": ("Congelados",           "congelados"),
    "cat20006":    ("Bebé",                 "bebe"),
    "cat20007":    ("Mascotas",             "mascotas"),
    "cat20008":    ("Parafarmacia",         "parafarmacia"),
}

# Cookies de sesión — actualizar periódicamente si dan 403
# (copiar de Chrome → DevTools → Application → Cookies → www.carrefour.es)
COOKIES = (
    "OptanonAlertBoxClosed=2026-02-03T00:35:55.612Z; "
    "eupubconsent-v2=CQfC7xgQfC7xgAcABBESCQFgAP7AAAAAAChQLewBQAKgAYABkAS0C3oAAAAA.f9gAAAAAAAAA.ILewBQAKgAYABkAS0C3o; "
    "_gcl_au=1.1.782886002.1770078956; "
    "_ga=GA1.1.29782969.1770078954; "
    "lantern=4e938cc3-5b46-49c7-bb2a-731ec340f1cc; "
    "session_id=3BMa07d6d1WawBYQfwrOEeleWQm; "
    "salepoint=005290||28232|A_DOMICILIO|1; "
    "_ga_KPXW54NX57=GS2.1.s1774301168$o10$g1$t1774301707$j59$l0$h0; "
    "ABTasty=uid=r4rvhjb68g656ndj&fst=1770078967008&pst=1773345258071&cst=1774301168645&ns=7&pvt=98&pvis=13; "
    "OptanonConsent=isGpcEnabled=0&datestamp=Mon+Mar+23+2026+22%3A35%3A07+GMT%2B0100&version=202510.1.0&browserGpcFlag=0&isIABGlobal=false&consentId=1167bf8a-6796-42f1-81c2-29e410f241c8&interactionCount=1&isAnonUser=1&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1"
)

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer":         BASE_URL + "/supermercado",
    "Cookie":          COOKIES,
}
HEADERS_HTML = {**HEADERS, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("carrefour")


# ── HTTP ──────────────────────────────────────────────────────────────────────

# Sesión persistente con impersonación de Chrome a nivel TLS (evita Cloudflare)
_session = requests.Session(impersonate="chrome124")

def get(url: str, params: dict = None, retries: int = 3) -> dict | list | None:
    for attempt in range(retries):
        try:
            r = _session.get(url, headers=HEADERS, params=params, timeout=20)
            if r.status_code == 200:
                return r.json()
            log.warning(f"HTTP {r.status_code}: {url}")
        except Exception as e:
            log.warning(f"Error ({attempt+1}/{retries}): {e}")
        time.sleep(DELAY * (attempt + 1))
    return None


def get_html(url: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            r = _session.get(url, headers=HEADERS_HTML, timeout=20)
            if r.status_code == 200:
                return r.text
            log.warning(f"HTTP {r.status_code}: {url}")
        except Exception as e:
            log.warning(f"Error ({attempt+1}/{retries}): {e}")
        time.sleep(DELAY * (attempt + 1))
    return None


def chunks(lst: list, n: int) -> Generator:
    it = iter(lst)
    while batch := list(islice(it, n)):
        yield batch


# ── Estrategia 1: API SAP Commerce (hybris) ───────────────────────────────────

def fetch_via_api(cat_id: str, cat_name: str) -> list[dict]:
    """
    Usa la API REST de SAP Commerce de Carrefour.
    Endpoint: /api/rest/v2/carrefouronline/products/search
    """
    products: list[dict] = {}
    page = 0

    while page < MAX_PAGES:
        data = get(
            f"{API_BASE}/products/search",
            params={
                "query":        f":relevance:allCategories:{cat_id}",
                "currentPage":  page,
                "pageSize":     PAGE_SIZE,
                "lang":         "es",
                "curr":         "EUR",
                "fields":       "FULL",
            }
        )

        if not data:
            break

        # La API devuelve {results: [...], pagination: {totalPages, ...}}
        results    = data.get("products") or data.get("results") or []
        pagination = data.get("pagination") or {}
        total_pages = pagination.get("totalPages", 1)

        if not results:
            break

        for raw in results:
            p = normalize_api(raw, cat_id)
            if p:
                products[p["id_api"]] = p

        log.info(f"    API página {page+1}/{total_pages}: {len(results)} productos (total: {len(products)})")

        if page + 1 >= total_pages:
            break

        page += 1
        time.sleep(DELAY)

    return list(products.values())


def normalize_api(raw: dict, cat_id: str) -> dict | None:
    """Normaliza un producto del API de SAP Commerce."""
    pid = str(raw.get("code") or raw.get("id") or "").strip()
    if not pid:
        return None

    # Precio
    price_data = raw.get("price") or {}
    precio = float(price_data.get("value") or price_data.get("formattedValue", "0")
                   .replace("€", "").replace(",", ".").strip() or 0)

    # Imagen
    images = raw.get("images") or []
    imagen = ""
    for img in images:
        if img.get("imageType") == "PRIMARY" or img.get("format") == "product":
            url_img = img.get("url", "")
            imagen = f"{BASE_URL}{url_img}" if url_img.startswith("/") else url_img
            break

    # Categorías
    cats = raw.get("categories") or []
    categoria = " > ".join(c.get("name", "") for c in cats if c.get("name"))

    return {
        "id":               f"CA-{pid}",
        "id_api":           pid,
        "nombre_comercial": (raw.get("name") or "").strip(),
        "precio":           precio,
        "marca":            (raw.get("brandName") or raw.get("brand") or "").strip(),
        "url":              f"{BASE_URL}/p/{pid}",
        "imagen":           imagen,
        "disponible":       raw.get("available", True),
        "categoria":        categoria or cat_id,
        "formato":          (raw.get("volumeField") or raw.get("netContent") or "").strip(),
    }


# ── Estrategia 2: HTML + JSON-LD (fallback, igual que Alcampo) ───────────────

def slug_to_name(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.replace("-", " ").split())


def get_product_urls_from_html(html: str) -> tuple[list[tuple[str, str]], int | None]:
    """Extrae URLs de producto del JSON-LD de una página de categoría."""
    soup  = BeautifulSoup(html, "html.parser")
    items: list[tuple[str, str]] = []
    total: int | None = None

    for pat in [r'"totalResults"\s*:\s*(\d+)', r'"total"\s*:\s*(\d+)',
                r'"numberOfResults"\s*:\s*(\d+)', r'"count"\s*:\s*(\d+)']:
        m = re.search(pat, html)
        if m:
            total = int(m.group(1))
            break

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        if data.get("@type") != "ItemList":
            continue
        for item in data.get("itemListElement", []):
            url = item.get("url", "")
            # Carrefour: /supermercado/.../nombre-producto/p/12345
            # o directamente /p/12345
            m = re.search(r"/p/([^/?#]+)$", url)
            if not m:
                m = re.search(r"/([^/?#]{5,})$", url)
            if m:
                pid  = m.group(1)
                slug = url.rstrip("/").split("/")[-2] if "/p/" in url else pid
                items.append((slug, pid))

    return items, total


def parse_product_html(html: str, pid: str, slug: str, cat_id: str) -> dict:
    """Extrae datos de producto desde su página HTML."""
    name    = slug_to_name(slug)
    price   = 0.0
    brand   = ""
    imagen  = ""
    formato = ""
    disponible = True

    soup = BeautifulSoup(html, "html.parser")

    # JSON-LD de producto
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        tipo = data.get("@type", "")
        if tipo not in ("Product", "IndividualProduct"):
            continue

        name   = data.get("name", name)
        imagen = data.get("image", imagen)
        if isinstance(imagen, list):
            imagen = imagen[0] if imagen else ""

        raw_brand = data.get("brand") or {}
        brand = raw_brand.get("name", brand) if isinstance(raw_brand, dict) else str(raw_brand)

        offers = data.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        p = offers.get("price") or offers.get("lowPrice")
        if p:
            try:
                price = float(str(p).replace(",", "."))
            except Exception:
                pass
        disponible = "InStock" in str(offers.get("availability", "InStock"))
        break

    # Precio en JSON embebido si no está en JSON-LD
    if price == 0.0:
        for pat in [r'"value"\s*:\s*([\d.]+)', r'"price"\s*:\s*"?([\d.,]+)"?',
                    r'([\d]+[.,][\d]{2})\s*€']:
            m = re.search(pat, html)
            if m:
                try:
                    price = float(m.group(1).replace(",", "."))
                    if price > 0:
                        break
                except Exception:
                    pass

    return {
        "id":               f"CA-{pid}",
        "id_api":           pid,
        "nombre_comercial": name.strip(),
        "precio":           price,
        "marca":            brand.strip(),
        "url":              f"{BASE_URL}/p/{pid}",
        "imagen":           imagen,
        "disponible":       disponible,
        "categoria":        cat_id,
        "formato":          formato,
    }


def fetch_via_html(cat_id: str, cat_name: str, slug: str) -> list[dict]:
    """Fallback: extrae productos del HTML como Alcampo."""
    all_items: dict[str, str] = {}
    max_pages = MAX_PAGES

    for page in range(max_pages):
        # Carrefour usa ?currentPage=N igual que Alcampo
        url  = f"{BASE_URL}/supermercado/{slug}/{cat_id}/c?currentPage={page}"
        html = get_html(url)
        if not html:
            break

        items, total = get_product_urls_from_html(html)

        if page == 0:
            if not items:
                log.warning(f"    Sin productos en JSON-LD — {url}")
                break
            if total:
                max_pages = min(math.ceil(total / PAGE_SIZE), MAX_PAGES)
                log.info(f"    HTML: {total} productos → {max_pages} páginas")

        new = {pid: s for s, pid in items if pid not in all_items}
        if not new:
            break

        all_items.update(new)
        log.info(f"    Página {page}: +{len(new)} (total: {len(all_items)})")
        time.sleep(DELAY)

    if not all_items:
        return []

    # Scraping de cada página de producto
    log.info(f"    Scrapeando {len(all_items)} páginas de producto...")
    products = []
    total_n  = len(all_items)

    for i, (pid, prod_slug) in enumerate(all_items.items(), 1):
        url  = f"{BASE_URL}/p/{pid}"
        html = get_html(url)
        if html:
            products.append(parse_product_html(html, pid, prod_slug, cat_id))
        else:
            products.append({
                "id": f"CA-{pid}", "id_api": pid,
                "nombre_comercial": slug_to_name(prod_slug),
                "precio": 0.0, "marca": "", "url": f"{BASE_URL}/p/{pid}",
                "imagen": "", "disponible": True, "categoria": cat_id, "formato": "",
            })
        if i % 10 == 0 or i == total_n:
            log.info(f"    {i}/{total_n} productos procesados")
        time.sleep(DELAY)

    return products


# ── Orquestador de categoría ──────────────────────────────────────────────────

def scrape_category(cat_id: str, cat_name: str, slug: str) -> list[dict]:
    log.info(f"    Intentando API SAP Commerce...")
    products = fetch_via_api(cat_id, cat_name)

    if products:
        log.info(f"    ✅ API: {len(products)} productos")
        return products

    log.info(f"    API sin datos → usando HTML + JSON-LD")
    products = fetch_via_html(cat_id, cat_name, slug)
    log.info(f"    HTML: {len(products)} productos")
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
    log.info("  SCRAPER CARREFOUR")
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
                log.info(f"      {p['id']} | {p['nombre_comercial'][:40]} | {p['precio']}€ | {p['marca']}")
            log.info("")

    log.info("━" * 55)
    log.info(f"  Total productos : {total_productos}")
    log.info(f"  Total upserted  : {total_upserted}")
    log.info("━" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--cat", help="Ej: cat20003")
    args = parser.parse_args()
    main(dry_run=args.dry_run, only_cat=args.cat)
