#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Scraping para Carrefour - Mi Mejor Cesta
Extrae productos y los clasifica según protocolo de códigos
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
from urllib.parse import urljoin

# =====================================================
# CONFIGURACIÓN
# =====================================================

BASE_URL = "https://www.carrefour.es"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# =====================================================
# MAPEO DE CATEGORÍAS CARREFOUR → TU PROTOCOLO
# =====================================================

MAPEO_CATEGORIAS = {
    # Bebidas
    'agua-y-refrescos': {'codigo': 'BE', 'subcategoria': 'AG'},
    'cerveza': {'codigo': 'BE', 'subcategoria': 'CE'},
    'vino-y-espumosos': {'codigo': 'BE', 'subcategoria': 'VI'},
    'zumos': {'codigo': 'BE', 'subcategoria': 'ZU'},
    'refrescos': {'codigo': 'BE', 'subcategoria': 'RE'},
    
    # Lácteos
    'leche': {'codigo': 'LA', 'subcategoria': 'LE'},
    'yogures': {'codigo': 'LA', 'subcategoria': 'YO'},
    'quesos': {'codigo': 'LA', 'subcategoria': 'QU'},
    'mantequilla-y-margarina': {'codigo': 'LA', 'subcategoria': 'MA'},
    'huevos': {'codigo': 'LA', 'subcategoria': 'HU'},
    
    # Panadería
    'pan-fresco': {'codigo': 'PA', 'subcategoria': 'PA'},
    'bolleria': {'codigo': 'PA', 'subcategoria': 'BO'},
    'pasteleria': {'codigo': 'PA', 'subcategoria': 'PT'},
    
    # Carnicería
    'pollo': {'codigo': 'CA', 'subcategoria': 'PO'},
    'cerdo': {'codigo': 'CA', 'subcategoria': 'CE'},
    'vacuno': {'codigo': 'CA', 'subcategoria': 'VA'},
    'cordero': {'codigo': 'CA', 'subcategoria': 'CO'},
    'charcuteria': {'codigo': 'CA', 'subcategoria': 'CH'},
    
    # Pescadería
    'pescado-fresco': {'codigo': 'PE', 'subcategoria': 'PE'},
    'marisco': {'codigo': 'PE', 'subcategoria': 'MA'},
    
    # Frutas y Verduras
    'frutas': {'codigo': 'FR', 'subcategoria': 'FR'},
    'verduras': {'codigo': 'FR', 'subcategoria': 'VE'},
    
    # Despensa
    'aceite': {'codigo': 'DS', 'subcategoria': 'AC'},
    'arroz-y-pasta': {'codigo': 'DS', 'subcategoria': 'AR'},
    'legumbres': {'codigo': 'DS', 'subcategoria': 'LE'},
    'harinas': {'codigo': 'DS', 'subcategoria': 'HA'},
    'azucar': {'codigo': 'DS', 'subcategoria': 'AZ'},
    'sal': {'codigo': 'DS', 'subcategoria': 'SA'},
    'especias': {'codigo': 'DS', 'subcategoria': 'ES'},
    
    # Conservas
    'conservas-pescado': {'codigo': 'CO', 'subcategoria': 'CO'},
    'conservas-verduras': {'codigo': 'CO', 'subcategoria': 'VE'},
    
    # Congelados
    'congelados-verduras': {'codigo': 'CO', 'subcategoria': 'VG'},
    'helados': {'codigo': 'CO', 'subcategoria': 'HE'},
    
    # Hogar
    'limpieza-hogar': {'codigo': 'HO', 'subcategoria': 'LI'},
    'detergente': {'codigo': 'HO', 'subcategoria': 'DE'},
    'suavizante': {'codigo': 'HO', 'subcategoria': 'SU'},
    
    # Cuidado Personal
    'higiene-corporal': {'codigo': 'CP', 'subcategoria': 'HC'},
    'higiene-bucal': {'codigo': 'CP', 'subcategoria': 'HB'},
    'desodorantes': {'codigo': 'CP', 'subcategoria': 'DE'},
    
    # Desayuno
    'cereales': {'codigo': 'DE', 'subcategoria': 'CE'},
    'galletas': {'codigo': 'DE', 'subcategoria': 'GA'},
    'cafe': {'codigo': 'DE', 'subcategoria': 'CA'},
    
    # Mascotas
    'comida-perros': {'codigo': 'MA', 'subcategoria': 'CP'},
    'comida-gatos': {'codigo': 'MA', 'subcategoria': 'CG'},
    
    # Bebés
    'panales': {'codigo': 'BB', 'subcategoria': 'PA'},
    'leche-infantil': {'codigo': 'BB', 'subcategoria': 'LE'},
}

