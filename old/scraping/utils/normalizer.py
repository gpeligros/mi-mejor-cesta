# utils/normalizer.py
import re

class ProductNormalizer:
    """
    Normaliza datos de productos:
    - Formatos: 6x1L → 6000ml, 1L → 1000ml
    - Precios: limpieza
    - Nombres: limpieza
    """
    
    @staticmethod
    def normalize_formato(texto_raw):
        """
        Normaliza formato a unidades base
        
        Ejemplos:
            "6 bricks x 1 L" → ("6L", "1L", 6.0)
            "Brick 1 L" → ("1L", "1L", 1.0)
            "pack" → ("1ud", "1ud", 1.0)
            "500 ml" → ("500ml", "1L", 0.5)
        
        Returns:
            (formato_original, formato_base, factor_conversion)
        """
        if not texto_raw:
            return ("1ud", "1ud", 1.0)
        
        texto = texto_raw.lower().strip()
        
        # Patrón: N x M unidad (ej: 6 x 1 L)
        match_multi = re.search(r'(\d+)\s*(?:x|bricks?)\s*(\d+(?:[.,]\d+)?)\s*(l|ml|g|kg)', texto)
        if match_multi:
            cantidad = int(match_multi.group(1))
            volumen = float(match_multi.group(2).replace(',', '.'))
            unidad = match_multi.group(3)
            
            if unidad == 'l':
                total_ml = cantidad * volumen * 1000
                return (f"{cantidad}x{volumen}L", "1L", cantidad * volumen)
            elif unidad == 'ml':
                total_ml = cantidad * volumen
                litros = total_ml / 1000
                return (f"{cantidad}x{volumen}ml", "1L", litros)
            elif unidad == 'kg':
                total_g = cantidad * volumen * 1000
                return (f"{cantidad}x{volumen}kg", "1kg", cantidad * volumen)
            elif unidad == 'g':
                total_g = cantidad * volumen
                kg = total_g / 1000
                return (f"{cantidad}x{volumen}g", "1kg", kg)
        
        # Patrón: M unidad (ej: 1 L, 500 ml)
        match_simple = re.search(r'(\d+(?:[.,]\d+)?)\s*(l|ml|g|kg)', texto)
        if match_simple:
            valor = float(match_simple.group(1).replace(',', '.'))
            unidad = match_simple.group(2)
            
            if unidad == 'l':
                return (f"{valor}L", "1L", valor)
            elif unidad == 'ml':
                litros = valor / 1000
                return (f"{int(valor)}ml", "1L", litros)
            elif unidad == 'kg':
                return (f"{valor}kg", "1kg", valor)
            elif unidad == 'g':
                kg = valor / 1000
                return (f"{int(valor)}g", "1kg", kg)
        
        # Unidades por defecto
        if 'pack' in texto or 'ud' in texto:
            return ("1ud", "1ud", 1.0)
        
        return ("1ud", "1ud", 1.0)
    
    @staticmethod
    def extract_formato_from_raw(texto_raw):
        """
        Extrae formato del texto raw
        "Leche entera Hacendado 6 bricks x 1 L" → "6x1L"
        """
        if not texto_raw:
            return ""
        
        formato_info, _, _ = ProductNormalizer.normalize_formato(texto_raw)
        return formato_info
    
    @staticmethod
    def clean_nombre(nombre, formato_detectado=""):
        """
        Limpia nombre del producto
        "Leche entera Hacendado 6 bricks x 1 L" → "Leche entera Hacendado"
        """
        nombre_limpio = nombre
        
        # Quitar información de formato
        patterns_to_remove = [
            r'\d+\s*(?:x|bricks?)\s*\d+(?:[.,]\d+)?\s*(?:l|ml|g|kg)',
            r'\d+(?:[.,]\d+)?\s*(?:l|ml|g|kg)',
            r'brick\s*\d+\s*l',
            r'/pack',
            r'/ud\.?',
        ]
        
        for pattern in patterns_to_remove:
            nombre_limpio = re.sub(pattern, '', nombre_limpio, flags=re.IGNORECASE)
        
        # Limpiar espacios extras
        nombre_limpio = ' '.join(nombre_limpio.split())
        
        return nombre_limpio.strip()
    
    @staticmethod
    def normalize_product(producto_raw):
        """
        Normaliza un producto completo
        
        Input:
            {
                'nombre': 'Leche entera Hacendado',
                'precio': 5.82,
                'raw_text': 'Leche entera Hacendado 6 bricks x 1 L 5,82 € /pack'
            }
        
        Output:
            {
                'nombre': 'Leche entera Hacendado',
                'precio': 5.82,
                'precio_unitario': 0.97,  # 5.82 / 6
                'formato': '6x1L',
                'formato_base': '1L',
                'factor_conversion': 6.0,
                'supermercado': 'Mercadona',
                ...
            }
        """
        raw_text = producto_raw.get('raw_text', '')
        
        # Normalizar formato
        formato, formato_base, factor = ProductNormalizer.normalize_formato(raw_text)
        
        # Limpiar nombre
        nombre_limpio = ProductNormalizer.clean_nombre(
            producto_raw.get('nombre', ''),
            formato
        )
        
        # Calcular precio unitario
        precio = producto_raw.get('precio', 0)
        precio_unitario = precio / factor if factor > 0 else precio
        
        return {
            'nombre': nombre_limpio,
            'precio': precio,
            'precio_unitario': round(precio_unitario, 2),
            'formato': formato,
            'formato_base': formato_base,
            'factor_conversion': factor,
            'supermercado': producto_raw.get('supermercado', 'Mercadona'),
            'fecha': producto_raw.get('fecha'),
            'posicion': producto_raw.get('posicion', 0)
        }


# Test
if __name__ == "__main__":
    normalizer = ProductNormalizer()
    
    # Test cases
    test_products = [
        {
            'nombre': 'Leche entera Hacendado',
            'precio': 5.82,
            'raw_text': 'Leche entera Hacendado 6 bricks x 1 L',
            'supermercado': 'Mercadona'
        },
        {
            'nombre': 'Leche entera Hacendado',
            'precio': 0.97,
            'raw_text': 'Leche entera Hacendado Brick 1 L',
            'supermercado': 'Mercadona'
        },
        {
            'nombre': 'Aceite oliva',
            'precio': 4.50,
            'raw_text': 'Aceite oliva virgen extra 1 L',
            'supermercado': 'Mercadona'
        }
    ]
    
    print("=" * 60)
    print("TEST NORMALIZACIÓN")
    print("=" * 60)
    
    for prod in test_products:
        print(f"\n📦 ORIGINAL:")
        print(f"   {prod['nombre']} - {prod['precio']}€")
        print(f"   Raw: {prod['raw_text']}")
        
        normalizado = normalizer.normalize_product(prod)
        
        print(f"\n✅ NORMALIZADO:")
        print(f"   Nombre: {normalizado['nombre']}")
        print(f"   Precio: {normalizado['precio']}€")
        print(f"   Precio/unidad: {normalizado['precio_unitario']}€/{normalizado['formato_base']}")
        print(f"   Formato: {normalizado['formato']}")
        print(f"   Factor: {normalizado['factor_conversion']}")