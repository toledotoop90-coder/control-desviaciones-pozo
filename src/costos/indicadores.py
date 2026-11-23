"""Indicadores para medir el control (fase Act).

Las metas son propuestas del equipo para validar con el área. La línea
base sale de los datos; el impacto se comprobará al medir los pozos
siguientes.
"""

from __future__ import annotations

import pandas as pd

from costos.config import Config
from costos.normalizar import normalizar_clave, precio_ya_tiene_descuento

SOPORTES_VALIDOS = {"DAC", "ICR", "SIS COMPLEMENTARIA", "REPORTE DIARIO", "MINUTA", "ESTADO MECANICO", "TALLY"}


def soporte_valido(tipo: str, folio: str) -> bool:
    """Un soporte es válido si tiene un tipo reconocido y un folio no vacío."""
    return str(tipo).strip().upper() in SOPORTES_VALIDOS and bool(str(folio).strip())


def calcular(
    vo: pd.DataFrame, etapas: pd.DataFrame, comparativa: pd.DataFrame, justificaciones: pd.DataFrame, cfg: Config = Config()
) -> pd.DataFrame:
    """Calcula la línea base de los seis indicadores del caso."""
    a_justificar = comparativa[comparativa["requiere_justificacion"]]
    j = justificaciones.assign(partida=justificaciones["partida"].map(normalizar_clave))
    j = j.merge(a_justificar[["etapa", "partida"]], on=["etapa", "partida"], how="inner")
    validas = sum(soporte_valido(t, f) for t, f in zip(j["tipo_soporte"], j["folio_soporte"], strict=True))
    revisadas = len(j)

    sujetos = vo[vo["contrato"].isin(cfg.contratos_con_descuento)]
    con_desc = sum(precio_ya_tiene_descuento(p, cfg) for p in sujetos["pu"])

    intervalo = (etapas.set_index("etapa")["prof_fin"] - etapas.set_index("etapa")["prof_inicio"]).to_dict()
    por_metro = vo[vo["unidad"].str.upper().isin(cfg.unidades_por_metro)].copy()
    por_metro["programa"] = por_metro["etapa"].map(intervalo)
    desv_metros = ((por_metro["cantidad"] - por_metro["programa"]) / por_metro["programa"]).abs().max()

    filas = [
        ("Justificaciones con soporte válido", "Con soporte válido ÷ revisadas", validas / revisadas if revisadas else None, 0.90, "Por etapa"),
        ("Partidas a justificar", "Partidas con desviación operativa", float(len(a_justificar)), None, "Por etapa"),
        (
            "Descuento aplicado en el VO",
            "Renglones con descuento ÷ renglones del contrato",
            con_desc / len(sujetos) if len(sujetos) else None,
            1.0,
            "Por VO",
        ),
        ("Metros del VO contra programa", "Máxima |VO − programa| ÷ programa", float(desv_metros) if pd.notna(desv_metros) else None, 0.0, "Por VO"),
    ]
    return pd.DataFrame(filas, columns=["indicador", "formula", "linea_base", "meta", "frecuencia"])
