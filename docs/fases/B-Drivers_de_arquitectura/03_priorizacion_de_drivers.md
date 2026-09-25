# Priorización de drivers

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** B — Drivers
**Estado:** Borrador formal para revisión

---

Un **driver arquitectónico** es un requisito que condiciona decisiones de arquitectura: obliga a elegir entre alternativas estructurales y no puede satisfacerse con una decisión local. Este documento identifica los drivers del proyecto, qué decisión abre cada uno y en qué orden deben resolverse.

---

## 1. Criterio de priorización

Los drivers se ordenan aplicando cuatro criterios, en este orden:

1. **Obligatoriedad** — lo que el proyecto exige implementar (RP-01) no es negociable.
2. **Impacto arquitectónico** — cuántas decisiones estructurales dependen del driver y cuánto cuesta cambiarlo después.
3. **Riesgo** — qué ocurre si el driver no se resuelve.
4. **Verificabilidad** — si permite o no producir las métricas que el curso exige (RP-10).

**Asignación del curso:** R1 y R2 son obligatorios para todos los grupos; R4 es el requerimiento adicional asignado a este grupo. Sobre esos tres se concentra la implementación. R3 y R5 deben quedar cubiertos por la arquitectura, pero no se implementan por completo.

---

## 2. Catálogo de drivers

| ID | Driver | Origen | Decisión arquitectónica que condiciona |
|---|---|---|---|
| D-01 | Control de acceso por dispositivo, perfil y contexto | R1 | Modelo de perfiles de acceso, política contextual (identidad + atributos + contexto + vigencia), registro de dispositivos privilegiados, y punto de la red donde se aplica la decisión. |
| D-02 | Protección diferenciada de recursos | R2 | Clasificación de recursos, segmentación y asociación recurso ↔ política. |
| D-03 | Detección de ataques encubiertos internos | R3 | Ubicación y tipo de sensores, qué se observa y con qué analítica. |
| D-04 | Mitigación de DDoS y brute-force | R4 | Cadena completa de detección → incidente → política → controlador → plano de datos; mecanismos de contención (meters para rate limiting, bloqueo, aislamiento), línea base y umbrales, y recuperación con timeouts. |
| D-05 | Seguridad perimetral | R5 | Control del borde, inspección del tráfico externo y determinación de indicadores maliciosos. |
| D-06 | Traducción de decisión a regla SDN | RT-03, RT-04, RT-05, R2.10 | Arquitectura northbound y southbound: cómo una decisión de seguridad se convierte en reglas sobre los dispositivos, con las primitivas OpenFlow disponibles en PicOS (flows, meters, groups, counters). |
| D-07 | Respuesta automatizada y reversible | RT-08, RT-10, PS-07 | Bucle detección → decisión → aplicación → reversión, y dónde reside el estado temporal. |
| D-08 | Trazabilidad y auditoría | R1.9, R2.9, RNF-09, RT-07 | Modelo de eventos y registros: qué se registra, con qué identificadores y dónde se persiste. |
| D-09 | Disponibilidad del servicio legítimo | RNF-02, R4.8 | Cómo se mitiga sin cortar el tráfico legítimo y con qué tolerancia a fallo del plano de control. |
| D-10 | Latencia de las decisiones críticas | RNF-04 | Dónde se decide (controlador, dispositivo o ambos) y qué presupuesto de latencia se admite. |
| D-11 | Escalabilidad | RNF-05, R1.10, RA-08 | Límites de usuarios, sesiones y reglas; capacidad del plano de control y de las tablas de los dispositivos. |
| D-12 | Modularidad y separación de responsabilidades | RT-02, RNF-07 | Descomposición en componentes y definición de sus interfaces: qué se separa y por qué. |
| D-13 | Administración y observabilidad | RT-06, RT-09, ADM-01–05 | Interfaz de administración e información mínima para operar, supervisar y auditar. |
| D-14 | Verificabilidad y comparación de alternativas | RNF-12, RP-10, PT-07 | Qué métricas se instrumentan y cómo se comparan las alternativas de diseño. |

---

## 3. Priorización

### P0 — Obligatorio: se implementa

