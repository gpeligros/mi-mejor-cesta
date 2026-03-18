"""
🔄 GESTOR MASIVO DE PRODUCTOS
Permite añadir, actualizar y recategorizar productos masivamente desde CSV

Funcionalidades:
1. ✅ Añadir productos masivamente (CSV)
2. ✅ Actualizar categorías masivamente
3. ✅ Eliminar productos mal categorizados
4. ✅ Reemplazar productos existentes
5. ✅ Validar datos antes de importar

Uso:
    python gestor_masivo.py
"""

import csv
import re
from datetime import datetime
import os

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

MERCADONA_CSV = 'mercadona_final.csv'
GENERICOS_CSV = 'PRODUCTOS_GENERICOS_FIXED.csv'
OUTPUT_DIR = 'output_sqls'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def cargar_productos_actuales():
    """Carga productos existentes desde CSV"""
    productos = []
    
    if os.path.exists(MERCADONA_CSV):
        with open(MERCADONA_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            productos = list(reader)
    
    return productos

def obtener_categorias_unicas():
    """Extrae categorías únicas de productos existentes"""
    productos = cargar_productos_actuales()
    categorias = {}
    
    for p in productos:
        cat = p['categoria']
        subcat = p['subcategoria']
        
        if cat not in categorias:
            categorias[cat] = set()
        categorias[cat].add(subcat)
    
    return {cat: sorted(list(subcats)) for cat, subcats in categorias.items()}

def escapar_sql(texto):
    """Escapa comillas simples para SQL"""
    return texto.replace("'", "''")

def generar_nombre_generico(nombre_mercadona):
    """Elimina marcas del nombre"""
    marcas = [
        'hacendado', 'deliplus', 'bosque verde', 'compy', 'granzoo', 'nuske',
        'nestlé', 'nesquik', 'danone', 'president', 'pascual', 'central lechera',
        'coca cola', 'fanta', 'sprite', 'aquarius', 'nestea',
        'colgate', 'oral-b', 'gillette', 'nivea', 'dove', 'pantene', 'tresemmé',
        'tampax', 'evax', 'ausonia'
    ]
    
    nombre = nombre_mercadona
    for marca in marcas:
        patron = re.compile(rf'\b{re.escape(marca)}\b', re.IGNORECASE)
        nombre = patron.sub('', nombre)
    
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    
    if len(nombre) < 3:
        nombre = nombre_mercadona
    
    return nombre

# =============================================================================
# OPCIÓN 1: AÑADIR PRODUCTOS MASIVAMENTE (SIN ELIMINAR)
# =============================================================================

def añadir_productos_desde_csv(archivo_csv):
    """
    Añade productos desde CSV sin tocar los existentes
    
    Formato CSV requerido:
    nombre_mercadona;precio;categoria;subcategoria
    """
    print(f"\n{'='*80}")
    print(f"📥 IMPORTACIÓN MASIVA - AÑADIR PRODUCTOS")
    print(f"{'='*80}\n")
    
    # Leer CSV nuevo
    with open(archivo_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        nuevos = list(reader)
    
    print(f"📋 Productos a añadir: {len(nuevos)}")
    
    # Obtener último ID
    actuales = cargar_productos_actuales()
    if actuales:
        ultimo_id = actuales[-1]['id_producto']
        numero_base = int(ultimo_id.split('-')[1])
    else:
        numero_base = 0
    
    print(f"🔢 Último ID existente: ME-{numero_base:04d}")
    print(f"🔢 Siguiente ID: ME-{numero_base + 1:04d}\n")
    
    # Validar categorías
    categorias_validas = obtener_categorias_unicas()
    errores = []
    
    for i, p in enumerate(nuevos):
        if p['categoria'] not in categorias_validas:
            errores.append(f"Fila {i+2}: Categoría '{p['categoria']}' no existe")
        elif p['subcategoria'] not in categorias_validas.get(p['categoria'], []):
            errores.append(f"Fila {i+2}: Subcategoría '{p['subcategoria']}' no existe en '{p['categoria']}'")
    
    if errores:
        print(f"❌ ERRORES DE VALIDACIÓN:\n")
        for error in errores:
            print(f"  - {error}")
        return None
    
    print(f"✅ Validación OK - Todas las categorías son válidas\n")
    
    # Generar SQLs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # SQL Mercadona
    sql_merc = []
    sql_merc.append("-- ============================================================================")
    sql_merc.append(f"-- AÑADIR {len(nuevos)} PRODUCTOS NUEVOS A productos_mercadona")
    sql_merc.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_merc.append("-- ============================================================================")
    sql_merc.append("")
    sql_merc.append("BEGIN;")
    sql_merc.append("")
    
    # SQL Genéricos
    sql_gen = []
    sql_gen.append("-- ============================================================================")
    sql_gen.append(f"-- AÑADIR {len(nuevos)} PRODUCTOS NUEVOS A productos_genericos")
    sql_gen.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_gen.append("-- ============================================================================")
    sql_gen.append("")
    sql_gen.append("BEGIN;")
    sql_gen.append("")
    
    for i, p in enumerate(nuevos):
        nuevo_id = f"ME-{numero_base + i + 1:04d}"
        nombre_merc = escapar_sql(p['nombre_mercadona'])
        nombre_gen = escapar_sql(generar_nombre_generico(p['nombre_mercadona']))
        precio = p['precio']
        cat = escapar_sql(p['categoria'])
        subcat = escapar_sql(p['subcategoria'])
        
        sql_merc.append(
            f"INSERT INTO productos_mercadona (id_producto, nombre, precio, categoria, subcategoria, imagen, url) "
            f"VALUES ('{nuevo_id}', '{nombre_merc}', '{precio}', '{cat}', '{subcat}', '', '');"
        )
        
        sql_gen.append(
            f"INSERT INTO productos_genericos (id_producto, nombre, categoria, subcategoria) "
            f"VALUES ('{nuevo_id}', '{nombre_gen}', '{cat}', '{subcat}');"
        )
    
    sql_merc.append("")
    sql_merc.append("COMMIT;")
    sql_merc.append("")
    sql_merc.append("-- Verificar")
    sql_merc.append("SELECT COUNT(*) FROM productos_mercadona;")
    
    sql_gen.append("")
    sql_gen.append("COMMIT;")
    sql_gen.append("")
    sql_gen.append("-- Verificar")
    sql_gen.append("SELECT COUNT(*) FROM productos_genericos;")
    
    # Guardar archivos
    archivo_merc = os.path.join(OUTPUT_DIR, f'AÑADIR_MASIVO_MERCADONA_{timestamp}.sql')
    archivo_gen = os.path.join(OUTPUT_DIR, f'AÑADIR_MASIVO_GENERICOS_{timestamp}.sql')
    
    with open(archivo_merc, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_merc))
    
    with open(archivo_gen, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_gen))
    
    print(f"✅ SQLs generados:")
    print(f"  📄 {archivo_merc}")
    print(f"  📄 {archivo_gen}\n")
    
    return archivo_merc, archivo_gen

