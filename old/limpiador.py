import pandas as pd

# 1. Ruta del fichero original
INPUT = "productos.csv"
OUTPUT = "productos_limpio.csv"

# 2. Intenta leer con varios encodings hasta que funcione
encodings_a_probar = ["utf-8", "latin-1", "cp1252"]

for enc in encodings_a_probar:
    try:
        print(f"Probando encoding: {enc}")
        df = pd.read_csv(INPUT, encoding=enc)
        print(f"Leído correctamente con {enc}")
        # si funciona, salimos del bucle
        break
    except UnicodeDecodeError:
        print(f"Fallo con {enc}")
        df = None

if df is None:
    raise ValueError("No se ha podido leer el CSV con los encodings probados.")

# 3. Nos aseguramos de que la columna de precio es numérica
#    (ajusta el nombre de columna exactamente como aparezca en tu CSV)
col_precio = "precio"
df[col_precio] = pd.to_numeric(df[col_precio], errors="coerce")

# 4. Creamos una nueva columna de texto con el precio + " €"
df["precio_euro"] = df[col_precio].map(lambda x: f"{x:.2f} €" if pd.notnull(x) else "")

# 5. (Opcional) pequeños arreglos de texto por si hay palabras mal codificadas
reemplazos = {
    "lctea": "láctea",
    "Jamn": "Jamón",
    "esprragos": "espárragos",
    "maz": "maíz",
    # añade aquí más pares "mal":"bien" si detectas patrones
}

def corrige_texto(valor):
    if not isinstance(valor, str):
        return valor
    for malo, bueno in reemplazos.items():
        valor = valor.replace(malo, bueno)
    return valor

# Aplica correcciones a todas las columnas de tipo texto
for col in df.select_dtypes(include=["object"]).columns:
    df[col] = df[col].map(corrige_texto)

# 6. Guardamos todo a UTF-8
df.to_csv(OUTPUT, index=False, encoding="utf-8")
print(f"Guardado en {OUTPUT}")
