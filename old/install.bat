@echo off
echo ========================================
echo   INSTALACION - Sistema de Scraping
echo ========================================
echo.

echo [1/2] Instalando dependencias Python...
pip install playwright anthropic supabase python-dotenv tqdm
echo.

echo [2/2] Instalando navegador Chromium...
playwright install chromium
echo.

echo ========================================
echo      INSTALACION COMPLETADA
echo ========================================
echo.
echo EJECUTA:
echo   python 1_scrape_mercadona.py
echo.
pause