# =============================================================================
# OPCIÓN 2: CAMBIAR CATEGORÍA DE PRODUCTOS EXISTENTES
# =============================================================================

def cambiar_categoria_masiva(ids_productos, nueva_categoria, nueva_subcategoria):
    """
    Cambia la categoría de múltiples productos a la vez
    
    Args:
        ids_productos: Lista de IDs ['ME-0001', 'ME-0002', ...]
        nueva_categoria: Nueva categoría
        nueva_subcategoria: Nueva subcategoría
    """
    print(f"\n{'='*80}")
    print(f"🔄 RECATEGORIZACIÓN MASIVA")
    print(f"{'='*80}\n")
    
    print(f"📋 Productos a recategorizar: {len(ids_productos)}")
    print(f"📁 Nueva categoría: {nueva_categoria} → {nueva_subcategoria}\n")
    
    # Validar categoría
    categorias_validas = obtener_categorias_unicas()
    
    if nueva_categoria not in categorias_validas:
        print(f"❌ Error: Categoría '{nueva_categoria}' no existe")
        return None
    
    if nueva_subcategoria not in categorias_validas[nueva_categoria]:
        print(f"❌ Error: Subcategoría '{nueva_subcategoria}' no existe en '{nueva_categoria}'")
        return None
    
    print(f"✅ Categoría válida\n")
    
    # Generar SQL
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    sql = []
    sql.append("-- ============================================================================")
    sql.append(f"-- RECATEGORIZAR {len(ids_productos)} PRODUCTOS")
    sql.append(f"-- Nueva categoría: {nueva_categoria} → {nueva_subcategoria}")
    sql.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql.append("-- ============================================================================")
    sql.append("")
    sql.append("BEGIN;")
    sql.append("")
    sql.append("-- Actualizar productos_mercadona")
    
    for id_p in ids_productos:
        cat = escapar_sql(nueva_categoria)
        subcat = escapar_sql(nueva_subcategoria)
        
        sql.append(
            f"UPDATE productos_mercadona SET categoria = '{cat}', subcategoria = '{subcat}' "
            f"WHERE id_producto = '{id_p}';"
        )
    
    sql.append("")
    sql.append("-- Actualizar productos_genericos")
    
    for id_p in ids_productos:
        cat = escapar_sql(nueva_categoria)
        subcat = escapar_sql(nueva_subcategoria)
        
        sql.append(
            f"UPDATE productos_genericos SET categoria = '{cat}', subcategoria = '{subcat}' "
            f"WHERE id_producto = '{id_p}';"
        )
    
    sql.append("")
    sql.append("COMMIT;")
    sql.append("")
    sql.append("-- Verificar cambios")
    
    # Crear lista de IDs escapados para SQL
    ids_escaped = [f"'{id_p}'" for id_p in ids_productos]
    ids_sql = ', '.join(ids_escaped)
    
    sql.append(f"SELECT id_producto, nombre, categoria, subcategoria FROM productos_mercadona WHERE id_producto IN ({ids_sql});")
    
    archivo = os.path.join(OUTPUT_DIR, f'RECATEGORIZAR_MASIVO_{timestamp}.sql')
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql))
    
    print(f"✅ SQL generado:")
    print(f"  📄 {archivo}\n")
    
    return archivo

