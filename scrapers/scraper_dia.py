"""
scraper_dia.py — DIA España -> Supabase (REESCRITO — API nueva, agosto 2026)
==============================================================================
DIA rehizo su web por completo desde la version anterior de este scraper.
Ya no existe /compra-online/{cat}/{id}/c ni la API antigua search-back.

API real descubierta via DevTools (Network tab) el 10/08/2026:
  GET https://www.dia.es/api/v1/plp-back/l1/all/{L1}/reduced?category_id={L2}&page={N}

Estructura de categorias: 2 niveles.
  L1 = departamento (ej. L104 = Verduras)
  L2 = subcategoria (ej. L2023 = Tomates, pimientos y pepinos)
Se itera cada L2 real (no el "todo X" que duplica L1) y se pagina cada una.

Se excluyen a proposito L126 (Sin gluten), L128 (Novedades y recomendados),
L133 (Verano) y L150 (Ofertas) del listado de categorias porque son
colecciones transversales que repiten productos ya cubiertos por su
categoria real -- incluirlas duplicaria trabajo y filas.

Guarda categoria_dia / subcategoria_dia en cada fila (antes se calculaba
y se tiraba sin guardar -- ver CONTEXTO.md).

Tabla destino: precios_dia
IDs: DI-XXXX secuencial (mantiene IDs existentes en productos_match)

Requiere que la migracion SQL haya anadido categoria_dia (ya deberia
existir si se aplico migracion_categorias_scrapers.sql).

USO:
  python scraper_dia.py --dry-run --cat verduras     # prueba 1 categoria
  python scraper_dia.py --dry-run                    # prueba todas, sin subir
  python scraper_dia.py                               # scrape completo real
"""
import argparse, json, logging, os, sys, time
from pathlib import Path
from curl_cffi import requests as curl_requests
from dotenv import load_dotenv
load_dotenv()

