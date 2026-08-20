"""
clasificar_categoria.py — Mi Mejor Cesta
==========================================
FASE 4b — asigna categoría a los 17.154 clusters del catálogo propuesto,
en TRES capas de fiabilidad decreciente, garantizando 0 sin categorizar:

  CAPA 1 — Categoría REAL de Mercadona (vía categoria_mercadona +
           subcategoria_mercadona del export original + el MAPPING oficial
           que ya usa construir_catalogo.py). 100% fiable, cubre los
           clusters que tienen un miembro Mercadona con categoría poblada.

  CAPA 2 — Clasificador por palabras clave contra las 87 categorías reales
           de categorias_maestras, para todo lo que no tenga Capa 1.

  CAPA 3 — Vecino más cercano: fuzzy matching contra clusters YA
           categorizados (Capa 1 o 2), para lo que ni tiene categoría real
           ni coincide con ninguna palabra clave. Última red de seguridad;
           si ni así encuentra nada, cae en "Bazar y Varios" (id 89).

No toca la BBDD. Solo lee CSVs locales y escribe un CSV de asignación.

USO:
  python scrapers/clasificar_categoria.py

Requiere en old/:
  - export_precios_mercadona_<fecha>.csv  (de exportar_todos_precios.py — Fase 1)
  - miembros_finales_<fecha>.csv           (de construir_propuesta_final.py — Fase 4)

SALIDA (en old/):
  categorias_asignadas_<fecha>.csv   -> cluster_id, id_categoria, categoria,
                                         subcategoria, origen (mercadona_real|
                                         keyword|vecino_cercano|sin_match_bazar)
"""

import csv
import glob
import re
import unicodedata
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

from rapidfuzz import fuzz

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_OLD = RAIZ / "old"

UMBRAL_VECINO = 55  # laxo a propósito: es la última red de seguridad, mejor
                     # una categoría aproximada que "sin categorizar"

# ── MAPPING oficial Mercadona → id_categoria (el mismo que usa
# construir_catalogo.py, para no duplicar criterio) ────────────────────────
MAPPING_MERCADONA = {
    "aceite, especias y salsas|aceite, vinagre y sal": 133,
    "aceite, especias y salsas|mayonesa, ketchup y mostaza": 140,
    "aceite, especias y salsas|especias": 136,
    "aceite, especias y salsas|otras salsas": 140,
    "aceite, especias y salsas|vinagre": 141,
    "agua y refrescos|agua": 94,
    "agua y refrescos|refresco de cola": 97,
    "agua y refrescos|refresco de naranja y de limon": 97,
    "agua y refrescos|tonica y bitter": 97,
    "agua y refrescos|refresco de te y sin gas": 97,
    "agua y refrescos|isotonico y energetico": 97,
    "aperitivos|patatas fritas y snacks": 131,
    "aperitivos|aceitunas y encurtidos": 140,
    "aperitivos|frutos secos y fruta desecada": 127,
    "arroz, legumbres y pasta|arroz": 134,
    "arroz, legumbres y pasta|legumbres": 138,
    "arroz, legumbres y pasta|pasta y fideos": 134,
    "azucar, caramelos y chocolate|chocolate": 87,
    "azucar, caramelos y chocolate|azucar y edulcorante": 135,
    "azucar, caramelos y chocolate|mermelada y miel": 130,
    "azucar, caramelos y chocolate|chicles y caramelos": 86,
    "azucar, caramelos y chocolate|golosinas": 88,
    "bebe|toallitas y panales": 92,
    "bebe|biberon y chupete": 91,
    "bebe|alimentacion infantil": 90,
    "bebe|higiene y cuidado": 91,
    "bodega|vino tinto": 98,
    "bodega|vino blanco": 98,
    "bodega|vino rosado": 98,
    "bodega|vino lambrusco y espumoso": 98,
    "bodega|sidra y cava": 98,
    "bodega|tinto de verano y sangria": 98,
    "bodega|cerveza": 95,
    "bodega|cerveza sin alcohol": 95,
    "bodega|licores": 96,
    "cacao, cafe e infusiones|cafe capsula y monodosis": 125,
    "cacao, cafe e infusiones|cafe molido y en grano": 125,
    "cacao, cafe e infusiones|cafe soluble y otras bebidas": 125,
    "cacao, cafe e infusiones|cacao soluble y chocolate a la taza": 125,
    "cacao, cafe e infusiones|te e infusiones": 132,
    "carne|aves y pollo": 105,
    "carne|cerdo": 101,
    "carne|vacuno": 106,
    "carne|conejo y cordero": 103,
    "carne|hamburguesas y picadas": 100,
    "carne|empanados y elaborados": 100,
    "carne|arreglos": 100,
    "carne|embutido": 102,
    "carne|carne congelada": 100,
    "cereales y galletas|cereales": 126,
    "cereales y galletas|galletas": 128,
    "cereales y galletas|tortitas": 128,
    "charcuteria y quesos|aves y jamon cocido": 102,
    "charcuteria y quesos|bacon y salchichas": 102,
    "charcuteria y quesos|chopped y mortadela": 102,
    "charcuteria y quesos|jamon serrano": 102,
    "charcuteria y quesos|embutido curado": 102,
    "charcuteria y quesos|pate y sobrasada": 102,
    "charcuteria y quesos|queso curado, semicurado y tierno": 157,
    "charcuteria y quesos|queso lonchas, rallado y en porciones": 157,
    "charcuteria y quesos|queso untable, fresco y especialidades": 157,
    "congelados|pescado": 108,
    "congelados|marisco": 108,
    "congelados|verdura": 109,
    "congelados|helados": 107,
    "congelados|tartas y churros": 107,
    "congelados|pizzas": 108,
    "congelados|rebozados": 108,
    "congelados|arroz y pasta": 108,
    "congelados|hielo": 107,
    "conservas, caldos y cremas|atun y otras conservas de pescado": 110,
    "conservas, caldos y cremas|berberechos y mejillones": 110,
    "conservas, caldos y cremas|conservas de verdura y frutas": 113,
    "conservas, caldos y cremas|tomate": 113,
    "conservas, caldos y cremas|sopa y caldo": 112,
    "conservas, caldos y cremas|gazpacho y cremas": 112,
    "cuidado del cabello|champu": 115,
    "cuidado del cabello|acondicionador y mascarilla": 115,
    "cuidado del cabello|coloracion cabello": 115,
    "cuidado del cabello|fijacion cabello": 115,
    "cuidado facial y corporal|gel y jabon de manos": 118,
    "cuidado facial y corporal|cuidado corporal": 118,
    "cuidado facial y corporal|higiene bucal": 117,
    "cuidado facial y corporal|desodorante": 116,
    "cuidado facial y corporal|afeitado y cuidado para hombre": 124,
    "cuidado facial y corporal|perfume y colonia": 123,
    "cuidado facial y corporal|manicura y pedicura": 121,
    "cuidado facial y corporal|depilacion": 121,
    "cuidado facial y corporal|higiene intima": 119,
    "cuidado facial y corporal|cuidado e higiene facial": 114,
    "cuidado facial y corporal|protector solar y aftersun": 114,
    "fitoterapia y parafarmacia|parafarmacia": 122,
    "fitoterapia y parafarmacia|fitoterapia": 122,
    "fruta y verdura|fruta": 142,
    "fruta y verdura|verdura": 144,
    "fruta y verdura|lechuga y ensalada preparada": 144,
    "huevos, leche y mantequilla|huevos": 153,
    "huevos, leche y mantequilla|leche y bebidas vegetales": 154,
    "huevos, leche y mantequilla|mantequilla y margarina": 155,
    "limpieza y hogar|detergente y suavizante ropa": 146,
    "limpieza y hogar|limpieza cocina": 149,
    "limpieza y hogar|insecticida y ambientador": 145,
    "limpieza y hogar|menaje y conservacion de alimentos": 151,
    "limpieza y hogar|papel y bolsas": 151,
    "limpieza y hogar|limpieza bano": 149,
    "limpieza y hogar|limpieza suelos y hogar": 149,
    "limpieza y hogar|lavavajillas": 147,
    "limpieza y hogar|lejia y desinfectante": 148,
    "maquillaje|labios": 120,
    "maquillaje|ojos": 120,
    "maquillaje|bases de maquillaje y corrector": 120,
    "maquillaje|unas": 121,
    "maquillaje|rostro": 120,
    "marisco y pescado|pescado fresco": 168,
    "marisco y pescado|marisco fresco": 166,
    "marisco y pescado|moluscos": 167,
    "mascotas|perro": 162,
    "mascotas|gato": 161,
    "mascotas|otros animales": 161,
    "mascotas|arena para gatos": 160,
    "mascotas|accesorios": 159,
    "panaderia y pasteleria|pan de horno": 164,
    "panaderia y pasteleria|bolleria de horno": 163,
    "panaderia y pasteleria|bolleria envasada": 163,
    "panaderia y pasteleria|pasteles y tartas": 165,
    "panaderia y pasteleria|pan de molde y otras especialidades": 164,
    "panaderia y pasteleria|pan sin gluten": 164,
    "panaderia y pasteleria|harina y preparado reposteria": 137,
    "pizzas y platos preparados|platos preparados calientes": 171,
    "pizzas y platos preparados|pizzas": 108,
    "pizzas y platos preparados|ensaladas y platos frios": 170,
    "pizzas y platos preparados|bocadillos": 169,
    "pizzas y platos preparados|pasta y arroces preparados": 171,
    "postres y yogures|yogur natural": 158,
    "postres y yogures|yogur con frutas y sabores": 158,
    "postres y yogures|yogur griego y skyr": 158,
    "postres y yogures|yogures liquidos": 158,
    "postres y yogures|postres lacteos": 156,
    "postres y yogures|nata y crema": 155,
    "postres y yogures|kefir y otros fermentados": 158,
    "panaderia y pasteleria|picos, rosquilletas y picatostes": 129,
    "panaderia y pasteleria|pan tostado y rallado": 164,
    "limpieza y hogar|utensilios de limpieza y calzado": 151,
    "limpieza y hogar|estropajo, bayeta y guantes": 151,
    "limpieza y hogar|lejia y liquidos fuertes": 148,
    "limpieza y hogar|limpieza vajilla": 147,
    "limpieza y hogar|limpiahogar y friegasuelos": 149,
    "limpieza y hogar|papel higienico y celulosa": 151,
    "limpieza y hogar|limpieza bano y wc": 149,
    "limpieza y hogar|limpieza muebles y multiusos": 149,
    "maquillaje|colorete y polvos": 120,
    "zumos|fruta variada": 99,
    "postres y yogures|gelatina y otros postres": 156,
    "postres y yogures|yogures naturales y sabores": 158,
    "postres y yogures|bifidus": 158,
    "postres y yogures|yogures desnatados": 158,
    "postres y yogures|flan y natillas": 156,
    "pizzas y platos preparados|listo para comer": 171,
    "marisco y pescado|salazones y ahumados": 168,
    "panaderia y pasteleria|velas y decoracion": 89,
    "pizzas y platos preparados|platos preparados frios": 171,
    "marisco y pescado|marisco": 166,
    "limpieza y hogar|pilas y bolsas de basura": 151,
    "zumos|naranja": 99,
    "zumos|melocoton y pina": 99,
    "zumos|tomate y otros sabores": 99,
    "postres y yogures|yogures griegos": 158,
    "postres y yogures|postres de soja": 156,
    "postres y yogures|yogures y postres infantiles": 158,
    "mascotas|otros": 161,
    "limpieza y hogar|limpiacristales": 149,
    "panaderia y pasteleria|tartas y pasteles": 165,
    "maquillaje|pinceles y brochas": 121,
}

