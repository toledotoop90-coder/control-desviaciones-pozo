"""Limpieza y transformación de las fuentes (fase Process).

Convierte cada fuente en una tabla ordenada: una variable por columna y
una observación (partida en una etapa) por fila. Ningún archivo fuente se
modifica; las correcciones viven en la tabla normalizada.
"""

from __future__ import annotations

import pandas as pd

from costos.config import Config


def normalizar_clave(clave: object) -> str:
    """Normaliza la clave de una partida conservándola como texto.

    Quita espacios y un punto final sobrante ("6.90." -> "6.90"). No
    convierte a número: "6.90" y "6.9" son partidas distintas.

    >>> normalizar_clave(" 6.90. ")
    '6.90'
    """
    texto = str(clave).strip()
    while texto.endswith("."):
        texto = texto[:-1]
    return texto


def _decimales(valor: float) -> int:
    texto = f"{valor:.6f}".rstrip("0")
    return len(texto.split(".")[1]) if "." in texto else 0


def precio_ya_tiene_descuento(pu: float, cfg: Config = Config()) -> bool:
    """Indica si un precio del VO ya trae el descuento contractual.

    Regla documentada (sin anexo de precios): si el precio tiene más de dos
    decimales y al dividirlo entre el factor vigente da un precio de dos
    decimales, el precio ya trae el descuento; si no, es precio completo.
    """
    if pd.isna(pu) or pu <= 0:
        return False
    if _decimales(pu) <= 2:
        return False
    base = pu / cfg.factor_vigente
    return abs(base - round(base, 2)) < 1e-4


def precio_base(pu: float, contrato: str, cfg: Config = Config()) -> float:
    """PU base del contrato deducido del precio del VO."""
    if contrato in cfg.contratos_con_descuento and precio_ya_tiene_descuento(pu, cfg):
        return round(pu / cfg.factor_vigente, 2)
    return float(pu)


def precio_vigente(pu_base: float, contrato: str, cfg: Config = Config()) -> float:
    """PU vigente: el que el contrato realmente cobra."""
    if contrato in cfg.contratos_con_descuento:
        return pu_base * cfg.factor_vigente
    return pu_base


def normalizar_fuente(df: pd.DataFrame, cfg: Config = Config()) -> pd.DataFrame:
    """Normaliza VO o ejecutado: claves, texto, montos y precios.

    Agrega las columnas ``monto``, ``pu_base``, ``pu_vigente`` y
    ``con_descuento``. Agrupa renglones repetidos de la misma partida en la
    misma etapa sumando cantidades, porque el modelo trabaja a nivel de
    partida por etapa.
    """
    out = df.copy()
    out["partida"] = out["partida"].map(normalizar_clave)
    for col in ("pozo", "etapa", "unidad", "contrato", "subrubro"):
        out[col] = out[col].astype(str).str.strip()
    out["unidad"] = out["unidad"].str.upper()
    out["cantidad"] = pd.to_numeric(out["cantidad"], errors="raise")
    out["pu"] = pd.to_numeric(out["pu"], errors="raise")
    out["monto"] = out["cantidad"] * out["pu"]
    out["con_descuento"] = [
        (c not in cfg.contratos_con_descuento) or precio_ya_tiene_descuento(p, cfg) for p, c in zip(out["pu"], out["contrato"], strict=True)
    ]
    out["pu_base"] = [precio_base(p, c, cfg) for p, c in zip(out["pu"], out["contrato"], strict=True)]
    out["pu_vigente"] = [precio_vigente(b, c, cfg) for b, c in zip(out["pu_base"], out["contrato"], strict=True)]
    return out


def quitar_duplicados_exactos(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Elimina renglones idénticos en todas sus columnas.

    Un renglón repetido completo es un error de captura, no una segunda
    solicitud; sumarlo duplicaría la cantidad. Devuelve la tabla limpia y
    el número de renglones eliminados, que se reporta en calidad.
    """
    limpio = df.drop_duplicates(keep="first").reset_index(drop=True)
    return limpio, len(df) - len(limpio)


def agregar_por_partida(df: pd.DataFrame) -> pd.DataFrame:
    """Suma cantidades y montos de renglones repetidos por etapa y partida."""
    claves = ["pozo", "etapa", "partida"]
    primeras = df.groupby(claves, as_index=False).agg(
        descripcion=("descripcion", "first"),
        unidad=("unidad", "first"),
        contrato=("contrato", "first"),
        subrubro=("subrubro", "first"),
        pu_base=("pu_base", "max"),
        pu_vigente=("pu_vigente", "max"),
        cantidad=("cantidad", "sum"),
        monto=("monto", "sum"),
    )
    primeras["pu"] = primeras["monto"] / primeras["cantidad"].where(primeras["cantidad"] != 0)
    return primeras
