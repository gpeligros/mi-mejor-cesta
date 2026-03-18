"""
aplicar_matches_revisados.py
Lee matches_revisar.csv, filtra los buenos automáticamente
y los aplica a Supabase.

Criterio automático: mismo producto = 2+ palabras clave en común
Los dudosos se guardan en matches_dudosos.csv para revisión manual.
"""

import csv
import json
import urllib.request
import urllib.error
import unicodedata

# ── CONFIGURACIÓN ─────────────────────────────────────────────
SUPABASE_URL = "https://scpuriaofisssalsbzqv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcHVyaWFvZmlzc3NhbHNienF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjgwNDksImV4cCI6MjA4NTkwNDA0OX0.oMYR_aV0SgMplBURwSESe8kLCWTl4QfQyOXsDfmBRfo"
CSV_INPUT    = "matches_revisar.csv"
# ─────────────────────────────────────────────────────────────

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=minimal",
}

# Palabras que NO cuentan como clave (son de formato/marca/cantidad)
STOP_WORDS = {
    'hacendado', 'dia', 'carrefour', 'lidl', 'aldi', 'pack', 'botella',
    'brik', 'lata', 'bote', 'bolsa', 'caja', 'sobre', 'tarro',
    'con', 'sin', 'para', 'del', 'los', 'las', 'una', 'unos', 'unas',
    'extra', 'light', 'zero', 'bio', 'ecologico', 'natural', 'clasico',
}


def normalizar(texto):
    t = texto.lower().strip()
    t = ''.join(c for c in unicodedata.normalize('NFD', t)
                if unicodedata.category(c) != 'Mn')
    return t


def palabras_clave(nombre):
    norm = normalizar(nombre)
    return [w for w in norm.split() if len(w) > 3 and w not in STOP_WORDS]


def es_buen_match(nombre_dia, nombre_mercadona):
    """True si comparten 2+ palabras clave"""
    pk_dia  = set(palabras_clave(nombre_dia))
    pk_merc = set(palabras_clave(nombre_mercadona))
    return len(pk_dia & pk_merc) >= 2


def patch_supabase(id_dia, id_maestro):
    url  = f"{SUPABASE_URL}/rest/v1/productos_supermercados?id=eq.{id_dia}"
    data = json.dumps({"id_producto_maestro": id_maestro}).encode()
    req  = urllib.request.Request(url, data=data, headers=HEADERS, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    print("=" * 55)
    print("  APLICAR MATCHES REVISADOS → SUPABASE")
    print("=" * 55)

    if "PEGA_AQUI" in SUPABASE_KEY:
        print("❌ Falta la SUPABASE_KEY")
        input("ENTER..."); return

    # Leer CSV
    try:
        with open(CSV_INPUT, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"❌ No se encontró {CSV_INPUT}")
        input("ENTER..."); return

    print(f"\n📄 {len(rows)} matches en el CSV")

    # Clasificar
    buenos  = []
    dudosos = []
    for r in rows:
        if es_buen_match(r['nombre_dia'], r['nombre_mercadona']):
            buenos.append(r)
        else:
            dudosos.append(r)

    print(f"✅ Buenos (2+ palabras clave):  {len(buenos)}")
    print(f"⚠️  Dudosos (revisar manual):    {len(dudosos)}")

    print(f"\nEjemplos de buenos matches:")
    for r in buenos[:6]:
        print(f"  {r['score'][:5]} | {r['nombre_dia'][:38]:38} → {r['nombre_mercadona'][:38]}")

    print(f"\n¿Aplicar los {len(buenos)} buenos matches? (s/n): ", end="")
    if input().strip().lower() != 's':
        print("Cancelado.")
        return

    # Aplicar
    ok = 0
    for i, r in enumerate(buenos):
        status = patch_supabase(r['id_dia'], r['id_maestro'])
        if status in (200, 204):
            ok += 1
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(buenos)} aplicados...")

    print(f"\n✅ {ok}/{len(buenos)} matches aplicados")

    # Guardar dudosos
    if dudosos:
        with open('matches_dudosos.csv', 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(sorted(dudosos, key=lambda x: -float(x['score'])))
        print(f"📄 {len(dudosos)} dudosos guardados en matches_dudosos.csv")

    print("\n✅ Hecho. Reinicia la app para ver los cambios.")
    input("ENTER para salir...")


if __name__ == "__main__":
    main()
