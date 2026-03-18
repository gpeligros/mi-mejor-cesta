"""
aplicar_dudosos.py
Lee el CSV dia_sin_match_ia_*.csv (los 933 dudosos)
y los aplica directamente a Supabase sin IA.
Solo aplica los que tienen score >= 75.
"""

import json
import csv
import os
import glob
import urllib.request
import urllib.error

try:
    from dotenv import load_dotenv
    _raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(_raiz, '.env'))
except ImportError:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "PEGA_AQUI_TU_KEY")
UMBRAL = 75.0

HEADERS_SB = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=minimal",
}

def sb_patch(tabla, filtro, datos):
    url  = f"{SUPABASE_URL}/rest/v1/{tabla}?{filtro}"
    data = json.dumps(datos).encode()
    req  = urllib.request.Request(url, data=data, headers=HEADERS_SB, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:100]


def main():
    print("=" * 55)
    print("  APLICAR DUDOSOS (umbral ≥75%)")
    print("=" * 55)

    # Buscar el CSV más reciente de dudosos
    carpeta = os.path.dirname(os.path.abspath(__file__))
    csvs = sorted(glob.glob(os.path.join(carpeta, "dia_sin_match_ia_*.csv")), reverse=True)

    if not csvs:
        print("❌ No se encontró dia_sin_match_ia_*.csv")
        return

    csv_path = csvs[0]
    print(f"\n📄 Usando: {os.path.basename(csv_path)}")

    with open(csv_path, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    print(f"   Total filas: {len(rows)}")

    # Filtrar por umbral
    aplicar = [r for r in rows if float(r.get('score', 0)) >= UMBRAL]
    saltar  = [r for r in rows if float(r.get('score', 0)) < UMBRAL]

    print(f"   Con score ≥{UMBRAL}%: {len(aplicar)}")
    print(f"   Con score <{UMBRAL}%: {len(saltar)} (se ignoran)")

    # Mostrar muestra
    print(f"\n  Ejemplos que se van a aplicar:")
    for r in aplicar[:8]:
        print(f"    {r['score']:>5}% | {r['nombre_dia'][:35]:35} → {r['nombre_catalogo'][:35]}")

    if not aplicar:
        print("\n  No hay matches que aplicar.")
        return

    confirmar = input(f"\n  ¿Aplicar {len(aplicar)} matches? (s/n): ").strip().lower()
    if confirmar != 's':
        print("  Cancelado.")
        return

    ok = 0
    errores = 0
    for i, r in enumerate(aplicar):
        status, err = sb_patch(
            "productos_match",
            f"id_catalogo=eq.{r['id_catalogo']}",
            {"id_dia": str(r['id_dia'])}
        )
        if status in (200, 204):
            ok += 1
        else:
            errores += 1
            if errores <= 3:
                print(f"  ⚠️  Error {status}: {err}")

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(aplicar)}...", end="\r")

    print(f"\n  ✅ Aplicados: {ok}")
    print(f"  ❌ Errores:   {errores}")
    print("\n✅ Listo.")


if __name__ == "__main__":
    main()
