# Cambios

## 1.2.0 (23 nov 2026)

Para que cualquier persona revise el proyecto sin pelear con la instalación.

* `costos revisar`: un solo comando corre el análisis, reproduce las figuras del documento y abre un reporte HTML.
* Reporte HTML autocontenido (`reporte.html`): validaciones, desviación por etapa, figuras embebidas, calidad y partidas a justificar. Se abre sin internet y es idéntico entre corridas.
* Archivos de doble clic: `ejecutar_windows.bat` y `ejecutar_mac_linux.command`. Crean un entorno aislado, instalan, corren las pruebas y abren el reporte.
* Notebook listo para Google Colab, con botón en el README: la primera celda descarga e instala el paquete.
* La integración continua prueba los archivos de doble clic en Windows, macOS y Linux, y el notebook en un entorno sin el paquete, como en Colab.
* Se elimina la advertencia de licencia que aparecía al instalar.
* 36 pruebas.

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
