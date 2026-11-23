"""Pruebas de extremo a extremo y de consistencia con el documento del caso."""

import pandas as pd
import pytest

from costos import cli, pipeline

SALIDAS = ["calidad", "comparativa_partidas", "resumen_etapa", "resumen_subrubro", "puente", "validacion", "indicadores", "huellas_fuentes"]


def test_ejecutar_escribe_todas_las_salidas(carpeta_sintetica, tmp_path):
    pipeline.ejecutar(carpeta_sintetica, tmp_path)
    for nombre in SALIDAS:
        assert (tmp_path / f"{nombre}.csv").stat().st_size > 0
    for fig in ("cascada.png", "pareto_subrubro.png", "metros.png"):
        assert (tmp_path / "figuras" / fig).stat().st_size > 10_000
    assert "Validación" in (tmp_path / "resumen.md").read_text(encoding="utf-8")


def test_el_analisis_es_reproducible(carpeta_sintetica):
    a = pipeline.analizar(carpeta_sintetica).comparativa
    b = pipeline.analizar(carpeta_sintetica).comparativa
    pd.testing.assert_frame_equal(a, b)


def test_cli_completo(tmp_path):
    datos, salida = tmp_path / "datos", tmp_path / "salida"
    assert cli.main(["generar-sintetico", "--salida", str(datos)]) == 0
    assert cli.main(["ejecutar", "--datos", str(datos), "--salida", str(salida)]) == 0
    assert (salida / "comparativa_partidas.csv").exists()


def test_indices_anonimizados_coinciden_con_el_documento(raiz):
    c = raiz / "data" / "anonimizado"
    pte = pd.read_csv(c / "puente_etapas_cerradas.csv")
    final = 100 + pte["valor"].fillna(0).iloc[1:].sum()
    assert round(final, 1) == 77.6, "Ejecutado de las etapas cerradas: 77.6 (22.4 puntos bajo el VO)"
    operativa = pte.loc[pte["tipo"].eq("operativo"), "valor"].sum()
    assert round(operativa, 1) == -17.0
    part = pd.read_csv(c / "participacion_subrubro.csv")
    assert round(part["participacion_pct"].head(2).sum(), 1) == 89.2
    assert round(part["participacion_pct"].head(3).sum(), 1) == 98.2
    met = pd.read_csv(c / "metros_etapa_20.csv").set_index("concepto")["metros"]
    assert met["Volumen de obra"] - met["Perforado en campo"] == 203
    assert met["Perforado en campo"] - met["Programa oficial"] == 47
    assert (met["Perforado en campo"] / met["Programa oficial"] - 1) == pytest.approx(0.0528, abs=1e-3)


def test_figuras_del_documento(raiz, tmp_path):
    rutas = pipeline.figuras_documento(raiz / "data" / "anonimizado", tmp_path)
    assert len(rutas) == 3
    assert all(r.stat().st_size > 10_000 for r in rutas)


def test_reporte_html_autocontenido(tmp_path):
    from costos import cli

    assert cli.main(["revisar", "--salida", str(tmp_path), "--no-abrir"]) == 0
    texto = (tmp_path / "reporte.html").read_text(encoding="utf-8")
    assert "5 de 5" in texto and "validaciones correctas" in texto
    assert texto.count("data:image/png;base64,") == 6  # tres del análisis y tres del documento
    assert "pozo sintético" in texto
    assert "-0.00" not in texto
    assert "http://" not in texto and "https://" not in texto  # no depende de internet


def test_reporte_es_reproducible(tmp_path):
    from costos import cli

    cli.main(["revisar", "--salida", str(tmp_path / "a"), "--no-abrir"])
    cli.main(["revisar", "--salida", str(tmp_path / "b"), "--no-abrir"])
    assert (tmp_path / "a" / "reporte.html").read_bytes() == (tmp_path / "b" / "reporte.html").read_bytes()
