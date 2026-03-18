# 📚 GUÍA COMPLETA - GESTIÓN DE PRODUCTOS

## 🎯 REGLAS DE ORO (NUNCA ROMPER):

### ✅ REGLA 1: MISMO `id_producto` EN AMBAS TABLAS
```
productos_mercadona.id_producto = productos_genericos.id_producto
```

### ✅ REGLA 2: MISMA `categoria` Y `subcategoria` EN AMBAS TABLAS
```
productos_mercadona.categoria = productos_genericos.categoria
productos_mercadona.subcategoria = productos_genericos.subcategoria
```

### ✅ REGLA 3: Categoría/Subcategoría DEBE EXISTIR en `categorias_maestras`
```sql
-- Verificar antes de insertar
SELECT * FROM categorias_maestras 
WHERE categoria = 'Despensa' AND subcategoria = 'Aceites';
```

---

## 1️⃣ AÑADIR PRODUCTO NUEVO

### **Opción A: Un producto (SQL directo)**

```sql
-- PASO 1: Añadir a productos_mercadona
INSERT INTO productos_mercadona (id_producto, nombre, precio, categoria, subcategoria, imagen, url)
VALUES (
  'ME-3899',                              -- ⚠️ Siguiente ID disponible
  'Aceite de oliva virgen Hacendado 1L', -- Con marca
  '4.50€',                                -- Formato €X.XX
  'Despensa',                             -- ✅ Debe existir
  'Aceites',                              -- ✅ Debe existir
  '',                                     
  ''
);

-- PASO 2: Añadir a productos_genericos (MISMO ID)
INSERT INTO productos_genericos (id_producto, nombre, categoria, subcategoria)
VALUES (
  'ME-3899',                           -- ✅ MISMO ID
  'Aceite de oliva virgen 1L',        -- Sin marca
  'Despensa',                          -- ✅ MISMA categoría
  'Aceites'                            -- ✅ MISMA subcategoría
);
```

### **Opción B: Múltiples productos (CSV + Script)**

1. Crear `nuevos_productos.csv`:
```csv
id_producto;nombre_mercadona;nombre_generico;precio;categoria;subcategoria;imagen;url
ME-3899;Aceite Hacendado 1L;Aceite oliva 1L;4.50€;Despensa;Aceites;;
ME-3900;Leche Hacendado;Leche entera;0.80€;Lácteos y Huevos;Leche y bebidas "lácteas";;
```

2. Ejecutar script:
```bash
python generar_sql_productos_nuevos.py
```

3. Ejecutar SQLs generados en Supabase

---

## 2️⃣ ACTUALIZAR PRODUCTO EXISTENTE

### **Actualizar precio de un producto:**
```sql
-- Solo en productos_mercadona (los genéricos no tienen precio)
UPDATE productos_mercadona 
SET precio = '5.20€'
WHERE id_producto = 'ME-0001';
```

### **Actualizar nombre:**
```sql
-- Actualizar en productos_mercadona
UPDATE productos_mercadona 
SET nombre = 'Patatas nuevas Hacendado'
WHERE id_producto = 'ME-0001';

-- Actualizar en productos_genericos (sin marca)
UPDATE productos_genericos 
SET nombre = 'Patatas nuevas'
WHERE id_producto = 'ME-0001';
```

### **Cambiar categoría (AMBAS TABLAS):**
```sql
-- 1. Verificar que existe la nueva categoría
SELECT * FROM categorias_maestras 
WHERE categoria = 'Despensa' AND subcategoria = 'Harinas';

-- 2. Actualizar en productos_mercadona
UPDATE productos_mercadona 
SET categoria = 'Despensa', subcategoria = 'Harinas'
WHERE id_producto = 'ME-1234';

-- 3. Actualizar en productos_genericos (MISMA)
UPDATE productos_genericos 
SET categoria = 'Despensa', subcategoria = 'Harinas'
WHERE id_producto = 'ME-1234';
```

---

## 3️⃣ ELIMINAR PRODUCTO

```sql
-- Eliminar de ambas tablas (MISMO ID)
BEGIN;

DELETE FROM productos_mercadona WHERE id_producto = 'ME-1234';
DELETE FROM productos_genericos WHERE id_producto = 'ME-1234';

COMMIT;
```

---

## 4️⃣ OBTENER SIGUIENTE ID DISPONIBLE

```sql
-- Ver último ID usado
SELECT id_producto 
FROM productos_mercadona 
ORDER BY id_producto DESC 
LIMIT 1;

-- Resultado: ME-3898
-- Siguiente: ME-3899
```

---

## 5️⃣ VERIFICAR INTEGRIDAD DE DATOS

### **Verificar que todos los genéricos tienen precio en Mercadona:**
```sql
SELECT 
  g.id_producto,
  g.nombre,
  m.precio
FROM productos_genericos g
LEFT JOIN productos_mercadona m ON g.id_producto = m.id_producto
WHERE m.precio IS NULL;

-- Si devuelve filas → HAY PRODUCTOS SIN PRECIO (error)
```

### **Verificar que IDs coinciden:**
```sql
SELECT 
  COUNT(*) as total_genericos,
  COUNT(DISTINCT g.id_producto) as ids_unicos,
  (SELECT COUNT(*) FROM productos_mercadona) as total_mercadona
FROM productos_genericos g;

-- total_genericos = total_mercadona = ids_unicos (deben ser iguales)
```

