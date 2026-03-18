"""
scraper_lidl.py - Versión 2 (API interna de Lidl)
Usa la API oficial de Lidl en lugar de scraping HTML
Más rápido y sin bloqueos de anti-bot
"""

import requests
import json
import csv
import time
import os
from datetime import datetime

# ── Configuración ────────────────────────────────────────────
OUTPUT_FILE = f"lidl_productos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
DELAY       = 0.5   # segundos entre peticiones (no abusar)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.lidl.es",
    "Referer": "https://www.lidl.es/",
}

# Categorías de la API de Lidl España
CATEGORIAS = [
    {"id": "fruit-vegetables",       "nombre": "Frutas y Verduras"},
    {"id": "meat-fish",              "nombre": "Carne y Pescado"},
    {"id": "dairy-eggs",             "nombre": "Lácteos y Huevos"},
    {"id": "bakery",                 "nombre": "Panadería"},
    {"id": "frozen",                 "nombre": "Congelados"},
    {"id": "beverages",              "nombre": "Bebidas"},
    {"id": "pantry",                 "nombre": "Despensa"},
    {"id": "snacks-sweets",          "nombre": "Snacks y Dulces"},
    {"id": "breakfast-spreads",      "nombre": "Desayuno"},
    {"id": "hygiene-body-care",      "nombre": "Higiene"},
    {"id": "cleaning-household",     "nombre": "Limpieza del hogar"},
    {"id": "baby",                   "nombre": "Bebé"},
    {"id": "pet",                    "nombre": "Mascotas"},
]

# ── Funciones ────────────────────────────────────────────────

def obtener_productos_categoria(categoria_id, categoria_nombre):
    """Obtiene productos de una categoría via API de Lidl"""
    productos = []
    page = 1
    
    while True:
        url = (
            f"https://www.lidl.es/api/v1/products"
            f"?category={categoria_id}"
            f"&page={page}"
            f"&pageSize=50"
            f"&locale=es_ES"
        )
        
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            
            if resp.status_code == 404:
                # Intentar URL alternativa
                url2 = (
                    f"https://www.lidl.es/api/groceries/v1/products"
                    f"?category={categoria_id}&page={page}&pageSize=50"
                )
                resp = requests.get(url2, headers=HEADERS, timeout=15)
            
            if resp.status_code != 200:
                print(f"  ⚠️  HTTP {resp.status_code} en página {page} — terminando categoría")
                break
            
            data = resp.json()
            
            # Extraer lista de productos (estructura puede variar)
            items = (
                data.get("products") or
                data.get("items") or
                data.get("data", {}).get("products") or
                []
            )
            
            if not items:
                break
            
            for item in items:
                producto = parsear_producto(item, categoria_nombre)
                if producto:
                    productos.append(producto)
            
            print(f"  📦 Página {page}: {len(items)} productos")
            
            # Verificar si hay más páginas
            total     = data.get("totalCount") or data.get("total") or 0
            por_pagina = 50
            if page * por_pagina >= total:
                break
            
            page += 1
            time.sleep(DELAY)
            
        except requests.exceptions.Timeout:
            print(f"  ⏱️  Timeout en página {page}")
            break
        except Exception as e:
            print(f"  ❌ Error en página {page}: {e}")
            break
    
    return productos


def parsear_producto(item, categoria_nombre):
    """Extrae los campos que necesitamos de un producto de la API"""
    try:
        # Precio — puede estar en diferentes sitios
        precio = (
            item.get("price") or
            item.get("currentPrice") or
            item.get("priceData", {}).get("price") or
            0
        )
        if isinstance(precio, dict):
            precio = precio.get("value") or precio.get("amount") or 0

        nombre = (
            item.get("name") or
            item.get("title") or
            item.get("fullTitle") or
            ""
        ).strip()

        if not nombre:
            return None

        imagen = (
            item.get("image") or
            item.get("imageUrl") or
            item.get("thumbnailUrl") or
            (item.get("images") or [{}])[0].get("url") or
            ""
        )

        return {
            "supermercado":    "Lidl",
            "nombre_comercial": nombre,
            "precio":          round(float(precio), 2) if precio else "",
            "marca":           item.get("brand") or item.get("brandName") or "Lidl",
            "categoria":       categoria_nombre,
            "subcategoria":    item.get("subcategory") or item.get("subCategory") or "",
            "precio_por_unidad": item.get("pricePerUnit") or item.get("basePrice") or "",
            "url":             item.get("url") or item.get("productUrl") or "",
            "imagen":          imagen,
            "referencia_externa": str(item.get("id") or item.get("productId") or ""),
        }
    except Exception as e:
        print(f"  ⚠️  Error parseando producto: {e}")
        return None


