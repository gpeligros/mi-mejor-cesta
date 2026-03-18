"""
BORRAR TODO Y EMPEZAR LIMPIO
"""
from supabase import create_client
import config

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

print("="*70)
print("⚠️  BORRAR TODO Y EMPEZAR DE CERO")
print("="*70)
print("\nEsto va a BORRAR:")
print("  - Todos los productos")
print("  - Todos los grupos")
print("  - Todas las relaciones")
print("\nLa estructura de las tablas se mantiene.")
print("="*70)

confirmar = input("\n¿Estás SEGURO? Escribe 'BORRAR' para confirmar: ")

if confirmar == 'BORRAR':
    print("\n[1/3] Borrando relaciones...")
    try:
        supabase.table('productos_en_grupos').delete().neq('id', 0).execute()
        print("  ✓ Relaciones borradas")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n[2/3] Borrando grupos...")
    try:
        supabase.table('productos_grupos').delete().neq('id', 0).execute()
        print("  ✓ Grupos borrados")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n[3/3] Borrando productos...")
    try:
        supabase.table('productos_nuevos').delete().neq('id', 0).execute()
        print("  ✓ Productos borrados")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n" + "="*70)
    print("✅ TODO BORRADO")
    print("="*70)
    print("\nSIGUIENTE PASO:")
    print("  1. Scrapear Mercadona CON categorías correctas")
    print("  2. python nuevo_scraper_mercadona.py")
    print("="*70)
else:
    print("\nCancelado. No se borró nada.")
