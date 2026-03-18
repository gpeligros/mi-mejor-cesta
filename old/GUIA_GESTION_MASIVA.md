# 📊 GUÍA COMPLETA: GESTIÓN MASIVA DE PRODUCTOS

## 🎯 4 OPERACIONES PRINCIPALES:

### 1️⃣ AÑADIR PRODUCTOS MASIVAMENTE (sin eliminar)
### 2️⃣ CAMBIAR CATEGORÍA DE PRODUCTOS
### 3️⃣ ELIMINAR PRODUCTOS MAL CATEGORIZADOS
### 4️⃣ REEMPLAZAR PRODUCTOS (eliminar + añadir)

---

# 1️⃣ AÑADIR PRODUCTOS MASIVAMENTE

## 📝 Paso 1: Crear CSV

Crea archivo `nuevos_productos.csv`:

```csv
nombre_mercadona;precio;categoria;subcategoria
Aceite de oliva Hacendado 1L;4.50€;Despensa;Aceites
Leche entera Hacendado 1L;0.85€;Lácteos y Huevos;Leche y bebidas "lácteas"
Pan integral 400g;1.20€;Panadería y Pastelería;Pan fresco
```

**Formato obligatorio:**
- ✅ Separador: `;` (punto y coma)
- ✅ Precio: termina en `€`
- ✅ Categoría/subcategoría: deben existir en la BD

## 📝 Paso 2: Ejecutar script

```bash
python gestor_masivo.py
```

**Menú:**
```
1️⃣  Añadir productos desde CSV
👉 Opción: 1
📄 Archivo CSV: nuevos_productos.csv
```

## 📝 Paso 3: Revisar SQLs generados

Se crean 2 archivos en `output_sqls/`:
```
AÑADIR_MASIVO_MERCADONA_20260307_170522.sql
AÑADIR_MASIVO_GENERICOS_20260307_170522.sql
```

## 📝 Paso 4: Ejecutar en Supabase

1. Abrir SQL Editor en Supabase
2. Copiar y ejecutar: `AÑADIR_MASIVO_MERCADONA_...sql`
3. Copiar y ejecutar: `AÑADIR_MASIVO_GENERICOS_...sql`

**Verificar:**
```sql
SELECT COUNT(*) FROM productos_mercadona;  -- Aumentó en 3
SELECT COUNT(*) FROM productos_genericos;  -- Aumentó en 3
```

---

# 2️⃣ CAMBIAR CATEGORÍA DE PRODUCTOS

## Caso de uso:
**Tengo 10 productos mal categorizados en "Bazar y Varios" y quiero moverlos a "Despensa" → "Aceites"**

## 📝 Paso 1: Identificar IDs

```sql
-- Ver productos mal categorizados
SELECT id_producto, nombre, categoria, subcategoria 
FROM productos_mercadona 
WHERE categoria = 'Bazar y Varios';
```

Resultado:
```
ME-0550 | Aceite girasol | Bazar y Varios | Hogar y decoración
ME-0551 | Vinagre | Bazar y Varios | Hogar y decoración
ME-0552 | Sal marina | Bazar y Varios | Hogar y decoración
```

## 📝 Paso 2: Ejecutar recategorización

```bash
python gestor_masivo.py
```

**Menú:**
```
2️⃣  Cambiar categoría de productos
👉 Opción: 2
👉 IDs: ME-0550,ME-0551,ME-0552
📁 Nueva categoría: Despensa
📁 Nueva subcategoría: Aceites
```

## 📝 Paso 3: Ejecutar SQL en Supabase

```sql
-- Se genera: RECATEGORIZAR_MASIVO_20260307_170800.sql
-- Ejecutar en Supabase
```

**Verificar:**
```sql
SELECT id_producto, nombre, categoria, subcategoria 
FROM productos_mercadona 
WHERE id_producto IN ('ME-0550', 'ME-0551', 'ME-0552');

-- Resultado:
-- ME-0550 | Aceite girasol | Despensa | Aceites ✅
-- ME-0551 | Vinagre | Despensa | Aceites ✅
-- ME-0552 | Sal marina | Despensa | Aceites ✅
```

---

# 3️⃣ ELIMINAR PRODUCTOS MAL CATEGORIZADOS

## Caso de uso:
**Quiero borrar TODOS los productos de "Bazar y Varios" → "Hogar y decoración"**

## 📝 Paso 1: Ejecutar script

```bash
python gestor_masivo.py
```

**Menú:**
```
3️⃣  Eliminar productos por categoría
👉 Opción: 3
📁 Categoría a eliminar: Bazar y Varios
📁 Subcategoría (Enter para toda): Hogar y decoración
```

