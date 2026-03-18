"""
match_mercadona.py
Matching Mercadona → productos_catalogo usando rapidfuzz.
Igual que match_dia.py pero para Mercadona.
Lee credenciales del .env en la raíz del proyecto.
"""
import os, sys
from pathlib import Path
from supabase import create_client
from rapidfuzz import process, fuzz

# ── Cargar .env desde la raíz ─────────────────────────────────────────────────
env_path = Path(__file__).resolve().parents[1] / '.env'
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SCORE_MIN    = 75

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY no encontrada en .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_all(table, columns):
    rows, offset = [], 0
    while True:
        res = supabase.table(table).select(columns).range(offset, offset + 999).execute()
        rows.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    print(f"  {table}: {len(rows)} filas")
    return rows

print("📥 Descargando tablas...")
catalogo  = fetch_all("productos_catalogo", "id, nombre_generico")
mercadona = fetch_all("precios_mercadona",  "id, nombre_comercial")

# Índice Mercadona: {nombre_lower: id}
merc_nombres = {p["nombre_comercial"].lower(): p["id"] for p in mercadona}
merc_lista   = list(merc_nombres.keys())

print(f"\n🔍 Haciendo matching (umbral: {SCORE_MIN})...")
matches   = []
sin_match = 0

for prod in catalogo:
    cat_id = prod["id"]
    nombre = prod["nombre_generico"].lower()

    result = process.extractOne(
        nombre,
        merc_lista,
        scorer=fuzz.WRatio,
        score_cutoff=SCORE_MIN
    )

    if result:
        merc_nombre, score, _ = result
        merc_id = merc_nombres[merc_nombre]
        matches.append((cat_id, merc_id, score))
    else:
        sin_match += 1

print(f"  ✅ Matches encontrados: {len(matches)}")
print(f"  ❌ Sin match:           {sin_match}")

# ── Preview ───────────────────────────────────────────────────────────────────
merc_lookup = {p["id"]: p["nombre_comercial"] for p in mercadona}
cat_lookup  = {p["id"]: p["nombre_generico"]  for p in catalogo}

print("\n📋 Preview top 20 matches:")
for cat_id, merc_id, score in sorted(matches, key=lambda x: x[2], reverse=True)[:20]:
    print(f"  [{score:5.1f}] {cat_id} | {cat_lookup[cat_id][:45]:<45} --> {merc_lookup[merc_id][:45]}")

print(f"\n⚠️  Preview 20 matches con score más bajo ({SCORE_MIN}-80):")
for cat_id, merc_id, score in sorted([m for m in matches if m[2] < 80], key=lambda x: x[2])[:20]:
    print(f"  [{score:5.1f}] {cat_id} | {cat_lookup[cat_id][:45]:<45} --> {merc_lookup[merc_id][:45]}")

# ── Confirmar ─────────────────────────────────────────────────────────────────
print(f"\n¿Subir {len(matches)} matches a productos_match? (s/n): ", end="")
if input().strip().lower() != "s":
    print("Cancelado.")
    sys.exit(0)

print("\n📤 Subiendo matches a Supabase...")
ok = err = 0
for i, (cat_id, merc_id, score) in enumerate(matches):
    try:
        supabase.table("productos_match")\
            .update({"id_mercadona": merc_id})\
            .eq("id_catalogo", cat_id)\
            .execute()
        ok += 1
    except Exception as e:
        print(f"  Error en {cat_id}: {e}")
        err += 1
    if (i + 1) % 500 == 0:
        print(f"  {i+1}/{len(matches)} procesados...")

print(f"\n✅ Completado: {ok} actualizados, {err} errores")

# ── Verificación final ────────────────────────────────────────────────────────
res      = fetch_all("productos_match", "id_catalogo,id_mercadona,id_dia")
con_merc = sum(1 for r in res if r["id_mercadona"])
con_dia  = sum(1 for r in res if r["id_dia"])
print(f"\n📊 Estado final productos_match:")
print(f"   Total:          {len(res)}")
print(f"   Con Mercadona:  {con_merc}")
print(f"   Con DIA:        {con_dia}")
print(f"   Sin Mercadona:  {len(res) - con_merc}")
print(f"   Sin DIA:        {len(res) - con_dia}")
