# Mejora Scrapers DIA / Alcampo / Ahorramas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reescribir los scrapers de DIA, Alcampo y Ahorramas siguiendo el patrón híbrido (API curl_cffi + Scrapling fallback) de `scraper_carrefour.py` para maximizar el número de productos capturados.

**Architecture:** Cada scraper sigue el patrón de Carrefour: intento de API JSON con `curl_cffi impersonate chrome124`, fallback a `Scrapling StealthyFetcher` con renderizado JS para la primera página, y `curl_cffi` para paginación posterior. Schema unificado con campos `id`, `id_api`, `nombre_comercial`, `precio`, `precio_unidad`, `marca`, `ean`, `url`, `imagen`, `disponible`, `formato`, `actualizado`. DIA y Ahorramas mantienen IDs secuenciales (`DI-XXXX`, `AH-XXXX`); Alcampo usa `AL-{pid}` directo.

**Tech Stack:** Python 3.10+, curl_cffi 0.15, Scrapling 0.4.7, supabase 2.27, beautifulsoup4 4.14, python-dotenv, pytest

---

> **Nota de scope:** Los tres scrapers son subsistemas independientes. Cada tarea está organizada por scraper y puede ejecutarse en sesiones separadas. Las tablas `productos_catalogo`, `categorias_maestras`, `productos_match`, `precios_carrefour` y `precios_mercadona` son INTOCABLES.

---

## Archivos a crear / modificar

| Acción | Archivo | Responsabilidad |
|---|---|---|
| Crear | `scrapers/tests/__init__.py` | Paquete de tests |
| Crear | `scrapers/tests/test_scraper_dia.py` | Unit tests parser DIA |
| Crear | `scrapers/tests/test_scraper_alcampo.py` | Unit tests parser Alcampo |
| Crear | `scrapers/tests/test_scraper_ahorramas.py` | Unit tests parser Ahorramas |
| Modificar | `scrapers/scraper_dia.py` | Reescritura completa |
| Modificar | `scrapers/scraper_alcampo.py` | Reescritura completa |
| Modificar | `scrapers/scraper_ahorramas.py` | Reescritura completa |

---

## Task 1: Estructura de tests

**Files:**
- Create: `scrapers/tests/__init__.py`

- [ ] **Step 1: Crear el paquete de tests**

```bash
# Desde la raíz del proyecto
echo "" > scrapers/tests/__init__.py
```

- [ ] **Step 2: Verificar que pytest funciona**

```bash
cd scrapers
python -m pytest tests/ -v
```

Expected: `no tests ran` (0 items, sin error).

- [ ] **Step 3: Commit inicial**

```bash
git add scrapers/tests/__init__.py
git commit -m "test: crear estructura de tests para scrapers"
```

---

## Task 2: Tests unitarios — scraper_dia.py

**Files:**
- Create: `scrapers/tests/test_scraper_dia.py`

- [ ] **Step 1: Escribir los tests que deben fallar**

Crear `scrapers/tests/test_scraper_dia.py` con el contenido siguiente. Estos tests importan funciones que aún no existen en el nuevo `scraper_dia.py`, por lo que fallarán:

