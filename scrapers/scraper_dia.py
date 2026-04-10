"""
scraper_dia.py  —  Mi Mejor Cesta
==================================
Descarga todos los productos de DIA por categorías
y los guarda en precios_dia (Supabase) + CSV de backup.

Mejora sobre v3: navega por árbol de categorías en lugar de
buscar por palabras clave — más completo y sin duplicados.

Esquema de precios_dia:
  id           → DI-xxxx  (generado por nosotros)
  id_api       → referencia_externa / sku_id original de DIA
  nombre_comercial, precio, precio_unidad, marca, url, imagen, disponible, actualizado

Uso:
  cd scrapers
  python scraper_dia.py
"""

import requests, json, csv, time, os, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

# ── Credenciales desde .env en la raíz del proyecto ───────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
DELAY        = 0.5

OUTPUT_CSV  = f"dia_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
TABLA_SB    = "precios_dia"
PREFIJO_ID  = "DI"

HEADERS_API = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer":         "https://www.dia.es/",
}
HEADERS_SB = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "resolution=merge-duplicates,return=minimal",
}

# ── IDs de categorías principales de DIA (árbol real de la web) ───────────────
# Obtenidos de https://www.dia.es/api/v1/search-back/categories
CATEGORIAS_DIA = [
    {"id": "01",  "nombre": "Frutas y verduras"},
    {"id": "02",  "nombre": "Carne y charcutería"},
    {"id": "03",  "nombre": "Pescado y marisco"},
    {"id": "04",  "nombre": "Lácteos y huevos"},
    {"id": "05",  "nombre": "Panadería y bollería"},
    {"id": "06",  "nombre": "Congelados"},
    {"id": "07",  "nombre": "Bebidas"},
    {"id": "08",  "nombre": "Bodega"},
    {"id": "09",  "nombre": "Aceite, vinagre y especias"},
    {"id": "10",  "nombre": "Arroz, pasta y legumbres"},
    {"id": "11",  "nombre": "Conservas y platos preparados"},
    {"id": "12",  "nombre": "Salsas y condimentos"},
    {"id": "13",  "nombre": "Desayuno y merienda"},
    {"id": "14",  "nombre": "Aperitivos y snacks"},
    {"id": "15",  "nombre": "Higiene y cosmética"},
    {"id": "16",  "nombre": "Limpieza del hogar"},
    {"id": "17",  "nombre": "Bebés"},
    {"id": "18",  "nombre": "Mascotas"},
]

# ── URL base de la API de búsqueda de DIA ─────────────────────────────────────
API_SEARCH = "https://www.dia.es/api/v1/search-back/search/reduced"


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE DESCARGA
# ══════════════════════════════════════════════════════════════════════════════

def buscar_por_categoria(cat_id, cat_nombre):
    """
    Descarga todos los productos de una categoría navegando la paginación.
    DIA no tiene API de categorías directa — usamos búsqueda filtrada por categoría.
    """
    productos = []
    vistos    = set()
    pagina    = 1

    while True:
        url = f"{API_SEARCH}?categoryId={cat_id}&page={pagina}&pageSize=100"
        try:
            r = requests.get(url, headers=HEADERS_API, timeout=15)
            if r.status_code != 200:
                # Fallback: búsqueda por nombre de categoría
                break
            data       = r.json()
            items      = data.get("search_items", [])
            paginacion = data.get("pagination", {})
            total_pags = paginacion.get("total_pages", 1)

            for item in items:
                sku = str(item.get("sku_id") or item.get("object_id") or "")
                if sku and sku not in vistos:
                    vistos.add(sku)
                    p = parsear_producto(item)
                    if p:
                        productos.append(p)

            if pagina >= total_pags:
                break
            pagina += 1
            time.sleep(DELAY)

        except Exception as e:
            print(f"  ⚠️  Error en {cat_nombre} pág {pagina}: {e}")
            break

    return productos


