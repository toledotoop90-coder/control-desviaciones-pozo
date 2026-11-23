"""Lectura de las fuentes y verificación de su esquema (fase Prepare).

Las claves de partida se leen siempre como texto. Si se leyeran como
número, "6.90" se convertiría en 6.9 y se cruzaría con otra partida.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ESQUEMAS: dict[str, list[str]] = {
    "vo": ["pozo", "etapa", "partida", "descripcion", "unidad", "contrato", "subrubro", "cantidad", "pu"],
    "ejecutado": ["pozo", "etapa", "partida", "descripcion", "unidad", "contrato", "subrubro", "cantidad", "pu", "fuente"],
    "etapas": ["etapa", "nombre", "estado", "prof_inicio", "prof_fin", "dias_programa", "dias_real"],
    "justificaciones": ["etapa", "partida", "causa", "subcausa", "justificacion", "tipo_soporte", "folio_soporte"],
}

_TEXTO = {"pozo": str, "etapa": str, "partida": str, "descripcion": str, "unidad": str, "contrato": str, "subrubro": str, "fuente": str}


class ErrorDeEsquema(ValueError):
    """La fuente no trae las columnas esperadas."""


def verificar_esquema(df: pd.DataFrame, nombre: str) -> None:
    """Lanza ``ErrorDeEsquema`` si faltan columnas obligatorias."""
    faltan = [c for c in ESQUEMAS[nombre] if c not in df.columns]
    if faltan:
        raise ErrorDeEsquema(f"La fuente '{nombre}' no trae las columnas: {', '.join(faltan)}")


def _leer_csv(ruta: Path, nombre: str) -> pd.DataFrame:
    tipos = {c: t for c, t in _TEXTO.items() if c in ESQUEMAS[nombre]}
    df = pd.read_csv(ruta, dtype=tipos, keep_default_na=False, na_values=[""])
    verificar_esquema(df, nombre)
    return df


def leer_vo(ruta: Path | str) -> pd.DataFrame:
    """Volumen de obra validado: lo programado por partida y etapa."""
    return _leer_csv(Path(ruta), "vo")


def leer_ejecutado(ruta: Path | str) -> pd.DataFrame:
    """Lo empleado en campo (etapas cerradas) o lo solicitado (etapas abiertas)."""
    return _leer_csv(Path(ruta), "ejecutado")


def leer_etapas(ruta: Path | str) -> pd.DataFrame:
    """Programa por etapa: estado, intervalo y días programados y reales."""
    df = pd.read_csv(ruta, dtype={"etapa": str, "nombre": str, "estado": str})
    verificar_esquema(df, "etapas")
    return df


def leer_justificaciones(ruta: Path | str) -> pd.DataFrame:
    """Justificaciones capturadas por el ingeniero de seguimiento."""
    df = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    verificar_esquema(df, "justificaciones")
    return df


def leer_cedula(ruta: Path | str) -> dict:
    """Total autorizado en la cédula, para el cuadre contra el VO."""
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_pozo(carpeta: Path | str) -> dict[str, object]:
    """Carga todas las fuentes de un pozo desde una carpeta.

    Espera los archivos ``vo.csv``, ``ejecutado.csv``, ``etapas.csv``,
    ``justificaciones.csv`` y ``cedula.json``.
    """
    c = Path(carpeta)
    return {
        "vo": leer_vo(c / "vo.csv"),
        "ejecutado": leer_ejecutado(c / "ejecutado.csv"),
        "etapas": leer_etapas(c / "etapas.csv"),
        "justificaciones": leer_justificaciones(c / "justificaciones.csv"),
        "cedula": leer_cedula(c / "cedula.json"),
    }
