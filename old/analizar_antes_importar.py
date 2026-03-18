"""
🔍 ANALIZADOR DE PRODUCTOS - PREVIO A IMPORTACIÓN
Detecta duplicados, productos nuevos, mal categorizados, etc.

Uso:
    python analizar_antes_importar.py archivo_a_importar.csv
"""

import csv
import sys
from difflib import SequenceMatcher

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

MERCADONA_CSV = 'MERCADONA_FINAL.csv'
UMBRAL_SIMILITUD = 0.85  # 85% similar = posible duplicado

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def cargar_productos_actuales():
    """Carga productos existentes desde CSV"""
    productos = []
    
    try:
        with open(MERCADONA_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            productos = list(reader)
    except FileNotFoundError:
        print(f"❌ No se encontró {MERCADONA_CSV}")
        return []
    
    return productos

def similitud_textos(a, b):
    """Calcula similitud entre dos textos (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def obtener_categorias_validas():
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

def normalizar_precio(precio):
    """Normaliza formato de precio para comparación"""
    # Elimina € y espacios
    return precio.replace('€', '').replace(' ', '').strip()

# =============================================================================
# ANÁLISIS PRINCIPAL
# =============================================================================

def analizar_csv(archivo_csv):
    """
    Analiza el CSV y detecta:
    1. Productos totalmente nuevos
    2. Posibles duplicados
    3. Productos con categorías inválidas
    4. Productos mal categorizados
    5. Diferencias de precio con existentes
    """
    
    print("="*80)
    print("🔍 ANÁLISIS DE PRODUCTOS - PREVIO A IMPORTACIÓN")
    print("="*80)
    print(f"\n📄 Archivo a analizar: {archivo_csv}\n")
    
    # Cargar datos
    try:
        with open(archivo_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            nuevos = list(reader)
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {archivo_csv}")
        return
    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        return
    
    actuales = cargar_productos_actuales()
    categorias_validas = obtener_categorias_validas()
    
    print(f"📊 RESUMEN INICIAL:")
    print(f"  - Productos en BD actual: {len(actuales)}")
    print(f"  - Productos a importar: {len(nuevos)}")
    print(f"  - Categorías válidas: {len(categorias_validas)}")
    print()
    
    # ==========================================================================
    # ANÁLISIS 1: CATEGORÍAS INVÁLIDAS
    # ==========================================================================
    
    print("="*80)
    print("1️⃣ VERIFICACIÓN DE CATEGORÍAS")
    print("="*80)
    
    categorias_invalidas = []
    
    for i, nuevo in enumerate(nuevos):
        cat = nuevo.get('categoria', '')
        subcat = nuevo.get('subcategoria', '')
        
        if not cat or not subcat:
            categorias_invalidas.append({
                'fila': i+2,
                'nombre': nuevo.get('nombre_mercadona', ''),
                'problema': 'Categoría o subcategoría vacía'
            })
        elif cat not in categorias_validas:
            categorias_invalidas.append({
                'fila': i+2,
                'nombre': nuevo.get('nombre_mercadona', ''),
                'problema': f"Categoría '{cat}' no existe"
            })
        elif subcat not in categorias_validas.get(cat, []):
            categorias_invalidas.append({
                'fila': i+2,
                'nombre': nuevo.get('nombre_mercadona', ''),
                'problema': f"Subcategoría '{subcat}' no existe en '{cat}'"
            })
    
    if categorias_invalidas:
        print(f"\n❌ CATEGORÍAS INVÁLIDAS ENCONTRADAS: {len(categorias_invalidas)}\n")
        for error in categorias_invalidas:
            print(f"  Fila {error['fila']}: {error['nombre']}")
            print(f"    └─ {error['problema']}")
        print(f"\n⚠️ ACCIÓN REQUERIDA: Corregir categorías antes de importar")
    else:
        print(f"\n✅ Todas las categorías son válidas")
    
    # ==========================================================================
    # ANÁLISIS 2: DUPLICADOS EXACTOS Y SIMILARES
    # ==========================================================================
    
    print("\n" + "="*80)
    print("2️⃣ DETECCIÓN DE DUPLICADOS")
    print("="*80)
    
    duplicados_exactos = []
    duplicados_similares = []
    
    for i, nuevo in enumerate(nuevos):
        nombre_nuevo = nuevo.get('nombre_mercadona', '').lower()
        precio_nuevo = normalizar_precio(nuevo.get('precio', ''))
        
        for actual in actuales:
            nombre_actual = actual.get('nombre', '').lower()
            precio_actual = normalizar_precio(actual.get('precio', ''))
            
            # Duplicado exacto (mismo nombre)
            if nombre_nuevo == nombre_actual:
                duplicados_exactos.append({
                    'fila': i+2,
                    'nombre_nuevo': nuevo.get('nombre_mercadona', ''),
                    'precio_nuevo': nuevo.get('precio', ''),
                    'id_existente': actual.get('id_producto', ''),
                    'nombre_existente': actual.get('nombre', ''),
                    'precio_existente': actual.get('precio', ''),
                    'misma_categoria': (
                        nuevo.get('categoria', '') == actual.get('categoria', '') and
                        nuevo.get('subcategoria', '') == actual.get('subcategoria', '')
                    )
                })
                break
            
            # Duplicado similar (85%+ parecido)
            similitud = similitud_textos(nombre_nuevo, nombre_actual)
            if similitud >= UMBRAL_SIMILITUD and nombre_nuevo != nombre_actual:
                duplicados_similares.append({
                    'fila': i+2,
                    'nombre_nuevo': nuevo.get('nombre_mercadona', ''),
                    'nombre_existente': actual.get('nombre', ''),
                    'id_existente': actual.get('id_producto', ''),
                    'similitud': similitud * 100
                })
                break
    
    # Mostrar duplicados exactos
    if duplicados_exactos:
        print(f"\n⚠️ DUPLICADOS EXACTOS ENCONTRADOS: {len(duplicados_exactos)}\n")
        for dup in duplicados_exactos:
            print(f"  Fila {dup['fila']}: {dup['nombre_nuevo']}")
            print(f"    ├─ YA EXISTE: {dup['id_existente']} - {dup['nombre_existente']}")
            print(f"    ├─ Precio nuevo: {dup['precio_nuevo']} | Existente: {dup['precio_existente']}")
            
            if dup['misma_categoria']:
                print(f"    └─ 🔴 DUPLICADO TOTAL - No importar")
            else:
                print(f"    └─ 🟡 MISMO NOMBRE, distinta categoría - Revisar")
        
        print(f"\n⚠️ ACCIÓN SUGERIDA:")
        print(f"  - Eliminar filas duplicadas del CSV")
        print(f"  - O usar Opción 2 para actualizar precios/categorías")
    else:
        print(f"\n✅ No se encontraron duplicados exactos")
    
    # Mostrar duplicados similares
    if duplicados_similares:
        print(f"\n🟡 DUPLICADOS SIMILARES ENCONTRADOS: {len(duplicados_similares)}\n")
        for dup in duplicados_similares:
            print(f"  Fila {dup['fila']}: {dup['nombre_nuevo']}")
            print(f"    ├─ Parecido a: {dup['id_existente']} - {dup['nombre_existente']}")
            print(f"    └─ Similitud: {dup['similitud']:.1f}%")
        
        print(f"\n⚠️ ACCIÓN SUGERIDA:")
        print(f"  - Revisar manualmente si son el mismo producto")
        print(f"  - Ajustar nombres para que coincidan o sean distintos")
    else:
        print(f"\n✅ No se encontraron duplicados similares")
    
    # ==========================================================================
    # ANÁLISIS 3: PRODUCTOS TOTALMENTE NUEVOS
    # ==========================================================================
    
    print("\n" + "="*80)
    print("3️⃣ PRODUCTOS TOTALMENTE NUEVOS")
    print("="*80)
    
    nombres_actuales = {p.get('nombre', '').lower() for p in actuales}
    productos_nuevos = []
    
    for i, nuevo in enumerate(nuevos):
        nombre_nuevo = nuevo.get('nombre_mercadona', '').lower()
        
        if nombre_nuevo not in nombres_actuales:
            # Verificar que no sea similar a ninguno
            es_totalmente_nuevo = True
            
            for actual in actuales:
                nombre_actual = actual.get('nombre', '').lower()
                if similitud_textos(nombre_nuevo, nombre_actual) >= UMBRAL_SIMILITUD:
                    es_totalmente_nuevo = False
                    break
            
            if es_totalmente_nuevo:
                productos_nuevos.append({
                    'fila': i+2,
                    'nombre': nuevo.get('nombre_mercadona', ''),
                    'precio': nuevo.get('precio', ''),
                    'categoria': nuevo.get('categoria', ''),
                    'subcategoria': nuevo.get('subcategoria', '')
                })
    
    if productos_nuevos:
        print(f"\n✅ PRODUCTOS TOTALMENTE NUEVOS: {len(productos_nuevos)}\n")
        
        # Mostrar solo primeros 10
        for prod in productos_nuevos[:10]:
            print(f"  Fila {prod['fila']}: {prod['nombre']}")
            print(f"    └─ {prod['precio']} | {prod['categoria']} → {prod['subcategoria']}")
        
        if len(productos_nuevos) > 10:
            print(f"\n  ... y {len(productos_nuevos) - 10} productos más")
        
        print(f"\n✅ ACCIÓN: Estos productos se pueden importar sin problemas")
    else:
        print(f"\n⚠️ No hay productos totalmente nuevos")
        print(f"   Todos los productos ya existen o son muy similares a existentes")
    
    # ==========================================================================
    # ANÁLISIS 4: FORMATO DE PRECIOS
    # ==========================================================================
    
    print("\n" + "="*80)
    print("4️⃣ VALIDACIÓN DE PRECIOS")
    print("="*80)
    
    precios_invalidos = []
    
    for i, nuevo in enumerate(nuevos):
        precio = nuevo.get('precio', '')
        
        # Validar formato
        if not precio:
            precios_invalidos.append({
                'fila': i+2,
                'nombre': nuevo.get('nombre_mercadona', ''),
                'problema': 'Precio vacío'
            })
        elif not precio.endswith('€'):
            precios_invalidos.append({
                'fila': i+2,
                'nombre': nuevo.get('nombre_mercadona', ''),
                'problema': f"Precio '{precio}' debe terminar en €"
            })
        else:
            # Validar que sea número
            try:
                valor = float(precio.replace('€', '').replace(',', '.').strip())
                if valor <= 0:
                    precios_invalidos.append({
                        'fila': i+2,
                        'nombre': nuevo.get('nombre_mercadona', ''),
                        'problema': f"Precio '{precio}' debe ser mayor que 0"
                    })
            except ValueError:
                precios_invalidos.append({
                    'fila': i+2,
                    'nombre': nuevo.get('nombre_mercadona', ''),
                    'problema': f"Precio '{precio}' no es un número válido"
                })
    
    if precios_invalidos:
        print(f"\n❌ PRECIOS INVÁLIDOS: {len(precios_invalidos)}\n")
        for error in precios_invalidos:
            print(f"  Fila {error['fila']}: {error['nombre']}")
            print(f"    └─ {error['problema']}")
        
        print(f"\n⚠️ ACCIÓN REQUERIDA: Corregir precios antes de importar")
    else:
        print(f"\n✅ Todos los precios son válidos")
    
    # ==========================================================================
    # RESUMEN FINAL
    # ==========================================================================
    
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"  - Productos a importar: {len(nuevos)}")
    print(f"  - Productos totalmente nuevos: {len(productos_nuevos)}")
    print(f"  - Duplicados exactos: {len(duplicados_exactos)}")
    print(f"  - Duplicados similares: {len(duplicados_similares)}")
    print(f"  - Categorías inválidas: {len(categorias_invalidas)}")
    print(f"  - Precios inválidos: {len(precios_invalidos)}")
    
    print(f"\n🎯 RECOMENDACIÓN:")
    
    errores_criticos = len(categorias_invalidas) + len(precios_invalidos)
    
    if errores_criticos > 0:
        print(f"  ❌ NO IMPORTAR - Hay {errores_criticos} errores críticos que corregir")
        print(f"\n  Pasos a seguir:")
        print(f"    1. Corregir categorías inválidas")
        print(f"    2. Corregir precios inválidos")
        print(f"    3. Volver a ejecutar este análisis")
    
    elif len(duplicados_exactos) > 0:
        print(f"  ⚠️ REVISAR - Hay {len(duplicados_exactos)} duplicados exactos")
        print(f"\n  Opciones:")
        print(f"    A) Eliminar duplicados del CSV y volver a analizar")
        print(f"    B) Usar 'gestor_masivo.py' Opción 2 para actualizar productos existentes")
        print(f"    C) Usar 'gestor_masivo.py' Opción 4 para reemplazar categoría completa")
    
    elif len(duplicados_similares) > 0:
        print(f"  🟡 REVISAR - Hay {len(duplicados_similares)} duplicados similares")
        print(f"\n  Revisa manualmente y decide:")
        print(f"    - ¿Son el mismo producto? → Ajustar nombre para que coincida")
        print(f"    - ¿Son productos distintos? → Ajustar nombre para diferenciar")
    
    else:
        print(f"  ✅ LISTO PARA IMPORTAR")
        print(f"\n  Comando:")
        print(f"    python gestor_masivo.py")
        print(f"    Opción 1 → Añadir productos desde CSV")
        print(f"    Archivo: {archivo_csv}")
    
    print("\n" + "="*80)
    print()

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\n❌ Uso: python analizar_antes_importar.py archivo.csv\n")
        print("Ejemplo:")
        print("  python analizar_antes_importar.py productos_nuevos.csv")
        print()
    else:
        archivo = sys.argv[1]
        analizar_csv(archivo)