```python
"""Tests unitarios para scraper_dia.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from scraper_dia import parse_api_product, extract_total_dia


# ─── parse_api_product ────────────────────────────────────────────────────────

def test_parse_api_product_completo():
    item = {
        "sku_id": "12345",
        "display_name": "Leche entera Celta 1 L",
        "prices": {
            "price": 1.29,
            "price_per_unit": 1.29,
            "measure_unit": "LITRO",
        },
        "brand": "Celta",
        "ean": "8410188012345",
        "image": "/images/leche.jpg",
        "url": "/p/leche-celta-1l/12345",
    }
    result = parse_api_product(item)
    assert result is not None
    assert result["id_api"] == "12345"
    assert result["nombre_comercial"] == "Leche entera Celta 1 L"
    assert result["precio"] == 1.29
    assert result["precio_unidad"] == "1.29€/L"
    assert result["marca"] == "Celta"
    assert result["ean"] == "8410188012345"
    assert result["imagen"] == "https://www.dia.es/images/leche.jpg"
    assert result["url"] == "https://www.dia.es/p/leche-celta-1l/12345"
    assert result["disponible"] is True
    assert result["formato"] == "1 L"


def test_parse_api_product_sin_precio_unidad():
    item = {
        "sku_id": "99999",
        "display_name": "Galletas María",
        "prices": {"price": 0.85},
        "brand": "Fontaneda",
    }
    result = parse_api_product(item)
    assert result is not None
    assert result["precio"] == 0.85
    assert result["precio_unidad"] == ""
    assert result["ean"] == ""


def test_parse_api_product_sin_sku_devuelve_none():
    item = {"display_name": "Sin SKU", "prices": {"price": 1.0}}
    assert parse_api_product(item) is None


def test_parse_api_product_kilogramo():
    item = {
        "sku_id": "11111",
        "display_name": "Arroz redondo 1 kg",
        "prices": {
            "price": 0.99,
            "price_per_unit": 0.99,
            "measure_unit": "KILOGRAMO",
        },
        "brand": "DIA",
    }
    result = parse_api_product(item)
    assert result["precio_unidad"] == "0.99€/kg"
    assert result["formato"] == "1 kg"


# ─── extract_total_dia ────────────────────────────────────────────────────────

def test_extract_total_dia_pagination():
    data = {"pagination": {"total_pages": 5, "page": 1}}
    assert extract_total_dia(data) == 5


def test_extract_total_dia_sin_pagination():
    data = {}
    assert extract_total_dia(data) == 1
```

- [ ] **Step 2: Ejecutar para verificar que fallan**

```bash
cd scrapers
python -m pytest tests/test_scraper_dia.py -v
```

Expected: `ImportError: cannot import name 'parse_api_product' from 'scraper_dia'` (las funciones aún no existen en el nuevo scraper).

---

## Task 3: Reescribir scraper_dia.py

**Files:**
- Modify: `scrapers/scraper_dia.py` (reescritura completa)

- [ ] **Step 1: Reemplazar todo el contenido de scraper_dia.py**

