"""
scraper_dia.py — DIA España → Supabase
Estrategia híbrida (patrón Carrefour):
  1) API de búsqueda DIA con curl_cffi + categorías dinámicas
  2) Fallback: Scrapling StealthyFetcher si la API falla
  3) Paginación con curl_cffi para páginas 2+

Tabla destino: precios_dia
IDs: DI-XXXX secuencial (mantiene IDs existentes en productos_match)
"""
import argparse, json, logging, os, re, time
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BASE_URL   = "https://www.dia.es"
API_SEARCH = f"{BASE_URL}/api/v1/search-back/search/reduced"
API_CATS   = f"{BASE_URL}/api/v1/search-back/categories"
TABLE_NAME = "precios_dia"
PREFIJO_ID = "DI"
PAGE_SIZE  = 100
DELAY      = 1.0
PAGINATION_DELAY = 0.5

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

CATEGORIES_FALLBACK = [
    ("01", "frutas-y-verduras",           "Frutas y verduras"),
    ("02", "carne-y-charcuteria",          "Carnes y charcutería"),
    ("03", "pescado-y-marisco",            "Pescado y marisco"),
    ("04", "lacteos-y-huevos",             "Lácteos y huevos"),
    ("05", "panaderia-y-bolleria",         "Panadería y bollería"),
    ("06", "congelados",                   "Congelados"),
    ("07", "bebidas",                      "Bebidas"),
    ("08", "bodega",                       "Bodega"),
    ("09", "aceite-vinagre-y-especias",    "Aceite, vinagre y especias"),
    ("10", "arroz-pasta-y-legumbres",      "Arroz, pasta y legumbres"),
    ("11", "conservas-y-platos-preparados","Conservas y platos preparados"),
    ("12", "salsas-y-condimentos",         "Salsas y condimentos"),
    ("13", "desayuno-y-merienda",          "Desayuno y merienda"),
    ("14", "aperitivos-y-snacks",          "Aperitivos y snacks"),
    ("15", "higiene-y-cosmetica",          "Higiene y cosmética"),
    ("16", "limpieza-del-hogar",           "Limpieza del hogar"),
    ("17", "bebes",                        "Bebés"),
    ("18", "mascotas",                     "Mascotas"),
]

UNIT_MAP = {
    "LITRO": "L", "LITROS": "L",
    "KILOGRAMO": "kg", "KILO": "kg", "KILOS": "kg",
    "GRAMO": "g", "GRAMOS": "g",
    "MILILITRO": "ml", "MILILITROS": "ml",
    "CENTILITRO": "cl", "CENTILITROS": "cl",
    "UNIDAD": "ud", "UNIDADES": "ud",
    "METRO": "m", "METROS": "m",
    "PIEZA": "ud", "PIEZAS": "ud",
    "DOCENA": "ud",
    "ROLLO": "ud", "ROLLOS": "ud",
    "TABLETA": "ud", "TABLETAS": "ud",
    "SOBRE": "ud", "SOBRES": "ud",
    "BOTELLA": "ud", "BOTELLAS": "ud",
    "LATA": "ud", "LATAS": "ud",
    "BRIK": "ud", "BRIKS": "ud",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": BASE_URL + "/",
}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("dia")

_http_session = curl_requests.Session(impersonate="chrome124")

# ─── CATEGORÍAS ──────────────────────────────────────────────────────────────

