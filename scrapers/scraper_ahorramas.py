"""
scraper_ahorramas.py  —  Mi Mejor Cesta
========================================
Descarga todos los productos de Ahorramas usando el endpoint
Demandware Search-ShowAjax y los guarda en precios_ahorramas (Supabase).

Uso:
  cd scrapers
  python scraper_ahorramas.py --dry-run   # solo muestra, no guarda
  python scraper_ahorramas.py             # descarga y sube
"""

import requests, json, csv, time, os, re, argparse
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

TABLA_SB   = "precios_ahorramas"
PREFIJO_ID = "AH"
DELAY      = 0.5
SZ         = 48   # productos por página

BASE_URL = "https://www.ahorramas.com/on/demandware.store/Sites-Ahorramas-Site/es/Search-ShowAjax"

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":          "text/html, */*; q=0.01",
    "Accept-Language": "es-ES,es;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer":         "https://www.ahorramas.com/",
}

# Categorías de Ahorramas con su cgid
CATEGORIAS = {
    "alimentacion":       "alimentacion",
    "bebidas":            "bebidas",
    "frescos":            "frescos",
    "congelados":         "congelados",
    "lacteos":            "lacteos",
    "drogueria":          "drogueria",
    "cuidado-personal":   "cuidadopersonal",
    "mascotas":           "mascotas",
    "bebe":               "bebe",
}

# ══════════════════════════════════════════════════════════════════════════════
# PARSEO HTML
# ══════════════════════════════════════════════════════════════════════════════

def parsear_precio(texto):
    """Extrae precio float de texto como '2,99 €' o '2.99€'."""
    if not texto:
        return None
    texto = texto.replace('\xa0', ' ').strip()
    m = re.search(r'(\d+)[,.](\d+)', texto)
    if m:
        try:
            return float(f"{m.group(1)}.{m.group(2)}")
        except:
            pass
    m = re.search(r'(\d+)', texto)
    if m:
        try:
            return float(m.group(1))
        except:
            pass
    return None

def parsear_producto(tile):
    """Extrae datos de un product-tile HTML."""
    try:
        # Nombre
        nombre_el = (
            tile.select_one('.pdp-link a') or
            tile.select_one('.product-name a') or
            tile.select_one('a.product-tile-link') or
            tile.select_one('[class*="product-name"]') or
            tile.select_one('h2 a') or
            tile.select_one('h3 a')
        )
        nombre = nombre_el.get_text(strip=True) if nombre_el else None
        if not nombre:
            return None

        # URL y ID
        url = nombre_el.get('href', '') if nombre_el else ''
        if url and not url.startswith('http'):
            url = 'https://www.ahorramas.com' + url

        # ID del producto desde data-pid o URL
        pid = tile.get('data-pid') or tile.get('data-product-id')
        if not pid and url:
            # URLs de Ahorramas terminan en -12345.html — ese número es el id
            m = re.search(r'-(\d+)\.html', url)
            if m:
                pid = m.group(1)

        # Precio
        precio_el = (
            tile.select_one('.price .value') or
            tile.select_one('.sales .value') or
            tile.select_one('[class*="price"] .value') or
            tile.select_one('.price-sales') or
            tile.select_one('[class*="sales-price"]') or
            tile.select_one('.price')
        )
        precio_texto = precio_el.get_text(strip=True) if precio_el else ''
        precio = parsear_precio(precio_texto)

        # Precio por unidad (reference price)
        ref_el = (
            tile.select_one('.price-per-unit') or
            tile.select_one('[class*="unit-price"]') or
            tile.select_one('[class*="per-unit"]')
        )
        precio_unidad = ref_el.get_text(strip=True) if ref_el else None

        # Imagen
        img_el = tile.select_one('img.tile-image') or tile.select_one('img[class*="product"]') or tile.select_one('img')
        imagen = img_el.get('src') or img_el.get('data-src') if img_el else ''

        # Marca
        marca_el = tile.select_one('[class*="brand"]') or tile.select_one('.product-brand')
        marca = marca_el.get_text(strip=True) if marca_el else None

        return {
            "id_api":           pid or "",
            "nombre_comercial": nombre,
            "precio":           precio,
            "precio_unidad":    precio_unidad,
            "marca":            marca,
            "url":              url,
            "imagen":           imagen or "",
            "disponible":       True,
        }
    except Exception as e:
        return None


def descargar_categoria(cgid, cat_nombre):
    """Descarga todos los productos de una categoría paginando."""
    productos = []
    start = 0
    total = None

    print(f"\n📂 {cat_nombre} (cgid={cgid})")

    while True:
        url = f"{BASE_URL}?cgid={cgid}&pmin=0.01&start={start}&sz={SZ}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                print(f"  ⚠️  HTTP {r.status_code}")
                break
        except Exception as e:
            print(f"  ❌ Error: {e}")
            break

        soup = BeautifulSoup(r.text, 'html.parser')

        # Obtener total de productos (primera vez)
        if total is None:
            total_el = soup.select_one('[data-page-size]')
            if total_el:
                page_size = total_el.get('data-page-size')
                # Buscar total en el JSON de opciones de ordenación
                match = re.search(r'"total"\s*:\s*(\d+)', r.text)
                if match:
                    total = int(match.group(1))
                else:
                    total = 999  # asumir grande

        # Encontrar tiles de productos
        tiles = (
            soup.select('.product-container [class*="product-tile"]') or
            soup.select('[class*="product-tile"]') or
            soup.select('.product-container') or
            soup.select('[data-pid]')
        )

        nuevos = 0
        for tile in tiles:
            p = parsear_producto(tile)
            if p and p['nombre_comercial']:
                p['categoria_ahorramas'] = cat_nombre
                productos.append(p)
                nuevos += 1

        print(f"  start={start}: {nuevos} productos | total acumulado: {len(productos)}", end='\r')

        if nuevos == 0 or (total and start + SZ >= total):
            break

        start += SZ
        time.sleep(DELAY)

    print(f"  ✅ {len(productos)} productos en {cat_nombre}          ")
    return productos


# ══════════════════════════════════════════════════════════════════════════════
# IDs y Supabase
# ══════════════════════════════════════════════════════════════════════════════

def obtener_ids_existentes():
    """Obtiene mapa id_api → AH-xxxx de Supabase."""
    try:
        import urllib.request
        mapa = {}
        offset = 0
        while True:
            url = f"{SUPABASE_URL}/rest/v1/{TABLA_SB}?select=id,id_api&offset={offset}&limit=1000"
            req = urllib.request.Request(url, headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                if not data:
                    break
                for r in data:
                    if r.get('id_api'):
                        mapa[r['id_api']] = r['id']
                if len(data) < 1000:
                    break
                offset += 1000
        return mapa
    except:
        return {}

def asignar_ids(productos, mapa_existente):
    """Asigna AH-xxxx a cada producto."""
    ultimo_num = max(
        (int(v.split('-')[1]) for v in mapa_existente.values() if '-' in v),
        default=0
    )
    contador = ultimo_num
    vistos = set()

    resultado = []
    for p in productos:
        key = p.get('id_api') or p.get('nombre_comercial', '')
        if key in vistos:
            continue
        vistos.add(key)

        if key in mapa_existente:
            p['id'] = mapa_existente[key]
        else:
            contador += 1
            p['id'] = f"{PREFIJO_ID}-{contador:04d}"

        resultado.append(p)

    return resultado

def subir_supabase(productos):
    """Sube productos a Supabase."""
    import urllib.request, urllib.error

    campos = ["id", "id_api", "nombre_comercial", "precio", "precio_unidad",
              "marca", "url", "imagen", "disponible", "categoria_ahorramas"]

    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=merge-duplicates,return=minimal",
    }

    ok = err = 0
    BATCH = 50
    total_lotes = (len(productos) + BATCH - 1) // BATCH

    for i in range(0, len(productos), BATCH):
        lote = [{k: p.get(k) for k in campos} for p in productos[i:i+BATCH]]
        for row in lote:
            row["actualizado"] = datetime.utcnow().isoformat() + "Z"

        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/{TABLA_SB}",
            data=json.dumps(lote).encode(),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30):
                ok += len(lote)
        except urllib.error.HTTPError as e:
            err += len(lote)
            if i == 0:
                print(f"\n  ❌ Error HTTP {e.code}: {e.read().decode()[:200]}")
                return ok, err

        print(f"  Lote {i//BATCH+1}/{total_lotes} ({ok} OK)", end='\r')

    print()
    return ok, err


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main(dry_run=False):
    print("=" * 55)
    print("  🛒 SCRAPER AHORRAMAS — Mi Mejor Cesta")
    print(f"  Modo: {'DRY-RUN' if dry_run else '⚠️  PRODUCCIÓN'}")
    print("=" * 55)

    if not SUPABASE_KEY and not dry_run:
        print("❌ SUPABASE_KEY no encontrada en .env")
        return

    # 1. Descargar todas las categorías
    todos = []
    vistos_ids = set()

    for cgid, nombre in CATEGORIAS.items():
        productos_cat = descargar_categoria(cgid, nombre)
        for p in productos_cat:
            key = p.get('id_api') or p.get('nombre_comercial', '')
            if key and key not in vistos_ids:
                vistos_ids.add(key)
                todos.append(p)

    print(f"\n{'='*55}")
    print(f"  Total únicos descargados: {len(todos)}")
    con_precio = sum(1 for p in todos if p.get('precio'))
    print(f"  Con precio:               {con_precio}")
    print(f"  Sin precio:               {len(todos) - con_precio}")

    # Muestra
    print("\n📋 Muestra primeros 10:")
    for p in todos[:10]:
        print(f"  {p.get('nombre_comercial', '?')[:50]} → {p.get('precio')}€ [{p.get('categoria_ahorramas')}]")

    if dry_run:
        print("\n[dry-run] No se guarda nada.")

        # Guardar CSV de muestra
        csv_file = f"ahorramas_dryrun_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            campos = ["id_api", "nombre_comercial", "precio", "precio_unidad", "marca", "url", "categoria_ahorramas"]
            w = csv.DictWriter(f, fieldnames=campos, extrasaction='ignore')
            w.writeheader()
            w.writerows(todos)
        print(f"  CSV guardado: {csv_file}")
        return

    # 2. Asignar IDs
    print("\n🔢 Obteniendo IDs existentes...")
    mapa = obtener_ids_existentes()
    print(f"  {len(mapa)} productos existentes en Supabase")
    todos = asignar_ids(todos, mapa)

    # 3. Confirmar
    print(f"\n¿Subir {len(todos)} productos a Supabase? (s/n): ", end="")
    if input().strip().lower() != 's':
        print("Cancelado.")
        return

    # 4. Subir
    print(f"\n🔄 Subiendo a {TABLA_SB}...")
    ok, err = subir_supabase(todos)
    print(f"  ✅ OK: {ok} | ❌ Errores: {err}")
    print("\n✅ Completado.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    main(dry_run=args.dry_run)