### **Verificar categorías válidas:**
```sql
-- Productos con categorías que NO existen
SELECT DISTINCT 
  p.categoria, 
  p.subcategoria
FROM productos_mercadona p
LEFT JOIN categorias_maestras cm 
  ON p.categoria = cm.categoria 
  AND p.subcategoria = cm.subcategoria
WHERE cm.id IS NULL;

-- Si devuelve filas → HAY CATEGORÍAS INVÁLIDAS (error)
```

---

## 6️⃣ AÑADIR NUEVA CATEGORÍA/SUBCATEGORÍA

```sql
-- 1. Añadir a categorias_maestras
INSERT INTO categorias_maestras (categoria, subcategoria, orden)
VALUES ('Nueva Categoría', 'Nueva Subcategoría', 85);

-- 2. Ahora puedes usar esta categoría en productos
INSERT INTO productos_mercadona (...)
VALUES (..., 'Nueva Categoría', 'Nueva Subcategoría', ...);
```

---

## 7️⃣ IMPORTACIÓN MASIVA SEGURA

```sql
-- PASO 1: Crear tabla temporal
CREATE TEMP TABLE temp_nuevos_productos (
  id_producto TEXT,
  nombre_mercadona TEXT,
  nombre_generico TEXT,
  precio TEXT,
  categoria TEXT,
  subcategoria TEXT,
  imagen TEXT,
  url TEXT
);

-- PASO 2: Copiar CSV a tabla temporal
COPY temp_nuevos_productos FROM '/ruta/nuevos_productos.csv' 
DELIMITER ';' CSV HEADER;

-- PASO 3: Validar categorías
SELECT t.* 
FROM temp_nuevos_productos t
LEFT JOIN categorias_maestras cm 
  ON t.categoria = cm.categoria 
  AND t.subcategoria = cm.subcategoria
WHERE cm.id IS NULL;

-- Si devuelve filas → HAY CATEGORÍAS INVÁLIDAS (corregir CSV)

-- PASO 4: Insertar en productos_mercadona
INSERT INTO productos_mercadona (id_producto, nombre, precio, categoria, subcategoria, imagen, url)
SELECT id_producto, nombre_mercadona, precio, categoria, subcategoria, imagen, url
FROM temp_nuevos_productos;

-- PASO 5: Insertar en productos_genericos
INSERT INTO productos_genericos (id_producto, nombre, categoria, subcategoria)
SELECT id_producto, nombre_generico, categoria, subcategoria
FROM temp_nuevos_productos;

-- PASO 6: Limpiar
DROP TABLE temp_nuevos_productos;
```

---

## 🚨 ERRORES COMUNES Y SOLUCIONES

### ❌ Error: "duplicate key value violates unique constraint"
**Causa:** Intentas insertar un `id_producto` que ya existe
**Solución:** Verificar último ID y usar el siguiente

```sql
-- Ver IDs usados
SELECT id_producto FROM productos_mercadona 
WHERE id_producto LIKE 'ME-389%' 
ORDER BY id_producto;
```

### ❌ Error: Producto aparece en sidebar pero sin precio
**Causa:** Existe en `productos_genericos` pero NO en `productos_mercadona`
**Solución:** Añadir a ambas tablas

```sql
-- Encontrar productos huérfanos
SELECT g.id_producto, g.nombre
FROM productos_genericos g
LEFT JOIN productos_mercadona m ON g.id_producto = m.id_producto
WHERE m.id_producto IS NULL;
```

### ❌ Error: Categoría no válida
**Causa:** Usas categoría que no existe en `categorias_maestras`
**Solución:** Ver categorías disponibles y usar una de ellas

```sql
-- Ver todas las categorías válidas
SELECT categoria, subcategoria 
FROM categorias_maestras 
ORDER BY categoria, subcategoria;
```

---

## 📊 QUERIES ÚTILES

### Ver distribución de productos por categoría:
```sql
SELECT 
  categoria, 
  subcategoria,
  COUNT(*) as total
FROM productos_mercadona
GROUP BY categoria, subcategoria
ORDER BY categoria, subcategoria;
```

### Buscar productos por nombre:
```sql
SELECT 
  m.id_producto,
  g.nombre as nombre_generico,
  m.nombre as nombre_mercadona,
  m.precio,
  m.categoria
FROM productos_genericos g
JOIN productos_mercadona m ON g.id_producto = m.id_producto
WHERE g.nombre ILIKE '%patata%';
```

### Productos más caros:
```sql
SELECT 
  id_producto,
  nombre,
  precio,
  categoria
FROM productos_mercadona
ORDER BY CAST(REPLACE(precio, '€', '') AS DECIMAL) DESC
LIMIT 20;
```

---

## ✅ CHECKLIST ANTES DE AÑADIR PRODUCTOS

- [ ] ID nuevo no existe (consultar último ID)
- [ ] Categoría/subcategoría existe en `categorias_maestras`
- [ ] Precio tiene formato €X.XX
- [ ] Añadir a AMBAS tablas (`productos_mercadona` Y `productos_genericos`)
- [ ] Mismo `id_producto` en ambas
- [ ] Misma `categoria` y `subcategoria` en ambas
- [ ] Verificar después con query de integridad

---

**Con esta guía puedes añadir/modificar productos sin romper nada** ✅
