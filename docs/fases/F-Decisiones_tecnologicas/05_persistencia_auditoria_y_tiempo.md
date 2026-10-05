# Persistencia, auditoría y tiempo

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

Tres decisiones en un documento: la **persistencia (I6)**, la **retención e integridad de los registros** —lo que E-04 §3 y [componentes/03](../../componentes/03_seguridad.md) §8 dejaron abierto, ahora con motivo forense concreto: el historial de dispositivo— y la **fuente de tiempo común** que E-05 §3 difirió a esta fase. Cierra además la decisión de **visualización** del catálogo de drivers (B-03).

## 1. Qué exige la arquitectura

| Exigencia | Origen |
|---|---|
| Cada servicio persiste sus datos a través de su repositorio: `DeviceRepository`, `IncidentRepository` (`INC-xxxx`), `PolicyRepository`, `PermissionRepository`, `AuditRepository` | D-04 §5 |
| Ningún servicio lee la base de datos de otro: la comunicación es por eventos, no por tablas | D-04, D-07 §3 |
| Los eventos relevantes se almacenan para análisis, asociables a quién, qué, cuándo y por qué | RT-07, RNF-09, P11 |
| Retención y recuperación de registros definidas; aptas para investigación forense | E-04 §3, componentes/05 §6 |
| Fuente de tiempo común: la desincronización deteriora la correlación de eventos | E-05 §3, RNF-09 |
| Información suficiente para supervisar la operación | RT-06, RNF-08 |

## 2. Decisión: PostgreSQL

**PostgreSQL** como almacén de la plataforma, en una instancia única del prototipo con **una base de datos por servicio**. La consolidación de instancia es la permitida por RP-04/RP-07 —el prototipo no opera cinco motores—, pero la frontera no se mueve: **cada servicio accede solo a su base**; ningún servicio consulta la de otro (D-04 §6).

**Por qué relacional:** lo que se persiste es inherentemente relacional y transaccional —dispositivos y sus auditorías, incidentes con su máquina de estados, políticas con vigencia, permisos con TTL, eventos con su cadena de asociación—. La transacción protege la consistencia de la máquina de estados del incidente (nunca dos transiciones a la vez) y las consultas de auditoría que la investigación exige (por dispositivo, por incidente, por operador) son SQL directo. Un solo producto para todo el estado persistente es también la decisión de simplicidad (P4).

```text
PostgreSQL (instancia única del prototipo — red de gestión)
├── bd_registro     dispositivos privilegiados · altas y auditoría del registro
├── bd_iam          operadores (bcrypt) · sesiones · accounting RADIUS
├── bd_incidentes   incidentes INC-xxxx · máquina de estados · acciones
├── bd_politicas    políticas de mitigación · PermissionRepository (elevaciones)
├── bd_auditoria    eventos · acciones · cambios de política · mitigaciones
└── bd_monitor      series de contadores (resúmenes) para línea base y evidencia
```

**Límites:** la persistencia del plano de control (topología y reglas) es del controlador, no de la plataforma; el esquema detallado (columnas, índices) es Fase G; el cifrado en reposo y la gestión de respaldos de un despliegue real pertenecen a la Fase H.

## 3. Qué guarda cada servicio

| Base | Contenido | Clave de la correlación |
|---|---|---|
| `bd_registro` | Dispositivo (MAC, tipo, titular, rol, vigencia, responsable) + historial de altas | `dispositivo_id` |
| `bd_iam` | Cuentas de operador (hash + secreto TOTP), sesiones con su ligadura (MAC/puerto/IP), accounting | `SES-…` |
| `bd_incidentes` | Incidente (`INC-…`), transiciones `DETECTED → … → CLOSED`, acciones ejecutadas, origen | `INC-…` |
| `bd_politicas` | Políticas por severidad, elevaciones con alcance, TTL y responsable | `POL-…` / `PE-…` |
| `bd_auditoria` | Todo evento del catálogo y toda acción, con autor y causa | `evento_id` |
| `bd_monitor` | Resúmenes de contadores (pps, bps, fuentes) por ventana | `(destino, ventana)` |

