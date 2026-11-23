"""Evaluación de la calidad de los datos (fase Prepare).

Las reglas se agrupan con las categorías de Wang y Strong (1996):
intrínseca, contextual, de representación y de acceso. Cada hallazgo se
reporta con su tratamiento, para que la decisión quede documentada.
"""

from __future__ import annotations

import pandas as pd

from costos.config import Config
from costos.normalizar import normalizar_clave, precio_ya_tiene_descuento

COLUMNAS = ["categoria", "regla", "fuente", "renglones", "detalle", "tratamiento"]


def _h(categoria: str, regla: str, fuente: str, renglones: int, detalle: str, tratamiento: str) -> dict:
    return dict(zip(COLUMNAS, [categoria, regla, fuente, renglones, detalle, tratamiento], strict=True))


def claves_con_formato_irregular(df: pd.DataFrame, fuente: str) -> list[dict]:
    """Claves con espacios o punto final que cambiarían el cruce."""
    malas = df[df["partida"].astype(str) != df["partida"].map(normalizar_clave)]
    if malas.empty:
        return []
    ejemplos = ", ".join(sorted(set(malas["partida"].astype(str)))[:5])
    return [
        _h(
            "Representación",
            "Clave de partida con formato irregular",
            fuente,
            len(malas),
            f"Ejemplos: {ejemplos}",
            "Se normaliza como texto sin punto final",
        )
    ]


def duplicados_exactos(df: pd.DataFrame, fuente: str) -> list[dict]:
    """Renglones repetidos en todas sus columnas."""
    n = int(df.duplicated(keep="first").sum())
    if not n:
        return []
    return [_h("Intrínseca", "Renglón duplicado", fuente, n, "Renglones idénticos en todas las columnas", "Se conserva uno; no se suma dos veces")]


def valores_faltantes(df: pd.DataFrame, fuente: str, columnas: list[str]) -> list[dict]:
    """Celdas vacías en columnas obligatorias."""
    out = []
    for c in columnas:
        n = int(df[c].isna().sum())
        if n:
            out.append(_h("Intrínseca", "Valor faltante", fuente, n, f"Columna '{c}' vacía", "Se reporta; no se imputa ningún valor"))
    return out


def renglones_sin_descuento(vo: pd.DataFrame, cfg: Config = Config()) -> list[dict]:
    """Renglones del VO de contratos con descuento que no lo aplicaron."""
    sujetos = vo[vo["contrato"].isin(cfg.contratos_con_descuento)]
    if sujetos.empty:
        return []
    sin = sujetos[[not precio_ya_tiene_descuento(p, cfg) for p in sujetos["pu"]]]
    if sin.empty:
        return []
    monto = (sujetos["cantidad"] * sujetos["pu"]).sum()
    sobre = (sin["cantidad"] * sin["pu"] * cfg.descuento).sum()
    return [
        _h(
            "Intrínseca",
            "Precio del VO sin descuento contractual",
            "vo",
            len(sin),
            f"{len(sin)} de {len(sujetos)} renglones ({len(sin) / len(sujetos):.0%}); VO sobreestimado {sobre / monto:.1%}",
            "Se separa como efecto descuento VO; no se cuenta como ahorro",
        )
    ]


def metros_contra_programa(vo: pd.DataFrame, etapas: pd.DataFrame, cfg: Config = Config()) -> list[dict]:
    """Partidas por metro cuyo VO no coincide con el intervalo del programa."""
    intervalo = (etapas.set_index("etapa")["prof_fin"] - etapas.set_index("etapa")["prof_inicio"]).to_dict()
    por_metro = vo[vo["unidad"].str.upper().isin(cfg.unidades_por_metro)]
    out = []
    for r in por_metro.itertuples(index=False):
        prog = intervalo.get(r.etapa)
        if prog and abs(r.cantidad - prog) > cfg.tolerancia_cuadre:
            out.append(
                _h(
                    "Intrínseca",
                    "Metros del VO distintos al programa",
                    "vo",
                    1,
                    f"Etapa {r.etapa}, partida {r.partida}: VO {r.cantidad:,.0f} m contra programa {prog:,.0f} m ({(r.cantidad - prog) / prog:+.0%})",
                    "Se reporta como error de planeación del VO",
                )
            )
    return out


def pozo_distinto(df: pd.DataFrame, fuente: str, pozo: str) -> list[dict]:
    """Renglones que pertenecen a otro pozo."""
    otros = df[df["pozo"].astype(str).str.strip() != pozo]
    if otros.empty:
        return []
    return [
        _h(
            "Contextual",
            "Renglones de otro pozo",
            fuente,
            len(otros),
            f"Pozos encontrados: {', '.join(sorted(otros['pozo'].astype(str).unique()))}",
            "Se excluyen del análisis",
        )
    ]


def evaluar(vo: pd.DataFrame, ejecutado: pd.DataFrame, etapas: pd.DataFrame, pozo: str, cfg: Config = Config()) -> pd.DataFrame:
    """Corre todas las reglas de calidad sobre las fuentes crudas."""
    hallazgos: list[dict] = []
    obligatorias = ["etapa", "partida", "unidad", "cantidad", "pu"]
    for nombre, df in (("vo", vo), ("ejecutado", ejecutado)):
        hallazgos += claves_con_formato_irregular(df, nombre)
        hallazgos += duplicados_exactos(df, nombre)
        hallazgos += valores_faltantes(df, nombre, obligatorias)
        hallazgos += pozo_distinto(df, nombre, pozo)
    hallazgos += renglones_sin_descuento(vo, cfg)
    hallazgos += metros_contra_programa(vo, etapas, cfg)
    return pd.DataFrame(hallazgos, columns=COLUMNAS)
