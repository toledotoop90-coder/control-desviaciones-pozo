# Control de desviaciones de costo de un pozo exploratorio

Proyecto final de **Ciencia de Datos** · Maestría en Big data e IA · Universidad Anáhuac Puebla

Este repositorio contiene el código que reproduce el análisis del caso *Del costo programado al ejecutado*: comparar, partida por partida, lo programado en el volumen de obra (VO) contra lo ejecutado en un pozo exploratorio, y explicar cada desviación con cifras exactas y trazables.

> **Confidencialidad.** Los datos reales del pozo son confidenciales y **no** están en este repositorio. El código corre sobre un **pozo sintético** que imita la estructura del caso, y las figuras del documento se reproducen con los **índices anonimizados** que ya se publicaron en él (sin montos absolutos).

## Qué resuelve

En exploración, el costo real casi nunca coincide con la cédula autorizada, y la explicación llega tarde, en totales y sin evidencia. Este código:

1. Lee las fuentes (VO, ejecutado, programa de etapas, justificaciones y cédula) y evalúa su calidad.
2. Normaliza y valida los datos sin modificar las fuentes.
3. Divide cada desviación en cinco efectos que suman exacto.
4. Responde las cuatro preguntas de investigación con tablas y figuras.
5. Calcula la línea base de los indicadores de control.

## El modelo: análisis de variaciones por partida

La elección del modelo sale de la necesidad, no de los datos:

| Pregunta | Respuesta del caso | Consecuencia |
| --- | --- | --- |
| ¿Qué tipo de pregunta es? | Diagnóstica: explicar lo que ya pasó | Descarta como primera opción el aprendizaje supervisado (predice) y el no supervisado (agrupa) |
| ¿Se conoce la fórmula del resultado? | Sí: monto = cantidad × precio | Se calcula, no se estima |
| ¿Qué exige quien recibe el resultado? | Cuadrar al peso, trazable y explicable | Solo un modelo determinístico lo cumple |

Para cada partida en cada etapa:

```
desviación = importe ejecutado − monto VO
           = descuento VO + cantidad + precio + nuevas − no usadas
```

| Efecto | Fórmula | Quién responde |
| --- | --- | --- |
| Descuento VO | monto VO a PU vigente − monto VO | Planeación |
| Cantidad | (q real − q VO) × PU vigente | Operación |
| Precio | q real × (PU real − PU vigente) | Contratos |
| Nueva | importe de partidas sin VO en la etapa | Cambio de alcance |
| No usada | −monto VO a PU vigente de partidas sin uso (etapa cerrada) | Planeación |

La **desviación operativa** es la total menos el efecto descuento, porque ese efecto es un error del VO y no algo que pasó en el pozo. Como el modelo no estima parámetros, **MSE y R² no aplican**: se valida por exactitud (cuadre y aditividad). Detalle en [`docs/metodologia.md`](docs/metodologia.md).

## Las seis fases en el código

| Fase | Qué se hace | Dónde está |
| --- | --- | --- |
| Ask | Problema, cinco porqués y preguntas de investigación | Documento del caso y [`notebooks/analisis_seis_fases.ipynb`](notebooks/analisis_seis_fases.ipynb) |
| Prepare | Lectura con esquema y evaluación de calidad (Wang y Strong, 1996) | [`io.py`](src/costos/io.py), [`calidad.py`](src/costos/calidad.py) |
| Process | Normalización, duplicados, precios vigentes y validación | [`normalizar.py`](src/costos/normalizar.py), [`validacion.py`](src/costos/validacion.py) |
| Analyze | Modelo de cinco efectos, resúmenes, puente y participación | [`modelo.py`](src/costos/modelo.py) |
| Share | Cascada, Pareto y caso de metros | [`visualizacion.py`](src/costos/visualizacion.py) |
| Act | Línea base de los indicadores | [`indicadores.py`](src/costos/indicadores.py) |

## Estructura

```
control-desviaciones-pozo/
├── src/costos/            Paquete del análisis
│   ├── config.py          Reglas de negocio (descuento, tolerancias, umbral)
│   ├── io.py              Lectura de fuentes y verificación de esquema
│   ├── calidad.py         Reglas de calidad de datos
│   ├── normalizar.py      Limpieza, claves como texto, precio base y vigente
│   ├── modelo.py          Análisis de variaciones en cinco efectos
│   ├── validacion.py      Cuadre, conservación y aditividad
│   ├── visualizacion.py   Figuras
│   ├── indicadores.py     Indicadores de control
│   ├── pipeline.py        Orquestación de las fases
│   ├── sintetico.py       Generador del pozo sintético
│   └── cli.py             Línea de comandos `costos`
├── data/
│   ├── sintetico/         Pozo de demostración (generado, valores inventados)
│   └── anonimizado/       Índices publicados en el documento del caso
├── notebooks/             Notebook ejecutado con las seis fases
├── tests/                 Pruebas automáticas (pytest)
├── docs/                  Metodología, diccionario de datos, decisiones y uso de IA
└── .github/workflows/     Integración continua
```

