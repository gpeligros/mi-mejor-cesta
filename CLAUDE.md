# CLAUDE.md — Mi Mejor Cesta

**Lee [`CONTEXTO.md`](CONTEXTO.md) completo antes de responder nada.** Ahí está
el estado real del proyecto: stack con versiones, arquitectura de la base de
datos, pipeline del catálogo, pendientes por prioridad y las trampas del
entorno. Este fichero solo recuerda lo que nunca hay que saltarse.

## Antes de tocar nada
- Leer los ficheros actuales. Nunca asumir en qué estado están.
- No cambiar la arquitectura de la BBDD sin consultar a David.
- No renombrar ficheros sin preguntar.
- No empezar a escribir código sin entender primero el estado real.

## Nunca
- Los scrapers no escriben en `productos_catalogo` ni en `categorias_maestras`.
- No se borra un CAT-xxxx: se desactiva con `activo=false`.
- No se sube `.env` a Git.
- No se ejecuta `TRUNCATE` sin verificar antes que hay backup.
- No se ejecutan comandos de `git` desde el puente al ordenador de David: los
  ejecuta él. Igual con `npm`, `npx` y el SQL de Supabase.
- No se borra nada: lo que sobra se mueve a `_to_delete/`.

## Convenciones
- Todo en castellano: textos, comentarios, tablas, columnas, funciones, ficheros
  y mensajes de commit (en imperativo).
- Sin fechas ni versiones en los nombres de fichero. Si algo se actualiza, se
  sobrescribe.
- Scrapers: `scraper_{super}.py` · Matching: `match_{super}.py` · Con IA:
  `match_{super}_ia.py` · Revisión: `revisar_matches_{super}.py`.
- Los CSV de trabajo del pipeline van en `datos/`, nunca en la raíz.

## Al terminar una sesión
Actualizar `CONTEXTO.md` con lo que se ha hecho. Si no queda escrito ahí, la
siguiente sesión no lo sabrá.
