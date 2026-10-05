# Comunicación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Cómo se comunican las partes del sistema: los tres canales que existen, la frontera entre lo síncrono y lo asíncrono (P13), el catálogo de eventos con sus payloads y la matriz completa de interacciones. Las interfaces formales están en [`07_interfaces_principales.md`](07_interfaces_principales.md).

## 1. Los tres canales

```text
┌─────────────────────────────────────────────────────────────────┐
│  BORDE EXTERNO (cliente-servidor)                               │
│  consola ──► API ──► servicios      portal ──► IAM/AAA           │
│  IdP ◄──► IAM/AAA                                                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│  BUS INTERNO DE LA PLATAFORMA                                   │
│  eventos (broker, asíncrono)  +  órdenes northbound (síncrono)  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│  CANAL DE CONTROL SDN (OpenFlow, out-of-band)                   │
│  controlador ◄──► switches                                      │
└─────────────────────────────────────────────────────────────────┘
```

- **Borde externo:** actores humanos y sistemas externos; siempre petición-respuesta.
- **Bus interno:** los servicios entre sí; dominan los eventos, con una excepción síncrona —las órdenes de Políticas al Controlador—.
- **Canal SDN:** protocolo de control con el plano de datos; comandos con confirmación y eventos asíncronos del switch.

## 2. La frontera síncrono/asíncrono

La regla (P13): **los eventos y las órdenes de reacción son asíncronos o de comando; las consultas son síncronas.** Criterios de decisión por interacción:

| Interacción | Sincronía | Por qué |
|---|---|---|
| Publicación de un evento (detección, incidente, verificación) | Asíncrona (broker) | El productor no espera ni conoce a los consumidores (P13); ráfagas del ataque se absorben en colas. |
| Orden de mitigación (Políticas → Controlador) | Síncrona (northbound) | La plataforma debe saber que la regla **se aplicó** antes de dar la acción por ejecutada (I2). |
| Instalación de reglas (Controlador → Switch) | Comando con confirmación | OpenFlow es petición-respuesta con `xid`; el resultado se confirma. |
| Consultas de consola (incidentes, políticas, dispositivos) | Síncrona (API) | El operador espera una respuesta; encolar preguntas no aporta nada (P4). |
| Login en el portal (IAM → IdP para la comunidad; repositorio propio + TOTP para operadores) | Síncrona | La persona espera el resultado de su autenticación. |
| Lectura de contadores (Monitor → Controlador → Switch) | Síncrona periódica | Sondeo con respuesta; no es un evento. |

El broker transporta **eventos y órdenes de reacción**, nunca preguntas (doc 02).

## 3. Catálogo de eventos

Cada evento declara productor, consumidores y payload mínimo. El catálogo es el contrato entre servicios (P13, doc 04).

| Evento | Productor | Consumidores | Payload mínimo |
|---|---|---|---|
| `DeviceConnected` | Controlador (primer PACKET_IN) | Registro, Monitor, Auditoría | MAC, IP, DPID, puerto, instante |
| `MAC_Moved` | Monitor | Incidentes, Políticas, Auditoría | MAC, ubicación anterior, ubicación nueva |
| `AnomalyDetected` | Detection Engine | Incidentes, Consola, Auditoría | tipo, destino, fuentes, tasas, línea base, desviación |
| `IncidentOpened` | Incident Manager | Políticas, Consola, Auditoría | INC-id, tipo, objetivo, severidad |
| `MitigationRequired` | Policy Engine | Controlador (comando, no broker), Auditoría | INC-id, acción (RATE_LIMIT/BLOCK/…), objetivo, orígenes, TTL |
| `MitigationApplied` | Controlador | Monitor, Incidentes, Auditoría | INC-id, reglas instaladas, switches |
| `MitigationVerified` | Monitor | Incidentes, Políticas, Auditoría | INC-id, tasas antes/después |
| `MitigationExpired` | Monitor / Controlador | Incidentes, Políticas, Auditoría | INC-id, regla, motivo (timeout/retirada) |
| `ElevationRequested` | IAM (solicitud del académico) | Políticas, Consola, Auditoría | solicitante, perfil pedido, alcance, duración |
| `ElevationGranted` | Policy Engine | Controlador (comando), Auditoría | solicitante, perfil, TTL |
| `ElevationExpired` | Policy Engine | Controlador (comando), Auditoría | solicitante, perfil, motivo |
| `SessionOpened` / `SessionClosed` | IAM/AAA | Políticas, Auditoría | identidad, perfil o rol, dispositivo, instante |
| `DeviceRegistered` / `DeviceRevoked` | Registro | Auditoría, Consola | MAC, titular, rol, responsable, vigencia |

**Nota sobre `MitigationRequired`, `ElevationGranted` y `ElevationExpired`:** son decisiones que deben **aplicarse con confirmación**, por eso además de publicarse (para que la Auditoría y la Consola los vean) viajan como comandos northbound al Controlador. El evento informa; el comando ejecuta.

## 4. Orden de eventos por incidente

La cadena de un incidente (INC-0042) puede emitir muchos eventos en poco tiempo. El orden se garantiza así:

- El payload de cada evento lleva el **id del incidente** y un **número de secuencia** monotónico por incidente.
- Los consumidores agregan por incidente y procesan en orden de secuencia; un evento fuera de orden se reordena o se descarta, nunca se aplica fuera de sitio.
- El mecanismo de entrega ordenada (colas por incidente, particionado) es decisión de la Fase F; el contrato de secuencia es de este documento.

## 5. Matriz de comunicación completa

| Par | Canal | Sincronía | Qué fluye |
|---|---|---|---|
| Switch → Controlador | SDN (I1) | Asíncrono | PACKET_IN, PORT_STATUS, FLOW_REMOVED |
| Controlador → Switch | SDN (I1) | Comando + confirmación | FLOW_MOD, METER_MOD, GROUP_MOD, PACKET_OUT, MULTIPART |
| Controlador ↔ Switch | SDN (I1) | Periódico | ECHO (latido) |
| Servicios → Controlador | Northbound (I2) | Síncrono | Órdenes de política, consultas de topología/estado |
| Monitor → Controlador → Switch | I8 (vía I2+I1) | Síncrono periódico | Contadores |
| Servicio → Broker → Servicios | Broker (I5) | Asíncrono | Eventos del catálogo (§3) |
| Consola → Servicios | API (I7) | Síncrono | Consultas y órdenes administrativas |
| Poblaciones → Portal → IAM | I3 | Síncrono | Credenciales, sesión |
| IAM → IdP | I4 | Síncrono | Verificación de identidad y atributos de la comunidad |
| Servicio → Repositorio | I6 | Síncrono local | Lectura/escritura de datos propios |

## 6. Cuestiones abiertas

- **Mecanismo de entrega ordenada** del broker (colas por incidente, particionado): Fase F.
- **Confirmación de los comandos northbound.** Si basta la confirmación de OpenFlow (regla instalada) o se exige además la verificación por contadores antes de declarar `MitigationApplied`.
- **Retención de eventos en el broker.** Cuánto tiempo se conservan los eventos consumidos; ligado a la retención de logs (fase A, cuestión abierta).
