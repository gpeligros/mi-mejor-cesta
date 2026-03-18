"""
IMPORTADOR MERCADONA - DEFINITIVO
Importa 4,524 productos con categorías fijas
"""
from supabase import create_client
import config
import json

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# =====================================================================
# MAPEO COMPLETO: Palabras → (Categoría, Subcategoría)
# =====================================================================
MAPEO = {
    # Bebidas
    'agua': ('Bebidas', 'Agua'),
    'cerveza': ('Bebidas', 'Cerveza'),
    'vino': ('Bebidas', 'Vino'),
    'tinto': ('Bebidas', 'Vino'),
    'blanco': ('Bebidas', 'Vino'),
    'rosado': ('Bebidas', 'Vino'),
    'cava': ('Bebidas', 'Vino'),
    'coca cola': ('Bebidas', 'Refrescos'),
    'fanta': ('Bebidas', 'Refrescos'),
    'sprite': ('Bebidas', 'Refrescos'),
    'aquarius': ('Bebidas', 'Refrescos'),
    'refresco': ('Bebidas', 'Refrescos'),
    'zumo': ('Bebidas', 'Zumos'),
    'nectar': ('Bebidas', 'Zumos'),
    'licor': ('Bebidas', 'Licores y destilados'),
    'whisky': ('Bebidas', 'Licores y destilados'),
    'ron': ('Bebidas', 'Licores y destilados'),
    'vodka': ('Bebidas', 'Licores y destilados'),
    'gin': ('Bebidas', 'Licores y destilados'),
    
    # Lácteos y Huevos
    'leche': ('Lácteos y Huevos', 'Leche y bebidas "lácteas"'),
    'yogur': ('Lácteos y Huevos', 'Yogures'),
    'queso': ('Lácteos y Huevos', 'Quesos'),
    'mantequilla': ('Lácteos y Huevos', 'Mantequillas y Natas'),
    'nata': ('Lácteos y Huevos', 'Mantequillas y Natas'),
    'huevo': ('Lácteos y Huevos', 'Huevos'),
    'flan': ('Lácteos y Huevos', 'Postres lácteos'),
    'natillas': ('Lácteos y Huevos', 'Postres lácteos'),
    
    # Carnicería
    'pollo': ('Carnicería y Charcutería', 'Pollo'),
    'pechuga': ('Carnicería y Charcutería', 'Pollo'),
    'pavo': ('Carnicería y Charcutería', 'Pavo'),
    'cerdo': ('Carnicería y Charcutería', 'Cerdo'),
    'ternera': ('Carnicería y Charcutería', 'Vacuno'),
    'cordero': ('Carnicería y Charcutería', 'Cordero'),
    'jamon': ('Carnicería y Charcutería', 'Charcuteria'),
    'chorizo': ('Carnicería y Charcutería', 'Charcuteria'),
    'salchichon': ('Carnicería y Charcutería', 'Charcuteria'),
    'hamburguesa': ('Carnicería y Charcutería', 'Carne preparada'),
    
    # Pescadería
    'salmon': ('Pescadería', 'Pescado'),
    'merluza': ('Pescadería', 'Pescado'),
    'bacalao': ('Pescadería', 'Pescado'),
    'pescado': ('Pescadería', 'Pescado'),
    'gamba': ('Pescadería', 'Marisco'),
    'langostino': ('Pescadería', 'Marisco'),
    'pulpo': ('Pescadería', 'Moluscos'),
    'calamar': ('Pescadería', 'Moluscos'),
    'mejillon': ('Pescadería', 'Moluscos'),
    
    # Frutas y Verduras
    'manzana': ('Frutas y Verduras', 'Fruta'),
    'platano': ('Frutas y Verduras', 'Fruta'),
    'naranja': ('Frutas y Verduras', 'Fruta'),
    'pera': ('Frutas y Verduras', 'Fruta'),
    'uva': ('Frutas y Verduras', 'Fruta'),
    'fresa': ('Frutas y Verduras', 'Fruta'),
    'melon': ('Frutas y Verduras', 'Fruta'),
    'kiwi': ('Frutas y Verduras', 'Fruta'),
    'tomate': ('Frutas y Verduras', 'Verduras'),
    'lechuga': ('Frutas y Verduras', 'Verduras'),
    'patata': ('Frutas y Verduras', 'Verduras'),
    'cebolla': ('Frutas y Verduras', 'Verduras'),
    'zanahoria': ('Frutas y Verduras', 'Verduras'),
    'pepino': ('Frutas y Verduras', 'Verduras'),
    'pimiento': ('Frutas y Verduras', 'Verduras'),
    'calabacin': ('Frutas y Verduras', 'Verduras'),
    'champiñon': ('Frutas y Verduras', 'Setas'),
    'seta': ('Frutas y Verduras', 'Setas'),
    
    # Panadería
    'pan': ('Panadería y Pastelería', 'Pan fresco'),
    'barra': ('Panadería y Pastelería', 'Pan fresco'),
    'croissant': ('Panadería y Pastelería', 'Bollos'),
    'magdalena': ('Panadería y Pastelería', 'Bollos'),
    'bollo': ('Panadería y Pastelería', 'Bollos'),
    'tarta': ('Panadería y Pastelería', 'Pasteles y Tartas'),
    'pastel': ('Panadería y Pastelería', 'Pasteles y Tartas'),
    
    # Despensa
    'aceite': ('Despensa', 'Aceites'),
    'arroz': ('Despensa', 'Arroz, pasta y quinoa'),
    'pasta': ('Despensa', 'Arroz, pasta y quinoa'),
    'macarron': ('Despensa', 'Arroz, pasta y quinoa'),
    'espagueti': ('Despensa', 'Arroz, pasta y quinoa'),
    'azucar': ('Despensa', 'Azúcares y edulcorantes'),
    'sal': ('Despensa', 'Sales'),
    'vinagre': ('Despensa', 'Vinagres'),
    'harina': ('Despensa', 'Harinas'),
    'lenteja': ('Despensa', 'Legumbres secas'),
    'garbanzo': ('Despensa', 'Legumbres secas'),
    'alubia': ('Despensa', 'Legumbres secas'),
    'salsa': ('Despensa', 'Salsas, caldos y condimentos preparados'),
    'tomate frito': ('Despensa', 'Salsas, caldos y condimentos preparados'),
    'ketchup': ('Despensa', 'Salsas, caldos y condimentos preparados'),
    'mayonesa': ('Despensa', 'Salsas, caldos y condimentos preparados'),
    
    # Desayuno y Snack
    'cafe': ('Desayuno y Snack', 'Café y cacaos'),
    'te ': ('Desayuno y Snack', 'Té e infusiones'),
    'infusion': ('Desayuno y Snack', 'Té e infusiones'),
    'galleta': ('Desayuno y Snack', 'Galletas dulces'),
    'cereales': ('Desayuno y Snack', 'Cereales para desayuno'),
    'mermelada': ('Desayuno y Snack', 'Mermelada y Miel'),
    'miel': ('Desayuno y Snack', 'Mermelada y Miel'),
    'chocolate': ('Desayuno y Snack', 'Cremas'),
    'nocilla': ('Desayuno y Snack', 'Cremas'),
    'patatas fritas': ('Desayuno y Snack', 'Snack salados'),
    'almendra': ('Desayuno y Snack', 'Frutos secos embasados'),
    'nuez': ('Desayuno y Snack', 'Frutos secos embasados'),
    
    # Conservas
    'atun': ('Conservas y Enlatados', 'Conservas de pescado y mariscos'),
    'sardina': ('Conservas y Enlatados', 'Conservas de pescado y mariscos'),
    'bonito': ('Conservas y Enlatados', 'Conservas de pescado y mariscos'),
    'esparrago': ('Conservas y Enlatados', 'Verduras, legumbres y hortalizas en conserva'),
    'alcachofa': ('Conservas y Enlatados', 'Verduras, legumbres y hortalizas en conserva'),
    
    # Congelados
    'helado': ('Congelados', 'Helados y postres congelados'),
    'pizza': ('Congelados', 'Platos congelados preparados'),
    'congelad': ('Congelados', 'Verduras congeladas'),
    
    # Higiene
    'gel de ducha': ('Cuidado personal e Higiene', 'Higiene corporal'),
    'gel baño': ('Cuidado personal e Higiene', 'Higiene corporal'),
    'jabon': ('Cuidado personal e Higiene', 'Higiene corporal'),
    'champu': ('Cuidado personal e Higiene', 'Cuidado del cabello'),
    'acondicionador': ('Cuidado personal e Higiene', 'Cuidado del cabello'),
    'pasta de dientes': ('Cuidado personal e Higiene', 'Higiene bucal'),
    'cepillo dental': ('Cuidado personal e Higiene', 'Higiene bucal'),
    'desodorante': ('Cuidado personal e Higiene', 'Desodorantes'),
    'crema facial': ('Cuidado personal e Higiene', 'Cremas y protectores'),
    
    # Hogar
    'detergente': ('Hogar', 'Detergentes para ropa'),
    'lavavajillas': ('Hogar', 'Lavavajillas'),
    'lejia': ('Hogar', 'Lejia y desinfectantes'),
    'fregasuelos': ('Hogar', 'Limpiadores de superficie'),
    'suavizante': ('Hogar', 'Suavizantes'),
    
    # Bebés
    'pañal': ('Bebes', 'Pañales'),
    'toallita': ('Bebes', 'Toallitas y algodón'),
    
    # Mascotas
    'comida perro': ('Mascotas', 'Comida para perros'),
    'comida gato': ('Mascotas', 'Comida para gatos'),
}

