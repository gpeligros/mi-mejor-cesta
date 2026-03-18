"""
scraper_mercadona_v2.py
API oficial Mercadona — estructura real:
  /api/categories/ → categorías principales con subcategorías
  /api/categories/{subcat_id}/ → productos de esa subcategoría

Captura precio_unidad calculado desde price_instructions.
"""

import requests
import json
import csv
import time
import os
import urllib.request
import urllib.error
from datetime import datetime

try:
    from dotenv import load_dotenv
    _raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(_raiz, '.env'))
except ImportError:
    pass

# ── CONFIGURACIÓN ─────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
DELAY        = 0.3
OUTPUT_FILE  = f"mercadona_v2_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
# ─────────────────────────────────────────────────────────────

API_BASE = "https://tienda.mercadona.es/api"
HEADERS  = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":          "application/json",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer":         "https://tienda.mercadona.es/",
}
HEADERS_SB = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "resolution=merge-duplicates,return=minimal",
}


def get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  ❌ {e}")
    return None


def calcular_precio_unidad(pi):
    """
    Calcula precio_unidad desde price_instructions.
    Ejemplos:
      pack 6 latas 0.33L × 0.97€/ud → "0.97€/ud · 2.94€/L"
      1L botella 1.05€ → "1.05€/L"
    """
    if not pi:
        return None

    unit_price  = pi.get("unit_price")   or pi.get("bulk_price")  or 0
    unit_size   = pi.get("unit_size")    or 0    # tamaño de cada unidad (ej: 0.33)
    unit_name   = pi.get("unit_name")    or ""   # "latas", "botellas", "l", "kg"
    is_pack     = pi.get("is_pack")      or False
    pack_size   = pi.get("pack_size")    or 1    # unidades en el pack

    try:
        unit_price = float(unit_price)
        unit_size  = float(unit_size) if unit_size else 0
        pack_size  = float(pack_size) if pack_size else 1
    except:
        return None

    if unit_price <= 0:
        return None

    # Precio por unidad individual del pack
    precio_ud = round(unit_price / pack_size, 2) if is_pack and pack_size > 1 else unit_price

    # Precio por litro/kg si tenemos tamaño
    if unit_size > 0 and unit_name.lower() in ['l', 'kg', 'litros', 'kilos']:
        total_litros = unit_size * (pack_size if is_pack else 1)
        precio_por_base = round(unit_price / total_litros, 2)
        unidad_base = "L" if "l" in unit_name.lower() else "kg"
        if is_pack and pack_size > 1:
            return f"{precio_ud}€/ud · {precio_por_base}€/{unidad_base}"
        return f"{precio_por_base}€/{unidad_base}"
    elif is_pack and pack_size > 1:
        return f"{precio_ud}€/ud"

    return None


def parsear_producto(item, cat_nombre, subcat_nombre):
    try:
        nombre = (item.get("display_name") or "").strip()
        if not nombre:
            return None

        pi     = item.get("price_instructions") or {}
        precio = pi.get("unit_price") or pi.get("bulk_price") or 0

        try:
            precio = float(precio)
        except:
            precio = 0

        precio_unidad = calcular_precio_unidad(pi)
        imagen        = item.get("thumbnail") or ""
        url           = item.get("share_url") or f"https://tienda.mercadona.es/product/{item.get('id','')}"
        id_externo    = str(item.get("id") or "")

        return {
            "id":               id_externo,
            "nombre_comercial": nombre,
            "precio":           round(precio, 2) if precio else None,
            "precio_unidad":    precio_unidad,
            "marca":            None,
            "url":              url,
            "imagen":           imagen,
            "disponible":       True,
            "categoria":        cat_nombre,
            "subcategoria":     subcat_nombre,
        }
    except:
        return None


def scraping():
    print("\n📂 Obteniendo árbol de categorías...")
    data = get(f"{API_BASE}/categories/?lang=es")
    if not data:
        print("❌ No se pudo obtener categorías"); return []

    cats_principales = data.get("results", [])
    print(f"  {len(cats_principales)} categorías principales")

    todos  = []
    vistos = set()

    for cat in cats_principales:
        cat_id   = cat.get("id")
        cat_name = cat.get("name", "")
        subcats  = cat.get("categories", [])

        print(f"\n📂 {cat_name} ({len(subcats)} subcategorías)")

        for subcat in subcats:
            sub_id   = subcat.get("id")
            sub_name = subcat.get("name", "")

            data_sub = get(f"{API_BASE}/categories/{sub_id}/?lang=es")
            if not data_sub:
                continue

            # Productos pueden estar en data_sub directamente o en sub-subcategorías
            prods_raw = []

            # Nivel directo
            for key in ["products", "result", "items"]:
                if key in data_sub and isinstance(data_sub[key], list):
                    prods_raw.extend(data_sub[key])

            # Sub-subcategorías
            for sub2 in data_sub.get("categories", []):
                prods_raw.extend(sub2.get("products", []))

            nuevos = 0
            for item in prods_raw:
                p = parsear_producto(item, cat_name, sub_name)
                if p and p["id"] and p["id"] not in vistos:
                    vistos.add(p["id"])
                    todos.append(p)
                    nuevos += 1

            con_pu = sum(1 for p in todos[-nuevos:] if p.get("precio_unidad")) if nuevos else 0
            if nuevos:
                print(f"  └─ {sub_name}: {nuevos} prods | {con_pu} con precio_unidad")

            time.sleep(DELAY)

    return todos


def guardar_csv(productos):
    campos = ["id", "nombre_comercial", "precio", "precio_unidad",
              "marca", "url", "imagen", "categoria", "subcategoria"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(productos)
    print(f"  📄 CSV guardado: {OUTPUT_FILE}")


def subir_supabase(productos):
    campos_tabla = ["id", "nombre_comercial", "precio", "precio_unidad",
                    "marca", "url", "imagen", "disponible"]
    ok = err = 0
    BATCH = 50

    for i in range(0, len(productos), BATCH):
        lote  = [{k: p[k] for k in campos_tabla if k in p} for p in productos[i:i+BATCH]]
        n     = i // BATCH + 1
        total = (len(productos) + BATCH - 1) // BATCH
        url   = f"{SUPABASE_URL}/rest/v1/precios_mercadona"
        data  = json.dumps(lote).encode()
        req   = urllib.request.Request(url, data=data, headers=HEADERS_SB, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30):
                ok += len(lote)
        except urllib.error.HTTPError as e:
            err += len(lote)
            if n == 1:
                print(f"  ❌ Error {e.code}: {e.read().decode()[:200]}")
                return ok, err
        print(f"  Lote {n}/{total} — OK: {ok}", end="\r")

    print()
    return ok, err


def main():
    print("=" * 55)
    print("  🛒 SCRAPER MERCADONA v2 — API oficial")
    print("=" * 55)

    todos = scraping()

    if not todos:
        print("\n❌ No se obtuvieron productos"); return

    con_pu = sum(1 for p in todos if p.get("precio_unidad"))
    print(f"\n{'='*55}")
    print(f"  TOTAL productos:    {len(todos)}")
    print(f"  Con precio_unidad:  {con_pu} ({con_pu/len(todos)*100:.1f}%)")
    print(f"  Sin precio_unidad:  {len(todos)-con_pu}")

    # Muestra de precio_unidad
    print(f"\n  Ejemplos precio_unidad:")
    for p in [x for x in todos if x.get("precio_unidad")][:5]:
        print(f"    {p['nombre_comercial'][:40]:40} {p['precio']}€ → {p['precio_unidad']}")

    guardar_csv(todos)

    print("\n¿Qué hacemos?")
    print("  1. Solo guardar CSV")
    print("  2. CSV + actualizar Supabase (precios_mercadona)")
    modo = input("Opción (1/2): ").strip()

    if modo == "2":
        if not SUPABASE_KEY:
            print("❌ SUPABASE_KEY no encontrada"); return
        print(f"\n🔄 Actualizando Supabase...")
        ok, err = subir_supabase(todos)
        print(f"  ✅ OK: {ok} | ❌ Errores: {err}")

    print("\n✅ Completado.")


if __name__ == "__main__":
    main()
