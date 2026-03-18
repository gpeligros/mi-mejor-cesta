import re
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

client = OpenAI()

# =========================
# CATEGORÍAS
# =========================

categories = [
("Azúcar, caramelos y chocolate","Caramelos"),
("Azúcar, caramelos y chocolate","Chicles"),
("Azúcar, caramelos y chocolate","Chocolates y bombones"),
("Azúcar, caramelos y chocolate","Golosinas"),
("Bazar y Varios","Hogar y decoración"),
("Bebes","Comida infantil"),
("Bebes","Cuidado e higiene del bebé"),
("Bebes","Pañales"),
("Bebes","Toallitas y algodón"),
("Bebidas","Agua"),
("Bebidas","Cerveza"),
("Bebidas","Licores y destilados"),
("Bebidas","Refrescos"),
("Bebidas","Vino"),
("Bebidas","Zumos"),
("Carnicería y Charcutería","Carne preparada"),
("Carnicería y Charcutería","Cerdo"),
("Carnicería y Charcutería","Charcuteria"),
("Carnicería y Charcutería","Cordero"),
("Carnicería y Charcutería","Pavo"),
("Carnicería y Charcutería","Pollo"),
("Carnicería y Charcutería","Vacuno"),
("Congelados","Helados y postres congelados"),
("Congelados","Platos congelados preparados"),
("Congelados","Verduras congeladas"),
("Conservas y Enlatados","Conservas de pescado y mariscos"),
("Conservas y Enlatados","Frutas en almíbar"),
("Conservas y Enlatados","Sopas, cremas y otros preparados"),
("Conservas y Enlatados","Verduras, legumbres y hortalizas en conserva"),
("Cuidado personal e Higiene","Cremas y protectores"),
("Cuidado personal e Higiene","Cuidado del cabello"),
("Cuidado personal e Higiene","Desodorantes"),
("Cuidado personal e Higiene","Higiene bucal"),
("Cuidado personal e Higiene","Higiene corporal"),
("Cuidado personal e Higiene","Higiene íntima femenina"),
("Cuidado personal e Higiene","Perfumes"),
("Cuidado personal e Higiene","Productos de afeitado"),
("Desayuno y Snack","Café y cacaos"),
("Desayuno y Snack","Cereales para desayuno"),
("Desayuno y Snack","Frutos secos embasados"),
("Desayuno y Snack","Galletas dulces"),
("Desayuno y Snack","Galletas saladas"),
("Desayuno y Snack","Mermelada y Miel"),
("Desayuno y Snack","Snack salados"),
("Desayuno y Snack","Té e infusiones"),
("Despensa","Aceites"),
("Despensa","Arroz, pasta y quinoa"),
("Despensa","Azúcares y edulcorantes"),
("Despensa","Especias e hierbas secas"),
("Despensa","Harinas"),
("Despensa","Legumbres secas"),
("Despensa","Sales"),
("Despensa","Salsas, caldos y condimentos preparados"),
("Despensa","Vinagres"),
("Frutas y Verduras","Fruta"),
("Frutas y Verduras","Setas"),
("Frutas y Verduras","Verduras"),
("Hogar","Ambientadores"),
("Hogar","Detergentes para ropa"),
("Hogar","Lavavajillas"),
("Hogar","Lejia y desinfectantes"),
("Hogar","Limpiadores de superficie"),
("Hogar","Suavizantes"),
("Hogar","Utensilios y consumibles de limpieza"),
("Lácteos y Huevos","Grasas vegetales"),
("Lácteos y Huevos","Huevos"),
("Lácteos y Huevos","Leche y bebidas lácteas"),
("Lácteos y Huevos","Mantequillas y Natas"),
("Lácteos y Huevos","Postres lácteos"),
("Lácteos y Huevos","Quesos"),
("Lácteos y Huevos","Yogures"),
("Mascotas","Accesorios para perros"),
("Mascotas","Arena y asea para gatos"),
("Mascotas","Comida para otros animales"),
("Mascotas","Comida para perros"),
("Panadería y Pastelería","Bollos"),
("Panadería y Pastelería","Pan fresco"),
("Panadería y Pastelería","Pasteles y Tartas"),
("Pescadería","Marisco"),
("Pescadería","Moluscos"),
("Pescadería","Pescado"),
("Platos preparados","Bocadillos y Sándwich listos"),
("Platos preparados","Ensaladas listas"),
("Platos preparados","Platos preparados refrigerados")
]

# =========================
# MARCAS
# =========================

brands = [
"Coca Cola","Pepsi","Nestle","Danone","Hacendado","Mahou","Heineken"
]

# =========================
# REGLAS
# =========================

rules = {
"leche":("Lacteos","Leche"),
"yogur":("Lacteos","Yogures"),
"pizza":("Congelados","Pizzas"),
"helado":("Congelados","Helados"),
"cerveza":("Bebidas","Cervezas"),
}

# =========================
# EMBEDDINGS
# =========================

def embed(text):

    r = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return r.data[0].embedding

cat_vectors = {}

for cat,sub in categories:
    cat_vectors[(cat,sub)] = embed(cat+" "+sub)

# =========================
# NORMALIZADOR
# =========================

def normalize(text):

    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]"," ",text)

    return text

# =========================
# EXTRAER FORMATO
# =========================

def extract_size(text):

    patterns = [
    r'(\d+)\s?ml',
    r'(\d+)\s?l',
    r'(\d+)\s?kg',
    r'(\d+)\s?g'
    ]

    for p in patterns:
        m = re.search(p,text)

        if m:
            return m.group(0)

    return None

# =========================
# EXTRAER MARCA
# =========================

def extract_brand(text):

    for b in brands:
        if b.lower() in text:
            return b

    return None

# =========================
# REGLAS
# =========================

def classify_rules(text):

    for k,v in rules.items():
        if k in text:
            return v

    return None

# =========================
# EMBEDDING CLASSIFIER
# =========================

def classify_embedding(text):

    v = embed(text)

    best = None
    best_score = -1

    for cat,vec in cat_vectors.items():

        score = cosine_similarity([v],[vec])[0][0]

        if score > best_score:
            best_score = score
            best = cat

    return best,best_score

# =========================
# LLM FALLBACK
# =========================

def classify_llm(text):

    prompt = f"""
Clasifica este producto.

Producto: {text}

Devuelve:
categoria|subcategoria
"""

    r = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    out = r.output[0].content[0].text

    return out.split("|")

# =========================
# PIPELINE
# =========================

def process(product):

    text = normalize(product)

    brand = extract_brand(text)

    size = extract_size(text)

    cat = classify_rules(text)

    if not cat:

        cat,score = classify_embedding(text)

        if score < 0.75:
            cat = classify_llm(text)

    return {
        "product":product,
        "brand":brand,
        "size":size,
        "category":cat[0],
        "subcategory":cat[1]
    }