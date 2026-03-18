"""
MEJORAR CATEGORIZACIÓN INTELIGENTE
Usa análisis de texto avanzado para recategorizar
"""
from supabase import create_client
import config
import re

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Diccionario COMPLETO y ESPECÍFICO
REGLAS_CATEGORIZACION = {
    # === BEBIDAS ===
    'Bebidas': {
        'Agua': ['agua mineral', 'agua con gas', 'agua sin gas'],
        'Refrescos': ['coca cola', 'pepsi', 'fanta', 'sprite', 'aquarius', 'nestea', 'trina', 'kas', 'seven up', 'refresco'],
        'Cervezas': ['cerveza', 'birra', 'clara', 'radler', 'shandy'],
        'Vinos': ['vino tinto', 'vino blanco', 'vino rosado', 'cava', 'champan', 'espumoso'],
        'Zumos': ['zumo', 'nectar', 'jugo'],
        'Cafés': ['cafe', 'te negro', 'te verde', 'infusion', 'manzanilla', 'tila'],
    },
    
    # === LÁCTEOS ===
    'Lácteos': {
        'Leche': ['leche entera', 'leche semidesnatada', 'leche desnatada', 'leche sin lactosa', 'bebida de soja', 'bebida de avena', 'bebida vegetal'],
        'Yogures': ['yogur', 'yoghurt', 'kefir', 'bifidus'],
        'Quesos': ['queso', 'quesito', 'mozzarella', 'parmesano', 'manchego', 'emmental', 'cheddar', 'philadelphia'],
        'Mantequilla': ['mantequilla', 'margarina'],
        'Nata': ['nata', 'crema de leche'],
        'Huevos': ['huevo', 'huevos'],
    },
    
    # === DESPENSA ===
    'Despensa': {
        'Aceites': ['aceite de oliva', 'aceite de girasol', 'aceite vegetal'],
        'Arroces': ['arroz blanco', 'arroz integral', 'arroz basmati'],
        'Pastas': ['pasta', 'macarrones', 'espaguetis', 'tallarines', 'fideos', 'ravioli', 'tortellini'],
        'Legumbres': ['lentejas', 'garbanzos', 'alubias', 'judias'],
        'Conservas': ['atun', 'bonito', 'sardinas', 'mejillones', 'berberechos', 'conserva', 'lata'],
        'Salsas': ['salsa', 'tomate frito', 'sofrito', 'ketchup', 'mayonesa', 'mostaza', 'alioli'],
        'Condimentos': ['sal', 'pimienta', 'oregano', 'albahaca', 'curry', 'pimenton', 'especias', 'condimento', 'caldo', 'cubitos'],
        'Azúcar': ['azucar', 'edulcorante', 'sacarina', 'miel', 'sirope'],
        'Harinas': ['harina', 'levadura', 'bicarbonato'],
    },
    
    # === PANADERÍA ===
    'Panadería': {
        'Pan': ['pan de molde', 'pan integral', 'pan blanco', 'pan tostado', 'barra de pan', 'chapata', 'baguette'],
        'Galletas': ['galletas', 'cookies', 'maria', 'digestive'],
        'Bollería': ['croissant', 'napolitana', 'palmera', 'magdalena', 'bollo', 'donut', 'berlina'],
    },
    
    # === CARNICERÍA ===
    'Carnicería': {
        'Aves': ['pollo', 'pechuga de pollo', 'muslos de pollo', 'alitas de pollo', 'pavo', 'pechuga de pavo'],
        'Cerdo': ['cerdo', 'lomo de cerdo', 'costillas', 'chuletas de cerdo', 'secreto iberico'],
        'Ternera': ['ternera', 'vacuno', 'solomillo', 'entrecot', 'chuleta de ternera'],
        'Cordero': ['cordero', 'chuletas de cordero'],
        'Carnes': ['carne picada', 'hamburguesa', 'albondigas', 'salchichas', 'bacon'],
    },
    
    # === CHARCUTERÍA ===
    'Charcutería': {
        'Jamón': ['jamon serrano', 'jamon york', 'jamon cocido', 'paletilla', 'iberico'],
        'Embutidos': ['chorizo', 'salchichon', 'fuet', 'salami', 'mortadela', 'longaniza'],
    },
    
    # === PESCADERÍA ===
    'Pescadería': {
        'Pescados': ['merluza', 'salmon', 'bacalao', 'lubina', 'dorada', 'lenguado', 'pescado'],
        'Mariscos': ['gambas', 'langostinos', 'mejillones', 'almejas', 'pulpo', 'calamar', 'sepia'],
    },
    
    # === FRUTAS Y VERDURAS ===
    'Frutas y Verduras': {
        'Frutas': ['manzana', 'platano', 'naranja', 'pera', 'uva', 'melon', 'sandia', 'kiwi', 'fresas', 'cerezas', 'melocoton', 'nectarina', 'albaricoque', 'ciruela', 'limon', 'mandarina', 'pomelo'],
        'Verduras': ['tomate', 'lechuga', 'cebolla', 'patata', 'zanahoria', 'pepino', 'pimiento', 'calabacin', 'berenjena', 'brocoli', 'coliflor', 'espinacas', 'judias verdes', 'guisantes', 'champiñon', 'setas', 'espárragos', 'apio', 'remolacha', 'ensalada', 'cogollos'],
    },
    
    # === CONGELADOS ===
    'Congelados': {
        'Helados': ['helado', 'polo', 'granizado'],
        'Pizzas': ['pizza'],
        'Congelados': ['congelado', 'producto congelado'],
    },
    
    # === HIGIENE ===
    'Higiene': {
        'Higiene corporal': ['gel de ducha', 'jabon', 'gel baño', 'crema corporal'],
        'Desodorantes': ['desodorante'],
        'Higiene bucal': ['pasta de dientes', 'dentifrico', 'cepillo de dientes', 'enjuague bucal', 'colutorio'],
        'Cuidado facial': ['crema facial', 'limpiador facial', 'tonico'],
        'Cabello': ['champu', 'acondicionador', 'mascarilla capilar', 'tinte'],
    },
    
    # === LIMPIEZA ===
    'Limpieza': {
        'Detergentes': ['detergente', 'jabon para la ropa', 'detergente liquido', 'detergente en polvo'],
        'Lavavajillas': ['lavavajillas', 'fairy'],
        'Limpieza': ['lejia', 'limpiador', 'fregasuelos', 'limpiacristales', 'multiusos'],
        'Suavizantes': ['suavizante'],
    },
    
    # === BEBÉ ===
    'Bebé': {
        'Pañales': ['pañal', 'pañales', 'toallitas'],
        'Alimentación': ['potito', 'papilla', 'leche infantil'],
    },
}

