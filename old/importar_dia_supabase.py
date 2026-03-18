"""
importar_dia_supabase.py
Columnas reales de productos_supermercados:
id, supermercado, nombre_comercial, precio, precio_unidad,
marca, url, imagen, id_externo, disponible, actualizado, id_producto_maestro
"""

import csv
import json
import urllib.request
import urllib.error
import os
import sys

# ── CONFIGURACIÓN — pega tu key de supabaseClient.js ─────────
SUPABASE_URL = "https://scpuriaofisssalsbzqv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcHVyaWFvZmlzc3NhbHNienF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjgwNDksImV4cCI6MjA4NTkwNDA0OX0.oMYR_aV0SgMplBURwSESe8kLCWTl4QfQyOXsDfmBRfo"
BATCH_SIZE   = 50
# ─────────────────────────────────────────────────────────────


def buscar_csv():
    carpeta = os.path.dirname(os.path.abspath(__file__))
    for f in sorted(os.listdir(carpeta), reverse=True):
        if f.startswith("dia_productos") and f.endswith(".csv"):
            return os.path.join(carpeta, f)
    return None


def leer_csv(ruta):
    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(ruta, encoding=enc, newline="") as f:
                rows = list(csv.DictReader(f))
            print(f"CSV leido ({enc}): {len(rows)} filas")
            return rows
        except:
            continue
    return []


def preparar_fila(row):
    try:
        precio = float(row.get("precio", "") or 0)
    except:
        precio = None

    return {
        "supermercado":     row.get("supermercado", "DIA"),
        "nombre_comercial": row.get("nombre_comercial", "").strip(),
        "precio":           precio,
        "precio_unidad":    row.get("precio_por_unidad", "").strip() or None,
        "marca":            row.get("marca", "").strip() or None,
        "url":              row.get("url", "").strip() or None,
        "imagen":           row.get("imagen", "").strip() or None,
        "id_externo":       row.get("referencia_externa", "").strip() or None,
        "disponible":       True,
    }


def insertar(filas):
    url = f"{SUPABASE_URL}/rest/v1/productos_supermercados"
    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=merge-duplicates",
    }
    data = json.dumps(filas).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)


def main():
    print("=" * 50)
    print("  IMPORTAR DIA -> SUPABASE")
    print("=" * 50)

    ruta = buscar_csv()
    if not ruta:
        print("No se encontro CSV de DIA en esta carpeta")
        input("ENTER para salir...")
        sys.exit(1)

    print(f"\nCSV: {ruta}")
    rows  = leer_csv(ruta)
    filas = [preparar_fila(r) for r in rows if r.get("nombre_comercial", "").strip()]
    print(f"Productos: {len(filas)}")

    ok = 0
    for i in range(0, len(filas), BATCH_SIZE):
        lote   = filas[i:i + BATCH_SIZE]
        n      = i // BATCH_SIZE + 1
        total  = (len(filas) + BATCH_SIZE - 1) // BATCH_SIZE
        status, err = insertar(lote)

        if status in (200, 201):
            ok += len(lote)
            print(f"  OK Lote {n}/{total} - {ok}/{len(filas)}")
        else:
            print(f"  ERROR Lote {n} HTTP {status}: {err[:200]}")
            if n == 1:
                print("\nFallo en el primer lote - revisa la SUPABASE_KEY")
                input("ENTER para salir...")
                sys.exit(1)

    print(f"\nImportados: {ok}/{len(filas)}")
    input("ENTER para salir...")


if __name__ == "__main__":
    main()
