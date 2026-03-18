"""
SCRAPER CARREFOUR - API OFICIAL
Esta sí funciona
"""
import requests
from supabase import create_client
import config
import time

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# API de Carrefour
CARREFOUR_API = "https://www.carrefour.es/api/v5/products"

# Categorías para buscar
CATEGORIAS_BUSQUEDA = {
    # Lácteos
    'leche': ('Lácteos', 'Leche'),
    'yogur': ('Lácteos', 'Yogures'),
    'queso': ('Lácteos', 'Quesos'),
    
    # Bebidas
    'agua': ('Bebidas', 'Agua'),
    'refresco': ('Bebidas', 'Refrescos'),
    'coca cola': ('Bebidas', 'Refrescos'),
    'cerveza': ('Bebidas', 'Cervezas'),
    'vino tinto': ('Bebidas', 'Vinos'),
    'zumo': ('Bebidas', 'Zumos'),
    
    # Despensa
    'aceite': ('Despensa', 'Aceites'),
    'arroz': ('Despensa', 'Arroces'),
    'pasta': ('Despensa', 'Pastas'),
    'conservas': ('Despensa', 'Conservas'),
    
    # Panadería
    'pan': ('Panadería', 'Pan'),
    'galletas': ('Panadería', 'Galletas'),
    
    # Carnes
    'pollo': ('Carnicería', 'Aves'),
    'carne': ('Carnicería', 'Carnes'),
}

def generar_id(contador):
    return f"CA-{contador:04d}"

def scrapear_carrefour():
    print("="*70)
    print("SCRAPER CARREFOUR - API OFICIAL")
    print("="*70)
    
    # Obtener contador actual
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
    
    total_insertados = 0
    
    for busqueda, (categoria, subcategoria) in CATEGORIAS_BUSQUEDA.items():
        print(f"\n[{categoria}] → {subcategoria} (buscando: {busqueda})")
        
        try:
            # Llamar API
            url = f"{CARREFOUR_API}/search"
            params = {
                'query': busqueda,
                'rows': 30,
                'start': 0
            }
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            }
            
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            
            if resp.status_code != 200:
                print(f"  ❌ Error API: {resp.status_code}")
                continue
            
            data = resp.json()
            productos = data.get('content', {}).get('docs', [])
            
            if not productos:
                print(f"  ⚠️  Sin productos")
                continue
            
            # Procesar productos
            insertados_cat = 0
            
            for prod in productos[:20]:
                try:
                    nombre = prod.get('display_name', '')
                    precio = prod.get('active_price', 0)
                    
                    if precio > 0 and len(nombre) > 3:
                        # Generar ID
                        id_producto = generar_id(contador)
                        contador += 1
                        
                        # Marca
                        marca = None
                        if 'Carrefour' in nombre:
                            marca = 'Carrefour'
                        
                        # Insertar en BD
                        supabase.table('productos_nuevos').insert({
                            'id_producto': id_producto,
                            'nombre': nombre,
                            'supermercado': 'Carrefour',
                            'precio': precio,
                            'categoria': categoria,
                            'subcategoria': subcategoria,
                            'marca': marca
                        }).execute()
                        
                        insertados_cat += 1
                        total_insertados += 1
                        
                        if insertados_cat <= 3:
                            print(f"  ✓ {nombre[:50]} ({precio}€)")
                
                except Exception as e:
                    if 'duplicate' not in str(e).lower():
                        print(f"  Error: {e}")
                    continue
            
            if insertados_cat > 3:
                print(f"  ... y {insertados_cat - 3} más")
            
            print(f"  ✓ {insertados_cat} productos insertados")
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    print(f"\n{'='*70}")
    print("SCRAPING COMPLETADO")
    print(f"{'='*70}")
    print(f"Total productos Carrefour: {total_insertados}")
    print(f"{'='*70}")
    
    if total_insertados > 0:
        print("\nSIGUIENTE PASO:")
        print("  python 11_recrear_grupos.py")
    
    return total_insertados

if __name__ == "__main__":
    confirmar = input("¿Scrapear Carrefour? (s/n): ")
    if confirmar.lower() == 's':
        scrapear_carrefour()
