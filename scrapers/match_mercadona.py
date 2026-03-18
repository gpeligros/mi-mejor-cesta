"""
match_mercadona.py  —  Mi Mejor Cesta
======================================
Vincula productos_catalogo (CAT-xxxx) con precios_mercadona (ME-xxxx)
usando similitud de nombres (rapidfuzz).

Resultado: rellena productos_match.id_mercadona

Uso:
  cd scrapers
  python match_mercadona.py
"""

import os, sys, json, urllib.request
from pathlib import Path
from rapidfuzz import process, fuzz

# ── Credenciales desde .env en la raíz ────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SCORE_MIN    = 75   # umbral mínimo 0-100

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY no encontrada en .env")
    sys.exit(1)

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=minimal",
}

def fetch_all(tabla, columnas):
    rows, offset = [], 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/{tabla}?select={columnas}&offset={offset}&limit=1000"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            lote = json.loads(resp.read())
            rows.extend(lote)
            if len(lote) < 1000:
                break
            offset += 1000
    print(f"  {tabla}: {len(rows)} filas")
    return rows

def hacer_matching(catalogo, mercadona):
    merc_index = {p["nombre_comercial"].lower(): p["id"] for p in mercadona}
    merc_lista = list(merc_index.keys())
    matches, sin_match = [], 0

    for prod in catalogo:
        resultado = process.extractOne(
            prod["nombre_generico"].lower(),
            merc_lista,
            scorer=fuzz.WRatio,
            score_cutoff=SCORE_MIN
        )
        if resultado:
            merc_nombre, score, _ = resultado
            matches.append({
                "cat_id":      prod["id"],
                "merc_id":     merc_index[merc_nombre],
                "score":       score,
                "cat_nombre":  prod["nombre_generico"],
                "merc_nombre": merc_nombre,
            })
        else:
            sin_match += 1

    return matches, sin_match

def subir_matches(matches):
    ok = err = 0
    for i, m in enumerate(matches):
        url = f"{SUPABASE_URL}/rest/v1/productos_match?id_catalogo=eq.{m['cat_id']}"
        req = urllib.request.Request(
            url,
            data=json.dumps({"id_mercadona": m["merc_id"]}).encode(),
            headers=HEADERS, method="PATCH"
        )
        try:
            with urllib.request.urlopen(req, timeout=15): ok += 1
        except: err += 1
        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(matches)} procesados...")
    return ok, err

def main():
    print("=" * 55)
    print("  🔗 MATCH MERCADONA — Mi Mejor Cesta")
    print("=" * 55)

    print("\n📥 Descargando tablas...")
    catalogo  = fetch_all("productos_catalogo", "id,nombre_generico")
    mercadona = fetch_all("precios_mercadona",  "id,nombre_comercial")

    print(f"\n🔍 Matching (umbral: {SCORE_MIN})...")
    matches, sin_match = hacer_matching(catalogo, mercadona)
    print(f"  ✅ Matches encontrados: {len(matches)}")
    print(f"  ❌ Sin match:           {sin_match}")

    if not matches:
        print("\nNada que subir."); return

    print("\n📋 Top 20 mejores matches:")
    for m in sorted(matches, key=lambda x: x["score"], reverse=True)[:20]:
        print(f"  [{m['score']:5.1f}] {m['cat_id']} | {m['cat_nombre'][:40]:<40} → {m['merc_nombre'][:40]}")

    bajos = [m for m in matches if m["score"] < 80]
    if bajos:
        print(f"\n⚠️  20 matches con score más bajo ({SCORE_MIN}-80):")
        for m in sorted(bajos, key=lambda x: x["score"])[:20]:
            print(f"  [{m['score']:5.1f}] {m['cat_id']} | {m['cat_nombre'][:40]:<40} → {m['merc_nombre'][:40]}")

    print(f"\n¿Subir {len(matches)} matches a productos_match.id_mercadona? (s/n): ", end="")
    if input().strip().lower() != "s":
        print("Cancelado."); return

    print(f"\n📤 Subiendo matches...")
    ok, err = subir_matches(matches)
    print(f"  ✅ OK: {ok} | ❌ Errores: {err}")

    print("\n📊 Verificación final:")
    rows = fetch_all("productos_match", "id_catalogo,id_mercadona")
    con  = sum(1 for r in rows if r.get("id_mercadona"))
    print(f"  Con Mercadona: {con} ({con/len(rows)*100:.1f}%)")
    print(f"  Sin Mercadona: {len(rows)-con}")
    print("\n✅ Completado.")

if __name__ == "__main__":
    main()
