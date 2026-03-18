"""
scraper_dia.py
Usa la API interna de DIA España — devuelve precios reales
Sin navegador, solo requests
"""

import requests
import csv
import time
from datetime import datetime

OUTPUT_FILE = f"dia_productos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
DELAY       = 0.4

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer":         "https://www.dia.es/",
    "Origin":          "https://www.dia.es",
}

# Categorías de DIA con sus IDs de la API
CATEGORIAS = [
    {"id": "01",  "nombre": "Frutas y Verduras"},
    {"id": "02",  "nombre": "Carne y Charcutería"},
    {"id": "03",  "nombre": "Pescado y Marisco"},
    {"id": "04",  "nombre": "Lácteos y Huevos"},
    {"id": "05",  "nombre": "Panadería"},
    {"id": "06",  "nombre": "Congelados"},
    {"id": "07",  "nombre": "Bebidas"},
    {"id": "08",  "nombre": "Despensa"},
    {"id": "09",  "nombre": "Snacks y Dulces"},
    {"id": "10",  "nombre": "Desayuno y Cereales"},
    {"id": "11",  "nombre": "Higiene y Belleza"},
    {"id": "12",  "nombre": "Limpieza del hogar"},
    {"id": "13",  "nombre": "Bebés"},
    {"id": "14",  "nombre": "Mascotas"},
]

# Intentaremos estas URLs en orden hasta que una funcione
API_URLS = [
    "https://www.dia.es/api/v1/c/{cat_id}/products?currentPage={page}&pageSize={size}&lang=es",
    "https://www.dia.es/api/rest/v2/dia/categories/{cat_id}/products?currentPage={page}&pageSize={size}",
    "https://www.dia.es/webapi/api/products/search?categoryCode={cat_id}&page={page}&pageSize={size}",
]


def obtener_productos(categoria):
    productos = []
    page      = 0
    page_size = 48
    url_base  = None

    print(f"\n📂 {categoria['nombre']}")

    # Detectar qué URL funciona en la primera petición
    for template in API_URLS:
        url = template.format(cat_id=categoria["id"], page=0, size=page_size)
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            if r.status_code == 200:
                data = r.json()
                if data:
                    url_base = template
                    print(f"  ✅ API encontrada: {url.split('dia.es')[1].split('?')[0]}")
                    break
        except:
            continue

    if not url_base:
        print(f"  ⚠️  No se encontró API para esta categoría")
        return productos

    # Paginar con la URL que funcionó
    while True:
        url  = url_base.format(cat_id=categoria["id"], page=page, size=page_size)
        try:
            r    = requests.get(url, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                break

            data  = r.json()
            items = (
                data.get("products") or
                data.get("results") or
                data.get("data", {}).get("products") or
                []
            )

            if not items:
                break

            for item in items:
                p = parsear_producto(item, categoria["nombre"])
                if p:
                    productos.append(p)

            total = (
                data.get("pagination", {}).get("totalResults") or
                data.get("total") or
                data.get("totalCount") or
                0
            )
            print(f"  📦 Página {page + 1}: {len(items)} productos (total: {total})")

            page += 1
            if page * page_size >= total or len(items) < page_size:
                break

            time.sleep(DELAY)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            break

    return productos


def parsear_producto(item, categoria_nombre):
    try:
        nombre = (
            item.get("name") or
            item.get("title") or
            item.get("displayName") or ""
        ).strip()

        if not nombre:
            return None

        # Precio — DIA lo pone en varios sitios
        precio = (
            item.get("price") or
            item.get("priceData", {}).get("value") or
            item.get("purchasePrice") or
            ""
        )
        if isinstance(precio, dict):
            precio = precio.get("value") or precio.get("formattedValue") or ""
        if isinstance(precio, str):
            precio = precio.replace("€", "").replace(",", ".").strip()

        # Imagen
        imagen = ""
        imgs   = item.get("images") or []
        if isinstance(imgs, list) and imgs:
            imagen = imgs[0].get("url") or ""
        if not imagen:
            imagen = item.get("image") or item.get("imageUrl") or ""
        if imagen and not imagen.startswith("http"):
            imagen = "https://www.dia.es" + imagen

        # URL
        slug = item.get("url") or item.get("code") or ""
        url  = f"https://www.dia.es{slug}" if slug and not slug.startswith("http") else slug

        return {
            "supermercado":      "DIA",
            "nombre_comercial":  nombre,
            "precio":            round(float(precio), 2) if precio else "",
            "marca":             item.get("brand") or item.get("brandName") or "DIA",
            "categoria":         categoria_nombre,
            "subcategoria":      item.get("subcategory") or "",
            "precio_por_unidad": item.get("pricePerUnit") or item.get("basePrice") or "",
            "url":               url,
            "imagen":            imagen,
            "referencia_externa": str(item.get("code") or item.get("id") or ""),
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

    con_precio = sum(1 for p in productos if p["precio"] != "")
    print(f"\n✅ CSV guardado: {OUTPUT_FILE}")
    print(f"📊 Total productos  : {len(productos)}")
    print(f"💰 Con precio       : {con_precio}")
    print(f"❓ Sin precio       : {len(productos) - con_precio}")
    return True


if __name__ == "__main__":
    print("=" * 55)
    print("  🛒 SCRAPER DIA — API interna")
    print("=" * 55)

    todos = []

    for cat in CATEGORIAS:
        prods = obtener_productos(cat)
        todos.extend(prods)
        print(f"  ✅ Subtotal: {len(prods)}")
        time.sleep(0.5)

    print(f"\n📊 TOTAL: {len(todos)} productos")
    guardado = guardar_csv(todos)

    if guardado:
        print(f"\n🎯 Listo. Importa '{OUTPUT_FILE}' en Supabase.")
    else:
        print("\n💡 Si da 0 productos, ejecuta desde el buscador de categorías:")
        print("   python scraper_dia_busqueda.py")
