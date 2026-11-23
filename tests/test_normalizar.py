import pandas as pd
import pytest

from costos.config import Config
from costos.normalizar import (
    agregar_por_partida,
    normalizar_clave,
    normalizar_fuente,
    precio_base,
    precio_vigente,
    precio_ya_tiene_descuento,
    quitar_duplicados_exactos,
)


@pytest.mark.parametrize(("entrada", "esperado"), [("6.90.", "6.90"), (" 6.90 ", "6.90"), ("6.9", "6.9"), ("3.10", "3.10"), ("4.186..", "4.186")])
def test_normalizar_clave_conserva_texto(entrada, esperado):
    assert normalizar_clave(entrada) == esperado


def test_claves_690_y_69_son_partidas_distintas():
    assert normalizar_clave("6.90.") != normalizar_clave("6.9")


@pytest.mark.parametrize(("pu", "esperado"), [(1761.234, True), (1893.80, False), (595.4511, True), (100.0, False), (0, False)])
def test_detecta_precio_con_descuento(pu, esperado):
    assert precio_ya_tiene_descuento(pu) is esperado


def test_precio_base_y_vigente():
    cfg = Config()
    assert precio_base(1761.234, "A", cfg) == pytest.approx(1893.80)
    assert precio_base(1893.80, "A", cfg) == pytest.approx(1893.80)
    assert precio_vigente(1893.80, "A", cfg) == pytest.approx(1761.234)
    assert precio_vigente(100.0, "Z", cfg) == pytest.approx(100.0), "Contratos sin acuerdo no llevan descuento"


def test_normalizar_fuente_y_agregar():
    df = pd.DataFrame(
        [("P", "E1", "6.90.", "x", "kg", "A", "S", 10, 1.3764), ("P", "E1", "6.90", "x", "kg", "A", "S", 5, 1.3764)],
        columns=["pozo", "etapa", "partida", "descripcion", "unidad", "contrato", "subrubro", "cantidad", "pu"],
    )
    n = normalizar_fuente(df)
    assert set(n["partida"]) == {"6.90"}
    assert n["unidad"].eq("KG").all()
    ag = agregar_por_partida(n)
    assert len(ag) == 1
    assert ag.loc[0, "cantidad"] == 15
    assert ag.loc[0, "monto"] == pytest.approx(15 * 1.3764)


def test_quitar_duplicados_exactos():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    limpio, n = quitar_duplicados_exactos(df)
    assert n == 1
    assert len(limpio) == 2
