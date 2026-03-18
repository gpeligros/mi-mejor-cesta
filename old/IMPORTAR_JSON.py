"""
IMPORTAR JSON - VERSIÓN FINAL
Adaptado a los formatos reales de los scrapers
"""
from supabase import create_client
import config
import json
import sys

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def generar_id(supermercado, contador):
    prefijos = {'Mercadona': 'ME', 'Lidl': 'LI', 'Carrefour': 'CA'}
    return f"{prefijos.get(supermercado, 'XX')}-{contador:04d}"

def asignar_categoria(nombre):
    """Asigna categoría basada en palabras clave"""
    nombre_lower = nombre.lower()
    
    categorias = {
        # Lácteos
        'leche': ('Lácteos', 'Leche'),
        'yogur': ('Lácteos', 'Yogures'),
        'queso': ('Lácteos', 'Quesos'),
        'mantequilla': ('Lácteos', 'Mantequilla'),
        'nata': ('Lácteos', 'Nata'),
        
        # Bebidas
        'agua': ('Bebidas', 'Agua'),
        'refresco': ('Bebidas', 'Refrescos'),
        'cola': ('Bebidas', 'Refrescos'),
        'fanta': ('Bebidas', 'Refrescos'),
        'sprite': ('Bebidas', 'Refrescos'),
        'cerveza': ('Bebidas', 'Cervezas'),
        'vino': ('Bebidas', 'Vinos'),
        'zumo': ('Bebidas', 'Zumos'),
        
        # Despensa
        'aceite': ('Despensa', 'Aceites'),
        'arroz': ('Despensa', 'Arroces'),
        'pasta': ('Despensa', 'Pastas'),
        'conserva': ('Despensa', 'Conservas'),
        'lata': ('Despensa', 'Conservas'),
        'sal': ('Despensa', 'Condimentos'),
        'azucar': ('Despensa', 'Azúcar'),
        
        # Panadería
        'pan': ('Panadería', 'Pan'),
        'galleta': ('Panadería', 'Galletas'),
        'bollo': ('Panadería', 'Bollería'),
        
        # Carnes
        'pollo': ('Carnicería', 'Aves'),
        'pavo': ('Carnicería', 'Aves'),
        'carne': ('Carnicería', 'Carnes'),
        'cerdo': ('Carnicería', 'Cerdo'),
        'ternera': ('Carnicería', 'Ternera'),
        
        # Charcutería
        'jamon': ('Charcutería', 'Jamón'),
        'chorizo': ('Charcutería', 'Embutidos'),
        'salchichon': ('Charcutería', 'Embutidos'),
        
        # Pescado
        'pescado': ('Pescadería', 'Pescados'),
        'merluza': ('Pescadería', 'Pescados'),
        'salmon': ('Pescadería', 'Pescados'),
        'atun': ('Pescadería', 'Pescados'),
        
        # Frutas y verduras
        'manzana': ('Frutas y Verduras', 'Frutas'),
        'platano': ('Frutas y Verduras', 'Frutas'),
        'naranja': ('Frutas y Verduras', 'Frutas'),
        'patata': ('Frutas y Verduras', 'Verduras'),
        'tomate': ('Frutas y Verduras', 'Verduras'),
        'lechuga': ('Frutas y Verduras', 'Verduras'),
        'cebolla': ('Frutas y Verduras', 'Verduras'),
        
        # Congelados
        'helado': ('Congelados', 'Helados'),
        'pizza': ('Congelados', 'Pizzas'),
        'congelad': ('Congelados', 'Congelados'),
        
        # Huevos
        'huevo': ('Lácteos', 'Huevos'),
    }
    
    for palabra, (cat, subcat) in categorias.items():
        if palabra in nombre_lower:
            return cat, subcat
    
    return 'General', 'Otros'

def importar_mercadona(archivo):
    """Importa JSON de Mercadona"""
    print("="*70)
    print("IMPORTANDO MERCADONA")
    print("="*70)
    
    with open(archivo, 'r', encoding='utf-8') as f:
        productos = json.load(f)
    
    print(f"Total en JSON: {len(productos)}")
    
    # Obtener contador
    try:
        response = supabase.table('productos_nuevos')\
            .select('id_producto')\
            .eq('supermercado', 'Mercadona')\
            .execute()
        
        contador = 1
        if response.data:
            ids = [int(p['id_producto'].split('-')[1]) for p in response.data if '-' in p['id_producto']]
            if ids:
                contador = max(ids) + 1
    except:
        contador = 1
    
    insertados = 0
    errores = 0
    
    for prod in productos:
        try:
            nombre = prod.get('display_name', '')
            
            # Precio en price_instructions.unit_price
            price_inst = prod.get('price_instructions', {})
            precio_str = price_inst.get('unit_price', '0')
            precio = float(precio_str)
            
            if not nombre or precio <= 0:
                errores += 1
                continue
            
            # Categoría
            categoria, subcategoria = asignar_categoria(nombre)
            
            # Marca
            marca = 'Hacendado' if 'Hacendado' in nombre else None
            
            # Insertar
            id_producto = generar_id('Mercadona', contador)
            contador += 1
            
            supabase.table('productos_nuevos').insert({
                'id_producto': id_producto,
                'nombre': nombre,
                'supermercado': 'Mercadona',
                'precio': precio,
                'categoria': categoria,
                'subcategoria': subcategoria,
                'marca': marca
            }).execute()
            
            insertados += 1
            
            if insertados % 500 == 0:
                print(f"  Insertados: {insertados}")
            
            if insertados <= 5:
                print(f"  ✓ {nombre[:50]} ({precio}€) → {categoria}/{subcategoria}")
        
        except Exception as e:
            errores += 1
            if errores <= 5:
                print(f"  Error: {e}")
    
    print(f"\n{'='*70}")
    print(f"Insertados: {insertados}")
    print(f"Errores: {errores}")
    print(f"{'='*70}")

