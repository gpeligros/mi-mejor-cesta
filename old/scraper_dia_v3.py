"""
scraper_dia_v3.py
Corregido con la estructura REAL del JSON de DIA:
  - productos en: search_items[]
  - precio en: prices.price
  - paginación en: pagination.total_pages
"""

import requests
import csv
import time
from datetime import datetime

OUTPUT_FILE = f"dia_productos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
DELAY       = 0.5

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer":         "https://www.dia.es/",
}

BUSQUEDAS = [
    {"q": "leche",          "categoria": "Lácteos y Huevos"},
    {"q": "yogur",          "categoria": "Lácteos y Huevos"},
    {"q": "queso",          "categoria": "Lácteos y Huevos"},
    {"q": "mantequilla",    "categoria": "Lácteos y Huevos"},
    {"q": "huevos",         "categoria": "Lácteos y Huevos"},
    {"q": "nata",           "categoria": "Lácteos y Huevos"},
    {"q": "fruta",          "categoria": "Frutas y Verduras"},
    {"q": "verdura",        "categoria": "Frutas y Verduras"},
    {"q": "ensalada",       "categoria": "Frutas y Verduras"},
    {"q": "carne",          "categoria": "Carne y Charcutería"},
    {"q": "pollo",          "categoria": "Carne y Charcutería"},
    {"q": "jamon",          "categoria": "Carne y Charcutería"},
    {"q": "embutido",       "categoria": "Carne y Charcutería"},
    {"q": "pescado",        "categoria": "Pescado y Marisco"},
    {"q": "atun",           "categoria": "Pescado y Marisco"},
    {"q": "salmon",         "categoria": "Pescado y Marisco"},
    {"q": "pan",            "categoria": "Panadería"},
    {"q": "bolleria",       "categoria": "Panadería"},
    {"q": "tostadas",       "categoria": "Panadería"},
    {"q": "pizza",          "categoria": "Congelados"},
    {"q": "congelado",      "categoria": "Congelados"},
    {"q": "helado",         "categoria": "Congelados"},
    {"q": "agua",           "categoria": "Bebidas"},
    {"q": "refresco",       "categoria": "Bebidas"},
    {"q": "zumo",           "categoria": "Bebidas"},
    {"q": "cerveza",        "categoria": "Bebidas"},
    {"q": "vino",           "categoria": "Bebidas"},
    {"q": "aceite",         "categoria": "Aceite y Condimentos"},
    {"q": "arroz",          "categoria": "Arroz y Legumbres"},
    {"q": "legumbres",      "categoria": "Arroz y Legumbres"},
    {"q": "pasta",          "categoria": "Pasta y Sopas"},
    {"q": "sopa",           "categoria": "Pasta y Sopas"},
    {"q": "conservas",      "categoria": "Conservas"},
    {"q": "salsa",          "categoria": "Conservas"},
    {"q": "snacks",         "categoria": "Snacks"},
    {"q": "patatas fritas", "categoria": "Snacks"},
    {"q": "chocolate",      "categoria": "Dulces"},
    {"q": "galletas",       "categoria": "Cereales y Galletas"},
    {"q": "cereales",       "categoria": "Cereales y Galletas"},
    {"q": "cafe",           "categoria": "Café e Infusiones"},
    {"q": "infusion",       "categoria": "Café e Infusiones"},
    {"q": "champu",         "categoria": "Higiene"},
    {"q": "gel",            "categoria": "Higiene"},
    {"q": "detergente",     "categoria": "Limpieza"},
    {"q": "limpiador",      "categoria": "Limpieza"},
    {"q": "pañales",        "categoria": "Bebés"},
    {"q": "pienso",         "categoria": "Mascotas"},
]


def buscar_productos(query, categoria):
    productos = []
    vistos    = set()
    pagina    = 1

    while True:
        url = (
            f"https://www.dia.es/api/v1/search-back/search/reduced"
            f"?q={requests.utils.quote(query)}&page={pagina}"
        )

        try:
            r = requests.get(url, headers=HEADERS, timeout=15)

            if r.status_code != 200:
                print(f"  ⚠️  HTTP {r.status_code}")
                break

            data = r.json()

            # ── Estructura real: search_items ──────────────────────
            items      = data.get("search_items", [])
            paginacion = data.get("pagination", {})
            total_pags = paginacion.get("total_pages", 1)

            if not items:
                break

            nuevos = 0
            for item in items:
                sku = str(item.get("sku_id") or item.get("object_id") or "")
                if sku in vistos:
                    continue
                vistos.add(sku)

                p = parsear_producto(item, categoria)
                if p:
                    productos.append(p)
                    nuevos += 1

            print(f"  📦 '{query}' pág {pagina}/{total_pags}: {nuevos} nuevos")

            if pagina >= total_pags:
                break

            pagina += 1
            time.sleep(DELAY)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            break

    return productos


def parsear_producto(item, categoria):
    try:
        nombre = (item.get("display_name") or "").strip()
        if not nombre:
            return None

        # ── Precio real ────────────────────────────────────────────
        precios = item.get("prices") or {}
        precio  = precios.get("price") or ""
        precio_por_unidad = precios.get("price_per_unit") or ""

        # ── Imagen ─────────────────────────────────────────────────
        imagen = item.get("image") or ""
        if imagen and not imagen.startswith("http"):
            imagen = "https://www.dia.es" + imagen

        # ── URL ────────────────────────────────────────────────────
        url = item.get("url") or ""
        if url and not url.startswith("http"):
            url = "https://www.dia.es" + url

        # ── Categoría real de DIA ──────────────────────────────────
        cat_real = item.get("l1_category_description") or categoria
        subcat   = item.get("l2_category_description") or ""

        return {
            "supermercado":      "DIA",
            "nombre_comercial":  nombre,
            "precio":            round(float(precio), 2) if precio else "",
            "marca":             item.get("brand") or "DIA",
            "categoria":         cat_real,
            "subcategoria":      subcat,
            "precio_por_unidad": str(precio_por_unidad),
            "url":               url,
            "imagen":            imagen,
            "referencia_externa": str(item.get("sku_id") or item.get("object_id") or ""),
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
    print(f"💰 Con precio real  : {con_precio}")
    return True


if __name__ == "__main__":
    print("=" * 55)
    print("  🛒 SCRAPER DIA v3 — estructura JSON real")
    print("=" * 55)

    todos  = []
    vistos = set()

    for b in BUSQUEDAS:
        print(f"\n📂 {b['categoria']} → '{b['q']}'")
        prods  = buscar_productos(b["q"], b["categoria"])
        nuevos = [p for p in prods if p["referencia_externa"] not in vistos]
        for p in nuevos:
            vistos.add(p["referencia_externa"])
        todos.extend(nuevos)
        print(f"  ✅ +{len(nuevos)} nuevos | total: {len(todos)}")
        time.sleep(0.3)

    guardar_csv(todos)
    print(f"\n🎯 Listo. Importa '{OUTPUT_FILE}' en Supabase.")
