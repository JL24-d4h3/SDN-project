# Requisitos → componentes

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Cada requisito de [B-01.1](../B-Drivers_de_arquitectura/01.1_RF_funcionales.md) (R1–R5) y [B-01.2](../B-Drivers_de_arquitectura/01.2_RQ_transversales-de_calidad-arquitectonicos.md) (RT, RNF, RA), con el componente del HLD que lo asume y dónde está descrito su mecanismo. Un requisito sin dueño es un hueco; un requisito cuyo valor concreto depende de mediciones queda marcado como pendiente de cuantificación (se cierra con el prototipo).

## 1. Requisitos funcionales

### R1 — Control de acceso según rol

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| R1.1 Identificación | Switches (MAC, puerto, switch, ubicación) · Controlador (asociación dispositivo↔ubicación) | Parte 2; D-04 §3 | Cubierto |
| R1.2 Autenticación | IAM/AAA con portal (RADIUS: IdP institucional para la comunidad; repositorio propio + TOTP para operadores) | Parte 3 §5; D-05 §6 | Cubierto |
| R1.3 Asignación de perfil | Policy Engine (BASE por defecto; ACADÉMICO o sesión de rol tras autenticación) · IAM/AAA | Parte 3 §5–6; D-05 §5–6 | Cubierto |
| R1.4 Política de acceso | Policy Engine (identidad, atributos, contexto, recurso, acción y vigencia → decisión) · Controlador (traducción a reglas) | Parte 3 §6; D-05 §5 | Cubierto |
| R1.5 Mínimo privilegio | Switches (DROP por defecto; BASE como lista cerrada) · Controlador | Parte 3 §2; D-11 §2 | Cubierto |
| R1.6 Denegación | Switches (DROP) · Controlador (regla de denegación) | Parte 3 §6; D-11 §2 | Cubierto |
| R1.7 Administración | Consola · IAM/AAA · Registro de dispositivos privilegiados | D-06 §4; D-05 §10, §6–7 | Cubierto |
| R1.8 Superusuarios | IAM/AAA (perfiles ADMIN_RED y SUPER_ADMIN, uso restringido) | D-05 §6; A-01 | Cubierto |
| R1.9 Trazabilidad | Auditoría | Parte 3 §6; D-05 §8 | Cubierto |
| R1.10 Escalabilidad | Arquitectura (registro acotado a dispositivos privilegiados; crecimiento previsto en el diseño) | D-08; parte 0 | Cubierto (magnitud en prototipo) |

### R2 — Protección de recursos privilegiados

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| R2.1 Inventario | Catálogo de recursos (fase A) como entrada del Policy Engine | A-02; D-05 §5 | Cubierto |
| R2.2 Clasificación | Catálogo con niveles general/privilegiado/crítico (fase A) | A-02 §1 | Cubierto |
| R2.3 Asociación de políticas | Policy Engine (PolicyRepository: cada recurso restringido con su política) | D-05 §5; componentes/02 | Cubierto |
| R2.4 Autorización | Policy Engine · IAM/AAA (verificación antes de permitir) | Parte 3 §6–7 | Cubierto |
| R2.5 Denegación | Switches (DROP) · Controlador | Parte 3 §6; D-11 §2 | Cubierto |
| R2.6 Segmentación | Switches (VLAN y segmentos) · Controlador | D-10; A-02 §2.3 | Cubierto |
| R2.7 Actualización | Consola · Policy Engine (políticas editables sin rediseño) | D-06 §4; access/02 | Cubierto |
| R2.8 Protección crítica | Infraestructura inaccesible desde BASE y ACADÉMICO; canal de control separado; protección por perfil | D-11 §2–3; A-02 §3 | Cubierto |
| R2.9 Auditoría | Auditoría | D-05 §8 | Cubierto |
| R2.10 Aplicación SDN | Controlador (decisión de autorización → FLOW_MOD) | Parte 3 §6; D-12 | Cubierto |

