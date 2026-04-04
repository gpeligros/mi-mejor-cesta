# Mi Mejor Cesta — Planes y Funcionalidades

## Resumen de planes

|Funcionalidad|Gratis|Gratis + registro|Básico 2,99€/mes|Premium 6,99€/mes|
|-|:-:|:-:|:-:|:-:|
|**COMPARADOR**|||||
|Supermercados|2 máx|2 máx|Todos|Todos|
|Productos en lista|20 máx|20 máx|Ilimitado|Ilimitado|
|**LISTA Y CESTA**|||||
|Guardar listas favoritas|—|1 lista|Ilimitado|Ilimitado|
|Compartir lista|—|✅|✅|✅|
|Exportar PDF|—|✅|✅|✅|
|Escanear lista externa (OCR)|—|—|✅|✅|
|Alertas subida/bajada de precio|—|—|✅|✅|
|**COMPRA REALIZADA**|||||
|Validar y guardar compra|—|—|✅|✅|
|Historial de compras|—|—|3 meses|Ilimitado|
|Planificación mensual|—|—|—|✅|
|**MENÚS Y RECETAS**|||||
|Generar menú semanal|—|—|—|✅|
|Lista de ingredientes desde receta|—|—|—|✅|
|Menú mensual con precios|—|—|—|✅|
|**ESTADÍSTICAS Y NUTRICIÓN**|||||
|Gasto por supermercado|—|—|Básico|Completo|
|Evolución de precios|—|—|—|✅|
|Datos nutricionales cesta|—|—|—|✅ \*|
|Ahorro acumulado histórico|—|—|—|✅|
|**CESTITA — IA ASISTENTE**|||||
|Consultas básicas|✅|✅|✅|✅|
|Contexto de cesta + comparativa|—|—|✅|✅|
|Dictado de lista por voz|—|—|✅|✅|
|Recetas, nutrición y menús|—|—|—|✅|

\---

> \\\\\\\* Los datos nutricionales son orientativos. No somos médicos ni nutricionistas.
> Consulta siempre a un profesional de la salud.





\*\*\*\*\*\*\* SELECT PARA SABER QUE PLAN TENEMOS \*\*\*\*\*\*\*\*\*\*\*\*\*

SELECT p.id, p.plan, u.email 

FROM profiles p

JOIN auth.users u ON p.id = u.id;







\*\*\*\*\*\*\*\* SENTENCIA PARA CAMBIAR DE PLAN UN USUARIO \*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*

UPDATE profiles 

SET plan = 'basic' 

WHERE id = '716a2d6a-eeb3-4576-99f2-e42fce0276c2';

