"""
🔄 GESTOR MASIVO DE PRODUCTOS - VERSIÓN CORREGIDA
Lee CSV desde la MISMA carpeta donde está el script

Uso:
    1. Poner el CSV en la MISMA carpeta que este script
    2. python gestor_masivo_fixed.py
"""

import csv
import re
from datetime import datetime
import os
import sys

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

OUTPUT_DIR = 'output_sqls'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================================================================
# CATEGORÍAS VÁLIDAS
# =============================================================================

CATEGORIAS = {
    "Azúcar, caramelos y chocolate": ["Caramelos", "Chicles", "Chocolates y bombones", "Golosinas"],
    "Bazar y Varios": ["Hogar y decoración"],
    "Bebes": ["Comida infantil", "Cuidado e higiene del bebé", "Pañales", "Toallitas y algodón"],
    "Bebidas": ["Agua", "Cerveza", "Licores y destilados", "Refrescos", "Vino", "Zumos"],
    "Carnicería y Charcutería": ["Carne preparada", "Cerdo", "Charcuteria", "Cordero", "Pavo", "Pollo", "Vacuno"],
    "Congelados": ["Helados y postres congelados", "Platos congelados preparados", "Verduras congeladas"],
    "Conservas y Enlatados": ["Conservas de pescado y mariscos", "Frutas en almíbar", "Sopas cremas y otros preparados", "Verduras legumbres y hortalizas en conserva"],
    "Cuidado personal e Higiene": ["Cremas y protectores", "Cuidado del cabello", "Desodorantes", "Higiene bucal", "Higiene corporal", "Higiene íntima femenina", "Perfumes", "Productos de afeitado"],
    "Desayuno y Snack": ["Café y cacaos", "Cereales para desayuno", "Frutos secos embasados", "Galletas dulces", "Galletas saladas", "Mermelada y Miel", "Snack salados", "Té e infusiones"],
    "Despensa": ["Aceites", "Arroz pasta y quinoa", "Azúcares y edulcorantes", "Especias e hierbas secas", "Harinas", "Legumbres secas", "Sales", "Salsas caldos y condimentos preparados", "Vinagres"],
    "Frutas y Verduras": ["Fruta", "Setas", "Verduras"],
    "Hogar": ["Ambientadores", "Detergentes para ropa", "Lavavajillas", "Lejia y desinfectantes", "Limpiadores de superficie", "Suavizantes", "Utensilios y consumibles de limpieza"],
    "Lácteos y Huevos": ["Grasas vegetales", "Huevos", "Leche y bebidas \"lácteas\"", "Mantequillas y Natas", "Postres lácteos", "Quesos", "Yogures"],
    "Mascotas": ["Accesorios para perros", "Arena y asea para gatos", "Comida para otros animales", "Comida para perros"],
    "Panadería y Pastelería": ["Bollos", "Pan fresco", "Pasteles y Tartas"],
    "Pescadería": ["Marisco", "Moluscos", "Pescado"],
    "Platos preparados": ["Bocadillos y Sándwich listos", "Ensaladas listas", "Platos preparados refrigerados"]
}

# =============================================================================
# FUNCIONES
# =============================================================================

