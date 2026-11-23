"""Control de desviaciones de costo en la perforación de un pozo exploratorio.

Paquete del proyecto final de Ciencia de Datos (Universidad Anáhuac Puebla).
Implementa las fases Prepare, Process, Analyze, Share y Act del análisis
de datos sobre la comparación partida por partida entre lo programado
(volumen de obra) y lo ejecutado.

El modelo central es un análisis de variaciones determinístico: cada
desviación se divide en cinco efectos que suman exactamente el total.
"""

from costos.config import Config
from costos.modelo import descomponer, resumir

__all__ = ["Config", "descomponer", "resumir"]
__version__ = "1.0.0"