## 📝 Paso 2: Revisar SQL generado

```sql
-- ELIMINAR_POR_CATEGORIA_20260307_171000.sql

-- PASO 1: Ver productos que se eliminarán
SELECT id_producto, nombre FROM productos_mercadona 
WHERE categoria = 'Bazar y Varios' AND subcategoria = 'Hogar y decoración';

-- PASO 2: Eliminar (descomenta para ejecutar)
-- DELETE FROM productos_mercadona WHERE categoria = 'Bazar y Varios' AND subcategoria = 'Hogar y decoración';
-- DELETE FROM productos_genericos WHERE categoria = 'Bazar y Varios' AND subcategoria = 'Hogar y decoración';
```

## 📝 Paso 3: Ejecutar en Supabase

1. **Primero:** Ejecuta el SELECT para ver qué se eliminará
2. **Luego:** Quita los comentarios `--` de las líneas DELETE
3. **Ejecutar:** DELETE completo

**Verificar:**
```sql
SELECT COUNT(*) FROM productos_mercadona 
WHERE categoria = 'Bazar y Varios' AND subcategoria = 'Hogar y decoración';
-- Resultado: 0 (eliminados)
```

---

# 4️⃣ REEMPLAZAR PRODUCTOS (eliminar + añadir)

## Caso de uso:
**Tengo una nueva lista de 50 productos de "Despensa" → "Aceites" que quiero usar en vez de los actuales**

## 📝 Paso 1: Crear CSV con productos nuevos

`aceites_nuevos.csv`:
```csv
nombre_mercadona;precio;categoria;subcategoria
Aceite oliva virgen extra Hacendado 1L;4.50€;Despensa;Aceites
Aceite girasol Hacendado 1L;2.20€;Despensa;Aceites
Aceite de coco Hacendado 500ml;3.80€;Despensa;Aceites
...
```

## 📝 Paso 2: Ejecutar reemplazo

```bash
python gestor_masivo.py
```

**Menú:**
```
4️⃣  Reemplazar productos de categoría
👉 Opción: 4
📁 Categoría: Despensa
📁 Subcategoría: Aceites
📄 CSV con productos nuevos: aceites_nuevos.csv
```

**Qué hace:**
1. ❌ Elimina TODOS los productos de Despensa → Aceites
2. ✅ Añade los 50 productos del CSV
3. 🔢 Usa IDs consecutivos nuevos

## 📝 Paso 3: Ejecutar SQL en Supabase

```sql
-- REEMPLAZAR_CATEGORIA_20260307_171200.sql
-- Ejecutar completo
```

**Verificar:**
```sql
SELECT COUNT(*) FROM productos_mercadona 
WHERE categoria = 'Despensa' AND subcategoria = 'Aceites';
-- Resultado: 50 (nuevos productos)
```

---

# 🎯 FLUJOS DE TRABAJO COMPLETOS

## Escenario A: "Tengo 100 productos nuevos para añadir"

```bash
1. Crear: nuevos_100.csv
2. Ejecutar: python gestor_masivo.py → Opción 1
3. Revisar SQLs generados
4. Ejecutar en Supabase
```

---

## Escenario B: "30 productos están mal en 'Bazar y Varios', deben ir a 'Despensa'"

### Método 1: Recategorizar (mantiene IDs)
```bash
1. Buscar IDs en Supabase:
   SELECT id_producto FROM productos_mercadona WHERE categoria = 'Bazar y Varios'
   
2. Ejecutar: python gestor_masivo.py → Opción 2
   IDs: ME-0550,ME-0551,ME-0552,...
   Nueva cat: Despensa
   Nueva subcat: Aceites
   
3. Ejecutar SQL en Supabase
```

### Método 2: Eliminar + Añadir (nuevos IDs)
```bash
1. Crear CSV con productos correctos
2. Ejecutar: python gestor_masivo.py → Opción 3 (eliminar viejos)
3. Ejecutar: python gestor_masivo.py → Opción 1 (añadir nuevos)
```

---

## Escenario C: "Quiero actualizar toda la categoría 'Bebidas' con datos nuevos"

```bash
1. Crear: bebidas_actualizadas.csv (con TODOS los productos)
2. Ejecutar: python gestor_masivo.py → Opción 4
   Categoría: Bebidas
   Subcategoría: [dejar vacío para TODA la categoría]
   CSV: bebidas_actualizadas.csv
   
3. Ejecutar SQL en Supabase
```

---

# 📋 FORMATOS DE CSV

