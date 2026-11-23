# Datos anonimizados del Pozo A

Estos archivos contienen solo los **índices y porcentajes** publicados en el documento del caso. No hay montos absolutos, nombres de pozo, contratos ni compañías.

| Archivo | Contenido | Origen en la versión interna |
| --- | --- | --- |
| `puente_etapas_cerradas.csv` | Pasos de la cascada como índice VO programado = 100 (etapas de 30" y 20") | Comparativa VO vs SIS, hoja Resumen, filas 3 y 4 |
| `participacion_subrubro.csv` | Participación de cada subrubro en la desviación operativa de las tres etapas | Comparativa VO vs SIS, hoja Resumen por subrubro, filas de total |
| `metros_etapa_20.csv` | Metros de la partida de perforación de 20": VO, programa y perforado | Comparativa VO vs SIS, hoja Validación metros, filas 3 y 4 |
| `resumen_etapas.csv` | Desviación por etapa contra el VO y días contra programa | Comparativa VO vs SIS, hojas Resumen y Tiempos por etapa |

Con ellos se reproducen las figuras 2, 3 y 4 del documento:

```bash
costos figuras-documento --datos data/anonimizado --salida reports/figuras_documento
```

Los archivos fuente originales son confidenciales y no forman parte de este repositorio.
