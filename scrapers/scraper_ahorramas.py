"""
scraper_ahorramas.py — Ahorramas España → Supabase
Estrategia híbrida (patrón Carrefour):
  1) Demandware Search-ShowAjax con curl_cffi
  2) Fallback: Scrapling StealthyFetcher
  3) Paginación completa hasta agotar productos

IDs: AH-XXXX secuencial (mantiene IDs existentes en productos_match).
Tabla destino: precios_ahorramas
"""
import argparse, logging, os, re, time
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BASE_URL   = "https://www.ahorramas.com"
SEARCH_URL = f"{BASE_URL}/on/demandware.store/Sites-Ahorramas-Site/es/Search-ShowAjax"
TABLE_NAME = "precios_ahorramas"
PREFIJO_ID = "AH"
SZ         = 48
DELAY      = 0.7
PAGINATION_DELAY = 0.5

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ~20 categorías: las 9 originales + subcategorías nuevas
CATEGORIES = [
    ("alimentacion",                "Alimentación"),
    ("bebidas",                     "Bebidas"),
    ("frescos",                     "Frescos"),
    ("congelados",                  "Congelados"),
    ("lacteos",                     "Lácteos"),
    ("drogueria",                   "Droguería"),
    ("cuidadopersonal",             "Cuidado personal"),
    ("mascotas",                    "Mascotas"),
    ("bebe",                        "Bebé"),
    ("panaderia-pasteleria",        "Panadería y pastelería"),
    ("charcuteria-carniceria",      "Carnicería y charcutería"),
    ("pescaderia",                  "Pescadería"),
    ("conservas",                   "Conservas"),
    ("cereales-galletas",           "Cereales y galletas"),
    ("aceites-salsas-condimentos",  "Aceites y condimentos"),
    ("limpieza",                    "Limpieza"),
    ("higiene",                     "Higiene"),
    ("vinos-cava-licores",          "Vinos y licores"),
    ("snacks-aperitivos",           "Aperitivos y snacks"),
    ("cafe-infusiones",             "Café e infusiones"),
]

