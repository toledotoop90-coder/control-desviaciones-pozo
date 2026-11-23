"""Reporte HTML autocontenido (fase Share).

Un solo archivo que se abre en cualquier navegador, sin conexión y sin
instalar nada: resultado general, validaciones, desviación por etapa,
figuras embebidas, hallazgos de calidad y partidas a justificar. Pensado
para que quien revise el proyecto vea el resultado sin abrir los CSV.

No incluye fecha ni hora para que la misma entrada produzca exactamente
el mismo archivo.
"""

from __future__ import annotations

import base64
import html
from pathlib import Path

import pandas as pd

from costos import __version__
from costos.pipeline import Resultado

_CSS = """
body{font-family:Calibri,'Segoe UI',Arial,sans-serif;color:#3C3C3B;max-width:1100px;margin:32px auto;padding:0 20px;line-height:1.45}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;color:#FF5900;margin:34px 0 10px;border-bottom:1px solid #eee;padding-bottom:4px}
.sub{color:#777;margin:0 0 18px}.aviso{background:#FFF4EC;border-left:4px solid #FF5900;padding:10px 14px;margin:14px 0}
.tiles{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0}.tile{flex:1;min-width:170px;border:1px solid #e6e6e6;border-radius:8px;padding:12px 14px}
.tile b{display:block;font-size:26px;color:#3C3C3B}.tile span{color:#777;font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0 4px}
th{background:#3C3C3B;color:#fff;text-align:left;padding:6px 8px;font-weight:600}
td{padding:5px 8px;border-bottom:1px solid #eee;vertical-align:top}td.n{text-align:right;white-space:nowrap}
.ok{color:#1b7f3b;font-weight:700}.falla{color:#c0392b;font-weight:700}
figure{margin:14px 0}figure img{max-width:100%;border:1px solid #eee;border-radius:6px}figcaption{color:#777;font-size:13px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:800px){.grid{grid-template-columns:1fr}}
footer{color:#999;font-size:12px;margin:40px 0 10px}
"""


_AVISO_DEMO = (
    "<div class='aviso'>Este reporte se generó con el <b>pozo sintético</b> del repositorio: los valores son inventados e imitan la estructura y "
    "los problemas del caso real, cuyos datos son confidenciales. Las figuras de la última sección sí corresponden al caso (Pozo A), "
    "reproducidas con los índices anonimizados publicados en el documento.</div>"
)


def _img(ruta: Path) -> str:
    datos = base64.b64encode(Path(ruta).read_bytes()).decode("ascii")
    return f'<img alt="{html.escape(Path(ruta).stem)}" src="data:image/png;base64,{datos}">'


def _tabla(df: pd.DataFrame, numericas: dict[str, str] | None = None) -> str:
    """Tabla HTML con formato por columna (``{"col": "{:,.2f}"}``)."""
    numericas = numericas or {}
    cab = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    filas = []
    for r in df.itertuples(index=False):
        celdas = []
        for c, v in zip(df.columns, r, strict=True):
            if c in numericas and pd.notna(v):
                v = 0.0 if abs(v) < 5e-5 else v  # evita mostrar "-0.00"
                celdas.append(f'<td class="n">{numericas[c].format(v)}</td>')
            elif c == "Resultado":
                clase = "ok" if v == "OK" else "falla"
                celdas.append(f'<td class="{clase}">{html.escape(str(v))}</td>')
            else:
                celdas.append(f"<td>{'' if pd.isna(v) else html.escape(str(v))}</td>")
        filas.append("<tr>" + "".join(celdas) + "</tr>")
    return f"<table><thead><tr>{cab}</tr></thead><tbody>{''.join(filas)}</tbody></table>"


def _tile(valor: str, texto: str) -> str:
    return f'<div class="tile"><b>{html.escape(valor)}</b><span>{html.escape(texto)}</span></div>'


