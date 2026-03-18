"""
SCRAPER MERCADONA DEFINITIVO
- Usa API oficial de Mercadona
- Extrae categorías reales
- Mapea a tu estructura del Excel
- Inserta productos limpios
"""
from supabase import create_client
import config
import requests
import openpyxl
from collections import defaultdict
import time
import re

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# API de Mercadona
MERCADONA_API = "https://tienda.mercadona.es/api"
CODIGO_POSTAL = "28001"  # Madrid

# Cargar mapeo del Excel
wb = openpyxl.load_workbook('productos_con_formato_generico.xlsx')
ws = wb.active

# Crear mapeo: palabras clave → (categoria, subcategoria)
MAPEO = defaultdict(list)

for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] and row[1] and row[2]:
        producto = row[0].strip().lower()
        categoria = row[1].strip()
        subcategoria = row[2].strip()
        
        # Extraer palabras clave (4+ letras)
        palabras = re.findall(r'\b\w{4,}\b', producto)
        
        for palabra in palabras:
            MAPEO[palabra].append((categoria, subcategoria))

print("="*70)
print("SCRAPER MERCADONA - API OFICIAL + CATEGORÍAS")
print("="*70)
print(f"Mapeo cargado: {len(MAPEO)} palabras clave")

def mapear_categoria(nombre_producto):
    """Mapea producto a categoría del Excel"""
    nombre_lower = nombre_producto.lower()
    palabras = re.findall(r'\b\w{4,}\b', nombre_lower)
    
    # Buscar coincidencias
    for palabra in palabras:
        if palabra in MAPEO:
            # Retornar primera coincidencia (la más común)
            return MAPEO[palabra][0]
    
    # Si no hay match, categoría por defecto
    return ("BAZAR Y VARIOS", "Otros bazar")

def obtener_categorias():
    """Obtiene categorías de Mercadona"""
    url = f"{MERCADONA_API}/categories/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('results', [])
    except Exception as e:
        print(f"Error obteniendo categorías: {e}")
    
    return []

def obtener_productos_categoria(cat_id):
    """Obtiene productos de una categoría"""
    url = f"{MERCADONA_API}/categories/{cat_id}/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            productos = []
            
            # Mercadona tiene subcategorías
            if 'categories' in data:
                for subcat in data['categories']:
                    if 'products' in subcat:
                        productos.extend(subcat['products'])
            
            if 'products' in data:
                productos.extend(data['products'])
            
            return productos
    except Exception as e:
        print(f"Error obteniendo productos: {e}")
    
    return []

def generar_id(contador):
    """Genera ID único para producto"""
    return f"ME-{contador:04d}"

# MAIN
print("\n[1/4] Obteniendo categorías de Mercadona...")
categorias = obtener_categorias()

if not categorias:
    print("❌ No se pudieron obtener categorías de la API")
    print("\n⚠️  ALTERNATIVA: Usar JSON local")
    
    # Si la API falla, usar JSON local
    import json
    with open('mercadona.json', 'r', encoding='utf-8') as f:
        productos_json = json.load(f)
    
    print(f"\n[2/4] Cargados {len(productos_json)} productos del JSON local")
    
    # Obtener contador
    response = supabase.table('productos').select('id_producto').eq('supermercado', 'Mercadona').execute()
    contador = 1
    if response.data:
        ids = [int(p['id_producto'].split('-')[1]) for p in response.data if '-' in p['id_producto']]
        if ids:
            contador = max(ids) + 1
    
    print(f"\n[3/4] Insertando productos con categorías mapeadas...")
    insertados = 0
    errores = 0
    
    for prod in productos_json[:1000]:  # Primeros 1000
        try:
            nombre = prod.get('display_name', '')
            precio_data = prod.get('price_instructions', {})
            precio = float(precio_data.get('unit_price', 0))
            imagen = prod.get('thumbnail', '')
            url = prod.get('share_url', '')
            
            if not nombre or precio <= 0:
                continue
            
            # Mapear a categoría del Excel
            categoria, subcategoria = mapear_categoria(nombre)
            
            # Generar ID
            id_producto = generar_id(contador)
            contador += 1
            
            # Insertar
            supabase.table('productos').insert({
                'id_producto': id_producto,
                'nombre': nombre,
                'supermercado': 'Mercadona',
                'precio': precio,
                'categoria': categoria,
                'subcategoria': subcategoria,
                'imagen': imagen,
                'url': url
            }).execute()
            
            insertados += 1
            
            if insertados % 100 == 0:
                print(f"  Insertados: {insertados}")
            
            if insertados <= 5:
                print(f"  ✓ {nombre[:40]} → {categoria}/{subcategoria}")
        
        except Exception as e:
            if 'duplicate' not in str(e).lower() and 'unique' not in str(e).lower():
                errores += 1
                if errores <= 5:
                    print(f"  Error: {e}")
    
    print(f"\n[4/4] Verificando resultado...")
    