# ── MAPPING Alcampo → id_categoria. Solo las categorías de Alcampo que
# mapean limpiamente a UNA sola de nuestras 87 (las "cestas mixtas" tipo
# "Galletas y bollería" se dejan para la Capa 2 de palabras clave, que
# clasifica producto a producto con más precisión). ─────────────────────
MAPPING_ALCAMPO = {
    "OC1001": 154,   # Leche
    "OC1701": 142,   # Fruta fresca
    "OC1702": 144,   # Verdura y hortaliza fresca
    "OC1401": 168,   # Pescado fresco
    "OC100302": 127, # Frutos secos y snacks
    "OC1003": 133,   # Aceites y vinagres
    "OC1006": 140,   # Salsas, especias y condimentos
    "OC1008": 125,   # Café e infusiones
    "OC1009": 135,   # Azúcar y edulcorantes
    "OC1010": 98,    # Vinos y cavas
    "OC1011": 95,    # Cervezas
    "OC069":  122,   # Parafarmacia
    "OC063":  162,   # Mascotas - Perros
    "OC064":  161,   # Mascotas - Gatos
}

# ── MAPPING DIA -> id_categoria. Clave: (categoria_dia.lower(), subcategoria_dia.lower()) ──
MAPPING_DIA = {
    ("quesos", "curado"): 157,
    ("quesos", "fresco"): 157,
    ("quesos", "azul y de cabra"): 157,
    ("quesos", "untable y en porciones"): 157,
    ("quesos", "especialidades"): 157,
    ("quesos", "en lonchas"): 157,
    ("quesos", "semicurado"): 157,
    ("quesos", "tierno"): 157,
    ("quesos", "rallado"): 157,
    ("carnes", "vacuno"): 106,
    ("carnes", "cerdo"): 101,
    ("carnes", "pavo"): 104,
    ("carnes", "conejo"): 100,
    ("carnes", "hamburguesas carne picada y albondigas"): 100,
    ("carnes", "pollo"): 105,
    ("carnes", "empanados y elaborados"): 100,
    ("carnes", "arreglos y despieces"): 100,
    ("pescados y mariscos", "fresco"): 168,
    ("pescados y mariscos", "ahumado y salazon"): 168,
    ("pescados y mariscos", "surimi y elaborados"): 168,
    ("pescados y mariscos", "congelado"): 168,
    ("pescados y mariscos", "rebozado"): 168,
    ("pescados y mariscos", "marisco gamba y calamar"): 166,
    ("verduras", "ajos cebollas y puerros"): 144,
    ("verduras", "tomates pimientos y pepinos"): 144,
    ("verduras", "brocoli coliflor y judias verdes"): 144,
    ("verduras", "verduras congeladas y al vapor"): 109,
    ("verduras", "conservas de verduras"): 113,
    ("verduras", "lechugas y hojas verdes"): 144,
    ("verduras", "patatas y zanahorias"): 144,
    ("verduras", "setas y champinones"): 143,
    ("verduras", "ensaladas y verduras preparadas"): 144,
    ("verduras", "hierbas aromaticas"): 144,
    ("verduras", "calabacin calabaza y berenjena"): 144,
    ("frutas", "manzanas y peras"): 142,
    ("frutas", "platanos y bananas"): 142,
    ("frutas", "uvas"): 142,
    ("frutas", "frutos rojos y del bosque"): 142,
    ("frutas", "frutas tropicales"): 142,
    ("frutas", "frutas de temporada"): 142,
    ("frutas", "naranjas mandarinas y limones"): 142,
    ("frutas", "melon y sandia"): 142,
    ("frutas", "frutas congeladas"): 142,
    ("arroz pastas y legumbres", "arroz"): 134,
    ("arroz pastas y legumbres", "quinoa couscous y soja"): 134,
    ("arroz pastas y legumbres", "macarrones espaguetis y pastas secas"): 134,
    ("arroz pastas y legumbres", "garbanzos y alubias"): 138,
    ("arroz pastas y legumbres", "lentejas"): 138,
    ("arroz pastas y legumbres", "fideos"): 134,
    ("arroz pastas y legumbres", "pastas rellenas y en salsa"): 134,
    ("arroz pastas y legumbres", "lasana y canelones"): 134,
    ("arroz pastas y legumbres", "noodles"): 134,
    ("arroz pastas y legumbres", "pastas sin gluten"): 134,
    ("arroz pastas y legumbres", "salsas para pasta"): 140,
    ("aceites salsas y especias", "aceites"): 133,
    ("aceites salsas y especias", "vinagres y alinos"): 141,
    ("aceites salsas y especias", "ajo sal y pimienta"): 136,
    ("aceites salsas y especias", "ketchup mayonesa y mostaza"): 140,
    ("aceites salsas y especias", "salsas de tomate y pasta"): 140,
    ("aceites salsas y especias", "especias y hierbas"): 136,
    ("aceites salsas y especias", "sazonadores"): 136,
    ("aceites salsas y especias", "salsas especiales y picantes"): 140,
    ("huevos leche y mantequilla", "leche"): 154,
    ("huevos leche y mantequilla", "bebidas vegetales y horchatas"): 154,
    ("huevos leche y mantequilla", "batidos"): 154,
    ("huevos leche y mantequilla", "nata"): 155,
    ("huevos leche y mantequilla", "huevos"): 153,
    ("huevos leche y mantequilla", "mantequilla y margarina"): 155,
    ("huevos leche y mantequilla", "leche sin lactosa y enriquecidas"): 154,
    ("huevos leche y mantequilla", "leche infantil"): 90,
    ("huevos leche y mantequilla", "leche condensada y evaporada"): 154,
    ("cafe cacao e infusiones", "capsulas compatibles nespresso"): 125,
    ("cafe cacao e infusiones", "cacao y chocolate a la taza"): 125,
    ("cafe cacao e infusiones", "infusiones"): 132,
    ("cafe cacao e infusiones", "capsulas compatibles dolce gusto"): 125,
    ("cafe cacao e infusiones", "otras capsulas compatibles"): 125,
    ("cafe cacao e infusiones", "cafe molido"): 125,
    ("cafe cacao e infusiones", "cafe soluble"): 125,
    ("cafe cacao e infusiones", "cafe en grano"): 125,
    ("cafe cacao e infusiones", "cafes frios"): 125,
    ("cafe cacao e infusiones", "te"): 132,
    ("chocolates y golosinas", "chocolatinas y bombones"): 87,
    ("chocolates y golosinas", "golosinas"): 88,
    ("chocolates y golosinas", "cremas de cacao y de untar"): 130,
    ("chocolates y golosinas", "chocolate con leche"): 87,
    ("chocolates y golosinas", "chocolate negro"): 87,
    ("chocolates y golosinas", "chocolate blanco"): 87,
    ("chocolates y golosinas", "chicles y caramelos"): 85,
    ("galletas cereales y mermeladas", "mermeladas"): 130,
    ("galletas cereales y mermeladas", "galletas clasicas y digestive"): 128,
    ("galletas cereales y mermeladas", "galletas saladas y crackers"): 129,
    ("galletas cereales y mermeladas", "cereales"): 126,
    ("galletas cereales y mermeladas", "tortitas"): 126,
    ("galletas cereales y mermeladas", "galletas de chocolate y rellenas"): 128,
    ("galletas cereales y mermeladas", "cereales integrales y muesli"): 126,
    ("galletas cereales y mermeladas", "barritas de cereales y proteinas"): 126,
    ("galletas cereales y mermeladas", "galletas cereales y tortitas sin gluten"): 128,
    ("panaderia", "pan de molde y especiales"): 164,
    ("panaderia", "pan recien horneado"): 164,
    ("panaderia", "pan rallado tostado y picos"): 164,
    ("panaderia", "pan para hamburguesas y perritos"): 164,
    ("panaderia", "tortillas de trigo y pitas"): 164,
    ("panaderia", "masas y hojaldres"): 163,
    ("panaderia", "pan sin gluten"): 164,
    ("panaderia", "horno"): 163,
    ("yogures y postres", "yogures bifidus y colesterol"): 158,
    ("yogures y postres", "yogures naturales y desnatados"): 158,
    ("yogures y postres", "yogures de sabores y frutas"): 158,
    ("yogures y postres", "yogures griegos"): 158,
    ("yogures y postres", "yogures y postres infantiles"): 90,
    ("yogures y postres", "kefir y postres vegetales"): 156,
    ("yogures y postres", "postres tradicionales"): 156,
    ("yogures y postres", "natillas flan y arroz con leche"): 156,
    ("yogures y postres", "gelatinas y cuajadas"): 156,
    ("yogures y postres", "postres y batidos de proteinas"): 156,
    ("yogures y postres", "yogures liquidos"): 158,
    ("conservas caldos y cremas", "conservas de verdura"): 113,
    ("conservas caldos y cremas", "caldos y sopas"): 112,
    ("conservas caldos y cremas", "cremas y pures"): 112,
    ("conservas caldos y cremas", "atun y bonito"): 110,
    ("conservas caldos y cremas", "mejillones berberechos y pescado"): 110,
    ("conservas caldos y cremas", "caballa y sardinas"): 110,
    ("conservas caldos y cremas", "conservas de fruta"): 111,
    ("conservas caldos y cremas", "pates"): 102,
    ("aperitivos y frutos secos", "frutas deshidratadas"): 127,
    ("aperitivos y frutos secos", "aceitunas"): 131,
    ("aperitivos y frutos secos", "frutos secos"): 127,
    ("aperitivos y frutos secos", "patatas fritas"): 131,
    ("aperitivos y frutos secos", "snacks salados"): 131,
    ("aperitivos y frutos secos", "mix de frutos secos"): 127,
    ("aperitivos y frutos secos", "encurtidos"): 113,
    ("aperitivos y frutos secos", "snacks vegetales"): 131,
    ("platos preparados y pizzas", "pizzas refrigeradas"): 171,
    ("platos preparados y pizzas", "listos para comer"): 171,
    ("platos preparados y pizzas", "comida mexicana"): 171,
    ("platos preparados y pizzas", "sandwiches y hamburguesas"): 169,
    ("platos preparados y pizzas", "tortillas y empanadas"): 171,
    ("platos preparados y pizzas", "gazpachos y salmorejos"): 171,
    ("platos preparados y pizzas", "pizzas congeladas"): 108,
    ("platos preparados y pizzas", "comida tradicional"): 171,
    ("platos preparados y pizzas", "hummus y guacamoles"): 171,
    ("platos preparados y pizzas", "comida asiatica"): 171,
    ("platos preparados y pizzas", "ensaladas y bowls"): 170,
    ("agua y refrescos", "agua"): 94,
    ("agua y refrescos", "cola"): 97,
    ("agua y refrescos", "kombucha y aguas vitaminadas"): 97,
    ("agua y refrescos", "te frio"): 97,
    ("agua y refrescos", "tonica gaseosa y bitter"): 97,
    ("agua y refrescos", "bebidas isotonicas y deportivas"): 97,
    ("agua y refrescos", "refrescos sin gas"): 97,
    ("agua y refrescos", "naranja limon y lima-limon"): 97,
    ("agua y refrescos", "bebidas energeticas"): 97,
    ("agua y refrescos", "packs de agua y refrescos"): 94,
    ("cervezas vinos y licores", "cervezas"): 95,
    ("cervezas vinos y licores", "cervezas premium y especiales"): 95,
    ("cervezas vinos y licores", "cervezas sin alcohol"): 95,
    ("cervezas vinos y licores", "tinto de verano y sangria"): 98,
    ("cervezas vinos y licores", "vino tinto"): 98,
    ("cervezas vinos y licores", "vino blanco"): 98,
    ("cervezas vinos y licores", "cavas y sidra"): 98,
    ("cervezas vinos y licores", "vino rosado"): 98,
    ("cervezas vinos y licores", "ginebra vodka y tequila"): 96,
    ("cervezas vinos y licores", "vermouth y aperitivos"): 96,
    ("cervezas vinos y licores", "ron y whisky"): 96,
    ("cervezas vinos y licores", "cremas licores y brandy"): 96,
    ("cervezas vinos y licores", "cervezas con limon"): 95,
    ("cervezas vinos y licores", "packs de cervezas"): 95,
    ("congelados y helados", "helados y hielo"): 107,
    ("congelados y helados", "pizzas y masas"): 108,
    ("congelados y helados", "pescado y marisco"): 108,
    ("congelados y helados", "croquetas y rebozados"): 108,
    ("congelados y helados", "tartas y churros"): 107,
    ("congelados y helados", "arroces y pasta"): 108,
    ("congelados y helados", "verduras y patatas"): 109,
    ("infantil", "leches y papillas"): 90,
    ("infantil", "yogures y postres"): 90,
    ("infantil", "bolsitas y snacks"): 90,
    ("infantil", "potitos y tarritos"): 90,
    ("infantil", "panales y toallitas"): 92,
    ("infantil", "higiene y cuidado"): 91,
    ("infantil", "zumos y batidos"): 90,
    ("infantil", "galletas y bolleria"): 90,
    ("infantil", "golosinas y chocolatinas"): 90,
    ("limpieza y hogar", "estropajos bayetas y guantes"): 151,
    ("limpieza y hogar", "bolsas de basura escobas y fregonas"): 151,
    ("limpieza y hogar", "lejia y desinfectantes"): 148,
    ("limpieza y hogar", "limpieza suelos cristales y muebles"): 149,
    ("limpieza y hogar", "limpieza bano y wc"): 149,
    ("limpieza y hogar", "limpieza cocina y quitagrasas"): 149,
    ("limpieza y hogar", "lavavajillas"): 147,
    ("limpieza y hogar", "papel higienico cocina y servilletas"): 151,
    ("limpieza y hogar", "film aluminio y conservacion"): 151,
    ("limpieza y hogar", "detergentes"): 146,
    ("limpieza y hogar", "insecticidas"): 145,
    ("limpieza y hogar", "pilas menaje y bolsas"): 151,
    ("limpieza y hogar", "ambientadores recambios y velas"): 145,
    ("limpieza y hogar", "suavizantes y cuidado de la ropa"): 150,
    ("mascotas", "perro comida seca"): 162,
    ("mascotas", "gato comida seca"): 161,
    ("mascotas", "gato comida humeda"): 161,
    ("mascotas", "gato snacks y cuidado"): 161,
    ("mascotas", "perro comida humeda"): 162,
    ("mascotas", "perro snacks y cuidado"): 159,
    ("zumos y smoothies", "recien exprimido y fresco"): 99,
    ("zumos y smoothies", "naranja"): 99,
    ("zumos y smoothies", "melocoton y pina"): 99,
    ("zumos y smoothies", "multifrutas y otros sabores"): 99,
    ("zumos y smoothies", "fruta y leche"): 99,
    ("zumos y smoothies", "smoothies"): 99,
    ("zumos y smoothies", "packs de zumos"): 99,
    ("zumos y smoothies", "limonadas"): 99,
    ("higiene y cuidado del cuerpo", "afeitado"): 124,
    ("higiene y cuidado del cuerpo", "higiene bucal"): 117,
    ("higiene y cuidado del cuerpo", "hidratacion de cuerpo y manos"): 114,
    ("higiene y cuidado del cuerpo", "desodorantes"): 116,
    ("higiene y cuidado del cuerpo", "jabon de manos"): 118,
    ("higiene y cuidado del cuerpo", "compresas e higiene intima"): 119,
    ("higiene y cuidado del cuerpo", "depilacion"): 124,
    ("higiene y cuidado del cuerpo", "gel de ducha y esponjas"): 118,
    ("higiene y cuidado del cuerpo", "protector solar y aftersun"): 114,
    ("cabello y perfumeria", "champu"): 115,
    ("cabello y perfumeria", "acondicionadores y mascarillas"): 115,
    ("cabello y perfumeria", "espumas y fijadores"): 115,
    ("cabello y perfumeria", "tintes"): 115,
    ("cabello y perfumeria", "cuidado facial"): 114,
    ("cabello y perfumeria", "perfumes y colonias"): 123,
    ("salud y parafarmacia", "complementos nutricionales"): 122,
    ("salud y parafarmacia", "parafarmacia"): 122,
    ("salud y parafarmacia", "botiquin"): 122,
    ("salud y parafarmacia", "protector solar"): 114,
    ("bolleria reposteria y azucar", "azucar miel y edulcorantes"): 135,
    ("bolleria reposteria y azucar", "magdalenas y bolleria clasica"): 163,
    ("bolleria reposteria y azucar", "harinas y levaduras"): 137,
    ("bolleria reposteria y azucar", "preparados para postres y decoracion"): 137,
    ("bolleria reposteria y azucar", "bolleria de horno dulce"): 163,
    ("bolleria reposteria y azucar", "rosquillas y pastelitos"): 163,
    ("bolleria reposteria y azucar", "tartas"): 165,
    ("charcuteria", "jamon cocido"): 102,
    ("charcuteria", "jamon serrano"): 102,
    ("charcuteria", "lomo y chorizo"): 102,
    ("charcuteria", "pate y sobrasada"): 102,
    ("charcuteria", "salchichas"): 102,
    ("charcuteria", "chopped y mortadela"): 102,
    ("charcuteria", "pavo y pollo"): 102,
    ("charcuteria", "fuet y salchichon"): 102,
    ("charcuteria", "bacon"): 102,
}


