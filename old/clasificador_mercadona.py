import pandas as pd

def clasificar_producto(row):
    nombre = str(row['nombre']).lower()
    
    # --- REGLAS PARA PRODUCTOS DELIPLUS / PARAFARMACIA ---
    if 'cápsulas' in nombre or 'capsulas' in nombre:
        if 'skin' in nombre or 'ojos' in nombre:
            return pd.Series(['Fitoterapia y parafarmacia', 'Cuidado facial'])
        return pd.Series(['Fitoterapia y parafarmacia', 'Complementos alimenticios'])
    
    # --- REGLAS PARA PRODUCTOS HOGAR (Velas y Ambientación) ---
    elif 'vela' in nombre:
        if 'cumpleaños' in nombre:
            return pd.Series(['Hogar y limpieza', 'Utensilios de limpieza y hogar'])
        if 'perfumada' in nombre or 'bosque verde' in nombre:
            return pd.Series(['Hogar y limpieza', 'Ambientadores'])

    # --- REGLAS DEL EJERCICIO ANTERIOR (Alimentación) ---
    elif 'aceite' in nombre and 'migas' not in nombre and 'pastas' not in nombre:
        return pd.Series(['Aceite, especias y salsas', 'Aceite'])
    elif 'yogur' in nombre:
        return pd.Series(['Postres y yogures', 'Yogures'])
    elif 'zumo' in nombre or 'bebida' in nombre:
        if 'golosinas' in nombre:
             return pd.Series(['Azúcar, caramelos y chocolate', 'Golosinas'])
        return pd.Series(['Zumos', 'Zumos de frutas'])
    
    return pd.Series(['Revisar', 'Revisar'])

def main():
    archivo_entrada = 'mercadona_prueba.csv'
    archivo_salida = 'mercadona_clasificado_v2.csv'
    
    print("Leyendo archivo...")
    # Usamos latin1 para evitar el error UnicodeDecodeError
    try:
        df = pd.read_csv(archivo_entrada, sep=';', encoding='latin1')
    except:
        df = pd.read_csv(archivo_entrada, sep=';', encoding='cp1252')
    
    print("Clasificando...")
    df[['categoria_nueva', 'subcategoria_nueva']] = df.apply(clasificar_producto, axis=1)
    
    # Guardamos con utf-8-sig para que Excel lo abra bien
    df.to_csv(archivo_salida, sep=';', index=False, encoding='utf-8-sig')
    print(f"Hecho. Archivo guardado como {archivo_salida}")

if __name__ == "__main__":
    main()