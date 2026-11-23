# Diccionario de datos

## Fuentes de entrada (`data/sintetico/`)

### `vo.csv`: volumen de obra validado

| Columna | Tipo | Descripción |
| --- | --- | --- |
| `pozo` | texto | Identificador del pozo |
| `etapa` | texto | Etapa del pozo |
| `partida` | texto | Clave del catálogo de servicios; siempre texto |
| `descripcion` | texto | Descripción de la partida |
| `unidad` | texto | Unidad de medida |
| `contrato` | texto | Contrato; A y B tienen descuento contractual |
| `subrubro` | texto | Capítulo del catálogo |
| `cantidad` | número | Cantidad programada |
| `pu` | número | Precio unitario del VO |

### `ejecutado.csv`

Mismas columnas que `vo.csv` más `fuente`: `empleado` (cantidad real de campo, etapas cerradas) o `solicitado` (etapas abiertas).

### `etapas.csv`

| Columna | Tipo | Descripción |
| --- | --- | --- |
| `etapa`, `nombre` | texto | Identificador y nombre |
| `estado` | texto | `cerrada` o `abierta` |
| `prof_inicio`, `prof_fin` | número | Intervalo del programa (m) |
| `dias_programa`, `dias_real` | número | Duración programada y real |

### `justificaciones.csv`

| Columna | Descripción |
| --- | --- |
| `etapa`, `partida` | Partida justificada |
| `causa`, `subcausa` | Catálogo de causas |
| `justificacion` | Explicación del ingeniero |
| `tipo_soporte`, `folio_soporte` | Documento soporte; es válido si el tipo es reconocido y tiene folio |

### `cedula.json`

`pozo`, `total_vo` (para el cuadre), `moneda` y `clase`.

## Salida principal: `comparativa_partidas.csv`

| Columna | Descripción |
| --- | --- |
| `estado_etapa`, `comparable` | Si la partida entra en la comparación |
| `q_vo`, `pu_vo`, `monto_vo` | Lo programado |
| `monto_vo_comparable` | Monto VO que entra en la comparación |
| `q_real`, `pu_real`, `importe_real` | Lo ejecutado |
| `pu_vigente` | PU base × 0.93 en contratos con descuento |
| `efecto_descuento`, `efecto_cantidad`, `efecto_precio`, `partida_nueva`, `partida_no_usada` | Los cinco efectos |
| `desviacion` | Importe real − monto VO comparable |
| `desviacion_operativa` | Desviación − efecto descuento |
| `requiere_justificacion`, `motivo`, `efecto_dominante` | Regla de justificación |