RAIZ = Path(__file__).resolve().parents[1]
CARPETA_OLD = RAIZ / "old"

# ── Las 87 categorías reales (id, categoria, subcategoria) ────────────────
CATEGORIAS_MAESTRAS = {
    85: ("Azúcar, caramelos y chocolate", "Caramelos"),
    86: ("Azúcar, caramelos y chocolate", "Chicles"),
    87: ("Azúcar, caramelos y chocolate", "Chocolates y bombones"),
    88: ("Azúcar, caramelos y chocolate", "Golosinas"),
    89: ("Bazar y Varios", "Hogar y decoración"),
    90: ("Bebes", "Comida infantil"),
    91: ("Bebes", "Cuidado e higiene del bebé"),
    92: ("Bebes", "Pañales"),
    93: ("Bebes", "Toallitas y algodón"),
    94: ("Bebidas", "Agua"),
    95: ("Bebidas", "Cerveza"),
    96: ("Bebidas", "Licores y destilados"),
    97: ("Bebidas", "Refrescos"),
    98: ("Bebidas", "Vino"),
    99: ("Bebidas", "Zumos"),
    100: ("Carnicería y Charcutería", "Carne preparada"),
    101: ("Carnicería y Charcutería", "Cerdo"),
    102: ("Carnicería y Charcutería", "Charcuteria"),
    103: ("Carnicería y Charcutería", "Cordero"),
    104: ("Carnicería y Charcutería", "Pavo"),
    105: ("Carnicería y Charcutería", "Pollo"),
    106: ("Carnicería y Charcutería", "Vacuno"),
    107: ("Congelados", "Helados y postres congelados"),
    108: ("Congelados", "Platos congelados preparados"),
    109: ("Congelados", "Verduras congeladas"),
    110: ("Conservas y Enlatados", "Conservas de pescado y mariscos"),
    111: ("Conservas y Enlatados", "Frutas en almíbar"),
    112: ("Conservas y Enlatados", "Sopas, cremas y otros preparados"),
    113: ("Conservas y Enlatados", "Verduras, legumbres y hortalizas en conserva"),
    114: ("Cuidado personal e Higiene", "Cremas y protectores"),
    115: ("Cuidado personal e Higiene", "Cuidado del cabello"),
    116: ("Cuidado personal e Higiene", "Desodorantes"),
    117: ("Cuidado personal e Higiene", "Higiene bucal"),
    118: ("Cuidado personal e Higiene", "Higiene corporal"),
    119: ("Cuidado personal e Higiene", "Higiene íntima femenina"),
    120: ("Cuidado personal e Higiene", "Maquillaje"),
    121: ("Cuidado personal e Higiene", "Maquillaje y otros"),
    122: ("Cuidado personal e Higiene", "Parafarmacia"),
    123: ("Cuidado personal e Higiene", "Perfumes"),
    124: ("Cuidado personal e Higiene", "Productos de afeitado"),
    125: ("Desayuno y Snack", "Café y cacaos"),
    126: ("Desayuno y Snack", "Cereales para desayuno"),
    127: ("Desayuno y Snack", "Frutos secos embasados"),
    128: ("Desayuno y Snack", "Galletas dulces"),
    129: ("Desayuno y Snack", "Galletas saladas"),
    130: ("Desayuno y Snack", "Mermelada y Miel"),
    131: ("Desayuno y Snack", "Snack salados"),
    132: ("Desayuno y Snack", "Té e infusiones"),
    133: ("Despensa", "Aceites"),
    134: ("Despensa", "Arroz, pasta y quinoa"),
    135: ("Despensa", "Azúcares y edulcorantes"),
    136: ("Despensa", "Especias e hierbas secas"),
    137: ("Despensa", "Harinas"),
    138: ("Despensa", "Legumbres secas"),
    139: ("Despensa", "Sales"),
    140: ("Despensa", "Salsas, caldos y condimentos preparados"),
    141: ("Despensa", "Vinagres"),
    142: ("Frutas y Verduras", "Fruta"),
    143: ("Frutas y Verduras", "Setas"),
    144: ("Frutas y Verduras", "Verduras"),
    145: ("Hogar", "Ambientadores"),
    146: ("Hogar", "Detergentes para ropa"),
    147: ("Hogar", "Lavavajillas"),
    148: ("Hogar", "Lejia y desinfectantes"),
    149: ("Hogar", "Limpiadores de superficie"),
    150: ("Hogar", "Suavizantes"),
    151: ("Hogar", "Utensilios y consumibles de limpieza"),
    152: ("Lácteos y Huevos", "Grasas vegetales"),
    153: ("Lácteos y Huevos", "Huevos"),
    154: ("Lácteos y Huevos", 'Leche y bebidas "lácteas"'),
    155: ("Lácteos y Huevos", "Mantequillas y Natas"),
    156: ("Lácteos y Huevos", "Postres lácteos"),
    157: ("Lácteos y Huevos", "Quesos"),
    158: ("Lácteos y Huevos", "Yogures"),
    159: ("Mascotas", "Accesorios para perros"),
    160: ("Mascotas", "Arena y asea para gatos"),
    161: ("Mascotas", "Comida para otros animales"),
    162: ("Mascotas", "Comida para perros"),
    163: ("Panadería y Pastelería", "Bollos"),
    164: ("Panadería y Pastelería", "Pan fresco"),
    165: ("Panadería y Pastelería", "Pasteles y Tartas"),
    166: ("Pescadería", "Marisco"),
    167: ("Pescadería", "Moluscos"),
    168: ("Pescadería", "Pescado"),
    169: ("Platos preparados", "Bocadillos y Sándwich listos"),
    170: ("Platos preparados", "Ensaladas listas"),
    171: ("Platos preparados", "Platos preparados refrigerados"),
}

