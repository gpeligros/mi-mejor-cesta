"""
CORRECCIÓN MANUAL DE CATEGORÍAS
Para productos específicos que están mal categorizados
"""
from supabase import create_client
import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Define aquí las correcciones específicas
CORRECCIONES = {
    # Formato: 'nombre_producto_parcial': ('categoria_correcta', 'subcategoria_correcta')
    
    # Ejemplos (ajusta según lo que veas mal):
    # 'Coca Cola': ('Bebidas', 'Refrescos'),
    # 'Fanta': ('Bebidas', 'Refrescos'),
    # 'Aceitunas': ('Despensa', 'Conservas'),
}

def corregir_categorias():
    print("="*70)
    print("CORRECCIÓN MANUAL DE CATEGORÍAS")
    print("="*70)
    
    # Obtener todos los productos
    print("\nObteniendo productos...")
    response = supabase.table('productos_nuevos').select('*').execute()
    productos = response.data
    print(f"Total productos: {len(productos)}")
    
    # Aplicar correcciones
    print("\nAplicando correcciones...")
    corregidos = 0
    
    for prod in productos:
        nombre = prod['nombre']
        
        for patron, (cat_nueva, subcat_nueva) in CORRECCIONES.items():
            if patron.lower() in nombre.lower():
                cat_actual = prod.get('categoria')
                subcat_actual = prod.get('subcategoria')
                
                if cat_actual != cat_nueva or subcat_actual != subcat_nueva:
                    print(f"\n  {nombre[:50]}")
                    print(f"    {cat_actual}/{subcat_actual} → {cat_nueva}/{subcat_nueva}")
                    
                    try:
                        supabase.table('productos_nuevos')\
                            .update({
                                'categoria': cat_nueva,
                                'subcategoria': subcat_nueva
                            })\
                            .eq('id_producto', prod['id_producto'])\
                            .execute()
                        
                        corregidos += 1
                    except Exception as e:
                        print(f"    Error: {e}")
    
    print(f"\n{'='*70}")
    print(f"Productos corregidos: {corregidos}")
    print(f"{'='*70}")

def mostrar_problematicos():
    """Muestra productos que podrían estar mal categorizados"""
    print("\n" + "="*70)
    print("PRODUCTOS POTENCIALMENTE MAL CATEGORIZADOS")
    print("="*70)
    
    # Buscar productos con categorías sospechosas
    response = supabase.table('productos_nuevos')\
        .select('nombre, categoria, subcategoria')\
        .execute()
    
    problematicos = []
    
    for prod in response.data:
        nombre = prod['nombre'].lower()
        cat = prod['categoria']
        
        # Detectar inconsistencias
        if 'agua' in nombre and cat != 'Bebidas':
            problematicos.append(prod)
        elif 'leche' in nombre and cat != 'Lácteos':
            problematicos.append(prod)
        elif 'pan' in nombre and cat != 'Panadería':
            problematicos.append(prod)
        elif 'aceite' in nombre and cat != 'Despensa':
            problematicos.append(prod)
    
    if problematicos:
        print(f"\nEncontrados {len(problematicos)} productos sospechosos:")
        for p in problematicos[:20]:
            print(f"  - {p['nombre'][:50]}")
            print(f"    Categoría: {p['categoria']}/{p['subcategoria']}")
        
        if len(problematicos) > 20:
            print(f"  ... y {len(problematicos) - 20} más")
        
        print("\nAñádelos al diccionario CORRECCIONES y ejecuta de nuevo.")
    else:
        print("\n✓ No se encontraron problemas evidentes")
    
    print("="*70)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'ver':
        mostrar_problematicos()
    else:
        print("\nOpciones:")
        print("  python 14_corregir_categorias.py ver      → Ver problemas")
        print("  python 14_corregir_categorias.py          → Aplicar correcciones")
        print()
        
        opcion = input("¿Qué quieres hacer? (ver/corregir): ")
        
        if opcion == 'ver':
            mostrar_problematicos()
        elif opcion == 'corregir':
            corregir_categorias()
        else:
            print("Cancelado")
