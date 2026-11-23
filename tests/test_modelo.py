"""Pruebas del modelo de cinco efectos.

Incluye el ejemplo ilustrativo del documento y una prueba de propiedad:
para cualquier conjunto de partidas, los efectos suman la desviación.
"""

import numpy as np
import pandas as pd
import pytest

from costos.config import Config
from costos.modelo import EFECTOS, descomponer, participacion_operativa, puente, resumir
from costos.normalizar import agregar_por_partida, normalizar_fuente

COLS = ["pozo", "etapa", "partida", "descripcion", "unidad", "contrato", "subrubro", "cantidad", "pu"]


def _fuente(filas):
    return agregar_por_partida(normalizar_fuente(pd.DataFrame(filas, columns=COLS)))


def test_ejemplo_ilustrativo_del_documento(etapas_simples):
    """A: 100 m a 10.00 sin descuento, real 90 m a 9.50. B: nueva. C: no usada."""
    vo = _fuente(
        [
            ("P", "E1", "A", "a", "METRO", "A", "S1", 100, 10.00),
            ("P", "E1", "C", "c", "DIA", "A", "S2", 10, 15.00),
        ]
    )
    ej = _fuente(
        [
            ("P", "E1", "A", "a", "METRO", "A", "S1", 90, 9.50),
            ("P", "E1", "B", "b", "DIA", "A", "S2", 5, 20.00),
        ]
    )
    # C se programó a 15.00 tratándolo como precio ya vigente: contrato sin descuento
    vo.loc[vo["partida"] == "C", ["pu_base", "pu_vigente"]] = 15.00
    comp = descomponer(vo, ej, etapas_simples).set_index("partida")

    a = comp.loc["A"]
    assert a["efecto_descuento"] == pytest.approx(-70.0)
    assert a["efecto_cantidad"] == pytest.approx(-93.0)
    assert a["efecto_precio"] == pytest.approx(18.0)
    assert a["desviacion"] == pytest.approx(-145.0)
    assert comp.loc["B", "partida_nueva"] == pytest.approx(100.0)
    assert comp.loc["C", "partida_no_usada"] == pytest.approx(-150.0)
    assert comp["desviacion"].sum() == pytest.approx(-195.0)
    assert comp["desviacion_operativa"].sum() == pytest.approx(-125.0)


def test_efectos_suman_la_desviacion_en_datos_aleatorios(etapas_simples):
    rng = np.random.default_rng(7)
    n = 300
    claves = [f"{i}.{j}" for i, j in zip(rng.integers(1, 9, n), rng.integers(1, 200, n), strict=True)]
    vo_filas, ej_filas = [], []
    for k, clave in enumerate(dict.fromkeys(claves)):
        etapa = "E1" if k % 3 else "E2"
        base = round(float(rng.uniform(1, 5000)), 2)
        con_desc = bool(rng.integers(0, 2))
        pu_vo = round(base * 0.93, 4) if con_desc else base
        if rng.random() < 0.85:
            vo_filas.append(("P", etapa, clave, "d", "DIA", "A", f"S{k % 5}", float(rng.integers(1, 500)), pu_vo))
        if rng.random() < 0.8:
            ej_filas.append(("P", etapa, clave, "d", "DIA", "A", f"S{k % 5}", float(rng.integers(0, 600)), round(base * 0.93 + rng.normal(0, 1), 4)))
    comp = descomponer(_fuente(vo_filas), _fuente(ej_filas), etapas_simples)
    suma = comp[EFECTOS].sum(axis=1)
    assert np.allclose(suma, comp["desviacion"], atol=1e-6)
    assert np.allclose(comp["desviacion_operativa"], comp["desviacion"] - comp["efecto_descuento"])


def test_etapa_abierta_sin_ejecucion_no_es_comparable(etapas_simples):
    vo = _fuente([("P", "E2", "X", "x", "DIA", "A", "S", 10, 100.0)])
    ej = _fuente([("P", "E2", "Y", "y", "DIA", "A", "S", 1, 93.0)])
    comp = descomponer(vo, ej, etapas_simples).set_index("partida")
    assert not comp.loc["X", "comparable"]
    assert comp.loc["X", "partida_no_usada"] == 0
    assert "Pendiente" in comp.loc["X", "motivo"]
    assert comp.loc["Y", "partida_nueva"] == pytest.approx(93.0)


def test_solo_descuento_no_requiere_justificacion(etapas_simples):
    vo = _fuente([("P", "E1", "X", "x", "DIA", "A", "S", 10, 100.00)])
    ej = _fuente([("P", "E1", "X", "x", "DIA", "A", "S", 10, 93.00)])
    fila = descomponer(vo, ej, etapas_simples).iloc[0]
    assert fila["efecto_descuento"] == pytest.approx(-70.0)
    assert not fila["requiere_justificacion"]
    assert fila["motivo"].startswith("Solo efecto descuento")


def test_umbral_mayor_a_cero_excusa_desviaciones_pequenas(etapas_simples):
    vo = _fuente([("P", "E1", "X", "x", "DIA", "Z", "S", 100, 10.0)])
    ej = _fuente([("P", "E1", "X", "x", "DIA", "Z", "S", 101, 10.0)])
    assert descomponer(vo, ej, etapas_simples).iloc[0]["requiere_justificacion"]
    assert not descomponer(vo, ej, etapas_simples, Config(umbral_justificacion=0.05)).iloc[0]["requiere_justificacion"]


def test_resumir_puente_y_participacion(resultado):
    comp = resultado.comparativa
    r = resumir(comp, "etapa")
    assert r["desviacion"].sum() == pytest.approx(comp["desviacion"].sum())
    p = puente(comp)
    final = 100 + p["valor"].fillna(0).iloc[1:].sum()
    cerr = comp[comp["estado_etapa"].eq("cerrada")]
    assert final == pytest.approx(cerr["importe_real"].sum() / cerr["monto_vo_comparable"].sum() * 100)
    part = participacion_operativa(comp)
    assert part["participacion_pct"].sum() == pytest.approx(100.0)