# ── Reglas: lista de (id_categoria, [frases clave]) EN ORDEN DE PRIORIDAD.
# Las más específicas van primero para evitar que una palabra genérica
# capture algo que pertenece a una categoría más concreta.
# ───────────────────────────────────────────────────────────────────────
REGLAS = [
    # --- Mascotas (muy específico, antes que "pollo"/"pavo" de carnicería) ---
    (162, ["pienso perro", "comida perro", "para perro", "snack perro", "snacks dental",
           "pedigree", "dentastix", "cesar natural", "cesar "]),
    (161, ["pienso gato", "comida gato", "para gato", "alimento gato", "whiskas", "friskies",
           "pienso conejo", "comida pajaro", "comida hamster"]),
    (160, ["arena gato", "arena para gatos"]),
    (159, ["correa perro", "juguete perro", "collar perro", "arnes perro"]),

    # --- Bebés (antes que lácteos/higiene genéricos) ---
    (92, ["pañal", "panal"]),
    (93, ["toallitas bebe", "toallitas infantil", "algodon bebe"]),
    (90, ["papilla", "potito", "leche infantil", "leche continuacion", "leche inicio",
          "cereales infantil", "alimentacion infantil", "tarrito bebe", "tarrito de"]),
    (91, ["colonia bebe", "champu bebe", "crema bebe", "aceite bebe", "jabon bebe"]),

    # --- Congelados (antes que pescado/verdura/carne frescos) ---
    (107, ["helado", "polo helado", "tarta helada", "hielo cubito", "hielo en cubito"]),
    (108, ["pizza congelada", "empanadillas congelad", "rebozado congelado",
           "nugget", "croqueta congelada", "canelones congelad", "lasagna congelad",
           "lasaña congelad", "varitas de merluza", "palitos de pescado congelad"]),
    (109, ["verdura congelada", "guisantes congelad", "espinacas congelad",
           "menestra congelad", "brocoli congelad", "arandanos congelad", "fruta congelada"]),

    # --- Conservas / caldos (antes que pescado/carne/verdura frescos) ---
    (110, ["atun en aceite", "atun en lata", "conserva de atun", "sardinas en aceite",
           "conserva de sardina", "mejillones en escabeche", "berberecho", "conserva de pescado"]),
    (111, ["melocoton en almibar", "fruta en almibar", "pina en almibar"]),
    (112, ["caldo de pollo", "caldo de carne", "caldo de verdura", "caldo de pescado",
           "sopa de", "crema de verdura", "gazpacho", "salmorejo", "pastilla de caldo",
           "avecrem"]),
    (113, ["tomate frito", "tomate triturado", "tomate natural lata", "legumbre en conserva",
           "garbanzos cocidos", "lentejas cocidas", "alubias cocidas", "maiz dulce lata",
           "verdura en conserva", "pisto"]),

    # --- Platos preparados (antes de que "pollo"/"ensalada" capturen mal) ---
    (163, ["masa de pizza", "masa para pizza", "masa fresca pizza", "masa fresca redonda"]),
    (169, ["bocadillo", "sandwich"]),
    (170, ["ensalada preparada", "ensalada lista", "ensalada de bolsa", "ensalada xtreme",
           "ensaladilla rusa", "ensaladilla"]),
    (171, ["plato preparado", "listo para comer", "wok de", "arroz tres delicias",
           "paella preparada", "canelones", "lasagna", "lasaña", "croquetas frescas",
           "pizza ", "porciones vegetarianas", "burger vegetal", "salteado de verdura"]),

    # --- Panadería y pastelería ---
    (163, ["napolitana", "croissant", "bolleria", "magdalena", "sobao", "palmera de",
           "bizcocho", "hojaldre", "masa quebrada", "masa de pizza", "masa para pizza"]),
    (165, ["tarta de", "pastel de", "milhojas"]),
    (164, ["pan de molde", "pan integral", "pan tostado", "pan rallado", "hogaza",
           "barra de pan", "pan sin gluten", "picos", "rosquilleta", "colines"]),

    # --- Desayuno y snack ---
    (125, ["cafe molido", "cafe soluble", "cafe capsula", "capsulas de cafe", "cacao soluble",
           "nescafe", "cafe en grano", "dolce gusto", "nespresso", "colacao", "cafe en capsula",
           "capsula de cafe", "cafe descafeinado", "petit nesquik", "batido de cacao"]),
    (132, ["te ", "infusion", "manzanilla bolsita", "poleo menta"]),
    (126, ["cereales desayuno", "copos de", "muesli", "granola"]),
    (127, ["frutos secos", "almendra", "nuez ", "avellana", "pistacho", "anacardo", "pipas"]),
    (128, ["galleta maria", "galletas dulces", "galleta chocolate", "oreo", "principe",
           "galletas rellenas"]),
    (129, ["galleta salada", "cracker", "tortitas de maiz", "tortitas de arroz"]),
    (130, ["mermelada", "miel de"]),
    (131, ["patatas fritas", "snack salado", "aperitivo salado", "gusanitos", "doritos",
           "takis", "cortezas", "risketos", "match ball", "bolitas de maiz", "garfitos",
           "aperitivo de maiz"]),

    # --- Azúcar, chocolate ---
    (87, ["chocolate con leche", "chocolate negro", "chocolate blanco", "bombon", "tableta de chocolate"]),
    (88, ["golosina", "chuche", "gominola", "regaliz", "licorice", "funky mix", "pica pica"]),
    (86, ["chicle"]),
    (85, ["caramelo"]),

    # --- Bebidas ---
    (95, ["cerveza"]),
    (98, ["vino tinto", "vino blanco", "vino rosado", "cava ", "vino crianza", "vino reserva",
          "vermut", "vermouth", "sangria", "tinto de verano"]),
    (96, ["ron ", "whisky", "ginebra", "vodka", "brandy", "licor de", "anis dulce", "orujo"]),
    (97, ["refresco", "tonica", "bitter", "cola zero", "cola light", "schweppes", "fanta",
          "pepsi", "coca cola", "seven up", "isotonico", "energetico", "monster ",
          "zumo shot", "granadina"]),
    (99, ["zumo de", "nectar de", "bebida de zumo"]),
    (94, ["agua mineral", "agua con gas", "agua sin gas"]),

    # --- Despensa ---
    (133, ["aceite de oliva", "aceite de girasol", "aceite vegetal"]),
    (141, ["vinagre"]),
    (139, ["sal marina", "sal fina", "sal gorda"]),
    (136, ["especias", "pimenton", "oregano", "comino", "canela en", "hierbas provenzales",
           "laurel", "curry"]),
    (140, ["salsa de tomate", "ketchup", "mostaza", "mayonesa", "salsa barbacoa",
           "salsa brava", "salsa mostaza", "salsa alioli", "condimento preparado"]),
    (137, ["harina de trigo", "harina integral", "levadura", "preparado reposteria"]),
    (135, ["azucar blanco", "azucar moreno", "edulcorante", "sacarina", "stevia"]),
    (134, ["arroz basmati", "arroz redondo", "arroz integral", "pasta italiana", "espaguetis",
           "macarrones", "fideos", "quinoa", "arroz bomba", "pasta penne", "penne",
           "tallarines", "canelones secos", "pasta seca"]),
    (138, ["lenteja", "garbanzo", "alubia", "judia seca"]),
    (137, ["harina de trigo", "harina integral", "levadura", "preparado reposteria",
           "preparado para crepes", "preparado para tortitas"]),

    # --- Frutas y verduras (frescas) ---
    (143, ["champinon", "seta ", "boletus", "hongo", "portobello"]),
    (142, ["manzana", "pera", "platano", "banana", "naranja", "mandarina", "fresa",
           "arandano", "uva", "melon", "sandia", "kiwi", "pina fresca", "nispero",
           "aguacate", "limon", "mango", "melocoton", "albaricoque", "cereza", "ciruela"]),
    (144, ["lechuga", "tomate fresco", "pepino", "pimiento", "calabacin", "cebolla",
           "patata", "zanahoria", "brocoli", "coliflor", "puerro", "calabaza", "berenjena",
           "espinaca fresca", "acelga", "judia verde", "col lombarda", "lombarda", "ajo",
           "yuca", "guisante ecologico", "guisante"]),

    # --- Hogar ---
    (146, ["detergente ropa", "detergente liquido", "detergente en polvo", "detergente capsulas",
           "detergente lavadora"]),
    (150, ["suavizante"]),
    (147, ["lavavajillas"]),
    (148, ["lejia", "desinfectante"]),
    (149, ["limpiador multiusos", "limpiacristales", "limpiahogar", "friegasuelos",
           "limpiador de", "quitagrasas", "limpiador bano", "limpiador cocina",
           "toallitas limpiadoras", "toallitas multiusos", "antical", "esponja jabonosa"]),
    (145, ["ambientador", "insecticida", "perfumador"]),
    (151, ["papel higienico", "papel de cocina", "bolsa de basura", "estropajo", "bayeta",
           "guantes de goma", "pilas alcalinas", "servilleta", "bolsas de congelacion",
           "cucharas de plastico", "cucharas reutilizables"]),
    (89, ["vela ", "decoracion hogar", "vaso reutilizable", "plato hondo", "ensaladera",
          "menaje de mesa"]),

    # --- Cuidado personal ---
    (117, ["dentifrico", "pasta de dientes", "enjuague bucal", "cepillo de dientes",
           "seda dental"]),
    (115, ["champu", "acondicionador", "mascarilla capilar", "tinte capilar",
           "coloracion cabello", "gel fijador", "laca para el cabello", "mascarilla cabello",
           "mascarilla para cabello"]),
    (116, ["desodorante", "antitranspirante"]),
    (124, ["espuma de afeitar", "afeitado", "cuchilla de afeitar", "maquinilla afeitar",
           "recambio gillette", "gillette"]),
    (123, ["perfume", "colonia", "agua de colonia", "eau de toilette", "eau de parfum"]),
    (119, ["compresa", "tampon", "salvaslip", "higiene intima"]),
    (118, ["gel de ducha", "jabon de manos", "jabon liquido", "gel de bano", "crema corporal",
           "locion corporal"]),
    (114, ["crema facial", "protector solar", "aftersun", "crema hidratante", "tonico facial"]),
    (120, ["maquillaje", "base de maquillaje", "corrector facial", "colorete", "mascara pestanas",
           "pintalabios", "labial", "corrector fluido"]),
    (121, ["esmalte de unas", "manicura", "pedicura", "cera depilatoria", "depilacion",
           "kit de pinceles", "pinceles de maquillaje"]),
    (122, ["parafarmacia", "vitamina ", "complemento alimenticio", "colageno",
           "tapones para los oidos", "parches termicos", "termacare"]),

    # --- Lácteos y huevos ---
    (153, ["huevo"]),
    (157, ["queso curado", "queso semicurado", "queso tierno", "queso rallado", "queso lonchas",
           "queso untable", "queso fresco", "queso crema", "queso de cabra", "queso de oveja",
           "philadelphia", "mozzarella", "parmesano"]),
    (158, ["yogur", "skyr", "kefir", "bifidus"]),
    (156, ["flan", "natillas", "postre lacteo", "postre de soja", "gelatina"]),
    (155, ["mantequilla", "nata para cocinar", "nata montar", "margarina"]),
    (152, ["grasa vegetal"]),
    (154, ["leche desnatada", "leche entera", "leche semidesnatada", "bebida de avena",
           "bebida de soja", "bebida de almendra", "bebida vegetal", "leche sin lactosa",
           "leche condensada", "bebida lactea"]),

    # --- Carnicería / charcutería ---
    (105, ["pollo", "pechuga de pollo", "muslo de pollo", "alitas de pollo", "jamoncito"]),
    (106, ["vacuno", "ternera", "solomillo de ternera", "filete de ternera", "carne picada de vacuno"]),
    (101, ["cerdo", "lomo de cerdo", "costilla de cerdo", "panceta", "chuleta de cerdo",
           "secreto iberico", "presa iberica"]),
    (103, ["cordero"]),
    (104, ["pavo"]),
    (102, ["jamon serrano", "jamon cocido", "jamon iberico", "chorizo", "salchichon", "mortadela",
           "bacon", "salchicha", "sobrasada", "pate", "fuet", "lomo embutido", "chopped"]),
    (100, ["hamburguesa", "carne picada", "albondiga", "empanado de pollo", "san jacobo"]),

    # --- Pescadería ---
    (166, ["langostino", "gamba", "marisco fresco", "cigala", "bogavante", "necora", "percebe"]),
    (167, ["mejillon fresco", "almeja", "berberecho fresco", "chirla", "sepia", "calamar", "pulpo"]),
    (168, ["merluza", "salmon", "atun fresco", "bacalao", "lubina", "dorada fresca",
           "dorada entera", "filete de dorada", "lomo de dorada", "boquerones",
           "sardina fresca", "rape", "gallo pescado", "pescadilla"]),

    # --- Catch-alls genéricos (baja prioridad: solo si nada más específico
    # coincidió antes). Palabras sueltas de una sola categoría dominante,
    # añadidas tras la segunda ronda de revisión de "sin_clasificar". ------
    (98, ["vino manzanilla", "vino frizzante", "vino "]),
    (99, ["zumo "]),
    (157, ["queso "]),
    (164, ["pan viena", "pan de pueblo", "chapata", "baguette", "pan "]),
    (97, ["cola ", "isotonica", "kombucha"]),
    (110, ["atun claro", "atun al natural", "mejillones en escabeche"]),
    (113, ["remolacha", "en su jugo"]),
    (111, ["pina en su jugo"]),
    (167, ["zamburina", "vieira", "mejillon"]),
    (154, ["fruta con leche"]),
    (128, ["barrita de galleta"]),
    (163, ["brownie"]),
    (165, ["tarta "]),
    (127, ["castana"]),
    (134, ["pasta fresca", "cappelleti", "noodles"]),
    (90, ["hero mi fruta", "bolsita de fruta", "leche de crecimiento",
          "preparado lacteo infantil", "pure de frutas"]),
    (88, ["banderilla"]),
    (96, ["bebida espirituosa"]),
    (125, ["tassimo"]),
    (102, ["lacon"]),
    (117, ["cepillo dental", "interproximales", "protesis dental"]),
    (149, ["desatascador", "escobilla"]),
    (151, ["quitapelusas", "bolsas basura", "bolsas microperforadas", "cierre zip"]),
    (122, ["balsamo", "spray nasal", "descongestion nasal", "arnica", "spf"]),
    (114, ["proteccion solar"]),
    (120, ["brillo de labios", "gloss"]),
    (118, ["crema de manos"]),
    (121, ["crema depilatoria"]),
    (146, ["detergente en pastilla", "detergente pastillas", "blanqueante"]),
    (123, ["body mist"]),
    (144, ["haba"]),
    (89, ["tealight", "velon"]),
    (171, ["migas manchegas", "migas "]),
    (107, ["granizado"]),
    (131, ["pringles"]),
    (134, ["espagueti"]),
    (96, ["tanqueray", "mojito"]),
    (98, ["sidra"]),
    (171, ["guacamole", "paella mixta", "paella "]),
    (165, ["tiramisu"]),
    (164, ["biscotte"]),
    (151, ["pila "]),
    (122, ["aposito", "carbonato de magnesio", "complemento nutricional"]),
    (97, ["champan infantil"]),
]