```python
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

# Fallback si /categories no responde — IDs numéricos que funcionan en la API actual
CATEGORIES_FALLBACK = [
    ("01", "frutas-y-verduras",          "Frutas y verduras"),
    ("02", "carne-y-charcuteria",         "Carnes y charcutería"),
    ("03", "pescado-y-marisco",           "Pescado y marisco"),
    ("04", "lacteos-y-huevos",            "Lácteos y huevos"),
    ("05", "panaderia-y-bolleria",        "Panadería y bollería"),
    ("06", "congelados",                  "Congelados"),
    ("07", "bebidas",                     "Bebidas"),
    ("08", "bodega",                      "Bodega"),
    ("09", "aceite-vinagre-y-especias",   "Aceite, vinagre y especias"),
    ("10", "arroz-pasta-y-legumbres",     "Arroz, pasta y legumbres"),
    ("11", "conservas-y-platos-preparados","Conservas y platos preparados"),
    ("12", "salsas-y-condimentos",        "Salsas y condimentos"),
    ("13", "desayuno-y-merienda",         "Desayuno y merienda"),
    ("14", "aperitivos-y-snacks",         "Aperitivos y snacks"),
    ("15", "higiene-y-cosmetica",         "Higiene y cosmética"),
    ("16", "limpieza-del-hogar",          "Limpieza del hogar"),
    ("17", "bebes",                       "Bebés"),
    ("18", "mascotas",                    "Mascotas"),
]

UNIT_MAP = {
    "LITRO": "L", "LITROS": "L",
    "KILOGRAMO": "kg", "KILO": "kg", "KILOS": "kg",
    "GRAMO": "g", "GRAMOS": "g",
    "MILILITRO": "ml", "MILILITROS": "ml",
    "CENTILITRO": "cl", "CENTILITROS": "cl",
    "UNIDAD": "ud", "UNIDADES": "ud",
    "METRO": "m", "METROS": "m",
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
    """Intenta obtener categorías desde la API. Fallback a CATEGORIES_FALLBACK."""
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
                    log.info(f"  📋 Categorías dinámicas: {len(result)}")
                    return result
    except Exception as e:
        log.debug(f"  categories API: {e}")
    log.info(f"  📋 Usando categorías fallback: {len(CATEGORIES_FALLBACK)}")
    return CATEGORIES_FALLBACK

# ─── API (curl_cffi) ─────────────────────────────────────────────────────────

def try_api(cat_id, page=1, retries=2):
    """Llama a la API de DIA. Devuelve lista de items crudos o None si falla."""
    params = {
        "categoryId": cat_id,
        "page":       page,
        "pageSize":   PAGE_SIZE,
    }
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
    """Extrae el número total de páginas de la respuesta de la API."""
    pag = data.get("pagination", {}) if isinstance(data, dict) else {}
    return int(pag.get("total_pages", 1))

# ─── PARSEO ───────────────────────────────────────────────────────────────────

def parse_api_product(item):
    """Normaliza un item de la API DIA al schema unificado."""
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

        # precio_unidad
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

        # ean
        ean = str(item.get("ean") or item.get("gtin") or "").strip()

        # imagen y url (pueden ser relativas)
        imagen = item.get("image") or ""
        if imagen and not imagen.startswith("http"):
            imagen = BASE_URL + imagen
        url = item.get("url") or ""
        if url and not url.startswith("http"):
            url = BASE_URL + url

        # formato desde el nombre
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

_stealthy_session = None

def get_stealthy_session():
    global _stealthy_session
    if _stealthy_session is None:
        from scrapling.fetchers import StealthySession
        log.info("    🦊 Abriendo navegador stealth (primera vez, ~5s)...")
        _stealthy_session = StealthySession(
            headless=True,
            solve_cloudflare=True,
            network_idle=True,
            block_webrtc=True,
            disable_resources=False,
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

def extract_total_from_html(html):
    """Extrae el total de productos desde el HTML renderizado."""
    for pat in [
        r'"total"\s*:\s*(\d+)',
        r'"totalResults"\s*:\s*(\d+)',
        r'"total_pages"\s*:\s*(\d+)',
        r'(\d+)\s+productos',
    ]:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0

def extract_products_from_html(html):
    """Extrae productos del HTML renderizado de DIA."""
    if not html:
        return []

    # Intento 1: buscar JSON de productos embebido
    for pat in [
        r'"search_items"\s*:\s*(\[.*?\])\s*[,}]',
        r'"products"\s*:\s*(\[.*?\])\s*[,}]',
        r'window\["products"\]\s*=\s*(\[.*?\]);',
    ]:
        m = re.search(pat, html, re.DOTALL)
        if m:
            try:
                items = json.loads(m.group(1))
                prods = [parse_api_product(it) for it in items]
                prods = [p for p in prods if p]
                if prods:
                    log.debug(f"    JSON embebido: {len(prods)} productos")
                    return prods
            except Exception as e:
                log.debug(f"    JSON parse error: {e}")

    # Intento 2: JSON-LD
    soup  = BeautifulSoup(html, "html.parser")
    prods = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data  = json.loads(script.string or "")
        except Exception:
            continue
        items = data.get("itemListElement", []) if isinstance(data, dict) else []
        for it in items:
            item = it.get("item", it)
            if item.get("@type") not in ("Product", "IndividualProduct"):
                continue
            p = _parse_jsonld_product_dia(item)
            if p:
                prods.append(p)
    if prods:
        return prods

    # Intento 3: tarjetas HTML
    for sel in [
        '[data-testid="product-card"]',
        'article.product-card',
        '[class*="product-card"]',
        '[data-pid]',
    ]:
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
    """Renderiza la primera página de categoría con Scrapling."""
    url = f"{BASE_URL}/compra-online/{cat_slug}/{cat_id}/c"
    for attempt in range(retries):
        try:
            session = get_stealthy_session()
            page    = session.fetch(url, timeout=60000)
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
    """Obtiene páginas 2..N con curl_cffi."""
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
                log.warning(f"    página {page}: HTTP {r.status_code} → parando")
                break
            prods = extract_products_from_html(r.text)
            new   = [p for p in prods if p["id_api"] not in seen]
            seen.update(p["id_api"] for p in new)
            all_products.extend(new)
            if not new:
                break
        except Exception as e:
            log.warning(f"    página {page}: {e} → parando")
            break
        time.sleep(PAGINATION_DELAY)
    return all_products

# ─── IDs SECUENCIALES ────────────────────────────────────────────────────────

def get_existing_id_map(client):
    """Obtiene {id_api: id} de Supabase para mantener IDs secuenciales."""
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
    """Asigna DI-XXXX manteniendo IDs existentes en Supabase."""
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
    log.info("━" * 55)
    log.info("  SCRAPER DIA (híbrido API + Scrapling)")
    log.info("━" * 55)

    db     = None
    id_map = {}
    if not dry_run:
        try:
            db     = get_supabase()
            id_map = get_existing_id_map(db)
            log.info(f"✅ Supabase conectado — {len(id_map)} IDs existentes")
        except Exception as e:
            log.warning(f"⚠️  Supabase: {e} → modo dry_run")
            dry_run = True

    categories = get_categories()
    if only_cat:
        categories = [(cid, sl, nm) for cid, sl, nm in categories if only_cat in cid or only_cat in nm.lower()]
    log.info(f"📋 {len(categories)} categorías\n")

    all_products = {}  # id_api → producto (deduplicar)
    total_upserted = 0

    for cat_id, cat_slug, cat_name in categories:
        log.info(f"📦  {cat_name}  [{cat_id}]")
        products_raw = []

        # FASE 1: API
        if not force_stealth:
            log.info("    ⚡ Intentando API DIA...")
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
                log.info(f"    ✅ API: {len(products_raw)} items crudos")

        # FASE 2: Scrapling si la API falló
        if not products_raw:
            log.info("    🦊 Fallback → Scrapling")
            html, total_str = scrape_first_page(cat_id, cat_slug, debug=debug)
            page_products   = extract_products_from_html(html)
            if not page_products:
                log.info("    ❌ Sin productos\n")
                continue
            log.info(f"    ✅ Pág. 1: {len(page_products)} productos")
            # Intentar paginar el HTML también
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

    # Asignar IDs y subir
    productos_lista = list(all_products.values())
    productos_lista = assign_ids(productos_lista, id_map)

    log.info("━" * 55)
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

    log.info("━" * 55)
    close_stealthy_session()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run",  action="store_true", help="No escribe en Supabase")
    ap.add_argument("--cat",      help="Filtrar por ID o nombre de categoría")
    ap.add_argument("--stealth",  action="store_true", help="Forzar Scrapling desde el inicio")
    ap.add_argument("--debug",    action="store_true", help="Guarda HTML de cada categoría")
    args = ap.parse_args()
    try:
        main(dry_run=args.dry_run, only_cat=args.cat,
             force_stealth=args.stealth, debug=args.debug)
    finally:
        close_stealthy_session()
```

