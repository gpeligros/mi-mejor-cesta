"""
scraper_dia_v2.py
Usa la API real de DIA: /api/v1/search-back/search/reduced
Descubierta capturando peticiones reales del navegador
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

# Términos de búsqueda por categoría
BUSQUEDAS = [
    {"q": "lacteos",          "categoria": "Lácteos y Huevos"},
    {"q": "leche",            "categoria": "Lácteos y Huevos"},
    {"q": "yogur",            "categoria": "Lácteos y Huevos"},
    {"q": "queso",            "categoria": "Lácteos y Huevos"},
    {"q": "huevos",           "categoria": "Lácteos y Huevos"},
    {"q": "fruta",            "categoria": "Frutas y Verduras"},
    {"q": "verdura",          "categoria": "Frutas y Verduras"},
    {"q": "carne",            "categoria": "Carne y Charcutería"},
    {"q": "pollo",            "categoria": "Carne y Charcutería"},
    {"q": "jamon",            "categoria": "Carne y Charcutería"},
    {"q": "pescado",          "categoria": "Pescado y Marisco"},
    {"q": "atun",             "categoria": "Pescado y Marisco"},
    {"q": "pan",              "categoria": "Panadería"},
    {"q": "bolleria",         "categoria": "Panadería"},
    {"q": "congelados",       "categoria": "Congelados"},
    {"q": "pizza",            "categoria": "Congelados"},
    {"q": "agua",             "categoria": "Bebidas"},
    {"q": "refresco",         "categoria": "Bebidas"},
    {"q": "zumo",             "categoria": "Bebidas"},
    {"q": "cerveza",          "categoria": "Bebidas"},
    {"q": "vino",             "categoria": "Bebidas"},
    {"q": "aceite",           "categoria": "Aceite, Arroz y Legumbres"},
    {"q": "arroz",            "categoria": "Aceite, Arroz y Legumbres"},
    {"q": "legumbres",        "categoria": "Aceite, Arroz y Legumbres"},
    {"q": "pasta",            "categoria": "Pasta y Sopas"},
    {"q": "sopa",             "categoria": "Pasta y Sopas"},
    {"q": "conservas",        "categoria": "Conservas"},
    {"q": "salsa",            "categoria": "Conservas"},
    {"q": "snacks",           "categoria": "Snacks"},
    {"q": "patatas fritas",   "categoria": "Snacks"},
    {"q": "chocolate",        "categoria": "Dulces"},
    {"q": "galletas",         "categoria": "Cereales y Galletas"},
    {"q": "cereales",         "categoria": "Cereales y Galletas"},
    {"q": "cafe",             "categoria": "Café e Infusiones"},
    {"q": "infusion",         "categoria": "Café e Infusiones"},
    {"q": "higiene",          "categoria": "Higiene"},
    {"q": "champu",           "categoria": "Higiene"},
    {"q": "limpieza",         "categoria": "Limpieza del hogar"},
    {"q": "detergente",       "categoria": "Limpieza del hogar"},
    {"q": "bebe",             "categoria": "Bebés"},
    {"q": "mascotas",         "categoria": "Mascotas"},
    {"q": "pienso",           "categoria": "Mascotas"},
]


def buscar_productos(query, categoria, max_paginas=5):
    productos  = []
    vistos     = set()

    for pagina in range(1, max_paginas + 1):
        url = f"https://www.dia.es/api/v1/search-back/search/reduced?q={requests.utils.quote(query)}&page={pagina}"

        try:
            r = requests.get(url, headers=HEADERS, timeout=12)

            if r.status_code != 200:
                print(f"  ⚠️  HTTP {r.status_code} en página {pagina}")
                break

            data  = r.json()

            # Extraer productos (varios formatos posibles)
            items = (
                data.get("products") or
                data.get("results") or
                data.get("items") or
                []
            )

            if not items:
                break

            nuevos = 0
            for item in items:
                p = parsear_producto(item, categoria)
                if p and p["referencia_externa"] not in vistos:
                    vistos.add(p["referencia_externa"])
                    productos.append(p)
                    nuevos += 1

            total = (
                data.get("total") or
                data.get("totalResults") or
                data.get("pagination", {}).get("totalResults") or
                0
            )

            print(f"  📦 '{query}' pág {pagina}: {nuevos} nuevos (total API: {total})")

            if nuevos == 0 or pagina * 20 >= total:
                break

            time.sleep(DELAY)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            break

    return productos


def parsear_producto(item, categoria):
    try:
        nombre = (
            item.get("name") or
            item.get("displayName") or
            item.get("title") or ""
        ).strip()

        if not nombre:
            return None

        # Precio
        precio = (
            item.get("price") or
            item.get("regularPrice") or
            item.get("priceData", {}).get("value") or
            ""
        )
        if isinstance(precio, dict):
            precio = precio.get("value") or precio.get("formattedValue") or ""
        if isinstance(precio, str):
            precio = precio.replace("€", "").replace(",", ".").strip()

        # Imagen
        imagen = item.get("image") or item.get("imageUrl") or ""
        imgs   = item.get("images") or []
        if not imagen and isinstance(imgs, list) and imgs:
            imagen = imgs[0].get("url") or ""
        if imagen and not imagen.startswith("http"):
            imagen = "https://www.dia.es" + imagen

        # URL
        slug = item.get("url") or item.get("slug") or item.get("code") or ""
        url  = f"https://www.dia.es{slug}" if slug and not slug.startswith("http") else slug

        ref  = str(item.get("code") or item.get("id") or item.get("ean") or nombre)

        return {
            "supermercado":      "DIA",
            "nombre_comercial":  nombre,
            "precio":            round(float(precio), 2) if precio else "",
            "marca":             item.get("brand") or item.get("brandName") or "DIA",
            "categoria":         categoria,
            "subcategoria":      item.get("subcategory") or "",
            "precio_por_unidad": item.get("pricePerUnit") or item.get("unitPrice") or "",
            "url":               url,
            "imagen":            imagen,
            "referencia_externa": ref,
        }
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
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
    print("  🛒 SCRAPER DIA v2 — API /search-back/search/reduced")
    print("=" * 55)

    todos  = []
    vistos = set()

    for b in BUSQUEDAS:
        print(f"\n📂 {b['categoria']} → búsqueda: '{b['q']}'")
        prods = buscar_productos(b["q"], b["categoria"])

        # Deduplicar globalmente por referencia
        nuevos = [p for p in prods if p["referencia_externa"] not in vistos]
        for p in nuevos:
            vistos.add(p["referencia_externa"])
        todos.extend(nuevos)

        print(f"  ✅ +{len(nuevos)} nuevos (total acumulado: {len(todos)})")
        time.sleep(0.3)

    guardar_csv(todos)
    print(f"\n🎯 Listo. Importa '{OUTPUT_FILE}' en Supabase.")