# Normalizar las reglas: quitar tildes para comparar sin acentos
NUMEROS_PALABRA_A_CIFRA = {
    "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5",
    "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10",
}
_RE_NUMERO_PALABRA = re.compile(
    r"\b(" + "|".join(NUMEROS_PALABRA_A_CIFRA.keys()) + r")\b"
)


def normalizar(t):
    t = (t or "").lower()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = _RE_NUMERO_PALABRA.sub(lambda m: NUMEROS_PALABRA_A_CIFRA[m.group(1)], t)
    return re.sub(r"\s+", " ", t).strip()


REGLAS_NORM = [(cat_id, [normalizar(kw) for kw in keywords]) for cat_id, keywords in REGLAS]

# Compilar cada keyword como regex de PALABRA/FRASE con límite al INICIO y
# sufijo de plural opcional (s|es) al final — así "caramelo" también casa
# con "caramelos", "yogur" con "yogures", sin caer en falsos positivos por
# subcadena a mitad de palabra (ej. "te " dentro de "aceite").
REGLAS_COMPILADAS = [
    (cat_id, [re.compile(r"\b" + re.escape(kw.strip()) + r"(?:s|es)?\b") for kw in keywords])
    for cat_id, keywords in REGLAS_NORM
]


def clasificar_texto(texto):
    t = normalizar(texto)
    for cat_id, patrones in REGLAS_COMPILADAS:
        for patron in patrones:
            if patron.search(t):
                return cat_id
    return None


