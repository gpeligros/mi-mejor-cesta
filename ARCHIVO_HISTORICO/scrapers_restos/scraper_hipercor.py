"""
scraper_hipercor.py — Hipercor → Supabase
URL: hipercor.es/supermercado/{categoria}/
ID producto: número largo al inicio del slug (ej: 0110118622500488)
"""
import argparse, json, logging, math, os, re, time
from curl_cffi import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

BASE_URL   = "https://www.hipercor.es"
TABLE_NAME = "precios_hipercor"
PAGE_SIZE  = 24
MAX_PAGES  = 100
DELAY      = 0.8
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

CATEGORIES = [
    ("supermercado/alimentacion",         "Alimentación"),
    ("supermercado/frescos",              "Frescos"),
    ("supermercado/bebidas",              "Bebidas"),
    ("supermercado/congelados",           "Congelados"),
    ("supermercado/drogueria-y-limpieza", "Droguería"),
    ("supermercado/perfumeria-e-higiene", "Perfumería"),
    ("supermercado/bebe",                 "Bebé"),
    ("supermercado/mascotas",             "Mascotas"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": BASE_URL,
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("hipercor")

_session = requests.Session(impersonate="chrome124")

def get_html(url, retries=3):
    for attempt in range(retries):
        try:
            r = _session.get(url, headers=HEADERS, timeout=25)
            if r.status_code == 200: return r.text
            log.warning(f"HTTP {r.status_code}: {url}")
        except Exception as e:
            log.warning(f"Error ({attempt+1}/{retries}): {e}")
        time.sleep(DELAY * (attempt + 1))
    return None

def extract_product_links(html):
    """
    Hipercor: URLs de producto tienen formato
    /supermercado/NNNNNNNNNNNNNNNN-slug-del-producto/
    donde N es un código numérico largo (EAN o similar)
    """
    items = {}
    soup  = BeautifulSoup(html, "html.parser")
    total = None

    for pat in [r'"totalResults"\s*:\s*(\d+)', r'"total"\s*:\s*(\d+)',
                r'"numberOfResults"\s*:\s*(\d+)']:
        m = re.search(pat, html)
        if m: total = int(m.group(1)); break

    # JSON-LD ItemList
    for script in soup.find_all("script", type="application/ld+json"):
        try: data = json.loads(script.string or "")
        except: continue
        if data.get("@type") != "ItemList": continue
        for item in data.get("itemListElement", []):
            url = item.get("url", "")
            m = re.search(r"/supermercado/(\d{10,}-[^/?#]+)/?$", url)
            if m:
                full_slug = m.group(1)
                pid = re.match(r"(\d+)-", full_slug)
                pid = pid.group(1) if pid else full_slug[:16]
                full_url = url if url.startswith("http") else BASE_URL + url
                items[pid] = (full_slug, full_url)

    # Fallback: links <a>
    if not items:
        for a in soup.find_all("a", href=True):
            href = a["href"].rstrip("/")
            m = re.search(r"/supermercado/(\d{10,}-[^/?#]+)/?$", href)
            if m:
                full_slug = m.group(1)
                pid = re.match(r"(\d+)-", full_slug)
                pid = pid.group(1) if pid else full_slug[:16]
                if pid not in items:
                    full = href if href.startswith("http") else BASE_URL + href
                    items[pid] = (full_slug, full)

    return items, total

def get_subcategories(base_slug):
    html = get_html(f"{BASE_URL}/{base_slug}/")
    if not html: return [(base_slug, base_slug.split("/")[-1])]

    items, _ = extract_product_links(html)
    if items: return [(base_slug, base_slug.split("/")[-1])]

    soup    = BeautifulSoup(html, "html.parser")
    subcats = []
    seen    = set()
    section = base_slug.split("/")[-1]  # ej: "bebidas"
    pat     = re.compile(r"^/supermercado/" + re.escape(section) + r"/([^/?#]+)/?$")

    for a in soup.find_all("a", href=True):
        href = a["href"].rstrip("/").split("?")[0]
        m    = pat.match(href)
        if m and href not in seen:
            seen.add(href)
            subcats.append((href.lstrip("/"), a.get_text(strip=True) or m.group(1)))

    return subcats if subcats else [(base_slug, section)]

def scrape_slug(slug, label):
    all_items = {}
    max_pages = MAX_PAGES

    for page in range(max_pages):
        url  = f"{BASE_URL}/{slug}/?start={page * PAGE_SIZE}" if page > 0 else f"{BASE_URL}/{slug}/"
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
    name = re.sub(r"^\d+-", "", slug_prod).replace("-", " ").title()
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

    # Precio en JSON embebido si JSON-LD no lo tiene
    if price == 0.0:
        for pat in [r'"price"\s*:\s*"?([\d.,]+)"?',
                    r'"currentPrice"\s*:\s*"?([\d.,]+)"?',
                    r'([\d]+[.,][\d]{2})\s*€']:
            m = re.search(pat, html)
            if m:
                try:
                    price = float(m.group(1).replace(",", "."))
                    if 0 < price < 10000: break
                except: pass

    return {
        "id": f"HC-{pid}", "id_api": pid,
        "nombre_comercial": name.strip(), "precio": price,
        "marca": brand.strip(),
        "url": f"{BASE_URL}/supermercado/{slug_prod}/",
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
    log.info("━"*55); log.info("  SCRAPER HIPERCOR"); log.info("━"*55)
    db = None
    if not dry_run:
        try: db = get_supabase(); log.info("✅ Supabase conectado")
        except Exception as e: log.warning(f"⚠️  {e} → dry_run"); dry_run = True

    cats = [(s, n) for s, n in CATEGORIES if not only_cat or s.endswith(only_cat)]
    log.info(f"📋 {len(cats)} categorías\n")

    total_p = total_u = 0
    for base_slug, cat_name in cats:
        log.info(f"📦  {cat_name}")

        subcats = get_subcategories(base_slug)
        log.info(f"    {len(subcats)} subcategorías")

        all_items = {}
        for subslug, sublabel in subcats:
            items = scrape_slug(subslug, sublabel)
            all_items.update(items)

        if not all_items:
            log.info("    Sin productos.\n"); continue

        log.info(f"    {len(all_items)} productos → scrapeando...")

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
    ap.add_argument("--cat")
    args = ap.parse_args()
    main(dry_run=args.dry_run, only_cat=args.cat)