- [ ] **Step 2: Ejecutar los tests — deben pasar**

```bash
cd scrapers
python -m pytest tests/test_scraper_dia.py -v
```

Expected: todos los tests en `PASSED`.

- [ ] **Step 3: Verificar que el scraper corre en dry-run**

```bash
cd scrapers
python scraper_dia.py --dry-run --cat 07
```

Expected: log mostrando categoría "Bebidas", productos descargados, sin error de Supabase.

- [ ] **Step 4: Commit**

```bash
git add scrapers/scraper_dia.py scrapers/tests/test_scraper_dia.py
git commit -m "feat: reescribir scraper_dia.py con patron hibrido API+Scrapling"
```

---

## Task 4: Tests unitarios — scraper_alcampo.py

**Files:**
- Create: `scrapers/tests/test_scraper_alcampo.py`

- [ ] **Step 1: Escribir los tests que deben fallar**

```python
"""Tests unitarios para scraper_alcampo.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from scraper_alcampo import extract_products_from_html, parse_api_product


# ─── parse_api_product ────────────────────────────────────────────────────────

def test_parse_api_product_completo():
    item = {
        "id":    "123456",
        "name":  "Leche entera 1 L",
        "price": {"value": 1.29, "referencePrice": "1,29 €/L"},
        "brand": {"name": "Celta"},
        "ean":   "8410188012345",
        "image": "https://cdn.alcampo.es/leche.jpg",
        "availability": "inStock",
        "slug":  "leche-entera-1-l",
    }
    result = parse_api_product(item)
    assert result is not None
    assert result["id_api"] == "123456"
    assert result["id"] == "AL-123456"
    assert result["nombre_comercial"] == "Leche entera 1 L"
    assert result["precio"] == 1.29
    assert result["precio_unidad"] == "1,29 €/L"
    assert result["marca"] == "Celta"
    assert result["ean"] == "8410188012345"
    assert result["disponible"] is True


def test_parse_api_product_sin_id_devuelve_none():
    item = {"name": "Sin ID", "price": {"value": 1.0}}
    assert parse_api_product(item) is None


def test_parse_api_product_precio_como_float():
    item = {
        "id":    "99999",
        "name":  "Agua mineral 1.5 L",
        "price": 0.49,   # a veces el precio llega como float directo
    }
    result = parse_api_product(item)
    assert result is not None
    assert result["precio"] == 0.49


# ─── extract_products_from_html ───────────────────────────────────────────────

def test_extract_from_jsonld_itemlist():
    html = """<html><body>
    <script type="application/ld+json">
    {"@type": "ItemList", "itemListElement": [
        {"url": "https://www.compraonline.alcampo.es/products/leche-entera-1l/654321",
         "item": {
           "@type": "Product",
           "name": "Leche entera 1 L",
           "offers": {"price": "1.29", "availability": "https://schema.org/InStock"},
           "brand": {"name": "Celta"},
           "image": "https://cdn.alcampo.es/leche.jpg"
         }}
    ]}
    </script></body></html>"""
    prods = extract_products_from_html(html)
    assert len(prods) >= 1
    assert prods[0]["id_api"] == "654321"
    assert prods[0]["precio"] == 1.29
    assert prods[0]["id"] == "AL-654321"


def test_extract_from_html_vacio_devuelve_lista_vacia():
    assert extract_products_from_html("") == []
    assert extract_products_from_html(None) == []
```

