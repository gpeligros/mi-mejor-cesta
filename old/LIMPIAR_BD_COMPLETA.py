"""
LIMPIEZA COMPLETA DE BD
1. Elimina duplicados (mantiene el más reciente)
2. Normaliza categorías automáticamente
3. Elimina productos basura (Lidl Alemania)
"""
from supabase import create_client
import config
from collections import defaultdict

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def mejorar_categoria(nombre):
    """Mejora la categorización basada en el nombre completo"""
    nombre_lower = nombre.lower()
    
    # Diccionario expandido
    categorias = {
        # Lácteos
        ('leche', 'lacteo'): ('Lácteos', 'Leche'),
        ('yogur', 'yoghurt'): ('Lácteos', 'Yogures'),
        ('queso', 'quesito'): ('Lácteos', 'Quesos'),
        ('mantequilla', 'margarina'): ('Lácteos', 'Mantequilla'),
        ('nata', 'crema'): ('Lácteos', 'Nata'),
        
        # Bebidas
        ('agua',): ('Bebidas', 'Agua'),
        ('refresco', 'cola', 'fanta', 'sprite', 'aquarius', 'nestea'): ('Bebidas', 'Refrescos'),
        ('cerveza', 'birra'): ('Bebidas', 'Cervezas'),
        ('vino', 'cava', 'champan'): ('Bebidas', 'Vinos'),
        ('zumo', 'nectar'): ('Bebidas', 'Zumos'),
        ('cafe', 'te ', 'infusion'): ('Bebidas', 'Cafés'),
        
        # Despensa
        ('aceite',): ('Despensa', 'Aceites'),
        ('arroz',): ('Despensa', 'Arroces'),
        ('pasta', 'macarron', 'espagueti', 'fideo'): ('Despensa', 'Pastas'),
        ('legumbre', 'lenteja', 'garbanzo', 'alubia'): ('Despensa', 'Legumbres'),
        ('conserva', 'lata', 'atun', 'sardina'): ('Despensa', 'Conservas'),
        ('sal ', 'pimienta', 'especias', 'condimento'): ('Despensa', 'Condimentos'),
        ('azucar', 'edulcorante', 'miel'): ('Despensa', 'Azúcar'),
        ('salsa', 'ketchup', 'mayonesa', 'mostaza'): ('Despensa', 'Salsas'),
        ('harina', 'levadura'): ('Despensa', 'Harinas'),
        
        # Panadería
        ('pan ',): ('Panadería', 'Pan'),
        ('galleta', 'cookie'): ('Panadería', 'Galletas'),
        ('bollo', 'magdalena', 'croissant', 'donut'): ('Panadería', 'Bollería'),
        ('tostada',): ('Panadería', 'Pan'),
        
        # Carnes
        ('pollo', 'pechuga'): ('Carnicería', 'Aves'),
        ('pavo',): ('Carnicería', 'Aves'),
        ('cerdo', 'lomo', 'costilla', 'chorizo'): ('Carnicería', 'Cerdo'),
        ('ternera', 'vaca', 'vacuno', 'buey'): ('Carnicería', 'Ternera'),
        ('cordero',): ('Carnicería', 'Cordero'),
        ('carne picada', 'hamburguesa'): ('Carnicería', 'Carnes'),
        
        # Charcutería
        ('jamon',): ('Charcutería', 'Jamón'),
        ('salchichon', 'fuet', 'salami'): ('Charcutería', 'Embutidos'),
        
        # Pescado
        ('pescado', 'merluza', 'salmon', 'bacalao', 'dorada', 'lubina'): ('Pescadería', 'Pescados'),
        ('marisco', 'gambas', 'langostino', 'mejillon'): ('Pescadería', 'Mariscos'),
        
        # Frutas y Verduras
        ('manzana', 'platano', 'naranja', 'pera', 'uva', 'melon', 'sandia', 'fruta', 'kiwi', 'limon'): ('Frutas y Verduras', 'Frutas'),
        ('patata', 'tomate', 'lechuga', 'cebolla', 'zanahoria', 'pepino', 'pimiento', 'verdura', 'espinaca', 'brocoli', 'coliflor'): ('Frutas y Verduras', 'Verduras'),
        ('ensalada',): ('Frutas y Verduras', 'Verduras'),
        
        # Congelados
        ('helado', 'polo', 'glace'): ('Congelados', 'Helados'),
        ('pizza',): ('Congelados', 'Pizzas'),
        ('congelad',): ('Congelados', 'Congelados'),
        
        # Huevos
        ('huevo',): ('Lácteos', 'Huevos'),
        
        # Higiene
        ('champu', 'gel de ducha', 'jabon', 'gel ducha'): ('Higiene', 'Higiene corporal'),
        ('desodorante',): ('Higiene', 'Desodorantes'),
        ('pasta de dientes', 'cepillo dientes', 'enjuague'): ('Higiene', 'Higiene bucal'),
        ('crema', 'locion'): ('Higiene', 'Cuidado facial'),
        
        # Limpieza
        ('detergente', 'jabon ropa'): ('Limpieza', 'Detergentes'),
        ('lavavajillas',): ('Limpieza', 'Lavavajillas'),
        ('lejia', 'limpiador', 'fregasuelos'): ('Limpieza', 'Limpieza'),
        ('suavizante',): ('Limpieza', 'Suavizantes'),
        
        # Bebé
        ('panal', 'toallitas bebe'): ('Bebé', 'Pañales'),
        ('leche infantil', 'papilla'): ('Bebé', 'Alimentación'),
    }
    
    for palabras, (cat, subcat) in categorias.items():
        if any(p in nombre_lower for p in palabras):
            return cat, subcat
    
    return 'General', 'Otros'

