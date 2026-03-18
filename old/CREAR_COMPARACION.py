"""
CREAR COMPARACIÓN DE PRECIOS
Agrupa productos equivalentes de diferentes supermercados
"""
from supabase import create_client
import config
from collections import defaultdict
import re

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def normalizar_nombre(nombre):
    """Normaliza nombre para comparación"""
    # Quitar marcas blancas
    nombre = re.sub(r'\b(Hacendado|Milbona|Carrefour|Dia)\b', '', nombre, flags=re.IGNORECASE)
    
    # Quitar palabras comunes
    nombre = re.sub(r'\b(marca|eco|bio|selección|pack|envase|botella)\b', '', nombre, flags=re.IGNORECASE)
    
    # Normalizar espacios
    nombre = ' '.join(nombre.split())
    
    return nombre.lower().strip()

def extraer_formato(nombre):
    """Extrae formato (1L, 500g, etc)"""
    match = re.search(r'(\d+[.,]?\d*\s*[LlKkGgMm][LlGg]?)', nombre)
    if match:
        formato = match.group(1).upper().replace(',', '.')
        # Normalizar: 1L, 1.5L, 500G, 1KG
        return formato
    return ''

def productos_son_equivalentes(p1, p2):
    """Determina si dos productos son equivalentes"""
    # Diferentes supermercados (obligatorio)
    if p1['supermercado'] == p2['supermercado']:
        return False
    
    # Misma categoría (obligatorio)
    if p1.get('categoria') != p2.get('categoria'):
        return False
    
    # Mismo formato (si existe)
    f1 = extraer_formato(p1['nombre'])
    f2 = extraer_formato(p2['nombre'])
    
    if f1 and f2 and f1 != f2:
        return False
    
    # Nombres normalizados similares
    n1 = normalizar_nombre(p1['nombre'])
    n2 = normalizar_nombre(p2['nombre'])
    
    if not n1 or not n2:
        return False
    
    # Palabras comunes
    palabras1 = set(n1.split())
    palabras2 = set(n2.split())
    
    comunes = palabras1 & palabras2
    union = palabras1 | palabras2
    
    if not union:
        return False
    
    similaridad = len(comunes) / len(union)
    
    return similaridad >= 0.6  # 60% de palabras en común

def generar_grupo_id(producto):
    """Genera ID de grupo desde producto"""
    nombre_norm = normalizar_nombre(producto['nombre'])
    formato = extraer_formato(producto['nombre'])
    
    # Tomar primeras 3 palabras
    palabras = nombre_norm.split()[:3]
    base = '_'.join(palabras)
    
    # Añadir formato si existe
    if formato:
        base += f'_{formato}'
    
    # Limpiar caracteres especiales
    base = re.sub(r'[^a-z0-9_]', '', base)
    
    return base.upper()[:50]

print("="*70)
print("CREANDO COMPARACIÓN DE PRECIOS")
print("="*70)

# PASO 1: Limpiar grupos anteriores
print("\n[1/4] Limpiando grupos anteriores...")
try:
    supabase.table('productos_en_grupos').delete().neq('id', 0).execute()
    supabase.table('productos_grupos').delete().neq('id', 0).execute()
    print("  ✓ Grupos limpiados")
except Exception as e:
    print(f"  Advertencia: {e}")

# PASO 2: Cargar productos
print("\n[2/4] Cargando productos...")
response = supabase.table('productos_nuevos').select('*').execute()
productos = response.data
print(f"  Total productos: {len(productos)}")

# Filtrar solo Mercadona (tiene más productos)
mercadona = [p for p in productos if p['supermercado'] == 'Mercadona']
otros = [p for p in productos if p['supermercado'] != 'Mercadona']

print(f"  Mercadona: {len(mercadona)}")
print(f"  Otros: {len(otros)}")

# PASO 3: Crear grupos
print("\n[3/4] Creando grupos de productos equivalentes...")
grupos_creados = 0
relaciones = 0
procesados = set()

for prod_merc in mercadona:
    if prod_merc['id_producto'] in procesados:
        continue
    
    # Buscar equivalentes en otros supers
    equivalentes = [prod_merc]
    
    for prod_otro in otros:
        if prod_otro['id_producto'] in procesados:
            continue
        
        if productos_son_equivalentes(prod_merc, prod_otro):
            equivalentes.append(prod_otro)
            procesados.add(prod_otro['id_producto'])
    
    # Solo crear grupo si hay productos de 2+ supermercados
    supers_unicos = set(p['supermercado'] for p in equivalentes)
    
    if len(supers_unicos) >= 2:
        # Generar grupo_id
        grupo_id = generar_grupo_id(prod_merc)
        
        # Nombre del grupo (sin marca)
        nombre_grupo = normalizar_nombre(prod_merc['nombre'])
        formato = extraer_formato(prod_merc['nombre'])
        if formato:
            nombre_grupo = f"{nombre_grupo} {formato}"
        
        try:
            # Crear grupo
            supabase.table('productos_grupos').insert({
                'grupo_id': grupo_id,
                'nombre_grupo': nombre_grupo.title(),
                'categoria': prod_merc.get('categoria'),
                'subcategoria': prod_merc.get('subcategoria'),
                'formato': formato,
                'num_productos': len(equivalentes)
            }).execute()
            
            grupos_creados += 1
            
            # Crear relaciones
            for i, prod in enumerate(equivalentes):
                try:
                    supabase.table('productos_en_grupos').insert({
                        'grupo_id': grupo_id,
                        'id_producto': prod['id_producto'],
                        'confianza': 100,
                        'es_principal': (i == 0)
                    }).execute()
                    relaciones += 1
                except:
                    pass
            
            procesados.add(prod_merc['id_producto'])
            
            if grupos_creados <= 5:
                print(f"  ✓ {nombre_grupo.title()} ({len(equivalentes)} productos)")
        
        except Exception as e:
            if 'duplicate' not in str(e).lower():
                print(f"  Error: {e}")

    if grupos_creados % 50 == 0 and grupos_creados > 0:
        print(f"  Procesados: {grupos_creados} grupos...")

# PASO 4: Mostrar resultado
print(f"\n[4/4] Resultado...")

print(f"\n{'='*70}")
print("COMPARACIÓN CREADA")
print(f"{'='*70}")
print(f"Grupos creados: {grupos_creados}")
print(f"Relaciones creadas: {relaciones}")
if grupos_creados > 0:
    print(f"Productos por grupo (media): {relaciones/grupos_creados:.1f}")
print(f"{'='*70}")

if grupos_creados == 0:
    print("\n⚠️  NO SE CREARON GRUPOS")
    print("\nPosibles causas:")
    print("  - Solo hay productos de 1 supermercado")
    print("  - Los nombres son muy diferentes")
    print("  - Las categorías no coinciden")
else:
    print("\n✅ COMPARACIÓN LISTA")
    print("\nPrueba en tu app:")
    print("  - Busca un producto")
    print("  - Verás precios de diferentes supers")
    print("  - El más barato aparecerá destacado")
