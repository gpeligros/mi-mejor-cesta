# utils/supabase_client.py - VERSIÓN ACTUALIZADA
"""
Cliente para Supabase con nueva estructura (marca + nombre_web)
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseClient:
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise Exception("Faltan credenciales de Supabase en .env")
        
        self.client: Client = create_client(url, key)
    
    def get_all_products(self):
        """Obtiene todos los productos de la BD"""
        try:
            response = self.client.table('productos').select('*').execute()
            return response.data
        except Exception as e:
            print(f"❌ Error obteniendo productos: {e}")
            return []
    
    def search_products(self, query, limit=20):
        """
        Busca productos por nombre o marca
        """
        try:
            # Buscar en nombre O marca
            response = (
                self.client.table('productos')
                .select('*')
                .or_(f'nombre.ilike.%{query}%,marca.ilike.%{query}%')
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"❌ Error buscando productos: {e}")
            return []
    
    def update_price(self, id_producto, supermercado, precio, nombre_web=None):
        """
        Actualiza precio de un producto
        NUEVO: Guarda también nombre_web (exacto del scraper)
        """
        try:
            from datetime import date
            today = date.today().isoformat()
            
            # Verificar si ya existe
            existing = (
                self.client.table('precios_mercado')
                .select('*')
                .eq('id_producto', id_producto)
                .eq('supermercado', supermercado)
                .execute()
            )
            
            data = {
                'precio': precio,
                'actualizado': today
            }
            
            # Añadir nombre_web si se proporciona
            if nombre_web:
                data['nombre_web'] = nombre_web
            
            if existing.data:
                # Update
                response = (
                    self.client.table('precios_mercado')
                    .update(data)
                    .eq('id_producto', id_producto)
                    .eq('supermercado', supermercado)
                    .execute()
                )
                return {'action': 'updated', 'data': response.data}
            else:
                # Insert
                data['id_producto'] = id_producto
                data['supermercado'] = supermercado
                
                response = (
                    self.client.table('precios_mercado')
                    .insert(data)
                    .execute()
                )
                return {'action': 'inserted', 'data': response.data}
                
        except Exception as e:
            print(f"❌ Error actualizando precio: {e}")
            return None
    
    def update_product_marca(self, id_producto, marca):
        """
        Actualiza la marca de un producto
        """
        try:
            response = (
                self.client.table('productos')
                .update({'marca': marca})
                .eq('id_producto', id_producto)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"❌ Error actualizando marca: {e}")
            return None
    
    def get_product_by_id(self, id_producto):
        """Obtiene un producto específico por ID"""
        try:
            response = (
                self.client.table('productos')
                .select('*')
                .eq('id_producto', id_producto)
                .execute()
            )
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo producto: {e}")
            return None
    
    def get_products_with_prices(self, supermercado=None):
        """
        Obtiene productos con sus precios (JOIN)
        """
        try:
            query = '''
                id_producto,
                nombre,
                marca,
                formato,
                categoria,
                subcategoria,
                precios_mercado(
                    supermercado,
                    precio,
                    actualizado,
                    nombre_web
                )
            '''
            
            response = self.client.table('productos').select(query).execute()
            
            # Filtrar por supermercado si se especifica
            if supermercado:
                filtered = []
                for prod in response.data:
                    if prod.get('precios_mercado'):
                        prod['precios_mercado'] = [
                            p for p in prod['precios_mercado'] 
                            if p['supermercado'] == supermercado
                        ]
                        if prod['precios_mercado']:
                            filtered.append(prod)
                return filtered
            
            return response.data
            
        except Exception as e:
            print(f"❌ Error obteniendo productos con precios: {e}")
            return []


# Test
if __name__ == "__main__":
    print("=" * 60)
    print("TEST SUPABASE CLIENT - NUEVA ESTRUCTURA")
    print("=" * 60)
    
    sb = SupabaseClient()
    
    # Test 1: Obtener productos
    print("\n📊 TEST 1: Obtener productos")
    productos = sb.get_all_products()
    print(f"✅ Total: {len(productos)}")
    
    if productos:
        # Contar con/sin marca
        con_marca = len([p for p in productos if p.get('marca')])
        sin_marca = len(productos) - con_marca
        
        print(f"   Con marca: {con_marca} ({con_marca/len(productos)*100:.1f}%)")
        print(f"   Sin marca: {sin_marca} ({sin_marca/len(productos)*100:.1f}%)")
        
        print(f"\n   Ejemplos con marca:")
        for p in productos[:5]:
            if p.get('marca'):
                print(f"   - {p['id_producto']}: {p['nombre']} ({p['marca']}) - {p['formato']}")
    
    # Test 2: Buscar productos
    print("\n🔍 TEST 2: Buscar 'leche'")
    resultados = sb.search_products('leche')
    print(f"✅ Encontrados: {len(resultados)}")
    
    for p in resultados[:5]:
        marca_str = f" ({p['marca']})" if p.get('marca') else ""
        print(f"   - {p['id_producto']}: {p['nombre']}{marca_str}")
    
    # Test 3: Obtener producto con precios
    print("\n💰 TEST 3: Productos con precios")
    productos_precios = sb.get_products_with_prices(supermercado='Mercadona')
    print(f"✅ Productos con precios en Mercadona: {len(productos_precios)}")
    
    if productos_precios:
        for p in productos_precios[:3]:
            print(f"\n   {p['nombre']} ({p.get('marca', 'Sin marca')})")
            for precio in p.get('precios_mercado', []):
                nombre_web = precio.get('nombre_web', 'N/A')
                print(f"      → {precio['precio']}€ - Web: {nombre_web[:50]}")
    
    print("\n" + "=" * 60)
    print("✅ Tests completados")