## CSV para añadir productos:
```csv
nombre_mercadona;precio;categoria;subcategoria
Producto con marca;4.50€;Categoría;Subcategoría
```

## CSV para recategorizar (alternativa):
Crear lista de IDs en TXT:
```
ME-0001
ME-0002
ME-0003
```

Luego: `ME-0001,ME-0002,ME-0003` en el script

---

# ⚠️ PRECAUCIONES

## ✅ SIEMPRE:
1. **Hacer backup** de CSVs antes de cambios masivos
2. **Ejecutar SELECT primero** antes de DELETE
3. **Verificar categorías válidas** antes de importar
4. **Revisar SQLs generados** antes de ejecutar

## ❌ NUNCA:
1. Ejecutar DELETE sin revisar qué se elimina
2. Importar CSV sin validar categorías
3. Cambiar categorías sin verificar que existen

---

# 🔍 VERIFICACIONES POST-OPERACIÓN

Después de cualquier operación masiva:

```sql
-- 1. Verificar totales
SELECT COUNT(*) FROM productos_mercadona;   -- Ej: 3948
SELECT COUNT(*) FROM productos_genericos;   -- Ej: 3948 (IGUAL)

-- 2. Verificar que IDs coinciden
SELECT COUNT(*) FROM productos_mercadona m
LEFT JOIN productos_genericos g ON m.id_producto = g.id_producto
WHERE g.id_producto IS NULL;
-- Resultado: 0 (todos coinciden)

-- 3. Verificar categorías válidas
SELECT DISTINCT p.categoria, p.subcategoria
FROM productos_mercadona p
LEFT JOIN categorias_maestras cm 
  ON p.categoria = cm.categoria AND p.subcategoria = cm.subcategoria
WHERE cm.id IS NULL;
-- Resultado: 0 (todas válidas)

-- 4. Verificar distribución por categoría
SELECT categoria, COUNT(*) as total
FROM productos_mercadona
GROUP BY categoria
ORDER BY total DESC;
```

---

# 🚀 EJEMPLOS PRÁCTICOS

## Ejemplo 1: Añadir 5 productos de aceites

**nuevos_aceites.csv:**
```csv
nombre_mercadona;precio;categoria;subcategoria
Aceite de oliva Hacendado 1L;4.50€;Despensa;Aceites
Aceite de girasol Hacendado 1L;2.20€;Despensa;Aceites
Aceite de coco Hacendado 500ml;3.80€;Despensa;Aceites
Vinagre de vino Hacendado 1L;0.90€;Despensa;Vinagres
Vinagre de manzana Hacendado 500ml;1.50€;Despensa;Vinagres
```

**Comandos:**
```bash
python gestor_masivo.py
👉 1
📄 nuevos_aceites.csv
```

---

## Ejemplo 2: Mover 3 productos a otra categoría

**IDs a mover:** ME-1200, ME-1201, ME-1202  
**De:** Bazar y Varios → Hogar y decoración  
**A:** Hogar → Limpiadores de superficie

**Comandos:**
```bash
python gestor_masivo.py
👉 2
👉 ME-1200,ME-1201,ME-1202
📁 Hogar
📁 Limpiadores de superficie
```

---

## Ejemplo 3: Eliminar categoría completa

**Eliminar:** Bazar y Varios (toda la categoría)

**Comandos:**
```bash
python gestor_masivo.py
👉 3
📁 Bazar y Varios
📁 [presionar Enter para toda la categoría]
```

---

# 📞 AYUDA RÁPIDA

**¿Cómo saber qué categorías existen?**
```bash
python gestor_masivo.py
👉 5
```

**¿Cómo buscar productos de una categoría?**
```sql
SELECT id_producto, nombre FROM productos_mercadona 
WHERE categoria = 'Despensa' AND subcategoria = 'Aceites';
```

**¿Cómo exportar productos para editarlos?**
```sql
-- En Supabase SQL Editor
COPY (
  SELECT nombre, precio, categoria, subcategoria 
  FROM productos_mercadona 
  WHERE categoria = 'Despensa'
) TO '/tmp/despensa.csv' DELIMITER ';' CSV HEADER;
```

**¿Formato del precio?**
→ Siempre `X.XX€` (ejemplo: 0.80€, 4.50€, 12.99€)

**¿Qué pasa si una categoría no existe?**
→ El script te avisa antes de generar el SQL

**¿Puedo deshacer cambios?**
→ NO - Por eso siempre haz backup de CSVs primero

---

**¡Listo para gestionar miles de productos fácilmente!** 🚀