def buscar_por_termino(termino, max_paginas=5):
    """
    Búsqueda por término como fallback si la navegación por categoría falla.
    """
    productos = []
    vistos    = set()

    for pagina in range(1, max_paginas + 1):
        url = f"{API_SEARCH}?q={requests.utils.quote(termino)}&page={pagina}"
        try:
            r = requests.get(url, headers=HEADERS_API, timeout=15)
            if r.status_code != 200:
                break
            data       = r.json()
            items      = data.get("search_items", [])
            paginacion = data.get("pagination", {})
            total_pags = paginacion.get("total_pages", 1)

            nuevos = 0
            for item in items:
                sku = str(item.get("sku_id") or item.get("object_id") or "")
                if sku and sku not in vistos:
                    vistos.add(sku)
                    p = parsear_producto(item)
                    if p:
                        productos.append(p)
                        nuevos += 1

            if pagina >= total_pags or not items:
                break
            time.sleep(DELAY)

        except Exception as e:
            print(f"  ⚠️  Error buscando '{termino}': {e}")
            break

    return productos


def parsear_producto(item):
    """Transforma un item de la API DIA al formato de precios_dia."""
    nombre = (item.get("display_name") or "").strip()
    if not nombre:
        return None

    # Precio
    precios = item.get("prices") or {}
    try:
        precio = float(precios.get("price") or 0)
    except:
        precio = 0

    # Precio por unidad con etiqueta de medida
    price_per_unit = precios.get("price_per_unit")
    measure_unit   = (precios.get("measure_unit") or "").strip().upper()
    unit_map = {
        "LITRO": "L", "LITROS": "L",
        "KILOGRAMO": "kg", "KILO": "kg", "KILOS": "kg",
        "GRAMO": "g", "GRAMOS": "g",
        "MILILITRO": "ml", "MILILITROS": "ml",
        "UNIDAD": "ud", "UNIDADES": "ud",
        "METRO": "m", "METROS": "m",
    }
    unit_label = unit_map.get(measure_unit, measure_unit.lower() if measure_unit else "")
    if price_per_unit and unit_label:
        precio_unidad = f"{float(price_per_unit):.2f}€/{unit_label}"
    elif price_per_unit:
        precio_unidad = f"{float(price_per_unit):.2f}€/ud"
    else:
        precio_unidad = None

    # Imagen
    imagen = item.get("image") or ""
    if imagen and not imagen.startswith("http"):
        imagen = "https://www.dia.es" + imagen

    # URL
    url = item.get("url") or ""
    if url and not url.startswith("http"):
        url = "https://www.dia.es" + url

    # ID API (referencia externa)
    id_api = str(item.get("sku_id") or item.get("object_id") or "")

    return {
        "id_api":          id_api,
        "nombre_comercial": nombre,
        "precio":          round(precio, 2) if precio else None,
        "precio_unidad":   precio_unidad,
        "marca":           item.get("brand") or None,
        "url":             url,
        "imagen":          imagen,
        "disponible":      True,
    }


def descargar_productos():
    """
    Intenta descargar por categoría (más completo).
    Si falla, usa búsqueda por términos como fallback.
    """
    todos  = {}  # id_api → producto (para deduplicar)

    print("📂 Descargando por categorías...")

    # Método 1: por categoría
    for cat in CATEGORIAS_DIA:
        print(f"\n📂 {cat['nombre']}...")
        prods = buscar_por_categoria(cat["id"], cat["nombre"])

        if not prods:
            # Fallback: buscar por nombre de categoría como término
            print(f"  → Usando búsqueda por término...")
            prods = buscar_por_termino(cat["nombre"].split()[0])

        nuevos = 0
        for p in prods:
            if p["id_api"] and p["id_api"] not in todos:
                todos[p["id_api"]] = p
                nuevos += 1

        print(f"  ✅ {nuevos} nuevos | total acumulado: {len(todos)}")

    # Método 2: términos adicionales para completar (productos que no caen en categorías)
    TERMINOS_EXTRA = [
        "leche", "yogur", "queso", "huevos", "pollo", "carne", "pescado",
        "pan", "galletas", "cereales", "cafe", "agua", "refresco", "cerveza",
        "vino", "aceite", "arroz", "pasta", "conservas", "detergente",
        "champu", "gel", "pañales", "comida gato", "comida perro",
    ]

    print(f"\n📂 Completando con términos adicionales...")
    for termino in TERMINOS_EXTRA:
        prods  = buscar_por_termino(termino, max_paginas=3)
        nuevos = sum(1 for p in prods if p["id_api"] and p["id_api"] not in todos)
        for p in prods:
            if p["id_api"] and p["id_api"] not in todos:
                todos[p["id_api"]] = p
        if nuevos:
            print(f"  '{termino}': +{nuevos} nuevos")
        time.sleep(0.2)

    return list(todos.values())


