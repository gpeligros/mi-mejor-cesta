"""
scraper_alcampo.py — Alcampo España → Supabase
Estrategia híbrida (patrón Carrefour):
  1) API JSON con curl_cffi
  2) Fallback: Scrapling StealthyFetcher (SPA React)
  3) Paginación con curl_cffi para páginas 2+

Sin visitas individuales por producto — todo desde el listado de categoría.
IDs: AL-{pid} directo (compatible con Carrefour).
Tabla destino: precios_alcampo
"""
import argparse, json, logging, os, re, time
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BASE_URL     = "https://www.compraonline.alcampo.es"
API_CAT_URL  = f"{BASE_URL}/api/v2/page/category"
TABLE_NAME   = "precios_alcampo"
PAGE_SIZE    = 50
DELAY        = 1.0
PAGINATION_DELAY = 0.5

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ~30 categorías cubriendo todo el catálogo de Alcampo
CATEGORIES = [
    ("OC10",       "desayuno-y-merienda",                              "Desayuno y merienda"),
    ("OC16",       "leche-huevos-lacteos-yogures-y-bebidas-vegetales", "Lácteos y huevos"),
    ("OC1001",     "leche-huevos-lacteos-yogures-y-bebidas-vegetales/leche", "Leche"),
    ("OC2112",     "frescos",                                          "Frescos"),
    ("OC20022018", "comida-preparada",                                 "Comida preparada"),
    ("OC1101",     "bebidas/agua-y-refrescos",                        "Agua y refrescos"),
    ("OC1102",     "bebidas/zumos-de-frutas",                         "Zumos"),
    ("OC1103",     "bebidas/bebidas-energeticas-e-isotonica",         "Bebidas energéticas"),
    ("OC1701",     "frutas-y-verduras/fruta-fresca",                  "Fruta fresca"),
    ("OC1702",     "frutas-y-verduras/verdura-y-hortaliza-fresca",    "Verdura fresca"),
    ("OC1401",     "pescado-y-marisco/pescado-fresco",                "Pescado fresco"),
    ("OC100302",   "alimentacion/frutos-secos-y-snacks",              "Frutos secos y snacks"),
    ("OC1002",     "alimentacion/arroz-legumbres-y-cereales",         "Arroz y legumbres"),
    ("OC1003",     "alimentacion/aceites-y-vinagres",                 "Aceites y vinagres"),
    ("OC1004",     "alimentacion/conservas-y-platos-preparados",      "Conservas"),
    ("OC1005",     "alimentacion/pasta-y-pizza",                      "Pasta y pizza"),
    ("OC1006",     "alimentacion/salsas-especias-y-condimentos",      "Salsas y condimentos"),
    ("OC1007",     "alimentacion/galletas-y-bolleria",                "Galletas y bollería"),
    ("OC1008",     "alimentacion/cafe-e-infusiones",                  "Café e infusiones"),
    ("OC1009",     "alimentacion/azucar-y-edulcorantes",              "Azúcar y edulcorantes"),
    ("OC1010",     "bebidas/vinos-y-cavas",                           "Vinos y cavas"),
    ("OC1011",     "bebidas/cervezas",                                "Cervezas"),
    ("OCSINGSINL", "sin-gluten-sin-lactosa-nutricion-deportiva-y-funcional", "Sin gluten / Sin lactosa"),
    ("OCC14",      "drogueria",                                       "Droguería"),
    ("OC70",       "perfumeria",                                      "Perfumería"),
    ("OCC13",      "bebe",                                            "Bebé"),
    ("OC069",      "parafarmacia",                                    "Parafarmacia"),
    ("OC062",      "mascotas",                                        "Mascotas"),
    ("OC063",      "mascotas/perros",                                 "Mascotas - Perros"),
    ("OC064",      "mascotas/gatos",                                  "Mascotas - Gatos"),
]

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/html, */*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer":         BASE_URL + "/",
}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("alcampo")

_http_session = curl_requests.Session(impersonate="chrome124")

# ─── API (curl_cffi) ─────────────────────────────────────────────────────────

def try_api(cat_id, page=0, retries=2):
    """Intenta el endpoint REST de Alcampo. Devuelve lista de productos o None."""
    params = {"categoryId": cat_id, "currentPage": page, "pageSize": PAGE_SIZE}
    for attempt in range(retries):
        try:
            r = _http_session.get(API_CAT_URL, params=params,
                                  headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data  = r.json()
                prods = (data.get("products") or data.get("items")
                         or data.get("data", {}).get("products") or [])
                return prods if prods else None
            log.debug(f"  API HTTP {r.status_code}")
        except Exception as e:
            log.debug(f"  API error: {e}")
        time.sleep(DELAY * (attempt + 1))
    return None

# ─── PARSEO ───────────────────────────────────────────────────────────────────

def parse_api_product(item):
    """Normaliza un producto de la API de Alcampo al schema unificado."""
    try:
        pid = str(item.get("id") or item.get("productId") or item.get("code") or "").strip()
        if not pid:
            return None
        nombre = (item.get("name") or item.get("displayName") or "").strip()
        if not nombre:
            return None

        # precio
        price_info = item.get("price") or {}
        if isinstance(price_info, (int, float)):
            precio = float(price_info)
            precio_unidad = ""
        else:
            precio = float(price_info.get("value") or price_info.get("amount") or 0)
            ref    = str(price_info.get("referencePrice") or price_info.get("pricePerUnit") or "")
            precio_unidad = ref.strip()

        # marca
        brand = item.get("brand") or {}
        if isinstance(brand, dict):
            marca = (brand.get("name") or "").strip()
        else:
            marca = str(brand).strip()

        # ean
        ean = str(item.get("ean") or item.get("gtin") or item.get("barcode") or "").strip()

        # imagen
        imagen = ""
        imgs   = item.get("images") or item.get("imageGallery") or []
        if isinstance(imgs, list) and imgs:
            imagen = imgs[0].get("url", "") if isinstance(imgs[0], dict) else str(imgs[0])
        elif isinstance(imgs, str):
            imagen = imgs
        if not imagen:
            imagen = item.get("image") or item.get("imageUrl") or ""

        # url
        slug = item.get("slug") or item.get("url") or ""
        url  = f"{BASE_URL}/products/{slug}/{pid}" if slug else f"{BASE_URL}/products/{pid}"

        # disponible
        avail      = item.get("availability") or item.get("stock") or ""
        disponible = str(avail).lower() not in ("outofstock", "out_of_stock", "false", "0")

        # formato
        fmt_m  = re.search(
            r'(\d+(?:[.,]\d+)?\s*(?:ml|l|g|kg|cl|ud|uds|pack)[\w\s]*)',
            nombre, re.IGNORECASE)
        formato = fmt_m.group(1).strip() if fmt_m else ""

        return {
            "id":               f"AL-{pid}",
            "id_api":           pid,
            "nombre_comercial": nombre,
            "precio":           round(precio, 2) if precio else None,
            "precio_unidad":    precio_unidad,
            "marca":            marca,
            "ean":              ean,
            "url":              url,
            "imagen":           imagen,
            "disponible":       disponible,
            "formato":          formato,
        }
    except Exception:
        return None

# ─── SCRAPLING (fallback) ────────────────────────────────────────────────────

_stealthy_session = None

def get_stealthy_session():
    global _stealthy_session
    if _stealthy_session is None:
        from scrapling.fetchers import StealthySession
        log.info("    Abriendo navegador stealth (~5s)...")
        _stealthy_session = StealthySession(
            headless=True,
            solve_cloudflare=True,
            network_idle=True,
            block_webrtc=True,
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

def _scroll_and_wait(page):
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)

def extract_total_from_html(html):
    for pat in [r'"totalResults"\s*:\s*(\d+)', r'"total"\s*:\s*(\d+)',
                r'"totalProducts"\s*:\s*(\d+)', r'"count"\s*:\s*(\d+)',
                r'(\d+)\s+productos']:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0

def extract_products_from_html(html):
    """Extrae productos del HTML renderizado de Alcampo."""
    if not html:
        return []

    # Intento 1: JSON embebido en window.__INITIAL_STATE__ o similar
    for pat in [
        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
        r'window\.__data__\s*=\s*(\{.*?\});',
        r'"productList"\s*:\s*(\[.*?\])\s*[,}]',
        r'"products"\s*:\s*(\[.*?\])\s*[,}]',
    ]:
        m = re.search(pat, html, re.DOTALL)
        if m:
            try:
                blob = json.loads(m.group(1))
                prods_raw = _find_products_in_blob(blob)
                if prods_raw:
                    parsed = [parse_api_product(it) for it in prods_raw]
                    parsed = [p for p in parsed if p]
                    if parsed:
                        log.debug(f"    JSON embebido: {len(parsed)} productos")
                        return parsed
            except Exception as e:
                log.debug(f"    JSON blob error: {e}")

    # Intento 2: JSON-LD ItemList
    soup  = BeautifulSoup(html, "html.parser")
    prods = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        if data.get("@type") != "ItemList":
            continue
        for it in data.get("itemListElement", []):
            p = _parse_jsonld_alcampo(it)
            if p:
                prods.append(p)
    if prods:
        return prods

    # Intento 3: tarjetas HTML
    for sel in [
        '[data-testid="product-card"]',
        '.product-card',
        '[class*="ProductCard"]',
        '[class*="product-card"]',
        '[data-pid]',
    ]:
        cards = soup.select(sel)
        if cards:
            for card in cards:
                p = _parse_html_card_alcampo(card)
                if p:
                    prods.append(p)
            break
    return prods

def _find_products_in_blob(blob):
    """Busca recursivamente una lista de productos en un JSON blob."""
    if isinstance(blob, list) and blob and isinstance(blob[0], dict):
        if any(k in blob[0] for k in ("id", "name", "price", "productId")):
            return blob
    if isinstance(blob, dict):
        for key in ("products", "items", "productList", "data"):
            val = blob.get(key)
            if val:
                result = _find_products_in_blob(val)
                if result:
                    return result
    return []

def _parse_jsonld_alcampo(it):
    try:
        url = it.get("url", "")
        m   = re.search(r"/products/([^/]+)/(\d+)$", url)
        if not m:
            return None
        slug, pid = m.group(1), m.group(2)
        item   = it.get("item", it)
        offers = item.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price  = offers.get("price") or offers.get("lowPrice") or 0
        try:
            price = float(str(price).replace(",", "."))
        except Exception:
            price = 0.0
        brand  = item.get("brand") or {}
        brand  = brand.get("name", "") if isinstance(brand, dict) else str(brand)
        disponible = "InStock" in str(offers.get("availability", "InStock"))
        return {
            "id":               f"AL-{pid}",
            "id_api":           pid,
            "nombre_comercial": (item.get("name") or "").strip(),
            "precio":           round(price, 2) if price else None,
            "precio_unidad":    "",
            "marca":            brand.strip(),
            "ean":              str(item.get("gtin13") or item.get("gtin") or "").strip(),
            "url":              url if url.startswith("http") else BASE_URL + url,
            "imagen":           item.get("image", ""),
            "disponible":       disponible,
            "formato":          "",
        }
    except Exception:
        return None

def _parse_html_card_alcampo(card):
    try:
        pid = card.get("data-pid") or card.get("data-product-id") or ""
        if not pid:
            link = card.find("a", href=True)
            if link:
                m   = re.search(r"/products/[^/]+/(\d+)", link["href"])
                pid = m.group(1) if m else ""
        if not pid:
            return None
        name_el = card.select_one('h2, h3, [class*="title"], [class*="name"]')
        name    = name_el.get_text(strip=True) if name_el else ""
        price   = 0.0
        for sel in ['[class*="price"]', '[itemprop="price"]', '[data-price]']:
            el = card.select_one(sel)
            if el:
                txt = el.get("content") or el.get_text(strip=True)
                m   = re.search(r"(\d+[.,]\d{2})", txt)
                if m:
                    try:
                        price = float(m.group(1).replace(",", "."))
                        break
                    except Exception:
                        pass
        unit_el = card.select_one('[class*="unit"], [class*="per-unit"], [class*="reference"]')
        precio_unidad = unit_el.get_text(strip=True) if unit_el else ""
        img_el = card.find("img")
        imagen = img_el.get("src") or img_el.get("data-src", "") if img_el else ""
        link   = card.find("a", href=True)
        slug   = ""
        if link:
            m = re.search(r"/products/([^/]+)/\d+", link["href"])
            slug = m.group(1) if m else ""
        return {
            "id":               f"AL-{pid}",
            "id_api":           pid,
            "nombre_comercial": name,
            "precio":           price,
            "precio_unidad":    precio_unidad,
            "marca":            "",
            "ean":              "",
            "url":              f"{BASE_URL}/products/{slug}/{pid}",
            "imagen":           imagen,
            "disponible":       price > 0,
            "formato":          "",
        }
    except Exception:
        return None

def scrape_first_page(cat_id, slug, retries=2, debug=False):
    """Renderiza la primera página de categoría con Scrapling."""
    url = f"{BASE_URL}/categories/{slug}/{cat_id}"
    for attempt in range(retries):
        try:
            session = get_stealthy_session()
            page    = session.fetch(url, page_action=_scroll_and_wait, timeout=60000)
            if page and page.status == 200:
                html  = page.html_content
                total = extract_total_from_html(html)
                if debug:
                    with open(f"debug_alcampo_{cat_id}.html", "w", encoding="utf-8") as f:
                        f.write(html)
                return html, total
            log.warning(f"    Stealthy HTTP {page.status if page else 'None'} (intento {attempt+1})")
        except Exception as e:
            log.warning(f"    Stealthy error: {e} (intento {attempt+1})")
        time.sleep(DELAY * 2)
    return None, 0

def fetch_pagination_pages(cat_id, slug, total):
    """Obtiene páginas 2..N con curl_cffi."""
    all_products = []
    seen         = set()
    pages        = min(total // PAGE_SIZE + 1, 200)
    for page in range(1, pages):
        url = f"{BASE_URL}/categories/{slug}/{cat_id}?currentPage={page}"
        try:
            r = _http_session.get(url, headers=HEADERS, timeout=20)
            if r.status_code in (502, 503, 429):
                time.sleep(5)
                r = _http_session.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                log.warning(f"    página {page}: HTTP {r.status_code} -> parando")
                break
            prods = extract_products_from_html(r.text)
            new   = [p for p in prods if p["id_api"] not in seen]
            seen.update(p["id_api"] for p in new)
            all_products.extend(new)
            if not new:
                break
        except Exception as e:
            log.warning(f"    página {page}: {e} -> parando")
            break
        time.sleep(PAGINATION_DELAY)
    log.info(f"    Paginación: {len(all_products)} productos adicionales")
    return all_products

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
    log.info("  SCRAPER ALCAMPO (hibrido API + Scrapling)")
    log.info("=" * 55)

    db = None
    if not dry_run:
        try:
            db = get_supabase()
            log.info("Supabase conectado")
        except Exception as e:
            log.warning(f"Supabase no disponible ({e}) -> dry_run activado")
            dry_run = True

    cats = [(cid, sl, nm) for cid, sl, nm in CATEGORIES
            if not only_cat or only_cat in cid or only_cat in sl]
    log.info(f"{len(cats)} categorias\n")

    total_p = total_u = 0
    seen_global = set()

    for cat_id, slug, cat_name in cats:
        log.info(f"  {cat_name}  [{cat_id}]")
        products_raw = []

        # FASE 1: API
        if not force_stealth:
            log.info("    Intentando API Alcampo...")
            page = 0
            while page < 200:
                items = try_api(cat_id, page=page)
                if items is None:
                    break
                products_raw.extend(items)
                if len(items) < PAGE_SIZE:
                    break
                page += 1
                time.sleep(DELAY)
            if products_raw:
                log.info(f"    API: {len(products_raw)} items")

        # FASE 2: Scrapling si la API falló
        if not products_raw:
            log.info("    Fallback -> Scrapling")
            html, total = scrape_first_page(cat_id, slug, debug=debug)
            page_prods  = extract_products_from_html(html)
            if not page_prods:
                log.info("    Sin productos\n")
                continue
            log.info(f"    Pag. 1: {len(page_prods)} (total anunciado: {total})")
            if total > PAGE_SIZE:
                extra       = fetch_pagination_pages(cat_id, slug, total)
                page_prods += extra
            parsed = page_prods
        else:
            parsed = [parse_api_product(it) for it in products_raw]
            parsed = [p for p in parsed if p]

        new_prods = [p for p in parsed if p["id_api"] not in seen_global]
        seen_global.update(p["id_api"] for p in new_prods)
        total_p += len(new_prods)
        log.info(f"    +{len(new_prods)} nuevos | total acumulado: {total_p}")

        if not dry_run and db and new_prods:
            n = upsert(db, new_prods)
            total_u += n
            log.info(f"    {n} upserted")
        elif dry_run:
            for p in new_prods[:3]:
                log.info(f"      {p['id']} | {p['nombre_comercial'][:45]} | "
                         f"{p.get('precio')}€ | {p.get('precio_unidad')}")
        log.info("")
        time.sleep(DELAY)

    close_stealthy_session()
    log.info("=" * 55)
    log.info(f"  Total productos : {total_p}")
    log.info(f"  Total upserted  : {total_u}")
    log.info("=" * 55)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run",  action="store_true", help="No escribe en Supabase")
    ap.add_argument("--cat",      help="Filtrar por ID o slug de categoría")
    ap.add_argument("--stealth",  action="store_true", help="Forzar Scrapling desde el inicio")
    ap.add_argument("--debug",    action="store_true", help="Guarda HTML de cada categoría")
    args = ap.parse_args()
    try:
        main(dry_run=args.dry_run, only_cat=args.cat,
             force_stealth=args.stealth, debug=args.debug)
    finally:
        close_stealthy_session()
