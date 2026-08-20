"""
exportar_todos_precios.py — Mi Mejor Cesta
============================================
Descarga TODAS las tablas de precios (los 5 supermercados activos) a CSV,
paginando de mil en mil filas — igual que backup_catalogo.py, pero para
las 5 tablas precios_* de una sola vez.

Necesario porque el "Download CSV" del SQL Editor de Supabase solo exporta
la vista previa (~100 filas), no la tabla entera.

Es la FASE 1 de la reconstrucción completa del catálogo: extracción de
datos, solo lectura, sin ningún riesgo para la BBDD.

USO:
  python scrapers/exportar_todos_precios.py

SALIDA:
  old/export_precios_mercadona_<fecha>.csv
  old/export_precios_dia_<fecha>.csv
  old/export_precios_alcampo_<fecha>.csv
  old/export_precios_carrefour_<fecha>.csv
  old/export_precios_ahorramas_<fecha>.csv

REQUISITOS:
  - pip install supabase python-dotenv
  - .env con SUPABASE_URL y SUPABASE_KEY (service_role recomendada)
"""

import csv
import os
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

TABLAS = [
    "precios_mercadona",
    "precios_dia",
    "precios_alcampo",
    "precios_carrefour",
    "precios_ahorramas",
]

if not SUPABASE_KEY:
    print("ERROR: falta SUPABASE_KEY en el .env")
    raise SystemExit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def exportar_tabla(tabla, fecha, destino_dir):
    print(f"\n📥 Descargando '{tabla}' completa (paginando)...")
    filas, offset = [], 0
    while True:
        try:
            res = supabase.table(tabla).select("*").range(offset, offset + 999).execute()
        except Exception as e:
            print(f"  ❌ ERROR leyendo {tabla}: {e}")
            return 0
        lote = res.data
        filas.extend(lote)
        print(f"  {len(filas)} filas leídas...", end="\r")
        if len(lote) < 1000:
            break
        offset += 1000
    print(f"  {len(filas)} filas leídas... OK          ")

    if not filas:
        print(f"  ⚠️  '{tabla}' está vacía o no accesible. Se omite.")
        return 0

    columnas = list(filas[0].keys())
    for r in filas:
        for k in r:
            if k not in columnas:
                columnas.append(k)

    destino = destino_dir / f"export_{tabla}_{fecha}.csv"
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        for r in filas:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in columnas})

    print(f"  ✅ Guardado en: {destino}")
    return len(filas)


def main():
    print("=" * 60)
    print("  📦 EXPORTAR TODAS LAS TABLAS DE PRECIOS")
    print("  (Fase 1 — reconstrucción del catálogo)")
    print("=" * 60)

    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    destino_dir = Path(__file__).resolve().parents[1] / "old"
    destino_dir.mkdir(parents=True, exist_ok=True)

    resumen = {}
    for tabla in TABLAS:
        resumen[tabla] = exportar_tabla(tabla, fecha, destino_dir)

    print("\n" + "=" * 60)
    print("  RESUMEN")
    print("=" * 60)
    total = 0
    for tabla, n in resumen.items():
        print(f"  {tabla:25s} {n:>8,} filas")
        total += n
    print(f"  {'TOTAL':25s} {total:>8,} filas")
    print("\n✅ Completado. Todos los CSVs están en la carpeta old/.")
    print("   Siguiente paso: Fase 2 — normalización de nombres.")


if __name__ == "__main__":
    main()