def encontrar_mejor_categoria(nombre):
    """Encuentra la mejor categoría/subcategoría para un producto"""
    nombre_lower = nombre.lower()
    
    mejores_coincidencias = []
    
    for categoria, subcategorias in REGLAS_CATEGORIZACION.items():
        for subcategoria, patrones in subcategorias.items():
            for patron in patrones:
                if patron in nombre_lower:
                    # Puntuación: más larga la coincidencia = mejor
                    puntuacion = len(patron)
                    mejores_coincidencias.append((puntuacion, categoria, subcategoria, patron))
    
    if mejores_coincidencias:
        # Ordenar por puntuación (coincidencia más larga gana)
        mejores_coincidencias.sort(reverse=True)
        _, categoria, subcategoria, patron = mejores_coincidencias[0]
        return categoria, subcategoria
    
    return None, None

print("="*70)
print("MEJORANDO CATEGORIZACIÓN INTELIGENTE")
print("="*70)

# Cargar productos mal categorizados
response = supabase.table('productos_nuevos')\
    .select('*')\
    .eq('supermercado', 'Mercadona')\
    .eq('categoria', 'General')\
    .execute()

productos_general = response.data
print(f"\nProductos en 'General/Otros': {len(productos_general)}")

if len(productos_general) == 0:
    print("✅ No hay productos en 'General/Otros'")
    exit(0)

print("\nAnalizando y recategorizando...")

recategorizados = 0
sin_solucion = []

for p in productos_general:
    categoria_nueva, subcategoria_nueva = encontrar_mejor_categoria(p['nombre'])
    
    if categoria_nueva:
        try:
            supabase.table('productos_nuevos')\
                .update({
                    'categoria': categoria_nueva,
                    'subcategoria': subcategoria_nueva
                })\
                .eq('id_producto', p['id_producto'])\
                .execute()
            
            recategorizados += 1
            
            if recategorizados <= 10:
                print(f"  ✓ {p['nombre'][:50]}")
                print(f"    → {categoria_nueva} / {subcategoria_nueva}")
        
        except Exception as e:
            print(f"  Error: {e}")
    else:
        sin_solucion.append(p['nombre'])

print(f"\n{'='*70}")
print("RESULTADO")
print(f"{'='*70}")
print(f"Recategorizados: {recategorizados}")
print(f"Sin solución: {len(sin_solucion)}")

if sin_solucion:
    print(f"\nProductos que siguen en 'General/Otros' ({len(sin_solucion)}):")
    for nombre in sin_solucion[:20]:
        print(f"  • {nombre}")
    
    if len(sin_solucion) > 20:
        print(f"  ... y {len(sin_solucion) - 20} más")
    
    print("\n⚠️  Estos productos necesitan revisión manual")
    print("   o añadir más patrones al diccionario")

print(f"\n{'='*70}")
print("✅ CATEGORIZACIÓN MEJORADA")
print(f"{'='*70}")
