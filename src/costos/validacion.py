"""Pruebas de validación del procesamiento y del modelo (fase Process).

Como el modelo es determinístico, no se valida con error de predicción
(MSE, R²) sino con exactitud: los totales deben cuadrar con las fuentes y
los efectos deben sumar la desviación de cada partida.
"""

from __future__ import annotations

import pandas as pd

from costos.config import Config
from costos.modelo import EFECTOS

COLUMNAS = ["prueba", "que_verifica", "esperado", "obtenido", "resultado"]


def _fila(prueba: str, que: str, esperado: float, obtenido: float, tol: float) -> dict:
    ok = abs(esperado - obtenido) <= tol
    return dict(zip(COLUMNAS, [prueba, que, round(esperado, 2), round(obtenido, 2), "OK" if ok else "FALLA"], strict=True))


def aditividad(comparativa: pd.DataFrame, cfg: Config = Config()) -> pd.DataFrame:
    """Partidas cuyos efectos no suman la desviación (deben ser cero)."""
    suma = comparativa[EFECTOS].sum(axis=1)
    error = (comparativa["desviacion"] - suma).abs()
    return comparativa.loc[error > cfg.tolerancia_cuadre, ["etapa", "partida", "desviacion"]].assign(suma_efectos=suma[error > cfg.tolerancia_cuadre])


def validar(vo_crudo: pd.DataFrame, ejecutado_crudo: pd.DataFrame, comparativa: pd.DataFrame, cedula: dict, cfg: Config = Config()) -> pd.DataFrame:
    """Corre las pruebas de validación y devuelve una tabla OK o FALLA.

    Args:
        vo_crudo: VO tal como se leyó, ya filtrado al pozo.
        ejecutado_crudo: Ejecutado tal como se leyó, ya filtrado y sin duplicados exactos.
        comparativa: Resultado de ``modelo.descomponer``.
        cedula: Contenido de ``cedula.json`` con ``total_vo``.
    """
    tol = cfg.tolerancia_cuadre
    total_vo = float((vo_crudo["cantidad"].astype(float) * vo_crudo["pu"].astype(float)).sum())
    total_ej = float((ejecutado_crudo["cantidad"].astype(float) * ejecutado_crudo["pu"].astype(float)).sum())
    filas = [
        _fila("Cuadre VO contra cédula", "La base de comparación es la oficial", float(cedula["total_vo"]), total_vo, tol),
        _fila("Conservación del VO", "Ningún renglón del VO se pierde al normalizar", total_vo, float(comparativa["monto_vo"].sum()), tol),
        _fila(
            "Conservación del ejecutado",
            "Ningún renglón del ejecutado se pierde al normalizar",
            total_ej,
            float(comparativa["importe_real"].sum()),
            tol,
        ),
        _fila("Aditividad de los efectos", "Los cinco efectos suman la desviación de cada partida", 0.0, float(len(aditividad(comparativa, cfg))), 0),
        _fila(
            "Desviación total",
            "La suma de desviaciones es ejecutado menos VO comparable",
            float(comparativa["importe_real"].sum() - comparativa["monto_vo_comparable"].sum()),
            float(comparativa["desviacion"].sum()),
            tol,
        ),
    ]
    return pd.DataFrame(filas, columns=COLUMNAS)