| Driver | Por qué |
|---|---|
| **D-01** Control de acceso por dispositivo, perfil y contexto | R1 es obligatorio para todos los grupos; su modelo (perfiles, registro de dispositivos privilegiados, elevación temporal) condiciona el resto de la arquitectura. |
| **D-02** Protección de recursos | R2 es obligatorio para todos los grupos. |
| **D-04** Mitigación de DDoS y brute-force | R4 es el requerimiento asignado a este grupo; es el caso de uso que demuestra la cadena completa de extremo a extremo. |
| **D-06** Traducción de decisión a regla SDN | Habilitante: sin él, ninguno de los tres requerimientos puede aplicarse sobre la red ni satisfacer RP-02. |
| **D-07** Respuesta automatizada y reversible | R4 exige mitigar y recuperar; sin reversión, la mitigación bloquea tráfico legítimo. |
| **D-08** Trazabilidad mínima | R1.9 y R2.9 pertenecen a requerimientos obligatorios: hay que registrar autenticación, autorización y accesos a recursos privilegiados. |
| **D-09** Disponibilidad del servicio legítimo | R4.8 es parte del requerimiento asignado. |
| **D-14** Verificabilidad y métricas | Sin métricas no hay criterios de éxito ni comparación de alternativas, que el curso exige. |

### P1 — Alta prioridad: se diseña por completo, se implementa de forma parcial

| Driver | Por qué |
|---|---|
| **D-03** Detección de ataques internos | R3 no está asignado, pero sus escenarios (scanning, spoofing) deben ser demostrables. |
| **D-05** Seguridad perimetral | R5 no está asignado: se diseña la frontera y se demuestra el bloqueo si el entorno lo permite. |
| **D-10** Latencia de las decisiones | Se mide sobre los tres requerimientos implementados; se optimiza si los resultados lo exigen. |
| **D-11** Escalabilidad | Se evalúa con carga creciente; el resultado alimenta el análisis de riesgo del controlador. |
| **D-12** Modularidad | Se materializa en la descomposición funcional y se evalúa en las fases D y E. |
| **D-13** Administración y observabilidad | Consola mínima para consultar políticas, eventos y registros. |

### P2 — Diferencial

- Umbrales dinámicos y detección adaptativa (extiende D-03 y D-04).
- Automatización de la respuesta sin intervención del Especialista de TI (extiende D-07).
- Comparación sistemática de alternativas de mitigación con resultados cuantitativos (extiende D-14).
- Implementación parcial de R3 y R5 más allá del escenario mínimo demostrable.

Los entregables del proyecto se derivan de estos niveles; esta priorización reemplaza la lista de entregables P0/P1/P2 que figuraba en el documento de requisitos.

---

## 4. Decisiones arquitectónicas que cada driver obliga a tomar

| Driver | Decisiones pendientes que activa |
|---|---|
| D-01 | perfiles de acceso; política contextual; registro de dispositivos privilegiados; portal cautivo y AAA |
| D-02 | segmentación; ubicación de los componentes de seguridad |
| D-03 | mecanismo de monitoreo; algoritmo o método de detección |
| D-04 | umbrales estáticos o dinámicos; meters nativos de PicOS o degradación por controlador; bloqueo; algoritmo de detección |
| D-05 | IDS, IPS o ambos; determinación de indicadores maliciosos |
| D-06 | controlador SDN; protocolo southbound (OpenFlow sobre PicOS, RP-11); diseño de la API northbound; virtualización o simulación |
| D-07 | estrategia de recuperación |
| D-08 | almacenamiento de logs; visualización |
| D-09 | estrategia de recuperación; tolerancia a fallo del plano de control |
| D-11 | virtualización o simulación; capacidad del entorno de pruebas |
| D-13 | visualización; almacenamiento de logs |

D-10 y D-14 no activan decisiones de esa lista: fijan criterios de diseño (presupuesto de latencia y conjunto de métricas) que las demás decisiones deben respetar.

---

## 5. Riesgos que la priorización controla

| Riesgo | Driver que lo atiende |
|---|---|
| Complejidad excesiva | La propia priorización: P0 antes que P1 y P2 |
| Bloqueo de usuarios legítimos | D-07 (reversión) y D-09 (disponibilidad) |
| Sobrecarga del controlador | D-11 y D-10, con medición en el entorno del prototipo |
| Exceso de reglas SDN | D-11, contra la capacidad del dispositivo |
| Falsos positivos | D-14, mediante tasa de detección y de falsos positivos |
| Punto único de fallo | D-09 |
| Falta de métricas | D-14, instrumentado antes de implementar |
| Falta de tiempo | La priorización P0/P1/P2 |

---

## 6. Cuestiones abiertas

- **Alcance de R3 y R5.** Definir qué se considera suficiente: ¿diseño documentado, o diseño más un escenario demostrable en el prototipo?
- **Umbrales y línea base.** Dependen de mediciones previas en el entorno del prototipo, que aún no existe.
- **Presupuesto de latencia.** RNF-04 no fija un valor; hay que establecer el límite que se considerará aceptable.
- **Capacidad de reglas.** Cuántas reglas simultáneas admite el dispositivo elegido es asunto de la Fase C y de la Fase G.
