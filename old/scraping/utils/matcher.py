# utils/matcher.py - VERSIÓN OPTIMIZADA
"""
Matcher mejorado con umbral de confianza ajustado
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv
import json
import re

load_dotenv()

class AIProductMatcher:
    def __init__(self, confidence_threshold=50):  # Reducido de 70 a 50
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model = "claude-sonnet-4-20250514"
        self.confidence_threshold = confidence_threshold
    
    def extract_marca(self, nombre_web):
        """Extrae marca del nombre"""
        marcas_conocidas = [
            'Hacendado', 'Pascual', 'Danone', 'Coca-Cola', 'Pepsi',
            'Nestlé', 'Nestle', 'Carbonell', 'Coosur', 'Bezoya',
            'Font Vella', 'Lanjarón', 'Lanjaron', 'Alpro', 
            'Central Lechera Asturiana', 'Asturiana', 'Kaiku', 
            'Oikos', 'President', 'Flora', 'Puleva', 'Galbani', 
            'Kerrygold', 'Philadelphia', 'Royal', 'Carrefour', 
            'Milbona', 'Mahou', 'Cruzcampo', 'Heineken', 
            'Don Simon', 'Don Simón'
        ]
        
        for marca in marcas_conocidas:
            if marca.lower() in nombre_web.lower():
                return marca
        
        return None
    
    def match_product(self, producto_web, productos_bd):
        """
        Matching mejorado con prompt optimizado
        """
        nombre_web = producto_web.get('nombre', '')
        raw_text = producto_web.get('raw_text', '')
        
        # Extraer marca
        marca_web = self.extract_marca(nombre_web)
        
        # Preparar lista productos BD (más detallada)
        productos_bd_text = "\n".join([
            f"{i+1}. ID: {p['id_producto']} | Nombre: {p['nombre']} | Marca: {p.get('marca', 'Sin marca')} | Formato: {p.get('formato', 'N/A')}"
            for i, p in enumerate(productos_bd[:20])
        ])
        
        # Prompt MEJORADO - más permisivo
        prompt = f"""Eres un experto en matching de productos de supermercado.

PRODUCTO WEB SCRAPEADO DE MERCADONA:
Nombre: {nombre_web}
Marca detectada: {marca_web or 'No detectada'}
Contexto: {raw_text[:150]}

PRODUCTOS EN BASE DE DATOS (CATÁLOGO):
{productos_bd_text}

REGLAS DE MATCHING:
1. PRIORIDAD ALTA: Coincidencia de marca + nombre base
   Ejemplo: "Leche entera Hacendado" → "Leche entera Hacendado 1L" = 95%
   
2. Ignora diferencias menores:
   - Mayúsculas/minúsculas
   - Acentos
   - Palabras como "brick", "botella", "pack"
   - Formato exacto (1L vs 1l vs 1 L)
   
3. Confianza mínima 50%:
   - 90-100%: Match perfecto (marca + nombre + formato similar)
   - 70-89%: Match bueno (marca + nombre, formato diferente)
   - 50-69%: Match aceptable (solo nombre coincide bien)
   - <50%: Sin match

4. Si el producto web es "Leche entera Hacendado" y en BD hay:
   - "Leche entera Hacendado 1L" → 95% (perfecto)
   - "Leche entera brick" (sin marca) → 70% (aceptable)
   - "Leche desnatada Hacendado" → 60% (diferente tipo)
   - "Yogur" → 0% (producto diferente)