print("="*70)
print("LIMPIEZA COMPLETA DE BASE DE DATOS")
print("="*70)

# PASO 1: Eliminar productos basura (Lidl Alemania, etc)
print("\n[1/4] Eliminando productos basura...")
response = supabase.table('productos_nuevos').select('*').execute()
productos = response.data

basura = []
for p in productos:
    nombre = p['nombre'].lower()
    # Detectar productos alemanes o no alimentarios
    if any(palabra in nombre for palabra in ['bad-', 'spiegelschrank', 'toiletten', 'schrank', 'möbel']):
        basura.append(p['id_producto'])

if basura:
    for pid in basura:
        supabase.table('productos_nuevos').delete().eq('id_producto', pid).execute()
    print(f"  ✓ Eliminados {len(basura)} productos basura")
else:
    print("  ✓ Sin productos basura")

# PASO 2: Eliminar duplicados (mantener el más reciente)
print("\n[2/4] Eliminando duplicados...")
response = supabase.table('productos_nuevos').select('*').execute()
productos = response.data

# Agrupar por nombre + supermercado
grupos = defaultdict(list)
for p in productos:
    key = f"{p['nombre']}_{p['supermercado']}"
    grupos[key].append(p)

eliminados = 0
for key, prods in grupos.items():
    if len(prods) > 1:
        # Ordenar por ID (más reciente = ID mayor)
        prods_sorted = sorted(prods, key=lambda x: x['id'], reverse=True)
        mantener = prods_sorted[0]
        
        # Eliminar los demás
        for p in prods_sorted[1:]:
            supabase.table('productos_nuevos').delete().eq('id', p['id']).execute()
            eliminados += 1

print(f"  ✓ Eliminados {eliminados} duplicados")

# PASO 3: Recategorizar productos mal categorizados
print("\n[3/4] Mejorando categorización...")
response = supabase.table('productos_nuevos').select('*').execute()
productos = response.data

recategorizados = 0
for p in productos:
    cat_actual = p.get('categoria')
    subcat_actual = p.get('subcategoria')
    
    # Si está en General/Otros, intentar mejorar
    if cat_actual == 'General' or subcat_actual == 'Otros':
        cat_nueva, subcat_nueva = mejorar_categoria(p['nombre'])
        
        if cat_nueva != 'General':
            supabase.table('productos_nuevos')\
                .update({
                    'categoria': cat_nueva,
                    'subcategoria': subcat_nueva
                })\
                .eq('id_producto', p['id_producto'])\
                .execute()
            recategorizados += 1

print(f"  ✓ Recategorizados {recategorizados} productos")

# PASO 4: Verificar resultado
print("\n[4/4] Verificando resultado...")
response = supabase.table('productos_nuevos').select('*').execute()
productos = response.data

# Contar por supermercado
supers = defaultdict(int)
for p in productos:
    supers[p['supermercado']] += 1

print(f"\n{'='*70}")
print("RESULTADO FINAL")
print(f"{'='*70}")
print(f"Total productos: {len(productos)}")
for super_name, count in sorted(supers.items()):
    print(f"  {super_name}: {count}")

# Contar categorías
cats = defaultdict(int)
for p in productos:
    cats[p.get('categoria', 'Sin categoría')] += 1

print(f"\nCategorías: {len(cats)}")
for cat in sorted(cats.keys()):
    print(f"  {cat}: {cats[cat]}")

general = cats.get('General', 0)
porcentaje = (general / len(productos) * 100) if len(productos) > 0 else 0
print(f"\n⚠️  'General/Otros': {general} ({porcentaje:.1f}%)")

print(f"\n{'='*70}")
print("✅ LIMPIEZA COMPLETADA")
print(f"{'='*70}")