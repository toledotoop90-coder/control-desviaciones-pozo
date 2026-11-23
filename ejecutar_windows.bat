@echo off
rem Revision del proyecto en Windows: doble clic en este archivo.
rem Crea un entorno aislado en la carpeta .venv, instala, corre las pruebas y abre el reporte.
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================================
echo  Control de desviaciones de costo - revision del proyecto
echo ============================================================
echo.

set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=python"
if not defined PY goto :sinpython
for /f "delims=" %%v in ('%PY% --version') do echo Python encontrado: %%v

if exist ".venv\Scripts\python.exe" (
  echo [1/4] Entorno aislado ya existe ^(.venv^).
) else (
  echo [1/4] Creando el entorno aislado ^(.venv^)...
  %PY% -m venv .venv
  if errorlevel 1 goto :error
)
set "VPY=.venv\Scripts\python.exe"

echo [2/4] Instalando el paquete ^(la primera vez tarda uno o dos minutos^)...
"%VPY%" -m pip install --disable-pip-version-check -q -e . pytest
if errorlevel 1 goto :error

echo [3/4] Corriendo las pruebas automaticas...
"%VPY%" -m pytest -q -p no:cacheprovider
if errorlevel 1 goto :error

echo [4/4] Analisis completo y reporte...
"%VPY%" -m costos revisar
if errorlevel 1 goto :error

echo.
echo Listo. El reporte se abrio en su navegador: reports\reporte.html
if not defined CI pause
exit /b 0

:sinpython
echo No encontre Python 3.10 o superior.
echo Instalelo desde https://www.python.org/downloads/
echo Durante la instalacion marque la casilla "Add python.exe to PATH" y vuelva a abrir este archivo.
if not defined CI pause
exit /b 1

:error
echo.
echo Ocurrio un error. El mensaje de arriba indica la causa.
if not defined CI pause
exit /b 1
