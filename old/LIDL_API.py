"""
SCRAPER LIDL - USANDO API OFICIAL
La forma más simple y confiable
"""
import requests
from supabase import create_client
import config
import time

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# API de Lidl (pública)
LIDL_API = "https://www.lidl.es/p/api/gridboxes/ES/es"

# Categorías de Lidl (IDs reales de su API)
CATEGORIAS_LIDL = {
    # Bebidas
    "c5491": ("Bebidas", "Agua"),
    "c5494": ("Bebidas", "Refrescos"),
    "c5492": ("Bebidas", "Cervezas"),
    "c5493": ("Bebidas", "Vinos"),
    
    # Lácteos
    "c5396": ("Lácteos", "Leche"),
    "c5397": ("Lácteos", "Yogures"),
    "c5398": ("Lácteos", "Quesos"),
    
    # Despensa
    "c5419": ("Despensa", "Aceites"),
    "c5420": ("Despensa", "Arroces"),
    "c5421": ("Despensa", "Pastas"),
    "c5422": ("Despensa", "Conservas"),
    
    # Panadería
    "c5406": ("Panadería", "Pan"),
    "c5407": ("Panadería", "Galletas"),
    "c5408": ("Panadería", "Bollería"),
    
    # Carnes
    "c5386": ("Carnicería", "Aves"),
    "c5387": ("Carnicería", "Cerdo"),
    "c5388": ("Carnicería", "Ternera"),
    
    # Frutas y verduras
    "c5376": ("Frutas y Verduras", "Frutas"),
    "c5377": ("Frutas y Verduras", "Verduras"),
}

def generar_id(contador):
    return f"LI-{contador:04d}"

def scrapear_lidl_api():
    print("="*70)
    print("SCRAPER LIDL - USANDO API OFICIAL")
    print("="*70)
    
    # Obtener contador actual
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
    
    total_insertados = 0
    
    for cat_id, (categoria, subcategoria) in CATEGORIAS_LIDL.items():
        print(f"\n[{categoria}] → {subcategoria}")
        
        try:
            # Llamar a la API de Lidl
            url = f"{LIDL_API}/{cat_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"  ❌ Error API: {response.status_code}")
                continue
            
            data = response.json()
            productos = data.get('results', [])
            
            if not productos:
                print(f"  ⚠️  Sin productos")
                continue
            
            # Procesar productos
            insertados_cat = 0
            
            for prod in productos[:30]:  # Máximo 30 por categoría
                try:
                    nombre = prod.get('fullTitle', prod.get('title', ''))
                    precio_str = prod.get('price', {}).get('price', '0')
                    
                    # Limpiar precio
                    precio = float(precio_str.replace('€', '').replace(',', '.').strip())
                    
                    if precio > 0 and len(nombre) > 3:
                        # Generar ID
                        id_producto = generar_id(contador)
                        contador += 1
                        
                        # Marca (Lidl usa "Milbona" para lácteos, etc)
                        marca = None
                        if 'Milbona' in nombre:
                            marca = 'Milbona'
                        elif 'Freeway' in nombre:
                            marca = 'Freeway'
                        elif 'Lidl' in nombre:
                            marca = 'Lidl'
                        
                        # Insertar en BD
                        supabase.table('productos_nuevos').insert({
                            'id_producto': id_producto,
                            'nombre': nombre,
                            'supermercado': 'Lidl',
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
                        print(f"  Error producto: {e}")
                    continue
            
            if insertados_cat > 3:
                print(f"  ... y {insertados_cat - 3} más")
            
            print(f"  ✓ {insertados_cat} productos insertados")
            time.sleep(1)  # Pausa entre categorías
            
        except Exception as e:
            print(f"  ❌ Error categoría: {e}")
            continue
    
    print(f"\n{'='*70}")
    print("SCRAPING COMPLETADO")
    print(f"{'='*70}")
    print(f"Total productos Lidl: {total_insertados}")
    print(f"Insertados en productos_nuevos ✅")
    print(f"{'='*70}")
    
    if total_insertados > 0:
        print("\nSIGUIENTE PASO:")
        print("  python 11_recrear_grupos.py")
        print("  (para crear comparación de precios)")
    
    return total_insertados

if __name__ == "__main__":
    print("\n⚠️  SCRAPER LIDL - API OFICIAL")
    print("  Más rápido y confiable que scraping web")
    print("  ~400 productos en 5 minutos\n")
    
    confirmar = input("¿Continuar? (s/n): ")
    if confirmar.lower() == 's':
        total = scrapear_lidl_api()
        if total == 0:
            print("\n⚠️  No se encontraron productos")
            print("  La API puede haber cambiado")
            print("  Usa el scraper manual como alternativa")
    else:
        print("Cancelado")
