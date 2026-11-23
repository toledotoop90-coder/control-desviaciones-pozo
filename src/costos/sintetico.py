"""Generador del pozo sintético de demostración.

Los datos reales son confidenciales. Este pozo sintético imita su
estructura y reproduce, a propósito, los mismos tipos de problemas que se
encontraron en el caso real: precios del VO sin descuento, metros del VO
distintos al programa, una clave con punto final, un renglón duplicado,
un renglón de otro pozo, partidas nuevas, partidas no usadas, una
diferencia de precio y justificaciones sin soporte.

Los valores son inventados. No representan ningún pozo real.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from costos.config import Config

POZO = "POZO-DEMO"
SUB = {
    "02": "1.2.02 Equipo de perforación y terminación",
    "03": "1.2.03 Perforación por etapas",
    "04": "1.2.04 Perforación direccional",
    "05": "1.2.05 Cementación",
    "06": "1.2.06 Fluidos de perforación",
    "07": "1.2.07 Registros geofísicos",
    "09": "1.2.09 Recuperación de fluidos",
}
# partida: (descripción, unidad, subrubro, PU base del contrato)
CATALOGO = {
    "3.05": ("Servicio integrado de perforación, conductor 30 pulgadas", "METRO PERFORADO", "03", 1800.55),
    "3.10": ("Servicio integrado de perforación, TR 20 pulgadas", "METRO PERFORADO", "03", 550.41),
    "3.22": ("Servicio integrado de perforación, TR 16 pulgadas", "METRO PERFORADO", "03", 680.37),
    "2.72": ("Servicio integral de membrana", "DIA", "02", 640.27),
    "4.23": ("Servicio direccional con sistema rotatorio", "DIA", "04", 9500.13),
    "4.186": ("Herramienta mitigadora de vibración axial", "DIA", "04", 300.29),
    "5.83": ("Tanque recirculador para preparar baches", "OPERACION", "05", 1550.47),
    "5.138": ("Bache lavador para lodo base agua", "M3", "05", 240.81),
    "6.78": ("Aplicación de viscosificante", "KG", "06", 21.01),
    "6.90": ("Material sellante y obturante", "KG", "06", 1.48),
    "6.9": ("Aditivo estabilizador de lutitas", "KG", "06", 3.21),
    "6.114": ("Especialista de fluidos en campo", "DIA", "06", 450.33),
    "6.117": ("Silos presurizables de 100 toneladas", "DIA", "06", 130.22),
    "6.174": ("Tanques auxiliares", "DIA", "06", 210.64),
    "7.12": ("Registro de rayos gamma", "OPERACION", "07", 2300.19),
    "9.46": ("Recuperación y transporte de fluidos residuales", "M3", "09", 115.37),
}
ETAPAS = [
    # etapa, nombre, estado, inicio, fin, días programa, días real
    ("1-30", "Etapa 30 pulgadas", "cerrada", 0, 50, 5.0, 4.0),
    ("2-20", "Etapa 20 pulgadas", "cerrada", 50, 900, 12.0, 18.0),
    ("3-16", "Etapa 16 pulgadas", "abierta", 900, 2300, 22.0, None),
]
# etapa, partida (como viene capturada), cantidad, ¿precio con descuento?
VO = [
    ("1-30", "3.05", 50, False),
    ("1-30", "2.72", 6, True),
    ("1-30", "5.83", 1, False),
    ("1-30", "6.78", 1000, True),
    ("1-30", "6.90.", 800, True),
    ("1-30", "6.117", 12, False),
    ("1-30", "6.174", 40, True),
    ("1-30", "9.46", 20, True),
    ("2-20", "3.10", 1150, False),
    ("2-20", "2.72", 14, True),
    ("2-20", "4.23", 10, True),
    ("2-20", "4.186", 12, False),
    ("2-20", "5.83", 2, True),
    ("2-20", "5.138", 8, True),
    ("2-20", "6.78", 3000, False),
    ("2-20", "6.9", 500, True),
    ("2-20", "6.114", 12, True),
    ("2-20", "6.117", 16, True),
    ("2-20", "6.174", 60, False),
    ("2-20", "9.46", 60, True),
    ("3-16", "3.22", 1400, True),
    ("3-16", "2.72", 22, True),
    ("3-16", "4.23", 18, True),
    ("3-16", "6.78", 2500, True),
    ("3-16", "6.114", 22, False),
    ("3-16", "7.12", 2, True),
]
# etapa, partida, cantidad, sobreprecio por unidad, fuente
EJECUTADO = [
    ("1-30", "3.05", 44, 0.0, "empleado"),
    ("1-30", "2.72", 5.3, 0.0, "empleado"),
    ("1-30", "5.83", 1, 0.0, "empleado"),
    ("1-30", "6.90", 650, 0.0, "empleado"),
    ("1-30", "6.117", 10, 0.0, "empleado"),
    ("1-30", "6.174", 22.25, 0.0, "empleado"),
    ("1-30", "9.46", 17, 0.0, "empleado"),
    ("1-30", "6.114", 8.6, 0.0, "empleado"),
    ("2-20", "3.10", 880, 0.0, "empleado"),
    ("2-20", "2.72", 19.5, 0.0, "empleado"),
    ("2-20", "4.23", 6, 0.0, "empleado"),
    ("2-20", "5.83", 2, 20.0, "empleado"),
    ("2-20", "5.138", 5, 0.0, "empleado"),
    ("2-20", "6.78", 1800, 0.0, "empleado"),
    ("2-20", "6.114", 19.5, 0.0, "empleado"),
    ("2-20", "6.117", 19.5, 0.0, "empleado"),
    ("2-20", "6.174", 58, 0.0, "empleado"),
    ("2-20", "9.46", 45, 0.0, "empleado"),
    ("2-20", "7.12", 1, 0.0, "empleado"),
    ("3-16", "3.22", 1400, 0.0, "solicitado"),
    ("3-16", "2.72", 23, 0.0, "solicitado"),
    ("3-16", "4.23", 18, 0.0, "solicitado"),
    ("3-16", "6.78", 2400, 0.0, "solicitado"),
]
JUSTIFICACIONES = [
    # etapa, partida, causa, subcausa, justificación, tipo de soporte, folio
    (
        "1-30",
        "3.05",
        "Desempeño real de la etapa",
        "Menos metros perforados que lo programado",
        "La zapata se asentó a 44 m por formación competente.",
        "ESTADO MECANICO",
        "EM-DEMO-014",
    ),
    (
        "1-30",
        "6.78",
        "Condición prevista que no se presentó",
        "Propiedades del fluido en rango sin el aditivo",
        "No fue necesario el viscosificante.",
        "",
        "",
    ),
    (
        "1-30",
        "6.114",
        "Planeación del VO",
        "Partida programada en otra etapa",
        "El especialista se requirió desde la etapa de 30.",
        "SIS COMPLEMENTARIA",
        "",
    ),
    ("1-30", "6.174", "Optimización", "Menos días de renta", "Optimización de partida.", "MINUTA", "MIN-DEMO-033"),
    (
        "2-20",
        "3.10",
        "Desempeño real de la etapa",
        "Más metros perforados que lo programado",
        "Se perforó 30 m más que el intervalo del programa.",
        "REPORTE DIARIO",
        "RD-DEMO-118",
    ),
    ("2-20", "4.186", "Condición prevista que no se presentó", "Material de contingencia no requerido", "Sin vibración axial significativa.", "", ""),
]


def _pu_vo(base: float, con_descuento: bool, cfg: Config) -> float:
    return round(base * cfg.factor_vigente, 4) if con_descuento else base


def generar(carpeta: Path | str, cfg: Config = Config()) -> Path:
    """Escribe el pozo sintético en ``carpeta`` y devuelve la ruta."""
    c = Path(carpeta)
    c.mkdir(parents=True, exist_ok=True)

    vo_filas = []
    for etapa, partida, q, con_desc in VO:
        desc, unidad, sub, base = CATALOGO[partida.rstrip(".")]
        pu = _pu_vo(base, con_desc, cfg)
        if con_desc:
            assert len(f"{pu:.6f}".rstrip("0").split(".")[1]) > 2, f"El precio con descuento de {partida} debe tener más de 2 decimales"
        vo_filas.append((POZO, etapa, partida, desc, unidad, "A", SUB[sub], q, pu))
    vo = pd.DataFrame(vo_filas, columns=["pozo", "etapa", "partida", "descripcion", "unidad", "contrato", "subrubro", "cantidad", "pu"])

    ej_filas = []
    for etapa, partida, q, extra, fuente in EJECUTADO:
        desc, unidad, sub, base = CATALOGO[partida]
        ej_filas.append((POZO, etapa, partida, desc, unidad, "A", SUB[sub], q, round(base * cfg.factor_vigente, 4) + extra, fuente))
    duplicado = next(f for f in ej_filas if f[1] == "2-20" and f[2] == "6.117")
    ej_filas.append(duplicado)
    ej_filas.append(("POZO-OTRO", "1-30", "6.117", "Silos presurizables de 100 toneladas", "", "A", SUB["06"], 4, 121.1046, "empleado"))
    ej = pd.DataFrame(ej_filas, columns=["pozo", "etapa", "partida", "descripcion", "unidad", "contrato", "subrubro", "cantidad", "pu", "fuente"])

    etapas = pd.DataFrame(ETAPAS, columns=["etapa", "nombre", "estado", "prof_inicio", "prof_fin", "dias_programa", "dias_real"])
    just = pd.DataFrame(JUSTIFICACIONES, columns=["etapa", "partida", "causa", "subcausa", "justificacion", "tipo_soporte", "folio_soporte"])

    vo.to_csv(c / "vo.csv", index=False)
    ej.to_csv(c / "ejecutado.csv", index=False)
    etapas.to_csv(c / "etapas.csv", index=False)
    just.to_csv(c / "justificaciones.csv", index=False)
    total_vo = round(float((vo["cantidad"] * vo["pu"]).sum()), 2)
    (c / "cedula.json").write_text(json.dumps({"pozo": POZO, "total_vo": total_vo, "moneda": "USD", "clase": 2}, indent=2), encoding="utf-8")
    return c