# =====================================================
# FUNCIONES PRINCIPALES
# =====================================================

class CarrefourScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.productos = []
        self.contadores_codigo = {}  # Para llevar cuenta de códigos por categoría
        
    def obtener_categorias(self):
        """
        Obtiene todas las categorías principales de Carrefour
        """
        print("🔍 Obteniendo categorías de Carrefour...")
        
        try:
            # URL del supermercado online
            url = "https://www.carrefour.es/supermercado/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar enlaces de categorías (estructura puede variar)
                categorias = []
                
                # Método 1: Buscar en navegación principal
                nav_items = soup.find_all('a', class_='category-link')
                for item in nav_items:
                    nombre = item.text.strip()
                    url = item.get('href')
                    if url:
                        categorias.append({
                            'nombre': nombre,
                            'url': urljoin(BASE_URL, url)
                        })
                
                print(f"✅ {len(categorias)} categorías encontradas")
                return categorias
            else:
                print(f"❌ Error HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error obteniendo categorías: {e}")
            return []
    
    def extraer_productos_categoria(self, categoria_url, categoria_nombre):
        """
        Extrae todos los productos de una categoría
        """
        print(f"📊 Procesando: {categoria_nombre}...")
        productos_categoria = []
        
        try:
            # Añadir parámetro de paginación si es necesario
            url = f"{categoria_url}?page=1&limit=100"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar productos (la estructura HTML puede variar)
                items = soup.find_all('div', class_='product-card')
                
                for item in items:
                    try:
                        producto = self.extraer_datos_producto(item, categoria_nombre)
                        if producto:
                            productos_categoria.append(producto)
                    except Exception as e:
                        print(f"  ⚠️ Error procesando producto: {e}")
                        continue
                
                print(f"   ✅ {len(productos_categoria)} productos extraídos")
                
            # Rate limiting: esperar entre requests
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        return productos_categoria
    
    def extraer_datos_producto(self, item, categoria):
        """
        Extrae datos de un producto individual
        """
        try:
            # Nombre del producto
            nombre_elem = item.find('h3', class_='product-name') or item.find('span', class_='name')
            nombre = nombre_elem.text.strip() if nombre_elem else None
            
            # Precio
            precio_elem = item.find('span', class_='price') or item.find('div', class_='price-value')
            precio_text = precio_elem.text.strip() if precio_elem else None
            
            # Limpiar precio (ej: "1,85 €" → "1.85")
            precio = None
            if precio_text:
                precio = precio_text.replace('€', '').replace(',', '.').strip()
                try:
                    precio = float(precio)
                except:
                    precio = None
            
            # Marca
            marca_elem = item.find('span', class_='brand')
            marca = marca_elem.text.strip() if marca_elem else "Sin marca"
            
            # Formato/Cantidad
            formato_elem = item.find('span', class_='format') or item.find('span', class_='quantity')
            formato = formato_elem.text.strip() if formato_elem else "1ud"
            
            if not nombre:
                return None
            
            return {
                'nombre': nombre,
                'precio': precio,
                'marca': marca,
                'formato': formato,
                'categoria': categoria
            }
            
        except Exception as e:
            return None
    
    def generar_codigo_producto(self, categoria, subcategoria):
        """
        Genera código único según protocolo
        Formato: XX-YY-NNN
        """
        clave = f"{categoria}-{subcategoria}"
        
        if clave not in self.contadores_codigo:
            self.contadores_codigo[clave] = 1
        else:
            self.contadores_codigo[clave] += 1
        
        numero = str(self.contadores_codigo[clave]).zfill(3)
        return f"{categoria}-{subcategoria}-{numero}"
    
    def asignar_codigos(self):
        """
        Asigna códigos a todos los productos según protocolo
        """
        print("\n🔢 Asignando códigos según protocolo...")
        
        productos_con_codigo = []
        
        for producto in self.productos:
            categoria_nombre = producto.get('categoria', '').lower()
            
            # Buscar mapeo
            mapeo = None
            for key, value in MAPEO_CATEGORIAS.items():
                if key in categoria_nombre:
                    mapeo = value
                    break
            
            if not mapeo:
                # Categoría no mapeada, asignar genérico
                mapeo = {'codigo': 'OT', 'subcategoria': 'OT'}
            
            # Generar código
            codigo = self.generar_codigo_producto(mapeo['codigo'], mapeo['subcategoria'])
            
            productos_con_codigo.append({
                'id_producto': codigo,
                'nombre': producto['nombre'],
                'categoria': self.obtener_categoria_completa(mapeo['codigo']),
                'subcategoria': self.obtener_subcategoria_completa(mapeo['subcategoria']),
                'formato': producto['formato'],
                'precio_carrefour': producto.get('precio', ''),
                'marca': producto.get('marca', ''),
            })
        
        return productos_con_codigo
    
    def obtener_categoria_completa(self, codigo):
        """Convierte código de categoría a nombre completo"""
        categorias = {
            'BE': 'Bebidas',
            'LA': 'Lácteos y Huevos',
            'PA': 'Panadería y Pastelería',
            'CA': 'Carnicería y Charcutería',
            'PE': 'Pescadería',
            'FR': 'Frutas y Verduras',
            'DS': 'Despensa',
            'CO': 'Conservas y Enlatados',
            'HO': 'Hogar',
            'CP': 'Cuidado personal e Higiene',
            'DE': 'Desayuno y Snack',
            'MA': 'Mascotas',
            'BB': 'Bebes',
            'BZ': 'Bazar y Varios',
            'PP': 'Platos preparados',
        }
        return categorias.get(codigo, 'Otros')
    
    def obtener_subcategoria_completa(self, codigo):
        """Convierte código de subcategoría a nombre (simplificado)"""
        return codigo  # Por ahora devolver código, se puede expandir
    
    def guardar_csv_productos(self, productos, filename='productos_carrefour.csv'):
        """Guarda productos en CSV para Supabase"""
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
        
        print(f"✅ Productos guardados en {filename}")
    
    def guardar_csv_precios(self, productos, filename='precios_carrefour.csv'):
        """Guarda precios en CSV para Supabase"""
        print(f"💾 Guardando precios en {filename}...")
        
        from datetime import date
        hoy = date.today().isoformat()
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id_producto', 'supermercado', 'precio', 'actualizado']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for p in productos:
                if p.get('precio_carrefour'):
                    writer.writerow({
                        'id_producto': p['id_producto'],
                        'supermercado': 'Carrefour',
                        'precio': p['precio_carrefour'],
                        'actualizado': hoy
                    })
        
        print(f"✅ Precios guardados en {filename}")
    
    def ejecutar(self):
        """Ejecuta el scraping completo"""
        print("=" * 60)
        print("🛒 SCRAPER DE CARREFOUR - MI MEJOR CESTA")
        print("=" * 60)
        
        # Obtener categorías
        categorias = self.obtener_categorias()
        
        if not categorias:
            print("⚠️ No se pudieron obtener categorías. Verificar estructura HTML.")
            return
        
        # Procesar cada categoría
        for i, cat in enumerate(categorias[:5], 1):  # Limitar a 5 para pruebas
            print(f"\n[{i}/{len(categorias)}] {cat['nombre']}")
            productos = self.extraer_productos_categoria(cat['url'], cat['nombre'])
            self.productos.extend(productos)
        
        print(f"\n📊 TOTAL PRODUCTOS EXTRAÍDOS: {len(self.productos)}")
        
        # Asignar códigos
        productos_finales = self.asignar_codigos()
        
        # Guardar archivos
        self.guardar_csv_productos(productos_finales)
        self.guardar_csv_precios(productos_finales)
        
        print("\n✅ PROCESO COMPLETADO")
        print(f"   Archivos generados:")
        print(f"   - productos_carrefour.csv ({len(productos_finales)} productos)")
        print(f"   - precios_carrefour.csv ({len([p for p in productos_finales if p.get('precio_carrefour')])} precios)")
# =====================================================
# EJECUCIÓN
# =====================================================

if __name__ == "__main__":
    scraper = CarrefourScraper()
    scraper.ejecutar()