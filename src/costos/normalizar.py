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


_VERDADERO = {"true", "1", "si", "sí", "s", "yes", "con descuento"}
_FALSO = {"false", "0", "no", "n", "sin descuento"}


def marca_descuento(valor: object) -> bool | None:
    """Lee la marca opcional ``precio_con_descuento`` de una fuente.

    Cuando el área ya revisó el precio contra el anexo, la fuente puede
    traer la marca y esta manda sobre la regla de los decimales. Vacío o
    no reconocido devuelve ``None`` y se aplica la regla.

    >>> marca_descuento("Sí"), marca_descuento("no"), marca_descuento("")
    (True, False, None)
    """
    if isinstance(valor, bool):
        return valor
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip().lower()
    if texto in _VERDADERO:
        return True
    if texto in _FALSO:
        return False
    return None


def monto_fuente(df: pd.DataFrame) -> pd.Series:
    """Monto de cada renglón tal como lo trae la fuente.

    Si la fuente trae la columna opcional ``monto`` se respeta (el VO
    calcula sus montos con el precio redondeado a dos decimales y la
    cédula se arma con esos montos). Si no, se calcula cantidad × PU.
    """
    calculado = pd.to_numeric(df["cantidad"], errors="raise") * pd.to_numeric(df["pu"], errors="raise")
    if "monto" not in df.columns:
        return calculado
    declarado = pd.to_numeric(df["monto"], errors="coerce")
    return declarado.where(declarado.notna(), calculado)


def normalizar_fuente(df: pd.DataFrame, cfg: Config = Config()) -> pd.DataFrame:
    """Normaliza VO o ejecutado: claves, texto, montos y precios.

    Agrega las columnas ``monto``, ``monto_vigente``, ``pu_base``,
    ``pu_vigente`` y ``con_descuento``. ``monto_vigente`` es el monto del
    renglón al precio vigente, escalado desde el monto de la fuente para
    conservar su redondeo.
    """
    out = df.copy()
    out["partida"] = out["partida"].map(normalizar_clave)
    for col in ("pozo", "etapa", "unidad", "contrato", "subrubro"):
        out[col] = out[col].astype(str).str.strip()
    out["unidad"] = out["unidad"].str.upper()
    out["cantidad"] = pd.to_numeric(out["cantidad"], errors="raise")
    out["pu"] = pd.to_numeric(out["pu"], errors="raise")
    out["monto"] = monto_fuente(out)
    marcas = out["precio_con_descuento"].map(marca_descuento) if "precio_con_descuento" in out.columns else [None] * len(out)
    con_desc, bases = [], []
    for p, c, marca in zip(out["pu"], out["contrato"], marcas, strict=True):
        if c not in cfg.contratos_con_descuento:
            con_desc.append(True)
            bases.append(float(p))
            continue
        tiene = precio_ya_tiene_descuento(p, cfg) if marca is None else marca
        con_desc.append(tiene)
        bases.append(round(p / cfg.factor_vigente, 2) if tiene else float(p))
    out["con_descuento"] = con_desc
    out["pu_base"] = bases
    out["pu_vigente"] = [precio_vigente(b, c, cfg) for b, c in zip(out["pu_base"], out["contrato"], strict=True)]
    escala = (out["pu_vigente"] / out["pu"]).where(out["pu"] != 0)
    out["monto_vigente"] = (out["monto"] * escala).where(escala.notna(), out["cantidad"] * out["pu_vigente"])
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
        monto_vigente=("monto_vigente", "sum"),
    )
    primeras["pu"] = primeras["monto"] / primeras["cantidad"].where(primeras["cantidad"] != 0)
    return primeras
