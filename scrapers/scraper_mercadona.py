"""
scraper_mercadona.py  —  Mi Mejor Cesta
=======================================
Descarga todos los productos de la API oficial de Mercadona
y los guarda en precios_mercadona (Supabase) + CSV de backup.

Esquema de precios_mercadona:
  id           → ME-xxxx  (generado por nosotros)
  id_api       → ID numérico original de la API de Mercadona
  nombre_comercial, precio, precio_unidad, marca, url, imagen, disponible, actualizado
  ean          → código EAN/GTIN del producto (Fase 3)

Uso:
  cd scrapers
  python scraper_mercadona.py
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
DELAY        = 0.3  # segundos entre llamadas a la API

# ── Configuración ──────────────────────────────────────────────────────────────
API_BASE    = "https://tienda.mercadona.es/api"
OUTPUT_CSV  = f"mercadona_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
TABLA_SB    = "precios_mercadona"
PREFIJO_ID  = "ME"

HEADERS_API = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
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

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE DESCARGA
# ══════════════════════════════════════════════════════════════════════════════

def api_get(url):
    """Llama a la API de Mercadona y devuelve JSON o None."""
    try:
        r = requests.get(url, headers=HEADERS_API, timeout=15)
        if r.status_code == 200:
            return r.json()
        print(f"  ⚠️  HTTP {r.status_code} → {url}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    return None


def calcular_precio_unidad(pi):
    """
    Calcula precio por unidad/litro/kg desde price_instructions.
    Ejemplos: '2.94€/L', '0.97€/ud', '0.97€/ud · 2.94€/L'
    """
    if not pi:
        return None
    try:
        unit_price = float(pi.get("unit_price") or pi.get("bulk_price") or 0)
        unit_size  = float(pi.get("unit_size") or 0)
        unit_name  = (pi.get("unit_name") or "").lower()
        is_pack    = bool(pi.get("is_pack"))
        pack_size  = float(pi.get("pack_size") or 1)
    except:
        return None

    if unit_price <= 0:
        return None

    precio_ud = round(unit_price / pack_size, 2) if is_pack and pack_size > 1 else unit_price

    if unit_size > 0 and unit_name in ('l', 'kg', 'litros', 'kilos'):
        total     = unit_size * (pack_size if is_pack else 1)
        p_base    = round(unit_price / total, 2)
        base      = "L" if "l" in unit_name else "kg"
        if is_pack and pack_size > 1:
            return f"{precio_ud}€/ud · {p_base}€/{base}"
        return f"{p_base}€/{base}"
    elif is_pack and pack_size > 1:
        return f"{precio_ud}€/ud"
    return None


def extraer_ean(item):
    """
    Extrae el EAN/GTIN del producto desde la respuesta de la API de Mercadona.
    La API puede devolver el EAN en distintos campos según la versión.
    """
    # Campo directo más habitual
    ean = item.get("ean") or item.get("ean13") or item.get("gtin")
    if ean:
        return str(ean).strip()

    # A veces está en details o en legal
    details = item.get("details") or {}
    if isinstance(details, dict):
        ean = details.get("ean") or details.get("ean13")
        if ean:
            return str(ean).strip()

    # A veces en price_instructions
    pi = item.get("price_instructions") or {}
    ean = pi.get("ean") or pi.get("ean13")
    if ean:
        return str(ean).strip()

    return None


def parsear_producto(item):
    """Transforma un item de la API al formato de precios_mercadona."""
    nombre = (item.get("display_name") or "").strip()
    if not nombre:
        return None

    pi    = item.get("price_instructions") or {}
    try:
        precio = float(pi.get("unit_price") or pi.get("bulk_price") or 0)
    except:
        precio = 0

    # reference_price: precio por unidad de medida (€/L, €/kg) — disponible en objeto resumido
    try:
        ref_price = float(pi.get("reference_price") or 0) or None
    except:
        ref_price = None

    # reference_format: unidad de medida ("L", "kg", "ud") — disponible en objeto resumido
    ref_format = (pi.get("reference_format") or "").strip() or None

    id_api = str(item.get("id") or "")
    url    = item.get("share_url") or f"https://tienda.mercadona.es/product/{id_api}"

    return {
        "id_api":            id_api,
        "nombre_comercial":  nombre,
        "precio":            round(precio, 2) if precio else None,
        "precio_unidad":     calcular_precio_unidad(pi),
        "marca":             None,  # Mercadona no devuelve marca en objeto resumido
        "url":               url,
        "imagen":            item.get("thumbnail") or "",
        "disponible":        True,
        "ean":               extraer_ean(item),
        "reference_price":   ref_price,   # ← precio €/L o €/kg
        "reference_format":  ref_format,  # ← "L", "kg", "ud"...
    }


def descargar_productos():
    """Descarga todos los productos de Mercadona recorriendo el árbol de categorías."""
    print("📂 Obteniendo árbol de categorías...")
    data = api_get(f"{API_BASE}/categories/?lang=es")
    if not data:
        print("❌ No se pudo obtener categorías")
        return []

    categorias = data.get("results", [])
    print(f"  {len(categorias)} categorías principales\n")

    productos = []
    vistos    = set()

    for cat in categorias:
        cat_nombre = cat.get("name", "")
        subcats    = cat.get("categories", [])
        print(f"📂 {cat_nombre} ({len(subcats)} subcategorías)")

        for subcat in subcats:
            sub_id     = subcat.get("id")
            sub_nombre = subcat.get("name", "")
            data_sub   = api_get(f"{API_BASE}/categories/{sub_id}/?lang=es")
            if not data_sub:
                continue

            # Recoger productos de este nivel y sub-niveles
            items_raw = []
            for key in ("products", "result", "items"):
                if isinstance(data_sub.get(key), list):
                    items_raw.extend(data_sub[key])
            for sub2 in data_sub.get("categories", []):
                items_raw.extend(sub2.get("products", []))

            nuevos = 0
            for item in items_raw:
                p = parsear_producto(item)
                if p and p["id_api"] and p["id_api"] not in vistos:
                    vistos.add(p["id_api"])
                    productos.append(p)
                    nuevos += 1

            if nuevos:
                print(f"  └─ {sub_nombre}: {nuevos} productos")
            time.sleep(DELAY)

    return productos


# ══════════════════════════════════════════════════════════════════════════════
# GENERACIÓN DE IDs  ME-xxxx
# ══════════════════════════════════════════════════════════════════════════════

def obtener_ultimo_id():
    """Obtiene el último ME-xxxx usado en Supabase para continuar la numeración."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{TABLA_SB}?select=id&order=id.desc&limit=1"
        req = urllib.request.Request(url, headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data:
                ultimo = data[0]["id"]  # "ME-1234"
                numero = int(ultimo.split("-")[1])
                return numero
    except:
        pass
    return 0


def asignar_ids(productos):
    """
    Asigna ME-xxxx a productos nuevos.
    Si el producto ya existe en Supabase (mismo id_api), mantiene su ME-xxxx.
    Si es nuevo, asigna el siguiente número disponible.
    """
    print("🔢 Obteniendo IDs existentes en Supabase...")
    try:
        url    = f"{SUPABASE_URL}/rest/v1/{TABLA_SB}?select=id,id_api"
        req    = urllib.request.Request(url, headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        })
        pages, offset = [], 0
        while True:
            paged_url = url + f"&offset={offset}&limit=1000"
            req = urllib.request.Request(paged_url, headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                lote = json.loads(resp.read())
                pages.extend(lote)
                if len(lote) < 1000:
                    break
                offset += 1000

        # Mapa id_api → ME-xxxx existente
        mapa_existente = {r["id_api"]: r["id"] for r in pages if r.get("id_api")}
        ultimo_num     = max((int(r["id"].split("-")[1]) for r in pages if r.get("id")), default=0)
        print(f"  {len(mapa_existente)} productos existentes | último ID: {PREFIJO_ID}-{ultimo_num:04d}")
    except Exception as e:
        print(f"  ⚠️  No se pudieron obtener IDs existentes: {e}")
        mapa_existente = {}
        ultimo_num     = 0

    contador = ultimo_num
    for p in productos:
        if p["id_api"] in mapa_existente:
            p["id"] = mapa_existente[p["id_api"]]  # mantener ID existente
        else:
            contador += 1
            p["id"] = f"{PREFIJO_ID}-{contador:04d}"

    nuevos    = sum(1 for p in productos if p["id"] not in mapa_existente.values())
    existentes = len(productos) - nuevos
    print(f"  Nuevos: {nuevos} | Actualizaciones: {existentes}")
    return productos


# ══════════════════════════════════════════════════════════════════════════════
# GUARDAR CSV
# ══════════════════════════════════════════════════════════════════════════════

def guardar_csv(productos):
    campos = ["id", "id_api", "nombre_comercial", "precio", "precio_unidad",
              "marca", "url", "imagen", "disponible", "ean",
              "reference_price", "reference_format"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=campos, extrasaction="ignore").writeheader()
        csv.DictWriter(f, fieldnames=campos, extrasaction="ignore").writerows(productos)
    print(f"  📄 CSV: {OUTPUT_CSV}")


# ══════════════════════════════════════════════════════════════════════════════
# SUBIR A SUPABASE
# ══════════════════════════════════════════════════════════════════════════════

def subir_supabase(productos):
    """Sube/actualiza precios_mercadona usando id_api como clave de upsert."""
    campos = ["id", "id_api", "nombre_comercial", "precio", "precio_unidad",
              "marca", "url", "imagen", "disponible", "ean",
              "reference_price", "reference_format"]
    HEADERS_SB["Prefer"] = "resolution=merge-duplicates,return=minimal"

    ok = err = 0
    BATCH = 50
    total_lotes = (len(productos) + BATCH - 1) // BATCH

    for i in range(0, len(productos), BATCH):
        lote  = [{k: p.get(k) for k in campos} for p in productos[i:i+BATCH]]
        # Añadir timestamp
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
                msg = e.read().decode()[:300]
                print(f"  ❌ Error HTTP {e.code}: {msg}")
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
    print("  🛒 SCRAPER MERCADONA — Mi Mejor Cesta")
    print("=" * 55)

    if not SUPABASE_KEY:
        print("❌ SUPABASE_KEY no encontrada en .env")
        return

    # 1. Descargar
    productos = descargar_productos()
    if not productos:
        print("❌ No se obtuvieron productos")
        return

    con_pu      = sum(1 for p in productos if p.get("precio_unidad"))
    con_ean     = sum(1 for p in productos if p.get("ean"))
    con_ref     = sum(1 for p in productos if p.get("reference_price"))
    print(f"\n{'='*55}")
    print(f"  Total descargados:    {len(productos)}")
    print(f"  Con precio_unidad:    {con_pu} ({con_pu/len(productos)*100:.1f}%)")
    print(f"  Con EAN:              {con_ean} ({con_ean/len(productos)*100:.1f}%)")
    print(f"  Con reference_price:  {con_ref} ({con_ref/len(productos)*100:.1f}%)")

    # 2. Asignar IDs ME-xxxx
    productos = asignar_ids(productos)

    # 3. Guardar CSV (siempre)
    guardar_csv(productos)

    # 4. Preguntar si subir a Supabase
    print(f"\n¿Subir {len(productos)} productos a Supabase? (s/n): ", end="")
    if input().strip().lower() != "s":
        print("Cancelado. El CSV queda guardado.")
        return

    print(f"\n🔄 Subiendo a {TABLA_SB}...")
    ok, err = subir_supabase(productos)
    print(f"  ✅ OK: {ok} | ❌ Errores: {err}")

    # 5. Verificación final
    try:
        url    = f"{SUPABASE_URL}/rest/v1/{TABLA_SB}?select=id&limit=1"
        req    = urllib.request.Request(url, headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Prefer": "count=exact",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            count = resp.headers.get("Content-Range", "").split("/")[-1]
            print(f"\n📊 Total en Supabase: {count} productos")
    except:
        pass

    print("\n✅ Completado.")


if __name__ == "__main__":
    main()
