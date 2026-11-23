#!/usr/bin/env bash
# Revisión del proyecto en macOS o Linux: doble clic (macOS) o "bash ejecutar_mac_linux.command".
# Crea un entorno aislado en la carpeta .venv, instala, corre las pruebas y abre el reporte.
set -euo pipefail
cd "$(dirname "$0")"

pausa() { if [ -z "${CI:-}" ]; then read -r -p "Presione Enter para cerrar..." _ || true; fi; }
trap 'echo; echo "Ocurrió un error. El mensaje de arriba indica la causa."; pausa' ERR

echo "============================================================"
echo " Control de desviaciones de costo · revisión del proyecto"
echo "============================================================"
echo

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "No encontré Python 3.10 o superior."
  echo "Instálelo desde https://www.python.org/downloads/ y vuelva a abrir este archivo."
  pausa; exit 1
fi
echo "Python encontrado: $("$PY" --version)"

if [ ! -x .venv/bin/python ]; then
  echo "[1/4] Creando el entorno aislado (.venv)..."
  "$PY" -m venv .venv
else
  echo "[1/4] Entorno aislado ya existe (.venv)."
fi
echo "[2/4] Instalando el paquete (la primera vez tarda uno o dos minutos)..."
.venv/bin/python -m pip install --disable-pip-version-check -q -e . pytest
echo "[3/4] Corriendo las pruebas automáticas..."
.venv/bin/python -m pytest -q -p no:cacheprovider
echo "[4/4] Análisis completo y reporte..."
.venv/bin/python -m costos revisar

echo
echo "Listo. El reporte se abrió en su navegador: reports/reporte.html"
pausa
