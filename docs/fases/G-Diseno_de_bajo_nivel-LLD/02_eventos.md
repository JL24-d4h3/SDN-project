# Eventos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

El **bus es la frontera asíncrona del sistema**: por él viaja todo lo que no espera respuesta ([`D-08`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md) §2). Su regla de fondo es la que fijó D: **el evento informa; el comando ejecuta** — las decisiones que deben aplicarse con confirmación (`MitigationRequired`, `ElevationGranted`, `ElevationExpired`) viajan como comandos por I2 y publican su eco por el bus para que la Auditoría y la Consola los vean. Los eventos cumplen **tres propósitos**: describir estado (sesiones, dispositivos), propagar detección (anomalías, verificaciones) y registrar decisión (incidentes, elevaciones). Las garantías de entrega son las de [`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md): al menos una vez, idempotencia, orden por incidente.

## 2. La envoltura común

Todo evento viaja con la misma envoltura; el contenido va en `payload`:

```json
{
  "evento_id": "018f2a...",            // UUIDv7: único, clave de idempotencia
  "tipo": "AnomalyDetected",           // nombre del catálogo (D-08 §3)
  "emisor": "deteccion",               // servicio que publica
  "timestamp": "2026-10-05T14:03:22Z", // UTC, reloj común (chrony)
  "secuencia": 7,                      // monótona por incidente; ausente fuera de incidentes
  "correlacion": {                     // claves de correlación entre servicios
    "incidente": "INC-0042",           //   cuando aplica
    "sesion": "SES-000123",            //   cuando aplica
    "dispositivo": "52:54:00:01:01"
  },
  "payload": { … }                     // específico del tipo, §3
}
```

- `evento_id` es lo que hace **idempotente** al consumidor: cada uno registra los ids ya procesados y descarta duplicados ([`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §4).
- `secuencia` es lo que hace **ordenable** al incidente: el consumidor acepta `secuencia == esperada + 1`; un salto se declara como hueco en auditoría, nunca se procesa fuera de sitio (D-08 §4).
- `correlacion` es lo que une los registros entre servicios sin cruzar bases ([`03`](03_datos.md) §1).

## 3. El catálogo, campo a campo

El catálogo es el contrato entre servicios (D-08 §3, P13). Aquí queda su forma definitiva:

| Tipo | Payload (campos) | Productor → consumidores |
|---|---|---|
| `DeviceConnected` | `mac`, `ip`, `switch`, `puerto`, `timestamp` | Controlador → Registro, Monitor, Auditoría |
| `MAC_Moved` | `mac`, `ubicacion_anterior` {switch,puerto}, `ubicacion_nueva` {switch,puerto} | Monitor → Incidentes, Políticas, Auditoría **y IAM** (invalida la sesión ligada, [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4) |
| `AnomalyDetected` | `tipo` (clase de ataque), `objetivo` {ip,servicio}, `origenes` [{mac,switch,puerto}], `tasas` {pps,bps}, `linea_base` {media,sigma}, `desviacion`, `severidad_propuesta` | Detección → Incidentes, Consola, Auditoría |
| `IncidentOpened` | `incidente`, `tipo`, `objetivo`, `severidad`, `abierto_en` | Incidentes → Políticas, Consola, Auditoría |
| `MitigationRequired` | `incidente`, `accion`, `objetivo`, `origenes`, `parametros`, `ttl` | Políticas → **comando I2**; eco al bus: Auditoría, Consola |
| `MitigationApplied` | `incidente`, `reglas` [ids], `switches`, `aplicada_en` | Controlador → Monitor (verifica), Incidentes, Auditoría |
| `MitigationVerified` | `incidente`, `tasas_antes`, `tasas_despues`, `cumple_objetivo` | Monitor → Incidentes, Políticas, Auditoría |
| `MitigationExpired` | `incidente`, `regla`, `motivo` (timeout o retirada) | Monitor / Controlador → Incidentes, Políticas, Auditoría |
| `ElevationRequested` | `solicitante`, `perfil_pedido`, `alcance`, `duracion` | IAM → Políticas, Consola, Auditoría |
| `ElevationGranted` / `ElevationExpired` | `solicitante`, `perfil`, `ttl` / `motivo` | Políticas → **comando I2**; eco al bus: Auditoría, Consola |
| `SessionOpened` / `SessionClosed` | `identidad`, `perfil_o_rol`, `dispositivo`, `timestamp` / `motivo` | IAM → Políticas, Auditoría |
| `DeviceRegistered` / `DeviceRevoked` | `mac`, `titular`, `rol`, `responsable`, `vigencia` | Registro → Auditoría, Consola |
| `MetricSample` | `destino`, `ventana`, `pps`, `bps`, `flujos_nuevos`, `fuentes_distintas` | Monitor → **Detección** (la materia prima, [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §2) |

`MetricSample` es la única adición de esta fase al catálogo de D: las métricas del Monitor hacia la Detección viajan por el bus por contrato (D-04, F-06 §2), y necesitan su tipo propio. No es un evento de auditoría: es observación en bruto, de alto volumen, consumida por un solo servicio.

**Qué no viaja nunca por el bus:** comandos (I2), preguntas (I7) y **credenciales** — ni en payload ni en correlación. Un evento puede referirse a una sesión por su identificador, jamás por su secreto.

## 4. Enrutamiento y colas

Exchange `plataforma` (topic, durable). Clave de enrutamiento: `evento.<Tipo>`. Cada servicio consumidor tiene **su propia cola durable** con sus enlaces ([`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §3):

| Cola | Enlaces (`evento.*`) | Consumidor |
|---|---|---|
| `auditoria` | `#` (todo el catálogo) | Auditoría |
| `monitor` | `DeviceConnected`, `MitigationApplied` | Monitor |
| `deteccion` | `MetricSample` | Detección |
| `incidentes` | `AnomalyDetected`, `MitigationVerified`, `MitigationExpired`, `MAC_Moved` | Incidentes |
| `politicas` | `IncidentOpened`, `MitigationVerified`, `MitigationExpired`, `ElevationRequested`, `MAC_Moved` | Políticas |
| `iam` | `MAC_Moved` | IAM |
| `registro` | `DeviceConnected` | Registro |
| `consola` | `AnomalyDetected`, `IncidentOpened`, `DeviceRegistered`, `DeviceRevoked` | Consola (alertas en vivo) |

**Cola por incidente** (`inc.INC-0042`): el ciclo completo del incidente —`IncidentOpened`, `MitigationRequired`, `MitigationApplied`, `MitigationVerified`, `MitigationExpired` y sus elevaciones asociadas— se publica **además** en su cola propia, declarada al abrir el incidente y auto-borrada al cerrarlo (TTL de respaldo 24 h). Es el mecanismo de entrega ordenada: orden FIFO de una sola cola, sin reordenamiento en el consumidor (D-08 §4). El Incident Manager consume de ella el ciclo completo; los demás servicios consumen de sus colas por servicio.

## 5. Parámetros de entrega y recuperación

| Parámetro | Valor inicial | Papel |
|---|---|---|
| Confirmación de publicación | Activada (`publisher confirms`) | El publicador sabe que el broker recibió (F-04 §4) |
| Buffer local del publicador | Acotado (10 000 mensajes), retroceso progresivo hasta 60 s | El broker caído no detiene al publicador; el desborde se registra como **hueco declarado** en auditoría — jamás se oculta (P11) |
| Ack de consumo | Manual, tras procesar | Un mensaje solo se descarta cuando se procesó |
| Reintentos | 5, con retroceso 1 s → 60 s | Tras agotarse: a la DLQ |
| DLQ | Una por cola (`dlq.<cola>`), sin consumidor automático | Lo no procesado queda visible; su llegada a DLQ se registra en auditoría |
| Ventana de duplicados | 7 días de `evento_id` procesados por consumidor | Idempotencia |
| Buffer de reorden | 100 mensajes por incidente | Hueco detectado: se espera el faltante; si no llega en 10 s, hueco declarado y se continúa |

## 6. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Consumidor detenido durante un ciclo de incidente; levantarlo | Cero eventos perdidos; orden restaurado por `secuencia` | I5, D-08 §4 |
| Reenvío con duplicados deliberados | Idempotencia por `evento_id`: sin efectos dobles | D-08 §4 |
| Broker detenido durante una ráfaga | Buffer local absorbe; reconexión; huecos declarados si los hubo | P13, E-04 |
| Mensaje que agota reintentos | Queda en DLQ y en auditoría | P11 |
| `MAC_Moved` con sesión viva | El IAM invalida la sesión; `SessionClosed` auditado | RNF-01, R3.3 |
| Validación de esquema | Todo evento emitido valida contra el catálogo de §3 | RNF-12 |