def mas_reciente(patron):
    candidatos = sorted(glob.glob(str(CARPETA_OLD / patron)))
    return candidatos[-1] if candidatos else None


def cargar_categoria_real_mercadona():
    """Devuelve dict id_mercadona -> id_categoria, usando el export original
    (categoria_mercadona/subcategoria_mercadona) + el MAPPING oficial."""
    ruta = mas_reciente("export_precios_mercadona_*.csv")
    if not ruta:
        print("  ⚠️  No se encontró export_precios_mercadona_*.csv — se omite Capa 1")
        return {}

    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    resultado = {}
    sin_mapping = Counter()
    for r in filas:
        cat = r.get("categoria_mercadona", "")
        subcat = r.get("subcategoria_mercadona", "")
        if not cat or not subcat:
            continue
        clave = f"{normalizar(cat)}|{normalizar(subcat)}"
        id_cat = MAPPING_MERCADONA.get(clave)
        if id_cat:
            resultado[r["id"]] = id_cat
        else:
            sin_mapping[clave] += 1

    print(f"  📥 {ruta}")
    print(f"  {len(resultado):,} productos Mercadona con categoría real mapeada")
    if sin_mapping:
        print(f"  ⚠️  {sum(sin_mapping.values())} filas con categoría Mercadona sin mapping conocido")
    return resultado


