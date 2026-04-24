"""
agregar_carrefour_faltantes.py  —  Mi Mejor Cesta
=================================================
Agrega productos Carrefour que NO están en el catálogo.

Lógica:
1. Lee precios_carrefour (7.241 productos)
2. Lee productos_match (ve cuáles id_carrefour YA están vinculados)
3. Calcula faltantes: 7.241 - (los ya vinculados)
4. Para cada faltante:
   - Genera nuevo CAT-xxxx (numeración secuencial)
   - Extrae categoría de Carrefour
   - Mapea a categorias_maestras (87 categorías fijas)
   - Inserta en productos_catalogo
   - Vincula en productos_match con id_carrefour

Resultado: ~6.162 nuevos productos en el catálogo

Uso:
  python agregar_carrefour_faltantes.py --dry-run   # ver sin guardar
  python agregar_carrefour_faltantes.py             # guardar en BBDD
"""

import os
import sys
import json
import argparse
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY no encontrada en .env")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

# Mapeo simplificado Carrefour → categorias_maestras
# (Se puede refinar según necesidad)
MAPPING_CATEGORIAS = {
    "la-despensa": 1,           # La despensa
    "frescos": 2,               # Frescos
    "bebidas": 3,               # Bebidas
    "perfumeria-e-higiene": 4,  # Perfumería e higiene
    "drogueria-y-limpieza": 5,  # Droguería y limpieza
    "congelados": 6,            # Congelados
    "bebe": 7,                  # Bebé
    "mascotas": 8,              # Mascotas
    "parafarmacia": 9,          # Parafarmacia
}

def fetch_all(tabla, columnas):
    """Fetch all rows from Supabase"""
    rows, offset = [], 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/{tabla}?select={columnas}&offset={offset}&limit=1000"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                lote = json.loads(resp.read())
                rows.extend(lote)
                if len(lote) < 1000:
                    break
                offset += 1000
        except Exception as e:
            print(f"❌ Error fetching {tabla}: {e}")
            break
    return rows

def obtener_max_cat_number():
    """Obtener el número más alto de CAT-xxxx para continuar la numeración"""
    catalogo = fetch_all("productos_catalogo", "id")
    max_num = 0
    for prod in catalogo:
        try:
            num = int(prod["id"].split("-")[1])
            max_num = max(max_num, num)
        except:
            pass
    return max_num

def generar_cat_id(numero):
    """Generar ID como CAT-0001, CAT-0002, etc."""
    return f"CAT-{numero:04d}"

def mapear_categoria(nombre_carrefour):
    """Mapea categoría Carrefour a id de categorias_maestras"""
    if not nombre_carrefour:
        return 1  # Default: La despensa
    
    nombre_norm = nombre_carrefour.lower().replace("_", "-")
    
    for clave, id_cat in MAPPING_CATEGORIAS.items():
        if clave in nombre_norm:
            return id_cat
    
    return 1  # Default

