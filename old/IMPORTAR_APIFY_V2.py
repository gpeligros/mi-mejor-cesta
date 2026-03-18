"""
IMPORTAR APIFY - VERSIÓN MEJORADA
Se adapta automáticamente al formato del JSON
"""
from supabase import create_client
import config
import json
import sys

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def generar_id(supermercado, contador):
    prefijos = {'Mercadona': 'ME', 'Lidl': 'LI', 'Carrefour': 'CA', 'Dia': 'DI'}
    return f"{prefijos.get(supermercado, 'XX')}-{contador:04d}"

def detectar_precio(prod):
    """Detecta el precio en diferentes formatos"""
    # Intentar diferentes campos
    for campo in ['price', 'currentPrice', 'precio', 'unit_price', 'unitPrice']:
        if campo in prod:
            precio = prod[campo]
            
            # Si es diccionario, buscar dentro
            if isinstance(precio, dict):
                for subcampo in ['amount', 'value', 'price', 'current']:
                    if subcampo in precio:
                        precio = precio[subcampo]
                        break
            
            # Convertir a float
            if isinstance(precio, (int, float)):
                return float(precio)
            
            if isinstance(precio, str):
                try:
                    # Limpiar y convertir
                    precio_limpio = precio.replace('€', '').replace(',', '.').strip()
                    return float(precio_limpio)
                except:
                    continue
    
    return 0.0

def detectar_nombre(prod):
    """Detecta el nombre en diferentes formatos"""
    for campo in ['title', 'name', 'nombre', 'display_name', 'productName']:
        if campo in prod and prod[campo]:
            return str(prod[campo])
    return ''

def asignar_categoria(nombre):
    """Asigna categoría basada en el nombre"""
    nombre_lower = nombre.lower()
    
    categorias = {
        'leche': ('Lácteos', 'Leche'),
        'yogur': ('Lácteos', 'Yogures'),
        'queso': ('Lácteos', 'Quesos'),
        'mantequilla': ('Lácteos', 'Mantequilla'),
        
        'agua': ('Bebidas', 'Agua'),
        'refresco': ('Bebidas', 'Refrescos'),
        'coca cola': ('Bebidas', 'Refrescos'),
        'fanta': ('Bebidas', 'Refrescos'),
        'cerveza': ('Bebidas', 'Cervezas'),
        'vino': ('Bebidas', 'Vinos'),
        'zumo': ('Bebidas', 'Zumos'),
        
        'aceite': ('Despensa', 'Aceites'),
        'arroz': ('Despensa', 'Arroces'),
        'pasta': ('Despensa', 'Pastas'),
        'conserva': ('Despensa', 'Conservas'),
        
        'pan': ('Panadería', 'Pan'),
        'galleta': ('Panadería', 'Galletas'),
        
        'pollo': ('Carnicería', 'Aves'),
        'carne': ('Carnicería', 'Carnes'),
        'cerdo': ('Carnicería', 'Cerdo'),
        
        'pescado': ('Pescadería', 'Pescados'),
        'merluza': ('Pescadería', 'Pescados'),
        
        'manzana': ('Frutas y Verduras', 'Frutas'),
        'platano': ('Frutas y Verduras', 'Frutas'),
        'tomate': ('Frutas y Verduras', 'Verduras'),
        'lechuga': ('Frutas y Verduras', 'Verduras'),
    }
    
    for palabra, (cat, subcat) in categorias.items():
        if palabra in nombre_lower:
            return cat, subcat
    
    return 'General', 'Otros'

def importar_apify(archivo, supermercado):
    print("="*70)
    print(f"IMPORTANDO {supermercado}")
    print("="*70)
    
    # Leer JSON
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error leyendo archivo: {e}")
        return
    
    # El JSON puede ser una lista o un dict con 'items' o 'results'
    if isinstance(data, dict):
        productos = data.get('items', data.get('results', data.get('data', [])))
    else:
        productos = data
    
    print(f"Total en JSON: {len(productos)}")
    
    # Mostrar estructura del primer producto
    if productos:
        print("\nEstructura del primer producto:")
        primer = productos[0]
        print(f"  Campos: {list(primer.keys())}")
        print(f"  Ejemplo: {primer}")
    
    # Obtener contador
    try:
        response = supabase.table('productos_nuevos')\
            .select('id_producto')\
            .eq('supermercado', supermercado)\
            .execute()
        
        contador = 1
        if response.data:
            ids = [int(p['id_producto'].split('-')[1]) for p in response.data if '-' in p['id_producto']]
            if ids:
                contador = max(ids) + 1
    except:
        contador = 1
    
    print(f"\nProcesando productos...")
    insertados = 0
    errores = 0
    
    for i, prod in enumerate(productos, 1):
        try:
            # Detectar nombre y precio
            nombre = detectar_nombre(prod)
            precio = detectar_precio(prod)
            
            if not nombre or len(nombre) < 3:
                errores += 1
                continue
            
            if precio <= 0:
                errores += 1
                if errores <= 5:
                    print(f"  ⚠️  Sin precio: {nombre}")
                continue
            
            # Asignar categoría
            categoria, subcategoria = asignar_categoria(nombre)
            
            # Detectar marca
            marca = None
            if 'Hacendado' in nombre:
                marca = 'Hacendado'
            elif 'Milbona' in nombre:
                marca = 'Milbona'
            elif supermercado in nombre:
                marca = supermercado
            
            # Generar ID
            id_producto = generar_id(supermercado, contador)
            contador += 1
            
            # Insertar
            supabase.table('productos_nuevos').insert({
                'id_producto': id_producto,
                'nombre': nombre,
                'supermercado': supermercado,
                'precio': precio,
                'categoria': categoria,
                'subcategoria': subcategoria,
                'marca': marca
            }).execute()
            
            insertados += 1
            
            if insertados % 100 == 0:
                print(f"  Insertados: {insertados}/{i}")
            
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
    
    if insertados == 0:
        print("\n⚠️  NO SE INSERTÓ NADA")
        print("\nEnvíame las primeras líneas del JSON para ver el formato:")
        if productos:
            print(json.dumps(productos[0], indent=2, ensure_ascii=False)[:500])

if __name__ == "__main__":
    if len(sys.argv) == 3:
        archivo = sys.argv[1]
        supermercado = sys.argv[2]
        importar_apify(archivo, supermercado)
    else:
        print("\nUSO:")
        print("  python IMPORTAR_APIFY_V2.py <archivo.json> <Supermercado>")
        print("\nEJEMPLO:")
        print("  python IMPORTAR_APIFY_V2.py mercadona.json Mercadona")
