"""
RECREAR GRUPOS CORRECTAMENTE
Borra grupos anteriores y crea nuevos BIEN
"""
from supabase import create_client
import config
from collections import defaultdict
import re

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def normalizar_nombre(nombre):
    """Genera ID de grupo desde nombre"""
    # Quitar marcas
    nombre = re.sub(r'\b(Hacendado|Milbona|Carrefour|Dia|Aldi|Bosque Verde)\b', '', nombre, flags=re.IGNORECASE)
    # Normalizar
    nombre = nombre.upper().strip()
    nombre = re.sub(r'\s+', '_', nombre)
    nombre = re.sub(r'[^A-Z0-9_]', '', nombre)
    return nombre[:50]

def extraer_formato(nombre):
    """Extrae formato (1L, 500g, etc)"""
    match = re.search(r'(\d+[.,]?\d*\s*[LlKkGgMm][LlGg]?)', nombre)
    return match.group(1).upper().replace(',', '.') if match else ''

def productos_son_similares(nombre1, nombre2):
    """Verifica si dos productos son similares SIN IA"""
    # Quitar marcas
    n1 = re.sub(r'\b(Hacendado|Milbona|Carrefour|Dia|Aldi)\b', '', nombre1, flags=re.IGNORECASE)
    n2 = re.sub(r'\b(Hacendado|Milbona|Carrefour|Dia|Aldi)\b', '', nombre2, flags=re.IGNORECASE)
    
    # Normalizar
    n1 = n1.lower().strip()
    n2 = n2.lower().strip()
    
    # Quitar palabras comunes
    for palabra in ['pack', 'envase', 'botella', 'paquete']:
        n1 = n1.replace(palabra, '')
        n2 = n2.replace(palabra, '')
    
    n1 = ' '.join(n1.split())
    n2 = ' '.join(n2.split())
    
    # Verificar formatos
    f1 = extraer_formato(nombre1)
    f2 = extraer_formato(nombre2)
    
    if f1 and f2 and f1 != f2:
        return False  # Diferentes formatos
    
    # Similaridad básica
    palabras1 = set(n1.split())
    palabras2 = set(n2.split())
    
    if not palabras1 or not palabras2:
        return False
    
    # Calcular intersección
    comunes = palabras1 & palabras2
    union = palabras1 | palabras2
    
    if not union:
        return False
    
    similaridad = len(comunes) / len(union)
    
    return similaridad >= 0.7