# ══════════════════════════════════════════════════════════════════════════════
# GENERACIÓN DE IDs DI-xxxx
# ══════════════════════════════════════════════════════════════════════════════

def asignar_ids(productos):
    """Asigna DI-xxxx manteniendo IDs existentes para productos ya en Supabase."""
    print("🔢 Obteniendo IDs existentes en Supabase...")
    mapa_existente = {}
    ultimo_num     = 0

    try:
        offset = 0
        while True:
            url = (f"{SUPABASE_URL}/rest/v1/{TABLA_SB}"
                   f"?select=id,id_api&offset={offset}&limit=1000")
            req = urllib.request.Request(url, headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                lote = json.loads(resp.read())
                for r in lote:
                    if r.get("id_api"):
                        mapa_existente[r["id_api"]] = r["id"]
                if len(lote) < 1000:
                    break
                offset += 1000

        if mapa_existente:
            ultimo_num = max(int(v.split("-")[1]) for v in mapa_existente.values())
        print(f"  {len(mapa_existente)} existentes | último: {PREFIJO_ID}-{ultimo_num:04d}")

    except Exception as e:
        print(f"  ⚠️  No se pudieron obtener IDs existentes: {e}")

    contador = ultimo_num
    for p in productos:
        if p["id_api"] in mapa_existente:
            p["id"] = mapa_existente[p["id_api"]]
        else:
            contador += 1
            p["id"] = f"{PREFIJO_ID}-{contador:04d}"

    return productos


# ══════════════════════════════════════════════════════════════════════════════
# GUARDAR CSV
# ══════════════════════════════════════════════════════════════════════════════

def guardar_csv(productos):
    campos = ["id", "id_api", "nombre_comercial", "precio", "precio_unidad",
              "marca", "url", "imagen", "disponible"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(productos)
    print(f"  📄 CSV: {OUTPUT_CSV}")


# ══════════════════════════════════════════════════════════════════════════════
# SUBIR A SUPABASE
# ══════════════════════════════════════════════════════════════════════════════

def subir_supabase(productos):
    """Sube/actualiza precios_dia usando id_api como clave de upsert."""
    campos = ["id", "id_api", "nombre_comercial", "precio", "precio_unidad",
              "marca", "url", "imagen", "disponible"]

    ok = err = 0
    BATCH = 50
    total_lotes = (len(productos) + BATCH - 1) // BATCH

    for i in range(0, len(productos), BATCH):
        lote = [{k: p.get(k) for k in campos} for p in productos[i:i+BATCH]]
        for row in lote:
            row["actualizado"] = datetime.utcnow().isoformat() + "Z"

        url_sb = f"{SUPABASE_URL}/rest/v1/{TABLA_SB}"
        req    = urllib.request.Request(
            url_sb,
            data=json.dumps(lote).encode(),
            headers=HEADERS_SB,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30):
                ok += len(lote)
        except urllib.error.HTTPError as e:
            err += len(lote)
            if i == 0:
                print(f"  ❌ Error HTTP {e.code}: {e.read().decode()[:300]}")
                return ok, err

        n = i // BATCH + 1
        print(f"  Lote {n}/{total_lotes} ({ok} OK)", end="\r")

    print()
    return ok, err


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 55)
    print("  🛒 SCRAPER DIA — Mi Mejor Cesta")
    print("=" * 55)

    if not SUPABASE_KEY:
        print("❌ SUPABASE_KEY no encontrada en .env")
        return

    # 1. Descargar
    productos = descargar_productos()
    if not productos:
        print("❌ No se obtuvieron productos")
        return

    con_precio = sum(1 for p in productos if p.get("precio"))
    print(f"\n{'='*55}")
    print(f"  Total descargados:  {len(productos)}")
    print(f"  Con precio:         {con_precio} ({con_precio/len(productos)*100:.1f}%)")

    # 2. Asignar IDs DI-xxxx
    productos = asignar_ids(productos)

    # 3. Guardar CSV
    guardar_csv(productos)

    # 4. Subir a Supabase
    print(f"\n¿Subir {len(productos)} productos a Supabase? (s/n): ", end="")
    if input().strip().lower() != "s":
        print("Cancelado. El CSV queda guardado.")
        return

    print(f"\n🔄 Subiendo a {TABLA_SB}...")
    ok, err = subir_supabase(productos)
    print(f"  ✅ OK: {ok} | ❌ Errores: {err}")
    print("\n✅ Completado.")


if __name__ == "__main__":
    main()
