#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Scraping para Carrefour - MI MEJOR CESTA
Versión mejorada con evasión de bloqueos
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
from datetime import date

# =====================================================
# CONFIGURACIÓN MEJORADA - Anti-bloqueo
# =====================================================

BASE_URL = "https://www.carrefour.es"

# Headers más realistas para evitar detección
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# =====================================================
# MÉTODO ALTERNATIVO: Usar API interna de Carrefour
# =====================================================

class CarrefourScraperAPI:
    """
    Scraper que usa la API interna de Carrefour
    (la que usa su propia web)
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.productos = []
        self.contadores_codigo = {}
    
    def obtener_productos_por_busqueda(self, termino_busqueda, limite=50):
        """
        Obtiene productos buscando en Carrefour
        Usa su API de búsqueda interna
        """
        print(f"🔍 Buscando: {termino_busqueda}...")
        
        try:
            # URL de la API de búsqueda de Carrefour
            url = f"https://www.carrefour.es/search-api/query/v1/search"
            
            params = {
                'query': termino_busqueda,
                'rows': limite,
                'start': 0,
                'lang': 'es',
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extraer productos del JSON
                productos = []
                if 'content' in data and 'docs' in data['content']:
                    for doc in data['content']['docs']:
                        producto = {
                            'nombre': doc.get('display_name', ''),
                            'precio': doc.get('active_price', ''),
                            'formato': doc.get('unit_size', '1ud'),
                            'marca': doc.get('brand', 'Sin marca'),
                            'categoria': termino_busqueda,
                        }
                        if producto['nombre']:
                            productos.append(producto)
                
                print(f"   ✅ {len(productos)} productos encontrados")
                return productos
            else:
                print(f"   ⚠️ HTTP {response.status_code}")
                return []
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []
        
        finally:
            # Rate limiting importante
            time.sleep(random.uniform(2, 4))
    
    def obtener_catalogo_basico(self):
        """
        Obtiene productos básicos más comunes
        """
        print("=" * 60)
        print("🛒 EXTRAYENDO CATÁLOGO BÁSICO DE CARREFOUR")
        print("=" * 60)
        
        # Lista de búsquedas para productos básicos
        busquedas = [
            # Bebidas
            'agua mineral',
            'leche',
            'zumo',
            'cerveza',
            'vino',
            'refresco',
            
            # Lácteos
            'yogur',
            'queso',
            'mantequilla',
            'huevos',
            
            # Panadería
            'pan de molde',
            'galletas',
            
            # Despensa
            'aceite de oliva',
            'arroz',
            'pasta',
            'atún',
            'tomate frito',
            'legumbres',
            
            # Limpieza
            'detergente',
            'suavizante',
            'papel higiénico',
            'lejía',
            
            # Higiene
            'gel de baño',
            'champú',
            'pasta de dientes',
            'desodorante',
            
            # Congelados
            'helado',
            'verduras congeladas',
            
            # Carnes
            'pollo',
            'cerdo',
            
            # Frutas y verduras
            'plátano',
            'manzana',
            'tomate',
            'lechuga',
        ]
        
        todos_productos = []
        
        for i, busqueda in enumerate(busquedas, 1):
            print(f"\n[{i}/{len(busquedas)}] {busqueda}")
            productos = self.obtener_productos_por_busqueda(busqueda, limite=20)
            todos_productos.extend(productos)
        
        # Eliminar duplicados por nombre
        productos_unicos = {}
        for p in todos_productos:
            if p['nombre'] not in productos_unicos:
                productos_unicos[p['nombre']] = p
        
        self.productos = list(productos_unicos.values())
        
        print(f"\n📊 TOTAL PRODUCTOS ÚNICOS: {len(self.productos)}")
        return self.productos
    
    def generar_codigo_producto(self, categoria_codigo, subcategoria_codigo):
        """Genera código según protocolo"""
        clave = f"{categoria_codigo}-{subcategoria_codigo}"
        
        if clave not in self.contadores_codigo:
            self.contadores_codigo[clave] = 1
        else:
            self.contadores_codigo[clave] += 1
        
        numero = str(self.contadores_codigo[clave]).zfill(3)
        return f"{categoria_codigo}-{subcategoria_codigo}-{numero}"
    
    def clasificar_producto(self, nombre, categoria_busqueda):
        """Clasifica producto según nombre y categoría"""
        nombre_lower = nombre.lower()
        cat_lower = categoria_busqueda.lower()
        
        # Bebidas
        if any(x in cat_lower or x in nombre_lower for x in ['agua', 'mineral']):
            return ('BE', 'AG', 'Bebidas', 'Agua')
        elif any(x in cat_lower or x in nombre_lower for x in ['zumo', 'jugo']):
            return ('BE', 'ZU', 'Bebidas', 'Zumos')
        elif 'cerveza' in cat_lower or 'cerveza' in nombre_lower:
            return ('BE', 'CE', 'Bebidas', 'Cerveza')
        elif 'vino' in cat_lower or 'vino' in nombre_lower:
            return ('BE', 'VI', 'Bebidas', 'Vino')
        elif any(x in cat_lower or x in nombre_lower for x in ['refresco', 'cola', 'fanta', 'sprite']):
            return ('BE', 'RE', 'Bebidas', 'Refrescos')
        
        # Lácteos
        elif 'leche' in nombre_lower:
            return ('LA', 'LE', 'Lácteos y Huevos', 'Leche')
        elif 'yogur' in nombre_lower:
            return ('LA', 'YO', 'Lácteos y Huevos', 'Yogures')
        elif 'queso' in nombre_lower:
            return ('LA', 'QU', 'Lácteos y Huevos', 'Quesos')
        elif any(x in nombre_lower for x in ['mantequilla', 'margarina', 'nata']):
            return ('LA', 'MA', 'Lácteos y Huevos', 'Mantequillas y Natas')
        elif 'huevo' in nombre_lower:
            return ('LA', 'HU', 'Lácteos y Huevos', 'Huevos')
        
        # Panadería
        elif any(x in nombre_lower for x in ['pan', 'barra', 'baguette']):
            return ('PA', 'PA', 'Panadería y Pastelería', 'Pan fresco')
        elif any(x in nombre_lower for x in ['galleta', 'cookie']):
            return ('DE', 'GA', 'Desayuno y Snack', 'Galletas dulces')
        
        # Despensa
        elif 'aceite' in nombre_lower:
            return ('DS', 'AC', 'Despensa', 'Aceites')
        elif 'arroz' in nombre_lower:
            return ('DS', 'AR', 'Despensa', 'Arroz, pasta y quinoa')
        elif 'pasta' in nombre_lower or 'macarron' in nombre_lower or 'espagueti' in nombre_lower:
            return ('DS', 'AR', 'Despensa', 'Arroz, pasta y quinoa')
        elif 'atún' in nombre_lower or 'sardina' in nombre_lower:
            return ('CO', 'CO', 'Conservas y Enlatados', 'Conservas de pescado')
        elif 'tomate' in nombre_lower and 'conserva' in nombre_lower:
            return ('CO', 'VE', 'Conservas y Enlatados', 'Verduras en conserva')
        elif any(x in nombre_lower for x in ['legumbre', 'lenteja', 'garbanzo', 'alubia']):
            return ('DS', 'LE', 'Despensa', 'Legumbres secas')
        
        # Limpieza
        elif 'detergente' in nombre_lower:
            return ('HO', 'DE', 'Hogar', 'Detergentes para ropa')
        elif 'suavizante' in nombre_lower:
            return ('HO', 'SU', 'Hogar', 'Suavizantes')
        elif any(x in nombre_lower for x in ['papel higiénico', 'papel wc']):
            return ('HO', 'UT', 'Hogar', 'Utensilios de limpieza')
        elif 'lejía' in nombre_lower or 'desinfectante' in nombre_lower:
            return ('HO', 'LE', 'Hogar', 'Lejia y desinfectantes')
        
        # Higiene personal
        elif any(x in nombre_lower for x in ['gel de baño', 'gel baño', 'ducha']):
            return ('CP', 'HC', 'Cuidado personal e Higiene', 'Higiene corporal')
        elif 'champú' in nombre_lower or 'champu' in nombre_lower:
            return ('CP', 'CC', 'Cuidado personal e Higiene', 'Cuidado del cabello')
        elif any(x in nombre_lower for x in ['pasta de dientes', 'dentífrico', 'dentifico']):
            return ('CP', 'HB', 'Cuidado personal e Higiene', 'Higiene bucal')
        elif 'desodorante' in nombre_lower:
            return ('CP', 'DE', 'Cuidado personal e Higiene', 'Desodorantes')
        
        # Congelados
        elif 'helado' in nombre_lower:
            return ('CO', 'HE', 'Congelados', 'Helados')
        elif 'congelad' in nombre_lower:
            return ('CO', 'VG', 'Congelados', 'Verduras congeladas')
        
        # Carnes
        elif 'pollo' in nombre_lower:
            return ('CA', 'PO', 'Carnicería y Charcutería', 'Pollo')
        elif 'cerdo' in nombre_lower:
            return ('CA', 'CE', 'Carnicería y Charcutería', 'Cerdo')
        
        # Frutas y verduras
        elif any(x in nombre_lower for x in ['plátano', 'platano', 'manzana', 'naranja']):
            return ('FR', 'FR', 'Frutas y Verduras', 'Fruta')
        elif any(x in nombre_lower for x in ['tomate', 'lechuga', 'pimiento', 'cebolla']):
            return ('FR', 'VE', 'Frutas y Verduras', 'Verduras')
        
        # Por defecto: Otros
        else:
            return ('DS', 'SC', 'Despensa', 'Otros')
    
    def asignar_codigos(self):
        """Asigna códigos a todos los productos"""
        print("\n🔢 Asignando códigos según protocolo...")
        
        productos_con_codigo = []
        
        for producto in self.productos:
            # Clasificar producto
            cat_codigo, sub_codigo, cat_nombre, sub_nombre = self.clasificar_producto(
                producto['nombre'], 
                producto.get('categoria', '')
            )
            
            # Generar código único
            codigo = self.generar_codigo_producto(cat_codigo, sub_codigo)
            
            productos_con_codigo.append({
                'id_producto': codigo,
                'nombre': producto['nombre'],
                'categoria': cat_nombre,
                'subcategoria': sub_nombre,
                'formato': producto.get('formato', '1ud'),
                'precio_carrefour': producto.get('precio', ''),
                'marca': producto.get('marca', ''),
            })
        
        return productos_con_codigo
    
    def guardar_csv_productos(self, productos, filename='productos_carrefour.csv'):
        """Guarda productos en CSV"""
        print(f"\n💾 Guardando {len(productos)} productos en {filename}...")
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id_producto', 'nombre', 'categoria', 'subcategoria', 'formato']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for p in productos:
                writer.writerow({
                    'id_producto': p['id_producto'],
                    'nombre': p['nombre'],
                    'categoria': p['categoria'],
                    'subcategoria': p['subcategoria'],
                    'formato': p['formato']
                })
        
        print(f"✅ Productos guardados")
    
    def guardar_csv_precios(self, productos, filename='precios_carrefour.csv'):
        """Guarda precios en CSV"""
        print(f"💾 Guardando precios en {filename}...")
        
        hoy = date.today().isoformat()
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id_producto', 'supermercado', 'precio', 'actualizado']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for p in productos:
                if p.get('precio_carrefour'):
                    try:
                        # Limpiar precio
                        precio = str(p['precio_carrefour']).replace('€', '').replace(',', '.').strip()
                        precio_float = float(precio)
                        
                        writer.writerow({
                            'id_producto': p['id_producto'],
                            'supermercado': 'Carrefour',
                            'precio': precio_float,
                            'actualizado': hoy
                        })
                    except:
                        pass
        
        print(f"✅ Precios guardados")
    
    def ejecutar(self):
        """Ejecuta el scraping completo"""
        # Obtener productos
        self.obtener_catalogo_basico()
        
        if not self.productos:
            print("\n❌ No se pudieron extraer productos")
            return
        
        # Asignar códigos
        productos_finales = self.asignar_codigos()
        
        # Guardar CSVs
        self.guardar_csv_productos(productos_finales)
        self.guardar_csv_precios(productos_finales)
        
        print("\n" + "=" * 60)
        print("✅ PROCESO COMPLETADO")
        print("=" * 60)
        print(f"📊 Total productos: {len(productos_finales)}")
        print(f"📄 Archivos generados:")
        print(f"   - productos_carrefour.csv")
        print(f"   - precios_carrefour.csv")
        print("\n🎯 Siguiente paso:")
        print("   1. Abre Supabase")
        print("   2. Importa ambos CSV")
        print("   3. ✅ Listo!")

# =====================================================
# EJECUCIÓN
# =====================================================

if __name__ == "__main__":
    scraper = CarrefourScraperAPI()
    scraper.ejecutar()