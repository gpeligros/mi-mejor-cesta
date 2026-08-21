"""
scraper_eroski.py — Eroski → Supabase (tabla precios_eroski)
URLs verificadas del sitio real.
Estrategia: categoría → descubrir subcategorías → paginar cada subcategoría → producto
"""
import argparse, json, logging, math, os, re, time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

BASE_URL   = "https://supermercado.eroski.es"
TABLE_NAME = "precios_eroski"
PAGE_SIZE  = 24
MAX_PAGES  = 100
DELAY      = 0.7
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# IDs y slugs verificados directamente desde la web
CATEGORIES = [
    ("2059806-alimentacion",   "Alimentación"),
    ("2059698-frescos",        "Frescos"),
    ("2060211-bebidas",        "Bebidas"),
    ("2059919-congelados",     "Congelados"),
    # Pendientes — añadir cuando tengamos las URLs:
    # ("XXXXXXX-dulces-y-desayuno",    "Dulces y desayuno"),
    # ("XXXXXXX-higiene-y-belleza",    "Higiene y belleza"),
    # ("XXXXXXX-limpieza",             "Limpieza"),
    # ("XXXXXXX-bebe",                 "Bebé"),
    # ("XXXXXXX-mascotas",             "Mascotas"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("eroski")


def get_html(url, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.text
            log.warning(f"HTTP {r.status_code}: {url}")
        except Exception as e:
            log.warning(f"Error ({attempt+1}/{retries}): {e}")
        time.sleep(DELAY * (attempt + 1))
    return None


def get_subcategories(cat_slug):
    """
    Descarga la página de categoría y extrae los links a subcategorías.
    Formato URL subcategoría: /es/supermercado/{cat_slug}/{subcat_id}-{subcat_name}/
    Si la categoría tiene productos directos, la devuelve tal cual.
    """
    url  = f"{BASE_URL}/es/supermercado/{cat_slug}/"
    html = get_html(url)
    if not html:
        return [(cat_slug, cat_slug.split("-", 1)[-1])]

    soup    = BeautifulSoup(html, "html.parser")
    subcats = []
    seen    = set()
    # Links con patrón /es/supermercado/{cat_slug}/{subcat}/
    pat = re.compile(rf"/es/supermercado/{re.escape(cat_slug)}/(\d+-[^/?#]+)/?$")
    for a in soup.find_all("a", href=True):
        m = pat.search(a["href"])
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            label = a.get_text(strip=True) or m.group(1).split("-", 1)[-1]
            subcats.append((f"{cat_slug}/{m.group(1)}", label))

    if subcats:
        log.info(f"    → {len(subcats)} subcategorías encontradas")
        return subcats

    # Sin subcategorías: la propia categoría tiene productos directos
    return [(cat_slug, cat_slug.split("-", 1)[-1])]


def get_product_links(cat_full_slug):
    """Pagina una categoría/subcategoría y devuelve todos los slugs de producto."""
    all_items = {}
    max_pages = MAX_PAGES

    for page in range(max_pages):
        url  = f"{BASE_URL}/es/supermercado/{cat_full_slug}/"
        if page > 0:
            url += f"?page={page}"
        html = get_html(url)
        if not html:
            break

        soup  = BeautifulSoup(html, "html.parser")
        found = {}
        total = None

        # Total de productos en la página
        for pat in [r'"totalResults"\s*:\s*(\d+)', r'"total"\s*:\s*(\d+)',
                    r'"numberOfResults"\s*:\s*(\d+)']:
            m = re.search(pat, html)
            if m:
                total = int(m.group(1))
                break

        # JSON-LD ItemList
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except Exception:
                continue
            if data.get("@type") != "ItemList":
                continue
            for item in data.get("itemListElement", []):
                prod_url = item.get("url", "")
                # /es/supermercado/.../slug-12345/
                m = re.search(r"/es/supermercado/.*?/([^/]+-(\d{4,}))/?$", prod_url)
                if m:
                    found[m.group(2)] = (m.group(1), prod_url)

        # Fallback: links <a> con patrón de producto
        if not found:
            for a in soup.find_all("a", href=True):
                m = re.search(r"/es/supermercado/.*?/([^/]+-(\d{4,}))/?$", a["href"])
                if m and m.group(2) not in found:
                    full = a["href"] if a["href"].startswith("http") else BASE_URL + a["href"]
                    found[m.group(2)] = (m.group(1), full)

        if page == 0:
            if not found:
                log.info(f"      Sin productos en {url}")
                break
            if total:
                max_pages = min(math.ceil(total / PAGE_SIZE), MAX_PAGES)

        new = {pid: v for pid, v in found.items() if pid not in all_items}
        if not new:
            break

        all_items.update(new)
        log.info(f"      Pág {page}: +{len(new)} (acum: {len(all_items)})")
        time.sleep(DELAY)

    return all_items


def parse_product(html, pid, slug, cat_name):
    name = slug.split("-", 1)[-1].replace("-", " ").title() if "-" in slug else slug
    price, brand, imagen = 0.0, "", ""
    disponible = True

    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        if data.get("@type") not in ("Product", "IndividualProduct"):
            continue
        name   = data.get("name", name)
        imagen = data.get("image", imagen)
        if isinstance(imagen, list):
            imagen = imagen[0] if imagen else ""
        rb    = data.get("brand") or {}
        brand = rb.get("name", brand) if isinstance(rb, dict) else str(rb)
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

    if price == 0.0:
        for pat in [r'"price"\s*:\s*"?([\d.,]+)"?', r'([\d]+[.,][\d]{2})\s*€']:
            m = re.search(pat, html)
            if m:
                try:
                    price = float(m.group(1).replace(",", "."))
                    if 0 < price < 10000:
                        break
                except Exception:
                    pass

    return {
        "id": f"ER-{pid}", "id_api": pid,
        "nombre_comercial": name.strip(), "precio": price,
        "marca": brand.strip(),
        "url": f"{BASE_URL}/es/supermercado/{slug}/{pid}/",
        "imagen": imagen, "disponible": disponible,
        "categoria": cat_name, "formato": "",
    }


def get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert(client, products):
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    for p in products:
        p["actualizado"] = now
    total = 0
    for i in range(0, len(products), 200):
        batch = products[i:i+200]
        for attempt in range(4):
            try:
                res = client.table(TABLE_NAME).upsert(batch, on_conflict="id_api").execute()
                total += len(res.data) if res.data else len(batch)
                break
            except Exception as e:
                if attempt < 3:
                    time.sleep(5 * (attempt + 1))
                else:
                    log.error(f"Upsert fallido: {e}")
        time.sleep(0.2)
    return total


def main(dry_run=False, only_cat=None):
    log.info("━" * 55)
    log.info("  SCRAPER EROSKI")
    log.info("━" * 55)

    db = None
    if not dry_run:
        try:
            db = get_supabase()
            log.info("✅ Supabase conectado")
        except Exception as e:
            log.warning(f"⚠️  {e} → dry_run")
            dry_run = True

    cats = [(s, n) for s, n in CATEGORIES
            if not only_cat or only_cat in s]
    log.info(f"📋 {len(cats)} categorías\n")

    total_p = total_u = 0

    for cat_slug, cat_name in cats:
        log.info(f"📦  {cat_name}  [{cat_slug}]")

        subcats = get_subcategories(cat_slug)

        all_items = {}
        for subslug, sublabel in subcats:
            log.info(f"  ↳ {sublabel}")
            items = get_product_links(subslug)
            all_items.update(items)

        if not all_items:
            log.info("    Sin productos.\n")
            continue

        log.info(f"    {len(all_items)} productos únicos — scrapeando...")

        products = []
        total_n  = len(all_items)
        for i, (pid, (prod_slug, prod_url)) in enumerate(all_items.items(), 1):
            html = get_html(prod_url if prod_url.startswith("http")
                            else f"{BASE_URL}/es/supermercado/{prod_slug}/{pid}/")
            if html:
                products.append(parse_product(html, pid, prod_slug, cat_name))
            if i % 20 == 0 or i == total_n:
                log.info(f"    {i}/{total_n} procesados")
            time.sleep(DELAY)

        total_p += len(products)

        if not dry_run and db:
            n = upsert(db, products)
            total_u += n
            log.info(f"    ✅ {n} upserted\n")
        else:
            log.info("    [dry-run] muestra:")
            for p in products[:3]:
                log.info(f"      {p['id']} | {p['nombre_comercial'][:40]} | {p['precio']}€")
            log.info("")

    log.info("━" * 55)
    log.info(f"  Total: {total_p} productos, {total_u} upserted")
    log.info("━" * 55)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cat", help="filtrar por slug de categoría")
    args = ap.parse_args()
    main(dry_run=args.dry_run, only_cat=args.cat)
