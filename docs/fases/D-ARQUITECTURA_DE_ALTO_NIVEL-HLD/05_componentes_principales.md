# Componentes principales

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Descripción detallada de cada componente de la descomposición ([`04_descomposición_arquitectonica.md`](04_descomposición_arquitectonica.md)): qué hace, qué recibe, qué produce, qué estado mantiene y qué mecanismos usa internamente. Las responsabilidades formales (qué sí y qué no) están en [`06_responsabilidades.md`](06_responsabilidades.md).

## 1. Controlador SDN

**Propósito:** traducir las decisiones de la plataforma a reglas del plano de datos y mantener el conocimiento de la red.

- **Entradas:** órdenes de política (instalar/retirar reglas, consultar estado); mensajes OpenFlow de los switches (PACKET_IN, PORT_STATUS, FLOW_REMOVED, FEATURES_REPLY).
- **Salidas:** mensajes OpenFlow (FLOW_MOD, METER_MOD, GROUP_MOD, PACKET_OUT, MULTIPART); topología y estado a la plataforma.
- **Estado:** grafo de topología (switches, enlaces, atributos), **inventario de servicios** (los anclajes declarados: servicio, IP, switch y puerto), asociaciones host ↔ MAC ↔ IP ↔ switch ↔ puerto, inventario de reglas instaladas (con sus cookies), capacidades declaradas por cada switch.
- **Mecanismos internos:** descubrimiento LLDP (inyección por PACKET_OUT y deducción de enlaces por cruce de metadatos); cálculo de caminos por destino sobre el grafo e instalación **proactiva** hacia los servicios declarados, además de la instalación reactiva ante PACKET_IN (FLOW_MOD + PACKET_OUT); respuesta ARP desde sus asociaciones; retirada de reglas por cookie; lectura de contadores por MULTIPART. Detalle completo en la serie de flujo (partes 1, 2 y 5).

## 2. Monitor

**Propósito:** observar el plano de datos y construir la línea base sobre la que se detecta.

- **Entradas:** contadores OpenFlow (por puerto y por flujo), leídos periódicamente a través del controlador; eventos de mitigación aplicada (para verificar).
- **Salidas:** métricas normalizadas (tasas por destino, por origen, nº de fuentes); eventos `MitigationVerified` / `MitigationExpired`.
- **Estado:** series temporales de contadores, línea base por destino protegido.
- **Mecanismos internos:** sondeo periódico (MULTIPART `OFPMP_PORT_STATS` / `OFPMP_FLOW`); normalización a tasas (pps, bps) por ventana temporal; comparación contra línea base para emitir materia prima de detección.

## 3. Detection Engine

**Propósito:** decidir si existe comportamiento anómalo y clasificarlo.

- **Entradas:** métricas normalizadas del Monitor (por el broker).
- **Salidas:** evento `AnomalyDetected` con tipo, destino, fuentes, tasas y desviación.
- **Estado:** umbrales y reglas de clasificación.
- **Mecanismos internos:** cadena Pipe-and-Filter — captura → normalización → extracción de features → comparación contra umbrales y línea base → clasificación (flood volumétrico vs brute-force de solicitudes) → emisión del evento. Nunca instala reglas (P8).

## 4. Incident Manager

**Propósito:** registrar cada incidente y gestionar su ciclo de vida.

- **Entradas:** `AnomalyDetected`; resultados de verificación (`MitigationVerified` / `MitigationExpired`).
- **Salidas:** `IncidentOpened`, `IncidentClosed`; consultas de la consola (estado del incidente).
- **Estado:** `IncidentRepository`: por incidente, tipo, objetivo, orígenes, severidad, estados (DETECTED → MITIGATING → MITIGATED → RECOVERED → CLOSED) y acciones asociadas.
- **Mecanismos internos:** correlación de anomalías con incidentes existentes (evitar duplicados); transición de estados según eventos recibidos; exposición del historial para auditoría.

## 5. Policy Engine

**Propósito:** decidir la respuesta ante incidentes y la concesión de elevaciones.