else:
    print(f"Total categorías Mercadona: {len(categorias)}")
    print("\n[2/4] Scrapeando productos por categoría...")
    
    # Obtener contador
    response = supabase.table('productos').select('id_producto').eq('supermercado', 'Mercadona').execute()
    contador = 1
    if response.data:
        ids = [int(p['id_producto'].split('-')[1]) for p in response.data if '-' in p['id_producto']]
        if ids:
            contador = max(ids) + 1
    
    total_insertados = 0
    
    for cat in categorias[:10]:  # Primeras 10 categorías
        cat_nombre = cat.get('name', '')
        cat_id = cat.get('id')
        
        print(f"\n  Categoría: {cat_nombre}")
        
        productos = obtener_productos_categoria(cat_id)
        
        if not productos:
            print(f"    Sin productos")
            continue
        
        insertados_cat = 0
        
        for prod in productos[:50]:  # Máximo 50 por categoría
            try:
                nombre = prod.get('display_name', '')
                precio_data = prod.get('price_instructions', {})
                precio = float(precio_data.get('unit_price', 0))
                imagen = prod.get('thumbnail', '')
                url = prod.get('share_url', '')
                
                if not nombre or precio <= 0:
                    continue
                
                # Mapear a categoría del Excel
                categoria, subcategoria = mapear_categoria(nombre)
                
                # Generar ID
                id_producto = generar_id(contador)
                contador += 1
                
                # Insertar
                supabase.table('productos').insert({
                    'id_producto': id_producto,
                    'nombre': nombre,
                    'supermercado': 'Mercadona',
                    'precio': precio,
                    'categoria': categoria,
                    'subcategoria': subcategoria,
                    'imagen': imagen,
                    'url': url
                }).execute()
                
                insertados_cat += 1
                total_insertados += 1
                
                if insertados_cat <= 3:
                    print(f"    ✓ {nombre[:40]}")
            
            except Exception as e:
                if 'duplicate' not in str(e).lower():
                    pass
        
        print(f"    Insertados: {insertados_cat}")
        time.sleep(1)  # Evitar rate limiting

print(f"\n{'='*70}")
print("SCRAPING COMPLETADO")
print(f"{'='*70}")

# Verificar distribución
response = supabase.table('productos').select('categoria').eq('supermercado', 'Mercadona').execute()

cats = {}
for p in response.data:
    cat = p.get('categoria', 'Sin categoría')
    cats[cat] = cats.get(cat, 0) + 1

total = sum(cats.values())
print(f"\nTotal productos: {total}")
print(f"\nDistribución por categorías:")
for cat in sorted(cats.keys()):
    porcentaje = (cats[cat] / total * 100) if total > 0 else 0
    print(f"  {cat}: {cats[cat]} ({porcentaje:.1f}%)")

print(f"\n{'='*70}")
print("✅ PRODUCTOS INSERTADOS CON CATEGORÍAS")
print(f"{'='*70}")