### R3 — Ataques encubiertos en la intranet

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| R3.1 Monitoreo | Monitor (counters y estadísticas del plano de datos) | Parte 1; D-05 §2 | Cubierto |
| R3.2 Scanning | Detection Engine (patrón de múltiples destinos) | D-11.1; parte 4 | Cubierto |
| R3.3 Spoofing | Controlador (MAC↔IP↔switch↔puerto; incoherencia) · Monitor y Detection Engine | Parte 3 §9; D-11 §4 | Cubierto |
| R3.4 Anomalías | Monitor (línea base) · Detection Engine (desviación) | D-05 §2–3 | Cubierto |
| R3.5 Ataques distribuidos | Detection Engine (múltiples orígenes contra un mismo destino) | Parte 4; D-11.1 | Cubierto |
| R3.6 Clasificación | Detection Engine (tipo) · Incident Manager (riesgo y registro) | D-05 §3–4 | Cubierto |
| R3.7 Mitigación | Policy Engine (decisión) · Controlador (aplicación) | Parte 4; D-05 §5 | Cubierto |
| R3.8 Acciones | Policy Engine y Controlador (bloqueo, rate limiting, aislamiento, redirección, alerta) · Switches (ejecución) | D-11 §4; parte 4 | Cubierto |
| R3.9 Recuperación | Policy Engine (TTL; retiro) · Controlador (retirada por cookie) | Parte 4; D-04 §3 | Cubierto |
| R3.10 Registro | Auditoría · Incident Manager | D-05 §4, §8 | Cubierto |

### R4 — DDoS brute-force en la intranet

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| R4.1 Línea base | Monitor (referencia por servicio protegido) | Parte 4; D-05 §2 | Cubierto |
| R4.2 Detección | Detection Engine (incremento anómalo hacia un nodo) | Parte 4; D-11 §4 | Cubierto |
| R4.3 Indicadores | Monitor (paquetes/s, solicitudes/s, conexiones/s, ancho de banda, fuentes, latencia) | Parte 1; D-05 §2 | Cubierto (valores en prototipo) |
| R4.4 Umbrales | Policy Engine (criterio cuantitativo relativo a la línea base) | Parte 4; D-12 | Cubierto (valores en prototipo) |
| R4.5 Mitigación | Policy Engine (escalera de mitigación) · Controlador | Parte 4; D-05 §5 | Cubierto |
| R4.6 Rate limiting | Controlador (METER_MOD) · Switches (meters) | Parte 4; D-12 (soporte del dispositivo: Fase F) | Cubierto |
| R4.7 Bloqueo | Controlador (FLOW_MOD) · Switches | Parte 4 | Cubierto |
| R4.8 Disponibilidad | Diseño de mitigación proporcional (rate limiting antes que bloqueo; servicio legítimo preservado) | D-11 §4; parte 4 | Cubierto (diseño) |
| R4.9 Recuperación | Policy Engine (restauración de la política normal) · Monitor (verificación) | Parte 4; D-04 §3 | Cubierto |
| R4.10 Medición | Monitor y Auditoría (tiempos de detección y mitigación, impacto) | Prototipo | Pendiente de cuantificación |

### R5 — Seguridad perimetral

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| R5.1 Perímetro | — (sin componente asignado) | C-04 §6; D-10 §6 (perímetro por definir) | **Hueco** |
| R5.2 IDS/IPS | — (evaluación tecnológica) | R5.2; fase F | **Hueco** |
| R5.3 Inspección | — | Depende de R5.1 | **Hueco** |
| R5.4 Bloqueo por IP | Controlador y Switches podrían ejecutarlo; falta el productor del evento perimetral | D-11 §4 (vía interna lista) | **Hueco** (parcial) |
| R5.5 Bloqueo hacia destinos | Ídem R5.4 | Ídem | **Hueco** (parcial) |
| R5.6 Inteligencia | — (definir cómo se determina que un indicador es malicioso) | Fase F | **Hueco** |
| R5.7 Integración SDN | Policy Engine y Controlador aceptan eventos externos como cualquier otro evento; falta la fuente | D-05 §5; D-08 | Parcial (vía lista, fuente ausente) |
| R5.8 Registro | Auditoría (receptora lista); falta la fuente | D-05 §8 | Parcial (vía lista, fuente ausente) |

## 2. Requerimientos transversales

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| RT-01 Gestión centralizada de políticas | Policy Engine (repositorio único) · Consola | D-05 §5, §10 | Cubierto |
| RT-02 Separación de responsabilidades | Los diez componentes con responsabilidades delimitadas | D-05; D-06 | Cubierto |
| RT-03 Integración SDN | Controlador · interfaces I2/I3 | D-07 | Cubierto |
| RT-04 Northbound | Controlador (API northbound de las aplicaciones); forma concreta: Fase F | D-07; access/00 | Cubierto (forma en F) |
| RT-05 Southbound | Controlador (OpenFlow hacia los switches) | D-07; D-12 | Cubierto |
| RT-06 Monitoreo | Monitor · Consola de monitoreo | D-05 §2, §10 | Cubierto |
| RT-07 Auditoría | Auditoría · almacenamiento de registros | D-05 §8 | Cubierto |
| RT-08 Respuesta automatizada | Policy Engine (condiciones → acción) · Incident Manager | Parte 4; D-05 §4–5 | Cubierto |
| RT-09 Administración | Consola · IAM/AAA (sesión de operador) | D-06 §4; access/02 | Cubierto |
| RT-10 Recuperación | Policy Engine (TTL y retiro) · Controlador | Parte 4; D-04 §3 | Cubierto |

