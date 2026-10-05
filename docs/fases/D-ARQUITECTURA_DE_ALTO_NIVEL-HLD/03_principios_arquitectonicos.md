# Principios arquitectónicos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

## 1. Naturaleza y uso

Un **principio arquitectónico** es una regla de diseño de cumplimiento obligatorio, derivada de los requerimientos y restricciones del proyecto, con la que se juzga cada decisión de arquitectura. No describe *cómo* se organiza el sistema (eso es el estilo, [`01_estilo(s)_arquitectonico(s).md`](01_estilo(s)_arquitectonico(s).md)) ni *cómo* se resuelve un problema local (eso son los patrones, [`02_patrones_arquitectonicos.md`](02_patrones_arquitectonicos.md)): establece **qué decisiones son aceptables y cuáles no**.

Cada principio se define con tres elementos:

- **Enunciado:** la regla, en una frase.
- **Origen:** los requerimientos, restricciones o drivers de los que deriva — ningún principio se inventa.
- **Implicaciones:** qué obliga en el diseño concreto de esta solución.

Los principios se agrupan en estructurales, de seguridad y operacionales. Toda decisión de los documentos siguientes del HLD se justifica contra ellos; cuando dos principios tiran en direcciones opuestas, la sección 5 fija el orden de precedencia.

---

## 2. Principios estructurales

### P1 — Separación de planos

**Enunciado:** toda decisión de seguridad nace en el plano de control y se ejecuta en el plano de datos; la red no se administra dispositivo por dispositivo.

**Origen:** RP-02, RA-02, RA-03, RT-03, RT-05.

**Implicaciones**

- Cualquier cambio de política de acceso o de mitigación se materializa como mensajes southbound (FLOW_MOD, METER_MOD, GROUP_MOD), nunca como configuración manual sobre un switch.
- El plano de datos no decide: ejecuta lo instalado y reporta (PACKET_IN, PORT_STATUS, FLOW_REMOVED, contadores).
- Las capacidades reales del switch limitan el diseño: nada puede asumirse sin verificarlo contra PicOS (RP-11).

### P2 — Decisión centralizada, ejecución distribuida

**Enunciado:** el controlador decide una vez; los switches ejecutan en todos los puntos donde la decisión deba aplicarse.

**Origen:** D-06, R2.10, RT-03, RT-04, RNF-04.

**Implicaciones**

- Una mitigación que afecta a varios orígenes se instala **en cada switch de ingreso correspondiente**, no en un único punto central.
- El controlador nunca es el camino del tráfico: los paquetes fluyen por el plano de datos; el controlador solo procesa novedades.
- La latencia de las decisiones críticas (RNF-04) se resuelve empujando la ejecución al plano de datos — meters y timeouts nativos — no acelerando al controlador.

### P3 — Responsabilidad única de los componentes

**Enunciado:** cada componente de la plataforma tiene una responsabilidad delimitada, una interfaz clara y puede evaluarse por separado.

**Origen:** RT-02, RNF-07, D-12, RA-04.

**Implicaciones**

- La cadena de R4 respeta la división: monitor observa, detector clasifica, incidentes gestiona, política decide, controlador traduce, switch ejecuta, auditoría registra. Ningún componente asume la tarea del siguiente.
- Cada componente es sustituible y verificable aislado (patrón Pipe-and-Filter en la detección).
- La separación entre identidad, autorización, detección, mitigación, monitoreo y administración es explícita en la descomposición ([`04_descomposición_arquitectónica.md`](04_descomposición_arquitectónica.md)).

### P4 — Complejidad justificada

**Enunciado:** ninguna tecnología, componente o mecanismo se incorpora si no responde a una necesidad concreta y evaluable del proyecto.

**Origen:** RP-07, RP-09.

**Implicaciones**

- Patrones descartados por no responder a una necesidad real (CQRS, Master-Slave como patrón global — ver [`02_patrones_arquitectonicos.md`](02_patrones_arquitectonicos.md)).
- El número de microservicios lo define la necesidad, no el catálogo: cada frontera de servicio debe poder justificarse contra un requerimiento.
- Las primitivas OpenFlow que se usan son exactamente las que los escenarios exigen (groups para inundación, meters para rate limiting, contadores para monitoreo); el resto se deja declarado y sin usar.

---

## 3. Principios de seguridad

### P5 — Mínimo privilegio con denegación por defecto

**Enunciado:** todo dispositivo conectado recibe el perfil mínimo; lo que no esté explícitamente permitido queda denegado.

**Origen:** R1.5, R1.6, R2.5.

**Implicaciones**

