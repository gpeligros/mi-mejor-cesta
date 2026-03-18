# scrapers/mercadona.py - VERSIÓN COMPLETA Y CORREGIDA
from playwright.sync_api import sync_playwright
import time
import json

class MercadonaScraper:
    def __init__(self, codigo_postal="28001"):
        self.base_url = "https://tienda.mercadona.es"
        self.codigo_postal = codigo_postal
        
    def search_product(self, query, max_results=5):
        """
        Busca un producto en Mercadona
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,  # True para no ver el navegador
                args=['--disable-blink-features=AutomationControlled']
            )
            
            page = browser.new_page()
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            try:
                print(f"🔍 Buscando: {query}")
                
                # 1. Ir a la web
                page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                
                # 2. Aceptar cookies
                self._handle_cookies(page)
                
                # 3. Código postal
                self._handle_postal_code(page)
                
                # 4. Buscar
                self._do_search(page, query)
                
                # 5. Extraer productos
                productos = self._extract_products(page, max_results)
                
                return productos
                
            except Exception as e:
                print(f"❌ Error: {e}")
                return []
                
            finally:
                browser.close()
    
    def _handle_cookies(self, page):
        """Acepta cookies"""
        try:
            cookie_buttons = [
                'button:has-text("Aceptar")',
                'button:has-text("Acepto")',
                '#onetrust-accept-btn-handler'
            ]
            
            for selector in cookie_buttons:
                try:
                    page.click(selector, timeout=2000)
                    print("✅ Cookies aceptadas")
                    return
                except:
                    continue
        except:
            pass
    
    def _handle_postal_code(self, page):
        """Introduce código postal"""
        try:
            print(f"📮 Introduciendo CP: {self.codigo_postal}")
            
            cp_selectors = [
                'input[placeholder*="código postal"]',
                'input[name="postalCode"]',
                'input[type="text"]'
            ]
            
            cp_input = None
            for selector in cp_selectors:
                try:
                    cp_input = page.locator(selector).first
                    if cp_input.is_visible(timeout=2000):
                        break
                except:
                    continue
            
            if cp_input:
                cp_input.fill(self.codigo_postal)
                time.sleep(1)
                
                confirm_buttons = [
                    'button:has-text("Continuar")',
                    'button:has-text("Confirmar")',
                    'button[type="submit"]'
                ]
                
                for btn in confirm_buttons:
                    try:
                        page.click(btn, timeout=2000)
                        print("✅ CP confirmado")
                        time.sleep(3)
                        return
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ Error con CP: {e}")
    
    def _do_search(self, page, query):
        """Realiza la búsqueda"""
        search_selectors = [
            'input[type="search"]',
            'input[placeholder*="Buscar"]',
            'input[name="search"]'
        ]
        
        search_input = None
        for selector in search_selectors:
            try:
                search_input = page.locator(selector).first
                if search_input.is_visible(timeout=3000):
                    break
            except:
                continue
        
        if search_input:
            search_input.fill(query)
            time.sleep(1)
            search_input.press('Enter')
            
            # Esperar resultados
            result_selectors = ['.product-cell', '.product-card', 'article']
            
            for selector in result_selectors:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    print("✅ Resultados cargados")
                    return
                except:
                    continue
    
    def _extract_products(self, page, max_results):
        """Extrae productos de la página"""
        productos = []
        result_selectors = ['.product-cell', '.product-card']
        
        for selector in result_selectors:
            try:
                cards = page.locator(selector).all()
                
                for i, card in enumerate(cards[:max_results]):
                    try:
                        card_text = card.inner_text()
                        
                        # Extraer nombre
                        nombre = None
                        nombre_selectors = ['.product-title', '.product-name', 'h3', 'h4']
                        
                        for ns in nombre_selectors:
                            try:
                                nombre_elem = card.locator(ns).first
                                nombre = nombre_elem.inner_text()
                                if nombre:
                                    break
                            except:
                                continue
                        
                        # Extraer precio
                        precio = None
                        precio_selectors = ['.price', '.product-price', 'span[class*="price"]']
                        
                        for ps in precio_selectors:
                            try:
                                precio_elem = card.locator(ps).first
                                precio_text = precio_elem.inner_text()
                                precio = self._parse_precio(precio_text)
                                if precio > 0:
                                    break
                            except:
                                continue
                        
                        if not nombre:
                            lines = card_text.split('\n')
                            nombre = lines[0] if lines else "Producto"
                        
                        if not precio:
                            import re
                            matches = re.findall(r'(\d+[.,]\d+)\s*€', card_text)
                            if matches:
                                precio = self._parse_precio(matches[0])
                        
                        producto = {
                            'nombre': nombre.strip(),
                            'precio': precio if precio else 0.0,
                            'raw_text': card_text[:200],
                            'supermercado': 'Mercadona',
                            'posicion': i + 1
                        }
                        
                        productos.append(producto)
                        
                    except Exception as e:
                        continue
                
                if productos:
                    break
                    
            except:
                continue
        
        return productos
    
    def _parse_precio(self, precio_text):
        """Parsea precio a float"""
        if not precio_text:
            return 0.0
        
        precio = precio_text.replace('€', '').replace(' ', '').strip()
        precio = precio.replace(',', '.')
        
        try:
            return float(precio)
        except:
            return 0.0


# Test
if __name__ == "__main__":
    print("=" * 60)
    print("TEST MERCADONA SCRAPER")
    print("=" * 60)
    
    scraper = MercadonaScraper()
    productos = scraper.search_product("leche entera", max_results=3)
    
    if productos:
        print(f"\n✅ Encontrados {len(productos)} productos\n")
        for p in productos:
            print(f"[{p['posicion']}] {p['nombre']}")
            print(f"    Precio: {p['precio']}€")
            print(f"    Raw: {p['raw_text'][:80]}...")
            print()
    else:
        print("❌ No se encontraron productos")