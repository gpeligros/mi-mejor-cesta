import pandas as pd

df = pd.read_csv("mercadona_bueno.csv", sep=None, engine="python")

resultados = []

for i,row in df.iterrows():

    producto = row["producto"]   # cambia el nombre si la columna se llama distinto

    r = process(producto)

    resultados.append(r)

out = pd.DataFrame(resultados)

out.to_csv("mercadona_clasificado.csv",index=False)

print("Clasificación terminada")