# =============================================================================
# OPCIÓN 3: ELIMINAR PRODUCTOS MAL CATEGORIZADOS
# =============================================================================

def eliminar_productos_por_categoria(categoria, subcategoria):
    """
    Elimina todos los productos de una categoría/subcategoría específica
    
    Args:
        categoria: Categoría a eliminar
        subcategoria: Subcategoría a eliminar (o None para toda la categoría)
    """
    print(f"\n{'='*80}")
    print(f"🗑️ ELIMINACIÓN MASIVA POR CATEGORÍA")
    print(f"{'='*80}\n")
    
    if subcategoria:
        print(f"📁 Eliminar: {categoria} → {subcategoria}")
    else:
        print(f"📁 Eliminar toda la categoría: {categoria}")
    
    # Generar SQL
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    sql = []
    sql.append("-- ============================================================================")
    if subcategoria:
        sql.append(f"-- ELIMINAR PRODUCTOS: {categoria} → {subcategoria}")
    else:
        sql.append(f"-- ELIMINAR PRODUCTOS DE CATEGORÍA: {categoria}")
    sql.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql.append("-- ⚠️ ADVERTENCIA: Esta operación NO se puede deshacer")
    sql.append("-- ============================================================================")
    sql.append("")
    sql.append("BEGIN;")
    sql.append("")
    sql.append("-- PASO 1: Ver productos que se eliminarán")
    
    cat = escapar_sql(categoria)
    
    if subcategoria:
        subcat = escapar_sql(subcategoria)
        sql.append(f"SELECT id_producto, nombre FROM productos_mercadona WHERE categoria = '{cat}' AND subcategoria = '{subcat}';")
        sql.append("")
        sql.append("-- PASO 2: Eliminar (descomenta las siguientes líneas para ejecutar)")
        sql.append(f"-- DELETE FROM productos_mercadona WHERE categoria = '{cat}' AND subcategoria = '{subcat}';")
        sql.append(f"-- DELETE FROM productos_genericos WHERE categoria = '{cat}' AND subcategoria = '{subcat}';")
    else:
        sql.append(f"SELECT id_producto, nombre FROM productos_mercadona WHERE categoria = '{cat}';")
        sql.append("")
        sql.append("-- PASO 2: Eliminar (descomenta las siguientes líneas para ejecutar)")
        sql.append(f"-- DELETE FROM productos_mercadona WHERE categoria = '{cat}';")
        sql.append(f"-- DELETE FROM productos_genericos WHERE categoria = '{cat}';")
    
    sql.append("")
    sql.append("COMMIT;")
    sql.append("")
    sql.append("-- Verificar después de eliminar")
    sql.append("SELECT COUNT(*) FROM productos_mercadona;")
    sql.append("SELECT COUNT(*) FROM productos_genericos;")
    
    archivo = os.path.join(OUTPUT_DIR, f'ELIMINAR_POR_CATEGORIA_{timestamp}.sql')
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql))
    
    print(f"\n✅ SQL generado:")
    print(f"  📄 {archivo}\n")
    print(f"⚠️ IMPORTANTE:")
    print(f"  1. El SQL está comentado por seguridad")
    print(f"  2. Primero revisa qué productos se eliminarán (paso 1)")
    print(f"  3. Luego descomenta las líneas DELETE para ejecutar\n")
    
    return archivo

# =============================================================================
# OPCIÓN 4: REEMPLAZAR PRODUCTOS (ELIMINAR + AÑADIR)
# =============================================================================

def reemplazar_productos_categoria(categoria, subcategoria, archivo_csv_nuevos):
    """
    Elimina productos de una categoría y los reemplaza con nuevos
    
    Args:
        categoria: Categoría a reemplazar
        subcategoria: Subcategoría a reemplazar
        archivo_csv_nuevos: CSV con productos nuevos
    """
    print(f"\n{'='*80}")
    print(f"🔄 REEMPLAZAR PRODUCTOS DE CATEGORÍA")
    print(f"{'='*80}\n")
    
    print(f"📁 Categoría: {categoria} → {subcategoria}")
    print(f"📄 Archivo: {archivo_csv_nuevos}\n")
    
    # Leer nuevos productos
    with open(archivo_csv_nuevos, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        nuevos = list(reader)
    
    print(f"📋 Productos nuevos: {len(nuevos)}")
    
    # Obtener IDs actuales para reutilizar
    actuales = cargar_productos_actuales()
    productos_a_eliminar = [
        p for p in actuales 
        if p['categoria'] == categoria and p['subcategoria'] == subcategoria
    ]
    
    print(f"🗑️ Productos a eliminar: {len(productos_a_eliminar)}\n")
    
    # Generar SQL
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    sql = []
    sql.append("-- ============================================================================")
    sql.append(f"-- REEMPLAZAR PRODUCTOS: {categoria} → {subcategoria}")
    sql.append(f"-- Eliminar: {len(productos_a_eliminar)} | Añadir: {len(nuevos)}")
    sql.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql.append("-- ============================================================================")
    sql.append("")
    sql.append("BEGIN;")
    sql.append("")
    sql.append("-- PASO 1: Eliminar productos antiguos")
    
    cat = escapar_sql(categoria)
    subcat = escapar_sql(subcategoria)
    
    sql.append(f"DELETE FROM productos_mercadona WHERE categoria = '{cat}' AND subcategoria = '{subcat}';")
    sql.append(f"DELETE FROM productos_genericos WHERE categoria = '{cat}' AND subcategoria = '{subcat}';")
    sql.append("")
    sql.append("-- PASO 2: Añadir productos nuevos")
    
    # Obtener último ID
    ultimo_id = actuales[-1]['id_producto']
    numero_base = int(ultimo_id.split('-')[1])
    
    for i, p in enumerate(nuevos):
        nuevo_id = f"ME-{numero_base + i + 1:04d}"
        nombre_merc = escapar_sql(p['nombre_mercadona'])
        nombre_gen = escapar_sql(generar_nombre_generico(p['nombre_mercadona']))
        precio = p['precio']
        
        sql.append(
            f"INSERT INTO productos_mercadona (id_producto, nombre, precio, categoria, subcategoria, imagen, url) "
            f"VALUES ('{nuevo_id}', '{nombre_merc}', '{precio}', '{cat}', '{subcat}', '', '');"
        )
        
        sql.append(
            f"INSERT INTO productos_genericos (id_producto, nombre, categoria, subcategoria) "
            f"VALUES ('{nuevo_id}', '{nombre_gen}', '{cat}', '{subcat}');"
        )
    
    sql.append("")
    sql.append("COMMIT;")
    sql.append("")
    sql.append("-- Verificar")
    sql.append(f"SELECT COUNT(*) FROM productos_mercadona WHERE categoria = '{cat}' AND subcategoria = '{subcat}';")
    
    archivo = os.path.join(OUTPUT_DIR, f'REEMPLAZAR_CATEGORIA_{timestamp}.sql')
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql))
    
    print(f"✅ SQL generado:")
    print(f"  📄 {archivo}\n")
    
    return archivo

