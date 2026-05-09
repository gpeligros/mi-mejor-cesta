# PLAN_REALISTA.md - Mi Mejor Cesta

> Documento honesto de cuanto trabajo queda y en que orden.
> Generado el 9 de mayo de 2026 tras detectar bugs de calidad de datos.

## Diagnostico actual (sin azucar)

La app **funciona** pero **promete mas de lo que cumple**. La causa raiz no es
el codigo, es la **calidad del catalogo y los matches**. Mientras esto no
este resuelto, la app:

1. Muestra "ahorro negativo" cuando algun super tiene cobertura parcial
   (ya arreglado en App.js: ahora se calcula producto a producto).
2. Tiene matches falsos (ej. "Sidra Polian" en Mercadona apuntando a
   "Sidra Asturiana" en Carrefour - son marcas distintas).
3. Tiene precios anomalos en catalogo (ej. botellas individuales con
   precio de caja).
4. Carrefour aparece visible en frontend pero solo cubre ~3 de 8
   productos en una cesta tipica (matching v5 sin ejecutar todavia).

**Es viable seguir.** No es un proyecto roto. Es un proyecto al 70% que
necesita una pasada de calidad seria antes de cobrar.

---

## Bloque 1 - Calidad de datos (PRIORIDAD ALTA, 4-8 horas)

Sin esto, cobrar es suicidio. Cualquier usuario que se de cuenta de un
match falso = se va y deja review malo.

### 1.1. Ejecutar la auditoria automatica (10 min)

```powershell
cd C:\Users\ccash\mi-mejor-cesta
python scrapers/auditar_catalogo.py
```

Genera 5 CSVs en la raiz:
- `audit_precios_extremos.csv` (precios <0,10 o >50 EUR)
- `audit_precios_anomalos.csv` (>3 sigma de la mediana del grupo)
- `audit_marcas_inconsistentes.csv` (CAT con marcas distintas en supers)
- `audit_huecos_cobertura.csv` (CAT con matches en <=2 supers)
- `audit_sin_categoria.csv` (productos invisibles en UI)

Empieza por **audit_precios_extremos** (errores obvios) y
**audit_marcas_inconsistentes** (matches falsos).

### 1.2. Limpiar matches falsos (2-3 horas)

Para cada fila sospechosa de `audit_marcas_inconsistentes.csv` decide:

- Si es realmente un match falso (ej. Polian/Asturiana): UPDATE en
  Supabase poniendo a NULL la columna del super equivocado:
  ```sql
  UPDATE productos_match
  SET id_carrefour = NULL
  WHERE id_catalogo = 'CAT-1234';
  ```
- Si es un match legitimo (mismo producto, marca distinta porque la una
  es marca blanca y la otra fabricante en otra cadena): dejarlo.

### 1.3. Arreglar precios extremos (1-2 horas)

`audit_precios_extremos.csv` te muestra precios <0,10 o >50 EUR.
Casi siempre son:
- Producto cargado como "caja" cuando deberia ser "unidad" -> separar en
  catalogo o eliminar la entrada y dejar solo la unidad.
- Errores de scraping (parseaste 1080 cuando era 10,80).
- Productos B2B (cajas de 24 latas) que no deberian estar en el comparador
  domestico -> desactivar con `UPDATE productos_catalogo SET activo=false`.

### 1.4. Ejecutar match_carrefour.py (30 min real, 30 min revisar dudosos)

```powershell
python scrapers/match_carrefour.py --dry-run
# Revisar la salida
python scrapers/match_carrefour.py
# Te pedira confirmacion (s/n) antes de aplicar
```

Resultado esperado: pasar de ~3 matches Carrefour a ~2.000-2.500.

Despues, **revisar el CSV de dudosos generado** (carrefour_dudosos_*.csv)
y elegir manualmente cuales son matches buenos. Marcar columna "ok" con 1
y reimportar via SQL si quieres ganar otros 500-800 matches.

### 1.5. Repetir matching para AhorraMas (15 min)

