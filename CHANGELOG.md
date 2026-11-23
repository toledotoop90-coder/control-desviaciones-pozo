# Cambios

## 1.1.0 (23 nov 2026)

Verificación con los datos originales del caso. Al correr el paquete con las fuentes reales del Pozo A (en un equipo del área, sin publicarlas) aparecieron tres diferencias contra el análisis interno. Se corrigieron y ahora el resultado coincide partida por partida (diferencia máxima de medio centavo) y en todas las cifras del documento.

* Columna opcional `monto`: si la fuente trae su monto se respeta. El VO calcula sus montos con el precio a dos decimales y la cédula se arma con ellos.
* Columna opcional `precio_con_descuento`: cuando el área ya revisó el precio contra el anexo, la marca manda sobre la regla de los decimales. Caso real: un PU de 0.93 que ya era vigente (1.00 × 0.93) y la regla lo tomaba como precio sin descuento.
* Tolerancia de redondeo con margen de punto flotante: 0.01 calculado como 0.0100000001 ya no se manda a justificar.
* Misma cantidad que el VO con solo centavos de diferencia se clasifica como redondeo, no como efecto cantidad.
* 34 pruebas (tres nuevas con los casos reales, sin datos de la empresa).

## 1.0.0 (22 nov 2026)

* Primera versión pública para el proyecto final de Ciencia de Datos.
* Paquete `costos` con las fases Prepare, Process, Analyze, Share y Act.
* Modelo de análisis de variaciones en cinco efectos con prueba de aditividad.
* Pozo sintético, índices anonimizados del documento y notebook ejecutado.
* 31 pruebas automáticas e integración continua.
