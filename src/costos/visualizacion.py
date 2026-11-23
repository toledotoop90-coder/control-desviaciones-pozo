"""Figuras del caso (fase Share).

Cada figura lleva el hallazgo en el título y un solo color de acento.
Las funciones reciben tablas ya calculadas, así que sirven igual para los
datos sintéticos que para los índices anonimizados del documento.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

OSCURO, GRIS, ACENTO = "#3C3C3B", "#7F7F7F", "#FF5900"
MENOS_COSTO, MAS_COSTO, TOTAL, CLARO = "#00917F", "#C4613F", "#6E6E6E", "#BFBFBF"


def _estilo(ax) -> None:
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)


def _signo(v: float) -> str:
    return "0.0" if abs(v) < 0.05 else f"{v:+.1f}".replace("-", "−")


def cascada(pasos: pd.DataFrame, titulo: str, nota: str = "") -> plt.Figure:
    """Puente del VO al ejecutado.

    Args:
        pasos: Columnas ``paso``, ``valor`` y ``tipo`` (total, vo, subtotal,
            operativo, final), como las devuelve ``modelo.puente``.
    """
    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=150)
    acumulado, inicio_operativo = 0.0, None
    for i, r in enumerate(pasos.itertuples(index=False)):
        if r.tipo == "total":
            a, b = 0.0, r.valor
            acumulado = r.valor
        elif r.tipo in ("subtotal", "final"):
            a, b = 0.0, acumulado
            if r.tipo == "subtotal":
                inicio_operativo = (i + 1, acumulado)
        else:
            a, b = acumulado, acumulado + r.valor
            acumulado = b
        bajo, alto = min(a, b), max(a, b)
        if r.tipo in ("total", "subtotal", "final"):
            kw = {"color": TOTAL}
        elif r.tipo == "vo":
            kw = {"color": "#EFEFEF", "edgecolor": GRIS, "hatch": "///", "linewidth": 0.8}
        else:
            kw = {"color": MENOS_COSTO if r.valor < 0 else MAS_COSTO}
        ax.bar(i, max(alto - bajo, 0.25), bottom=bajo, width=0.62, **kw)
        etiqueta = f"{b:.1f}" if r.tipo in ("total", "subtotal", "final") else _signo(r.valor)
        ax.text(i, alto + 1.2, etiqueta, ha="center", va="bottom", fontsize=11, color=OSCURO, fontweight="bold" if r.tipo == "final" else "normal")
        if i < len(pasos) - 1:
            ax.plot([i + 0.31, i + 0.69], [b, b], color=GRIS, lw=0.8, ls="--")
    if inicio_operativo:
        operativa = acumulado - inicio_operativo[1]
        x0, x1 = inicio_operativo[0] - 0.3, len(pasos) - 2 + 0.3
        tope = 100 + 3
        ax.plot([x0, x1], [tope, tope], color=OSCURO, lw=0.9)
        ax.text(
            (x0 + x1) / 2, tope + 1.5, f"Desviación operativa: {_signo(operativa)} puntos", ha="center", fontsize=11, fontweight="bold", color=OSCURO
        )
    ax.set_xticks(range(len(pasos)))
    ax.set_xticklabels([textwrap.fill(p, 11) for p in pasos["paso"]], fontsize=10, color=OSCURO)
    ax.set_ylim(0, 112)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    _estilo(ax)
    ax.set_title(titulo, fontsize=13, fontweight="bold", color=OSCURO, loc="left", pad=14)
    if nota:
        fig.text(0.01, -0.02, nota, fontsize=9, color=GRIS)
    return fig


def barras_horizontales(
    etiquetas: list[str],
    valores: list[float],
    titulo: str,
    resaltar: int = 2,
    formato: str = "{:.1f}%",
    nota: str = "",
    colores: list[str] | None = None,
) -> plt.Figure:
    """Barras ordenadas con las primeras ``resaltar`` en color de acento.

    ``colores`` fija el color de cada barra cuando el orden no indica
    importancia (por ejemplo, VO contra programa contra real).
    """
    fig, ax = plt.subplots(figsize=(10, 0.6 * len(valores) + 1.2), dpi=150)
    colores = colores or [ACENTO if i < resaltar else CLARO for i in range(len(valores))]
    ax.barh(range(len(valores)), valores, color=colores, height=0.6)
    maximo = max(valores) if valores else 1
    for i, v in enumerate(valores):
        ax.text(v + maximo * 0.01, i, formato.format(v), va="center", fontsize=11, color=OSCURO)
    ax.set_yticks(range(len(valores)))
    ax.set_yticklabels(etiquetas, fontsize=11, color=OSCURO)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.set_xlim(0, maximo * 1.15)
    _estilo(ax)
    ax.set_title(titulo, fontsize=13, fontweight="bold", color=OSCURO, loc="left", pad=10)
    if nota:
        fig.text(0.01, -0.03, nota, fontsize=9, color=GRIS)
    return fig


def guardar(fig: plt.Figure, ruta: Path | str) -> Path:
    """Guarda la figura en PNG y la cierra."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta
