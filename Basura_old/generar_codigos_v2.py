#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de codigos - VERSION 2
Lee tus productos existentes y continua la numeracion
"""

import csv
from datetime import date
import sys
import os

if sys.version_info[0] >= 3:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# =====================================================
# MAPEO DE CATEGORIAS Y SUBCATEGORIAS
# =====================================================

MAPEO_CATEGORIAS = {
    'Bazar y Varios': 'BZ',
    'Bebes': 'BB',
    'Bebidas': 'BE',
    'Carniceria y Charcuteria': 'CA',
    'Congelados': 'CO',
    'Conservas y Enlatados': 'CO',
    'Cuidado personal e Higiene': 'CP',
    'Desayuno y Snack': 'DE',
    'Despensa': 'DS',
    'Frutas y Verduras': 'FR',
    'Hogar': 'HO',
    'Lacteos y Huevos': 'LA',
    'Mascotas': 'MA',
    'Panaderia y Pasteleria': 'PA',
    'Pescaderia': 'PE',
    'Platos preparados': 'PP',
}

MAPEO_SUBCATEGORIAS = {
    'Agua': 'AG', 'Cerveza': 'CE', 'Licores y destilados': 'LI',
    'Refrescos': 'RE', 'Vino': 'VI', 'Zumos': 'ZU',
    'Leche y bebidas lacteas': 'LE', 'Yogures': 'YO', 'Quesos': 'QU',
    'Mantequillas y Natas': 'MA', 'Huevos': 'HU', 'Grasas vegetales': 'GR',
    'Postres lacteos': 'PO', 'Pan fresco': 'PA', 'Bollos': 'BO',
    'Pasteles y Tartas': 'PT', 'Reposteria': 'RE', 'Aceites': 'AC',
    'Arroz pasta quinoa': 'AR', 'Azucares y edulcorantes': 'AZ',
    'Especias e hierbas secas': 'ES', 'Harinas': 'HA', 'Legumbres secas': 'LE',
    'Sales': 'SA', 'Salsas caldos condimentos': 'SC', 'Vinagres': 'VI',
    'Conservas de pescado': 'CO', 'Conservas de pescado y mariscos': 'CO',
    'Conservas de marisco': 'CM', 'Conservas de marisco/moluscos especificos': 'CM',
    'Frutas en almibar': 'FR', 'Frutas en almibar o en su jugo': 'FR',
    'Sopas cremas preparados': 'SO', 'Sopas, cremas y otros preparados': 'SO',
    'Verduras legumbres hortalizas conserva': 'VE',
    'Verduras, legumbres y hortalizas en conserva': 'VE',
    'Helados y postres congelados': 'HE', 'Platos congelados preparados': 'PL',
    'Verduras congeladas': 'VG', 'Ambientadores': 'AM',
    'Bolsas de basura': 'BO', 'Bolsas de basura y congelacion': 'BO',
    'Detergentes para ropa': 'DE', 'Lavavajillas': 'LA',
    'Lejia y desinfectantes': 'LE', 'Limpiadores de superficie': 'LI',
    'Suavizantes': 'SU', 'Utensilios y consumibles de limpieza': 'UT',
    'Cremas y protectores': 'CR', 'Cuidado del cabello': 'CC',
    'Desodorantes': 'DE', 'Desodorante': 'DE', 'Higiene bucal': 'HB',
    'Higiene corporal': 'HC', 'Higiene intima femenina y accesorios': 'HI',
    'Productos de afeitado': 'PR', 'Cafe y cacaos': 'CA',
    'Cereales para desayuno': 'CE', 'Cremas': 'CR',
    'Frutos secos embasados': 'FR', 'Galletas dulces': 'GA',
    'Galletas saladas': 'GS', 'Mermelada y Miel': 'ME',
    'Snack salados': 'SN', 'Te e infusiones': 'TE',
    'Fruta': 'FR', 'Frutos secos': 'FS', 'Setas': 'SE', 'Verduras': 'VE',
    'Arena y asea para gatos': 'AR', 'Comida para gatos': 'CG',
    'Comida para perros': 'CP', 'Juguetes y accesorios': 'JU',
    'Comida infantil': 'CO', 'Cuidado e higiene del bebe': 'CU',
    'Leche de formula': 'LE', 'Panales': 'PA', 'Toallitas y algodon': 'TO',
    'Bombillas y material electrico': 'BO', 'Menaje y utensilios de cocina': 'ME',
    'Otros bazar': 'OT', 'Papeleria y oficina': 'PA', 'Pilas': 'PI',
    'Revistas': 'RE', 'Carne preparada': 'CA', 'Cerdo': 'CE',
    'Charcuteria': 'CH', 'Cordero': 'CO', 'Pavo': 'PA', 'Pollo': 'PO',
    'Vacuno': 'VA', 'Marisco': 'MA', 'Moluscos': 'MO', 'Pescado': 'PE',
    'Bocadillos y Sandwich listos': 'BO', 'Ensaladas listas': 'EN',
    'Platos de carne / ave': 'PC', 'Platos de pasta / arroz / fideos': 'PA',
    'Platos de pescado / marino': 'PL', 'Sopas y cremas frias': 'SO',
    'Tortilas y platos de huevos preparados': 'TO',
}

class GeneradorCodigosV2:
    def __init__(self):
        self.contadores = {}
        self.codigos_existentes = set()
    
    def leer_codigos_existentes(self, archivo_existentes='productos_existentes.csv'):
        """
        Lee un CSV con tus 703 productos existentes
        para saber que numeros ya estan usados
        """
        print("\n1. Leyendo productos existentes...")
        
        if not os.path.exists(archivo_existentes):
            print(f"   AVISO: No se encontro {archivo_existentes}")
            print(f"   Se generaran codigos desde 001")
            print(f"   ")
            print(f"   Para continuar numeracion correcta:")
            print(f"   1. Exporta tus 703 productos de Supabase como CSV")
            print(f"   2. Guardalo como: productos_existentes.csv")
            print(f"   3. Vuelve a ejecutar este script")
            return
        
        try:
            with open(archivo_existentes, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    codigo = (row.get('id') or row.get('id_producto') or '').strip()
                    if codigo:
                        self.codigos_existentes.add(codigo)
                        
                        # Extraer contador
                        if '-' in codigo:
                            partes = codigo.split('-')
                            if len(partes) == 3:
                                clave = f"{partes[0]}-{partes[1]}"
                                try:
                                    numero = int(partes[2])
                                    if clave not in self.contadores:
                                        self.contadores[clave] = numero
                                    else:
                                        self.contadores[clave] = max(self.contadores[clave], numero)
                                except:
                                    pass
            
            print(f"   {len(self.codigos_existentes)} codigos existentes leidos")
            print(f"   Contadores actualizados: {len(self.contadores)} categorias")
            
        except Exception as e:
            print(f"   ERROR leyendo existentes: {e}")
    
    def generar_codigo(self, categoria, subcategoria):
        """Genera codigo unico continuando numeracion"""
        cod_cat = MAPEO_CATEGORIAS.get(categoria, 'OT')
        cod_sub = MAPEO_SUBCATEGORIAS.get(subcategoria, 'OT')
        
        clave = f"{cod_cat}-{cod_sub}"
        
        # Incrementar desde el ultimo usado
        if clave not in self.contadores:
            self.contadores[clave] = 1
        else:
            self.contadores[clave] += 1
        
        numero = str(self.contadores[clave]).zfill(3)
        codigo = f"{cod_cat}-{cod_sub}-{numero}"
        
        # Verificar que no exista
        while codigo in self.codigos_existentes:
            self.contadores[clave] += 1
            numero = str(self.contadores[clave]).zfill(3)
            codigo = f"{cod_cat}-{cod_sub}-{numero}"
        
        self.codigos_existentes.add(codigo)
        return codigo
    
    def procesar_csv(self, input_file='productos_nuevos.csv'):
        print("\n2. Procesando productos nuevos...")
        
        productos = []
        precios = []
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    nombre = (row.get('nombre') or '').strip()
                    if not nombre or nombre.startswith('#'):
                        continue
                    
                    categoria = (row.get('categoria') or '').strip()
                    subcategoria = (row.get('subcategoria') or '').strip()
                    formato = (row.get('formato') or '1ud').strip()
                    
                    if not categoria or not subcategoria:
                        continue
                    
                    codigo = self.generar_codigo(categoria, subcategoria)
                    
                    productos.append({
                        'id': codigo,
                        'nombre': nombre,
                        'categoria': categoria,
                        'subcategoria': subcategoria,
                        'formato': formato
                    })
                    
                    hoy = date.today().isoformat()
                    
                    for super_nombre in ['carrefour', 'mercadona', 'lidl']:
                        precio_str = (row.get(f'precio_{super_nombre}') or '').strip()
                        if precio_str:
                            try:
                                precio_float = float(precio_str.replace(',', '.'))
                                precios.append({
                                    'id_producto': codigo,
                                    'supermercado': super_nombre.capitalize(),
                                    'precio': precio_float,
                                    'actualizado': hoy
                                })
                            except:
                                pass
                
                print(f"   {len(productos)} productos nuevos procesados")
                print(f"   {len(precios)} precios encontrados")
                
                self.guardar_productos(productos)
                self.guardar_precios(precios)
                
                return productos, precios
                
        except FileNotFoundError:
            print(f"\n   ERROR: No se encontro {input_file}")
            return [], []
        except Exception as e:
            print(f"\n   ERROR: {e}")
            return [], []
    
    def guardar_productos(self, productos, filename='productos_IMPORTAR.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'nombre', 'categoria', 'subcategoria', 'formato']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(productos)
        print(f"\n   Guardado: {filename}")
    
    def guardar_precios(self, precios, filename='precios_IMPORTAR.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id_producto', 'supermercado', 'precio', 'actualizado']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(precios)
        print(f"   Guardado: {filename}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MI MEJOR CESTA - Generador de Codigos V2")
    print("Continua numeracion desde productos existentes")
    print("=" * 60)
    
    generador = GeneradorCodigosV2()
    generador.leer_codigos_existentes()
    productos, precios = generador.procesar_csv()
    
    if productos:
        print("\n" + "=" * 60)
        print("PROCESO COMPLETADO")
        print("=" * 60)
        print(f"Productos nuevos: {len(productos)}")
        print(f"Precios: {len(precios)}")
        print("\nArchivos generados:")
        print("  - productos_IMPORTAR.csv  (listo para Supabase)")
        print("  - precios_IMPORTAR.csv    (listo para Supabase)")
        print("\nSiguiente paso:")
        print("  1. Supabase -> productos -> Import CSV")
        print("  2. Supabase -> precios_mercado -> Import CSV")
    else:
        print("\nNo se procesaron productos")
    
    print("\nPresiona Enter para salir...")
    input()