# Datos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La **persistencia es la memoria de cada servicio, y de nadie más** (I6, [`D-04`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md) §3): un repositorio por servicio, sin accesos cruzados. Los datos del sistema son de **tres clases**, y la clasificación manda sobre todo lo demás:

- **Estado operativo** — lo que describe la realidad del sistema ahora (sesiones, líneas base, mitigaciones vigentes). Se **reconcilia contra el plano de datos** cuando hay duda ([`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §6: el plano de datos es la verdad).
- **Registros de negocio** — lo que las personas y los procesos declaran (dispositivos, políticas, umbrales). Viven hasta que una autoridad los cambia.
- **Auditoría** — lo que prueba quién hizo qué y cuándo. Inmutable y con retención propia ([`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md)).

**La correlación viaja en los eventos, no en las consultas.** Ningún servicio lee la base de otro (D-04). Un incidente y la sesión que lo provocó se relacionan por los identificadores que el evento lleva en su envoltura ([`02`](02_eventos.md) §2: `correlacion`), y cada base guarda su copia del identificador ajeno. Un `JOIN` entre bases no existe: es una decisión de arquitectura, no una limitación del motor.

## 2. El diccionario de entidades

| Entidad | Identificador | Qué es | Vive en |
|---|---|---|---|
| Dispositivo | `mac` | Equipo conocido del campus, con su historial | `bd_registro` |
| Identidad | `usuario` | Persona de la comunidad (IdP) o del reino operadores | IdP / `bd_iam` |
| Sesión | `SES-xxxxxx` | El SSO: identidad + rol + dispositivo ligado + vigencias | `bd_iam` |
| Perfil | `perfil` | ACADÉMICO, operador, elevación: alcance y vigencias | `bd_politicas` |
| Incidente | `INC-xxxx` | La detección y su ciclo de vida completo | `bd_incidentes` |
| Mitigación | (parte del incidente) | La respuesta instalada, de aplicada a expirada | `bd_incidentes` |
| Elevación | `ELE-xxxxxx` | Privilegio temporal, con alcance y tope | `bd_politicas` |
| Línea base | `destino` protegido | La EWMA que el Monitor mantiene por destino | `bd_monitor` |

## 3. Esquemas por servicio

