"""
CAPTURADOR UNIVERSAL - FUNCIONA CON CUALQUIER SUPER
Tú copias y pegas productos, yo los inserto en BD
"""
from supabase import create_client
import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

SUPERMERCADOS = {
    '1': 'Mercadona',
    '2': 'Lidl',
    '3': 'Carrefour',
    '4': 'Dia',
}

CATEGORIAS = {
    '1': 'Lácteos',
    '2': 'Bebidas',
    '3': 'Despensa',
    '4': 'Panadería',
    '5': 'Carnicería',
    '6': 'Charcutería',
    '7': 'Pescadería',
    '8': 'Frutas y Verduras',
    '9': 'Congelados',
    '10': 'Higiene',
    '11': 'Limpieza',
}

def generar_id(supermercado, contador):
    prefijos = {
        'Mercadona': 'ME',
        'Lidl': 'LI',
        'Carrefour': 'CA',
        'Dia': 'DI'
    }
    return f"{prefijos[supermercado]}-{contador:04d}"

def capturar_manual():
    print("="*70)
    print("CAPTURADOR MANUAL UNIVERSAL")
    print("="*70)
    print("\nCOPIA PRODUCTOS DE CUALQUIER WEB Y PÉGALOS AQUÍ")
    print("\nFORMATO:")
    print("  nombre | precio")
    print("  Leche entera 1L | 0.95")
    print("  Yogur natural | 1.25")
    print("  (una línea por producto)\n")
    
    # Elegir supermercado
    print("SUPERMERCADOS:")
    for k, v in SUPERMERCADOS.items():
        print(f"  {k}. {v}")
    super_num = input("\nElige supermercado (1-4): ")
    supermercado = SUPERMERCADOS.get(super_num)
    
    if not supermercado:
        print("Supermercado inválido")
        return
    
    # Elegir categoría
    print("\nCATEGORÍAS:")
    for k, v in CATEGORIAS.items():
        print(f"  {k}. {v}")
    cat_num = input("\nElige categoría (1-11): ")
    categoria = CATEGORIAS.get(cat_num)
    
    if not categoria:
        print("Categoría inválida")
        return
    
    # Subcategoría
    subcategoria = input("Subcategoría (ej: Leche, Yogures, Agua): ")
    
    # Obtener contador
    try:
        response = supabase.table('productos_nuevos')\
            .select('id_producto')\
            .eq('supermercado', supermercado)\
            .execute()
        
        contador = 1
        if response.data:
            ids = [int(p['id_producto'].split('-')[1]) for p in response.data if '-' in p['id_producto']]
            if ids:
                contador = max(ids) + 1
    except:
        contador = 1
    
    print("\n" + "="*70)
    print(f"SUPERMERCADO: {supermercado}")
    print(f"CATEGORÍA: {categoria} / {subcategoria}")
    print("="*70)
    print("\nPEGA LOS PRODUCTOS (formato: nombre | precio)")
    print("Deja una línea en blanco para terminar\n")
    
    insertados = 0
    
    while True:
        linea = input()
        
        if not linea.strip():
            break
        
        try:
            # Parsear línea
            partes = linea.split('|')
            if len(partes) != 2:
                print(f"  ❌ Formato incorrecto: {linea}")
                continue
            
            nombre = partes[0].strip()
            precio_str = partes[1].strip().replace('€', '').replace(',', '.')
            precio = float(precio_str)
            
            # Generar ID
            id_producto = generar_id(supermercado, contador)
            contador += 1
            
            # Insertar
            supabase.table('productos_nuevos').insert({
                'id_producto': id_producto,
                'nombre': nombre,
                'supermercado': supermercado,
                'precio': precio,
                'categoria': categoria,
                'subcategoria': subcategoria
            }).execute()
            
            insertados += 1
            print(f"  ✓ {nombre} ({precio}€)")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n{'='*70}")
    print(f"Total insertados: {insertados}")
    print("="*70)
    
    if insertados > 0:
        continuar = input("\n¿Insertar más productos de otra categoría? (s/n): ")
        if continuar.lower() == 's':
            capturar_manual()

if __name__ == "__main__":
    capturar_manual()
