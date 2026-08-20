"""
subir_backup_dia.py — Mi Mejor Cesta
======================================
Sube a Supabase un backup local generado por scraper_dia.py (el JSON que
se guarda antes de intentar subir, para no perder el scrape si falla la
subida). Evita repetir el scrape completo (~15 min) por un fallo de subida.

USO:
  python scrapers/subir_backup_dia.py backup_dia_20260810_2123.json
"""
import json
import os
import sys
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
TABLE_NAME = "precios_dia"
PREFIJO_ID = "DI"


def assign_ids(products, id_map):
    ultimo_num = max(
        (int(v.split("-")[1]) for v in id_map.values()
         if "-" in v and v.split("-")[1].isdigit()),
        default=0,
    )
    contador = ultimo_num
    resultado = []
    vistos = set()
    for p in products:
        key = p["id_api"]
        if not key or key in vistos:
            continue
        vistos.add(key)
        if key in id_map:
            p["id"] = id_map[key]
        else:
            contador += 1
            p["id"] = f"{PREFIJO_ID}-{contador:04d}"
        resultado.append(p)
    return resultado


def upsert(client, products):
    now = datetime.datetime.now(datetime.UTC).isoformat()
    for p in products:
        p["actualizado"] = now
    if not products:
        return 0
    res = client.table(TABLE_NAME).upsert(products, on_conflict="id_api").execute()
    return len(res.data) if res.data else len(products)


def main():
    if len(sys.argv) < 2:
        print("Uso: python subir_backup_dia.py <ruta_backup.json>")
        return
    ruta = sys.argv[1]
    if not Path(ruta).exists():
        print(f"ERROR: no existe {ruta}")
        return
    if not SUPABASE_KEY:
        print("ERROR: falta SUPABASE_KEY en .env")
        return

    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    with open(ruta, encoding="utf-8") as f:
        items = json.load(f)
    print(f"Cargados {len(items)} productos de {ruta}")

    existentes = []
    offset = 0
    while True:
        res = client.table(TABLE_NAME).select("id,id_api").range(offset, offset + 999).execute()
        existentes.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    id_map = {r["id_api"]: r["id"] for r in existentes if r.get("id_api")}
    print(f"{len(id_map)} IDs existentes en Supabase")

    productos_con_id = assign_ids(items, id_map)

    total_ok = 0
    for i in range(0, len(productos_con_id), 500):
        lote = productos_con_id[i:i + 500]
        subido = False
        for intento in range(3):
            try:
                total_ok += upsert(client, lote)
                subido = True
                break
            except Exception as e:
                print(f"  Error subiendo lote (intento {intento+1}/3): {e}")
                time.sleep(5 * (intento + 1))
        estado = "OK" if subido else "FALLÓ tras 3 intentos"
        print(f"  Lote {i}-{i+len(lote)}: {estado}  (total: {min(i+500, len(productos_con_id))}/{len(productos_con_id)})")

    print(f"\nTotal upserted: {total_ok}")


if __name__ == "__main__":
    main()