def main(dry_run=False):
    print("=" * 60)
    print("  AGREGAR PRODUCTOS CARREFOUR FALTANTES AL CATÁLOGO")
    print("=" * 60)
    
    print("\n📥 Cargando datos...")
    carrefour = fetch_all("precios_carrefour", "id,nombre_comercial,marca")
    print(f"  precios_carrefour: {len(carrefour)} productos")
    
    matches = fetch_all("productos_match", "id_catalogo,id_carrefour")
    ya_tienen_cf = {m["id_carrefour"] for m in matches if m.get("id_carrefour")}
    print(f"  productos_match: {len(matches)} registros")
    print(f"  Con id_carrefour: {len(ya_tienen_cf)}")
    
    # Identificar faltantes
    faltantes = [p for p in carrefour if p["id"] not in ya_tienen_cf]
    print(f"\n🔍 Productos Carrefour SIN catálogo: {len(faltantes)}")
    
    if not faltantes:
        print("✅ Todos los productos Carrefour ya están en el catálogo.")
        return
    
    # Generar nuevos CAT-xxxx
    max_num = obtener_max_cat_number()
    print(f"   Numeración actual máxima: CAT-{max_num:04d}")
    print(f"   Comenzaremos en: CAT-{max_num+1:04d}")
    
    nuevos_productos = []
    nuevos_matches = []
    
    for i, cf in enumerate(faltantes, 1):
        cat_id = generar_cat_id(max_num + i)
        id_categoria = 1  # Default: La despensa (sin categoría en precios_carrefour)
        
        nuevos_productos.append({
            "id": cat_id,
            "nombre_generico": cf.get("nombre_comercial", "Producto Carrefour"),
            "marca": cf.get("marca", "Carrefour"),
            "id_categoria": id_categoria,
            "tipo": "marca_fabricante",
            "formato": None,
            "nombre_normalizado": (cf.get("nombre_comercial", "").lower()),
            "ean": None,
            "activo": True,
        })
        
        nuevos_matches.append({
            "id_catalogo": cat_id,
            "id_carrefour": cf["id"],
        })
        
        if i % 1000 == 0:
            print(f"   Preparados {i}/{len(faltantes)}...")
    
    print(f"\n✅ Preparados {len(nuevos_productos)} nuevos productos")
    
    # Vista previa
    print("\n📋 Primeros 5 nuevos productos:")
    for p in nuevos_productos[:5]:
        print(f"   {p['id']} | {p['nombre_generico'][:40]:<40} | {p['marca']}")
    
    if dry_run:
        print("\n[dry-run] No se guarda nada en BBDD.")
        return
    
    # Guardar en BBDD
    print(f"\n📤 Guardando en productos_catalogo...")
    guardados_cat = 0
    batch_size = 50
    
    for i in range(0, len(nuevos_productos), batch_size):
        batch = nuevos_productos[i:i + batch_size]
        try:
            url = f"{SUPABASE_URL}/rest/v1/productos_catalogo"
            data = json.dumps(batch).encode()
            req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
            with urllib.request.urlopen(req, timeout=30):
                guardados_cat += len(batch)
        except Exception as e:
            print(f"   ⚠️  Error en batch {i//batch_size}: {e}")
        
        if (i + batch_size) % 500 == 0:
            print(f"   {min(i + batch_size, len(nuevos_productos))}/{len(nuevos_productos)}...")
    
    print(f"  ✅ {guardados_cat} productos insertados en productos_catalogo")
    
    print(f"\n📤 Guardando matches en productos_match...")
    guardados_match = 0
    
    for i, m in enumerate(nuevos_matches):
        try:
            url = f"{SUPABASE_URL}/rest/v1/productos_match?id_catalogo=eq.{m['id_catalogo']}"
            data = json.dumps({"id_carrefour": m["id_carrefour"]}).encode()
            req = urllib.request.Request(url, data=data, headers=HEADERS, method="PATCH")
            with urllib.request.urlopen(req, timeout=15):
                guardados_match += 1
        except Exception as e:
            print(f"   ⚠️  Error vinculando {m['id_catalogo']}: {e}")
        
        if (i + 1) % 1000 == 0:
            print(f"   {i + 1}/{len(nuevos_matches)}...")
    
    print(f"  ✅ {guardados_match} matches vinculados en productos_match")
    
    # Verificación final
    print(f"\n📊 Verificación final:")
    catalogo_final = fetch_all("productos_catalogo", "id")
    matches_cf = fetch_all("productos_match", "id_catalogo,id_carrefour")
    matches_cf_count = sum(1 for m in matches_cf if m.get("id_carrefour"))
    
    print(f"  productos_catalogo: {len(catalogo_final)} (antes: 4009)")
    print(f"  productos_match con id_carrefour: {matches_cf_count} (antes: 1079)")
    print(f"\n✅ COMPLETADO. {len(nuevos_productos)} productos Carrefour agregados al catálogo.")
    print("=" * 60)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    main(dry_run=args.dry_run)