- **Entradas:** `IncidentOpened` (con severidad y contexto); `ElevationRequested` (solicitud aprobada por el Administrador de Red); consultas del IAM/AAA (perfil de una sesión).
- **Salidas:** `MitigationRequired` (comando al controlador vía northbound); `ElevationGranted` / `ElevationExpired`.
- **Estado:** `PolicyRepository` (políticas de acceso y de mitigación), `PermissionRepository` (permisos y vigencia de las elevaciones).
- **Mecanismos internos:** evaluación de condiciones ABAC-like — identidad + dispositivo + ubicación + contexto + recurso + acción + vigencia — para permitir/denegar; escalera de respuestas por severidad (RATE_LIMIT → BLOCK_SOURCE → ISOLATE_DEVICE → QUARANTINE); programación de expiraciones (TTL) para elevaciones y mitigaciones.

## 6. IAM/AAA (con portal cautivo)

**Propósito:** autenticar a las poblaciones (la comunidad contra el IdP; los operadores contra su repositorio propio) y autorizar sus sesiones.

- **Entradas:** credenciales de la población (portal cautivo o acceso remoto); atributos del IdP institucional para la comunidad; código TOTP para operadores.
- **Salidas:** identidad autenticada + perfil o rol al Policy Engine; `SessionOpened` / `SessionClosed`; registros de accounting.
- **Estado:** identidades privilegiadas con sus credenciales propias y su segundo factor, sesiones activas y su vigencia. No almacena credenciales de la comunidad: las valida el IdP; el servicio AAA no las guarda.
- **Mecanismos internos:** diálogo RADIUS (Authentication, Authorization, Accounting): contra el IdP para la comunidad, y contra el repositorio propio con TOTP para los operadores; gestión del ciclo de sesión (login → perfil ACADÉMICO o sesión de rol → logout/inactividad → retorno a BASE, vía idle_timeout).

## 7. Registro de dispositivos privilegiados

**Propósito:** mantener el catálogo de dispositivos de los operadores y su auditoría.

- **Entradas:** altas, modificaciones y bajas ordenadas por el Administrador de Red o el Superadministrador (P30).
- **Salidas:** consultas de pertenencia al Policy Engine (¿este dispositivo está registrado y para qué rol?); historial de cambios para auditoría.
- **Estado:** `DeviceRepository`: MAC, tipo, titular, rol asociado, vigencia, responsable del registro.
- **Mecanismos internos:** regla inversa — todo lo que **no** hace match queda fuera del registro y recibe perfil BASE; el match solo habilita el intento de elevación (P7). Los dispositivos académicos no se registran.

## 8. Auditoría

**Propósito:** registrar toda decisión y acción relevante para responder quién, qué, cuándo y por qué.

- **Entradas:** todos los eventos del catálogo (suscripta al broker); acciones administrativas (quién registró qué dispositivo, quién aprobó qué elevación).
- **Salidas:** consultas de la consola para operadores autorizados (P25).
- **Estado:** `AuditRepository` (eventos, acciones, cambios de política, mitigaciones con su origen y su retirada).
- **Mecanismos internos:** consumo pasivo del broker — nunca participa en la cadena de decisión (P11); asociación de cada acción con el incidente, la política o el operador que la originó (RNF-09).

## 9. Switches (plano de datos)

**Propósito:** ejecutar las reglas instaladas y reportar.

- **Entradas:** mensajes del controlador (FLOW_MOD, METER_MOD, GROUP_MOD, PACKET_OUT, MULTIPART).
- **Salidas:** PACKET_IN, PORT_STATUS, FLOW_REMOVED, contadores, tráfico reenviado.
- **Estado:** pipeline de tablas de flujo, group table, meter table, contadores, búfer de paquetes (anatomía: serie de flujo, parte 0).
- **Mecanismos internos:** evaluación por prioridad de las entradas; ejecución de instrucciones (output, drop, meter, group); expiración por hard/idle_timeout; captura por table-miss y por regla explícita (OFPR_NO_MATCH / OFPR_ACTION).

## 10. Consola de administración

**Propósito:** interfaz de operación de la plataforma para los operadores.

- **Entradas:** acciones del operador autenticado.
- **Salidas:** peticiones a los servicios (consultas, aprobaciones, altas, cambios de política).
- **Estado:** ninguno propio: es un cliente (cliente-servidor, doc 01).
- **Mecanismos internos:** renderiza estado consultado; aplica los permisos del rol de la sesión (P-catálogo, fase A).

## 11. Qué no es un componente de esta lista

- **El IdP institucional** es un sistema externo (SE-02, fase C): se consulta, no se administra.
- **Los hosts y servidores protegidos** son activos protegidos, no componentes de la plataforma.
- **El firewall perimetral** queda por definir (R5 no está asignado a este grupo; fase C).