- El perfil BASE permite solo DHCP, DNS y el portal; todo acceso a infraestructura tiene una entrada DROP por defecto con prioridad sobre el forwarding.
- La regla del registro de dispositivos privilegiados es inversa a un catálogo total: **no match → BASE**. La población académica no requiere alta alguna.
- Ningún rol hereda permisos por acumulación: cada permiso se concede explícitamente.

### P6 — La identidad se exige solo para elevar privilegios

**Enunciado:** la presencia física confiere el perfil mínimo; cualquier privilegio superior exige autenticación y autorización con contexto y vigencia.

**Origen:** RP-13, R1.2, R1.3.

**Implicaciones**

- La comunidad se autentica en el portal contra el IdP institucional (perfil ACADÉMICO); los operadores, contra el repositorio propio con MFA (sesión de rol).
- La elevación se decide en el Policy Engine con identidad + dispositivo registrado + contexto + vigencia; la presencia física jamás justifica privilegios.
- La cadena de confianza es explícita: sin presencia → sin acceso; presencia → BASE; registro + login → identidad; política contextual → privilegios con TTL o sesión.

### P7 — La MAC es atributo, no credencial

**Enunciado:** la identidad de un dispositivo no se confía por su MAC; se observa, se asocia y se detecta su incoherencia.

**Origen:** R3.3, modelo de actores (fase A), flujo de autenticación (parte 3 de la serie de flujo).

**Implicaciones**

- La coincidencia con el registro de dispositivos privilegiados **habilita** el intento de elevación, nunca lo concede.
- La incoherencia (misma MAC en otro puerto, MAC con otra IP o con otra identidad) produce eventos MAC_MOVE con respuesta escalonada: alerta → bloqueo → cuarentena.
- Los mecanismos de puerto (port security, 802.1X) se reservan para puertos sensibles; ninguno sustituye a la identidad de la persona.

### P8 — El detector observa; la política decide; la red ejecuta

**Enunciado:** la detección, la decisión de respuesta y la ejecución son responsabilidades de componentes distintos, enlazados por una cadena trazable.

**Origen:** R3.7, R4.5, RT-08, RA-06, D-04.

**Implicaciones**

- El Detection Engine **nunca instala reglas**: produce eventos. Toda respuesta pasa por Incidente → Policy Engine → Controlador → Switch.
- La cadena completa debe poder trazarse como **evento → detección → evaluación → decisión → política → aplicación → resultado** (RA-06).
- La automatización (RT-08) se aplica a las decisiones del Policy Engine, no a saltos directos entre detección y red.

### P9 — Mitigar cerca del origen sin cortar el tráfico legítimo

**Enunciado:** la contención se aplica en el punto de ingreso del tráfico malicioso y debe preservar el servicio legítimo.

**Origen:** R4.8, RNF-02, D-09.

**Implicaciones**

- La regla de mitigación se instala en el switch de ingreso del origen, no junto a la víctima: el tráfico malicioso se descarta antes de atravesar la red.
- La escalera de respuestas (RATE_LIMIT → BLOCK → ISOLATE → QUARANTINE) elige la mínima intervención suficiente; el meter limita antes que el DROP total.
- Ninguna mitigación se da por buena sin verificación con contadores: si el tráfico legítimo no se recupera, la respuesta se ajusta.

---

## 4. Principios operacionales

### P10 — Todo privilegio y toda mitigación es temporal y reversible

**Enunciado:** ningún permiso excepcional ni regla de mitigación permanece por defecto: expira, se retira y la política original se restaura.

**Origen:** RT-10, R3.9, R4.9, D-07.

**Implicaciones**

- Elevaciones con TTL y sesiones con idle_timeout: el estado BASE es el punto de retorno obligatorio.
- Reglas de mitigación con hard_timeout/idle_timeout y cookie por incidente, retiradas con FLOW_MOD DELETE; FLOW_REMOVED informa la expiración.
- El incidente recorre estados explícitos hasta CLOSED; una mitigación sin cierre es un defecto, no un estado válido.

### P11 — Trazabilidad y observabilidad por diseño

**Enunciado:** toda decisión y acción relevante queda registrada y asociable a quién, qué, cuándo y por qué; la red expone la información necesaria para supervisarla.

**Origen:** R1.9, R2.9, RNF-08, RNF-09, RT-06, RT-07, D-08.

**Implicaciones**

