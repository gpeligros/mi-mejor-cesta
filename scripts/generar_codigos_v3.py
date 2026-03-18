#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de codigos V3 - Con reutilizacion de codigos libres
Conecta directamente a Supabase para detectar huecos
"""

import csv
from datetime import date
import sys

# IMPORTANTE: pip install supabase
try:
    from supabase import create_client, Client
    SUPABASE_DISPONIBLE = True
except ImportError:
    print("AVISO: supabase no instalado")
    print("Para reutilizar codigos: pip install supabase")
    SUPABASE_DISPONIBLE = False

# =====================================================
# CONFIGURACION
# =====================================================

# IMPORTANTE: Reemplaza con tus credenciales
SUPABASE_URL = "https://scpuriaofisssalsbzqv.supabase.co"
SUPABASE_KEY = "sb_secret_izhTc9q5TA_p4ItbeDB-UA_9zCDAYvi"

# Mapeos (mismo que antes)
MAPEO_CATEGORIAS = {
    'Bazar y Varios': 'BZ', 'Bebes': 'BB', 'Bebidas': 'BE',
    'Carniceria y Charcuteria': 'CA', 'Congelados': 'CO',
    'Conservas y Enlatados': 'CO', 'Cuidado personal e Higiene': 'CP',
    'Desayuno y Snack': 'DE', 'Despensa': 'DS', 'Frutas y Verduras': 'FR',
    'Hogar': 'HO', 'Lacteos y Huevos': 'LA', 'Mascotas': 'MA',
    'Panaderia y Pasteleria': 'PA', 'Pescaderia': 'PE', 'Platos preparados': 'PP',
}

MAPEO_SUBCATEGORIAS = {
    'Agua': 'AG', 'Cerveza': 'CE', 'Licores y destilados': 'LI',
    'Refrescos': 'RE', 'Vino': 'VI', 'Zumos': 'ZU',
    'Leche y bebidas lacteas': 'LE', 'Yogures': 'YO', 'Quesos': 'QU',
    'Mantequillas y Natas': 'MA', 'Huevos': 'HU', 'Pan fresco': 'PA',
    'Bollos': 'BO', 'Aceites': 'AC', 'Arroz pasta quinoa': 'AR',
    'Legumbres secas': 'LE', 'Harinas': 'HA', 'Azucares y edulcorantes': 'AZ',
    'Salsas caldos condimentos': 'SC', 'Conservas de pescado': 'CO',
    'Verduras legumbres hortalizas conserva': 'VE',
    'Detergentes para ropa': 'DE', 'Suavizantes': 'SU',
    'Lavavajillas': 'LA', 'Utensilios y consumibles de limpieza': 'UT',
    'Higiene corporal': 'HC', 'Cuidado del cabello': 'CC',
    'Higiene bucal': 'HB', 'Desodorantes': 'DE',
    'Cafe y cacaos': 'CA', 'Cereales para desayuno': 'CE',
    'Galletas dulces': 'GA', 'Mermelada y Miel': 'ME',
    'Snack salados': 'SN', 'Fruta': 'FR', 'Verduras': 'VE',
    'Comida para perros': 'CP', 'Comida para gatos': 'CG',
}

class GeneradorCodigosV3:
    def __init__(self):
        self.contadores = {}
        self.codigos_existentes = set()
        self.codigos_libres = {}
        self.supabase = None
        
        if SUPABASE_DISPONIBLE and "https://scpuriaofisssalsbzqv.supabase.co" not in SUPABASE_URL:
            try:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("✅ Conectado a Supabase")
            except Exception as e:
                print(f"⚠️  Error conectando: {e}")
    
    def detectar_codigos_libres_supabase(self):
        """Detecta huecos leyendo directamente de Supabase"""
        if not self.supabase:
            return
        
        try:
            response = self.supabase.table('productos').select('id_producto').execute()
            productos = response.data
            
            # Agrupar por categoria-subcategoria
            grupos = {}
            for p in productos:
                codigo = p['id_producto']
                self.codigos_existentes.add(codigo)
                
                if '-' in codigo:
                    partes = codigo.split('-')
                    if len(partes) == 3:
                        clave = f"{partes[0]}-{partes[1]}"
                        numero = int(partes[2])
                        
                        if clave not in grupos:
                            grupos[clave] = []
                        grupos[clave].append(numero)
                        
                        if clave not in self.contadores:
                            self.contadores[clave] = numero
                        else:
                            self.contadores[clave] = max(self.contadores[clave], numero)
            
            # Detectar huecos
            for clave, numeros in grupos.items():
                numeros.sort()
                maximo = max(numeros)
                
                libres = []
                for i in range(1, maximo + 1):
                    if i not in numeros:
                        libres.append(i)
                
                if libres:
                    self.codigos_libres[clave] = libres
            
            total_libres = sum(len(v) for v in self.codigos_libres.values())
            print(f"✅ {len(self.codigos_existentes)} codigos en uso")
            print(f"✅ {total_libres} codigos libres detectados")
            
        except Exception as e:
            print(f"Error leyendo Supabase: {e}")
    
    def generar_codigo(self, categoria, subcategoria):
        """Genera codigo reutilizando huecos si existen"""
        cod_cat = MAPEO_CATEGORIAS.get(categoria, 'OT')
        cod_sub = MAPEO_SUBCATEGORIAS.get(subcategoria, 'OT')
        clave = f"{cod_cat}-{cod_sub}"
        
        # Primero intentar reutilizar codigo libre
        if clave in self.codigos_libres and self.codigos_libres[clave]:
            numero = self.codigos_libres[clave].pop(0)
            codigo = f"{clave}-{str(numero).zfill(3)}"
            self.codigos_existentes.add(codigo)
            print(f"  ♻️  Reutilizando: {codigo}")
            return codigo
        
        # Si no hay libres, generar nuevo
        if clave not in self.contadores:
            self.contadores[clave] = 1
        else:
            self.contadores[clave] += 1
        
        numero = str(self.contadores[clave]).zfill(3)
        codigo = f"{clave}-{numero}"
        
        while codigo in self.codigos_existentes:
            self.contadores[clave] += 1
            numero = str(self.contadores[clave]).zfill(3)
            codigo = f"{clave}-{numero}"
        
        self.codigos_existentes.add(codigo)
        return codigo
    
    def procesar_csv(self, input_file='productos_nuevos.csv'):
        print("\n📊 Procesando productos nuevos...")
        
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
                
                print(f"\n✅ {len(productos)} productos procesados")
                print(f"✅ {len(precios)} precios encontrados")
                
                self.guardar_productos(productos)
                self.guardar_precios(precios)
                
                return productos, precios
                
        except Exception as e:
            print(f"ERROR: {e}")
            return [], []
    
    def guardar_productos(self, productos, filename='productos_IMPORTAR.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id_producto', 'nombre', 'categoria', 'subcategoria', 'formato']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(productos)
        print(f"💾 {filename}")
    
    def guardar_precios(self, precios, filename='precios_IMPORTAR.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id_producto', 'supermercado', 'precio', 'actualizado']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(precios)
        print(f"💾 {filename}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GENERADOR DE CODIGOS V3 - Con reutilizacion")
    print("=" * 60)
    
    generador = GeneradorCodigosV3()
    
    if generador.supabase:
        print("\n🔍 Detectando codigos libres en Supabase...")
        generador.detectar_codigos_libres_supabase()
    else:
        print("\n⚠️  Modo offline - No se reutilizaran codigos")
        print("Para habilitar: pip install supabase")
    
    productos, precios = generador.procesar_csv()
    
    if productos:
        print("\n" + "=" * 60)
        print("✅ COMPLETADO")
        print("=" * 60)
        print(f"Productos: {len(productos)}")
        print(f"Precios: {len(precios)}")
        print("\nArchivos:")
        print("  - productos_IMPORTAR.csv")
        print("  - precios_IMPORTAR.csv")
    
    input("\nEnter para salir...")