import os
from supabase import create_client
from rapidfuzz import process, fuzz

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://scpuriaofisssalsbzqv.supabase.co"
SUPABASE_KEY = "sb_publishable_NfUDh2hQ_5HiFqnL7MNCeA_7MTs4_Kb"  # ← reemplaza esto
SCORE_MIN    = 75   # umbral mínimo de similitud (0-100)
# ──────────────────────────────────────────────────────────────────────────────

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_all(table, columns):
    """Descarga todos los registros de una tabla paginando de 1000 en 1000."""
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
catalogo = fetch_all("productos_catalogo", "id, nombre_generico")
dia      = fetch_all("precios_dia",        "id, nombre_comercial")

# Índice DIA: {nombre_lower: id}
dia_nombres = {p["nombre_comercial"].lower(): p["id"] for p in dia}
dia_lista   = list(dia_nombres.keys())

print(f"\n🔍 Haciendo matching (umbral: {SCORE_MIN})...")
matches = []   # [(cat_id, dia_id, score)]
sin_match = 0

for prod in catalogo:
    cat_id  = prod["id"]
    nombre  = prod["nombre_generico"].lower()

    # WORD_SIMILARITY equivalente: partial_ratio mide si el nombre corto
    # aparece dentro del nombre largo — exactamente lo que necesitamos
    result = process.extractOne(
        nombre,
        dia_lista,
        scorer=fuzz.WRatio,
        score_cutoff=SCORE_MIN
    )

    if result:
        dia_nombre, score, _ = result
        dia_id = dia_nombres[dia_nombre]
        matches.append((cat_id, dia_id, score))
    else:
        sin_match += 1

print(f"  ✅ Matches encontrados: {len(matches)}")
print(f"  ❌ Sin match:           {sin_match}")

# ─── Preview top 20 ───────────────────────────────────────────────────────────
dia_lookup = {p["id"]: p["nombre_comercial"] for p in dia}
cat_lookup = {p["id"]: p["nombre_generico"]  for p in catalogo}

print("\n📋 Preview top 20 matches (ordenados por score desc):")
top20 = sorted(matches, key=lambda x: x[2], reverse=True)[:20]
for cat_id, dia_id, score in top20:
    print(f"  [{score:5.1f}] {cat_id} | {cat_lookup[cat_id][:45]:<45} --> {dia_lookup[dia_id][:45]}")

# ─── Preview matches bajos (zona de riesgo) ───────────────────────────────────
print(f"\n⚠️  Preview 20 matches con score más bajo ({SCORE_MIN}-80):")
low = sorted([m for m in matches if m[2] < 80], key=lambda x: x[2])[:20]
for cat_id, dia_id, score in low:
    print(f"  [{score:5.1f}] {cat_id} | {cat_lookup[cat_id][:45]:<45} --> {dia_lookup[dia_id][:45]}")

# ─── Confirmar antes de subir ─────────────────────────────────────────────────
print(f"\n¿Subir {len(matches)} matches a productos_match? (s/n): ", end="")
confirm = input().strip().lower()
if confirm != "s":
    print("Cancelado.")
    exit()

print("\n📤 Subiendo matches a Supabase...")
ok, err = 0, 0
for i, (cat_id, dia_id, score) in enumerate(matches):
    try:
        supabase.table("productos_match")\
            .update({"id_dia": dia_id})\
            .eq("id_catalogo", cat_id)\
            .execute()
        ok += 1
    except Exception as e:
        print(f"  Error en {cat_id}: {e}")
        err += 1

    if (i + 1) % 500 == 0:
        print(f"  {i+1}/{len(matches)} procesados...")

print(f"\n✅ Completado: {ok} actualizados, {err} errores")

# ─── Verificación final ───────────────────────────────────────────────────────
res = supabase.table("productos_match").select("id_catalogo, id_dia").execute()
con_dia = sum(1 for r in res.data if r["id_dia"] is not None)
print(f"\n📊 Estado final productos_match:")
print(f"   Total filas:  {len(res.data)}")
print(f"   Con DIA:      {con_dia}")
print(f"   Sin DIA:      {len(res.data) - con_dia}")