- [ ] **Step 2: Ejecutar para verificar que fallan**

```bash
cd scrapers
python -m pytest tests/test_scraper_alcampo.py -v
```

Expected: `ImportError` — las funciones aún no existen en el nuevo `scraper_alcampo.py`.

---

## Task 5: Reescribir scraper_alcampo.py

**Files:**
- Modify: `scrapers/scraper_alcampo.py` (reescritura completa)

- [ ] **Step 1: Reemplazar todo el contenido de scraper_alcampo.py**

```python
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
    # Alimentación
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
    # Droguería, perfumería y bebé
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
        avail  = item.get("availability") or item.get("stock") or ""
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
        log.info("    🦊 Abriendo navegador stealth (primera vez, ~5s)...")
        _stealthy_session = StealthySession(
            headless=True,
            solve_cloudflare=True,
            network_idle=True,
            block_webrtc=True,
            disable_resources=False,
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
                # Puede estar anidado — buscar lista de productos
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
        item  = it.get("item", it)
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
        slug   = ""
        link   = card.find("a", href=True)
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
            page    = session.fetch(url, timeout=60000)
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
                log.warning(f"    página {page}: HTTP {r.status_code} → parando")
                break
            prods = extract_products_from_html(r.text)
            new   = [p for p in prods if p["id_api"] not in seen]
            seen.update(p["id_api"] for p in new)
            all_products.extend(new)
            if not new:
                break
        except Exception as e:
            log.warning(f"    página {page}: {e} → parando")
            break
        time.sleep(PAGINATION_DELAY)
    log.info(f"    📄 Paginación: {len(all_products)} productos adicionales")
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
    log.info("━" * 55)
    log.info("  SCRAPER ALCAMPO (híbrido API + Scrapling)")
    log.info("━" * 55)

    db = None
    if not dry_run:
        try:
            db = get_supabase()
            log.info("✅ Supabase conectado")
        except Exception as e:
            log.warning(f"⚠️  Supabase: {e} → modo dry_run")
            dry_run = True

    cats = [(cid, sl, nm) for cid, sl, nm in CATEGORIES
            if not only_cat or only_cat in cid or only_cat in sl]
    log.info(f"📋 {len(cats)} categorías\n")

    total_p = total_u = 0
    seen_global = set()

    for cat_id, slug, cat_name in cats:
        log.info(f"📦  {cat_name}  [{cat_id}]")
        products_raw = []

        # FASE 1: API
        if not force_stealth:
            log.info("    ⚡ Intentando API Alcampo...")
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
                log.info(f"    ✅ API: {len(products_raw)} items")

        # FASE 2: Scrapling si la API falló
        if not products_raw:
            log.info("    🦊 Fallback → Scrapling")
            html, total = scrape_first_page(cat_id, slug, debug=debug)
            page_prods  = extract_products_from_html(html)
            if not page_prods:
                log.info("    ❌ Sin productos\n")
                continue
            log.info(f"    ✅ Pág. 1: {len(page_prods)} (total anunciado: {total})")
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
            log.info(f"    ✅ {n} upserted")
        elif dry_run:
            for p in new_prods[:3]:
                log.info(f"      {p['id']} | {p['nombre_comercial'][:45]} | "
                         f"{p.get('precio')}€ | {p.get('precio_unidad')}")
        log.info("")
        time.sleep(DELAY)

    close_stealthy_session()
    log.info("━" * 55)
    log.info(f"  Total productos : {total_p}")
    log.info(f"  Total upserted  : {total_u}")
    log.info("━" * 55)


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
```

