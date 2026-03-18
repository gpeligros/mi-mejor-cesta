@echo off
REM ============================================================
REM SCRIPT DE REORGANIZACION - Mi Mejor Cesta
REM ============================================================
REM Ejecutar desde la raiz del proyecto: mi-mejor-cesta/

echo.
echo ========================================================
echo     REORGANIZACION AUTOMATICA - Mi Mejor Cesta
echo ========================================================
echo.
echo Este script reorganizara tu proyecto en:
echo   - frontend/      (App web)
echo   - backend/       (API + Scraping)
echo   - scripts/       (Utilidades)
echo   - docs/          (Documentacion)
echo.

REM Verificar que estamos en el directorio correcto
if not exist "package.json" (
    echo ERROR: No se encuentra package.json
    echo Asegurate de ejecutar este script desde la raiz del proyecto
    echo Ejemplo: cd mi-mejor-cesta
    pause
    exit /b 1
)

echo [ADVERTENCIA] Este script movera archivos en tu proyecto
echo.
set /p confirm="Continuar? (S/N): "
if /i not "%confirm%"=="S" (
    echo Operacion cancelada
    pause
    exit /b 0
)

echo.
echo ========================================================
echo PASO 1: Crear backup
echo ========================================================

REM Crear carpeta de backup con fecha
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%b%%a)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set backup_name=backup_%mydate%_%mytime%

mkdir "%backup_name%" 2>nul
echo Backup creado: %backup_name%
echo.

echo ========================================================
echo PASO 2: Crear nueva estructura
echo ========================================================

REM Crear directorios principales
mkdir frontend 2>nul
mkdir backend\api 2>nul
mkdir backend\scraping\scrapers 2>nul
mkdir backend\scraping\matcher 2>nul
mkdir backend\scraping\data 2>nul
mkdir backend\scraping\logs 2>nul
mkdir backend\scraping\config 2>nul
mkdir scripts 2>nul
mkdir docs 2>nul

echo [OK] Estructura creada
echo.

echo ========================================================
echo PASO 3: Mover archivos del FRONTEND
echo ========================================================

REM Mover frontend
if exist "src" (
    echo Moviendo src/...
    xcopy /E /I /Y "src" "frontend\src\" >nul
    echo [OK] src/ movido
)

if exist "public" (
    echo Moviendo public/...
    xcopy /E /I /Y "public" "frontend\public\" >nul
    echo [OK] public/ movido
)

if exist "templates" (
    echo Moviendo templates/...
    xcopy /E /I /Y "templates" "frontend\templates\" >nul
    echo [OK] templates/ movido
)

REM Archivos de configuracion frontend
if exist "package.json" (
    copy /Y "package.json" "frontend\package.json" >nul
    echo [OK] package.json copiado
)

if exist "package-lock.json" (
    copy /Y "package-lock.json" "frontend\package-lock.json" >nul
    echo [OK] package-lock.json copiado
)

if exist "tailwind.config" (
    copy /Y "tailwind.config" "frontend\tailwind.config.js" >nul
    echo [OK] tailwind.config copiado
)

if exist "tailwind.config.js" (
    copy /Y "tailwind.config.js" "frontend\tailwind.config.js" >nul
    echo [OK] tailwind.config.js copiado
)

REM Mover node_modules si existe (opcional, mejor reinstalar)
REM if exist "node_modules" (
REM     echo Moviendo node_modules/ (esto puede tardar...)
REM     xcopy /E /I /Y "node_modules" "frontend\node_modules\" >nul
REM     echo [OK] node_modules/ movido
REM )

echo.

echo ========================================================
echo PASO 4: Mover archivos del BACKEND
echo ========================================================

REM Backend API
if exist "app_gestion" (
    copy /Y "app_gestion" "backend\api\app_gestion.py" >nul
    echo [OK] app_gestion movido
)

if exist "app_gestion.py" (
    copy /Y "app_gestion.py" "backend\api\app_gestion.py" >nul
    echo [OK] app_gestion.py movido
)

REM Scraping
if exist "scraper\scrapers" (
    echo Moviendo scrapers/...
    xcopy /E /I /Y "scraper\scrapers" "backend\scraping\scrapers\" >nul
    echo [OK] scrapers/ movido
)

if exist "scraper\data" (
    echo Moviendo data/...
    xcopy /E /I /Y "scraper\data" "backend\scraping\data\" >nul
    echo [OK] data/ movido
)

if exist "scraper\logs" (
    echo Moviendo logs/...
    xcopy /E /I /Y "scraper\logs" "backend\scraping\logs\" >nul
    echo [OK] logs/ movido
)

if exist "scraper\utils" (
    echo Moviendo utils/...
    xcopy /E /I /Y "scraper\utils" "backend\scraping\utils\" >nul
    echo [OK] utils/ movido
)

if exist "scraper\.env" (
    copy /Y "scraper\.env" "backend\scraping\config\.env" >nul
    echo [OK] .env movido
)

if exist "scraper\requirements" (
    copy /Y "scraper\requirements" "backend\scraping\requirements.txt" >nul
    echo [OK] requirements movido
)

if exist "scraper\requirements.txt" (
    copy /Y "scraper\requirements.txt" "backend\scraping\requirements.txt" >nul
    echo [OK] requirements.txt movido
)

REM Archivos Python del scraper
if exist "scraper\main" (
    copy /Y "scraper\main" "backend\scraping\main.py" >nul
    echo [OK] main movido
)