def leer_csv(nombre_archivo):
    """Lee CSV probando diferentes encodings y separadores"""
    
    # Construir ruta completa
    if not os.path.isabs(nombre_archivo):
        # Si es ruta relativa, usar carpeta actual
        ruta_completa = os.path.join(os.getcwd(), nombre_archivo)
    else:
        ruta_completa = nombre_archivo
    
    print(f"\n🔍 Buscando archivo: {ruta_completa}")
    
    if not os.path.exists(ruta_completa):
        print(f"❌ Archivo no encontrado: {ruta_completa}")
        print(f"\n📁 Archivos CSV en esta carpeta:")
        
        archivos = [f for f in os.listdir(os.getcwd()) if f.lower().endswith('.csv')]
        if archivos:
            for arch in archivos:
                print(f"   - {arch}")
        else:
            print("   (ninguno)")
        
        return None
    
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    separadores = [';', ',', '\t', '|']
    
    for encoding in encodings:
        for sep in separadores:
            try:
                with open(ruta_completa, 'r', encoding=encoding) as f:
                    # Leer primera línea para detectar formato
                    primera_linea = f.readline()
                    f.seek(0)  # Volver al inicio
                    
                    # Verificar que tenga el separador
                    if sep not in primera_linea:
                        continue
                    
                    reader = csv.DictReader(f, delimiter=sep)
                    datos = list(reader)
                    
                    if datos and len(datos) > 0:
                        # Verificar que tenga las columnas necesarias
                        columnas = list(datos[0].keys())
                        
                        if 'nombre_mercadona' in columnas or 'nombre' in columnas:
                            print(f"✅ Archivo leído correctamente")
                            print(f"   Encoding: {encoding}")
                            print(f"   Separador: '{sep}'")
                            print(f"   Productos: {len(datos)}")
                            print(f"   Columnas: {columnas}")
                            return datos
            
            except Exception as e:
                continue
    
    print(f"❌ No se pudo leer el archivo con ningún formato")
    return None

def escapar_sql(texto):
    """Escapa comillas para SQL"""
    if not texto:
        return ''
    return str(texto).replace("'", "''")

def generar_nombre_generico(nombre):
    """Quita marcas del nombre"""
    if not nombre:
        return ''
    
    marcas = ['hacendado', 'deliplus', 'bosque verde', 'nestlé', 'danone', 'pascual']
    
    nombre_limpio = nombre
    for marca in marcas:
        patron = re.compile(rf'\b{re.escape(marca)}\b', re.IGNORECASE)
        nombre_limpio = patron.sub('', nombre_limpio)
    
    nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio).strip()
    
    return nombre_limpio if len(nombre_limpio) >= 3 else nombre

def obtener_ultimo_id_manual():
    """Pide al usuario el último ID de Supabase"""
    print("\n" + "="*80)
    print("🔢 OBTENER ÚLTIMO ID")
    print("="*80)
    print("\n📋 Paso 1: Ve a Supabase SQL Editor")
    print("📋 Paso 2: Ejecuta esta query:")
    print()
    print("   SELECT id_producto FROM productos_mercadona")
    print("   ORDER BY id_producto DESC LIMIT 1;")
    print()
    print("📋 Paso 3: Introduce el resultado aquí")
    print()
    
    while True:
        ultimo = input("🔢 Último ID en Supabase (ej: ME-3899): ").strip().upper()
        
        if ultimo.startswith('ME-') and len(ultimo) == 7:
            try:
                numero = int(ultimo.split('-')[1])
                print(f"\n✅ Último ID: {ultimo}")
                print(f"✅ Siguiente ID: ME-{numero + 1:04d}\n")
                return numero
            except:
                print("❌ Formato inválido")
        else:
            print("❌ Debe ser formato: ME-XXXX (ej: ME-3899)")