- [ ] **Step 2: Ejecutar los tests — deben pasar**

```bash
cd scrapers
python -m pytest tests/test_scraper_alcampo.py -v
```

Expected: todos los tests en `PASSED`.

- [ ] **Step 3: Verificar dry-run**

```bash
cd scrapers
python scraper_alcampo.py --dry-run --cat OC1101
```

Expected: log mostrando "Agua y refrescos", productos o mensaje de fallback, sin traceback.

- [ ] **Step 4: Commit**

```bash
git add scrapers/scraper_alcampo.py scrapers/tests/test_scraper_alcampo.py
git commit -m "feat: reescribir scraper_alcampo.py con patron hibrido API+Scrapling"
```

---

## Task 6: Tests unitarios — scraper_ahorramas.py

**Files:**
- Create: `scrapers/tests/test_scraper_ahorramas.py`

- [ ] **Step 1: Escribir los tests que deben fallar**

```python
"""Tests unitarios para scraper_ahorramas.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from bs4 import BeautifulSoup
from scraper_ahorramas import parsear_producto, parsear_precio, extract_total_ahorramas


# ─── parsear_precio ───────────────────────────────────────────────────────────

def test_parsear_precio_coma():
    assert parsear_precio("2,99 €") == 2.99

def test_parsear_precio_punto():
    assert parsear_precio("2.99€") == 2.99

def test_parsear_precio_entero():
    assert parsear_precio("3 €") == 3.0

def test_parsear_precio_none():
    assert parsear_precio(None) is None

def test_parsear_precio_vacio():
    assert parsear_precio("") is None


# ─── parsear_producto ─────────────────────────────────────────────────────────

def test_parsear_producto_completo():
    html = """
    <div class="product-tile" data-pid="98765">
        <div class="pdp-link"><a href="/leche-entera-98765.html">Leche entera 1L</a></div>
        <div class="price">
            <span class="sales"><span class="value" content="1.29">1,29 €</span></span>
        </div>
        <div class="price-per-unit">1,29 €/L</div>
        <img src="https://www.ahorramas.com/leche.jpg" />
    </div>"""
    soup = BeautifulSoup(html, "html.parser")
    tile = soup.select_one("[data-pid]")
    result = parsear_producto(tile)
    assert result is not None
    assert result["id_api"] == "98765"
    assert result["nombre_comercial"] == "Leche entera 1L"
    assert result["precio"] == 1.29
    assert result["precio_unidad"] == "1,29 €/L"
    assert result["imagen"] == "https://www.ahorramas.com/leche.jpg"


def test_parsear_producto_sin_nombre_devuelve_none():
    html = '<div class="product-tile" data-pid="11111"><div class="price">1,99 €</div></div>'
    soup = BeautifulSoup(html, "html.parser")
    tile = soup.select_one("[data-pid]")
    assert parsear_producto(tile) is None


def test_parsear_producto_pid_desde_url():
    html = """
    <div class="product-tile">
        <div class="pdp-link"><a href="/galletas-maria-22222.html">Galletas María</a></div>
        <div class="price"><span class="sales"><span class="value">0,85 €</span></span></div>
    </div>"""
    soup = BeautifulSoup(html, "html.parser")
    tile = soup.select_one(".product-tile")
    result = parsear_producto(tile)
    assert result is not None
    assert result["id_api"] == "22222"


# ─── extract_total_ahorramas ──────────────────────────────────────────────────

def test_extract_total_json():
    html = '... "total": 245 ...'
    assert extract_total_ahorramas(html) == 245

def test_extract_total_count():
    html = '... "count":112 ...'
    assert extract_total_ahorramas(html) == 112

def test_extract_total_sin_datos():
    assert extract_total_ahorramas("sin datos") == 0
```