```powershell
python scrapers/match_ahorramas.py --dry-run
python scrapers/match_ahorramas.py
```

### 1.6. Verificar que los huecos no son criticos (30 min)

```powershell
python scrapers/verificar_estado.py
```

Esto te dice cuantos matches hay por super tras los pasos anteriores.
Objetivo realista para considerar la app "lista":

| Super     | Matches minimos | Cobertura |
|-----------|-----------------|-----------|
| Mercadona | >=3.500         | 85%+      |
| DIA       | >=2.500         | 60%+      |
| Carrefour | >=2.000         | 50%+      |
| Alcampo   | >=400           | 10%+      |
| AhorraMas | >=300           | 7%+       |

**Total estimado del bloque 1: 4-8 horas reales de trabajo concentrado.**

---

## Bloque 2 - UX y robustez (PRIORIDAD MEDIA, 2-3 horas)

Cosas que mejoran percepcion sin tocar datos.

### 2.1. Mostrar cobertura por super en SuperCard (30 min)

Que cada tarjeta de supermercado muestre "Tiene 6 de 8 productos" para
que el usuario entienda los huecos. Hoy no se dice nada y parece bug.

### 2.2. Avisar cuando la cesta tiene productos sin precio en ningun super (15 min)

Si `productosSinPrecio > 0` en stats, mostrar un aviso visible:
"3 productos no estan disponibles en ninguno de los supermercados
seleccionados. Activa mas supers para verlos."

### 2.3. Permitir ordenar/filtrar por cobertura completa (1 hora)

Boton "Solo productos disponibles en todos los supers seleccionados" para
que el usuario pueda comparar sin huecos.

### 2.4. Mensajes de error reales (30 min)

Si Supabase falla al cargar, hoy se queda en blanco. Anadir mensaje
"No hemos podido cargar los precios. Reintentar".

### 2.5. Activar Sentry cuando puedas (15 min)

Ya esta el codigo preparado en index.js (comentado). Cuando crees cuenta
gratis en sentry.io, descomentas el bloque + var de entorno y listo.

**Total bloque 2: 2-3 horas.**

---

## Bloque 3 - Hipercor (PRIORIDAD BAJA, 4-6 horas)

Solo cuando los bloques 1 y 2 esten cerrados. Anade una cadena mas pero
mientras los matches actuales no esten limpios, sumar otra cadena solo
diluye el problema.

```sql
ALTER TABLE productos_match ADD COLUMN id_hipercor TEXT;
```

```powershell
python scrapers/scraper_hipercor.py    # ~30-60 min
python scrapers/match_hipercor.py --dry-run
python scrapers/match_hipercor.py
```

Despues integrarlo en App.js + LogosSuper.js + asset del logo.

**Total bloque 3: 4-6 horas.**

---

## Bloque 4 - Legal y Stripe (PRIORIDAD CONDICIONAL)

Solo cuando los bloques 1 y 2 esten cerrados Y hayas decidido alta fiscal.

1. Rellenar placeholders [TITULAR], [NIF], [DIRECCION], [EMAIL],
   [PROVINCIA] en los 4 ficheros legales.
2. Decidir alta como autonomo o SL.
3. Crear webhook nuevo en Stripe live, copiar STRIPE_WEBHOOK_SECRET.
4. Cambiar variables Stripe en Vercel a las _PROD.
5. Hacer webhook idempotente (crear tabla webhook_events_seen).
6. Anadir handler customer.subscription.updated.
7. Anadir boton "Gestionar suscripcion" -> Stripe Customer Portal.
8. Activar Stripe Tax para IVA espanol.
9. Probar end-to-end con tarjeta real propia.

**Total bloque 4: 3-5 horas + decisiones fiscales.**

---

## Resumen de horas honestas

| Bloque | Horas | Bloqueante para cobrar? |
|--------|-------|-------------------------|
| 1. Calidad de datos | 4-8 | SI - sin esto nadie paga |
| 2. UX y robustez | 2-3 | NO pero recomendado |
| 3. Hipercor | 4-6 | NO - feature posterior |
| 4. Legal + Stripe live | 3-5 | SI - antes de cobrar |
| **Total minimo** | **9-13 horas** | para empezar a cobrar |