La correlación entre bases no se hace con JOIN —sería leer la base ajena—: se hace con los identificadores que viajan en los eventos (P11): un incidente tiene su `INC-…`, su sesión, su dispositivo y sus cookies de reglas; con esos cuatro hilos, la auditoría reconstruye la historia completa.

## 4. Auditoría: retención e integridad

**Decisión.** El `AuditRepository` es la fuente autoritativa, con dos formas del mismo registro:

- **Tabla de auditoría** en `bd_auditoria`: consultable por rol (P08, P25), con todos los campos de asociación. Retención en línea: **90 días** (propuesta de despliegue), todo el período de validación en el prototipo.
- **Export JSONL append-only, con cadena de hash:** cada evento se anexa a un archivo diario (`auditoria-AAAA-MM-DD.jsonl`) y cada línea incluye el `sha256` de la línea anterior. Un borrado o una edición intermedia rompe la cadena y es detectable con un verificador de una página. **Es la respuesta a «¿se protegen contra manipulación?»**: la manipulación no se impide —el atacante con acceso total siempre puede borrar— pero **no puede pasar inadvertida**, que es lo que la evidencia forense necesita.

**Recuperación.** Respaldo lógico periódico (`pg_dump`) + el export JSONL, que es a la vez respaldo y evidencia: aunque la base se pierda, la secuencia de eventos sobrevive en texto verificable. En el prototipo se ejecuta un **drill de restauración**: restaurar la auditoría desde el export y verificar la cadena de hash de punta a punta; el tiempo de restauración se reporta (RNF-12).

## 5. Tiempo común

**Decisión.** **chrony** como cliente/servidor NTP en el segmento de gestión: el prototipo tiene **una fuente de tiempo propia** (el servidor de gestión), sincronizada a internet si el laboratorio lo permite y con reloj local disciplinado si no. Todos los nodos —servicios, controlador, hosts simulados— sincronizan contra ella; los switches usan el mismo servidor vía su cliente NTP.

- **Todo sello de tiempo se registra en UTC** (ISO 8601) y la auditoría guarda además el nodo de origen: la correlación (RNF-09) exige que dos eventos de nodos distintos sean comparables, y el orden del historial de dispositivo depende de ello.
- **Verificación:** se mide el desfase de cada nodo contra la fuente; el valor se reporta y se vigila (un desfase creciente es un síntoma temprano, no una sorpresa). Esto cierra el tratamiento de la «desincronización de tiempo» registrado en E-05 §3.

## 6. Visualización

**Decisión.** Dos vistas con audiencias distintas, sin solaparse (P4):

| Vista | Qué es | Para quién |
|---|---|---|
| **Consola** | El componente de administración (I7): consultar y modificar políticas, gestionar el registro de dispositivos, seguir incidentes, consultar auditoría según rol | Los operadores, en la operación diaria |
| **Tableros de observabilidad** | Grafana en modo lectura sobre `bd_monitor` y `bd_auditoria`: línea base, tasas antes/después de una mitigación, tiempos de detección y mitigación, el material de evidencia de R4.10 | La verificación del prototipo y la defensa del proyecto |

La consola no se reconstruye como herramienta de analítica, y los tableros no administran: cada vista hace lo suyo. El conjunto cierra RT-06 y RNF-08.

## 7. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Drill de restauración desde el export JSONL | Auditoría restaurada y cadena de hash verificada | E-04 §3, RT-07 |
| Corrupción deliberada de una línea del export | El verificador la detecta | Integridad, P11 |
| Desfase NTP de cada nodo | Desfase medido y acotado | E-05 §3, RNF-09 |
| Consulta de auditoría por rol | Cada rol ve lo que le corresponde (P08, P25) | R1.9, R2.9 |
| Alimentación de tableros | Línea base y métricas R4.10 visibles como evidencia | RT-06, RNF-08, RNF-12 |
| Aislamiento entre bases | Un servicio no puede leer la base de otro | D-04 §6 |
