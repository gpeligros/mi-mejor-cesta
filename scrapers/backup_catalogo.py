"""
backup_catalogo.py  —  Mi Mejor Cesta
=====================================
Descarga la tabla productos_catalogo COMPLETA a un CSV, paginando de mil en mil.
Necesario porque el "Download CSV" del SQL Editor de Supabase solo exporta la
vista previa (~100 filas), no la tabla entera.

USO:
  python scrapers/backup_catalogo.py

SALIDA:
  old/backup_productos_catalogo_<fecha>.csv   (con TODAS las filas)

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
TABLA = "productos_catalogo"

if not SUPABASE_KEY:
    print("ERROR: falta SUPABASE_KEY en el .env")
    raise SystemExit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"Descargando '{TABLA}' completa (paginando)...")
filas, offset = [], 0
while True:
    res = supabase.table(TABLA).select("*").range(offset, offset + 999).execute()
    lote = res.data
    filas.extend(lote)
    print(f"  {len(filas)} filas leidas...")
    if len(lote) < 1000:
        break
    offset += 1000

if not filas:
    print("No se leyo ninguna fila. Revisa SUPABASE_KEY.")
    raise SystemExit(1)

# Columnas: preservamos el orden de la primera fila y añadimos las que falten
columnas = list(filas[0].keys())
for r in filas:
    for k in r:
        if k not in columnas:
            columnas.append(k)

fecha = datetime.now().strftime("%Y%m%d_%H%M")
destino = Path(__file__).resolve().parents[1] / "old" / f"backup_{TABLA}_{fecha}.csv"
destino.parent.mkdir(parents=True, exist_ok=True)

with open(destino, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=columnas)
    w.writeheader()
    for r in filas:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in columnas})

print(f"\nOK: {len(filas)} filas guardadas en:")
print(f"  {destino}")
print(f"\nComprueba que el numero de arriba es 10171 antes de seguir.")