## Instalación

Requiere Python 3.10 o superior. Para obtener el código, use `git clone https://github.com/toledotoop90-coder/control-desviaciones-pozo` o, sin git, el botón verde **Code → Download ZIP** de esta página, y abra una terminal dentro de la carpeta.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Si PowerShell responde que la ejecución de scripts está deshabilitada, corra antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (solo afecta esa ventana) o use `cmd` con `.venv\Scripts\activate.bat`.

**macOS o Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Solo para correr el análisis, sin herramientas de desarrollo: `pip install -r requirements.txt` y luego `pip install -e .`

## Uso

```bash
costos generar-sintetico --salida data/sintetico
costos ejecutar --datos data/sintetico --salida reports/sintetico
costos figuras-documento --datos data/anonimizado --salida reports/figuras_documento
```

`costos ejecutar` escribe en la carpeta de salida:

| Archivo | Contenido |
| --- | --- |
| `calidad.csv` | Hallazgos de calidad con su categoría y tratamiento |
| `comparativa_partidas.csv` | Una fila por partida y etapa con los cinco efectos y si requiere justificación |
| `resumen_etapa.csv`, `resumen_subrubro.csv` | Agregados con porcentaje contra el VO |
| `puente.csv` | Pasos de la cascada como índice VO = 100 |
| `validacion.csv` | Pruebas de validación (OK o FALLA) |
| `indicadores.csv` | Línea base de los indicadores |
| `huellas_fuentes.csv` | Huella SHA-256 de cada archivo fuente |
| `figuras/` | Cascada, Pareto y metros en PNG |
| `resumen.md` | Resumen en texto |

Si alguna validación falla, el comando termina con código 1 y lo avisa.

**Resultado esperado con el pozo sintético:** 28 partidas, 23 a justificar, 6 hallazgos de calidad y 5 de 5 validaciones correctas. En las etapas cerradas, la desviación es −29.6% contra el VO, de la cual −5.9 puntos son descuento no aplicado.

## Pruebas

```bash
pytest --cov=costos      # 34 pruebas, cobertura de 97%
ruff check src tests     # estilo y errores comunes
```

Las pruebas cubren el ejemplo numérico del documento, una prueba de propiedad (los efectos suman la desviación en 300 partidas aleatorias), los casos de etapa abierta, partida nueva y no usada, la detección de los problemas de calidad sembrados, una **prueba de mutación** (si se altera un efecto en 1 USD, la validación falla), la reproducibilidad del análisis y la consistencia de los índices anonimizados con las cifras del documento.

## Verificación con los datos originales del caso

Los datos del Pozo A son confidenciales y no están en este repositorio. Para comprobar que el paquete reproduce el documento, se corrió en un equipo del área con las fuentes originales convertidas a este formato (sin publicarlas). Resultado:

| Cifra del documento | Análisis interno | Este paquete |
| --- | --- | --- |
| Puente de etapas cerradas (VO = 100) | −5.423, −8.308, −10.927, +2.244, −0.0002 → 77.6 | Igual |
| Desviación total y operativa por etapa (%) | 30": −32.8 / −27.1; 20": −21.0 / −15.6; 16": −2.5 / −0.8 | Igual |
| Partidas a justificar | 13, 28 y 22 (63 en total) | Igual |
| Participación por subrubro (%) | 63.7, 25.5, 9.0, 2.2, 0.3 | Igual |
| Partidas comparadas | 90 | 90; diferencia máxima por partida de medio centavo |
| Validaciones | | 5 de 5 correctas, cuadre contra el VO al centavo |

La primera corrida mostró tres diferencias pequeñas (redondeo de montos, un precio de 0.93 que ya traía descuento y un caso de punto flotante). Se corrigieron en la versión 1.1.0; el detalle está en [`CHANGELOG.md`](CHANGELOG.md).

## Reproducibilidad

* La misma entrada produce la misma salida: el modelo no tiene componentes aleatorios.
* El pozo sintético se genera de forma determinística.
* Cada corrida guarda la huella SHA-256 de las fuentes.
* La integración continua corre las pruebas, el análisis completo y el notebook en Windows, macOS y Linux, con Python 3.10, 3.12 y 3.14, en cada cambio.

## Uso de inteligencia artificial

El código se desarrolló con apoyo de Claude (Anthropic). Las reglas de negocio las confirmó el líder del área y cada resultado se verificó contra las fuentes. Detalle en [`docs/uso_ia.md`](docs/uso_ia.md).

## Limitaciones

* Un solo pozo real y dos etapas cerradas: es un estudio de caso.
* El precio base se deduce del VO porque no se cuenta con el anexo de precios del contrato.
* El modelo atribuye montos; la causa de cada desviación la documenta el ingeniero con su soporte.
* La versión interna, con lectores de los formatos institucionales y la aplicación para los ingenieros, no se publica.

## Cómo citar

Ver [`CITATION.cff`](CITATION.cff).

## Licencia

MIT. Ver [`LICENSE`](LICENSE).
