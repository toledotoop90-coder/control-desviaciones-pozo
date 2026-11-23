# Bitácora de decisiones

Cada regla del código corresponde a una decisión confirmada por el líder del área. Cambiar una regla es una decisión de criterio y debe registrarse aquí.

| Fecha | Decisión | Dónde vive en el código |
| --- | --- | --- |
| 13 nov 2026 | Descuento de 7% a todas las partidas de los contratos con acuerdo referencial; no aplica a otros contratos | `Config.descuento`, `Config.contratos_con_descuento` |
| 13 nov 2026 | Base de comparación: VO validado tal como está; el efecto descuento se reporta aparte, no como ahorro | `modelo.descomponer` (efecto descuento y desviación operativa) |
| 13 nov 2026 | Umbral de justificación de 0%; se exceptúan efecto descuento y redondeo | `Config.umbral_justificacion`, `modelo._motivo` |
| 13 nov 2026 | Claves de partida siempre como texto | `io._TEXTO`, `normalizar.normalizar_clave` |
| 13 nov 2026 | Sin anexo de precios: precio base deducido del VO con la premisa del 7% | `normalizar.precio_ya_tiene_descuento`, `normalizar.precio_base` |
| 13 nov 2026 | Contingencias no activadas no requieren justificación | Pendiente de implementar en esta versión pública |
| 14 nov 2026 | Etapas abiertas se comparan contra lo solicitado; las partidas sin ejecución quedan pendientes | `modelo.descomponer` (columna `comparable`) |
| 15 nov 2026 | Documento soporte obligatorio; se considera válido si tiene tipo reconocido y folio | `indicadores.soporte_valido` |
| 17 nov 2026 | El reporte no se emite si la validación falla | `cli.main` termina con código 1 |
| 21 nov 2026 | Verificación con prueba de mutación | `tests/test_calidad_y_validacion.py` |
| 23 nov 2026 | Se respetan el monto y la revisión de precio de la fuente; misma cantidad con centavos de diferencia es redondeo. Surgió al verificar el paquete con los datos originales del caso | `normalizar.monto_fuente`, `normalizar.marca_descuento`, `modelo._motivo` |