---

## Sobre la viabilidad - vision honesta

### Lo que TIENES a favor

- Producto comparador funcional para 3 cadenas grandes (Mercadona, DIA,
  Alcampo). Mercadona al 100%.
- CESTITA (asistente IA) funciona y diferencia tu app del resto.
- Funciones premium implementadas (menus, recetas, nutricional).
- Stripe integrado (test).
- Auth completa, sincronizacion en nube, lista colaborativa.
- PWA instalable.
- Stack moderno y mantenible.
- Tu perfil profesional (15 anos en banca, BI, automatizacion) encaja
  perfecto con la fase B2B de Marketplace.

### Lo que va EN CONTRA

- El mercado de comparadores de supermercados en Espana esta vacio
  (Lola Market cerro, Glovo no compara, hipertextil murio). Eso es a la
  vez **oportunidad** (no hay competidor serio) y **riesgo** (puede que
  no haya mercado real, todos los anteriores quebraron).
- El precio de 2,99 EUR / 6,99 EUR es bajo: necesitas 500-1.000 usuarios
  pagando para que sea rentable. Adquirir 500 usuarios pagando con un
  presupuesto de marketing cero es muy duro.
- La calidad de los datos depende de scraping, que se puede romper si
  los supers cambian su web (y lo van a hacer).
- Stripe Tax + alta autonomo + 21% IVA + IRPF se come una buena parte
  del 2,99 EUR mensual. Margen real por usuario: ~1,80-2,00 EUR.

### Recomendacion personal

**Sigue, pero con plan claro.** No tires el trabajo. Tienes 200 horas
invertidas y estas a 10-15 horas mas de tener algo cobrabe. Ahora bien:

1. **No metas mas funcionalidades** hasta cerrar los bloques 1 y 2.
2. **No actives Stripe live** hasta que la calidad de los datos sea
   creible. Si lanzas con datos malos pierdes la confianza para siempre.
3. **Lanza primero gratis** con los 3 supers principales bien limpios.
   Cobra solo cuando tengas tracion organica (50-100 usuarios usandola
   varias veces por semana).
4. **El verdadero negocio es B2B**, vendiendo inteligencia de precios a
   las propias cadenas o a marcas. Eso necesita primero demostrar que
   tienes datos de calidad y usuarios reales. Lo que estamos haciendo
   ahora.

Si en 3 meses no consigues 100 usuarios activos pese a tener datos
limpios, replantea: o monetizar de otra forma (afiliacion, B2B,
licencias) o pausar y dedicarle horas solo cuando te apetezca como
hobby tecnico.

No tiene sentido tirar el trabajo. Tiene sentido **bloque 1 + bloque 2 +
2 semanas de prueba gratis con amigos antes de cobrar**.

---

## Lo proximo que tienes que hacer (orden)

1. `git status` y subir el commit de la sesion anterior si no lo has
   hecho aun.
2. Ejecutar `python scrapers/verificar_estado.py` para tener
   foto del estado real.
3. Ejecutar `python scrapers/auditar_catalogo.py` para tener los CSVs
   sospechosos.
4. Abrir los CSVs y dedicar 2 horas a limpiar matches falsos manualmente.
5. Ejecutar `python scrapers/match_carrefour.py --dry-run`, revisar y
   ejecutar real.
6. Ejecutar `python scrapers/match_ahorramas.py --dry-run`, revisar y
   ejecutar real.
7. Verificar resultado: abrir https://mi-mejor-cesta.vercel.app y meter
   una cesta tipica. Comprobar que el ahorro ya no es negativo y que
   los precios cuadran.
8. Pasame las dudas concretas que tengas tras los pasos anteriores.

No hace falta hacerlo todo hoy. Marca un sabado para los pasos 1-7 y
me cuentas.