- [ ] **Step 2: Ejecutar para verificar que fallan**

```bash
cd scrapers
python -m pytest tests/test_scraper_ahorramas.py -v
```

Expected: `ImportError` — `extract_total_ahorramas` no existe aún.

---

## Task 7: Reescribir scraper_ahorramas.py

**Files:**
- Modify: `scrapers/scraper_ahorramas.py` (reescritura completa)

- [ ] **Step 1: Reemplazar todo el contenido de scraper_ahorramas.py**

```python
"""
scraper_ahorramas.py — Ahorramas España → Supabase
Estrategia híbrida (patrón Carrefour):
  1) Demandware Search-ShowAjax con curl_cffi
  2) Fallback: Scrapling StealthyFetcher
  3) Paginación completa hasta agotar productos

IDs: AH-XXXX secuencial (mantiene IDs existentes en productos_match).
Tabla destino: precios_ahorramas
"""
import argparse, json, logging, os, re, time
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
        log.info("    🦊 Abriendo navegador stealth (~5s)...")
        _stealthy_session = StealthySession(
            headless=True,
            solve_cloudflare=True,
            network_idle=True,
            block_webrtc=True,
            disable_resources=False,
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
    log.info("━" * 55)
    log.info("  SCRAPER AHORRAMAS (híbrido Demandware + Scrapling)")
    log.info("━" * 55)

    db     = None
    id_map = {}
    if not dry_run:
        try:
            db     = get_supabase()
            id_map = get_existing_id_map(db)
            log.info(f"✅ Supabase conectado — {len(id_map)} IDs existentes")
        except Exception as e:
            log.warning(f"⚠️  Supabase: {e} → modo dry_run")
            dry_run = True

    categories = [(cgid, nm) for cgid, nm in CATEGORIES
                  if not only_cat or only_cat in cgid]
    log.info(f"📋 {len(categories)} categorías\n")

    all_products = {}  # id_api → producto
    total_upserted = 0

    for cgid, cat_name in categories:
        log.info(f"📦  {cat_name}  [{cgid}]")
        page_products = []

        # FASE 1: Demandware con curl_cffi
        if not force_stealth:
            log.info("    ⚡ Intentando Demandware API...")
            html, total = try_api(cgid, start=0)
            if html:
                page_products = parse_tiles_from_html(html)
                log.info(f"    ✅ Pág. 1: {len(page_products)} productos (total: {total})")

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
            log.info("    🦊 Fallback → Scrapling")
            html, total = scrape_with_scrapling(cgid)
            if html:
                page_products = parse_tiles_from_html(html)
                log.info(f"    ✅ Scrapling: {len(page_products)} productos")
            if not page_products:
                log.info("    ❌ Sin productos\n")
                continue

        nuevos = 0
        for p in page_products:
            if p["id_api"] and p["id_api"] not in all_products:
                all_products[p["id_api"]] = p
                nuevos += 1
        log.info(f"    +{nuevos} nuevos | total acumulado: {len(all_products)}")
        log.info("")
        time.sleep(DELAY)

    # Asignar IDs y subir
    productos_lista = list(all_products.values())
    productos_lista = assign_ids(productos_lista, id_map)

    log.info("━" * 55)
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

    log.info("━" * 55)
    close_stealthy_session()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run",  action="store_true", help="No escribe en Supabase")
    ap.add_argument("--cat",      help="Filtrar por cgid de categoría")
    ap.add_argument("--stealth",  action="store_true", help="Forzar Scrapling desde el inicio")
    ap.add_argument("--debug",    action="store_true", help="Guarda HTML de cada categoría")
    args = ap.parse_args()
    try:
        main(dry_run=args.dry_run, only_cat=args.cat,
             force_stealth=args.stealth, debug=args.debug)
    finally:
        close_stealthy_session()
```

