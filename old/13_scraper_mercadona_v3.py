"""
SCRAPER MERCADONA V3 - CON CATEGORÍAS CORRECTAS
Scrapea productos Y asigna categorías/subcategorías correctas desde el inicio
"""
from playwright.sync_api import sync_playwright
from supabase import create_client
import config
import json
import time
import re

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# ✅ CATEGORÍAS CORRECTAS PREDEFINIDAS
CATEGORIAS_MERCADONA = {
    # Lácteos
    'leche': ('Lácteos', 'Leche'),
    'yogur': ('Lácteos', 'Yogures'),
    'queso': ('Lácteos', 'Quesos'),
    'mantequilla': ('Lácteos', 'Mantequilla'),
    'nata': ('Lácteos', 'Nata'),
    
    # Bebidas
    'agua': ('Bebidas', 'Agua'),
    'refresco': ('Bebidas', 'Refrescos'),
    'zumo': ('Bebidas', 'Zumos'),
    'cerveza': ('Bebidas', 'Cervezas'),
    'vino': ('Bebidas', 'Vinos'),
    'cafe': ('Bebidas', 'Cafés'),
    
    # Despensa
    'aceite': ('Despensa', 'Aceites'),
    'arroz': ('Despensa', 'Arroces'),
    'pasta': ('Despensa', 'Pastas'),
    'legumbres': ('Despensa', 'Legumbres'),
    'conservas': ('Despensa', 'Conservas'),
    'sal': ('Despensa', 'Condimentos'),
    'azucar': ('Despensa', 'Azúcar'),
    
    # Panadería
    'pan': ('Panadería', 'Pan'),
    'galletas': ('Panadería', 'Galletas'),
    'bolleria': ('Panadería', 'Bollería'),
    
    # Carnicería
    'pollo': ('Carnicería', 'Aves'),
    'carne': ('Carnicería', 'Carnes'),
    'cerdo': ('Carnicería', 'Cerdo'),
    
    # Charcutería
    'jamon': ('Charcutería', 'Jamón'),
    'chorizo': ('Charcutería', 'Embutidos'),
    
    # Pescadería
    'pescado': ('Pescadería', 'Pescados'),
    'marisco': ('Pescadería', 'Mariscos'),
    
    # Frutas y Verduras
    'frutas': ('Frutas y Verduras', 'Frutas'),
    'verduras': ('Frutas y Verduras', 'Verduras'),
    
    # Congelados
    'helado': ('Congelados', 'Helados'),
    'pizza': ('Congelados', 'Pizzas'),
    
    # Higiene
    'gel': ('Higiene', 'Higiene corporal'),
    'champu': ('Higiene', 'Cabello'),
    'desodorante': ('Higiene', 'Desodorantes'),
    
    # Limpieza
    'detergente': ('Limpieza', 'Detergentes'),
    'lavavajillas': ('Limpieza', 'Lavavajillas'),
}

def extraer_formato(nombre):
    """Extrae formato (1L, 500g, etc)"""
    match = re.search(r'(\d+[.,]?\d*\s*[LlKkGgMm][LlGg]?)', nombre)
    return match.group(1).upper().replace(',', '.') if match else ''

def generar_id(supermercado, contador):
    """Genera ID único"""
    prefijo = {
        'Mercadona': 'ME',
        'Lidl': 'LI',
        'Carrefour': 'CA',
        'Dia': 'DI'
    }.get(supermercado, 'XX')
    
    return f"{prefijo}-{contador:04d}"

