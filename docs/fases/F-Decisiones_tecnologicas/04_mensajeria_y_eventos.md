# Mensajería y eventos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

El bus de eventos es el canal interno de [`D-08`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md): los componentes de seguridad se comunican por eventos a través de un intermediario (P13) y el catálogo de eventos es su contrato. Esta fase decide **el producto del intermediario (I5), el mecanismo de entrega ordenada, las garantías de entrega y la reconciliación tras un fallo** —los tres últimos diferidos explícitamente por D-08 §4/§6 y E-04 §2.

## 1. Qué exige la arquitectura

| Exigencia | Origen |
|---|---|
| Todo evento del catálogo viaja por el intermediario; publicar no espera al consumidor | P13, D-08 §3 |
| Un consumidor caído **no pierde eventos**: las colas retienen lo no entregado | D-07 I5 |
| Los eventos de un incidente se entregan **en orden**: contrato de identificador de incidente + secuencia monótona | D-08 §4 |
| Las ráfagas de un ataque se absorben en colas; el intermediario caído no detiene a los publicadores | P13, E-04 §2 |
| Tras un fallo, el estado se **reconcilia** contra la realidad del plano de datos | E-04 §2, RA-07 |
| El producto se elige **contra el tamaño real del prototipo**, no contra producción | P4, D-03 §5 |

## 2. Decisión: RabbitMQ

**RabbitMQ** como intermediario de I5, en una instancia única del prototipo. Es un broker de mensajes maduro cuyo modelo —exchange/cola/routing key— calza exactamente con lo que el contrato de D-08 pide sin inventar nada: colas durables (I5: nada se pierde con el consumidor caído), orden FIFO por cola (la entrega ordenada por incidente), confirmaciones de publicación, colas con TTL y auto-borrado (el ciclo de vida de un incidente) y cola de mensajes muertos (lo que no pudo entregarse queda visible, no se pierde).

**Dimensionamiento contra el prototipo (P4).** El bus transporta eventos de **incidente**, no paquetes: un flood sostenido produce decenas de eventos por segundo en el peor caso —muestras de anomalía, transiciones de incidente, aplicaciones y verificaciones—, cada uno del orden de un kilobyte. Es una carga trivial para una instancia única en una VM modesta del laboratorio y, a la vez, suficiente para medir lo que RNF-03/RA-08 piden: la latencia de publicación a consumo y el comportamiento bajo ráfaga. La alta disponibilidad del broker **no se despliega** (C-04 §4); su vía es la misma que la del controlador: por diseño, no en el prototipo.

## 3. Topología de colas

```text
                    exchange  plataforma  (topic, durable)
   publicadores ──────────►  evento.<Tipo>            inc.<INC-id>
                                  │                       │
        colas durables por servicio                    cola por incidente
   ┌──────────┬──────────┬───────────┬──────────┐   ┌──────────────────┐
   │auditoría │ monitor  │ incidentes│ política │   │ inc.INC-0042     │
   │(todo)    │(muestras│(anomalías,│(eleva-   │   │ ciclo de mitiga- │
   │          │ y verif.)│ incidentes)│ ciones) │   │ ción ordenado    │
   └──────────┴──────────┴───────────┴──────────┘   └──────────────────┘
```

- **Exchange único de eventos** (`plataforma`, topic, durable): cada servicio consumidor tiene **su propia cola durable** enlazada a los tipos de evento que le interesan. Añadir un consumidor no toca a ningún publicador (P13); un consumidor caído acumula en su cola y procesa al volver (I5).
- **Cola por incidente** (`inc.<INC-id>`): el ciclo de vida de un incidente —`IncidentOpened`, `MitigationRequired`, `MitigationApplied`, `MitigationVerified`, `MitigationExpired`, las elevaciones asociadas— se publica además en una cola propia del incidente, declarada al abrirse y auto-borrada al cerrarse (con TTL de respaldo). **Es el mecanismo de entrega ordenada que D-08 §4 dejó a esta fase:** orden FIFO de una sola cola, sin reordenamiento en el consumidor.

## 4. Garantías de entrega

