"""
scraper_ahorramas.py — AhorraMas → Supabase
Descubre subcategorías automáticamente y pagina cada una.
"""
import argparse, json, logging, math, os, re, time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

BASE_URL   = "https://www.ahorramas.com"
TABLE_NAME = "precios_ahorramas"
PAGE_SIZE  = 30
MAX_PAGES  = 100
DELAY      = 0.7
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Categorías principales — el scraper descubre las subcategorías automáticamente
CATEGORIES = [
    ("alimentacion",      "Alimentación"),
    ("frescos",           "Frescos"),
    ("bebidas",           "Bebidas"),
    ("congelados",        "Congelados"),
    ("drogueria",         "Droguería"),
    ("higiene-y-belleza", "Higiene y belleza"),
    ("bebe-y-embarazo",   "Bebé"),
    ("mascotas",          "Mascotas"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": BASE_URL,
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("ahorramas")

def get_html(url, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200: return r.text
            log.warning(f"HTTP {r.status_code}: {url}")
        except Exception as e:
            log.warning(f"Error ({attempt+1}/{retries}): {e}")
        time.sleep(DELAY * (attempt + 1))
    return None

def extract_product_links(html):
    """Extrae links de producto del HTML. Formato: /slug-nombre-12345.html"""
    items = {}
    soup  = BeautifulSoup(html, "html.parser")
    total = None

    # Total de productos
    for pat in [r'"total"\s*:\s*(\d+)', r'"totalResults"\s*:\s*(\d+)',
                r'(\d+)\s+resultados', r'(\d+)\s+productos']:
        m = re.search(pat, html)
        if m: total = int(m.group(1)); break

    # JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try: data = json.loads(script.string or "")
        except: continue
        if data.get("@type") != "ItemList": continue
        for item in data.get("itemListElement", []):
            url = item.get("url", "")
            m = re.search(r"/([^/]+-(\d{5,}))\.html$", url)
            if m: items[m.group(2)] = (m.group(1), url if url.startswith("http") else BASE_URL + url)

    # Fallback: links <a>
    if not items:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = re.search(r"/([^/]+-(\d{5,}))\.html", href)
            if m and m.group(2) not in items:
                full = href if href.startswith("http") else BASE_URL + href
                items[m.group(2)] = (m.group(1), full)

    return items, total

def get_subcategories(slug):
    """Devuelve lista de (subslug, nombre) para una categoría top-level."""
    html = get_html(f"{BASE_URL}/{slug}/")
    if not html: return []

    items, _ = extract_product_links(html)
    if items: return [(slug, slug)]  # tiene productos directos

    soup = BeautifulSoup(html, "html.parser")
    subcats = []
    seen    = set()
    # Links que son subsección de la categoría actual
    pat = re.compile(rf"^/{re.escape(slug)}/([^/?#]+)/?$")
    for a in soup.find_all("a", href=True):
        href = a["href"].rstrip("/").split("?")[0]
        m    = pat.match(href)
        if m and href not in seen:
            seen.add(href)
            subcats.append((f"{slug}/{m.group(1)}", a.get_text(strip=True) or m.group(1)))

    return subcats if subcats else [(slug, slug)]

def scrape_slug(slug, label):
    """Scrape todos los productos de un slug (categoría o subcategoría)."""
    all_items = {}
    max_pages = MAX_PAGES

    for page in range(max_pages):
        url  = f"{BASE_URL}/{slug}/?p={page+1}" if page > 0 else f"{BASE_URL}/{slug}/"
        html = get_html(url)
        if not html: break

        items, total = extract_product_links(html)

        if page == 0:
            if not items: break
            if total:
                max_pages = min(math.ceil(total / PAGE_SIZE), MAX_PAGES)
                log.info(f"    [{label}] {total} productos → {max_pages} págs")

        new = {pid: val for pid, val in items.items() if pid not in all_items}
        if not new: break

        all_items.update(new)
        time.sleep(DELAY)

    return all_items

def parse_product(html, pid, slug_prod, cat_name):
    name = slug_prod.replace("-", " ").title()
    price, brand, imagen = 0.0, "", ""
    disponible = True

    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try: data = json.loads(script.string or "")
        except: continue
        if data.get("@type") not in ("Product", "IndividualProduct"): continue
        name   = data.get("name", name)
        imagen = data.get("image", imagen)
        if isinstance(imagen, list): imagen = imagen[0] if imagen else ""
        rb = data.get("brand") or {}
        brand = rb.get("name", brand) if isinstance(rb, dict) else str(rb)
        offers = data.get("offers") or {}
        if isinstance(offers, list): offers = offers[0] if offers else {}
        p = offers.get("price") or offers.get("lowPrice")
        if p:
            try: price = float(str(p).replace(",", "."))
            except: pass
        disponible = "InStock" in str(offers.get("availability", "InStock"))
        break

    if price == 0.0:
        for pat in [r'"price"\s*:\s*"?([\d.,]+)"?', r'([\d]+[.,][\d]{2})\s*€']:
            m = re.search(pat, html)
            if m:
                try:
                    price = float(m.group(1).replace(",", "."))
                    if price > 0: break
                except: pass

    return {
        "id": f"AM-{pid}", "id_api": pid,
        "nombre_comercial": name.strip(), "precio": price,
        "marca": brand.strip(),
        "url": f"{BASE_URL}/{slug_prod}.html",
        "imagen": imagen, "disponible": disponible,
        "categoria": cat_name, "formato": "",
    }

def get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upsert(client, products):
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    for p in products: p["actualizado"] = now
    res = client.table(TABLE_NAME).upsert(products, on_conflict="id_api").execute()
    return len(res.data) if res.data else len(products)

def main(dry_run=False, only_cat=None):
    log.info("━"*55); log.info("  SCRAPER AHORRAMAS"); log.info("━"*55)
    db = None
    if not dry_run:
        try: db = get_supabase(); log.info("✅ Supabase conectado")
        except Exception as e: log.warning(f"⚠️  {e} → dry_run"); dry_run = True

    cats = [(s, n) for s, n in CATEGORIES if not only_cat or s == only_cat]
    log.info(f"📋 {len(cats)} categorías\n")

    total_p = total_u = 0
    for slug, cat_name in cats:
        log.info(f"📦  {cat_name}  [{slug}]")

        # Descubrir subcategorías
        subcats = get_subcategories(slug)
        log.info(f"    {len(subcats)} subcategorías")

        all_items = {}
        for subslug, sublabel in subcats:
            items = scrape_slug(subslug, sublabel)
            all_items.update(items)

        if not all_items:
            log.info("    Sin productos.\n"); continue

        log.info(f"    {len(all_items)} productos únicos → scrapeando páginas...")

        products = []
        total_n  = len(all_items)
        for i, (pid, (prod_slug, prod_url)) in enumerate(all_items.items(), 1):
            html = get_html(prod_url)
            if html:
                products.append(parse_product(html, pid, prod_slug, cat_name))
            if i % 20 == 0 or i == total_n:
                log.info(f"    {i}/{total_n} procesados")
            time.sleep(DELAY)

        total_p += len(products)
        if not dry_run and db:
            n = upsert(db, products); total_u += n
            log.info(f"    ✅ {n} upserted\n")
        else:
            log.info("    [dry-run] muestra:")
            for p in products[:3]:
                log.info(f"      {p['id']} | {p['nombre_comercial'][:40]} | {p['precio']}€")
            log.info("")

    log.info("━"*55)
    log.info(f"  Total: {total_p} productos, {total_u} upserted")
    log.info("━"*55)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cat", help="Ej: bebidas")
    args = ap.parse_args()
    main(dry_run=args.dry_run, only_cat=args.cat)
