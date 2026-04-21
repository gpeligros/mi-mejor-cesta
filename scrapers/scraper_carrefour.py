"""
scraper_carrefour.py — Carrefour España → Supabase
Estrategia híbrida:
  1) Intenta API SAP Commerce (/api/rest/v2/carrefouronline/products/search)
     → rápido con curl_cffi + impersonate, por si Cloudflare está relajado.
  2) Si falla (HTTP 5xx, timeout, 0 productos) → fallback a Scrapling
     StealthyFetcher con solve_cloudflare=True + scroll para cargar toda la SPA.

Mantiene la MISMA estructura que scraper_hipercor.py (CONTEXTO.md rule).
ID producto: código numérico interno de Carrefour con prefijo CF-
Tabla destino: precios_carrefour
"""
import argparse, json, logging, os, re, time
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────
BASE_URL   = "https://www.carrefour.es"
API_URL    = f"{BASE_URL}/api/rest/v2/carrefouronline/products/search"
TABLE_NAME = "precios_carrefour"
PAGE_SIZE  = 40
MAX_PAGES  = 100
DELAY      = 2.5
PAGINATION_DELAY = 1.0   # segundos entre páginas de paginación via curl_cffi
PER_PAGE   = 24          # productos por página en la SPA de Carrefour
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Categorías top. Si alguna URL cambia, se detecta al scrapear.
CATEGORIES = [
    ("la-despensa",          "cat20001",   "La despensa"),
    ("frescos",              "cat20002",   "Frescos"),
    ("bebidas",              "cat20003",   "Bebidas"),
    ("perfumeria-e-higiene", "cat20004",   "Perfumería e higiene"),
    ("drogueria-y-limpieza", "cat20005",   "Droguería y limpieza"),
    ("congelados",           "cat21449123","Congelados"),
    ("bebe",                 "cat20006",   "Bebé"),
    ("mascotas",             "cat20007",   "Mascotas"),
    ("parafarmacia",         "cat20008",   "Parafarmacia"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json,text/html,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": BASE_URL,
}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("carrefour")

# ─────────────────────────────────────────────────────────
# SESIÓN HTTP (curl_cffi) — intento rápido
# ─────────────────────────────────────────────────────────
_http_session = curl_requests.Session(impersonate="chrome124")

def try_api(category_id, page=0, retries=2):
    """Intenta API SAP Commerce. Devuelve lista de productos o None si falla."""
    params = {
        "query": f":relevance:category:{category_id}",
        "fields": "FULL",
        "pageSize": PAGE_SIZE,
        "currentPage": page,
    }
    for attempt in range(retries):
        try:
            r = _http_session.get(API_URL, params=params,
                                  headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                products = data.get("products", [])
                return products if products else None
            log.debug(f"API HTTP {r.status_code}")
        except Exception as e:
            log.debug(f"API error: {e}")
        time.sleep(DELAY * (attempt + 1))
    return None

# ─────────────────────────────────────────────────────────
# SCRAPLING — fallback con navegador stealth
# ─────────────────────────────────────────────────────────
_stealthy_session = None  # Lazy init (tarda ~5s en abrir)

def get_stealthy_session():
    """Inicializa StealthySession solo cuando se necesita."""
    global _stealthy_session
    if _stealthy_session is None:
        from scrapling.fetchers import StealthySession
        log.info("    🦊 Abriendo navegador stealth (primera vez, ~5s)...")
        _stealthy_session = StealthySession(
            headless=True,
            solve_cloudflare=True,
            network_idle=True,
            block_webrtc=True,
            disable_resources=False,  # necesitamos JS y CSS para que la SPA monte
            capture_xhr="search-api",  # captura llamadas al API EmpathyX durante el scroll
        ).__enter__()
        log.info("    ✅ Navegador listo")
    return _stealthy_session

def close_stealthy_session():
    global _stealthy_session
    if _stealthy_session is not None:
        try:
            _stealthy_session.__exit__(None, None, None)
        except Exception:
            pass
        _stealthy_session = None

def scroll_and_wait(page):
    """page_action: scroll mínimo para que la SPA monte el primer lote de productos."""
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)

def extract_total_count(html):
    """Extrae el total de productos anunciado en la página."""
    m = re.search(r'"offerCount"\s*:\s*"(\d+)"', html)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)\s+productos', html, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 0

