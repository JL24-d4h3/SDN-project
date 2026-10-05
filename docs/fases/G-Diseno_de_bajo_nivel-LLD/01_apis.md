# APIs

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La **API es la frontera síncrona del sistema**: todo lo que se pide con respuesta inmediata viaja por una API, nunca por el bus ([`D-08`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/08_comunicacion.md) §2). El sistema tiene **dos familias** de API, por su naturaleza:

- **I2 — la API del plano de control.** Órdenes de política al controlador y consultas de topología y estado. La hablan los servicios (Políticas, IAM, Monitor, Incidentes), no las personas.
- **I7 — las API de administración.** Cada servicio expone sus consultas y órdenes administrativas; la Consola es su cliente y **la sesión del operador es el SSO** ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4).

Y una tercera superficie, **I3**: los formularios del portal — la única API que hablan las poblaciones.

**Principios comunes a las tres.** HTTPS sobre la red de gestión (out-of-band), JSON UTF-8, autenticación y autorización validadas **del lado del servidor, siempre** (nunca se confía en el cliente), operaciones idempotentes, errores estructurados y versionado `/v1` en la ruta.

## 2. I2 — órdenes al controlador

Un solo recurso de órdenes y una confirmación en dos niveles ([`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §4.4). Las cuatro órdenes fijadas en F —`APLICAR_PERFIL`, `APLICAR_MITIGACION`, `RETIRAR`, `CONSULTAR`— se materializan así: las tres primeras por `POST /api/v1/ordenes`; `CONSULTAR` se realiza como la familia `GET` de la tabla siguiente (estado de órdenes, asociaciones, reglas, topología, contadores, servicios). Autenticación: clave de servicio por cliente sobre TLS.

| Recurso | Uso |
|---|---|
| `POST /api/v1/ordenes` | Ejecutar una orden (`APLICAR_PERFIL`, `APLICAR_MITIGACION`, `RETIRAR`) |
| `GET /api/v1/ordenes?cookie=…` | Estado de una orden anterior (idempotencia y reconciliación) |
| `GET /api/v1/asociaciones?ip=…` | Asociación vigente MAC ↔ switch:puerto ↔ IP (ligadura de sesión) |
| `GET /api/v1/reglas?cookie=…&switch=…` | Reglas instaladas (reconciliación de incidentes) |
| `GET /api/v1/topologia` · `GET /api/v1/contadores` | Grafo de la red; contadores por puerto y flujo (I8) |
| `POST /api/v1/servicios` · `GET /api/v1/servicios` | Inventario de servicios (anclajes del grafo, §4) |

**Estructura común de la orden** (todas las órdenes la respetan):

```json
POST /api/v1/ordenes            (HTTPS, red de gestión)
{
  "orden": "APLICAR_PERFIL",
  "dispositivo": { "mac": "52:54:00:01:01", "switch": "SA1", "puerto": "p3" },
  "vigencia":    { "idle_timeout_s": 1800, "hard_timeout_s": 43200 },
  "contexto":    { "cookie": "SES-000123", "solicitante": "iam",
                   "motivo": "login-academico" }
}
→ 201  { "estado": "APLICADA", "reglas": ["…"], "confirmada_en": "…" }
```

| Campo | Tipo | Regla |
|---|---|---|
| `orden` | string | Una de las cuatro; las demás claves dependen de ella |
| `dispositivo` | objeto | `mac`, `switch`, `puerto` — la ubicación aprendida del dispositivo |
| `vigencia` | objeto | `idle_timeout_s` y `hard_timeout_s`: **el mismo valor que la sesión** ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §5) |
| `contexto.cookie` | string | Clave de idempotencia: reaplicar la misma cookie produce las mismas reglas, sin duplicados |
| `contexto.solicitante` | string | Identidad del servicio que ordena — se registra y se audita |

**`APLICAR_PERFIL`** — instala las reglas de un perfil (sesión o elevación). Además de la anterior: `perfil` (`ACADEMICO`, `OPERADOR`, elevación). El controlador traduce el perfil a sus reglas de alcance ([`06`](06_reglas.md) §3); el solicitante **no** dicta prioridades ni matches: expresa el qué, no el cómo (I2, [`D-07`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md)).

**`APLICAR_MITIGACION`** — instala la respuesta de la escalera:

```json
{
  "orden": "APLICAR_MITIGACION",
  "accion": "RATE_LIMIT",
  "objetivo": { "tipo": "servicio", "ip": "10.2.0.10" },
  "origenes": [ { "mac": "52:54:00:03:02", "switch": "SA1", "puerto": "p9" } ],
  "parametros": { "tasa_pps": 1000, "ttl_s": 300 },
  "contexto": { "cookie": "INC-0042", "incidente": "INC-0042",
                "solicitante": "policy-engine", "motivo": "flood",
                "aprobacion": null }
}
→ 201  { "estado": "APLICADA", "verificacion": "PENDIENTE" }
```

| Campo | Tipo | Regla |
|---|---|---|
| `accion` | string | `RATE_LIMIT`, `BLOCK_SOURCE`, `ISOLATE_DEVICE`, `QUARANTINE` |
| `objetivo` / `origenes` | objetos | Dónde y contra quién; `ISOLATE_DEVICE` y `QUARANTINE` apuntan al dispositivo, `BLOCK_SOURCE` al origen |
| `parametros` | objeto | `tasa_pps` (solo `RATE_LIMIT`) y `ttl_s` — toda mitigación expira sola (P10) |
| `contexto.aprobacion` | string o null | Obligatorio para `QUARANTINE`: el identificador de la aprobación humana (D-03 §5). El Policy Engine no emite cuarentena sin él; el controlador la rechaza si falta |

La respuesta `APLICADA` es la **confirmación de aplicación** (OpenFlow barrier). La **verificación** (`verificacion: "PENDIENTE"`) la cierra el Monitor por contadores y llega por el bus como `MitigationVerified` ([`02`](02_eventos.md) §3) — nunca por esta API.

**`RETIRAR`** — `{ "orden": "RETIRAR", "contexto": { "cookie": "SES-000123" } }` → `200 { "estado": "RETIRADA" }`. El retiro es **por cookie, siempre**: nunca se toca una regla ajena (P10, [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §3).

**Errores** (comunes a las tres órdenes): `400` esquema inválido · `401` sin clave válida · `403` orden fuera de la competencia del solicitante · `404` dispositivo o cookie desconocidos · `409` orden duplicada con cookie distinta · `503` controlador no disponible — el solicitante **reintenta la misma orden** (idempotencia por cookie) hasta confirmación.

## 3. I7 — API de administración por servicio

Cada servicio expone sus propios recursos; la Consola los agrega. La sesión llega como cookie (navegador) o como **token derivado de vida corta** (herramientas) — ambas con la misma vigencia y ligadura ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §4). El servicio valida sesión **y** rol en cada petición; la interfaz no concede nada.

| Servicio | Recursos principales | Rol mínimo |
|---|---|---|
| IAM | `GET /sesiones/{id}` · `DELETE /sesiones/{id}` (logout administrativo) · `POST /dispositivos/{mac}/reaprovisionar-totp` | TI |
| Registro | `GET/POST /dispositivos` · `GET /dispositivos/{mac}/historial` | TI / Admin |
| Incidentes | `GET /incidentes` · `GET /incidentes/{id}` · `POST /incidentes/{id}/aprobar` (cuarentena) · `POST /incidentes/{id}/cerrar` | Admin / SA |
| Políticas | `GET/PUT /perfiles` · `GET/PUT /umbrales` · `GET /elevaciones` | TI / Admin |
| Auditoría | `GET /eventos?desde=…&actor=…` (solo lectura) | Auditor |
| Monitor | `GET /metricas` · `GET /lineas-base` (solo lectura) | Admin / SA |

**Convenciones.** Respuesta `{ "datos": …, "error": { "codigo": "SESION_EXPIRADA", "mensaje": "…" } }`; paginación por cursor (`?cursor=…&limite=100`); `401` sin sesión, `403` con sesión sin rol. El `PUT` de umbrales y perfiles escribe en `bd_politicas` y publica el cambio en auditoría — los valores son configurables por diseño (P12), y **quién** los cambió queda registrado.

## 4. El inventario de servicios (cierre de flows/05 §8)

El grafo de la red no ve extremos: LLDP conecta switches, no servicios. Los servicios son infraestructura **declarada** ([`flows/05`](../../../flows/05_enrutamiento.md) §4). La vía que la declara, fijada aquí: **I2, con privilegio administrativo**.

```json
POST /api/v1/servicios
{
  "nombre": "bd-academica", "clase": "critico",
  "ip": "10.2.0.12", "switch": "SA2", "puerto": "p4",
  "declarado_por": "ti-operaciones"
}
```

El controlador ancla cada servicio al grafo y calcula sus caminos; un cambio de anclaje rehace el cálculo igual que un cambio de topología. La administración de la red es la única que declara servicios — ningún servicio se autodeclara.

## 5. I3 — los formularios del portal

La única API que hablan las poblaciones. Un solo servicio, tres pasos:

| Recurso | Qué ocurre |
|---|---|
| `GET /login` | Selector explícito de población: «Comunidad universitaria» / «Personal de operación» ([`F-03`](../F-Decisiones_tecnologicas/03_identidad_sesiones_y_portal.md) §6) |
| `POST /login` | Credenciales (+ TOTP si operación). El IAM verifica por la ruta elegida; la sesión resultante la decide el Policy Engine — el portal no conecta nada por sí mismo (I3, [`D-07`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md)) |
| `POST /logout` | Retiro por cookie y `SessionClosed` inmediatos, sin esperar relojes |
| `GET/POST /elevacion` | Solicitud de elevación del académico → `ElevationRequested` al bus |

El selector no concede nada: solo elige la ruta de verificación. Un intento con credenciales en la ruta equivocada falla y se audita.

## 6. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Orden de perfil completa (I2 → reglas → `APLICADA`) | Latencia orden → confirmación; idempotencia por cookie | RT-04, RNF-04 |
| Rechazo de orden inválida (cuarentena sin aprobación, cookie ajena) | `403`/`400` y registro en auditoría | D-03 §5, P10 |
| Consulta de asociación durante el login | Ligadura de sesión con la ubicación aprendida | RNF-01 |
| Declaración de un servicio en el inventario | El grafo lo ancla y recalcula caminos | flows/05 §4 |
| Petición I7 con sesión vencida y con rol insuficiente | `401` y `403`; la interfaz no concede | R1.8, I7 |