def scraper_alternativo_html():
    """
    Alternativa: descarga el JSON embebido en el HTML de Lidl
    Lidl carga sus productos como __NEXT_DATA__ en el HTML
    """
    from playwright.sync_api import sync_playwright
    import re

    productos = []
    print("\n🔄 Intentando método alternativo (HTML + JSON embebido)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="es-ES",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.set_extra_http_headers({"Accept-Language": "es-ES,es;q=0.9"})

        for cat in CATEGORIAS:
            url = f"https://www.lidl.es/c/{cat['id']}"
            print(f"\n📂 {cat['nombre']} → {url}")

            try:
                page.goto(url, timeout=45000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)  # esperar JS

                # Buscar JSON embebido en la página
                content = page.content()
                match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', content, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    items = (
                        data.get("props", {})
                            .get("pageProps", {})
                            .get("products") or []
                    )
                    for item in items:
                        p_ = parsear_producto(item, cat["nombre"])
                        if p_:
                            productos.append(p_)
                    print(f"  ✅ {len(items)} productos encontrados")
                else:
                    # Buscar cards de productos en el DOM
                    cards = page.query_selector_all('[data-testid="product-card"], .product-card, article.product')
                    print(f"  🃏 {len(cards)} cards encontradas en DOM")
                    for card in cards:
                        try:
                            nombre = card.query_selector('h2, h3, .product-name, [data-testid="product-name"]')
                            precio = card.query_selector('[data-testid="price"], .price, .product-price')
                            imagen = card.query_selector('img')
                            productos.append({
                                "supermercado":      "Lidl",
                                "nombre_comercial":  nombre.inner_text().strip() if nombre else "",
                                "precio":            precio.inner_text().strip().replace("€","").replace(",",".") if precio else "",
                                "marca":             "Lidl",
                                "categoria":         cat["nombre"],
                                "subcategoria":      "",
                                "precio_por_unidad": "",
                                "url":               url,
                                "imagen":            imagen.get_attribute("src") if imagen else "",
                                "referencia_externa": "",
                            })
                        except:
                            pass

            except Exception as e:
                print(f"  ❌ Error: {e}")

            time.sleep(1)

        browser.close()

    return productos


def guardar_csv(productos, filename):
    """Guarda los productos en CSV"""
    if not productos:
        print("\n❌ No hay productos para guardar")
        return

    campos = ["supermercado", "nombre_comercial", "precio", "marca",
              "categoria", "subcategoria", "precio_por_unidad", "url",
              "imagen", "referencia_externa"]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(productos)

    print(f"\n✅ CSV guardado: {filename}")
    print(f"📊 Total productos: {len(productos)}")


# ── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  🛒 SCRAPER LIDL v2 — API + Playwright fallback")
    print("=" * 55)

    todos_productos = []

    # ── Método 1: API directa ────────────────────────────────
    print("\n🚀 Intentando API directa de Lidl...\n")
    for cat in CATEGORIAS:
        print(f"📂 {cat['nombre']}")
        prods = obtener_productos_categoria(cat["id"], cat["nombre"])
        todos_productos.extend(prods)
        print(f"  ✅ Subtotal: {len(prods)} productos")
        time.sleep(DELAY)

    # ── Método 2: Playwright si la API no devolvió nada ──────
    if len(todos_productos) < 50:
        print(f"\n⚠️  API devolvió solo {len(todos_productos)} productos.")
        print("🔄 Activando método Playwright (navegador)...")
        todos_productos = scraper_alternativo_html()

    # ── Guardar ──────────────────────────────────────────────
    guardar_csv(todos_productos, OUTPUT_FILE)
    print(f"\n🎯 Listo. Importa '{OUTPUT_FILE}' en Supabase.")