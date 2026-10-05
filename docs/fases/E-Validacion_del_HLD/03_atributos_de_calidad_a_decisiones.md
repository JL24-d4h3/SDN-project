# Atributos de calidad → decisiones

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Los atributos de calidad de [B-01.2](../B-Drivers_de_arquitectura/01.2_RQ_transversales-de_calidad-arquitectonicos.md) (RNF-01–RNF-12), frente a la decisión arquitectónica concreta que los resuelve: los principios (D-03), el estilo (D-01), los patrones (D-02) y las decisiones del HLD (D-04–D-12). Un atributo sin decisión es un hueco; un atributo cuya comprobación depende de mediciones queda pendiente de cuantificación (P12: sin métrica no hay decisión válida).

## 1. Atributo por atributo

| Atributo | Decisión arquitectónica que lo resuelve | Dónde | Veredicto |
|---|---|---|---|
| RNF-01 Seguridad | Mínimo privilegio con denegación por defecto (P5), identidad solo para elevar (P6), MAC como atributo (P7) y modelo por capas | D-11; D-03 §3 | Cubierto |
| RNF-02 Disponibilidad | Mitigar cerca del origen sin cortar el tráfico legítimo (P9): escalera RATE_LIMIT → BLOCK → ISOLATE → QUARANTINE; el bloqueo total exige aprobación humana | D-03 §3 y §5; D-11 §4 | Cubierto (diseño); verificación con contadores |
| RNF-03 Rendimiento | El controlador no es camino del tráfico (P2): los paquetes fluyen por el plano de datos y la sobrecarga se acota por diseño | D-03 §2 | Pendiente de cuantificación (límite «experimental») |
| RNF-04 Latencia | Decisión centralizada con ejecución en el plano de datos: meters y timeouts nativos ejecutan a velocidad de línea (resolución explícita del conflicto P2 vs RNF-04) | D-03 §5 | Cubierto (diseño); medición en prototipo |
| RNF-05 Escalabilidad | Comunicación por eventos con colas que absorben ráfagas (P13); cadena de detección como pipeline; el registro solo contiene dispositivos privilegiados | D-03 §4; D-08 | Cubierto (diseño); magnitud en prototipo |
| RNF-06 Flexibilidad | Gestión centralizada de políticas (RT-01): una política se cambia en el repositorio y se aplica sin tocar los componentes | D-05 §5; D-06 §4 | Cubierto |
| RNF-07 Modularidad | Responsabilidad única (P3): diez componentes con interfaz clara, evaluables y sustituibles por separado | D-05; D-07 | Cubierto |
| RNF-08 Observabilidad | Trazabilidad y observabilidad por diseño (P11): los contadores OpenFlow son la fuente del plano de datos; monitor y consola la exponen | D-03 §4; D-05 §2, §10 | Cubierto |
| RNF-09 Trazabilidad | P11: accounting AAA, cookie por incidente y estados explícitos hasta CLOSED; cada mitigación es respondible | D-03 §4; D-05 §8 | Cubierto |
| RNF-10 Mantenibilidad | P3 + P13: añadir un consumidor de eventos no modifica a ningún productor; cada componente se verifica aislado | D-03 §2, §4 | Cubierto |
| RNF-11 Reproducibilidad | Instrumentación temprana (P12): línea base, umbrales y contadores se definen al diseñar; pruebas bajo condiciones controladas | D-03 §4 | Pendiente de cuantificación (prototipo) |
| RNF-12 Verificabilidad | P12: toda funcionalidad crítica se evalúa con métricas objetivas definidas antes de implementarla | D-03 §4; R4.10 | Cubierto (métricas definidas); valores en prototipo |

## 2. Conflictos entre atributos, ya resueltos

La precedencia está fijada en D-03 §5 y no queda a interpretación:

| Conflicto | Resolución |
|---|---|
| Decisión centralizada (P2) vs latencia (RNF-04) | La ejecución se empuja al plano de datos: meters y timeouts nativos. |
| Preservar el servicio legítimo (P9) vs automatización (P8) | Escalera de respuestas: la severidad baja se limita sola; el bloqueo total de alto impacto exige aprobación humana. |
| Métricas primero (P12) vs tiempo del curso (RP-03) | La instrumentación se acota a lo que R4.10 exige: tiempos e impacto. |
| Complejidad justificada (P4) vs comunicación por eventos (P13) | El broker se introduce como patrón, no como producto: la tecnología se elige en la Fase F contra el tamaño real del prototipo. |

## 3. Pendientes

Los cuatro pendientes de cuantificación (RNF-03, RNF-04, RNF-11, RNF-12) no son huecos de arquitectura: la decisión existe y la métrica está definida; falta el número, que produce el prototipo. Es el insumo natural de la fase de decisiones tecnológicas y del análisis experimental.
