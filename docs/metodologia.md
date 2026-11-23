# Metodología

## 1. Selección del modelo

La necesidad es explicar ante Dirección, partida por partida y con evidencia, por qué el costo real se apartó del programado. Tres preguntas llevan a la elección, antes de ver los datos:

1. **Tipo de pregunta.** Es diagnóstica: el pozo ya se perforó. Una pregunta predictiva pediría aprendizaje supervisado; una exploratoria, no supervisado.
2. **Fórmula conocida.** El monto es cantidad por precio según el contrato y el costo de la etapa es la suma de sus partidas. Lo que se conoce se calcula, no se estima.
3. **Exigencia del usuario.** El resultado debe cuadrar al peso con la cédula, ser trazable al documento y explicable para quien lo firma.

Los datos no decidieron el modelo. Con cientos de pozos, la pregunta de por qué se desvió este pozo se contestaría igual; esos pozos servirían para otra pregunta, predictiva: cuánto se desviará el siguiente pozo antes de emitir su cédula (Breiman, 2001).

### Alternativas evaluadas

| Criterio | Comparar totales | Supervisado (regresión, random forest) | No supervisado (clustering) | Descomposición (elegido) |
| --- | --- | --- | --- | --- |
| Responde por qué pasó | Parcial | No | No | Sí |
| Cuadra al peso | Sí | No | No | Sí |
| Trazable a documento | No | No | No | Sí |
| Explicable para quien firma | Parcial | Parcial | Parcial | Sí |
| Dice qué partida justificar | No | Parcial | Parcial | Sí |

Además, con un pozo y dos etapas cerradas no hay muestra para entrenar ni validar un modelo supervisado, y las partidas no son observaciones independientes: repartirlas al azar entre entrenamiento y prueba produciría fuga de datos (Kapoor y Narayanan, 2023).

## 2. El modelo

Es un análisis de variaciones (Datar y Rajan, 2021), adaptado al contrato con tres efectos propios. La unidad de análisis es la partida en una etapa.

Definiciones:

* `PU base`: precio del contrato. Sin anexo de precios, se deduce del VO: si el precio tiene más de dos decimales y al dividirlo entre 0.93 da dos decimales, ya trae el descuento. Si la fuente trae la marca `precio_con_descuento` (revisión del área), la marca manda.
* `VO a PU vigente`: el monto del VO escalado al precio vigente. Si la fuente trae su propio monto (redondeado a centavos) se parte de él; si no, es `q_vo × PU vigente`.
* `PU vigente = PU base × 0.93` para contratos con acuerdo referencial; igual al PU base en los demás.

Efectos, en este orden:

| Efecto | Fórmula | Se calcula cuando |
| --- | --- | --- |
| Descuento VO | `VO a PU vigente − monto VO` | La partida tiene VO y es comparable |
| Cantidad | `q_real × PU vigente − VO a PU vigente`; con montos exactos es `(q_real − q_vo) × PU vigente` | Tiene VO y ejecución |
| Precio | `importe real − q_real × PU vigente` | Tiene VO y ejecución |
| Nueva | `importe real` | Tiene ejecución y no tiene VO |
| No usada | `−VO a PU vigente` | Tiene VO, no tiene ejecución y la etapa está cerrada |

En una etapa abierta, una partida con VO y sin ejecución no es comparable todavía: queda como pendiente.

**Propiedad de aditividad.** En toda partida comparable, la suma de los cinco efectos es igual a la desviación. Se comprueba en cada corrida (`validacion.aditividad`) y con una prueba de propiedad sobre datos aleatorios.

**Regla de justificación.** Con umbral de 0%, toda partida con efecto cantidad, precio (fuera de redondeo), nueva o no usada requiere justificación. Se exceptúan el efecto descuento y el redondeo de precio, incluido el caso en que la cantidad es igual a la del VO y la diferencia es solo de centavos.

## 3. Validación

El modelo no estima, así que no se valida con error de predicción. Su equivalente es la exactitud:

| Concepto de aprendizaje automático | Equivalente en este modelo |
| --- | --- |
| MSE, RMSE, MAE | Diferencia entre el cálculo y la fuente (cuadre) |
| R² | Los efectos suman la desviación por construcción; un R² de 1 sería engañoso y no se reporta |
| Validación cruzada | Réplica en otro pozo y lector independiente de los originales |
| Prueba de robustez | Prueba de mutación |

## 4. Hoja de ruta hacia el aprendizaje automático

* **5 a 20 pozos:** detección de anomalías no supervisada (por ejemplo, isolation forest) para priorizar la revisión.
* **20 pozos o más:** modelo supervisado (random forest o gradient boosting) para estimar la desviación esperada de cada etapa antes de la cédula, con validación cruzada agrupada por pozo, RMSE y MAE en USD, y comparación contra un modelo base.

Los umbrales son orientativos. La condición es tener etiquetas confiables: justificaciones con soporte.

## Referencias

* Breiman, L. (2001). Statistical modeling: The two cultures. *Statistical Science, 16*(3), 199–215.
* Datar, S. M., y Rajan, M. V. (2021). *Horngren's cost accounting: A managerial emphasis* (17.ª ed.). Pearson.
* Kapoor, S., y Narayanan, A. (2023). Leakage and the reproducibility crisis in machine-learning-based science. *Patterns, 4*(9), 100804.
* Wang, R. Y., y Strong, D. M. (1996). Beyond accuracy: What data quality means to data consumers. *Journal of Management Information Systems, 12*(4), 5–33.
* Wickham, H. (2014). Tidy data. *Journal of Statistical Software, 59*(10), 1–23.