def scrapear_mercadona():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(60000)
        
        print("="*70)
        print("SCRAPER MERCADONA V3 - CON CATEGORÍAS CORRECTAS")
        print("="*70)
        
        page.goto("https://tienda.mercadona.es", wait_until="domcontentloaded")
        time.sleep(5)
        
        # Cookies
        for selector in ['button:has-text("Aceptar")', '#onetrust-accept-btn-handler']:
            try:
                if page.locator(selector).is_visible(timeout=3000):
                    page.click(selector)
                    time.sleep(2)
                    break
            except:
                pass
        
        # CP
        cp_ok = False
        for selector in ['input[placeholder*="código"]', 'input[type="text"]']:
            try:
                if page.locator(selector).first.is_visible(timeout=5000):
                    page.locator(selector).first.fill("28001")
                    time.sleep(2)
                    
                    for boton in ['button:has-text("Continuar")', 'button[type="submit"]']:
                        try:
                            page.click(boton, timeout=3000)
                            cp_ok = True
                            time.sleep(5)
                            break
                        except:
                            pass
                    
                    if cp_ok:
                        break
            except:
                pass
        
        if not cp_ok:
            print("\n⚠️  Introduce el CP MANUALMENTE")
            input("Presiona Enter cuando estés listo...")
        
        # Obtener ID actual más alto
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
        
        # Scrapear categorías
        total_insertados = 0
        
        for categoria_busqueda, (categoria, subcategoria) in CATEGORIAS_MERCADONA.items():
            print(f"\n{'='*70}")
            print(f"[{categoria}] → {subcategoria} ({categoria_busqueda})")
            print(f"{'='*70}")
            
            # Buscar
            for selector in ['input[type="search"]', 'input[placeholder*="Buscar"]']:
                try:
                    if page.locator(selector).is_visible(timeout=5000):
                        search_input = page.locator(selector).first
                        search_input.fill(categoria_busqueda)
                        time.sleep(1)
                        search_input.press('Enter')
                        time.sleep(5)
                        break
                except:
                    continue
            
            # Scroll
            for _ in range(2):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            # Extraer productos
            encontrados = 0
            for selector in ['.product-cell', 'article']:
                try:
                    cards = page.locator(selector).all()
                    if not cards:
                        continue
                    
                    for card in cards[:30]:  # Máximo 30 por categoría
                        try:
                            texto = card.inner_text()
                            lineas = texto.split('\n')
                            
                            nombre = lineas[0] if lineas else "Producto"
                            
                            # Extraer precio
                            precio = 0.0
                            for linea in lineas:
                                if '€' in linea:
                                    try:
                                        precio_limpio = linea.replace('€','').replace(',','.').strip().split()[0]
                                        precio = float(precio_limpio)
                                        break
                                    except:
                                        pass
                            
                            if precio > 0:
                                # Generar ID
                                id_producto = generar_id('Mercadona', contador)
                                contador += 1
                                
                                # Formato
                                formato = extraer_formato(nombre)
                                
                                # Marca
                                marca = 'Hacendado' if 'Hacendado' in nombre else None
                                
                                # Insertar directamente en BD
                                try:
                                    supabase.table('productos_nuevos').insert({
                                        'id_producto': id_producto,
                                        'nombre': nombre,
                                        'supermercado': 'Mercadona',
                                        'precio': precio,
                                        'categoria': categoria,
                                        'subcategoria': subcategoria,
                                        'formato': formato,
                                        'marca': marca
                                    }).execute()
                                    
                                    encontrados += 1
                                    total_insertados += 1
                                    
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
            
            print(f"  ✓ {encontrados} productos insertados en BD")
            time.sleep(2)
        
        browser.close()
    
    print(f"\n{'='*70}")
    print("SCRAPING COMPLETADO")
    print(f"{'='*70}")
    print(f"Total productos insertados: {total_insertados}")
    print(f"Directamente en productos_nuevos ✅")
    print(f"Con categorías y subcategorías correctas ✅")
    print(f"{'='*70}")

if __name__ == "__main__":
    print("\n⚠️  Este scraper:")
    print("  1. Scrapea Mercadona")
    print("  2. Asigna categorías/subcategorías CORRECTAS")
    print("  3. Inserta DIRECTAMENTE en productos_nuevos")
    print("  4. Sin archivos intermedios JSON\n")
    
    confirmar = input("¿Continuar? (s/n): ")
    if confirmar.lower() == 's':
        scrapear_mercadona()
        print("\n✅ Listo. Ahora puedes scrapear otros supermercados")
        print("   Cuando tengas 2+, ejecuta: python 11_recrear_grupos.py")
    else:
        print("Cancelado")