- [ ] **Step 2: Ejecutar los tests — deben pasar**

```bash
cd scrapers
python -m pytest tests/test_scraper_ahorramas.py -v
```

Expected: todos los tests en `PASSED`.

- [ ] **Step 3: Verificar dry-run**

```bash
cd scrapers
python scraper_ahorramas.py --dry-run --cat bebidas
```

Expected: log mostrando "Bebidas", productos o mensaje de fallback, sin traceback.

- [ ] **Step 4: Commit**

```bash
git add scrapers/scraper_ahorramas.py scrapers/tests/test_scraper_ahorramas.py
git commit -m "feat: reescribir scraper_ahorramas.py con patron hibrido Demandware+Scrapling"
```

---

## Task 8: Verificación final — suite completa de tests

**Files:** ninguno nuevo

- [ ] **Step 1: Ejecutar suite completa**

```bash
cd scrapers
python -m pytest tests/ -v
```

Expected: todos los tests en `PASSED`. Si alguno falla, leer el traceback, corregir el código y volver a ejecutar.

- [ ] **Step 2: Verificar que los tres scrapers importan sin errores**

```bash
cd scrapers
python -c "import scraper_dia; import scraper_alcampo; import scraper_ahorramas; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Dry-run rápido de los tres scrapers (una categoría cada uno)**

```bash
cd scrapers
python scraper_dia.py --dry-run --cat 07
python scraper_alcampo.py --dry-run --cat OC1101
python scraper_ahorramas.py --dry-run --cat bebidas
```

Expected: cada scraper muestra el banner, entra en la categoría indicada, descarga productos (puede ser 0 si la API está caída — lo relevante es que NO hay traceback) y termina sin error.

- [ ] **Step 4: Commit final**

```bash
git add -A
git commit -m "test: verificacion final scrapers DIA, Alcampo y Ahorramas"
```

---

## Notas de implementación

### Si la API de DIA devuelve siempre 0 productos en una categoría
El endpoint `/api/v1/search-back/categories` puede revelar los IDs reales. Si ese endpoint también falla, ejecutar con `--stealth` para que Scrapling renderice la página de categoría y extraiga los productos del HTML.

### Si la API de Alcampo no existe o devuelve 404
El endpoint `/api/v2/page/category` es una hipótesis. Si devuelve 404, el scraper caerá automáticamente a Scrapling. Agregar `--stealth` para forzar Scrapling directamente durante la exploración inicial.

### Si Ahorramas devuelve 0 productos con todos los cgids nuevos
Los cgids de Demandware son jerárquicos. Si un cgid como `panaderia-pasteleria` no existe, Demandware devuelve HTML vacío. El scraper lo detecta (`page_products == []`) y registra "Sin productos". Los cgids válidos son los que ya funcionan (los 9 originales). Los nuevos son una hipótesis — filtrar con `--cat` para probarlos uno a uno.

### Columna precio_unidad en Supabase
Si la tabla no tiene la columna `precio_unidad TEXT`, ejecutar en Supabase SQL editor:
```sql
ALTER TABLE precios_dia       ADD COLUMN IF NOT EXISTS precio_unidad TEXT;
ALTER TABLE precios_alcampo   ADD COLUMN IF NOT EXISTS precio_unidad TEXT;
ALTER TABLE precios_ahorramas ADD COLUMN IF NOT EXISTS precio_unidad TEXT;
```