| Garantía | Cómo |
|---|---|
| **Nada se pierde con el consumidor caído** | colas durables + mensajes persistentes; el consumidor acumula y procesa al volver |
| **Nada se pierde con el broker caído** | el publicador confirma (`publisher confirms`); si el broker no está, el publicador **bufferiza localmente** (bounded) y reintenta con retroceso progresivo — la ráfaga de un ataque no tumba a nadie (P13, E-04 §2) |
| **Entrega al menos una vez, sin efectos dobles** | ack manual tras procesar; todo evento lleva `evento_id` y los consumidores son **idempotentes** (descartan duplicados por id) |
| **Detección de huecos y desorden** | todo evento de incidente lleva `secuencia` monótona por incidente; el consumidor agrega por incidente y detecta saltos |
| **Lo que no se pudo procesar queda visible** | cola de mensajes muertos (DLQ) por cola: tras N reintentos con retroceso, el mensaje va a la DLQ y su existencia se registra en auditoría — nunca se descarta en silencio |

**Frontera:** el buffer local del publicador es acotado; si se desborda, la pérdida se registra como **hueco declarado** en auditoría — el sistema puede perder un evento bajo una caída doble, pero jamás lo oculta (P11).

## 5. Qué viaja por dónde

- **Eventos** (todos los del catálogo de D-08 §3): por el exchange `plataforma`; los del ciclo de un incidente, además, por su cola `inc.<id>`.
- **Órdenes**: las órdenes de mitigación y de perfil viajan por **I2 hacia el controlador** (síncronas, con confirmación — [`01`](01_controlador_y_api_northbound.md) §4); su eco informativo (`MitigationRequired`, `ElevationGranted`, `ElevationExpired`) viaja como evento —el evento informa, la orden ejecuta (D-08 §3).
- **Preguntas**: no entran al bus (D-08 §2): las consultas administrativas y de reconciliación van directas al interesado.

## 6. Reconciliación tras un fallo (decisión de E-04)

La regla que ordena todo: **el plano de datos es la verdad; los registros se reconcilian contra él.** Los hechos sobreviven en los switches —reglas con cookie y timeout— aunque los servicios pierdan memoria.

| Fallo | Al recuperar |
|---|---|
| **Incident Manager** | relee su cola durable (nada perdido) y **reconcilia contra el controlador**: consulta las mitigaciones vigentes por cookie (I2) y cierra los incidentes cuyas mitigaciones ya expiraron (P10) — una mitigación sin regla viva no puede quedar como activa |
| **Broker** | las colas durables restauran lo pendiente; los publicadores vacían su buffer local; el orden por incidente se restaura por secuencia |
| **Consumidor cualquiera** | procesa el atraso de su cola; la idempotencia absorbe los duplicados del reenvío |
| **Controlador** | los switches conservan reglas y timeouts; al reconectar, re-registro y reinstalación ([`01`](01_controlador_y_api_northbound.md) §6); los servicios confirmados como «aplicado» que ya no existan se reportan como expirados |

## 7. Retención en el broker (decisión de D-08 §6)

El broker es **tránsito, no archivo**: las colas por incidente se autoborran al cerrarse; las colas por servicio tienen TTL de respaldo para lo no entregado; la retención duradera de eventos vive en el `AuditRepository` ([`05`](05_persistencia_auditoria_y_tiempo.md) §4). La capacidad de las colas se acota con límite de longitud y desborde controlado, para que una avalancha no consuma el disco del laboratorio.

## 8. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Publicar con el consumidor detenido; levantarlo | Cero eventos perdidos; todo procesado | I5, D-07 |
| Orden de un ciclo de incidente completo bajo ráfaga | Llegan en orden por la cola del incidente | D-08 §4 |
| Reenvío con duplicados deliberados | Idempotencia: sin efectos dobles | D-08 §4 |
| Detener el broker durante una ráfaga | Buffer local absorbe; reconexión; huecos declarados si los hubo | P13, E-04 |
| Reintento agotado | El mensaje queda en DLQ y en auditoría | P11 |
| Drill de reconciliación: caída del Incident Manager + expiración de una mitigación durante la caída | Al volver, el incidente se cierra por reconciliación con el plano de datos | E-04, P10 |
| Latencia publicación → consumo y caudal sostenido | Los números del prototipo | RNF-03, RA-08 |
