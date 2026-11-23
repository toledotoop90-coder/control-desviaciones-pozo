"""Línea de comandos del proyecto.

Ejemplos::

    costos revisar                      # todo en un paso y abre el reporte
    costos generar-sintetico --salida data/sintetico
    costos ejecutar --datos data/sintetico --salida reports/sintetico
    costos figuras-documento --datos data/anonimizado --salida reports/figuras_documento
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import webbrowser
from pathlib import Path

from costos import pipeline, reporte, sintetico


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="costos", description="Control de desviaciones de costo de un pozo exploratorio.")
    p.add_argument("-v", "--verbose", action="store_true", help="Muestra el detalle de cada fase.")
    sub = p.add_subparsers(dest="comando", required=True)

    r = sub.add_parser("revisar", help="Todo en un paso: análisis del pozo sintético, figuras del documento y reporte HTML.")
    r.add_argument("--salida", type=Path, default=Path("reports"))
    r.add_argument("--no-abrir", action="store_true", help="No abre el reporte en el navegador.")

    g = sub.add_parser("generar-sintetico", help="Escribe el pozo sintético de demostración.")
    g.add_argument("--salida", type=Path, default=Path("data/sintetico"))

    e = sub.add_parser("ejecutar", help="Corre el análisis completo de un pozo.")
    e.add_argument("--datos", type=Path, default=Path("data/sintetico"))
    e.add_argument("--salida", type=Path, default=Path("reports/sintetico"))

    f = sub.add_parser("figuras-documento", help="Reproduce las figuras del documento con los índices anonimizados.")
    f.add_argument("--datos", type=Path, default=Path("data/anonimizado"))
    f.add_argument("--salida", type=Path, default=Path("reports/figuras_documento"))
    return p


def _raiz_datos() -> Path:
    """Carpeta ``data`` del repositorio, sin importar desde dónde se llame."""
    for base in (Path.cwd(), *Path(__file__).resolve().parents):
        if (base / "data" / "anonimizado").is_dir():
            return base / "data"
    raise SystemExit("No encuentro la carpeta data del repositorio. Corra el comando dentro de la carpeta del proyecto.")


def _revisar(salida: Path, abrir: bool) -> int:
    datos = _raiz_datos()
    print("1/3 Análisis del pozo sintético...")
    res = pipeline.ejecutar(datos / "sintetico", salida / "sintetico")
    print("2/3 Figuras del documento con los índices anonimizados del Pozo A...")
    figs_doc = pipeline.figuras_documento(datos / "anonimizado", salida / "figuras_documento")
    print("3/3 Reporte HTML...")
    orden = ["cascada.png", "pareto_subrubro.png", "metros.png"]
    figs = [salida / "sintetico" / "figuras" / n for n in orden if (salida / "sintetico" / "figuras" / n).exists()]
    ruta = reporte.escribir(res, figs, salida / "reporte.html", figs_doc).resolve()
    fallas = int((res.validacion["resultado"] != "OK").sum())
    print()
    print(
        f"Listo: {len(res.comparativa)} partidas, {int(res.comparativa['requiere_justificacion'].sum())} a justificar, "
        f"{len(res.validacion) - fallas} de {len(res.validacion)} validaciones correctas."
    )
    print(f"Reporte: {ruta}")
    if abrir:
        webbrowser.open(ruta.as_uri())
    return 1 if fallas else 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    if args.comando == "revisar":
        return _revisar(args.salida, abrir=not args.no_abrir and not os.environ.get("CI"))
    if args.comando == "generar-sintetico":
        print(f"Pozo sintético escrito en {sintetico.generar(args.salida)}")
    elif args.comando == "ejecutar":
        res = pipeline.ejecutar(args.datos, args.salida)
        fallas = (res.validacion["resultado"] != "OK").sum()
        print(
            f"Análisis completo en {args.salida}: {len(res.comparativa)} partidas, "
            f"{int(res.comparativa['requiere_justificacion'].sum())} a justificar, "
            f"{len(res.validacion) - fallas} de {len(res.validacion)} pruebas de validación correctas."
        )
        if fallas:
            print("Hay pruebas de validación con FALLA: revise validacion.csv antes de usar los resultados.", file=sys.stderr)
            return 1
    elif args.comando == "figuras-documento":
        rutas = pipeline.figuras_documento(args.datos, args.salida)
        print("Figuras escritas: " + ", ".join(str(r) for r in rutas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