def importar_lidl(archivo):
    """Importa JSON de Lidl"""
    print("="*70)
    print("IMPORTANDO LIDL")
    print("="*70)
    
    with open(archivo, 'r', encoding='utf-8') as f:
        productos = json.load(f)
    
    print(f"Total en JSON: {len(productos)}")
    print("⚠️  Filtrando solo productos de alimentación...")
    
    # Obtener contador
    try:
        response = supabase.table('productos_nuevos')\
            .select('id_producto')\
            .eq('supermercado', 'Lidl')\
            .execute()
        
        contador = 1
        if response.data:
            ids = [int(p['id_producto'].split('-')[1]) for p in response.data if '-' in p['id_producto']]
            if ids:
                contador = max(ids) + 1
    except:
        contador = 1
    
    insertados = 0
    errores = 0
    
    # Palabras clave de alimentación
    palabras_alimentos = ['leche', 'yogur', 'queso', 'pan', 'agua', 'cerveza', 
                         'vino', 'zumo', 'aceite', 'arroz', 'pasta', 'carne',
                         'pescado', 'fruta', 'verdura', 'patata', 'tomate',
                         'galleta', 'chocolate', 'cafe']
    
    for prod in productos:
        try:
            nombre = prod.get('title', '')
            
            # Filtrar solo alimentación
            es_alimento = any(palabra in nombre.lower() for palabra in palabras_alimentos)
            if not es_alimento:
                continue
            
            # Precio
            price_data = prod.get('price', {})
            precio = price_data.get('current', 0)
            
            if not nombre or precio <= 0:
                errores += 1
                continue
            
            # Categoría
            categoria, subcategoria = asignar_categoria(nombre)
            
            # Marca
            marca = prod.get('brand')
            if marca and 'Milbona' in marca:
                marca = 'Milbona'
            
            # Insertar
            id_producto = generar_id('Lidl', contador)
            contador += 1
            
            supabase.table('productos_nuevos').insert({
                'id_producto': id_producto,
                'nombre': nombre,
                'supermercado': 'Lidl',
                'precio': precio,
                'categoria': categoria,
                'subcategoria': subcategoria,
                'marca': marca
            }).execute()
            
            insertados += 1
            
            if insertados <= 10:
                print(f"  ✓ {nombre[:50]} ({precio}€)")
        
        except Exception as e:
            errores += 1
    
    print(f"\n{'='*70}")
    print(f"Insertados: {insertados}")
    print(f"Errores/No alimentación: {errores}")
    print(f"{'='*70}")

def importar_carrefour(archivo):
    """Importa JSON de Carrefour"""
    print("="*70)
    print("IMPORTANDO CARREFOUR")
    print("="*70)
    
    with open(archivo, 'r', encoding='utf-8') as f:
        productos = json.load(f)
    
    print(f"Total en JSON: {len(productos)}")
    
    # Obtener contador
    try:
        response = supabase.table('productos_nuevos')\
            .select('id_producto')\
            .eq('supermercado', 'Carrefour')\
            .execute()
        
        contador = 1
        if response.data:
            ids = [int(p['id_producto'].split('-')[1]) for p in response.data if '-' in p['id_producto']]
            if ids:
                contador = max(ids) + 1
    except:
        contador = 1
    
    insertados = 0
    errores = 0
    
    for prod in productos:
        try:
            nombre = prod.get('title', prod.get('name', ''))
            precio = prod.get('price', prod.get('currentPrice', 0))
            
            if isinstance(precio, dict):
                precio = precio.get('current', 0)
            
            if not nombre or precio <= 0:
                errores += 1
                continue
            
            # Categoría
            categoria, subcategoria = asignar_categoria(nombre)
            
            # Marca
            marca = 'Carrefour' if 'Carrefour' in nombre else None
            
            # Insertar
            id_producto = generar_id('Carrefour', contador)
            contador += 1
            
            supabase.table('productos_nuevos').insert({
                'id_producto': id_producto,
                'nombre': nombre,
                'supermercado': 'Carrefour',
                'precio': precio,
                'categoria': categoria,
                'subcategoria': subcategoria,
                'marca': marca
            }).execute()
            
            insertados += 1
            
            if insertados <= 5:
                print(f"  ✓ {nombre[:50]} ({precio}€)")
        
        except Exception as e:
            errores += 1
    
    print(f"\n{'='*70}")
    print(f"Insertados: {insertados}")
    print(f"Errores: {errores}")
    print(f"{'='*70}")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        archivo = sys.argv[1]
        supermercado = sys.argv[2].lower()
        
        if 'mercadona' in supermercado:
            importar_mercadona(archivo)
        elif 'lidl' in supermercado:
            importar_lidl(archivo)
        elif 'carrefour' in supermercado:
            importar_carrefour(archivo)
        else:
            print(f"Supermercado desconocido: {supermercado}")
    else:
        print("\nUSO:")
        print("  python IMPORTAR_JSON.py <archivo> <supermercado>")
        print("\nEJEMPLO:")
        print("  python IMPORTAR_JSON.py mercadona.json Mercadona")
        print("  python IMPORTAR_JSON.py lidl.json Lidl")
