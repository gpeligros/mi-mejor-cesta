"""
ANÁLISIS Y CORRECCIÓN DE CATEGORÍAS MERCADONA
Identifica problemas y propone soluciones
"""
from supabase import create_client
import config
from collections import defaultdict

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

print("="*70)
print("ANÁLISIS DE CATEGORIZACIÓN MERCADONA")
print("="*70)

# Cargar solo Mercadona
response = supabase.table('productos_nuevos')\
    .select('*')\
    .eq('supermercado', 'Mercadona')\
    .execute()

productos = response.data
print(f"\nTotal Mercadona: {len(productos)}")

# Agrupar por categoría/subcategoría
categorias = defaultdict(lambda: defaultdict(list))

for p in productos:
    cat = p.get('categoria', 'Sin categoría')
    subcat = p.get('subcategoria', 'Sin subcategoría')
    categorias[cat][subcat].append(p)

# Mostrar estructura actual
print("\n" + "="*70)
print("ESTRUCTURA ACTUAL")
print("="*70)

total_bien_categorizado = 0
total_general = 0

for cat in sorted(categorias.keys()):
    subcats = categorias[cat]
    total_cat = sum(len(prods) for prods in subcats.values())
    
    if cat == 'General':
        total_general = total_cat
    else:
        total_bien_categorizado += total_cat
    
    print(f"\n{cat.upper()} ({total_cat} productos)")
    for subcat in sorted(subcats.keys()):
        prods = subcats[subcat]
        print(f"  └─ {subcat}: {len(prods)}")
        
        # Mostrar 3 ejemplos
        if len(prods) <= 5:
            for p in prods:
                print(f"      • {p['nombre'][:60]}")

porcentaje_ok = (total_bien_categorizado / len(productos) * 100)
porcentaje_general = (total_general / len(productos) * 100)

print("\n" + "="*70)
print("RESUMEN")
print("="*70)
print(f"Bien categorizados: {total_bien_categorizado} ({porcentaje_ok:.1f}%)")
print(f"'General/Otros': {total_general} ({porcentaje_general:.1f}%)")

# Análisis de "General/Otros"
if total_general > 0:
    print("\n" + "="*70)
    print("PRODUCTOS EN 'GENERAL/OTROS' (muestra)")
    print("="*70)
    
    general_prods = categorias['General']['Otros'][:50]
    
    for p in general_prods:
        print(f"  • {p['nombre']}")

print("\n" + "="*70)
print("RECOMENDACIONES")
print("="*70)

if porcentaje_general > 20:
    print("⚠️  Más del 20% en 'General/Otros'")
    print("   → Ejecuta: python MEJORAR_CATEGORIAS.py")
else:
    print("✅ Categorización aceptable")

print("\n¿Quieres ver productos específicos de alguna categoría?")
print("  python ANALIZAR_CATEGORIA.py <nombre_categoria>")