def get_categories():
    try:
        r = _http_session.get(API_CATS, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            cats = data if isinstance(data, list) else data.get("categories", [])
            if cats:
                result = []
                for c in cats:
                    cat_id   = str(c.get("id") or c.get("code") or "")
                    cat_name = str(c.get("name") or c.get("nombre") or "")
                    cat_slug = re.sub(r"[^a-z0-9]+", "-", cat_name.lower()).strip("-")
                    if cat_id:
                        result.append((cat_id, cat_slug, cat_name))
                if result:
                    log.info(f"  Categorias dinamicas: {len(result)}")
                    return result
    except Exception as e:
        log.debug(f"  categories API: {e}")
    log.info(f"  Usando categorias fallback: {len(CATEGORIES_FALLBACK)}")
    return CATEGORIES_FALLBACK

# ─── API (curl_cffi) ─────────────────────────────────────────────────────────

def try_api(cat_id, page=1, retries=2):
    params = {"categoryId": cat_id, "page": page, "pageSize": PAGE_SIZE}
    for attempt in range(retries):
        try:
            r = _http_session.get(API_SEARCH, params=params,
                                  headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data  = r.json()
                items = data.get("search_items", [])
                return items if items is not None else None
            log.debug(f"  API HTTP {r.status_code}")
        except Exception as e:
            log.debug(f"  API error: {e}")
        time.sleep(DELAY * (attempt + 1))
    return None

def extract_total_dia(data):
    pag = data.get("pagination", {}) if isinstance(data, dict) else {}
    return int(pag.get("total_pages", 1))

# ─── PARSEO ───────────────────────────────────────────────────────────────────

def parse_api_product(item):
    try:
        sku = str(item.get("sku_id") or item.get("object_id") or "").strip()
        if not sku:
            return None
        nombre = (item.get("display_name") or "").strip()
        if not nombre:
            return None

        precios = item.get("prices") or {}
        try:
            precio = float(precios.get("price") or 0)
        except Exception:
            precio = 0.0

        price_per_unit = precios.get("price_per_unit")
        measure_unit   = (precios.get("measure_unit") or "").strip().upper()
        unit_label     = UNIT_MAP.get(measure_unit,
                                      measure_unit.lower() if measure_unit else "")
        if price_per_unit and unit_label:
            precio_unidad = f"{float(price_per_unit):.2f}€/{unit_label}"
        elif price_per_unit:
            precio_unidad = f"{float(price_per_unit):.2f}€/ud"
        else:
            precio_unidad = ""

        ean = str(item.get("ean") or item.get("gtin") or "").strip()

        imagen = item.get("image") or ""
        if imagen and not imagen.startswith("http"):
            imagen = BASE_URL + imagen
        url = item.get("url") or ""
        if url and not url.startswith("http"):
            url = BASE_URL + url

        fmt_m = re.search(
            r'(\d+(?:[.,]\d+)?\s*(?:ml|l|g|kg|cl|ud|uds|pack)[\w\s]*)',
            nombre, re.IGNORECASE)
        formato = fmt_m.group(1).strip() if fmt_m else ""

        return {
            "id_api":           sku,
            "nombre_comercial": nombre,
            "precio":           round(precio, 2) if precio else None,
            "precio_unidad":    precio_unidad,
            "marca":            (item.get("brand") or "").strip(),
            "ean":              ean,
            "url":              url,
            "imagen":           imagen,
            "disponible":       True,
            "formato":          formato,
        }
    except Exception:
        return None

# ─── SCRAPLING (fallback) ────────────────────────────────────────────────────

def _scroll_and_wait(page):
    """Scroll to bottom and wait for content to load."""
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)

_stealthy_session = None

def get_stealthy_session():
    global _stealthy_session
    if _stealthy_session is None:
        from scrapling.fetchers import StealthySession
        log.info("    Abriendo navegador stealth (~5s)...")
        _stealthy_session = StealthySession(
            headless=True, solve_cloudflare=True,
            network_idle=True, block_webrtc=True,
            disable_resources=False,
        ).__enter__()
        log.info("    Navegador listo")
    return _stealthy_session

def close_stealthy_session():
    global _stealthy_session
    if _stealthy_session is not None:
        try:
            _stealthy_session.__exit__(None, None, None)
        except Exception:
            pass
        _stealthy_session = None

def extract_total_from_html(html):
    for pat in [r'"total"\s*:\s*(\d+)', r'"totalResults"\s*:\s*(\d+)',
                r'"total_pages"\s*:\s*(\d+)', r'(\d+)\s+productos']:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0

def extract_products_from_html(html):
    if not html:
        return []
    for pat in [r'"search_items"\s*:\s*(\[.*?\])\s*[,}]',
                r'"products"\s*:\s*(\[.*?\])\s*[,}]',
                r'window\["products"\]\s*=\s*(\[.*?\]);']:
        m = re.search(pat, html, re.DOTALL)
        if m:
            try:
                items = json.loads(m.group(1))
                prods = [parse_api_product(it) for it in items]
                prods = [p for p in prods if p]
                if prods:
                    return prods
            except Exception:
                pass
    soup  = BeautifulSoup(html, "html.parser")
    prods = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        for it in data.get("itemListElement", []) if isinstance(data, dict) else []:
            item = it.get("item", it)
            if item.get("@type") not in ("Product", "IndividualProduct"):
                continue
            p = _parse_jsonld_product_dia(item)
            if p:
                prods.append(p)
    if prods:
        return prods
    for sel in ['[data-testid="product-card"]', 'article.product-card',
                '[class*="product-card"]', '[data-pid]']:
        cards = soup.select(sel)
        if cards:
            for card in cards:
                p = _parse_html_card_dia(card)
                if p:
                    prods.append(p)
            break
    return prods

def _parse_jsonld_product_dia(item):
    try:
        offers = item.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = offers.get("price") or offers.get("lowPrice") or 0
        try:
            price = float(str(price).replace(",", "."))
        except Exception:
            price = 0.0
        sku = item.get("sku") or item.get("productID") or ""
        if not sku:
            url = item.get("url", "")
            m   = re.search(r"/(\d{4,})", url)
            sku = m.group(1) if m else ""
        if not sku:
            return None
        brand = item.get("brand") or {}
        brand = brand.get("name", "") if isinstance(brand, dict) else str(brand)
        return {
            "id_api":           sku,
            "nombre_comercial": (item.get("name") or "").strip(),
            "precio":           price,
            "precio_unidad":    "",
            "marca":            brand.strip(),
            "ean":              str(item.get("gtin13") or item.get("gtin") or "").strip(),
            "url":              item.get("url", ""),
            "imagen":           item.get("image", ""),
            "disponible":       "InStock" in str(offers.get("availability", "InStock")),
            "formato":          "",
        }
    except Exception:
        return None

def _parse_html_card_dia(card):
    try:
        pid = card.get("data-pid") or card.get("data-sku") or ""
        if not pid:
            link = card.find("a", href=True)
            if link:
                m   = re.search(r"/(\d{4,})", link["href"])
                pid = m.group(1) if m else ""
        if not pid:
            return None
        name_el = card.select_one('h2, h3, [class*="name"], [class*="title"]')
        name    = name_el.get_text(strip=True) if name_el else ""
        price   = 0.0
        price_el = card.select_one('[class*="price"], [itemprop="price"]')
        if price_el:
            txt = price_el.get_text(" ", strip=True)
            m   = re.search(r"(\d+[.,]\d{2})", txt)
            if m:
                try:
                    price = float(m.group(1).replace(",", "."))
                except Exception:
                    pass
        img_el = card.find("img")
        img    = img_el.get("src", "") if img_el else ""
        return {
            "id_api":           pid,
            "nombre_comercial": name,
            "precio":           price,
            "precio_unidad":    "",
            "marca":            "",
            "ean":              "",
            "url":              f"{BASE_URL}/p/{pid}",
            "imagen":           img,
            "disponible":       price > 0,
            "formato":          "",
        }
    except Exception:
        return None

def scrape_first_page(cat_id, cat_slug, retries=2, debug=False):
    url = f"{BASE_URL}/compra-online/{cat_slug}/{cat_id}/c"
    for attempt in range(retries):
        try:
            session = get_stealthy_session()
            page    = session.fetch(url, page_action=_scroll_and_wait, timeout=60000)
            if page and page.status == 200:
                html  = page.html_content
                total = extract_total_from_html(html)
                if debug:
                    with open(f"debug_dia_{cat_id}.html", "w", encoding="utf-8") as f:
                        f.write(html)
                return html, total
            log.warning(f"    Stealthy HTTP {page.status if page else 'None'} (intento {attempt+1})")
        except Exception as e:
            log.warning(f"    Stealthy error: {e} (intento {attempt+1})")
        time.sleep(DELAY * 2)
    return None, 0

def fetch_pagination_pages(cat_id, cat_slug, total_pages):
    all_products = []
    seen = set()
    for page in range(2, total_pages + 1):
        url = f"{BASE_URL}/compra-online/{cat_slug}/{cat_id}/c?page={page}"
        try:
            r = _http_session.get(url, headers=HEADERS, timeout=20)
            if r.status_code in (502, 503, 429):
                time.sleep(5)
                r = _http_session.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                break
            prods = extract_products_from_html(r.text)
            new   = [p for p in prods if p["id_api"] not in seen]
            seen.update(p["id_api"] for p in new)
            all_products.extend(new)
            if not new:
                break
        except Exception as e:
            log.warning(f"    pagina {page}: {e} -> parando")
            break
        time.sleep(PAGINATION_DELAY)
    return all_products

# ─── IDs SECUENCIALES ────────────────────────────────────────────────────────

def get_existing_id_map(client):
    mapa   = {}
    offset = 0
    while True:
        res = client.table(TABLE_NAME).select("id,id_api").range(offset, offset + 999).execute()
        for r in (res.data or []):
            if r.get("id_api"):
                mapa[r["id_api"]] = r["id"]
        if len(res.data or []) < 1000:
            break
        offset += 1000
    return mapa

def assign_ids(products, id_map):
    ultimo_num = max(
        (int(v.split("-")[1]) for v in id_map.values()
         if "-" in v and v.split("-")[1].isdigit()),
        default=0,
    )
    contador = ultimo_num
    resultado = []
    vistos    = set()
    for p in products:
        key = p["id_api"]
        if key in vistos:
            continue
        vistos.add(key)
        if key in id_map:
            p["id"] = id_map[key]
        else:
            contador += 1
            p["id"] = f"{PREFIJO_ID}-{contador:04d}"
        resultado.append(p)
    return resultado

# ─── SUPABASE ────────────────────────────────────────────────────────────────

def get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upsert(client, products):
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    for p in products:
        p["actualizado"] = now
    if not products:
        return 0
    res = client.table(TABLE_NAME).upsert(products, on_conflict="id_api").execute()
    return len(res.data) if res.data else len(products)

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main(dry_run=False, only_cat=None, force_stealth=False, debug=False):
    log.info("=" * 55)
    log.info("  SCRAPER DIA (hibrido API + Scrapling)")
    log.info("=" * 55)

    db     = None
    id_map = {}
    if not dry_run:
        try:
            db     = get_supabase()
            id_map = get_existing_id_map(db)
            log.info(f"Supabase conectado — {len(id_map)} IDs existentes")
        except Exception as e:
            log.warning(f"Supabase: {e} -> modo dry_run")
            dry_run = True

    categories = get_categories()
    if only_cat:
        categories = [(cid, sl, nm) for cid, sl, nm in categories
                      if only_cat in cid or only_cat in nm.lower()]
    log.info(f"{len(categories)} categorias\n")

    all_products = {}
    total_upserted = 0

    for cat_id, cat_slug, cat_name in categories:
        log.info(f"  {cat_name}  [{cat_id}]")
        products_raw = []

        if not force_stealth:
            log.info("    Intentando API DIA...")
            page = 1
            while True:
                items = try_api(cat_id, page=page)
                if not items:
                    break
                products_raw.extend(items)
                if len(items) < PAGE_SIZE:
                    break
                page += 1
                time.sleep(DELAY)
            if products_raw:
                log.info(f"    API: {len(products_raw)} items crudos")

        if not products_raw:
            log.info("    Fallback -> Scrapling")
            html, total_str = scrape_first_page(cat_id, cat_slug, debug=debug)
            page_products   = extract_products_from_html(html)
            if not page_products:
                log.info("    Sin productos\n")
                continue
            log.info(f"    Pag. 1: {len(page_products)} productos")
            total_pages_html = max(1, total_str // PAGE_SIZE + 1) if total_str else 1
            if total_pages_html > 1:
                extra = fetch_pagination_pages(cat_id, cat_slug, total_pages_html)
                page_products.extend(extra)
            parsed = page_products
        else:
            parsed = [parse_api_product(it) for it in products_raw]
            parsed = [p for p in parsed if p]

        nuevos = 0
        for p in parsed:
            if p["id_api"] not in all_products:
                all_products[p["id_api"]] = p
                nuevos += 1
        log.info(f"    +{nuevos} nuevos | total acumulado: {len(all_products)}")
        log.info("")
        time.sleep(DELAY)

    productos_lista = list(all_products.values())
    productos_lista = assign_ids(productos_lista, id_map)

    log.info("=" * 55)
    log.info(f"  Total productos : {len(productos_lista)}")

    if dry_run or not db:
        log.info("  [dry-run] Muestra:")
        for p in productos_lista[:5]:
            log.info(f"    {p['id']} | {p['nombre_comercial'][:45]} | "
                     f"{p.get('precio')}EUR | {p.get('precio_unidad')}")
    else:
        n = upsert(db, productos_lista)
        total_upserted = n
        log.info(f"  Total upserted  : {total_upserted}")

    log.info("=" * 55)
    close_stealthy_session()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run",  action="store_true")
    ap.add_argument("--cat",      help="Filtrar por ID o nombre de categoria")
    ap.add_argument("--stealth",  action="store_true")
    ap.add_argument("--debug",    action="store_true")
    args = ap.parse_args()
    try:
        main(dry_run=args.dry_run, only_cat=args.cat,
             force_stealth=args.stealth, debug=args.debug)
    finally:
        close_stealthy_session()
