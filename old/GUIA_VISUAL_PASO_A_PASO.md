# 🚀 GUÍA VISUAL: PASO A PASO PARA IMPORTAR PRODUCTOS

## 📂 PASO 0: ORGANIZAR ARCHIVOS

```
C:\Users\ccash\mi-mejor-cesta\
│
├── 📊 TUS DATOS
│   ├── MERCADONA_FINAL.csv              ← Ya lo tienes
│   ├── PRODUCTOS_GENERICOS_FIXED.csv    ← Ya lo tienes
│   └── productos_a_importar.csv         ← TÚ LO CREAS
│
├── 🐍 SCRIPTS (descargar y copiar aquí)
│   ├── analizar_antes_importar.py       ← NUEVO ⭐
│   ├── gestor_masivo.py
│   └── gestor_productos.py
│
└── 📤 output_sqls/ (se crea solo)
    └── (archivos SQL generados)
```

---

## 🎯 FLUJO COMPLETO (3 PASOS)

```
┌──────────────────────────────────────────────────────┐
│ PASO 1: ANALIZAR (antes de importar)                │
├──────────────────────────────────────────────────────┤
│ python analizar_antes_importar.py productos.csv     │
│                                                      │
│ ✅ Detecta duplicados                               │
│ ✅ Valida categorías                                │
│ ✅ Valida precios                                   │
│ ✅ Te dice QUÉ VA A PASAR                          │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ PASO 2: CORREGIR (si hay errores)                   │
├──────────────────────────────────────────────────────┤
│ - Editar CSV según recomendaciones                  │
│ - Volver a PASO 1                                   │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ PASO 3: IMPORTAR (cuando todo esté OK)              │
├──────────────────────────────────────────────────────┤
│ python gestor_masivo.py                             │
│ Opción 1 → Importar                                 │
│                                                      │
│ Ejecutar SQLs en Supabase                           │
└──────────────────────────────────────────────────────┘
```

---

# 📝 EJEMPLO PRÁCTICO COMPLETO

## Situación: "Tengo 20 productos nuevos en un Excel"

### 📊 PASO 1A: Crear CSV desde Excel

**En Excel:**
```
1. Abrir Excel con tus productos
2. Asegurarte que tiene estas columnas:
   - nombre_mercadona
   - precio
   - categoria
   - subcategoria
   
3. Guardar como → CSV (delimitado por comas)
4. Abrir el CSV con Notepad
5. Reemplazar todas las comas (,) por punto y coma (;)
6. Guardar
```

**Resultado: `mis_productos.csv`**
```csv
nombre_mercadona;precio;categoria;subcategoria
Aceite de oliva Hacendado 1L;4.50€;Despensa;Aceites
Leche Hacendado 1L;0.85€;Lácteos y Huevos;Leche y bebidas "lácteas"
```

---

### 🔍 PASO 1B: ANALIZAR PRIMERO

**Abrir terminal:**
```
Win + R
cmd
cd C:\Users\ccash\mi-mejor-cesta
```

**Ejecutar análisis:**
```bash
python analizar_antes_importar.py mis_productos.csv
```

---

### 📊 RESULTADO DEL ANÁLISIS:

```
================================================================================
🔍 ANÁLISIS DE PRODUCTOS - PREVIO A IMPORTACIÓN
================================================================================

📄 Archivo a analizar: mis_productos.csv

📊 RESUMEN INICIAL:
  - Productos en BD actual: 3898
  - Productos a importar: 20
  - Categorías válidas: 17

================================================================================
1️⃣ VERIFICACIÓN DE CATEGORÍAS
================================================================================

✅ Todas las categorías son válidas

================================================================================
2️⃣ DETECCIÓN DE DUPLICADOS
================================================================================

⚠️ DUPLICADOS EXACTOS ENCONTRADOS: 2

  Fila 3: Aceite de oliva Hacendado 1L
    ├─ YA EXISTE: ME-0234 - Aceite de oliva Hacendado 1L
    ├─ Precio nuevo: 4.50€ | Existente: 4.30€
    └─ 🔴 DUPLICADO TOTAL - No importar

  Fila 8: Leche Hacendado 1L
    ├─ YA EXISTE: ME-0045 - Leche Hacendado 1L
    ├─ Precio nuevo: 0.85€ | Existente: 0.80€
    └─ 🔴 DUPLICADO TOTAL - No importar

⚠️ ACCIÓN SUGERIDA:
  - Eliminar filas duplicadas del CSV
  - O usar Opción 2 para actualizar precios

🟡 DUPLICADOS SIMILARES ENCONTRADOS: 1

  Fila 15: Pan integral Hacendado
    ├─ Parecido a: ME-0567 - Pan integral 100% Hacendado
    └─ Similitud: 92.3%

⚠️ ACCIÓN SUGERIDA:
  - Revisar manualmente si son el mismo producto

================================================================================
3️⃣ PRODUCTOS TOTALMENTE NUEVOS
================================================================================

✅ PRODUCTOS TOTALMENTE NUEVOS: 17

  Fila 2: Yogur griego Hacendado
    └─ 1.50€ | Lácteos y Huevos → Yogures
  
  Fila 4: Arroz basmati Hacendado
    └─ 2.10€ | Despensa → Arroz pasta y quinoa
  
  ... y 15 productos más

✅ ACCIÓN: Estos productos se pueden importar sin problemas

================================================================================
4️⃣ VALIDACIÓN DE PRECIOS
================================================================================

✅ Todos los precios son válidos

================================================================================
📊 RESUMEN FINAL
================================================================================

📈 ESTADÍSTICAS:
  - Productos a importar: 20
  - Productos totalmente nuevos: 17
  - Duplicados exactos: 2
  - Duplicados similares: 1
  - Categorías inválidas: 0
  - Precios inválidos: 0

🎯 RECOMENDACIÓN:
  ⚠️ REVISAR - Hay 2 duplicados exactos

  Opciones:
    A) Eliminar duplicados del CSV y volver a analizar
    B) Usar 'gestor_masivo.py' Opción 2 para actualizar productos existentes
    C) Usar 'gestor_masivo.py' Opción 4 para reemplazar categoría completa

================================================================================
```