- Los contadores OpenFlow son la única fuente de observación del plano de datos; el monitor los lee periódicamente y construye la línea base.
- El accounting AAA registra las acciones de los operadores; el registro de dispositivos privilegiados guarda la auditoría de altas (quién registró qué, cuándo).
- Cada cambio de política y cada mitigación es respondible: qué regla, en qué switch, originada por qué incidente o decisión, y cuándo se retiró.

### P12 — Sin métrica no hay decisión válida

**Enunciado:** toda funcionalidad crítica se evalúa con métricas objetivas definidas antes de implementarla; una alternativa sin medición no es una alternativa.

**Origen:** RP-10, RNF-12, R4.10, D-14.

**Implicaciones**

- Instrumentación temprana: línea base, umbrales y contadores se definen al diseñar, no al terminar.
- Toda elección entre alternativas de diseño (p. ej. group ALL vs PACKET_OUT, meters nativos vs degradación por controlador) se decide con resultados cuantitativos del prototipo.
- Los tiempos de detección, mitigación e impacto sobre el servicio de R4.10 se miden y se reportan.

### P13 — Comunicación por eventos entre componentes de seguridad

**Enunciado:** los componentes internos de la plataforma se comunican por eventos a través de un intermediario; las peticiones síncronas quedan confinadas al borde.

**Origen:** estilos (doc 01), patrones (doc 02), RT-08, RA-05, RA-06.

**Implicaciones**

- El catálogo de eventos (`DeviceConnected`, `AnomalyDetected`, `IncidentOpened`, `MitigationRequired`, …) es el contrato entre componentes; añadir un consumidor no modifica a ningún productor.
- Las ráfagas de eventos de un ataque se absorben en colas: el detector publica y sigue observando, sin esperar al consumidor.
- Las consultas administrativas (consolas, APIs) siguen siendo petición-respuesta directa: el broker transporta eventos y órdenes, no preguntas.

---

## 5. Conflictos entre principios

Cuando dos principios tiran en direcciones opuestas, la resolución es explícita y se documenta:

| Conflicto | Resolución |
|---|---|
| **P2** (decisión centralizada) vs **RNF-04** (latencia) | La ejecución se empuja al plano de datos: meters y timeouts nativos. El controlador decide en el plano de control; el switch aplica a velocidad de línea. |
| **P9** (preservar el tráfico legítimo) vs **P8** (automatización) | La escalera de respuestas resuelve: la severidad baja se limita (RATE_LIMIT) sin intervención; el bloqueo total de alto impacto exige aprobación humana. |
| **P12** (métricas primero) vs **RP-03** (tiempo del curso) | La instrumentación se acota a lo que R4.10 y RP-10 exigen: tiempos e impacto, no una plataforma de telemetría completa. |
| **P4** (complejidad justificada) vs **P13** (comunicación por eventos) | El broker se introduce como patrón, no como producto: la tecnología se elige en la Fase F contra el tamaño real del prototipo, no contra un despliegue de producción. |

---

## 6. Trazabilidad

| Principio | Origen directo |
|---|---|
| P1 Separación de planos | RP-02, RA-02, RA-03, RT-03, RT-05 |
| P2 Decisión centralizada, ejecución distribuida | D-06, R2.10, RT-03, RT-04, RNF-04 |
| P3 Responsabilidad única | RT-02, RNF-07, D-12, RA-04 |
| P4 Complejidad justificada | RP-07, RP-09 |
| P5 Mínimo privilegio | R1.5, R1.6, R2.5 |
| P6 Identidad solo para elevar | RP-13, R1.2, R1.3 |
| P7 MAC como atributo | R3.3, fase A (actores) |
| P8 Detectar / decidir / ejecutar | R3.7, R4.5, RT-08, RA-06, D-04 |
| P9 Mitigar cerca del origen | R4.8, RNF-02, D-09 |
| P10 Temporalidad y reversibilidad | RT-10, R3.9, R4.9, D-07 |
| P11 Trazabilidad y observabilidad | R1.9, R2.9, RNF-08, RNF-09, RT-06, RT-07, D-08 |
| P12 Métricas objetivas | RP-10, RNF-12, R4.10, D-14 |
| P13 Comunicación por eventos | Estilos (01), Patrones (02), RT-08, RA-05, RA-06 |

---

## 7. Cuestiones abiertas

- **Frontera síncrono/asíncrono.** Qué interacciones internas quedan fuera del broker y por qué: se fija en [`08_comunicacion.md`](08_comunicacion.md).
- **Precedencia entre P9 y P12 en caso extremo.** Si una mitigación que preserva el servicio legítimo no alcanza las métricas exigidas, decidir si prima la disponibilidad (P9) o el resultado medido (P12); depende de los umbrales que se fijen en la Fase F.
