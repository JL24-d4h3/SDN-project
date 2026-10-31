# Contratos de API

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Contratos
**Estado:** Borrador formal para revisión

---

La API es la frontera síncrona del sistema; la fuente es [`LLD 01_apis.md`](../../../docs/fases/G-Diseno_de_bajo_nivel-LLD/01_apis.md). Principios comunes: HTTPS sobre la red de gestión, JSON UTF-8, autorización validada del lado del servidor siempre, operaciones idempotentes, errores estructurados y `/v1` en la ruta.

| Archivo | API | Hablada por |
|---|---|---|
| [i2-controller.openapi.yaml](i2-controller.openapi.yaml) | I2 — órdenes al controlador y consultas del plano de control | Servicios (Políticas, IAM, Monitor, Incidentes) |
| [i7-administracion.openapi.yaml](i7-administracion.openapi.yaml) | I7 — administración por servicio | La Consola, con la sesión del operador como SSO |
| [i3-portal.openapi.yaml](i3-portal.openapi.yaml) | I3 — los formularios del portal | Las poblaciones; la única API pre-sesión |

**Correspondencia con el LLD.** Las rutas, campos y valores están en inglés; el LLD los describe en español:

| LLD (español) | Contrato (inglés) |
|---|---|
| `/ordenes`, `/asociaciones`, `/reglas`, `/topologia`, `/contadores`, `/servicios` | `/orders`, `/associations`, `/rules`, `/topology`, `/counters`, `/services` |
| `APLICAR_PERFIL`, `APLICAR_MITIGACION`, `RETIRAR` | `APPLY_PROFILE`, `APPLY_MITIGATION`, `WITHDRAW` |
| `APLICADA`, `PENDIENTE`, `RETIRADA` | `APPLIED`, `PENDING`, `WITHDRAWN` |
| `orden`, `dispositivo`, `vigencia`, `contexto` | `order`, `device`, `validity`, `context` |
| `solicitante`, `motivo`, `aprobacion`, `estado` | `requester`, `reason`, `approval`, `status` |
| `sesiones`, `dispositivos`, `incidentes`, `perfiles`, `umbrales`, `eventos`, `metricas`, `lineas-base` | `sessions`, `devices`, `incidents`, `profiles`, `thresholds`, `events`, `metrics`, `baselines` |
| `datos`, `codigo`, `mensaje` | `data`, `code`, `message` |