def scrape_first_page(slug, cat_id, retries=2, debug=False):
    """Renderiza la primera página con Scrapling. Devuelve (html, total_count)."""
    url = f"{BASE_URL}/supermercado/{slug}/{cat_id}/c"
    for attempt in range(retries):
        try:
            session = get_stealthy_session()
            page = session.fetch(url, page_action=scroll_and_wait, timeout=60000)
            if page and page.status == 200:
                html = page.html_content
                total = extract_total_count(html)
                if debug:
                    with open(f"debug_carrefour_{slug}.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    log.info(f"    💾 HTML guardado ({len(html)} bytes)")
                return html, total
            log.warning(f"    Stealthy HTTP {page.status if page else 'None'} (intento {attempt+1})")
        except Exception as e:
            log.warning(f"    Stealthy error: {e} (intento {attempt+1})")
        time.sleep(DELAY * 2)
    return None, 0

def fetch_pagination_pages(slug, cat_id, total):
    """Obtiene las páginas 2-N via curl_cffi directo (rápido, sin browser)."""
    seen = set()
    all_products = []
    pages_fetched = 0
    for offset in range(PER_PAGE, total, PER_PAGE):
        url = f"{BASE_URL}/supermercado/{slug}/{cat_id}/c?offset={offset}"
        try:
            r = _http_session.get(url, headers=HEADERS, timeout=20)
            if r.status_code in (502, 503, 429):
                log.debug(f"    offset={offset}: HTTP {r.status_code} → reintentando en 5s")
                time.sleep(5)
                r = _http_session.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 403:
                log.info(f"    offset={offset}: HTTP 403 → esperando 60s y reintentando...")
                time.sleep(60)
                r = _http_session.get(url, headers=HEADERS, timeout=20)
                if r.status_code != 200:
                    log.warning(f"    offset={offset}: HTTP {r.status_code} tras reintento → parando esta categoría")
                    break
            elif r.status_code != 200:
                log.warning(f"    offset={offset}: HTTP {r.status_code} → parando paginación")
                break
            prods = extract_products_from_html(r.text)
            new = [p for p in prods if p["id_api"] not in seen]
            seen.update(p["id_api"] for p in new)
            all_products.extend(new)
            pages_fetched += 1
            if not new:
                log.debug(f"    offset={offset}: sin productos nuevos → parando")
                break
        except Exception as e:
            log.warning(f"    offset={offset}: {e} → parando paginación")
            break
        time.sleep(PAGINATION_DELAY)
    log.info(f"    📄 Paginación: {pages_fetched} páginas más, {len(all_products)} productos adicionales")
    return all_products

def parse_impressions_product(item):
    """Parsea un producto del array window['impressions'] embebido en el HTML."""
    try:
        item_id = str(item.get("item_id") or "").strip()
        if not item_id:
            return None
        try:
            price = float(item.get("price", 0))
        except Exception:
            price = 0.0

        slug = (item.get("item_name") or "").strip()
        nombre = slug.replace("-", " ").title()

        formato = ""
        m = re.search(r'(\d+(?:[.,]\d+)?)-?(ml|cl|l|kg|g|ud|pack)', slug, re.IGNORECASE)
        if m:
            formato = f"{m.group(1)} {m.group(2).lower()}"

        return {
            "id":               f"CF-{item_id}",
            "id_api":           item_id,
            "nombre_comercial": nombre,
            "precio":           price,
            "marca":            (item.get("item_brand") or "").strip().title(),
            "ean":              str(item.get("item_ean") or "").strip(),
            "url":              f"{BASE_URL}/p/{slug}/{item_id}/p",
            "imagen":           "",
            "disponible":       price > 0,
            "formato":          formato,
        }
    except Exception:
        return None


def extract_products_from_html(html):
    """Extrae productos del HTML renderizado."""
    if not html:
        return []

    # Intento 1: window["impressions"] — array JSON con EAN embebido en el HTML
    m = re.search(r'window\["impressions"\]\s*=\s*(\[.*?\]);', html, re.DOTALL)
    if m:
        try:
            items = json.loads(m.group(1))
            productos = [parse_impressions_product(it) for it in items]
            productos = [p for p in productos if p]
            if productos:
                log.debug(f"    impressions: {len(productos)} productos")
                return productos
        except Exception as e:
            log.debug(f"    impressions parse error: {e}")

    # Intento 2: JSON-LD con itemListElement
    soup = BeautifulSoup(html, "html.parser")
    productos = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        items = data.get("itemListElement", []) if isinstance(data, dict) else []
        for it in items:
            item = it.get("item", it)
            if item.get("@type") not in ("Product", "IndividualProduct"):
                continue
            productos.append(parse_jsonld_product(item))
    if productos:
        return [p for p in productos if p]

    # Intento 3: tarjetas HTML
    selectors = [
        '[data-testid="product-card"]',
        'article.product-card',
        'div[class*="product-card__"]',
        'li[class*="product-card"]',
    ]
    cards = []
    for sel in selectors:
        cards = soup.select(sel)
        if cards:
            log.debug(f"    Selector válido: {sel} ({len(cards)} cards)")
            break
    for card in cards:
        p = parse_html_card(card)
        if p:
            productos.append(p)
    return productos

def parse_jsonld_product(item):
    """Parsea un item JSON-LD de Product."""
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
            m = re.search(r"/(\d{6,})/p", url)
            sku = m.group(1) if m else ""
        if not sku:
            return None

        brand = item.get("brand") or {}
        brand = brand.get("name", "") if isinstance(brand, dict) else str(brand)

        img = item.get("image", "")
        if isinstance(img, list):
            img = img[0] if img else ""

        return {
            "id":               f"CF-{sku}",
            "id_api":           sku,
            "nombre_comercial": (item.get("name") or "").strip(),
            "precio":           price,
            "marca":            brand.strip(),
            "ean":              str(item.get("gtin13") or item.get("gtin") or "").strip(),
            "url":              item.get("url", ""),
            "imagen":           img,
            "disponible":       "InStock" in str(offers.get("availability", "InStock")),
            "formato":          "",
        }
    except Exception:
        return None

def parse_html_card(card):
    """Parsea una tarjeta HTML de producto."""
    try:
        link = card.find("a", href=True)
        if not link:
            return None
        href = link["href"]
        m = re.search(r"/(\d{6,})/p", href)
        if not m:
            return None
        sku = m.group(1)

        # Nombre
        name_el = (card.select_one('h2, h3, [class*="title"], [class*="name"]'))
        name = name_el.get_text(strip=True) if name_el else ""

        # Precio (múltiples formatos posibles)
        price = 0.0
        price_el = card.select_one('[class*="price"], [data-testid*="price"]')
        if price_el:
            txt = price_el.get_text(" ", strip=True)
            m = re.search(r"(\d+[.,]\d{2})\s*€", txt)
            if m:
                try:
                    price = float(m.group(1).replace(",", "."))
                except Exception:
                    pass

        img_el = card.find("img")
        img = img_el.get("src", "") if img_el else ""

        full_url = href if href.startswith("http") else BASE_URL + href

        return {
            "id": f"CF-{sku}",
            "id_api": sku,
            "nombre_comercial": name,
            "precio": price,
            "marca": "",
            "url": full_url,
            "imagen": img,
            "disponible": price > 0,
            "formato": "",
        }
    except Exception:
        return None

# ─────────────────────────────────────────────────────────
# API → productos normalizados (cuando la API sí responde)
# ─────────────────────────────────────────────────────────
def parse_api_product(p):
    try:
        sku = str(p.get("code") or p.get("productCode") or "")
        if not sku:
            return None
        price = p.get("price", {})
        if isinstance(price, dict):
            price = price.get("value", 0)
        try:
            price = float(price)
        except Exception:
            price = 0.0
        return {
            "id":               f"CF-{sku}",
            "id_api":           sku,
            "nombre_comercial": (p.get("name") or "").strip(),
            "precio":           price,
            "marca":            (p.get("brand") or "").strip(),
            "ean":              str(p.get("ean") or p.get("gtin") or "").strip(),
            "url":              BASE_URL + (p.get("url", "") or ""),
            "imagen":           (p.get("images", [{}])[0].get("url", "")
                                if p.get("images") else ""),
            "disponible":       p.get("stock", {}).get("stockLevelStatus") != "outOfStock",
            "formato":          (p.get("packaging") or "").strip(),
        }
    except Exception:
        return None

# ─────────────────────────────────────────────────────────
# SUPABASE
# ─────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────
def main(dry_run=False, only_cat=None, force_stealth=False, debug=False):
    log.info("━" * 55)
    log.info("  SCRAPER CARREFOUR (híbrido API + Scrapling)")
    log.info("━" * 55)

    db = None
    if not dry_run:
        try:
            db = get_supabase()
            log.info("✅ Supabase conectado")
        except Exception as e:
            log.warning(f"⚠️  Supabase: {e} → modo dry_run")
            dry_run = True

    cats = [(s, c, n) for s, c, n in CATEGORIES if not only_cat or only_cat in s]
    log.info(f"📋 {len(cats)} categorías")
    if force_stealth:
        log.info("🦊 Modo forzado: Scrapling desde el inicio\n")
    else:
        log.info("")

    total_p = total_u = 0
    for slug, cat_id, cat_name in cats:
        log.info(f"📦  {cat_name}  [{cat_id}]")
        products_raw = []

        # FASE 1: API
        if not force_stealth:
            log.info("    ⚡ Intentando API SAP Commerce...")
            page = 0
            while page < MAX_PAGES:
                items = try_api(cat_id, page=page)
                if items is None:
                    break
                products_raw.extend(items)
                if len(items) < PAGE_SIZE:
                    break
                page += 1
                time.sleep(DELAY)
            if products_raw:
                log.info(f"    ✅ API OK: {len(products_raw)} productos crudos")

        # FASE 2: Fallback Scrapling si la API falló
        if not products_raw:
            log.info("    🦊 Fallback → Scrapling (pág. 1) + curl_cffi (paginación)")
            html, total = scrape_first_page(slug, cat_id, debug=debug)
            productos_final = extract_products_from_html(html)

            if not productos_final:
                log.info("    ❌ Sin productos")
                log.info("")
                continue

            log.info(f"    ✅ Pág. 1: {len(productos_final)} productos (total anunciado: {total})")

            # Paginación con curl_cffi para las páginas restantes
            if total > PER_PAGE:
                seen = {p["id_api"] for p in productos_final}
                extra = fetch_pagination_pages(slug, cat_id, total)
                new_extra = [p for p in extra if p["id_api"] not in seen]
                productos_final.extend(new_extra)

            log.info(f"    ✅ Total categoría: {len(productos_final)} productos")
            if dry_run or not db:
                log.info("    [dry-run] muestra:")
                for p in productos_final[:3]:
                    log.info(f"      {p['id']} | "
                             f"{p['nombre_comercial'][:45]} | "
                             f"{p['precio']}€ | EAN:{p.get('ean','')}")
            else:
                n = upsert(db, productos_final)
                total_u += n
                log.info(f"    ✅ {n} upserted")
            total_p += len(productos_final)
            log.info("")
            continue

        # Normalizar productos de la API
        products = [parse_api_product(p) for p in products_raw]
        products = [p for p in products if p]
        total_p += len(products)

        if dry_run or not db:
            log.info(f"    [dry-run] {len(products)} productos. Muestra:")
            for p in products[:3]:
                log.info(f"      {p['id']} | "
                         f"{p['nombre_comercial'][:45]} | "
                         f"{p['precio']}€")
        else:
            n = upsert(db, products)
            total_u += n
            log.info(f"    ✅ {n} upserted")
        log.info("")

    close_stealthy_session()
    log.info("━" * 55)
    log.info(f"  Total productos : {total_p}")
    log.info(f"  Total upserted  : {total_u}")
    log.info("━" * 55)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="No escribe en Supabase")
    ap.add_argument("--cat", help="Filtrar por slug (ej: 'bebidas')")
    ap.add_argument("--stealth", action="store_true",
                    help="Saltar API, usar Scrapling directamente")
    ap.add_argument("--debug", action="store_true",
                    help="Guarda el HTML de cada categoría en debug_carrefour_<slug>.html")
    args = ap.parse_args()
    try:
        main(dry_run=args.dry_run, only_cat=args.cat,
             force_stealth=args.stealth, debug=args.debug)
    finally:
        close_stealthy_session()
