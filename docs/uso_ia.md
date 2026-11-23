# Uso de inteligencia artificial

Se usó Claude (Anthropic, 2026, versión Opus 5.5) como asistente de programación y redacción. La IA propuso y escribió código; el equipo decidió los criterios, verificó los resultados y aprobó.

| Uso | Cómo se verificó |
| --- | --- |
| Escribir los módulos del paquete | 36 pruebas automáticas, cobertura de 98% y revisión del código |
| Proponer reglas de negocio | Cada regla la confirmó el líder del área (`docs/decisiones.md`) |
| Generar el pozo sintético | Se comprobó que reproduce los problemas de calidad del caso real |
| Redactar documentación | Revisión del equipo |

Reglas que seguimos:

* Ninguna decisión de criterio ni aprobación quedó en manos de la IA.
* Todo cálculo debe cuadrar contra la fuente; si no cuadra, el comando falla.
* Ninguna afirmación del documento va más allá de lo que los datos permiten decir.
* Ningún dato confidencial se compartió en este repositorio.