PostgreSQL, **una base por servicio** con su usuario propio y sin permisos cruzados ([`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §2). Notación: PK clave primaria, FK clave foránea local (nunca entre bases).

### `bd_registro` — catálogo de dispositivos privilegiados

| Tabla | Columnas principales |
|---|---|
| `dispositivos` | `mac` PK · `tipo` · `titular` · `rol` · `estado` (activo/revocado) · `vigencia_hasta` · `responsable` · `creado_en` |
| `historial_dispositivo` | `id` PK · `mac` FK · `evento` (alta, revocación, movimiento, incidente asociado) · `detalle` · `ts` |

El historial es la fuente del «historial de dispositivo» que la investigación de un `MAC_Moved` consulta ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4). Solo dispositivos privilegiados se registran (los académicos no viven en ningún catálogo, [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md) §3).

### `bd_iam` — identidades privilegiadas y sesiones

| Tabla | Columnas principales |
|---|---|
| `operadores` | `usuario` PK · `hash_bcrypt` · `totp_secreto` (cifrado) · `rol` (TI/Admin/SA) · `estado` · `creado_en` |
| `provision_totp` | `usuario` FK · `emitido_en` · `verificado_en` — el alta no se habilita hasta verificar el código ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §3) |
| `sesiones` | `sesion_id` PK · `usuario` · `rol` · `mac` · `switch_puerto` · `ip` · `idle_timeout_s` · `hard_timeout_s` · `creada_en` · `ultima_actividad` · `estado` (activa/cerrada/invalidada) · `motivo_cierre` |
| `tokens_derivados` | `token_hash` PK · `sesion_id` FK · `expira_en` — el token corto para herramientas, la misma sesión |

La ligadura de la sesión (MAC, switch:puerto, IP) es la que la petición valida en cada uso y la que `MAC_Moved` invalida. Las credenciales de la comunidad **no** viven aquí: viven en el IdP ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §2).

### `bd_incidentes` — ciclo de vida y mitigaciones

| Tabla | Columnas principales |
|---|---|
| `incidentes` | `inc_id` PK · `tipo` · `objetivo` · `severidad` · `estado` (abierto → en_mitigacion → mitigado → escalado → cerrado) · `abierto_en` · `cerrado_en` · `ultima_secuencia` |
| `eventos_incidente` | `inc_id` FK · `secuencia` · `evento_id` · `payload_json` · `procesado_en` — la cola del incidente, persistida |
| `mitigaciones` | `inc_id` FK · `accion` · `alcance` · `tasa_pps` · `ttl_s` · `cookie` · `estado` (aplicada/verificada/expirada) · `aplicada_en` · `verificada_en` · `expirada_en` · `aprobacion` (si cuarentena) |

`eventos_incidente` es el registro local de la cola `inc.<id>`: el Incident Manager persiste cada evento con su secuencia antes de procesarlo — un reinicio retoma exactamente donde quedó (idempotencia durable, [`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §4).

### `bd_politicas` — perfiles, umbrales y elevaciones

| Tabla | Columnas principales |
|---|---|
| `perfiles` | `perfil` PK · `idle_timeout_s` · `hard_timeout_s` · `alcance` — los valores iniciales de [`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §5 |
| `umbrales` | `destino` PK · `alfa` · `k_in` · `k_out` · `piso_pps` · `piso_bps` · `n_ventanas` — la parametrización de [`F-06`](../F-Decisiones_tecnologicas/06_deteccion_y_mitigacion.md) §3 |
| `escalera` | `accion` PK · `automatica` (bool) · `condicion` · `ttl_por_defecto` — la tabla de automatización de F-06 §5 |
| `elevaciones` | `elev_id` PK · `solicitante` · `perfil` · `alcance` · `ttl_s` · `estado` · `otorgante` · `ts` |

Todo cambio en estas tablas es una orden administrativa (I7) y queda en auditoría con su autor: los umbrales son configurables por diseño (P12), y **quién los movió** es parte del registro.

### `bd_monitor` — observación y línea base

| Tabla | Columnas principales |
|---|---|
| `contadores` | `ts` · `switch` · `puerto_o_flujo` · `pps` · `bps` — crudo del sondeo I8 · **retención: 24 h crudo, 7 días agregado** |
| `lineas_base` | `destino` PK · `media` · `varianza` · `ultima_ventana` — la EWMA por destino protegido |
| `features` | `ventana` · `destino` · `fuentes_distintas` · `flujos_nuevos` · `destinos_distintos_por_origen` — la materia prima de la clasificación |

El Monitor es el único que escribe aquí; la Detección recibe los features por el bus (`MetricSample`) y no toca esta base. Grafana lee esta base (y `bd_auditoria`) en **solo lectura** ([`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §6).

### `bd_auditoria` — quién, qué, cuándo y por qué

| Tabla | Columnas principales |
|---|---|
| `eventos_auditoria` | `id` PK · `ts` (UTC) · `actor` · `accion` · `objetivo` · `detalle` · `evento_id` (correlación) · `hash_previo` — **retención: 90 días** |
| `exports` | `archivo` · `rango_ts` · `hash_final` · `exportado_por` — el registro de cada export JSONL |

La auditoría llega **por el bus** (la cola `auditoria` consume todo el catálogo) y por registros directos de los servicios para sus actos administrativos (I7). El export de retención larga es **JSONL append-only con cadena de hash**: cada línea lleva el `sha256(línea ‖ hash_anterior)`; el hash final se copia en `exports` y en la primera línea del archivo siguiente. La manipulación no se impide — no puede pasar inadvertida (P11, [`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §4).

## 4. El plano de datos manda

Ninguna de estas bases es la verdad del plano de datos: lo son los switches ([`F-04`](../F-Decisiones_tecnologicas/04_mensajeria_y_eventos.md) §6). Tras cualquier caída, los registros se **reconcilian contra I2** —las reglas vivas por cookie— y el estado que no corresponda a una regla viva se cierra (una mitigación sin regla no puede quedar activa). Esta regla vale para todas las tablas de estado operativo de §3.

## 5. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Aislamiento entre bases: intento de acceso cruzado | Rechazo por permisos | I6, D-04 |
| Ciclo de incidente completo persistido | `incidentes` + `eventos_incidente` + `mitigaciones` coherentes al reiniciar el servicio | D-08 §4 |
| Drill de reconciliación (caída + expiración durante la caída) | Al volver, la mitigación expirada se cierra contra I2 | E-04, P10 |
| Verificador de cadena de hash sobre un export | Toda línea valida; una línea alterada rompe la cadena | P11 |
| Retención: borrado automático de `contadores` crudos | 24 h / 7 días según política | F-05 |
| Consulta de auditoría por rol | Solo el Auditor lee; el resto `403` | RT-07 |
