"""
SCRAPER LIDL - VERSIÓN SEMI-MANUAL
Tú navegas manualmente, el script captura los productos
"""
from playwright.sync_api import sync_playwright
from supabase import create_client
import config
import time
import re

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def extraer_formato(nombre):
    match = re.search(r'(\d+[.,]?\d*\s*[LlKkGgMm][LlGg]?)', nombre)
    return match.group(1).upper().replace(',', '.') if match else ''

def generar_id(contador):
    return f"LI-{contador:04d}"

def capturar_productos():
    """Captura productos de la página actual"""
    productos = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("="*70)
        print("SCRAPER LIDL - SEMI MANUAL")
        print("="*70)
        print("\nINSTRUCCIONES:")
        print("1. Voy a abrir el navegador")
        print("2. Tú navegas a Lidl y buscas lo que quieras")
        print("3. Cuando estés en una página con productos, presiona Enter")
        print("4. Yo capturo los productos automáticamente")
        print("5. Repite para cada categoría\n")
        
        page.goto("https://www.lidl.es")
        time.sleep(3)
        
        # Contador de productos
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
        
        while True:
            input("\nNavega a una categoría y presiona Enter para capturar productos (o 'salir' para terminar): ")
            
            # Preguntar categoría
            print("\nCATEGORÍAS DISPONIBLES:")
            print("  1. Lácteos    2. Bebidas    3. Despensa")
            print("  4. Panadería  5. Carnicería 6. Charcutería")
            print("  7. Pescadería 8. Frutas y Verduras")
            print("  9. Congelados 10. Higiene  11. Limpieza")
            
            cat_num = input("\n¿Qué categoría es? (1-11): ")
            
            categorias_map = {
                '1': ('Lácteos', 'input subcategoría (Leche/Yogures/Quesos): '),
                '2': ('Bebidas', 'input subcategoría (Agua/Refrescos/Cervezas/Vinos): '),
                '3': ('Despensa', 'input subcategoría (Aceites/Arroces/Pastas/Conservas): '),
                '4': ('Panadería', 'input subcategoría (Pan/Galletas/Bollería): '),
                '5': ('Carnicería', 'input subcategoría (Aves/Carnes/Cerdo): '),
                '6': ('Charcutería', 'input subcategoría (Jamón/Embutidos): '),
                '7': ('Pescadería', 'input subcategoría (Pescados/Mariscos): '),
                '8': ('Frutas y Verduras', 'input subcategoría (Frutas/Verduras): '),
                '9': ('Congelados', 'input subcategoría (Helados/Pizzas): '),
                '10': ('Higiene', 'input subcategoría (Higiene corporal/Cabello): '),
                '11': ('Limpieza', 'input subcategoría (Detergentes/Lavavajillas): '),
            }
            
            if cat_num not in categorias_map:
                print("Categoría inválida")
                continue
            
            categoria, msg_subcat = categorias_map[cat_num]
            subcategoria = input(msg_subcat)
            
            # Capturar productos
            print("\nCapturando productos...")
            encontrados = 0
            
            for selector in ['.product', '.product-card', 'article', '[class*="product"]']:
                try:
                    cards = page.locator(selector).all()
                    
                    for card in cards[:30]:
                        try:
                            texto = card.inner_text()
                            lineas = texto.split('\n')
                            
                            nombre = lineas[0] if lineas else "Producto"
                            
                            # Buscar precio
                            precio = 0.0
                            for linea in lineas:
                                if '€' in linea:
                                    try:
                                        precio_limpio = linea.replace('€','').replace(',','.').strip().split()[0]
                                        precio = float(precio_limpio)
                                        break
                                    except:
                                        pass
                            
                            if precio > 0 and len(nombre) > 3:
                                # Generar ID
                                id_producto = generar_id(contador)
                                contador += 1
                                
                                # Formato
                                formato = extraer_formato(nombre)
                                
                                # Marca
                                marca = 'Milbona' if 'Milbona' in nombre else None
                                
                                # Insertar en BD
                                try:
                                    supabase.table('productos_nuevos').insert({
                                        'id_producto': id_producto,
                                        'nombre': nombre,
                                        'supermercado': 'Lidl',
                                        'precio': precio,
                                        'categoria': categoria,
                                        'subcategoria': subcategoria,
                                        'formato': formato,
                                        'marca': marca
                                    }).execute()
                                    
                                    encontrados += 1
                                    
                                    if encontrados <= 3:
                                        print(f"  ✓ {nombre[:50]} ({precio}€)")
                                        
                                except Exception as e:
                                    if 'duplicate' not in str(e).lower():
                                        print(f"  Error: {e}")
                        except:
                            continue
                    
                    if encontrados > 0:
                        break
                except:
                    continue
            
            if encontrados > 3:
                print(f"  ... y {encontrados - 3} más")
            
            print(f"\n  ✓ {encontrados} productos capturados e insertados en BD")
            
            continuar = input("\n¿Capturar otra categoría? (s/n): ")
            if continuar.lower() != 's':
                break
        
        browser.close()
    
    print(f"\n{'='*70}")
    print("CAPTURA COMPLETADA")
    print(f"{'='*70}")

if __name__ == "__main__":
    print("\n⚠️  SCRAPER SEMI-MANUAL:")
    print("  Tú navegas → Yo capturo → BD actualizada")
    print("  Perfecto para sitios difíciles de scrapear\n")
    
    confirmar = input("¿Continuar? (s/n): ")
    if confirmar.lower() == 's':
        capturar_productos()
    else:
        print("Cancelado")
