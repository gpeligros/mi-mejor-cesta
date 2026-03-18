"""
scraper_openfoodfacts.py
Descarga productos de supermercados españoles desde Open Food Facts
API gratuita, sin bloqueos, datos reales
"""

import requests
import csv
import time
from datetime import datetime

# ── Configuración ────────────────────────────────────────────
OUTPUT_FILE = f"openfoodfacts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
DELAY       = 0.5
PAGE_SIZE   = 200   # máximo permitido por la API

# Supermercados españoles que queremos (tal como aparecen en OFF)
SUPERMERCADOS = [
    "Lidl",
    "Carrefour",
    "DIA",
    "Alcampo",
    "El Corte Inglés",
]

HEADERS = {
    "User-Agent": "MiMejorCesta/1.0 (comparador precios España; contacto@mimejorcesta.es)"
}

# Mapeo de categorías OFF → nuestras categorías
CATEGORIA_MAP = {
    "dairies":                   "Lácteos y Huevos",
    "milks":                     "Lácteos y Huevos",
    "yogurts":                   "Lácteos y Huevos",
    "cheeses":                   "Lácteos y Huevos",
    "eggs":                      "Lácteos y Huevos",
    "fruits":                    "Frutas y Verduras",
    "vegetables":                "Frutas y Verduras",
    "meats":                     "Carne y Charcutería",
    "fish":                      "Pescado y Marisco",
    "seafood":                   "Pescado y Marisco",
    "frozen-foods":              "Congelados",
    "beverages":                 "Bebidas",
    "waters":                    "Bebidas",
    "juices":                    "Bebidas",
    "sodas":                     "Bebidas",
    "beers":                     "Bebidas",
    "wines":                     "Bebidas",
    "breads":                    "Panadería",
    "pastries":                  "Panadería",
    "breakfast-cereals":         "Cereales y Galletas",
    "biscuits-and-cakes":        "Cereales y Galletas",
    "chocolates":                "Dulces",
    "candies":                   "Dulces",
    "snacks":                    "Snacks",
    "chips-and-fries":           "Snacks",
    "pasta":                     "Pasta y Sopas",
    "rice":                      "Aceite, Arroz y Legumbres",
    "legumes":                   "Aceite, Arroz y Legumbres",
    "oils":                      "Aceite, Arroz y Legumbres",
    "canned-foods":              "Conservas",
    "sauces":                    "Conservas",
    "coffee":                    "Café e Infusiones",
    "teas-and-herbal-teas":      "Café e Infusiones",
    "baby-foods":                "Bebés",
    "hygiene":                   "Higiene",
    "cleaning-products":         "Limpieza",
    "pet-foods":                 "Mascotas",
}


def inferir_categoria(categorias_raw):
    """Infiere nuestra categoría a partir de las tags de OFF"""
    if not categorias_raw:
        return "Otros"
    tags = categorias_raw.lower()
    for key, valor in CATEGORIA_MAP.items():
        if key in tags:
            return valor
    return "Otros"


def obtener_productos_supermercado(supermercado, max_productos=1000):
    """Descarga productos de un supermercado desde Open Food Facts"""
    productos = []
    page = 1

    print(f"\n🛒 Descargando {supermercado}...")

    while len(productos) < max_productos:
        url = (
            f"https://world.openfoodfacts.org/cgi/search.pl"
            f"?action=process"
            f"&tagtype_0=stores&tag_contains_0=contains&tag_0={requests.utils.quote(supermercado)}"
            f"&tagtype_1=countries&tag_contains_1=contains&tag_1=es"
            f"&page_size={PAGE_SIZE}"
            f"&page={page}"
            f"&json=1"
            f"&fields=id,product_name,brands,categories_tags,stores,"
            f"image_url,quantity,nutriments,url,code"
        )

        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code != 200:
                print(f"  ⚠️  HTTP {resp.status_code} en página {page}")
                break

            data = resp.json()
            items = data.get("products", [])

            if not items:
                break

            for item in items:
                nombre = (item.get("product_name") or "").strip()
                if not nombre:
                    continue

                categorias_raw = " ".join(item.get("categories_tags") or [])
                categoria = inferir_categoria(categorias_raw)

                # Precio — OFF no siempre tiene precio, dejamos vacío
                # (se puede completar después con matching manual o scraping puntual)
                precio = ""

                productos.append({
                    "supermercado":      supermercado,
                    "nombre_comercial":  nombre,
                    "precio":            precio,
                    "marca":             item.get("brands") or "",
                    "categoria":         categoria,
                    "subcategoria":      "",
                    "precio_por_unidad": item.get("quantity") or "",
                    "url":               f"https://es.openfoodfacts.org/producto/{item.get('code','')}",
                    "imagen":            item.get("image_url") or "",
                    "referencia_externa": item.get("code") or item.get("id") or "",
                })

            total = data.get("count", 0)
            print(f"  📦 Página {page}: {len(items)} productos (total disponible: {total})")

            if page * PAGE_SIZE >= min(total, max_productos):
                break

            page += 1
            time.sleep(DELAY)

        except Exception as e:
            print(f"  ❌ Error página {page}: {e}")
            break

    print(f"  ✅ Total {supermercado}: {len(productos)} productos")
    return productos


def guardar_csv(productos):
    if not productos:
        print("\n❌ No hay productos para guardar")
        return False

    campos = ["supermercado", "nombre_comercial", "precio", "marca",
              "categoria", "subcategoria", "precio_por_unidad",
              "url", "imagen", "referencia_externa"]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(productos)

    print(f"\n✅ CSV guardado: {OUTPUT_FILE}")
    print(f"📊 Total productos: {len(productos)}")

    # Resumen por supermercado
    print("\n📋 Resumen por supermercado:")
    from collections import Counter
    conteo = Counter(p["supermercado"] for p in productos)
    for super_, n in conteo.items():
        print(f"  {super_:20s}: {n} productos")

    return True


# ── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  🌍 OPEN FOOD FACTS — Productos supermercados ES")
    print("=" * 55)
    print(f"  Supermercados: {', '.join(SUPERMERCADOS)}")
    print(f"  Límite por super: 1,000 productos")

    todos = []

    for super_ in SUPERMERCADOS:
        prods = obtener_productos_supermercado(super_, max_productos=1000)
        todos.extend(prods)
        time.sleep(1)

    guardar_csv(todos)
    print(f"\n🎯 Listo. Importa '{OUTPUT_FILE}' en Supabase con gestor_masivo_fixed.py")
    print("\n⚠️  NOTA: Los precios estarán vacíos (OFF no tiene precios).")
    print("    Los productos sirven para el matching y catálogo.")
    print("    Los precios se pueden añadir después con scraping puntual.")