# Histórico de precios (P1 #4, 23/08/2026) — módulo hermano en scrapers/
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from historico_precios import registrar_cambios_precio
except ImportError:
    registrar_cambios_precio = None

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BASE_URL   = "https://www.dia.es"
API_PLP    = BASE_URL + "/api/v1/plp-back/l1/all/{l1}/reduced"
TABLE_NAME = "precios_dia"
PREFIJO_ID = "DI"
DELAY      = 0.6          # entre paginas
DELAY_CAT  = 1.0          # entre subcategorias

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ─── CATEGORIAS REALES (descubiertas via DevTools, menu_analytics) ───────────
CATEGORIES_DIA = [
    ("L101", "Quesos", [
        ("L2007", "Curado"), ("L2008", "Fresco"), ("L2009", "Azul y de cabra"),
        ("L2010", "Untable y en porciones"), ("L2011", "Especialidades"),
        ("L2205", "En lonchas"), ("L2345", "Semicurado"), ("L2346", "Tierno"),
        ("L2347", "Rallado"),
    ]),
    ("L102", "Carnes", [
        ("L2013", "Vacuno"), ("L2014", "Cerdo"), ("L2015", "Pavo"),
        ("L2016", "Conejo"), ("L2017", "Hamburguesas carne picada y albondigas"),
        ("L2202", "Pollo"), ("L2265", "Empanados y elaborados"),
        ("L2266", "Arreglos y despieces"),
    ]),
    ("L103", "Pescados y mariscos", [
        ("L2019", "Fresco"), ("L2020", "Ahumado y salazon"),
        ("L2021", "Surimi y elaborados"), ("L2249", "Congelado"),
        ("L2251", "Rebozado"), ("L2253", "Marisco gamba y calamar"),
    ]),
    ("L104", "Verduras", [
        ("L2022", "Ajos cebollas y puerros"), ("L2023", "Tomates pimientos y pepinos"),
        ("L2024", "Brocoli coliflor y judias verdes"),
        ("L2025", "Verduras congeladas y al vapor"), ("L2026", "Conservas de verduras"),
        ("L2027", "Lechugas y hojas verdes"), ("L2028", "Patatas y zanahorias"),
        ("L2029", "Setas y champinones"), ("L2030", "Ensaladas y verduras preparadas"),
        ("L2031", "Hierbas aromaticas"), ("L2181", "Calabacin calabaza y berenjena"),
    ]),
    ("L105", "Frutas", [
        ("L2032", "Manzanas y peras"), ("L2033", "Platanos y bananas"), ("L2035", "Uvas"),
        ("L2038", "Frutos rojos y del bosque"), ("L2039", "Frutas tropicales"),
        ("L2040", "Frutas de temporada"), ("L2196", "Naranjas mandarinas y limones"),
        ("L2267", "Melon y sandia"), ("L2268", "Frutas congeladas"),
    ]),
    ("L106", "Arroz pastas y legumbres", [
        ("L2042", "Arroz"), ("L2043", "Quinoa couscous y soja"),
        ("L2044", "Macarrones espaguetis y pastas secas"),
        ("L2191", "Garbanzos y alubias"), ("L2193", "Lentejas"), ("L2270", "Fideos"),
        ("L2271", "Pastas rellenas y en salsa"), ("L2272", "Lasana y canelones"),
        ("L2273", "Noodles"), ("L2274", "Pastas sin gluten"),
        ("L2297", "Salsas para pasta"),
    ]),
    ("L107", "Aceites salsas y especias", [
        ("L2046", "Aceites"), ("L2047", "Vinagres y alinos"),
        ("L2048", "Ajo sal y pimienta"), ("L2050", "Ketchup mayonesa y mostaza"),
        ("L2208", "Salsas de tomate y pasta"), ("L2294", "Especias y hierbas"),
        ("L2295", "Sazonadores"), ("L2296", "Salsas especiales y picantes"),
    ]),
    ("L108", "Huevos leche y mantequilla", [
        ("L2051", "Leche"), ("L2052", "Bebidas vegetales y horchatas"),
        ("L2053", "Batidos"), ("L2054", "Nata"), ("L2055", "Huevos"),
        ("L2056", "Mantequilla y margarina"),
        ("L2261", "Leche sin lactosa y enriquecidas"), ("L2262", "Leche infantil"),
        ("L2264", "Leche condensada y evaporada"),
    ]),
    ("L109", "Cafe cacao e infusiones", [
        ("L2057", "Capsulas compatibles nespresso"),
        ("L2058", "Cacao y chocolate a la taza"), ("L2059", "Infusiones"),
        ("L2275", "Capsulas compatibles dolce gusto"),
        ("L2276", "Otras capsulas compatibles"), ("L2277", "Cafe molido"),
        ("L2278", "Cafe soluble"), ("L2279", "Cafe en grano"),
        ("L2280", "Cafes frios"), ("L2281", "Te"),
    ]),
    ("L110", "Chocolates y golosinas", [
        ("L2063", "Chocolatinas y bombones"), ("L2064", "Golosinas"),
        ("L2228", "Cremas de cacao y de untar"), ("L2324", "Chocolate con leche"),
        ("L2325", "Chocolate negro"), ("L2326", "Chocolate blanco"),
        ("L2327", "Chicles y caramelos"),
    ]),
    ("L111", "Galletas cereales y mermeladas", [
        ("L2062", "Mermeladas"), ("L2065", "Galletas clasicas y digestive"),
        ("L2066", "Galletas saladas y crackers"), ("L2068", "Cereales"),
        ("L2216", "Tortitas"), ("L2320", "Galletas de chocolate y rellenas"),
        ("L2321", "Cereales integrales y muesli"),
        ("L2322", "Barritas de cereales y proteinas"),
        ("L2323", "Galletas cereales y tortitas sin gluten"),
    ]),
    ("L112", "Panaderia", [
        ("L2069", "Pan de molde y especiales"), ("L2070", "Pan recien horneado"),
        ("L2072", "Pan rallado tostado y picos"),
        ("L2073", "Pan para hamburguesas y perritos"),
        ("L2074", "Tortillas de trigo y pitas"), ("L2076", "Masas y hojaldres"),
        ("L2200", "Pan sin gluten"), ("L2304", "Horno"),
    ]),
    ("L113", "Yogures y postres", [
        ("L2078", "Yogures bifidus y colesterol"),
        ("L2079", "Yogures naturales y desnatados"),
        ("L2081", "Yogures de sabores y frutas"), ("L2082", "Yogures griegos"),
        ("L2083", "Yogures y postres infantiles"),
        ("L2085", "Kefir y postres vegetales"), ("L2087", "Postres tradicionales"),
        ("L2088", "Natillas flan y arroz con leche"),
        ("L2089", "Gelatinas y cuajadas"),
        ("L2229", "Postres y batidos de proteinas"), ("L2248", "Yogures liquidos"),
    ]),
    ("L114", "Conservas caldos y cremas", [
        ("L2092", "Conservas de verdura"), ("L2093", "Caldos y sopas"),
        ("L2094", "Cremas y pures"), ("L2179", "Atun y bonito"),
        ("L2195", "Mejillones berberechos y pescado"),
        ("L2207", "Caballa y sardinas"), ("L2298", "Conservas de fruta"),
        ("L2341", "Pates"),
    ]),
    ("L115", "Aperitivos y frutos secos", [
        ("L2041", "Frutas deshidratadas"), ("L2096", "Aceitunas"),
        ("L2097", "Frutos secos"), ("L2098", "Patatas fritas"),
        ("L2282", "Snacks salados"), ("L2283", "Mix de frutos secos"),
        ("L2284", "Encurtidos"), ("L2285", "Snacks vegetales"),
    ]),
    ("L116", "Platos preparados y pizzas", [
        ("L2101", "Pizzas refrigeradas"), ("L2102", "Listos para comer"),
        ("L2103", "Comida mexicana"), ("L2104", "Sandwiches y hamburguesas"),
        ("L2105", "Tortillas y empanadas"), ("L2106", "Gazpachos y salmorejos"),
        ("L2246", "Pizzas congeladas"), ("L2247", "Comida tradicional"),
        ("L2269", "Hummus y guacamoles"), ("L2299", "Comida asiatica"),
        ("L2300", "Ensaladas y bowls"),
    ]),
    ("L117", "Agua y refrescos", [
        ("L2107", "Agua"), ("L2108", "Cola"),
        ("L2110", "Kombucha y aguas vitaminadas"), ("L2111", "Te frio"),
        ("L2112", "Tonica gaseosa y bitter"),
        ("L2114", "Bebidas isotonicas y deportivas"),
        ("L2192", "Refrescos sin gas"), ("L2212", "Naranja limon y lima-limon"),
        ("L2217", "Bebidas energeticas"), ("L2286", "Packs de agua y refrescos"),
    ]),
    ("L118", "Cervezas vinos y licores", [
        ("L2115", "Cervezas"), ("L2117", "Cervezas premium y especiales"),
        ("L2118", "Cervezas sin alcohol"), ("L2119", "Tinto de verano y sangria"),
        ("L2120", "Vino tinto"), ("L2121", "Vino blanco"), ("L2122", "Cavas y sidra"),
        ("L2124", "Vino rosado"), ("L2125", "Ginebra vodka y tequila"),
        ("L2127", "Vermouth y aperitivos"), ("L2128", "Ron y whisky"),
        ("L2129", "Cremas licores y brandy"), ("L2182", "Cervezas con limon"),
        ("L2293", "Packs de cervezas"),
    ]),
    ("L119", "Congelados y helados", [
        ("L2130", "Helados y hielo"), ("L2131", "Pizzas y masas"),
        ("L2132", "Pescado y marisco"), ("L2135", "Croquetas y rebozados"),
        ("L2136", "Tartas y churros"), ("L2137", "Arroces y pasta"),
        ("L2210", "Verduras y patatas"),
    ]),
    ("L120", "Infantil", [
        ("L2138", "Leches y papillas"), ("L2139", "Yogures y postres"),
        ("L2140", "Bolsitas y snacks"), ("L2141", "Potitos y tarritos"),
        ("L2142", "Panales y toallitas"), ("L2143", "Higiene y cuidado"),
        ("L2314", "Zumos y batidos"), ("L2315", "Galletas y bolleria"),
        ("L2316", "Golosinas y chocolatinas"),
    ]),
    ("L122", "Limpieza y hogar", [
        ("L2159", "Estropajos bayetas y guantes"),
        ("L2160", "Bolsas de basura escobas y fregonas"),
        ("L2161", "Lejia y desinfectantes"),
        ("L2163", "Limpieza suelos cristales y muebles"),
        ("L2164", "Limpieza bano y wc"),
        ("L2166", "Limpieza cocina y quitagrasas"), ("L2167", "Lavavajillas"),
        ("L2168", "Papel higienico cocina y servilletas"),
        ("L2169", "Film aluminio y conservacion"), ("L2170", "Detergentes"),
        ("L2173", "Insecticidas"), ("L2209", "Pilas menaje y bolsas"),
        ("L2226", "Ambientadores recambios y velas"),
        ("L2306", "Suavizantes y cuidado de la ropa"),
    ]),
    ("L123", "Mascotas", [
        ("L2174", "Perro comida seca"), ("L2175", "Gato comida seca"),
        ("L2308", "Gato comida humeda"), ("L2309", "Gato snacks y cuidado"),
        ("L2310", "Perro comida humeda"), ("L2311", "Perro snacks y cuidado"),
    ]),
    ("L127", "Zumos y smoothies", [
        ("L2113", "Recien exprimido y fresco"), ("L2287", "Naranja"),
        ("L2288", "Melocoton y pina"), ("L2289", "Multifrutas y otros sabores"),
        ("L2290", "Fruta y leche"), ("L2291", "Smoothies"),
        ("L2292", "Packs de zumos"), ("L2312", "Limonadas"),
    ]),
    ("L129", "Higiene y cuidado del cuerpo", [
        ("L2150", "Afeitado"), ("L2151", "Higiene bucal"),
        ("L2153", "Hidratacion de cuerpo y manos"), ("L2154", "Desodorantes"),
        ("L2156", "Jabon de manos"), ("L2158", "Compresas e higiene intima"),
        ("L2188", "Depilacion"), ("L2211", "Gel de ducha y esponjas"),
        ("L2227", "Protector solar y aftersun"),
    ]),
    ("L130", "Cabello y perfumeria", [
        ("L2144", "Champu"), ("L2145", "Acondicionadores y mascarillas"),
        ("L2146", "Espumas y fijadores"), ("L2147", "Tintes"),
        ("L2148", "Cuidado facial"), ("L2155", "Perfumes y colonias"),
    ]),
    ("L131", "Salud y parafarmacia", [
        ("L2183", "Complementos nutricionales"), ("L2184", "Parafarmacia"),
        ("L2307", "Botiquin"), ("L2340", "Protector solar"),
    ]),
    ("L132", "Bolleria reposteria y azucar", [
        ("L2060", "Azucar miel y edulcorantes"),
        ("L2067", "Magdalenas y bolleria clasica"),
        ("L2075", "Harinas y levaduras"),
        ("L2077", "Preparados para postres y decoracion"),
        ("L2317", "Bolleria de horno dulce"), ("L2318", "Rosquillas y pastelitos"),
        ("L2319", "Tartas"),
    ]),
    ("L134", "Charcuteria", [
        ("L2001", "Jamon cocido"), ("L2004", "Jamon serrano"),
        ("L2005", "Lomo y chorizo"), ("L2012", "Pate y sobrasada"),
        ("L2206", "Salchichas"), ("L2259", "Chopped y mortadela"),
        ("L2342", "Pavo y pollo"), ("L2343", "Fuet y salchichon"),
        ("L2344", "Bacon"),
    ]),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": BASE_URL + "/",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("dia")

_http_session = curl_requests.Session(impersonate="chrome124")


def calentar_sesion():
    """Visita la home primero para obtener cookies de sesion (session_id,
    bot-manager) antes de llamar a la API -- igual que haria un navegador
    real. Sin esto la API puede bloquear peticiones 'en frio'."""
    try:
        _http_session.get(BASE_URL + "/", headers=HEADERS, timeout=15)
        log.info("Sesion inicializada (cookies obtenidas de la home)")
    except Exception as e:
        log.warning(f"No se pudo calentar sesion: {e}")


def fetch_subcategoria(l1_code, l2_code, retries=2):
    """Devuelve TODOS los items de una subcategoria, paginando."""
    items_totales = []
    page = 1
    total_pages = 1
    while page <= total_pages:
        url = API_PLP.format(l1=l1_code)
        params = {"category_id": l2_code, "page": page}
        ok = False
        for attempt in range(retries):
            try:
                r = _http_session.get(url, params=params, headers=HEADERS, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    items = data.get("items", [])
                    items_totales.extend(items)
                    total_pages = data.get("pagination", {}).get("total_pages", 1)
                    ok = True
                    break
                log.debug(f"    HTTP {r.status_code} (intento {attempt+1})")
            except Exception as e:
                log.debug(f"    error: {e} (intento {attempt+1})")
            time.sleep(1.0 * (attempt + 1))
        if not ok:
            break
        page += 1
        if page <= total_pages:
            time.sleep(DELAY)
    return items_totales


def parse_item(item, l1_name, l2_name):
    prices = item.get("prices", {}) or {}
    precio = prices.get("price")
    if precio is None:
        return None
    return {
        "id_api": str(item.get("object_id") or item.get("sku_id") or ""),
        "nombre_comercial": item.get("display_name", "").strip(),
        "precio": float(precio),
        "precio_unidad": (
            f"{prices.get('price_per_unit')}€/{prices.get('measure_unit')}"
            if prices.get("price_per_unit") and prices.get("measure_unit") else None
        ),
        "marca": item.get("brand", "") or "",
        "url": BASE_URL + item.get("url", "") if item.get("url") else None,
        "imagen": BASE_URL + item.get("image", "") if item.get("image") else None,
        "disponible": item.get("units_in_stock", 0) != 0,
        "categoria_dia": l1_name,
        "subcategoria_dia": l2_name,
    }


def assign_ids(products, id_map):
    ultimo_num = max(
        (int(v.split("-")[1]) for v in id_map.values()
         if "-" in v and v.split("-")[1].isdigit()),
        default=0,
    )
    contador = ultimo_num
    resultado = []
    vistos = set()
    for p in products:
        key = p["id_api"]
        if not key or key in vistos:
            continue
        vistos.add(key)
        if key in id_map:
            p["id"] = id_map[key]
        else:
            contador += 1
            p["id"] = f"{PREFIJO_ID}-{contador:04d}"
        resultado.append(p)
    return resultado


def get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upsert(client, products):
    import datetime
    now = datetime.datetime.now(datetime.UTC).isoformat()
    for p in products:
        p["actualizado"] = now
    if not products:
        return 0
    if registrar_cambios_precio:
        registrar_cambios_precio(client, TABLE_NAME, "dia", products)
    res = client.table(TABLE_NAME).upsert(products, on_conflict="id_api").execute()
    return len(res.data) if res.data else len(products)


def main(dry_run=False, only_cat=None, debug=False):
    print("=" * 60)
    print("  SCRAPER DIA v2 — API plp-back (agosto 2026)")
    print("=" * 60)

    if debug:
        log.setLevel(logging.DEBUG)

    client = None
    id_map = {}
    if not dry_run:
        if not SUPABASE_KEY:
            print("ERROR: falta SUPABASE_KEY en .env"); return
        client = get_supabase()
        existentes = []
        offset = 0
        while True:
            res = client.table(TABLE_NAME).select("id,id_api").range(offset, offset + 999).execute()
            existentes.extend(res.data)
            if len(res.data) < 1000:
                break
            offset += 1000
        id_map = {r["id_api"]: r["id"] for r in existentes if r.get("id_api")}
        log.info(f"Supabase conectado — {len(id_map)} IDs existentes")

    calentar_sesion()

    categorias = CATEGORIES_DIA
    if only_cat:
        oc = only_cat.lower()
        categorias = [c for c in categorias if oc in c[0].lower() or oc in c[1].lower()]
    log.info(f"{len(categorias)} categorias L1 a procesar\n")

    todos_los_items = []
    for l1_code, l1_name, subcats in categorias:
        log.info(f"[{l1_code}] {l1_name}  ({len(subcats)} subcategorias)")
        for l2_code, l2_name in subcats:
            items_raw = fetch_subcategoria(l1_code, l2_code)
            parseados = [parse_item(it, l1_name, l2_name) for it in items_raw]
            parseados = [p for p in parseados if p]
            todos_los_items.extend(parseados)
            log.info(f"    {l2_name}: {len(parseados)} productos")
            time.sleep(DELAY_CAT)

    print(f"\n{'='*60}")
    print(f"  Total productos recogidos: {len(todos_los_items)}")

    if dry_run:
        print("  [dry-run] Muestra:")
        for p in todos_los_items[:8]:
            print(f"    {p['id_api']} | {p['nombre_comercial'][:45]:<45} | "
                  f"{p['precio']}€ | {p['categoria_dia']} > {p['subcategoria_dia']}")
        print(f"{'='*60}")
        return

    # ── Backup local ANTES de subir — si falla la red durante el upsert,
    # no se pierde el trabajo de scraping (antes pasaba justo eso) ────────
    import datetime as _dt
    backup_path = f"backup_dia_{_dt.datetime.now().strftime('%Y%m%d_%H%M')}.json"
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(todos_los_items, f, ensure_ascii=False)
        log.info(f"Backup local guardado: {backup_path}")
    except Exception as e:
        log.warning(f"No se pudo guardar backup local: {e}")

    productos_con_id = assign_ids(todos_los_items, id_map)
    total_ok = 0
    for i in range(0, len(productos_con_id), 500):
        lote = productos_con_id[i:i + 500]
        subido = False
        for intento in range(3):
            try:
                total_ok += upsert(client, lote)
                subido = True
                break
            except Exception as e:
                log.warning(f"  Error subiendo lote (intento {intento+1}/3): {e}")
                time.sleep(5 * (intento + 1))
        if not subido:
            log.error(f"  Lote {i}-{i+len(lote)} NO se pudo subir tras 3 intentos. "
                       f"Datos a salvo en {backup_path} — reintenta más tarde.")
        else:
            log.info(f"  Subidos {min(i+500, len(productos_con_id))}/{len(productos_con_id)}")

    print(f"  Total upserted: {total_ok}")
    print(f"{'='*60}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cat", help="Filtrar por codigo L1 o nombre (ej. 'verduras')")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    main(dry_run=args.dry_run, only_cat=args.cat, debug=args.debug)