def generar_sqls(productos, numero_base):
    """Genera archivos SQL"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # SQL Mercadona
    sql_merc = []
    sql_merc.append("-- ============================================================================")
    sql_merc.append(f"-- AÑADIR {len(productos)} PRODUCTOS A productos_mercadona")
    sql_merc.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_merc.append("-- Último ID: ME-{:04d}".format(numero_base))
    sql_merc.append("-- Nuevos IDs: ME-{:04d} a ME-{:04d}".format(numero_base + 1, numero_base + len(productos)))
    sql_merc.append("-- ============================================================================")
    sql_merc.append("")
    sql_merc.append("BEGIN;")
    sql_merc.append("")
    
    # SQL Genéricos
    sql_gen = []
    sql_gen.append("-- ============================================================================")
    sql_gen.append(f"-- AÑADIR {len(productos)} PRODUCTOS A productos_genericos")
    sql_gen.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_gen.append("-- ============================================================================")
    sql_gen.append("")
    sql_gen.append("BEGIN;")
    sql_gen.append("")
    
    for i, p in enumerate(productos):
        nuevo_id = f"ME-{numero_base + i + 1:04d}"
        
        # Detectar columnas (por si el CSV tiene nombres diferentes)
        nombre = p.get('nombre_mercadona') or p.get('nombre', '')
        precio = p.get('precio', '0€')
        cat = p.get('categoria', '')
        subcat = p.get('subcategoria', '')
        
        nombre_merc = escapar_sql(nombre)
        nombre_gen = escapar_sql(generar_nombre_generico(nombre))
        cat_sql = escapar_sql(cat)
        subcat_sql = escapar_sql(subcat)
        
        sql_merc.append(
            f"INSERT INTO productos_mercadona (id_producto, nombre, precio, categoria, subcategoria, imagen, url) "
            f"VALUES ('{nuevo_id}', '{nombre_merc}', '{precio}', '{cat_sql}', '{subcat_sql}', '', '');"
        )
        
        sql_gen.append(
            f"INSERT INTO productos_genericos (id_producto, nombre, categoria, subcategoria) "
            f"VALUES ('{nuevo_id}', '{nombre_gen}', '{cat_sql}', '{subcat_sql}');"
        )
    
    sql_merc.append("")
    sql_merc.append("COMMIT;")
    sql_gen.append("")
    sql_gen.append("COMMIT;")
    
    # Guardar archivos
    archivo_merc = os.path.join(OUTPUT_DIR, f'MERCADONA_{timestamp}.sql')
    archivo_gen = os.path.join(OUTPUT_DIR, f'GENERICOS_{timestamp}.sql')
    
    with open(archivo_merc, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_merc))
    
    with open(archivo_gen, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_gen))
    
    return archivo_merc, archivo_gen

def procesar_csv(nombre_archivo):
    """Procesa el CSV y genera SQLs"""
    
    print("\n" + "="*80)
    print("📥 PROCESANDO CSV")
    print("="*80)
    
    # Leer CSV
    productos = leer_csv(nombre_archivo)
    
    if not productos:
        return
    
    print(f"\n📊 Productos leídos: {len(productos)}")
    
    # Validar categorías
    errores = []
    for i, p in enumerate(productos[:10]):  # Revisar primeros 10
        cat = p.get('categoria', '')
        subcat = p.get('subcategoria', '')
        
        if cat not in CATEGORIAS:
            errores.append(f"Fila {i+2}: Categoría '{cat}' inválida")
        elif subcat not in CATEGORIAS.get(cat, []):
            errores.append(f"Fila {i+2}: Subcategoría '{subcat}' inválida")
    
    if errores:
        print(f"\n⚠️ ADVERTENCIA: Se encontraron categorías inválidas:")
        for err in errores:
            print(f"   {err}")
        
        continuar = input("\n¿Continuar de todas formas? (s/n): ").lower()
        if continuar != 's':
            print("❌ Importación cancelada")
            return
    
    # Obtener último ID
    numero_base = obtener_ultimo_id_manual()
    
    # Generar SQLs
    print(f"\n⚙️ Generando SQLs...")
    archivo_merc, archivo_gen = generar_sqls(productos, numero_base)
    
    print(f"\n✅ SQLs generados:")
    print(f"   📄 {archivo_merc}")
    print(f"   📄 {archivo_gen}")
    
    print(f"\n🎯 SIGUIENTE PASO:")
    print(f"   1. Abrir Supabase SQL Editor")
    print(f"   2. Copiar y ejecutar: {os.path.basename(archivo_merc)}")
    print(f"   3. Copiar y ejecutar: {os.path.basename(archivo_gen)}")
    print()

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("\n🛒 GESTOR MASIVO DE PRODUCTOS")
    print(f"📁 Carpeta de trabajo: {os.getcwd()}\n")
    
    # Listar CSVs disponibles
    archivos_csv = [f for f in os.listdir('.') if f.lower().endswith('.csv')]
    
    if archivos_csv:
        print("📁 Archivos CSV encontrados:")
        for i, arch in enumerate(archivos_csv, 1):
            print(f"   {i}. {arch}")
        print()
    
    # Pedir nombre del archivo
    nombre = input("📄 Nombre del archivo CSV a importar: ").strip()
    
    procesar_csv(nombre)
    
    input("\n⏎ Presiona ENTER para salir...")
