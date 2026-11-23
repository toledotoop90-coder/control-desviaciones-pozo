"""Línea de comandos del proyecto.

Ejemplos::

    costos generar-sintetico --salida data/sintetico
    costos ejecutar --datos data/sintetico --salida reports/sintetico
    costos figuras-documento --datos data/anonimizado --salida reports/figuras_documento
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from costos import pipeline, sintetico


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="costos", description="Control de desviaciones de costo de un pozo exploratorio.")
    p.add_argument("-v", "--verbose", action="store_true", help="Muestra el detalle de cada fase.")
    sub = p.add_subparsers(dest="comando", required=True)

    g = sub.add_parser("generar-sintetico", help="Escribe el pozo sintético de demostración.")
    g.add_argument("--salida", type=Path, default=Path("data/sintetico"))

    e = sub.add_parser("ejecutar", help="Corre el análisis completo de un pozo.")
    e.add_argument("--datos", type=Path, default=Path("data/sintetico"))
    e.add_argument("--salida", type=Path, default=Path("reports/sintetico"))

    f = sub.add_parser("figuras-documento", help="Reproduce las figuras del documento con los índices anonimizados.")
    f.add_argument("--datos", type=Path, default=Path("data/anonimizado"))
    f.add_argument("--salida", type=Path, default=Path("reports/figuras_documento"))
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
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