def construir(res: Resultado, figuras: list[Path], figuras_documento: list[Path] | None = None, titulo: str = "") -> str:
    """Arma el HTML del reporte a partir del resultado y las figuras ya escritas."""
    comp = res.comparativa
    cerr = comp[comp["estado_etapa"].eq("cerrada")]
    vo = cerr["monto_vo_comparable"].sum()
    ok = int((res.validacion["resultado"] == "OK").sum())
    total = len(res.validacion)
    pozo = str(comp["pozo"].iloc[0]) if len(comp) else ""

    val = res.validacion.rename(
        columns={"prueba": "Prueba", "que_verifica": "Qué verifica", "esperado": "Esperado", "obtenido": "Obtenido", "resultado": "Resultado"}
    )
    etapa = res.resumen_etapa[
        [
            "etapa",
            "monto_vo_comparable",
            "importe_real",
            "efecto_descuento",
            "desviacion_operativa",
            "pct_desviacion",
            "pct_operativa",
            "partidas_a_justificar",
        ]
    ]
    etapa = etapa.rename(
        columns={
            "etapa": "Etapa",
            "monto_vo_comparable": "VO comparable (USD)",
            "importe_real": "Ejecutado (USD)",
            "efecto_descuento": "Efecto descuento (USD)",
            "desviacion_operativa": "Desviación operativa (USD)",
            "pct_desviacion": "% total",
            "pct_operativa": "% operativa",
            "partidas_a_justificar": "A justificar",
        }
    )
    dinero = "{:,.2f}"
    pct = "{:+.1%}"
    cal = res.calidad[["categoria", "regla", "fuente", "renglones", "tratamiento"]].rename(
        columns={"categoria": "Categoría", "regla": "Regla", "fuente": "Fuente", "renglones": "Renglones", "tratamiento": "Tratamiento"}
    )
    just = comp[comp["requiere_justificacion"]].copy()
    just["abs"] = just["desviacion_operativa"].abs()
    just = just.sort_values("abs", ascending=False)[["etapa", "partida", "descripcion", "desviacion_operativa", "efecto_dominante", "motivo"]].rename(
        columns={
            "etapa": "Etapa",
            "partida": "Partida",
            "descripcion": "Descripción",
            "desviacion_operativa": "Desviación operativa (USD)",
            "efecto_dominante": "Efecto dominante",
            "motivo": "Motivo",
        }
    )

    estado = "Todas las validaciones son correctas." if ok == total else "Hay validaciones con FALLA: no use estos resultados sin revisarlas."
    partes = [
        "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>",
        f"<title>Reporte de desviaciones · {html.escape(pozo)}</title><style>{_CSS}</style></head><body>",
        f"<h1>{html.escape(titulo or 'Del costo programado al ejecutado')}</h1>",
        f"<p class='sub'>Análisis de desviaciones por partida · pozo {html.escape(pozo)} · paquete costos {__version__}</p>",
        _AVISO_DEMO if pozo == "POZO-DEMO" else "",
        "<div class='tiles'>",
        _tile(f"{ok} de {total}", "validaciones correctas"),
        _tile(f"{len(comp)}", "partidas comparadas"),
        _tile(f"{int(comp['requiere_justificacion'].sum())}", "partidas a justificar"),
        _tile(f"{cerr['desviacion'].sum() / vo:+.1%}" if vo else "s/d", "desviación en etapas cerradas"),
        _tile(f"{cerr['efecto_descuento'].sum() / vo:+.1%}" if vo else "s/d", "de ella, descuento no aplicado en el VO"),
        "</div>",
        f"<h2>1. Validación del procesamiento y del modelo</h2><p>{estado} El modelo es determinístico, así que se valida por exactitud "
        "(cuadre y aditividad), no con MSE o R².</p>",
        _tabla(val, {"Esperado": dinero, "Obtenido": dinero}),
        "<h2>2. Desviación por etapa</h2><p>Desviación total = ejecutado − VO. Se separa el efecto descuento (precios del VO sin el 7%), "
        "que no es ahorro de la operación; lo que queda es la desviación operativa, que se justifica partida por partida.</p>",
        _tabla(
            etapa,
            {
                "VO comparable (USD)": dinero,
                "Ejecutado (USD)": dinero,
                "Efecto descuento (USD)": dinero,
                "Desviación operativa (USD)": dinero,
                "% total": pct,
                "% operativa": pct,
            },
        ),
        "<h2>3. Figuras del análisis</h2><div class='grid'>",
        *[f"<figure>{_img(f)}</figure>" for f in figuras],
        "</div>",
        "<h2>4. Hallazgos de calidad de datos</h2><p>Problemas detectados en las fuentes y cómo se trataron (categorías de Wang y Strong).</p>",
        _tabla(cal),
        "<h2>5. Partidas que requieren justificación</h2><p>Ordenadas por el tamaño de su desviación operativa. Umbral de 0%: toda desviación "
        "operativa se justifica; se exceptúan el efecto descuento y el redondeo.</p>",
        _tabla(just, {"Desviación operativa (USD)": dinero}),
    ]
    if figuras_documento:
        partes += [
            "<h2>6. Figuras del documento del caso (Pozo A)</h2><p>Reproducidas con los índices anonimizados de <code>data/anonimizado</code>; "
            "son las figuras 2, 3 y 4 del documento.</p><div class='grid'>",
            *[f"<figure>{_img(f)}</figure>" for f in figuras_documento],
            "</div>",
        ]
    partes += [
        "<footer>Generado con el paquete costos. La misma entrada produce siempre este mismo archivo.</footer></body></html>",
    ]
    return "\n".join(partes) + "\n"


def escribir(res: Resultado, figuras: list[Path], ruta: Path | str, figuras_documento: list[Path] | None = None) -> Path:
    """Escribe el reporte en disco y devuelve su ruta."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(construir(res, figuras, figuras_documento), encoding="utf-8")
    return ruta
