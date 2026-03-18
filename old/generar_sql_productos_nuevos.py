"""
Script para añadir productos nuevos a la BD sin romper relaciones
Uso: 
1. Crea CSV con formato: id_producto;nombre_mercadona;nombre_generico;precio;categoria;subcategoria;imagen;url
2. Ejecuta este script
3. Ejecuta los SQLs generados en Supabase
"""
import csv

def generar_sql_desde_csv(archivo_csv):
    # Leer CSV
    with open(archivo_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        productos = list(reader)
    
    print(f"📥 Productos leídos del CSV: {len(productos)}")
    
    # Generar SQL para productos_mercadona
    sql_mercadona = []
    sql_mercadona.append("-- ============================================================================")
    sql_mercadona.append("-- AÑADIR PRODUCTOS NUEVOS A productos_mercadona")
    sql_mercadona.append("-- ============================================================================")
    sql_mercadona.append("")
    sql_mercadona.append("BEGIN;")
    sql_mercadona.append("")
    
    for p in productos:
        id_p = p['id_producto']
        nombre = p['nombre_mercadona'].replace("'", "''")
        precio = p['precio']
        cat = p['categoria'].replace("'", "''")
        subcat = p['subcategoria'].replace("'", "''")
        imagen = p.get('imagen', '').replace("'", "''")
        url = p.get('url', '').replace("'", "''")
        
        sql_mercadona.append(
            f"INSERT INTO productos_mercadona (id_producto, nombre, precio, categoria, subcategoria, imagen, url) "
            f"VALUES ('{id_p}', '{nombre}', '{precio}', '{cat}', '{subcat}', '{imagen}', '{url}');"
        )
    
    sql_mercadona.append("")
    sql_mercadona.append("COMMIT;")
    sql_mercadona.append("")
    sql_mercadona.append("-- Verificar")
    sql_mercadona.append("SELECT COUNT(*) FROM productos_mercadona;")
    
    # Guardar SQL Mercadona
    with open('AÑADIR_PRODUCTOS_MERCADONA.sql', 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_mercadona))
    
    print(f"✅ SQL generado: AÑADIR_PRODUCTOS_MERCADONA.sql")
    
    # Generar SQL para productos_genericos
    sql_genericos = []
    sql_genericos.append("-- ============================================================================")
    sql_genericos.append("-- AÑADIR PRODUCTOS NUEVOS A productos_genericos")
    sql_genericos.append("-- ============================================================================")
    sql_genericos.append("")
    sql_genericos.append("BEGIN;")
    sql_genericos.append("")
    
    for p in productos:
        id_p = p['id_producto']
        nombre = p['nombre_generico'].replace("'", "''")
        cat = p['categoria'].replace("'", "''")
        subcat = p['subcategoria'].replace("'", "''")
        
        sql_genericos.append(
            f"INSERT INTO productos_genericos (id_producto, nombre, categoria, subcategoria) "
            f"VALUES ('{id_p}', '{nombre}', '{cat}', '{subcat}');"
        )
    
    sql_genericos.append("")
    sql_genericos.append("COMMIT;")
    sql_genericos.append("")
    sql_genericos.append("-- Verificar")
    sql_genericos.append("SELECT COUNT(*) FROM productos_genericos;")
    
    # Guardar SQL Genéricos
    with open('AÑADIR_PRODUCTOS_GENERICOS.sql', 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_genericos))
    
    print(f"✅ SQL generado: AÑADIR_PRODUCTOS_GENERICOS.sql")
    
    print(f"\n{'='*80}")
    print(f"✅ PROCESO COMPLETADO")
    print(f"{'='*80}")
    print(f"  Productos a añadir: {len(productos)}")
    print(f"  Archivos generados:")
    print(f"    - AÑADIR_PRODUCTOS_MERCADONA.sql")
    print(f"    - AÑADIR_PRODUCTOS_GENERICOS.sql")
    print(f"\n  IMPORTANTE: Ejecutar AMBOS SQLs en orden:")
    print(f"    1. AÑADIR_PRODUCTOS_MERCADONA.sql")
    print(f"    2. AÑADIR_PRODUCTOS_GENERICOS.sql")
    print(f"{'='*80}")

if __name__ == "__main__":
    # Ejemplo de uso
    print("="*80)
    print("GENERADOR DE SQLs PARA AÑADIR PRODUCTOS")
    print("="*80)
    print("\n📋 FORMATO DEL CSV:")
    print("id_producto;nombre_mercadona;nombre_generico;precio;categoria;subcategoria;imagen;url")
    print("\nEjemplo:")
    print("ME-3899;Aceite Hacendado;Aceite oliva;4.50€;Despensa;Aceites;;")
    print("\n" + "="*80)
    
    archivo = input("\n📁 Introduce el nombre del archivo CSV: ")
    
    try:
        generar_sql_desde_csv(archivo)
    except FileNotFoundError:
        print(f"\n❌ Error: No se encontró el archivo '{archivo}'")
    except Exception as e:
        print(f"\n❌ Error: {e}")