---

### 🛠️ PASO 2: CORREGIR SEGÚN ANÁLISIS

**Opción A: Eliminar duplicados del CSV**

1. Abrir `mis_productos.csv`
2. Eliminar filas 3 y 8 (duplicados)
3. Revisar fila 15 manualmente
4. Guardar CSV
5. Volver a ejecutar análisis:
   ```bash
   python analizar_antes_importar.py mis_productos.csv
   ```

**Ahora debería mostrar:**
```
🎯 RECOMENDACIÓN:
  ✅ LISTO PARA IMPORTAR
  
  Comando:
    python gestor_masivo.py
    Opción 1 → Añadir productos desde CSV
    Archivo: mis_productos.csv
```

---

**Opción B: Actualizar precios de duplicados**

Si quieres actualizar los precios de los productos que ya existen:

```bash
python gestor_masivo.py

👉 Opción: 2  (Cambiar categoría/precio)
👉 IDs: ME-0234,ME-0045
```

Pero esto solo cambia categorías, no precios. Para precios necesitas:
1. Ir a Supabase SQL Editor
2. Ejecutar:
```sql
UPDATE productos_mercadona SET precio = '4.50€' WHERE id_producto = 'ME-0234';
UPDATE productos_mercadona SET precio = '0.85€' WHERE id_producto = 'ME-0045';
```

---

### ✅ PASO 3: IMPORTAR (cuando análisis diga OK)

```bash
python gestor_masivo.py
```

**Menú:**
```
👉 Opción: 1
📄 Archivo CSV: mis_productos.csv

✅ Validación OK
✅ SQLs generados:
  📄 AÑADIR_MASIVO_MERCADONA_20260307_181022.sql
  📄 AÑADIR_MASIVO_GENERICOS_20260307_181022.sql
```

**En Supabase:**
1. SQL Editor
2. Copiar `AÑADIR_MASIVO_MERCADONA_....sql` → Ejecutar
3. Copiar `AÑADIR_MASIVO_GENERICOS_....sql` → Ejecutar

**Verificar:**
```sql
SELECT COUNT(*) FROM productos_mercadona;  -- Debe ser 3898 + 18 = 3916
```

---

# 🎓 CASOS PRÁCTICOS

## CASO 1: "No estoy segura si son nuevos o duplicados"

```bash
# Siempre ejecuta PRIMERO:
python analizar_antes_importar.py mi_archivo.csv

# Te dirá exactamente:
# - Cuáles son nuevos
# - Cuáles ya existen
# - Cuáles son similares
```

---

## CASO 2: "Algunos productos están mal categorizados"

**Si el análisis muestra:**
```
❌ CATEGORÍAS INVÁLIDAS: 3

  Fila 5: Aceite girasol
    └─ Categoría 'Bazar' no existe
```

**Solución:**
1. Ver categorías válidas:
   ```bash
   python gestor_masivo.py
   👉 5  (Ver categorías)
   ```

2. Editar CSV con categoría correcta

3. Volver a analizar

---

## CASO 3: "Voy a duplicar productos sin querer"

**El análisis te avisa ANTES:**
```
⚠️ DUPLICADOS EXACTOS: 5

  Fila 3: Leche Hacendado 1L
    └─ YA EXISTE: ME-0045
```

**Entonces puedes decidir:**
- ❌ Eliminar del CSV
- 🔄 Actualizar el existente (Opción 2)
- ✅ Importar de todas formas (si es intencional)

---

# 📋 CHECKLIST ANTES DE IMPORTAR

```
□ CSV tiene formato correcto (;)
□ Ejecuté: python analizar_antes_importar.py
□ Revisé el análisis completo
□ Corregí errores críticos (rojo)
□ Decidí qué hacer con duplicados (amarillo)
□ El análisis dice "✅ LISTO PARA IMPORTAR"
□ Hice backup de CSVs actuales
□ Ejecuté gestor_masivo.py → Opción 1
□ Revisé SQLs generados
□ Ejecuté en Supabase
□ Verifiqué totales después
```

---

# 🔍 COMANDOS RÁPIDOS

```bash
# Ver categorías disponibles
python gestor_masivo.py
👉 5

# Analizar CSV antes de importar
python analizar_antes_importar.py productos.csv

# Importar productos (después de analizar)
python gestor_masivo.py
👉 1
```

---

# ⚠️ ERRORES COMUNES

| Error | Causa | Solución |
|-------|-------|----------|
| `FileNotFoundError` | CSV no existe | Verificar nombre y ubicación |
| `Categoría no existe` | Categoría mal escrita | Usar opción 5 para ver válidas |
| `Precio inválido` | Falta € o formato malo | Asegurar que termina en € |
| `Duplicados exactos` | Producto ya existe | Eliminar del CSV o actualizar |

---

**¡NUNCA importes sin analizar primero!** 🚀