RESPONDE SOLO JSON (sin markdown ni ```):
{{
  "id_producto": "LA-LE-015",
  "confianza": 95,
  "razon": "Match exacto: marca Hacendado + nombre 'leche entera'"
}}

O si no hay match ≥50%:
{{
  "id_producto": "NONE",
  "confianza": 0,
  "razon": "No se encontró coincidencia suficiente"
}}

RESPONDE AHORA:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Limpiar markdown
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Intentar parsear
            result = json.loads(response_text)
            
            # Validar umbral
            if result['id_producto'] == 'NONE' or result['confianza'] < self.confidence_threshold:
                return None
            
            return result
            
        except Exception as e:
            print(f"❌ Error en matching: {e}")
            print(f"   Respuesta IA: {response_text if 'response_text' in locals() else 'N/A'}")
            return None
    
    def match_and_update(self, producto_web, productos_bd, supabase_client):
        """Match + Update en un paso"""
        match_result = self.match_product(producto_web, productos_bd)
        
        if not match_result:
            return {'status': 'no_match', 'producto_web': producto_web}
        
        id_producto = match_result['id_producto']
        confianza = match_result['confianza']
        marca_detectada = self.extract_marca(producto_web.get('nombre', ''))
        
        # Obtener producto BD
        producto_bd = supabase_client.get_product_by_id(id_producto)
        
        if not producto_bd:
            return {'status': 'error', 'message': f'Producto {id_producto} no encontrado'}
        
        # Actualizar marca si falta
        if marca_detectada and not producto_bd.get('marca'):
            print(f"   📝 Actualizando marca: {marca_detectada}")
            supabase_client.update_product_marca(id_producto, marca_detectada)
        
        # Actualizar precio + nombre_web
        nombre_web = producto_web.get('nombre', '') + ' ' + producto_web.get('raw_text', '')[:100]
        nombre_web = ' '.join(nombre_web.split())  # Limpiar espacios
        
        result = supabase_client.update_price(
            id_producto=id_producto,
            supermercado=producto_web.get('supermercado', 'Mercadona'),
            precio=producto_web.get('precio', 0),
            nombre_web=nombre_web[:300]
        )
        
        return {
            'status': 'success',
            'match': match_result,
            'update': result,
            'producto_bd': producto_bd
        }
    
    def match_batch(self, productos_web, productos_bd, supabase_client=None):
        """Match múltiple"""
        results = {
            'success': [],
            'review': [],
            'no_match': [],
            'errors': []
        }
        
        print(f"\n🔍 Procesando {len(productos_web)} productos...")
        print(f"   Umbral de confianza: ≥{self.confidence_threshold}%")
        
        for i, prod_web in enumerate(productos_web, 1):
            print(f"\n[{i}/{len(productos_web)}] {prod_web['nombre'][:40]}...")
            
            try:
                if supabase_client:
                    result = self.match_and_update(prod_web, productos_bd, supabase_client)
                    
                    if result['status'] == 'success':
                        confianza = result['match']['confianza']
                        if confianza >= 80:
                            print(f"✅ Actualizado: {result['match']['id_producto']} ({confianza}%)")
                            results['success'].append(result)
                        else:
                            print(f"⚠️ Actualizado (baja confianza): {result['match']['id_producto']} ({confianza}%)")
                            results['review'].append(result)
                    
                    elif result['status'] == 'no_match':
                        print(f"❌ Sin match (confianza <{self.confidence_threshold}%)")
                        results['no_match'].append(prod_web)
                    
                    else:
                        print(f"❌ Error: {result.get('message', 'Unknown')}")
                        results['errors'].append(result)
                
                else:
                    # Solo matching
                    match_result = self.match_product(prod_web, productos_bd)
                    
                    if match_result and match_result['confianza'] >= 80:
                        print(f"✅ Match: {match_result['id_producto']} ({match_result['confianza']}%)")
                        results['success'].append({'producto_web': prod_web, 'match': match_result})
                    elif match_result:
                        print(f"⚠️ Match dudoso: {match_result['id_producto']} ({match_result['confianza']}%)")
                        results['review'].append({'producto_web': prod_web, 'match': match_result})
                    else:
                        print(f"❌ Sin match")
                        results['no_match'].append(prod_web)
                        
            except Exception as e:
                print(f"❌ Error: {e}")
                results['errors'].append({'producto': prod_web, 'error': str(e)})
        
        return results


# Test
if __name__ == "__main__":
    matcher = AIProductMatcher(confidence_threshold=50)
    
    print("=" * 60)
    print("TEST MATCHER OPTIMIZADO")
    print("=" * 60)
    
    # Test con el ejemplo real
    producto_web = {
        'nombre': 'Leche entera Hacendado',
        'precio': 5.82,
        'raw_text': 'Leche entera Hacendado 6 bricks x 1 L 5,82 €',
        'supermercado': 'Mercadona'
    }
    
    productos_bd = [
        {
            'id_producto': 'LA-LE-015',
            'nombre': 'Leche entera Hacendado 1L',
            'marca': 'Hacendado',
            'formato': '1l'
        },
        {
            'id_producto': 'LA-LE-006',
            'nombre': 'Leche entera brick',
            'marca': None,
            'formato': '1l'
        },
        {
            'id_producto': 'LA-LE-013',
            'nombre': 'Leche entera Pascual 1L',
            'marca': 'Pascual',
            'formato': '1l'
        }
    ]
    
    print(f"\n📦 Producto web: {producto_web['nombre']}")
    print(f"💰 Precio: {producto_web['precio']}€")
    
    result = matcher.match_product(producto_web, productos_bd)
    
    if result:
        print(f"\n✅ MATCH ENCONTRADO:")
        print(f"   ID: {result['id_producto']}")
        print(f"   Confianza: {result['confianza']}%")
        print(f"   Razón: {result['razon']}")
    else:
        print(f"\n❌ No se encontró match")
    
    print("\n" + "=" * 60)