## 3. Requerimientos de calidad

| Requisito | Cómo se resuelve | Dónde | Veredicto |
|---|---|---|---|
| RNF-01 Seguridad | Modelo por capas: mínimo privilegio, segmentación, detección y mitigación | D-11 completo | Cubierto |
| RNF-02 Disponibilidad | Mitigación proporcional; el mecanismo de seguridad no bloquea el servicio legítimo | D-11 §4 | Cubierto (diseño) |
| RNF-03 Rendimiento | Sobrecarga dentro de límites «definidos experimentalmente» | Prototipo | Pendiente de cuantificación |
| RNF-04 Latencia | Decisiones críticas con latencia compatible con la operación | Prototipo | Pendiente de cuantificación |
| RNF-05 Escalabilidad | Diseño admite crecimiento de usuarios, dispositivos, sesiones y eventos | D-08; parte 0 | Cubierto (magnitud en prototipo) |
| RNF-06 Flexibilidad | Políticas modificables sin rediseño (repositorio y consola) | D-05 §5, §10 | Cubierto |
| RNF-07 Modularidad | Diez componentes con responsabilidades e interfaces claras | D-05; D-06; D-07 | Cubierto |
| RNF-08 Observabilidad | Monitor · Consola de monitoreo · Auditoría | D-05 §2, §8, §10 | Cubierto |
| RNF-09 Trazabilidad | Auditoría (correlación usuario/evento/flujo/política) | D-05 §8 | Cubierto |
| RNF-10 Mantenibilidad | Modularidad por componentes y fases | D-05; D-06 | Cubierto |
| RNF-11 Reproducibilidad | Pruebas repetibles bajo condiciones controladas | Prototipo | Pendiente de cuantificación |
| RNF-12 Verificabilidad | Requisitos críticos comprobables con métricas objetivas | Prototipo | Pendiente de cuantificación |

## 4. Requisitos arquitectónicos

| Requisito | Cómo se resuelve | Dónde | Veredicto |
|---|---|---|---|
| RA-01 Arquitectura integral | Interacción de R1–R5 representada en el HLD y la serie de flujo | D-01–D-12; partes 0–5 | Cubierto |
| RA-02 Plano de control | Controlador SDN identificado con sus responsabilidades | D-05 §1 | Cubierto |
| RA-03 Plano de datos | Switches identificados como ejecutores | D-05 §9 | Cubierto |
| RA-04 Aplicaciones de seguridad | Módulos de política, detección, mitigación, monitoreo y administración identificados | D-05 §2–6, §8, §10 | Cubierto |
| RA-05 Flujo de información | Interfaces y comunicación entre componentes especificadas | D-07; D-08 | Cubierto |
| RA-06 Flujo de decisión | Cadena evento → detección → evaluación → decisión → política → aplicación → resultado trazable | Partes 3–4; D-08 | Cubierto |
| RA-07 Fallos | Puntos de fallo y sus efectos identificados | `04_escenarios_de_fallo.md` (esta fase) | Cubierto (en E-04) |
| RA-08 Escalabilidad evaluada | Comportamiento ante aumento de usuarios y tráfico | D-08; prototipo | Cubierto (diseño); magnitud en prototipo |
| RA-09 Protección del plano de control | Canal de control separado; acceso al controlador restringido a operadores con MFA | D-11 §3; access/02 | Cubierto |

## 5. Huecos y pendientes

**Huecos** — el bloque R5 completo: el perímetro no tiene componente asignado (R5.1–R5.6). La vía de integración hacia la red SDN ya existe (R5.7: un evento perimetral entra al Policy Engine como cualquier otro), pero falta la fuente —sistema externo con el que integrarse o componente propio— y la evaluación IDS/IPS de R5.2. Se cierra en la fase de decisiones tecnológicas.

**Pendientes de cuantificación** — se cierran con el prototipo, no con más diseño: R4.10 y RNF-03/04 (tiempos, latencia, sobrecarga), RNF-11/12 (reproducibilidad y verificación con métricas), y los valores concretos de R4.3/R4.4 y de la escalabilidad (R1.10, RA-08).