if exist "scraper\main.py" (
    copy /Y "scraper\main.py" "backend\scraping\main.py" >nul
    echo [OK] main.py movido
)

if exist "scraper\diagnostico" (
    copy /Y "scraper\diagnostico" "backend\scraping\diagnostico.py" >nul
    echo [OK] diagnostico movido
)

if exist "scraper\test_*.py" (
    copy /Y "scraper\test_*.py" "backend\scraping\" >nul
    echo [OK] tests movidos
)

echo.

echo ========================================================
echo PASO 5: Mover SCRIPTS y UTILIDADES
echo ========================================================

if exist "generar_codigos_v3" (
    copy /Y "generar_codigos_v3" "scripts\generar_codigos_v3.py" >nul
    echo [OK] generar_codigos_v3 movido
)

if exist "generar_codigos_v3.py" (
    copy /Y "generar_codigos_v3.py" "scripts\generar_codigos_v3.py" >nul
    echo [OK] generar_codigos_v3.py movido
)

if exist "supabase" (
    copy /Y "supabase" "scripts\supabase_config" >nul
    echo [OK] supabase config movido
)

echo.

echo ========================================================
echo PASO 6: Mover DOCUMENTACION
echo ========================================================

if exist "README" (
    copy /Y "README" "docs\README_old.md" >nul
    echo [OK] README movido
)

if exist "README.md" (
    copy /Y "README.md" "docs\README_old.md" >nul
    echo [OK] README.md movido
)

echo.

echo ========================================================
echo PASO 7: Copiar archivos raiz importantes
echo ========================================================

REM Mantener algunos archivos en la raiz
if exist ".gitignore" (
    copy /Y ".gitignore" ".gitignore.backup" >nul
    echo [OK] .gitignore respaldado
)

echo.

echo ========================================================
echo PASO 8: Crear archivos README
echo ========================================================

REM README principal
(
echo # Mi Mejor Cesta - Comparador de Precios
echo.
echo ## Estructura del Proyecto
echo.
echo ```
echo mi-mejor-cesta/
echo ├── frontend/           # Aplicacion web ^(React/Next.js^)
echo ├── backend/            # API + Sistema de scraping
echo │   ├── api/            # Flask API
echo │   └── scraping/       # Scrapers + Matching IA
echo ├── scripts/            # Utilidades
echo └── docs/               # Documentacion
echo ```
echo.
echo ## Instalacion
echo.
echo ### Frontend
echo ```bash
echo cd frontend
echo npm install
echo npm run dev
echo ```
echo.
echo ### Backend
echo ```bash
echo cd backend/scraping
echo pip install -r requirements.txt
echo python main.py
echo ```
echo.
echo ## Mas informacion
echo.
echo Ver carpeta `docs/` para documentacion completa.
) > README.md

echo [OK] README.md principal creado
echo.

REM README frontend
(
echo # Frontend - Mi Mejor Cesta
echo.
echo Aplicacion web del comparador de precios.
echo.
echo ## Instalacion
echo ```bash
echo npm install
echo ```
echo.
echo ## Desarrollo
echo ```bash
echo npm run dev
echo ```
echo.
echo ## Build
echo ```bash
echo npm run build
echo ```
) > frontend\README.md

echo [OK] README frontend creado
echo.

REM README backend
(
echo # Backend - Mi Mejor Cesta
echo.
echo ## Estructura
echo.
echo - `api/` - Flask API para el frontend
echo - `scraping/` - Sistema de actualizacion de precios
echo.
echo ## Scraping
echo.
echo ### Instalacion
echo ```bash
echo cd scraping
echo pip install -r requirements.txt
echo playwright install chromium
echo ```
echo.
echo ### Uso
echo ```bash
echo python main.py
echo ```
echo.
echo Ver `scraping/README.md` para mas detalles.
) > backend\README.md

echo [OK] README backend creado
echo.

echo ========================================================
echo PASO 9: Crear archivo de configuracion Git
echo ========================================================

(
echo # Dependencias
echo node_modules/
echo __pycache__/
echo *.pyc
echo.
echo # Variables de entorno
echo .env
echo backend/scraping/config/.env
echo.
echo # Datos temporales
echo backend/scraping/data/*
echo backend/scraping/logs/*
echo.
echo # Backups
echo backup_*/
echo *.backup
echo.
echo # OS
echo .DS_Store
echo Thumbs.db
) > .gitignore

echo [OK] .gitignore actualizado
echo.

echo ========================================================
echo              REORGANIZACION COMPLETADA
echo ========================================================
echo.
echo Nueva estructura:
echo.
echo mi-mejor-cesta/
echo ├── frontend/           ^(App web^)
echo ├── backend/
echo │   ├── api/            ^(Flask API^)
echo │   └── scraping/       ^(Scrapers + IA^)
echo ├── scripts/            ^(Utilidades^)
echo ├── docs/               ^(Documentacion^)
echo └── README.md
echo.
echo ========================================================
echo PROXIMOS PASOS:
echo ========================================================
echo.
echo 1. Verificar que todo esta correcto
echo 2. Instalar dependencias frontend:
echo    cd frontend
echo    npm install
echo.
echo 3. Instalar dependencias backend:
echo    cd backend/scraping
echo    pip install -r requirements.txt
echo.
echo 4. Si todo funciona, BORRAR carpetas antiguas:
echo    - scraper/
echo    - Basura_old/
echo    - src/ ^(si esta vacia^)
echo    - public/ ^(si esta vacia^)
echo.
echo 5. Backup guardado en: %backup_name%/
echo.
pause
