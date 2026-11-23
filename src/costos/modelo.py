"""Modelo de análisis de variaciones por partida (fase Analyze).

Para cada partida en cada etapa, la desviación se divide en cinco efectos
que suman exactamente el total:

    desviación = importe ejecutado − monto VO
               = descuento VO + cantidad + precio + nuevas − no usadas

* Descuento VO = monto VO a PU vigente − monto VO. Es un error del VO.
* Cantidad     = (q real − q VO) × PU vigente. Variación de eficiencia.
* Precio       = q real × (PU real − PU vigente). Variación de precio.
* Nueva        = importe de partidas sin VO en la etapa.
* No usada     = −monto VO a PU vigente de partidas sin uso (etapa cerrada).

La desviación operativa es la desviación total menos el efecto descuento.
El orden de cálculo es fijo (precio vigente, luego cantidad, luego precio
real), por eso no queda residuo ni efecto conjunto.

El modelo es determinístico: no estima parámetros. Su validación es de
exactitud (cuadre y aditividad), no de error de predicción.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from costos.config import Config

EFECTOS = ["efecto_descuento", "efecto_cantidad", "efecto_precio", "partida_nueva", "partida_no_usada"]
_EFECTOS_OPERATIVOS = ["efecto_cantidad", "efecto_precio", "partida_nueva", "partida_no_usada"]
_NOMBRES = {
    "efecto_cantidad": "Efecto cantidad",
    "efecto_precio": "Efecto precio",
    "partida_nueva": "Partida nueva",
    "partida_no_usada": "Partida no usada",
}


def descomponer(vo: pd.DataFrame, ejecutado: pd.DataFrame, etapas: pd.DataFrame, cfg: Config = Config()) -> pd.DataFrame:
    """Compara VO contra ejecutado partida por partida y calcula los efectos.

    Args:
        vo: VO normalizado y agregado por partida (``normalizar.agregar_por_partida``).
        ejecutado: Ejecutado normalizado y agregado por partida.
        etapas: Tabla de etapas con la columna ``estado`` ("cerrada" o "abierta").
        cfg: Reglas de negocio.

    Returns:
        Una fila por etapa y partida con montos, los cinco efectos, la
        desviación total y operativa, y si la partida requiere justificación.
    """
    claves = ["pozo", "etapa", "partida"]
    a = vo.rename(columns={"cantidad": "q_vo", "pu": "pu_vo", "monto": "monto_vo"})
    b = ejecutado.rename(columns={"cantidad": "q_real", "pu": "pu_real", "monto": "importe_real"})
    cols_info = ["descripcion", "unidad", "contrato", "subrubro"]
    m = a.merge(b, on=claves, how="outer", suffixes=("", "_ej"), indicator=True)
    for c in cols_info + ["pu_vigente"]:
        m[c] = m[c].where(m[c].notna(), m[f"{c}_ej"])
    m = m.drop(columns=[f"{c}_ej" for c in cols_info + ["pu_base", "pu_vigente"]])

    estado = etapas.set_index("etapa")["estado"].to_dict()
    m["estado_etapa"] = m["etapa"].map(estado).fillna("sin programa")
    for c in ("q_vo", "monto_vo", "q_real", "importe_real"):
        m[c] = m[c].fillna(0.0)

    hay_vo = m["_merge"].isin(["both", "left_only"])
    hay_ej = m["_merge"].isin(["both", "right_only"])
    cerrada = m["estado_etapa"].eq("cerrada")

    m["comparable"] = hay_ej | (hay_vo & cerrada)
    vo_vig = m["q_vo"] * m["pu_vigente"]

    m["efecto_descuento"] = np.where(hay_vo & m["comparable"], vo_vig - m["monto_vo"], 0.0)
    m["efecto_cantidad"] = np.where(hay_vo & hay_ej, (m["q_real"] - m["q_vo"]) * m["pu_vigente"], 0.0)
    m["efecto_precio"] = np.where(hay_vo & hay_ej, m["importe_real"] - m["q_real"] * m["pu_vigente"], 0.0)
    m["partida_nueva"] = np.where(~hay_vo & hay_ej, m["importe_real"], 0.0)
    m["partida_no_usada"] = np.where(hay_vo & ~hay_ej & cerrada, -vo_vig, 0.0)

    m["monto_vo_comparable"] = np.where(m["comparable"], m["monto_vo"], 0.0)
    m["desviacion"] = np.where(m["comparable"], m["importe_real"] - m["monto_vo"], 0.0)
    m["desviacion_operativa"] = m["desviacion"] - m["efecto_descuento"]

    m["requiere_justificacion"], m["motivo"] = zip(*[_motivo(r, cfg) for r in m.itertuples(index=False)], strict=True)
    m["efecto_dominante"] = m[_EFECTOS_OPERATIVOS].abs().idxmax(axis=1).map(_NOMBRES)
    m.loc[~m["requiere_justificacion"], "efecto_dominante"] = ""
    m = m.drop(columns="_merge")
    orden = (
        claves
        + cols_info
        + [
            "estado_etapa",
            "comparable",
            "q_vo",
            "pu_vo",
            "monto_vo",
            "monto_vo_comparable",
            "q_real",
            "pu_real",
            "importe_real",
            "pu_vigente",
            *EFECTOS,
            "desviacion",
            "desviacion_operativa",
            "requiere_justificacion",
            "efecto_dominante",
            "motivo",
        ]
    )
    return m[orden].sort_values(["etapa", "partida"]).reset_index(drop=True)


def _motivo(r, cfg: Config) -> tuple[bool, str]:
    """Decide si la partida requiere justificación y por qué."""
    tol = cfg.tolerancia_cuadre
    if not r.comparable:
        return False, "Pendiente: etapa abierta sin ejecución de la partida"
    redondeo = abs(r.efecto_precio) <= cfg.tolerancia_redondeo * max(abs(r.q_real), 1.0)
    base = abs(r.monto_vo_comparable) if r.monto_vo_comparable else abs(r.importe_real)
    operativa = abs(r.desviacion_operativa)
    if base and operativa / base <= cfg.umbral_justificacion and cfg.umbral_justificacion > 0:
        return False, "Desviación operativa dentro del umbral"
    activos = [n for n in _EFECTOS_OPERATIVOS if abs(getattr(r, n)) > tol and not (n == "efecto_precio" and redondeo)]
    if activos:
        return True, " + ".join(_NOMBRES[n] for n in activos)
    if abs(r.efecto_descuento) > tol:
        return False, "Solo efecto descuento VO (no requiere justificación)"
    if abs(r.efecto_precio) > tol:
        return False, "Solo redondeo de precio"
    return False, "Sin desviación"


def resumir(comparativa: pd.DataFrame, por: list[str] | str = "etapa") -> pd.DataFrame:
    """Agrega la comparativa por etapa, subrubro o cualquier columna.

    Incluye el porcentaje de la desviación total y operativa contra el VO
    comparable, y el número de partidas que requieren justificación.
    """
    por = [por] if isinstance(por, str) else por
    g = comparativa.groupby(por, as_index=False).agg(
        monto_vo_comparable=("monto_vo_comparable", "sum"),
        importe_real=("importe_real", "sum"),
        **{e: (e, "sum") for e in EFECTOS},
        desviacion=("desviacion", "sum"),
        desviacion_operativa=("desviacion_operativa", "sum"),
        partidas_a_justificar=("requiere_justificacion", "sum"),
    )
    base = g["monto_vo_comparable"].where(g["monto_vo_comparable"] != 0)
    g["pct_desviacion"] = g["desviacion"] / base
    g["pct_operativa"] = g["desviacion_operativa"] / base
    return g


def puente(comparativa: pd.DataFrame, etapas: list[str] | None = None) -> pd.DataFrame:
    """Pasos del puente (cascada) del VO al ejecutado como índice VO = 100.

    Args:
        comparativa: Resultado de ``descomponer``.
        etapas: Etapas a incluir; por defecto, las cerradas.
    """
    cerradas = comparativa["estado_etapa"].eq("cerrada")
    df = comparativa[cerradas] if etapas is None else comparativa[comparativa["etapa"].isin(etapas)]
    vo = df["monto_vo_comparable"].sum()
    if vo == 0:
        raise ValueError("No hay VO comparable para construir el puente")
    pasos = [
        ("VO programado", 100.0, "total"),
        ("Descuento no aplicado", df["efecto_descuento"].sum() / vo * 100, "vo"),
        ("VO a precio vigente", None, "subtotal"),
        ("Cantidad", df["efecto_cantidad"].sum() / vo * 100, "operativo"),
        ("Partidas no usadas", df["partida_no_usada"].sum() / vo * 100, "operativo"),
        ("Partidas nuevas", df["partida_nueva"].sum() / vo * 100, "operativo"),
        ("Precio", df["efecto_precio"].sum() / vo * 100, "operativo"),
        ("Ejecutado", None, "final"),
    ]
    return pd.DataFrame(pasos, columns=["paso", "valor", "tipo"])


def participacion_operativa(comparativa: pd.DataFrame, por: str = "subrubro") -> pd.DataFrame:
    """Participación de cada grupo en la desviación operativa total (%)."""
    g = comparativa.groupby(por, as_index=False)["desviacion_operativa"].sum()
    total = g["desviacion_operativa"].sum()
    g["participacion_pct"] = g["desviacion_operativa"] / total * 100 if total else np.nan
    return g.sort_values("participacion_pct", ascending=False).reset_index(drop=True)
