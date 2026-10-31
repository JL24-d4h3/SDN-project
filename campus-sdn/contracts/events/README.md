# Contratos de eventos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Contratos
**Estado:** Borrador formal para revisión

---

Esquemas JSON del catálogo de eventos del bus. La fuente es [`LLD 02_eventos.md`](../../../docs/fases/G-Diseno_de_bajo_nivel-LLD/02_eventos.md) §2–3; la decisión de mensajería, [`F-04`](../../../docs/fases/F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md). Cada archivo valida el `payload` de su tipo; [`envelope.schema.json`](envelope.schema.json) valida el mensaje completo.

Regla de fondo: **el evento informa; el comando ejecuta**. Las decisiones con confirmación (`MitigationRequired`, `ElevationGranted`, `ElevationExpired`) viajan como comandos por I2 y publican su eco por el bus. Nunca viajan credenciales, ni en `payload` ni en `correlation`.

**Nombres de campos.** Los esquemas usan nombres en inglés; el LLD los describe en español. Correspondencia del vocabulario recurrente:

| LLD (español) | Esquema (inglés) |
|---|---|
| `evento_id`, `emisor`, `secuencia`, `correlacion` | `event_id`, `sender`, `sequence`, `correlation` |
| `incidente`, `sesion`, `dispositivo` | `incident`, `session`, `device` |
| `objetivo`, `origenes`, `tasas`, `linea_base` | `target`, `origins`, `rates`, `baseline` |
| `puerto`, `motivo`, `regla`, `reglas` | `port`, `reason`, `rule`, `rules` |
| `solicitante`, `perfil`, `vigencia`, `titular` | `requester`, `profile`, `validity`, `owner` |
| `desviacion`, `severidad`, `abierto_en` | `deviation`, `severity`, `opened_at` |
| `retirada` (valor de `reason`) | `withdrawn` |

**Colas.** Los nombres de cola también van en inglés en el código; el LLD las llama en español: `auditoria` → `audit`, `consola` → `console`, `deteccion` → `detection`, `incidentes` → `incidents`, `politicas` → `policies`, `registro` → `registry` (`monitor` e `iam` coinciden).

| Tipo | Esquema | Productor | Consumidores |
|---|---|---|---|
| `DeviceConnected` | [device-connected.schema.json](device-connected.schema.json) | Controlador | Registro, Monitor, Auditoría |
| `MAC_Moved` | [mac-moved.schema.json](mac-moved.schema.json) | Monitor | Incidentes, Políticas, Auditoría, IAM |
| `AnomalyDetected` | [anomaly-detected.schema.json](anomaly-detected.schema.json) | Detección | Incidentes, Consola, Auditoría |
| `IncidentOpened` | [incident-opened.schema.json](incident-opened.schema.json) | Incidentes | Políticas, Consola, Auditoría |
| `MitigationRequired` | [mitigation-required.schema.json](mitigation-required.schema.json) | Políticas | comando I2; eco: Auditoría, Consola |
| `MitigationApplied` | [mitigation-applied.schema.json](mitigation-applied.schema.json) | Controlador | Monitor, Incidentes, Auditoría |
| `MitigationVerified` | [mitigation-verified.schema.json](mitigation-verified.schema.json) | Monitor | Incidentes, Políticas, Auditoría |
| `MitigationExpired` | [mitigation-expired.schema.json](mitigation-expired.schema.json) | Monitor / Controlador | Incidentes, Políticas, Auditoría |
| `ElevationRequested` | [elevation-requested.schema.json](elevation-requested.schema.json) | IAM | Políticas, Consola, Auditoría |
| `ElevationGranted` | [elevation-granted.schema.json](elevation-granted.schema.json) | Políticas | comando I2; eco: Auditoría, Consola |
| `ElevationExpired` | [elevation-expired.schema.json](elevation-expired.schema.json) | Políticas | comando I2; eco: Auditoría, Consola |
| `SessionOpened` | [session-opened.schema.json](session-opened.schema.json) | IAM | Políticas, Auditoría |
| `SessionClosed` | [session-closed.schema.json](session-closed.schema.json) | IAM | Políticas, Auditoría |
| `DeviceRegistered` | [device-registered.schema.json](device-registered.schema.json) | Registro | Auditoría, Consola |
| `DeviceRevoked` | [device-revoked.schema.json](device-revoked.schema.json) | Registro | Auditoría, Consola |
| `MetricSample` | [metric-sample.schema.json](metric-sample.schema.json) | Monitor | Detección |

`MetricSample` es observación en bruto de alto volumen, no evento de auditoría. La prueba de validación de esquema del catálogo corresponde a RNF-12 ([`LLD 02_eventos.md`](../../../docs/fases/G-Diseno_de_bajo_nivel-LLD/02_eventos.md) §6).
