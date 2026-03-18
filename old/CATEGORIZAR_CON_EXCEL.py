"""
CATEGORIZADOR DEFINITIVO MERCADONA
Usa el Excel con categorías oficiales y mapea todos los productos
"""
from supabase import create_client
import config
import openpyxl
import re

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Cargar estructura del Excel
wb = openpyxl.load_workbook('productos_con_formato_generico.xlsx')
ws = wb.active

# Crear mapeo de palabras clave → categoría/subcategoría
MAPEO_CATEGORIAS = {}

for row in ws.iter_rows(min_row=2, values_only=True):
    if not row[0] or not row[1] or not row[2]:
        continue
    
    producto = row[0].strip().lower()
    categoria = row[1].strip()
    subcategoria = row[2].strip()
    
    # Extraer palabras clave del nombre del producto
    palabras = re.findall(r'\b\w+\b', producto)
    
    for palabra in palabras:
        if len(palabra) > 3:  # Solo palabras de 4+ letras
            if palabra not in MAPEO_CATEGORIAS:
                MAPEO_CATEGORIAS[palabra] = []
            
            MAPEO_CATEGORIAS[palabra].append((categoria, subcategoria, len(palabras)))

print("="*70)
print("CATEGORIZADOR MERCADONA - BASADO EN EXCEL")
print("="*70)
print(f"Palabras clave cargadas: {len(MAPEO_CATEGORIAS)}")

# Cargar productos de Mercadona
response = supabase.table('productos').select('*').eq('supermercado', 'Mercadona').execute()
productos = response.data

print(f"Productos Mercadona: {len(productos)}")

def encontrar_mejor_categoria(nombre):
    """Encuentra la mejor categoría para un producto"""
    nombre_lower = nombre.lower()
    palabras_producto = re.findall(r'\b\w+\b', nombre_lower)
    
    # Buscar coincidencias
    coincidencias = []
    
    for palabra in palabras_producto:
        if palabra in MAPEO_CATEGORIAS:
            for cat, subcat, peso in MAPEO_CATEGORIAS[palabra]:
                # Puntuación: más específico (menos palabras en el original) = mayor prioridad
                puntuacion = 1.0 / peso
                coincidencias.append((puntuacion, cat, subcat))
    
    if coincidencias:
        # Ordenar por puntuación
        coincidencias.sort(reverse=True)
        return coincidencias[0][1], coincidencias[0][2]
    
    return None, None

# Categorizar productos
print("\nCategorizando productos...")
categorizados = 0
sin_categoria = 0

for i, prod in enumerate(productos, 1):
    cat_nueva, subcat_nueva = encontrar_mejor_categoria(prod['nombre'])
    
    if cat_nueva:
        try:
            supabase.table('productos')\
                .update({
                    'categoria': cat_nueva,
                    'subcategoria': subcat_nueva
                })\
                .eq('id_producto', prod['id_producto'])\
                .execute()
            
            categorizados += 1
            
            if categorizados <= 10:
                print(f"  ✓ {prod['nombre'][:50]}")
                print(f"    → {cat_nueva} / {subcat_nueva}")
        
        except Exception as e:
            print(f"  Error: {e}")
    else:
        sin_categoria += 1
        
        # Poner en "General / Otros"
        try:
            supabase.table('productos')\
                .update({
                    'categoria': 'BAZAR Y VARIOS',
                    'subcategoria': 'Otros bazar'
                })\
                .eq('id_producto', prod['id_producto'])\
                .execute()
        except:
            pass
    
    if i % 500 == 0:
        print(f"  Procesados: {i}/{len(productos)}")

print(f"\n{'='*70}")
print("RESULTADO FINAL")
print(f"{'='*70}")
print(f"Categorizados: {categorizados}")
print(f"Sin categoría específica: {sin_categoria} (→ BAZAR Y VARIOS / Otros bazar)")
print(f"{'='*70}")

# Verificar distribución
print("\nDistribución por categorías:")
response = supabase.table('productos')\
    .select('categoria')\
    .eq('supermercado', 'Mercadona')\
    .execute()

cats = {}
for p in response.data:
    cat = p.get('categoria', 'Sin categoría')
    cats[cat] = cats.get(cat, 0) + 1

for cat in sorted(cats.keys()):
    print(f"  {cat}: {cats[cat]}")

print(f"\n{'='*70}")
print("✅ CATEGORIZACIÓN COMPLETADA")
print(f"{'='*70}")
