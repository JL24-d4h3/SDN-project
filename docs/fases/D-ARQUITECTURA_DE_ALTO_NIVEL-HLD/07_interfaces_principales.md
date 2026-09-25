# Interfaces principales

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Cada interfaz define **qué fluye entre qué partes**, con qué sincronía y bajo qué contrato. Los protocolos concretos que no están decididos se marcan como Fase G; el único fijado hoy es el southbound (OpenFlow, por RP-11). El mapa completo de comunicación está en [`08_comunicacion.md`](08_comunicacion.md).

## 1. Registro de interfaces

| ID | Interfaz | Entre | Tipo | Sincronía |
|---|---|---|---|---|
| I1 | Southbound SDN | Controlador ↔ Switches | Protocolo de control (OpenFlow) | Mixta (petición-respuesta + asíncronos) |
| I2 | Northbound | Servicios ↔ Controlador | API del controlador | Petición-respuesta |
| I3 | Portal cautivo | Operador ↔ IAM/AAA | Interfaz web de autenticación | Petición-respuesta |
| I4 | Identidad institucional | IAM/AAA ↔ IdP (externo) | Protocolo de directorio/AAA | Petición-respuesta |
| I5 | Broker de eventos | Servicios ↔ Servicios | Publicación-suscripción | Asíncrona |
| I6 | Persistencia | Servicios ↔ Repositorios | Acceso a datos del propio servicio | Síncrona local |
| I7 | API de administración | Consola ↔ Servicios | API de la plataforma | Petición-respuesta |
| I8 | Observación del plano de datos | Monitor → Controlador → Switches | Consulta de contadores (vía I2 + I1) | Petición-respuesta periódica |

## 2. Fichas

### I1 — Southbound: Controlador ↔ Switches

- **Protocolo:** OpenFlow 1.3 sobre TCP 6653, por el canal de control out-of-band (RP-11; variante in-band en la serie de flujo, parte 2).
- **Qué fluye:** instalación y retirada de estado (FLOW_MOD, METER_MOD, GROUP_MOD), emisión de paquetes (PACKET_OUT), lectura de contadores (MULTIPART), eventos del switch (PACKET_IN, PORT_STATUS, FLOW_REMOVED), latidos (ECHO), negociación (HELLO, FEATURES).
- **Contrato:** las capacidades las declara el switch en FEATURES_REPLY; el controlador no puede ordenar más de lo declarado (P1, RP-11). Las reglas llevan cookie y timeouts para su gestión y reversión (P10).
- **Sincronía:** los comandos son petición-respuesta con `xid`; los eventos del switch son asíncronos.

### I2 — Northbound: Servicios ↔ Controlador

- **Protocolo:** API del controlador (forma concreta en Fase G; típicamente REST o similar).
- **Qué fluye:** órdenes de política —instalar/retirar reglas de acceso, de elevación y de mitigación— y consultas —topología, asociaciones host↔puerto, contadores, estado de reglas—.
- **Contrato:** la orden expresa **qué** se quiere (bloquear tráfico de X hacia Y, limitar tasa a Z); el **cómo** (FLOW_MOD concreto, prioridades, meters) es responsabilidad del controlador (P2, P8).
- **Sincronía:** petición-respuesta con confirmación de aplicación. La plataforma espera la confirmación antes de dar la acción por ejecutada.

### I3 — Portal cautivo: Operador ↔ IAM/AAA

- **Protocolo:** interfaz web de autenticación (HTTPS).
- **Qué fluye:** credenciales del operador (usuario, contraseña, MFA si aplica) y la respuesta de sesión.
- **Contrato:** el portal solo autentica **operadores privilegiados**; el usuario académico no pasa por él (RP-13). La sesión resultante habilita la elevación por el Policy Engine, no conecta nada por sí misma.
- **Sincronía:** petición-respuesta.

### I4 — Identidad institucional: IAM/AAA ↔ IdP

- **Protocolo:** diálogo AAA contra el backend de identidad (RADIUS/LDAP; producto en Fase G).
- **Qué fluye:** verificación de credenciales y atributos del operador.
- **Contrato:** el IdP es el dueño de la identidad (SE-02, fase C); el IAM/AAA la consume y no almacena credenciales. El resultado llega al Policy Engine como identidad + rol + atributos.
- **Sincronía:** petición-respuesta.

### I5 — Broker de eventos: Servicios ↔ Servicios

- **Protocolo:** publicación-suscripción con colas (producto en Fase G; patrón Broker, doc 02).
- **Qué fluye:** el catálogo de eventos (`DeviceConnected`, `AnomalyDetected`, `IncidentOpened`, `MitigationRequired`, `MitigationApplied`, `MitigationVerified`, `MitigationExpired`, `SessionOpened/Closed`, `ElevationGranted/Expired`, `DeviceRegistered/Revoked`).
- **Contrato:** cada evento declara productor, consumidores y payload (ver [`08_comunicacion.md`](08_comunicacion.md) §3). Publicar no espera al consumidor; los eventos se encolan y no se pierden ante un consumidor caído (P13).
- **Sincronía:** asíncrona, con desacoplamiento temporal.

### I6 — Persistencia: Servicios ↔ Repositorios

- **Protocolo:** acceso a datos a través del repositorio del propio servicio (patrón Repository, doc 02).
- **Qué fluye:** lectura y escritura de las entidades del dominio del servicio (incidentes, políticas, dispositivos, eventos).
- **Contrato:** **ningún servicio accede a la base de datos de otro** (doc 04). El cambio de motor de persistencia no puede afectar la lógica del servicio.
- **Sincronía:** síncrona, local al servicio.

### I7 — API de administración: Consola ↔ Servicios

- **Protocolo:** API de la plataforma (forma concreta en Fase G).
- **Qué fluye:** consultas (incidentes, políticas, dispositivos, eventos, estado) y órdenes administrativas (aprobar elevación, registrar dispositivo, modificar política).
- **Contrato:** la consola actúa con los permisos del rol de la sesión autenticada (P-catálogo); el servicio valida, no confía en la interfaz.
- **Sincronía:** petición-respuesta.

### I8 — Observación del plano de datos: Monitor → Controlador → Switches

- **Protocolo:** composición de I2 e I1: el Monitor consulta contadores al controlador, que los lee del switch con MULTIPART (`OFPMP_PORT_STATS`, `OFPMP_FLOW`).
- **Qué fluye:** contadores por puerto y por flujo, convertidos por el Monitor en métricas y línea base.
- **Contrato:** el Monitor **no habla con los switches** (P1): toda observación pasa por el controlador. La frecuencia de sondeo la define el Monitor y es configurable.
- **Sincronía:** petición-respuesta periódica (fondo).

## 3. Qué NO son interfaces de esta arquitectura

- **Conexiones directas servicio ↔ switch:** prohibidas por P1; solo el controlador habla OpenFlow.
- **Acceso de la consola a la base de datos:** prohibido por I6; todo pasa por la API.
- **Autenticación del usuario académico:** no existe interfaz para ella, por diseño (RP-13).

## 4. Cuestiones abiertas

- **Forma concreta de I2 e I7.** API REST, RPC o ambas: Fase G, con el controlador elegido.
- **Producto del broker (I5).** Broker dedicado vs colas embebidas: Fase G, contra el tamaño del prototipo.
- **Frecuencia de sondeo de I8.** Depende de los umbrales de detección que se fijen con mediciones del prototipo (Fase G).
