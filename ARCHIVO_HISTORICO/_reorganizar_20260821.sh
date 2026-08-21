#!/bin/bash
set -uo pipefail
cd "$HOME/mnt/mi-mejor-cesta" || exit 1

mkdir -p ARCHIVO_HISTORICO/raiz_suelta
mkdir -p ARCHIVO_HISTORICO/scripts
mkdir -p ARCHIVO_HISTORICO/old_scripts_legacy
mkdir -p ARCHIVO_HISTORICO/old_datos_legacy
mkdir -p ARCHIVO_HISTORICO/old_contexto_antiguos
mkdir -p ARCHIVO_HISTORICO/scrapers_restos
mkdir -p ARCHIVO_HISTORICO/revisar_datos_viejos

moved=0
missing=0

mv_one() {
  if [ -e "$1" ]; then
    mv -n -- "$1" "$2" && moved=$((moved+1))
  else
    echo "  (no encontrado, salto: $1)"
    missing=$((missing+1))
  fi
}

echo "=== 1. Raiz suelta -> ARCHIVO_HISTORICO/raiz_suelta/ ==="
for f in ahorramas_dudosos_20260726_1355.csv audit_huecos_cobertura.csv audit_marcas_inconsistentes.csv audit_precios_anomalos.csv audit_precios_extremos.csv audit_sin_categoria.csv backup_dia_20260810_2123.json carrefour_dudosos_20260725_2008.csv limpiar_ahorramas_20260726_1412.sql matches_ahorramas_incorrectos_20260726_1412.csv matches_ahorramas_revisados_20260726_1412.csv; do
  mv_one "$f" ARCHIVO_HISTORICO/raiz_suelta/
done

echo "=== 2. output_sqls/ (carpeta entera) -> ARCHIVO_HISTORICO/ ==="
mv_one output_sqls ARCHIVO_HISTORICO/

echo "=== 3. scripts/ restos OpenAI -> ARCHIVO_HISTORICO/scripts/ ==="
for f in scripts/import_openai.py scripts/test_openai_key.py; do
  mv_one "$f" ARCHIVO_HISTORICO/scripts/
done

echo "=== 4. old/ scripts sueltos de las primeras semanas -> ARCHIVO_HISTORICO/old_scripts_legacy/ ==="
for f in 01_CREAR_CATEGORIAS.sql 02_SCRAPER_MERCADONA_API.py 11_recrear_grupos.py 13_scraper_mercadona_v3.py 14_corregir_categorias.py 15_scraper_lidl_manual.py 16_scraper_carrefour_manual.py ANALISIS_PROYECTO_COMPLETO.md analizar_antes_importar.py ANALIZAR_CATEGORIAS.py aplicar_dudosos.py aplicar_matches_revisados.py BORRAR_TODO.py CAPTURADOR_MANUAL.py CARREFOUR_API.py CATEGORIZAR_CON_EXCEL.py clasificador_mercadona.py CREAR_COMPARACION.py DESCARGAR_TODOS.py generar_sql_productos_nuevos.py gestor_masivo.py gestor_masivo_fixed.py gestor_productos.py GUIA_GESTION_MASIVA.md GUIA_VISUAL_PASO_A_PASO.md IMPORTAR_APIFY.py IMPORTAR_APIFY_V2.py IMPORTAR_JSON.py IMPORTAR_MERCADONA_FINAL.py importar_dia_supabase.py install.bat LIDL_API.py LIMPIAR_BD_COMPLETA.py limpiador.py matching_automatico.py matching_dia_v2.py MEJORAR_CATEGORIAS.py reorganizar_proyecto.bat SCRAPER_MERCADONA_DEFINITIVO.py SQL_2B_IMPORTAR_GENERICOS.sql; do
  mv_one "old/$f" ARCHIVO_HISTORICO/old_scripts_legacy/
done

