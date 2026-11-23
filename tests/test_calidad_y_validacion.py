"""Calidad de datos y validación, incluida una prueba de mutación.

La prueba de mutación introduce errores a propósito y comprueba que la
validación los detecta. Si una validación nunca falla, no está probando nada.
"""

import pandas as pd

from costos import validacion
from costos.io import cargar_pozo


def test_calidad_detecta_los_problemas_sembrados(resultado):
    reglas = set(resultado.calidad["regla"])
    assert {
        "Clave de partida con formato irregular",
        "Renglón duplicado",
        "Valor faltante",
        "Renglones de otro pozo",
        "Precio del VO sin descuento contractual",
        "Metros del VO distintos al programa",
    } <= reglas


def test_validacion_pasa_con_datos_correctos(resultado):
    assert resultado.validacion["resultado"].eq("OK").all()


def _entradas(carpeta, resultado):
    f = cargar_pozo(carpeta)
    vo = f["vo"][f["vo"]["pozo"] == f["cedula"]["pozo"]]
    ej = f["ejecutado"][f["ejecutado"]["pozo"] == f["cedula"]["pozo"]].drop_duplicates()
    return vo, ej, resultado.comparativa.copy(), dict(f["cedula"])


def test_mutacion_un_dolar_en_un_efecto(carpeta_sintetica, resultado):
    vo, ej, comp, ced = _entradas(carpeta_sintetica, resultado)
    comp.loc[comp.index[0], "efecto_cantidad"] += 1.0
    v = validacion.validar(vo, ej, comp, ced).set_index("prueba")
    assert v.loc["Aditividad de los efectos", "resultado"] == "FALLA"


def test_mutacion_cedula_distinta(carpeta_sintetica, resultado):
    vo, ej, comp, ced = _entradas(carpeta_sintetica, resultado)
    ced["total_vo"] += 1.0
    v = validacion.validar(vo, ej, comp, ced).set_index("prueba")
    assert v.loc["Cuadre VO contra cédula", "resultado"] == "FALLA"


def test_mutacion_renglon_perdido(carpeta_sintetica, resultado):
    vo, ej, comp, ced = _entradas(carpeta_sintetica, resultado)
    comp = comp.drop(index=comp.index[comp["monto_vo"] > 0][0])
    v = validacion.validar(vo, ej, comp, ced).set_index("prueba")
    assert v.loc["Conservación del VO", "resultado"] == "FALLA"


def test_aditividad_vacia_si_todo_cuadra(resultado):
    assert validacion.aditividad(resultado.comparativa).empty
    assert isinstance(validacion.aditividad(resultado.comparativa), pd.DataFrame)
