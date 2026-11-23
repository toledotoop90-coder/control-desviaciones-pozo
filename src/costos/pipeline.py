"""Orquestación de las fases Prepare, Process, Analyze, Share y Act.

``ejecutar`` corre el análisis completo de un pozo y escribe todas las
salidas en una carpeta: tablas en CSV, figuras en PNG, un resumen en
Markdown y un reporte HTML. La misma entrada produce siempre la misma salida.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from costos import calidad, indicadores, modelo, validacion, visualizacion
from costos.config import Config
from costos.io import cargar_pozo
from costos.normalizar import agregar_por_partida, normalizar_fuente, quitar_duplicados_exactos

log = logging.getLogger(__name__)


@dataclass
class Resultado:
    """Tablas producidas por el análisis."""

    calidad: pd.DataFrame
    comparativa: pd.DataFrame
    resumen_etapa: pd.DataFrame
    resumen_subrubro: pd.DataFrame
    puente: pd.DataFrame
    validacion: pd.DataFrame
    indicadores: pd.DataFrame
    huellas: pd.DataFrame


def huellas(carpeta: Path) -> pd.DataFrame:
    """Huella SHA-256 de cada archivo fuente, para saber qué cambió entre corridas."""
    filas = []
    for ruta in sorted(Path(carpeta).glob("*")):
        if ruta.is_file():
            filas.append({"archivo": ruta.name, "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest()})
    return pd.DataFrame(filas)


def analizar(carpeta_datos: Path | str, cfg: Config = Config()) -> Resultado:
    """Corre el análisis completo en memoria y devuelve las tablas."""
    carpeta = Path(carpeta_datos)
    f = cargar_pozo(carpeta)
    pozo = f["cedula"]["pozo"]

    # Prepare: calidad sobre las fuentes tal como llegaron
    hallazgos = calidad.evaluar(f["vo"], f["ejecutado"], f["etapas"], pozo, cfg)
    log.info("Calidad: %d hallazgos", len(hallazgos))

    # Process: filtrar al pozo, quitar duplicados exactos y normalizar
    vo = f["vo"][f["vo"]["pozo"].str.strip() == pozo]
    ej = f["ejecutado"][f["ejecutado"]["pozo"].str.strip() == pozo]
    ej, n_dup = quitar_duplicados_exactos(ej)
    log.info("Duplicados exactos eliminados: %d", n_dup)
    vo_n = agregar_por_partida(normalizar_fuente(vo, cfg))
    ej_n = agregar_por_partida(normalizar_fuente(ej, cfg))

    # Analyze: modelo de cinco efectos y agregados
    comp = modelo.descomponer(vo_n, ej_n, f["etapas"], cfg)
    res_etapa = modelo.resumir(comp, "etapa")
    res_sub = modelo.resumir(comp, "subrubro")
    pte = modelo.puente(comp)

    # Validación del procesamiento y del modelo
    val = validacion.validar(vo, ej, comp, f["cedula"], cfg)
    log.info("Validación: %s", dict(val["resultado"].value_counts()))

    # Act: línea base de los indicadores
    kpi = indicadores.calcular(normalizar_fuente(vo, cfg), f["etapas"], comp, f["justificaciones"], cfg)
    return Resultado(hallazgos, comp, res_etapa, res_sub, pte, val, kpi, huellas(carpeta))


def figuras(res: Resultado, etapas: pd.DataFrame, carpeta: Path) -> list[Path]:
    """Genera las tres figuras del caso a partir del resultado."""
    rutas = []
    rutas.append(
        visualizacion.guardar(
            visualizacion.cascada(
                res.puente,
                "Puente del VO al ejecutado en las etapas cerradas",
                "Índice VO programado = 100. Verde: menos costo; rojo: más costo; rayado: precio del VO sin descuento.",
            ),
            carpeta / "cascada.png",
        )
    )
    part = modelo.participacion_operativa(res.comparativa)
    part = part[part["participacion_pct"] > 0]
    rutas.append(
        visualizacion.guardar(
            visualizacion.barras_horizontales(
                part["subrubro"].tolist(), part["participacion_pct"].round(1).tolist(), "Participación de cada subrubro en la desviación operativa"
            ),
            carpeta / "pareto_subrubro.png",
        )
    )
    intervalo = (etapas.set_index("etapa")["prof_fin"] - etapas.set_index("etapa")["prof_inicio"]).to_dict()
    metro = res.comparativa[res.comparativa["unidad"].isin(Config().unidades_por_metro) & res.comparativa["estado_etapa"].eq("cerrada")].copy()
    if not metro.empty:
        metro["programa"] = metro["etapa"].map(intervalo)
        r = metro.loc[(metro["q_vo"] - metro["programa"]).abs().idxmax()]
        rutas.append(
            visualizacion.guardar(
                visualizacion.barras_horizontales(
                    ["Volumen de obra", "Programa", "Perforado"],
                    [r["q_vo"], r["programa"], r["q_real"]],
                    f"Metros de la partida {r['partida']}, etapa {r['etapa']}",
                    resaltar=0,
                    formato="{:,.0f} m",
                    colores=[visualizacion.CLARO, visualizacion.OSCURO, visualizacion.ACENTO],
                ),
                carpeta / "metros.png",
            )
        )
    return rutas


def _tabla_md(df: pd.DataFrame) -> str:
    """Tabla en Markdown sin dependencias externas."""
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "| " + " | ".join("---" for _ in df.columns) + " |"
    filas = ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)]
    return "\n".join([cab, sep, *filas])


def _resumen_md(res: Resultado) -> str:
    cerr = res.comparativa[res.comparativa["estado_etapa"].eq("cerrada")]
    vo = cerr["monto_vo_comparable"].sum()
    lineas = [
        "# Resumen del análisis",
        "",
        f"- Etapas cerradas: desviación total {cerr['desviacion'].sum() / vo:+.1%} contra el VO; "
        f"efecto descuento {cerr['efecto_descuento'].sum() / vo:+.1%}; desviación operativa {cerr['desviacion_operativa'].sum() / vo:+.1%}.",
        f"- Partidas que requieren justificación: {int(res.comparativa['requiere_justificacion'].sum())}.",
        f"- Hallazgos de calidad: {len(res.calidad)}.",
        f"- Pruebas de validación: {(res.validacion['resultado'] == 'OK').sum()} de {len(res.validacion)} correctas.",
        "",
        "## Validación",
        "",
        _tabla_md(res.validacion),
    ]
    return "\n".join(lineas) + "\n"


def ejecutar(carpeta_datos: Path | str, carpeta_salida: Path | str, cfg: Config = Config()) -> Resultado:
    """Corre el análisis completo y escribe las salidas en disco."""
    salida = Path(carpeta_salida)
    salida.mkdir(parents=True, exist_ok=True)
    res = analizar(carpeta_datos, cfg)
    tablas = {
        "calidad": res.calidad,
        "comparativa_partidas": res.comparativa,
        "resumen_etapa": res.resumen_etapa,
        "resumen_subrubro": res.resumen_subrubro,
        "puente": res.puente,
        "validacion": res.validacion,
        "indicadores": res.indicadores,
        "huellas_fuentes": res.huellas,
    }
    for nombre, df in tablas.items():
        df.to_csv(salida / f"{nombre}.csv", index=False, encoding="utf-8-sig")
    etapas = cargar_pozo(carpeta_datos)["etapas"]
    rutas = figuras(res, etapas, salida / "figuras")
    (salida / "resumen.md").write_text(_resumen_md(res), encoding="utf-8")
    from costos import reporte  # importación local: reporte depende de este módulo

    reporte.escribir(res, rutas, salida / "reporte.html")
    log.info("Salidas escritas en %s", salida)
    return res


def figuras_documento(carpeta_anonimizado: Path | str, carpeta_salida: Path | str) -> list[Path]:
    """Reproduce las figuras 2 a 4 del documento con los índices anonimizados."""
    c, s = Path(carpeta_anonimizado), Path(carpeta_salida)
    pte = pd.read_csv(c / "puente_etapas_cerradas.csv")
    part = pd.read_csv(c / "participacion_subrubro.csv")
    met = pd.read_csv(c / "metros_etapa_20.csv")
    return [
        visualizacion.guardar(
            visualizacion.cascada(
                pte, "De 22.4 puntos por debajo del VO, 5.4 son descuento no aplicado", 'Índice VO programado = 100. Etapas cerradas de 30" y 20".'
            ),
            s / "figura_2_cascada.png",
        ),
        visualizacion.guardar(
            visualizacion.barras_horizontales(
                part["subrubro"].tolist(), part["participacion_pct"].tolist(), "Dos subrubros explican 89% de la desviación operativa"
            ),
            s / "figura_3_pareto.png",
        ),
        visualizacion.guardar(
            visualizacion.barras_horizontales(
                met["concepto"].tolist(),
                met["metros"].tolist(),
                "Contra el VO parecen 203 m de ahorro; contra el programa son 47 m de más",
                resaltar=0,
                formato="{:,.0f} m",
                colores=[visualizacion.CLARO, visualizacion.OSCURO, visualizacion.ACENTO],
            ),
            s / "figura_4_metros.png",
        ),
    ]