def recrear_grupos():
    print("="*70)
    print("RECREAR GRUPOS CORRECTAMENTE")
    print("="*70)
    
    # PASO 1: Borrar grupos anteriores
    print("\n[1/4] Borrando grupos anteriores...")
    try:
        supabase.table('productos_en_grupos').delete().neq('id', 0).execute()
        supabase.table('productos_grupos').delete().neq('id', 0).execute()
        print("  ✓ Grupos borrados")
    except Exception as e:
        print(f"  Error: {e}")
    
    # PASO 2: Cargar productos
    print("\n[2/4] Cargando productos...")
    response = supabase.table('productos_nuevos').select('*').execute()
    productos = response.data
    print(f"  Total productos: {len(productos)}")
    
    # Agrupar por supermercado + categoría + formato
    print("\n[3/4] Agrupando productos...")
    agrupados = defaultdict(list)
    
    for prod in productos:
        cat = prod.get('categoria', 'General')
        formato = extraer_formato(prod['nombre'])
        super_name = prod.get('supermercado', 'Desconocido')
        
        # Clave ÚNICA por categoría + formato + supermercado
        clave = f"{cat}_{formato}_{super_name}"
        agrupados[clave].append(prod)
    
    print(f"  Pre-grupos: {len(agrupados)}")
    
    # PASO 3: Crear grupos finales
    print("\n[4/4] Creando grupos finales...")
    grupos_creados = 0
    relaciones = 0
    procesados = set()
    
    for clave, prods in agrupados.items():
        if len(prods) < 1:
            continue
        
        # Tomar primer producto como referencia
        prod_ref = prods[0]
        
        if prod_ref['id_producto'] in procesados:
            continue
        
        # Generar ID de grupo
        nombre_limpio = re.sub(r'\b(Hacendado|Milbona|Carrefour|Dia|Aldi)\b', '', 
                              prod_ref['nombre'], flags=re.IGNORECASE).strip()
        
        grupo_id = normalizar_nombre(nombre_limpio)
        formato = extraer_formato(prod_ref['nombre'])
        
        # Buscar productos equivalentes en OTROS supermercados
        productos_grupo = [prod_ref]
        super_ref = prod_ref['supermercado']
        
        # Buscar en otros grupos
        for otra_clave, otros_prods in agrupados.items():
            if otra_clave == clave:
                continue
            
            for otro_prod in otros_prods:
                if otro_prod['id_producto'] in procesados:
                    continue
                
                # Mismo super? Skip
                if otro_prod['supermercado'] == super_ref:
                    continue
                
                # Misma categoría?
                if otro_prod.get('categoria') != prod_ref.get('categoria'):
                    continue
                
                # Productos similares?
                if productos_son_similares(prod_ref['nombre'], otro_prod['nombre']):
                    productos_grupo.append(otro_prod)
                    procesados.add(otro_prod['id_producto'])
        
        # Solo crear grupo si hay productos de diferentes supers
        supers_unicos = set(p['supermercado'] for p in productos_grupo)
        
        if len(supers_unicos) >= 2:  # Al menos 2 supermercados diferentes
            try:
                # Crear grupo
                supabase.table('productos_grupos').insert({
                    'grupo_id': grupo_id,
                    'nombre_grupo': nombre_limpio[:100],
                    'categoria': prod_ref.get('categoria'),
                    'formato': formato,
                    'num_productos': len(productos_grupo)
                }).execute()
                
                grupos_creados += 1
                
                # Crear relaciones
                for i, prod in enumerate(productos_grupo):
                    try:
                        supabase.table('productos_en_grupos').insert({
                            'grupo_id': grupo_id,
                            'id_producto': prod['id_producto'],
                            'confianza': 100,
                            'es_principal': (i == 0)
                        }).execute()
                        relaciones += 1
                        procesados.add(prod['id_producto'])
                    except:
                        pass
                
            except Exception as e:
                if 'duplicate' not in str(e).lower():
                    print(f"  Error: {e}")
    
    print(f"\n{'='*70}")
    print("RECREACIÓN COMPLETADA")
    print(f"{'='*70}")
    print(f"Grupos creados: {grupos_creados}")
    print(f"Relaciones creadas: {relaciones}")
    if grupos_creados > 0:
        print(f"Productos por grupo (media): {relaciones/grupos_creados:.1f}")
    print(f"{'='*70}")
    
    # Mostrar ejemplos
    if grupos_creados > 0:
        print("\n" + "="*70)
        print("EJEMPLOS DE GRUPOS:")
        print("="*70)
        
        ejemplos = supabase.table('productos_grupos').select('*').limit(5).execute()
        
        for grupo in ejemplos.data:
            print(f"\n[{grupo['grupo_id']}]")
            print(f"  {grupo['nombre_grupo']}")
            print(f"  Categoría: {grupo['categoria']}")
            
            # Productos del grupo
            rel = supabase.table('productos_en_grupos')\
                .select('id_producto')\
                .eq('grupo_id', grupo['grupo_id'])\
                .execute()
            
            for r in rel.data[:3]:
                prod = supabase.table('productos_nuevos')\
                    .select('*')\
                    .eq('id_producto', r['id_producto'])\
                    .single()\
                    .execute()
                
                if prod.data:
                    p = prod.data
                    print(f"    - {p['supermercado']}: {p['nombre'][:50]} ({p.get('precio', 0)}€)")

if __name__ == "__main__":
    print("\n⚠️  Este script va a:")
    print("  1. BORRAR todos los grupos anteriores")
    print("  2. Crear grupos CORRECTAMENTE")
    print("  3. Solo agrupar productos MUY similares")
    print("  4. Solo agrupar productos de DIFERENTES supermercados\n")
    
    confirmar = input("¿Continuar? (s/n): ")
    if confirmar.lower() == 's':
        recrear_grupos()
        print("\n✅ SISTEMA LISTO PARA USAR")
    else:
        print("Cancelado")
