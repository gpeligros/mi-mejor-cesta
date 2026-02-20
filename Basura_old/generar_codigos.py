#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de codigos automatico para Mi Mejor Cesta
Lee productos_nuevos.csv y genera codigos siguiendo tu protocolo
"""

import csv
from datetime import date
import sys

# Configurar encoding para evitar errores con tildes
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
    # Bebidas
    'Agua': 'AG',
    'Cerveza': 'CE',
    'Licores y destilados': 'LI',
    'Refrescos': 'RE',
    'Vino': 'VI',
    'Zumos': 'ZU',
    
    # Lacteos
    'Leche y bebidas lacteas': 'LE',
    'Yogures': 'YO',
    'Quesos': 'QU',
    'Mantequillas y Natas': 'MA',
    'Huevos': 'HU',
    'Grasas vegetales': 'GR',
    'Postres lacteos': 'PO',
    
    # Panaderia
    'Pan fresco': 'PA',
    'Bollos': 'BO',
    'Pasteles y Tartas': 'PT',
    'Reposteria': 'RE',
    
    # Despensa
    'Aceites': 'AC',
    'Arroz pasta quinoa': 'AR',
    'Azucares y edulcorantes': 'AZ',
    'Especias e hierbas secas': 'ES',
    'Harinas': 'HA',
    'Legumbres secas': 'LE',
    'Sales': 'SA',
    'Salsas caldos condimentos': 'SC',
    'Vinagres': 'VI',
    
    # Conservas
    'Conservas de pescado': 'CO',
    'Conservas de pescado y mariscos': 'CO',
    'Conservas de marisco': 'CM',
    'Conservas de marisco/moluscos especificos': 'CM',
    'Frutas en almibar': 'FR',
    'Frutas en almibar o en su jugo': 'FR',
    'Sopas cremas preparados': 'SO',
    'Sopas, cremas y otros preparados': 'SO',
    'Verduras legumbres hortalizas conserva': 'VE',
    'Verduras, legumbres y hortalizas en conserva': 'VE',
    
    # Congelados
    'Helados y postres congelados': 'HE',
    'Platos congelados preparados': 'PL',
    'Verduras congeladas': 'VG',
    
    # Hogar
    'Ambientadores': 'AM',
    'Bolsas de basura': 'BO',
    'Bolsas de basura y congelacion': 'BO',
    'Detergentes para ropa': 'DE',
    'Lavavajillas': 'LA',
    'Lejia y desinfectantes': 'LE',
    'Limpiadores de superficie': 'LI',
    'Suavizantes': 'SU',
    'Utensilios y consumibles de limpieza': 'UT',
    
    # Cuidado Personal
    'Cremas y protectores': 'CR',
    'Cuidado del cabello': 'CC',
    'Desodorantes': 'DE',
    'Desodorante': 'DE',
    'Higiene bucal': 'HB',
    'Higiene corporal': 'HC',
    'Higiene intima femenina y accesorios': 'HI',
    'Productos de afeitado': 'PR',
    
    # Desayuno
    'Cafe y cacaos': 'CA',
    'Cereales para desayuno': 'CE',
    'Cremas': 'CR',
    'Frutos secos embasados': 'FR',
    'Galletas dulces': 'GA',
    'Galletas saladas': 'GS',
    'Mermelada y Miel': 'ME',
    'Snack salados': 'SN',
    'Te e infusiones': 'TE',
    
    # Frutas y Verduras
    'Fruta': 'FR',
    'Frutos secos': 'FS',
    'Setas': 'SE',
    'Verduras': 'VE',
    
    # Mascotas
    'Arena y asea para gatos': 'AR',
    'Comida para gatos': 'CG',
    'Comida para perros': 'CP',
    'Juguetes y accesorios': 'JU',
    
    # Bebes
    'Comida infantil': 'CO',
    'Cuidado e higiene del bebe': 'CU',
    'Leche de formula': 'LE',
    'Panales': 'PA',
    'Toallitas y algodon': 'TO',
    
    # Bazar
    'Bombillas y material electrico': 'BO',
    'Menaje y utensilios de cocina': 'ME',
    'Otros bazar': 'OT',
    'Papeleria y oficina': 'PA',
    'Pilas': 'PI',
    'Revistas': 'RE',
    
    # Carniceria
    'Carne preparada': 'CA',
    'Cerdo': 'CE',
    'Charcuteria': 'CH',
    'Cordero': 'CO',
    'Pavo': 'PA',
    'Pollo': 'PO',
    'Vacuno': 'VA',
    
    # Pescaderia
    'Marisco': 'MA',
    'Moluscos': 'MO',
    'Pescado': 'PE',
    
    # Platos preparados
    'Bocadillos y Sandwich listos': 'BO',
    'Ensaladas listas': 'EN',
    'Platos de carne / ave': 'PC',
    'Platos de pasta / arroz / fideos': 'PA',
    'Platos de pescado / marino': 'PL',
    'Sopas y cremas frias': 'SO',
    'Tortilas y platos de huevos preparados': 'TO',
}

class GeneradorCodigos:
    def __init__(self):
        self.contadores = {}
    
    def generar_codigo(self, categoria, subcategoria):
        """Genera codigo unico segun protocolo"""
        cod_cat = MAPEO_CATEGORIAS.get(categoria, 'OT')
        cod_sub = MAPEO_SUBCATEGORIAS.get(subcategoria, 'OT')
        
        clave = f"{cod_cat}-{cod_sub}"
        
        if clave not in self.contadores:
            self.contadores[clave] = 1
        else:
            self.contadores[clave] += 1
        
        numero = str(self.contadores[clave]).zfill(3)
        return f"{cod_cat}-{cod_sub}-{numero}"
    
    def procesar_csv(self, input_file='productos_nuevos.csv'):
        print("=" * 60)
        print("GENERADOR DE CODIGOS AUTOMATICO")
        print("=" * 60)
        
        productos = []
        precios = []
        linea_num = 0
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    linea_num += 1
                    
                    # Obtener valores con manejo seguro de None
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
                        'id_producto': codigo,
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
                
                print(f"\n{len(productos)} productos procesados")
                print(f"{len(precios)} precios encontrados")
                
                self.guardar_productos(productos)
                self.guardar_precios(precios)
                
                return productos, precios
                
        except FileNotFoundError:
            print(f"\nERROR: No se encontro {input_file}")
            return [], []
        except Exception as e:
            print(f"\nERROR: {e}")
            return [], []
    
    def guardar_productos(self, productos, filename='productos_con_codigos.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id_producto', 'nombre', 'categoria', 'subcategoria', 'formato']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(productos)
        print(f"\nGuardado: {filename}")
    
    def guardar_precios(self, precios, filename='precios_con_codigos.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id_producto', 'supermercado', 'precio', 'actualizado']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(precios)
        print(f"Guardado: {filename}")

if __name__ == "__main__":
    print("\nMI MEJOR CESTA - Generador de Codigos")
    print("=" * 60)
    
    generador = GeneradorCodigos()
    productos, precios = generador.procesar_csv()
    
    if productos:
        print("\n" + "=" * 60)
        print("PROCESO COMPLETADO")
        print("=" * 60)
        print(f"Productos con codigos: {len(productos)}")
        print(f"Precios: {len(precios)}")
        print("\nArchivos generados:")
        print("  - productos_con_codigos.csv")
        print("  - precios_con_codigos.csv")
        print("\nSiguiente paso:")
        print("  1. Abre Supabase")
        print("  2. Importa ambos CSV")
        print("  3. Listo!")
    else:
        print("\nNo se procesaron productos")
    
    print("\nPresiona Enter para salir...")
    input()