HEADERS = {
    "User-Agent":        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":            "text/html, */*; q=0.01",
    "Accept-Language":   "es-ES,es;q=0.9",
    "X-Requested-With":  "XMLHttpRequest",
    "Referer":           BASE_URL + "/",
}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("ahorramas")

_http_session = curl_requests.Session(impersonate="chrome124")

# ─── PARSEO DE PRECIO ────────────────────────────────────────────────────────

def parsear_precio(texto):
    """Extrae float de '2,99 €', '2.99€', '3 €', etc. Devuelve None si falla."""
    if not texto:
        return None
    texto = str(texto).replace("\xa0", " ").strip()
    m = re.search(r"(\d+)[,.](\d+)", texto)
    if m:
        try:
            return float(f"{m.group(1)}.{m.group(2)}")
        except Exception:
            pass
    m = re.search(r"(\d+)", texto)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            pass
    return None

# ─── PARSEO HTML ─────────────────────────────────────────────────────────────

def parsear_producto(tile):
    """Extrae datos de un product-tile de Demandware."""
    try:
        # Nombre
        nombre_el = (
            tile.select_one(".pdp-link a") or
            tile.select_one(".product-name a") or
            tile.select_one("a.product-tile-link") or
            tile.select_one("[class*='product-name'] a") or
            tile.select_one("h2 a") or tile.select_one("h3 a") or
            tile.select_one("a[title]")
        )
        nombre = nombre_el.get_text(strip=True) if nombre_el else None
        if not nombre:
            return None

        # URL
        url = nombre_el.get("href", "") if nombre_el else ""
        if url and not url.startswith("http"):
            url = BASE_URL + url

        # ID desde data-pid o URL
        pid = (tile.get("data-pid") or tile.get("data-product-id") or
               tile.get("data-itemid") or "")
        if not pid and url:
            m   = re.search(r"-(\d+)\.html", url)
            pid = m.group(1) if m else ""
        if not pid:
            return None

        # Precio principal
        precio_el = (
            tile.select_one(".sales .value") or
            tile.select_one(".price .value") or
            tile.select_one("[itemprop='price']") or
            tile.select_one("[class*='sales-price']") or
            tile.select_one(".price-sales") or
            tile.select_one("[class*='price']")
        )
        precio_txt  = (precio_el.get("content") or
                       precio_el.get_text(strip=True)) if precio_el else ""
        precio = parsear_precio(precio_txt)

        # Precio por unidad
        ref_el = (
            tile.select_one(".price-per-unit") or
            tile.select_one("[class*='per-unit']") or
            tile.select_one("[class*='unit-price']") or
            tile.select_one("[class*='reference-price']")
        )
        precio_unidad = ref_el.get_text(strip=True) if ref_el else ""

        # Imagen
        img_el = (tile.select_one("img.tile-image") or
                  tile.select_one("img[class*='product']") or
                  tile.select_one("img"))
        imagen = ""
        if img_el:
            imagen = img_el.get("src") or img_el.get("data-src") or ""

        # Marca
        marca_el = (tile.select_one("[class*='brand']") or
                    tile.select_one(".product-brand"))
        marca = marca_el.get_text(strip=True) if marca_el else ""

        # Formato desde el nombre
        fmt_m  = re.search(
            r'(\d+(?:[.,]\d+)?\s*(?:ml|l|g|kg|cl|ud|uds|pack)[\w\s]*)',
            nombre, re.IGNORECASE)
        formato = fmt_m.group(1).strip() if fmt_m else ""

        return {
            "id_api":           pid,
            "nombre_comercial": nombre,
            "precio":           precio,
            "precio_unidad":    precio_unidad,
            "marca":            marca,
            "ean":              "",
            "url":              url,
            "imagen":           imagen or "",
            "disponible":       True,
            "formato":          formato,
        }
    except Exception:
        return None

# ─── EXTRACCIÓN DE TOTAL ──────────────────────────────────────────────────────

def extract_total_ahorramas(html):
    """Detecta el total de productos con múltiples patrones."""
    for pat in [
        r'"total"\s*:\s*(\d+)',
        r'"count"\s*:\s*(\d+)',
        r'"totalCount"\s*:\s*(\d+)',
        r'data-count="(\d+)"',
        r'"numberOfResults"\s*:\s*(\d+)',
    ]:
        m = re.search(pat, html)
        if m:
            return int(m.group(1))
    return 0

# ─── API (curl_cffi) ─────────────────────────────────────────────────────────

def try_api(cgid, start=0, retries=2):
    """Llama al endpoint Demandware. Devuelve (html_text, total) o (None, 0)."""
    params = {"cgid": cgid, "pmin": "0.01", "start": start, "sz": SZ}
    for attempt in range(retries):
        try:
            r = _http_session.get(SEARCH_URL, params=params,
                                  headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.text, extract_total_ahorramas(r.text)
            if r.status_code in (429, 503):
                time.sleep(10)
                continue
            log.debug(f"  Demandware HTTP {r.status_code}")
        except Exception as e:
            log.debug(f"  Demandware error: {e}")
        time.sleep(DELAY * (attempt + 1))
    return None, 0

def parse_tiles_from_html(html):
    """Extrae todos los product-tiles de una respuesta Demandware."""
    if not html:
        return []
    soup  = BeautifulSoup(html, "html.parser")
    tiles = (
        soup.select("[data-pid]") or
        soup.select("[class*='product-tile']") or
        soup.select(".product-container") or
        soup.select("[data-product-id]")
    )
    prods = []
    for tile in tiles:
        p = parsear_producto(tile)
        if p and p["nombre_comercial"]:
            prods.append(p)
    return prods

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

def scrape_with_scrapling(cgid, retries=2):
    """Renderiza la página de categoría con Scrapling."""
    url = f"{BASE_URL}/es/c/{cgid}"
    for attempt in range(retries):
        try:
            session = get_stealthy_session()
            page    = session.fetch(url, timeout=60000)
            if page and page.status == 200:
                return page.html_content, extract_total_ahorramas(page.html_content)
            log.warning(f"    Stealthy HTTP {page.status if page else 'None'}")
        except Exception as e:
            log.warning(f"    Stealthy error: {e}")
        time.sleep(DELAY * 2)
    return None, 0

# ─── IDs SECUENCIALES ────────────────────────────────────────────────────────

def get_existing_id_map(client):
    """Obtiene {id_api: id} de Supabase."""
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
    """Asigna AH-XXXX manteniendo IDs existentes en Supabase."""
    ultimo_num = max(
        (int(v.split("-")[1]) for v in id_map.values()
         if "-" in v and v.split("-")[1].isdigit()),
        default=0,
    )
    contador  = ultimo_num
    resultado = []
    vistos    = set()
    for p in products:
        key = p["id_api"]
        if key in vistos:
            continue
        vistos.add(key)
        p["id"] = id_map.get(key) or f"{PREFIJO_ID}-{(contador := contador + 1):04d}"
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
    log.info("  SCRAPER AHORRAMAS (hibrido Demandware + Scrapling)")
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

    categories = [(cgid, nm) for cgid, nm in CATEGORIES
                  if not only_cat or only_cat in cgid]
    log.info(f"{len(categories)} categorias\n")

    all_products = {}  # id_api → producto
    total_upserted = 0

    for cgid, cat_name in categories:
        log.info(f"  {cat_name}  [{cgid}]")
        page_products = []

        # FASE 1: Demandware con curl_cffi
        if not force_stealth:
            log.info("    Intentando Demandware API...")
            html, total = try_api(cgid, start=0)
            if html:
                page_products = parse_tiles_from_html(html)
                log.info(f"    Pag. 1: {len(page_products)} productos (total: {total})")

                if total > SZ:
                    for start in range(SZ, total + SZ, SZ):
                        chunk_html, _ = try_api(cgid, start=start)
                        if not chunk_html:
                            break
                        chunk = parse_tiles_from_html(chunk_html)
                        if not chunk:
                            break
                        page_products.extend(chunk)
                        time.sleep(PAGINATION_DELAY)

        # FASE 2: Scrapling si Demandware falló o devolvió 0
        if not page_products:
            log.info("    Fallback -> Scrapling")
            html, total = scrape_with_scrapling(cgid)
            if html:
                page_products = parse_tiles_from_html(html)
                log.info(f"    Scrapling: {len(page_products)} productos")
            if not page_products:
                log.info("    Sin productos\n")
                continue

        nuevos = 0
        for p in page_products:
            if p["id_api"] and p["id_api"] not in all_products:
                p["categoria_ahorramas"] = cat_name
                all_products[p["id_api"]] = p
                nuevos += 1
        log.info(f"    +{nuevos} nuevos | total acumulado: {len(all_products)}")
        log.info("")
        time.sleep(DELAY)

    # Asignar IDs y subir
    productos_lista = list(all_products.values())
    productos_lista = assign_ids(productos_lista, id_map)

    log.info("=" * 55)
    log.info(f"  Total productos : {len(productos_lista)}")

    if dry_run or not db:
        log.info("  [dry-run] Muestra:")
        for p in productos_lista[:5]:
            log.info(f"    {p['id']} | {p['nombre_comercial'][:45]} | "
                     f"{p.get('precio')}€ | {p.get('precio_unidad')}")
    else:
        n = upsert(db, productos_lista)
        total_upserted = n
        log.info(f"  Total upserted  : {total_upserted}")

    log.info("=" * 55)
    close_stealthy_session()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run",  action="store_true", help="No escribe en Supabase")
    ap.add_argument("--cat",      help="Filtrar por cgid de categoria")
    ap.add_argument("--stealth",  action="store_true", help="Forzar Scrapling desde el inicio")
    ap.add_argument("--debug",    action="store_true", help="Guarda HTML de cada categoria")
    args = ap.parse_args()
    try:
        main(dry_run=args.dry_run, only_cat=args.cat,
             force_stealth=args.stealth, debug=args.debug)
    finally:
        close_stealthy_session()
