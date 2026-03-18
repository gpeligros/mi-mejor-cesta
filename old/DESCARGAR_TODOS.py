"""
DESCARGADOR COMPLETO DE PRODUCTOS
Descarga TODOS los productos de Mercadona a CSV
"""
from supabase import create_client
import config
import csv

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

print("Descargando TODOS los productos de Mercadona...")

# Descargar en páginas de 1000 (Supabase limita)
productos = []
page_size = 1000
offset = 0

while True:
    print(f"  Descargando desde {offset}...")
    
    response = supabase.table('productos')\
        .select('id_producto, nombre, precio, categoria, subcategoria')\
        .eq('supermercado', 'Mercadona')\
        .order('nombre')\
        .range(offset, offset + page_size - 1)\
        .execute()
    
    batch = response.data
    
    if not batch:
        break
    
    productos.extend(batch)
    print(f"  Descargados: {len(batch)} productos (total: {len(productos)})")
    
    if len(batch) < page_size:
        break
    
    offset += page_size

print(f"\n✅ Total productos descargados: {len(productos)}")

# Escribir CSV
filename = 'mercadona_COMPLETO.csv'
with open(filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=';')
    
    # Cabecera
    writer.writerow([
        'id_producto',
        'nombre',
        'precio',
        'categoria_actual',
        'subcategoria_actual',
        'categoria_nueva',
        'subcategoria_nueva'
    ])
    
    # Datos
    for p in productos:
        writer.writerow([
            p['id_producto'],
            p['nombre'],
            p['precio'],
            p['categoria'],
            p['subcategoria'],
            '',  # categoria_nueva (para que tú rellenes)
            ''   # subcategoria_nueva (para que tú rellenes)
        ])

print(f"\n✅ Archivo generado: {filename}")
print(f"✅ Total productos: {len(productos)}")
print(f"\nAbre el archivo en Excel, corrige las columnas 'categoria_nueva' y 'subcategoria_nueva'")
print(f"y súbeme el CSV corregido.")
