"""Parámetros del análisis.

Todas las reglas de negocio que cambian el resultado viven aquí, con un
valor por defecto que corresponde a las decisiones documentadas en
``docs/decisiones.md``. Cambiar un parámetro es una decisión de criterio,
no de programación: debe quedar registrada en la bitácora.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    """Reglas de negocio del modelo.

    Attributes:
        descuento: Descuento contractual aplicable a los contratos con
            acuerdo referencial. PU vigente = PU base × (1 − descuento).
        contratos_con_descuento: Contratos a los que aplica el descuento.
        tolerancia_redondeo: Diferencia de precio por unidad que se
            considera redondeo (no requiere justificación).
        tolerancia_cuadre: Diferencia máxima aceptada al comparar sumas.
        umbral_justificacion: Fracción de desviación operativa a partir de
            la cual una partida requiere justificación. 0 significa que
            toda desviación operativa se justifica.
        unidades_por_metro: Unidades que se comparan contra el intervalo
            perforado del programa.
    """

    descuento: float = 0.07
    contratos_con_descuento: tuple[str, ...] = ("A", "B")
    tolerancia_redondeo: float = 0.005
    tolerancia_cuadre: float = 0.01
    umbral_justificacion: float = 0.0
    unidades_por_metro: tuple[str, ...] = field(default=("METRO PERFORADO", "METRO"))

    @property
    def factor_vigente(self) -> float:
        """Factor que convierte PU base en PU vigente."""
        return 1.0 - self.descuento
