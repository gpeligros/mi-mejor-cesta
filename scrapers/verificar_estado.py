"""
verificar_estado.py - Mi Mejor Cesta
====================================
Imprime un resumen del estado actual de la BBDD: cuantos productos
hay en cada tabla de precios y cuantos matches hay rellenos en
productos_match. Util para saber si hay que ejecutar algun matching.

Uso desde la raiz del proyecto (con .env cargado):
    python scrapers/verificar_estado.py
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_KEY no encontrada en .env")
    exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("  Mi Mejor Cesta - Estado de la BBDD")
print("=" * 60)

# Total productos catalogo
try:
    r = sb.table("productos_catalogo").select("id", count="exact").limit(1).execute()
    print(f"\nTotal productos_catalogo: {r.count}")
except Exception as e:
    print(f"productos_catalogo: ERROR {e}")

# Precios por supermercado
print("\nPRECIOS POR SUPERMERCADO:")
print("-" * 40)
for tabla in ["precios_mercadona", "precios_dia", "precios_alcampo",
              "precios_carrefour", "precios_ahorramas", "precios_hipercor",
              "precios_lidl", "precios_eroski", "precios_despensa"]:
    try:
        r = sb.table(tabla).select("id", count="exact").limit(1).execute()
        marca = "OK" if r.count > 0 else "vacia"
        print(f"  {tabla:25s} {r.count:>8,} ({marca})")
    except Exception as e:
        print(f"  {tabla:25s} ERROR  ({str(e)[:40]})")

# Matches por columna
print("\nMATCHES EN productos_match:")
print("-" * 40)
columnas = ["id_mercadona", "id_dia", "id_alcampo", "id_carrefour",
            "id_ahorramas", "id_hipercor"]
total_cat = 0
try:
    rt = sb.table("productos_catalogo").select("id", count="exact").limit(1).execute()
    total_cat = rt.count or 1
except Exception:
    total_cat = 1

for col in columnas:
    try:
        r = sb.table("productos_match").select(col, count="exact").not_.is_(col, "null").limit(1).execute()
        pct = (r.count / total_cat * 100) if total_cat else 0
        print(f"  productos_match.{col:15s} {r.count:>5,} ({pct:5.1f}% del catalogo)")
    except Exception as e:
        print(f"  productos_match.{col:15s} ERROR  ({str(e)[:40]})")

print("\n" + "=" * 60)
print("  Acciones recomendadas")
print("=" * 60)

acciones = []

# Carrefour: si hay precios pero pocos matches -> matching
try:
    rp = sb.table("precios_carrefour").select("id", count="exact").limit(1).execute()
    rm = sb.table("productos_match").select("id_carrefour", count="exact").not_.is_("id_carrefour", "null").limit(1).execute()
    if (rp.count or 0) > 100 and (rm.count or 0) < 200:
        acciones.append(f"  -> python scrapers/match_carrefour.py --dry-run")
        acciones.append(f"     (luego sin --dry-run cuando los dudosos esten OK)")
except Exception:
    pass

# Ahorramas
try:
    rp = sb.table("precios_ahorramas").select("id", count="exact").limit(1).execute()
    rm = sb.table("productos_match").select("id_ahorramas", count="exact").not_.is_("id_ahorramas", "null").limit(1).execute()
    if (rp.count or 0) > 100 and (rm.count or 0) < 200:
        acciones.append(f"  -> python scrapers/match_ahorramas.py --dry-run")
except Exception:
    pass

# Hipercor: si la columna id_hipercor no existe, indicarlo
try:
    rp = sb.table("precios_hipercor").select("id", count="exact").limit(1).execute()
    if (rp.count or 0) == 0:
        acciones.append(f"  -> python scrapers/scraper_hipercor.py   (no hay datos aun)")
    else:
        try:
            rm = sb.table("productos_match").select("id_hipercor", count="exact").not_.is_("id_hipercor", "null").limit(1).execute()
            if (rm.count or 0) < 200:
                acciones.append(f"  -> python scrapers/match_hipercor.py --dry-run")
        except Exception:
            acciones.append(f"  -> ALTER TABLE productos_match ADD COLUMN id_hipercor TEXT;")
            acciones.append(f"     y luego: python scrapers/match_hipercor.py --dry-run")
except Exception:
    acciones.append(f"  -> Verificar tabla precios_hipercor (no existe o error)")

if acciones:
    for a in acciones:
        print(a)
else:
    print("  Todo en orden - no hay acciones criticas pendientes.")

print()