def cargar_categoria_real_alcampo():
    """Devuelve dict id_alcampo -> id_categoria, decodificando el código
    interno (ej. 'OC1701') con MAPPING_ALCAMPO. No necesita re-scrapear:
    el código ya estaba guardado en la BBDD, solo estaba sin decodificar."""
    ruta = mas_reciente("export_precios_alcampo_*.csv")
    if not ruta:
        print("  ⚠️  No se encontró export_precios_alcampo_*.csv — se omite Capa 1b")
        return {}

    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    resultado = {}
    for r in filas:
        codigo = (r.get("categoria") or "").strip()
        id_cat = MAPPING_ALCAMPO.get(codigo)
        if id_cat:
            resultado[r["id"]] = id_cat

    print(f"  📥 {ruta}")
    print(f"  {len(resultado):,} productos Alcampo con categoría real decodificada")
    return resultado


def cargar_categoria_real_dia():
    """Devuelve dict id_dia -> id_categoria, usando categoria_dia/
    subcategoria_dia (nuevo desde el 10/08/2026, scraper reescrito) +
    MAPPING_DIA."""
    ruta = mas_reciente("export_precios_dia_*.csv")
    if not ruta:
        print("  ⚠️  No se encontró export_precios_dia_*.csv — se omite Capa 1c")
        return {}

    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    resultado = {}
    sin_mapping = Counter()
    for r in filas:
        cat = (r.get("categoria_dia") or "").strip().lower()
        subcat = (r.get("subcategoria_dia") or "").strip().lower()
        if not cat or not subcat:
            continue
        id_cat = MAPPING_DIA.get((cat, subcat))
        if id_cat:
            resultado[r["id"]] = id_cat
        else:
            sin_mapping[(cat, subcat)] += 1

    print(f"  📥 {ruta}")
    print(f"  {len(resultado):,} productos DIA con categoría real mapeada")
    if sin_mapping:
        print(f"  ⚠️  {sum(sin_mapping.values())} filas con categoría DIA sin mapping conocido")
    return resultado


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--umbral-vecino", type=int, default=UMBRAL_VECINO)
    ap.add_argument("--activar-vecino", action="store_true",
                     help="Reactiva la Capa 3 (vecino más cercano). No recomendado: "
                          "produce errores incluso a umbrales altos (ver pruebas).")
    args = ap.parse_args()
    umbral_vecino = args.umbral_vecino

    print("=" * 60)
    print("  🏷️  CLASIFICAR CATEGORÍA — Fase 4b (3 capas, sin coste)")
    print(f"  Umbral vecino más cercano: {umbral_vecino}")
    print("=" * 60)

    ruta = mas_reciente("miembros_finales_*.csv")
    if not ruta:
        print(f"\n❌ No se encontró miembros_finales_*.csv en {CARPETA_OLD}")
        print("   Ejecuta primero: python scrapers/construir_propuesta_final.py")
        return

    print(f"\n📥 {ruta}")
    with open(ruta, encoding="utf-8") as f:
        miembros = list(csv.DictReader(f))

    por_cluster = defaultdict(list)
    for m in miembros:
        por_cluster[m["cluster_id"]].append(m)
    print(f"  {len(por_cluster):,} clusters")

    # ── CAPA 1: categoría real de Mercadona ──────────────────────────────
    print("\n🥇 CAPA 1 — Categoría real de Mercadona...")
    cat_real_mercadona = cargar_categoria_real_mercadona()

    resultados = {}
    contador = Counter()

    for cid, filas in por_cluster.items():
        id_cat_real = None
        for f in filas:
            if f["super"] == "Mercadona" and f["id_super"] in cat_real_mercadona:
                id_cat_real = cat_real_mercadona[f["id_super"]]
                break
        if id_cat_real:
            categoria, subcategoria = CATEGORIAS_MAESTRAS[id_cat_real]
            resultados[cid] = {
                "cluster_id": cid, "id_categoria": id_cat_real,
                "categoria": categoria, "subcategoria": subcategoria,
                "origen": "mercadona_real", "nombre_representativo": filas[0]["nombre_original"],
            }
            contador["mercadona_real"] += 1

    print(f"  {contador['mercadona_real']:,} clusters con categoría real de Mercadona")

    # ── CAPA 1b: categoría real de Alcampo (decodificada, sin re-scrapear) ──
    print("\n🥇 CAPA 1b — Categoría real de Alcampo (decodificada)...")
    cat_real_alcampo = cargar_categoria_real_alcampo()

    for cid, filas in por_cluster.items():
        if cid in resultados:
            continue
        id_cat_real = None
        for f in filas:
            if f["super"] == "Alcampo" and f["id_super"] in cat_real_alcampo:
                id_cat_real = cat_real_alcampo[f["id_super"]]
                break
        if id_cat_real:
            categoria, subcategoria = CATEGORIAS_MAESTRAS[id_cat_real]
            resultados[cid] = {
                "cluster_id": cid, "id_categoria": id_cat_real,
                "categoria": categoria, "subcategoria": subcategoria,
                "origen": "alcampo_real", "nombre_representativo": filas[0]["nombre_original"],
            }
            contador["alcampo_real"] += 1

    print(f"  {contador['alcampo_real']:,} clusters adicionales con categoría real de Alcampo")

    # ── CAPA 1c: categoría real de DIA (nueva desde 10/08/2026) ──────────
    print("\n🥇 CAPA 1c — Categoría real de DIA...")
    cat_real_dia = cargar_categoria_real_dia()

    for cid, filas in por_cluster.items():
        if cid in resultados:
            continue
        id_cat_real = None
        for f in filas:
            if f["super"] == "DIA" and f["id_super"] in cat_real_dia:
                id_cat_real = cat_real_dia[f["id_super"]]
                break
        if id_cat_real:
            categoria, subcategoria = CATEGORIAS_MAESTRAS[id_cat_real]
            resultados[cid] = {
                "cluster_id": cid, "id_categoria": id_cat_real,
                "categoria": categoria, "subcategoria": subcategoria,
                "origen": "dia_real", "nombre_representativo": filas[0]["nombre_original"],
            }
            contador["dia_real"] += 1

    print(f"  {contador['dia_real']:,} clusters adicionales con categoría real de DIA")

    # ── CAPA 2: palabras clave ────────────────────────────────────────────
    print("\n🥈 CAPA 2 — Palabras clave...")
    for cid, filas in por_cluster.items():
        if cid in resultados:
            continue
        texto_conjunto = " | ".join(f["nombre_original"] for f in filas)
        cat_id = clasificar_texto(texto_conjunto)
        if cat_id:
            categoria, subcategoria = CATEGORIAS_MAESTRAS[cat_id]
            resultados[cid] = {
                "cluster_id": cid, "id_categoria": cat_id,
                "categoria": categoria, "subcategoria": subcategoria,
                "origen": "keyword", "nombre_representativo": filas[0]["nombre_original"],
            }
            contador["keyword"] += 1

    print(f"  {contador['keyword']:,} clusters adicionales por palabra clave")

    # ── CAPA 3: vecino más cercano — DESACTIVADA POR DEFECTO ─────────────
    # Se probó a varios umbrales (55/65/70/75/85/90) y incluso a 85 seguía
    # produciendo errores reales (ej. "Red Bull" -> Frutas, "Comida húmeda
    # gato" -> Vacuno). El bucket por primera palabra no es lo bastante
    # fiable. Se deja el código por si se quiere reactivar con --activar-
    # vecino, pero por defecto lo que no tiene Capa 1/2 va directo a
    # Bazar y Varios (categoría real, no un vacío -> sigue siendo 0
    # "sin categorizar" en el sentido estricto).
    if args.activar_vecino:
        print("\n🥉 CAPA 3 — Vecino más cercano (ACTIVADA manualmente)...")
    else:
        print("\n🥉 CAPA 3 — Vecino más cercano: DESACTIVADA (ver comentario en código).")
        print("   Usa --activar-vecino si quieres reactivarla (no recomendado, ver historial de pruebas).")

    STOP_WORDS = {"de", "con", "y", "sin", "para", "a", "en", "del", "la", "el", "los", "las"}

    def primera_palabra(t):
        for w in normalizar(t).split():
            if w not in STOP_WORDS and len(w) > 2:
                return w
        return normalizar(t).split()[0] if t.split() else ""

    if args.activar_vecino:
        buckets_categorizados = defaultdict(list)
        for cid, r in resultados.items():
            texto = por_cluster[cid][0]["nombre_original"]
            buckets_categorizados[primera_palabra(texto)].append((texto, r["id_categoria"]))

        pendientes = [cid for cid in por_cluster if cid not in resultados]
        for cid in pendientes:
            texto = por_cluster[cid][0]["nombre_original"]
            candidatos = buckets_categorizados.get(primera_palabra(texto), [])

            mejor_score, mejor_cat = 0, None
            for texto_c, cat_id in candidatos:
                score = fuzz.token_sort_ratio(normalizar(texto), normalizar(texto_c))
                if score > mejor_score:
                    mejor_score, mejor_cat = score, cat_id

            if mejor_cat and mejor_score >= umbral_vecino:
                categoria, subcategoria = CATEGORIAS_MAESTRAS[mejor_cat]
                resultados[cid] = {
                    "cluster_id": cid, "id_categoria": mejor_cat,
                    "categoria": categoria, "subcategoria": subcategoria,
                    "origen": "vecino_cercano", "nombre_representativo": texto,
                }
                contador["vecino_cercano"] += 1

        print(f"  {contador['vecino_cercano']:,} clusters adicionales por vecino más cercano")

    # ── Última red: lo que ni así encontró nada -> Bazar y Varios (89) ───
    for cid in por_cluster:
        if cid not in resultados:
            texto = por_cluster[cid][0]["nombre_original"]
            categoria, subcategoria = CATEGORIAS_MAESTRAS[89]
            resultados[cid] = {
                "cluster_id": cid, "id_categoria": 89,
                "categoria": categoria, "subcategoria": subcategoria,
                "origen": "sin_match_bazar", "nombre_representativo": texto,
            }
            contador["sin_match_bazar"] += 1

    if contador["sin_match_bazar"]:
        print(f"  ⚠️  {contador['sin_match_bazar']:,} clusters sin ningún match -> 'Bazar y Varios' por defecto")

    resultados_lista = list(resultados.values())

    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    ruta_salida = CARPETA_OLD / f"categorias_asignadas_{fecha}.csv"
    with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
        cols = ["cluster_id", "id_categoria", "categoria", "subcategoria", "origen", "nombre_representativo"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(resultados_lista)

    # muestra de lo asignado por vecino más cercano (menos fiable, para revisar)
    ruta_vecinos = CARPETA_OLD / f"revisar_vecino_cercano_{fecha}.csv"
    vecinos = [r for r in resultados_lista if r["origen"] in ("vecino_cercano", "sin_match_bazar")]
    with open(ruta_vecinos, "w", newline="", encoding="utf-8") as f:
        cols = ["cluster_id", "id_categoria", "categoria", "subcategoria", "origen", "nombre_representativo"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(vecinos)

    print(f"\n{'='*60}")
    print("  RESUMEN")
    print(f"{'='*60}")
    print(f"  Capa 1  (Mercadona real):  {contador['mercadona_real']:,}")
    print(f"  Capa 1b (Alcampo real):    {contador['alcampo_real']:,}")
    print(f"  Capa 1c (DIA real):        {contador['dia_real']:,}")
    print(f"  Capa 2  (palabra clave):   {contador['keyword']:,}")
    print(f"  Capa 3  (vecino cercano):  {contador['vecino_cercano']:,}")
    print(f"  Sin match (Bazar/Varios):  {contador['sin_match_bazar']:,}")
    print(f"  TOTAL clasificado:         {len(resultados_lista):,} / {len(por_cluster):,}  (100%)")

    dist = Counter(r["categoria"] for r in resultados_lista)
    print(f"\n  Distribución (top 15):")
    for cat, n in dist.most_common(15):
        print(f"    {cat:32s} {n:>5,}")

    print(f"\n✅ CSVs generados en {CARPETA_OLD}:")
    print(f"  {ruta_salida.name}")
    print(f"  {ruta_vecinos.name}  <- revisa esto (categorías menos fiables: {len(vecinos):,} filas)")


if __name__ == "__main__":
    main()
