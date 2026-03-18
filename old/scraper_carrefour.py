"""
scraper_carrefour.py
Usa la API pública oficial de Carrefour España
No requiere navegador — solo requests
"""

import requests
import json
import csv
import time
from datetime import datetime

# ── Configuración ────────────────────────────────────────────
OUTPUT_FILE = f"carrefour_productos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
DELAY       = 0.3

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.carrefour.es/",
}

# API base de Carrefour España
API_BASE = "https://www.carrefour.es/api/rest"

# Categorías principales de Carrefour
CATEGORIAS = [
    {"id": "cat_1",   "slug": "frutas-y-verduras",         "nombre": "Frutas y Verduras"},
    {"id": "cat_2",   "slug": "carne-y-charcuteria",       "nombre": "Carne y Charcutería"},
    {"id": "cat_3",   "slug": "pescado-y-marisco",         "nombre": "Pescado y Marisco"},
    {"id": "cat_4",   "slug": "lacteos-y-huevos",          "nombre": "Lácteos y Huevos"},
    {"id": "cat_5",   "slug": "panaderia-y-bolleria",      "nombre": "Panadería"},
    {"id": "cat_6",   "slug": "congelados",                "nombre": "Congelados"},
    {"id": "cat_7",   "slug": "bebidas",                   "nombre": "Bebidas"},
    {"id": "cat_8",   "slug": "aceite-arroz-legumbres",    "nombre": "Aceite, Arroz y Legumbres"},
    {"id": "cat_9",   "slug": "pasta-y-sopas",             "nombre": "Pasta y Sopas"},
    {"id": "cat_10",  "slug": "conservas-y-platos-preparados", "nombre": "Conservas"},
    {"id": "cat_11",  "slug": "snacks-y-aperitivos",       "nombre": "Snacks"},
    {"id": "cat_12",  "slug": "dulces-y-chocolates",       "nombre": "Dulces"},
    {"id": "cat_13",  "slug": "cafe-e-infusiones",         "nombre": "Café e Infusiones"},
    {"id": "cat_14",  "slug": "cereales-y-galletas",       "nombre": "Cereales y Galletas"},
    {"id": "cat_15",  "slug": "higiene-y-belleza",         "nombre": "Higiene"},
    {"id": "cat_16",  "slug": "limpieza-del-hogar",        "nombre": "Limpieza"},
    {"id": "cat_17",  "slug": "bebes",                     "nombre": "Bebés"},
    {"id": "cat_18",  "slug": "mascotas",                  "nombre": "Mascotas"},
]


def obtener_productos(categoria_slug, categoria_nombre):
    """Obtiene productos de Carrefour por categoría"""
    productos = []
    offset = 0
    page_size = 48

    while True:
        # URL 1: API REST oficial
        url = (
            f"{API_BASE}/catalogs/carrefour/categories/{categoria_slug}/products"
            f"?offset={offset}&limit={page_size}&lang=es"
        )

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)

            # Si falla, intentar URL alternativa
            if resp.status_code != 200:
                url2 = (
                    f"https://www.carrefour.es/api/rest/products/search"
                    f"?category={categoria_slug}&offset={offset}&limit={page_size}"
                )
                resp = requests.get(url2, headers=HEADERS, timeout=15)

            if resp.status_code != 200:
                print(f"  ⚠️  HTTP {resp.status_code} — terminando categoría")
                break

            data = resp.json()

            # Extraer productos (varias estructuras posibles)
            items = (
                data.get("results") or
                data.get("products") or
                data.get("data", {}).get("products") or
                []
            )

            if not items:
                break

            for item in items:
                p = parsear_producto(item, categoria_nombre, categoria_slug)
                if p:
                    productos.append(p)

            print(f"  📦 Offset {offset}: {len(items)} productos")

            total = data.get("total") or data.get("totalCount") or 0
            offset += page_size
            if offset >= total or len(items) < page_size:
                break

            time.sleep(DELAY)

        except Exception as e:
            print(f"  ❌ Error offset {offset}: {e}")
            break

    return productos


def parsear_producto(item, categoria_nombre, categoria_slug):
    """Extrae campos de un producto de la API de Carrefour"""
    try:
        nombre = (
            item.get("display_name") or
            item.get("name") or
            item.get("title") or ""
        ).strip()

        if not nombre:
            return None

        # Precio
        precio_data = item.get("price") or item.get("priceData") or {}
        if isinstance(precio_data, (int, float)):
            precio = precio_data
        else:
            precio = (
                precio_data.get("value") or
                precio_data.get("amount") or
                precio_data.get("selling_price") or
                item.get("selling_price") or
                0
            )

        # Imagen
        media = item.get("media") or []
        imagen = ""
        if isinstance(media, list) and media:
            imagen = media[0].get("url") or media[0].get("path") or ""
        elif isinstance(media, dict):
            imagen = media.get("url") or ""
        if not imagen:
            imagen = item.get("image") or item.get("imageUrl") or ""

        # URL del producto
        slug = item.get("slug") or item.get("id") or ""
        url = f"https://www.carrefour.es/supermercado/{slug}/p" if slug else ""

        return {
            "supermercado":      "Carrefour",
            "nombre_comercial":  nombre,
            "precio":            round(float(precio), 2) if precio else "",
            "marca":             item.get("brand") or item.get("brandName") or "",
            "categoria":         categoria_nombre,
            "subcategoria":      item.get("subcategory") or "",
            "precio_por_unidad": item.get("price_per_unit") or item.get("pricePerUnit") or "",
            "url":               url,
            "imagen":            imagen,
            "referencia_externa": str(item.get("id") or item.get("ean") or ""),
        }
    except Exception as e:
        print(f"  ⚠️  Error parseando: {e}")
        return None


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
    return True


# ── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  🛒 SCRAPER CARREFOUR — API REST oficial")
    print("=" * 55)

    todos = []

    for cat in CATEGORIAS:
        print(f"\n📂 {cat['nombre']}")
        prods = obtener_productos(cat["slug"], cat["nombre"])
        todos.extend(prods)
        print(f"  ✅ Subtotal categoría: {len(prods)}")
        time.sleep(DELAY)

    print(f"\n📊 TOTAL PRODUCTOS: {len(todos)}")
    guardado = guardar_csv(todos)

    if guardado:
        print(f"\n🎯 Listo. Importa '{OUTPUT_FILE}' en Supabase.")
    else:
        print("\n💡 Si no funcionó, prueba: python scraper_carrefour.py")