echo "=== 5. old/ variantes de datos superadas -> ARCHIVO_HISTORICO/old_datos_legacy/ ==="
for f in backup_genericos.csv.csv backup_mercadona.csv.csv backup_match_carrefour_20260723.csv.csv carrefour_dudosos.csv dia_productos_20260312_2134.csv dia_sin_match_20260314_1809.csv dia_sin_match_20260314_1814.csv dia_sin_match_ia_20260314_1809.csv dia_sin_match_ia_20260314_1814.csv matches_dudosos.csv matches_revisar.csv matching_dia_completo_dudosos.csv mercadona.csv mercadona.json mercadona_bueno.csv mercadona_categorizado.csv mercadona_clasificado.csv mercadona_clasificado_v2.csv mercadona_COMPLETO.csv mercadona_COMPLETO_old.csv mercadona_final.csv mercadona_prueba.csv mercadona_v2_20260314_2004.csv mercadona_v2_20260314_2007.csv mercadona_v2_20260314_2011.csv mis_1000_productos.csv openfoodfacts_20260312_2051.csv productos.csv productos_dia_sin_match.csv PRODUCTOS_GENERICOS.csv PRODUCTOS_GENERICOS_FIXED.csv productos_con_formato_generico.xlsx "Supabase Snippet Productos de Mercadona.csv" "Supabase Snippet Untitled query.csv" ahorramas_dudosos_20260424_0026.csv; do
  mv_one "old/$f" ARCHIVO_HISTORICO/old_datos_legacy/
done

echo "=== 6. old/ copias antiguas de CONTEXTO -> ARCHIVO_HISTORICO/old_contexto_antiguos/ ==="
for f in CONTEXTO.md CONTEXTO_nuevo.md CONTEXTO_old.md CONTEXTO_old_old.md; do
  mv_one "old/$f" ARCHIVO_HISTORICO/old_contexto_antiguos/
done

echo "=== 7. old/scraping y old/templates (carpetas enteras, prototipo superado) ==="
mv_one old/scraping ARCHIVO_HISTORICO/old_scraping_prototipo
mv_one old/templates ARCHIVO_HISTORICO/old_templates_flask

echo "=== 8. old/ scripts scraper/match duplicados de scrapers/ -> ARCHIVO_HISTORICO/old_scripts_legacy/ ==="
for f in scraper_dia.py scraper_dia_v2.py scraper_dia_v3.py scraper_carrefour.py scraper_mercadona_v2.py scraper_lidl.py scraper_openfoodfacts.py match_dia.py match_mercadona.py; do
  mv_one "old/$f" ARCHIVO_HISTORICO/old_scripts_legacy/
done

echo "=== 9. scrapers/ restos (eroski, hipercor, gemini, debug, v1) -> ARCHIVO_HISTORICO/scrapers_restos/ ==="
for f in scrapers/scraper_eroski.py scrapers/match_eroski.py scrapers/scraper_hipercor.py scrapers/match_hipercor.py scrapers/scraper_carrefour_gemini.py scrapers/scraper_mercadona_gemini.py scrapers/construir_catalogo.py scrapers/construir_catalogo_desde_carrefour.py scrapers/debug_dia.py scrapers/debug_dia2.py scrapers/debug_carrefour_bebidas.html; do
  mv_one "$f" ARCHIVO_HISTORICO/scrapers_restos/
done

echo "=== 10. old/Revisar -> documentos .docx a docs/, el resto a ARCHIVO_HISTORICO/revisar_datos_viejos/ ==="
for f in "🎯 PLAN ESTRATÉGICO PERSONALIZADO.docx" "📊 ANÁLISIS COMPLETO Y PROFUNDO.docx" "🚀 DEPLOY A VERCEL.docx" "Configuracion.docx" "Especificaciones.docx" "Informe de Arquitectura.docx" "TRASPASO_MiMejorCesta_16032026.docx"; do
  mv_one "old/Revisar/$f" docs/
done
for f in "menu-semanal-mi-mejor-cesta.txt" "mi_mejor_cesta_linkedin.svg" "precio_mercado.csv" "productos_010326.xlsx" "productos.js" "productos.xlsx"; do
  mv_one "old/Revisar/$f" ARCHIVO_HISTORICO/revisar_datos_viejos/
done

echo ""
echo "=== RESUMEN: $moved ficheros/carpetas movidos, $missing no encontrados (revisar arriba) ==="