def mapear_categoria(nombre):
    """Mapea producto a categoría basado en palabras clave"""
    nombre_lower = nombre.lower()
    
    # Buscar coincidencias
    for palabra, (cat, subcat) in MAPEO.items():
        if palabra in nombre_lower:
            return cat, subcat
    
    # Por defecto
    return 'Bazar y Varios', 'Otros bazar'

# =====================================================================
# MAIN - IMPORTACIÓN
# =====================================================================
print("="*70)
print("IMPORTADOR MERCADONA - 4,524 PRODUCTOS")
print("="*70)

# Leer JSON
print("\nLeyendo mercadona.json...")
with open('mercadona.json', 'r', encoding='utf-8') as f:
    productos = json.load(f)

print(f"Total productos: {len(productos)}")

# Obtener contador
response = supabase.table('productos').select('id_producto').eq('supermercado', 'Mercadona').execute()
contador = 1
if response.data:
    ids = [int(p['id_producto'].split('-')[1]) for p in response.data if '-' in p['id_producto']]
    if ids:
        contador = max(ids) + 1

print(f"Empezando desde: ME-{contador:04d}")
print(f"\nInsertando productos...")

insertados = 0
errores = 0
sin_precio = 0

for prod in productos:
    try:
        nombre = prod.get('display_name', '')
        precio_data = prod.get('price_instructions', {})
        precio = float(precio_data.get('unit_price', 0))
        imagen = prod.get('thumbnail', '')
        url = prod.get('share_url', '')
        
        if not nombre:
            continue
        
        if precio <= 0:
            sin_precio += 1
            continue
        
        # Mapear categoría
        categoria, subcategoria = mapear_categoria(nombre)
        
        # ID único
        id_producto = f"ME-{contador:04d}"
        contador += 1
        
        # Insertar
        supabase.table('productos').insert({
            'id_producto': id_producto,
            'nombre': nombre,
            'supermercado': 'Mercadona',
            'precio': precio,
            'categoria': categoria,
            'subcategoria': subcategoria,
            'imagen': imagen,
            'url': url
        }).execute()
        
        insertados += 1
        
        if insertados % 500 == 0:
            print(f"  ✓ {insertados} productos insertados...")
        
        if insertados <= 5:
            print(f"  ✓ {nombre[:50]} → {categoria}/{subcategoria}")
    
    except Exception as e:
        if 'duplicate' not in str(e).lower() and 'unique' not in str(e).lower():
            errores += 1
            if errores <= 5:
                print(f"  ❌ Error: {e}")

print(f"\n{'='*70}")
print("IMPORTACIÓN COMPLETADA")
print(f"{'='*70}")
print(f"Total insertados: {insertados}")
print(f"Sin precio: {sin_precio}")
print(f"Errores: {errores}")

# Verificar distribución
print(f"\n{'='*70}")
print("DISTRIBUCIÓN POR CATEGORÍAS:")
print(f"{'='*70}")

response = supabase.table('productos').select('categoria').eq('supermercado', 'Mercadona').execute()

cats = {}
for p in response.data:
    cat = p.get('categoria', 'Sin categoría')
    cats[cat] = cats.get(cat, 0) + 1

for cat in sorted(cats.keys()):
    print(f"  {cat}: {cats[cat]} productos")

print(f"\n{'='*70}")
print("✅ APP LISTA PARA USAR")
print(f"{'='*70}")