# =============================================================================
# MENÚ INTERACTIVO
# =============================================================================

def menu_principal():
    """Menú interactivo para elegir operación"""
    print("\n" + "="*80)
    print("🛒 GESTOR MASIVO DE PRODUCTOS - MI MEJOR CESTA")
    print("="*80)
    print("\nSelecciona una operación:\n")
    print("  1️⃣  Añadir productos desde CSV (sin eliminar existentes)")
    print("  2️⃣  Cambiar categoría de productos (recategorizar)")
    print("  3️⃣  Eliminar productos por categoría")
    print("  4️⃣  Reemplazar productos de categoría (eliminar + añadir)")
    print("  5️⃣  Ver categorías disponibles")
    print("  0️⃣  Salir")
    print("\n" + "="*80)
    
    opcion = input("\n👉 Opción: ").strip()
    
    if opcion == '1':
        archivo = input("\n📄 Archivo CSV (nombre_mercadona;precio;categoria;subcategoria): ").strip()
        añadir_productos_desde_csv(archivo)
    
    elif opcion == '2':
        print("\n📋 Ingresa los IDs de productos separados por coma")
        print("   Ejemplo: ME-0001,ME-0002,ME-0003")
        ids_str = input("👉 IDs: ").strip()
        ids = [id.strip() for id in ids_str.split(',')]
        
        cat = input("📁 Nueva categoría: ").strip()
        subcat = input("📁 Nueva subcategoría: ").strip()
        
        cambiar_categoria_masiva(ids, cat, subcat)
    
    elif opcion == '3':
        cat = input("📁 Categoría a eliminar: ").strip()
        subcat = input("📁 Subcategoría (Enter para toda la categoría): ").strip()
        
        if not subcat:
            subcat = None
        
        eliminar_productos_por_categoria(cat, subcat)
    
    elif opcion == '4':
        cat = input("📁 Categoría: ").strip()
        subcat = input("📁 Subcategoría: ").strip()
        archivo = input("📄 CSV con productos nuevos: ").strip()
        
        reemplazar_productos_categoria(cat, subcat, archivo)
    
    elif opcion == '5':
        categorias = obtener_categorias_unicas()
        print("\n" + "="*80)
        print("📁 CATEGORÍAS DISPONIBLES")
        print("="*80 + "\n")
        
        for cat, subcats in categorias.items():
            print(f"📂 {cat}")
            for subcat in subcats:
                print(f"   └─ {subcat}")
            print()
    
    elif opcion == '0':
        print("\n👋 ¡Hasta luego!\n")
        return False
    
    else:
        print("\n❌ Opción inválida\n")
    
    return True

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    continuar = True
    
    while continuar:
        continuar = menu_principal()
        
        if continuar:
            input("\n⏎ Presiona ENTER para continuar...")
