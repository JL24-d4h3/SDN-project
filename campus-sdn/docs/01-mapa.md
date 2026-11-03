# Mapa del repositorio

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación
**Estado:** Vivo — se actualiza cuando la estructura cambia

---

## 1. Propósito

Que cualquiera que abra este repositorio sepa, en pocos minutos, **qué hay, qué significa cada pieza y cómo se conectan**. Responde cuatro preguntas en este orden: qué es este repositorio (§2), cómo se ve completo (§3), por dónde se empieza a leer (§4), qué es y para qué sirve cada pieza (§5) y qué flujos las unen (§6). Cuando un formato no se entienda, [`03-formatos.md`](03-formatos.md) lo explica desde cero. Las reglas de implementación están en [`../CLAUDE.md`](../CLAUDE.md).

## 2. Qué es este repositorio

La solución tiene dos mitades que viven en dos lugares:

| Mitad | Qué contiene | Dónde |
|---|---|---|
| **El corpus** | El diseño: arquitectura, decisiones, flujos y planes | [`../../docs/`](../../docs/), [`../../implementation/`](../../implementation/), [`../../flows/`](../../flows/) |
| **Este repositorio** | La construcción: contratos, política, automatización y pruebas | `campus-sdn/` |

El corpus es el plano; este repositorio es la obra. Todo lo que aquí existe materializa una decisión del corpus: un esquema traduce un catálogo de eventos, un Compose traduce el mapa de servidores, un rol traduce un paso del plan. Por eso cada pieza de aquí se entiende preguntando «¿qué decisión del corpus ejecuta?», y por eso los documentos del corpus se enlazan desde las piezas que los implementan.

## 3. El árbol, de un vistazo

Las carpetas marcadas *(pendiente)* existen a propósito: fijan el lugar de cada pieza antes de escribirla, para que el orden de construcción del plan se vea en la estructura. `tree` no muestra los archivos ocultos (`.gitignore`, `.env.example`, `.gitkeep`); los `.gitkeep` están vacíos y existen solo porque git no guarda carpetas vacías.

```text
campus-sdn/
├── CLAUDE.md                    # reglas de implementación y documentación: leer antes de tocar
├── README.md                    # puerta de entrada: objetivos make, reglas y enlaces
├── Makefile                     # única puerta de operación: cada tarea es un objetivo
├── .gitignore                   # qué no se versiona: bundles, .env, slice.yml, vault
│
├── contracts/                   # las promesas formales entre servicios, validables por máquina
│   ├── api/
│   │   ├── README.md            # índice: I2 e I7, la frontera síncrona
│   │   ├── i2-controller.openapi.yaml     # la API del plano de control: órdenes al controlador
│   │   └── i7-administration.openapi.yaml # las APIs de administración por servicio
│   ├── events/
│   │   ├── README.md            # índice del catálogo: tipo ↔ productor ↔ consumidores
│   │   ├── envelope.schema.json          # la envoltura que todo evento del bus lleva
│   │   └── <evento>.schema.json (×16)    # un esquema por evento: valida su payload
│   └── policy/
│       └── permissions.schema.json       # la forma que permissions.yaml debe cumplir
│
├── deploy/                      # todo lo que lleva la solución a las 14 VMs del slice
│   ├── ansible/
│   │   ├── ansible.cfg          # ajustes de Ansible: inventario, sudo, sin prompts
│   │   ├── inventory/
│   │   │   └── slice.example.yml          # plantilla de las 14 VMs; el real se ignora
│   │   ├── playbooks/
│   │   │   └── site.yml         # el sitio: un play por frente, con etiquetas
│   │   └── roles/               # un rol por frente del despliegue
│   │       ├── base/            # paquetes comunes, Docker, chrony, DNS
│   │       ├── images/          # copia, verifica y carga los bundles en la VM
│   │       ├── platform/        # Compose por VM: levantar, detener y salud
│   │       ├── onos/            # contenedor ONOS por VM y cluster.json del clúster
│   │       ├── switches/        # OVS: bridge, VLANs y controladores (la escalera la instala ONOS)
│   │       ├── identity/        # corte vertical a S1: construye en la laptop y carga los bundles propios
│   │       └── verify/          # salud de los servicios propios y conteo de switches desde onos1
│   ├── compose/                 # un archivo por VM de plataforma y ONOS
│   │   ├── onos.yml             # ONOS y el adaptador I2 por VM, red host
│   │   ├── s1-identity.yml      # S1 completo: Portal, IAM, Registry (build) + FreeRADIUS y OpenLDAP
│   │   ├── s2-observability.yml # Prometheus, Grafana y Suricata (espejo) de S2
│   │   ├── prometheus.yml       # configuración de rastreo de Prometheus
│   │   ├── s3-response.yml      # S3 completo: Incidentes, Políticas (build) + PostgreSQL
│   │   ├── s4-governance.yml    # RabbitMQ, el bus de eventos
│   │   └── minimal-slice.yml    # corte mínimo para el slice actual (bus, IAM, portal, registro, adaptador)
│   ├── scripts/
│   │   └── install_skeleton.py  # esqueleto BASE por la API REST de ONOS (los flujos ajenos los purga)
│   ├── radius/                  # el IdP simulado de la comunidad (F-03 §2): FreeRADIUS → OpenLDAP
│   │   ├── clients.conf.tpl     # plantilla de clientes (la imagen no los genera por entorno)
│   │   ├── mods-ldap.tpl        # plantilla del módulo LDAP (secreto del .env al desplegar)
│   │   └── site-default         # sitio default: autenticación LDAP + accounting detail
│   ├── ldap/
│   │   └── seed-users.ldif      # semilla de la comunidad (USR-000X); se siembra con ldapadd
│   ├── env/
│   │   └── .env.example         # plantilla de secretos; el .env real se ignora
│   └── images/                  # modelo de imágenes: descripción en git, binarios fuera
│       ├── images.lock          # referencia y digest de cada imagen: fuente única
│       ├── pull.sh              # descarga las imágenes y fija sus digests
│       ├── verify.sh            # compara los digests locales con el lock
│       ├── save.sh              # empaqueta los bundles con su suma
│       ├── load.sh              # carga y verifica los bundles en la VM
│       └── bundles/             # tarballs: existen solo en disco, nunca en git
│
├── docs/                        # documentación de este repositorio (nombres en español, numerados)
│   ├── 01-mapa.md               # este documento: estructura y sus hilos
│   ├── 02-estado.md             # avances y pendientes, actualizado en cada cierre
│   ├── 03-formatos.md           # tutorial: leer YAML, JSON, OpenAPI y Compose
│   ├── adr/                     # decisiones de código; se llena al decidir
│   ├── pruebas/                 # manuales de prueba sobre el slice actual (se ejecutan en orden)
│   │   ├── 00-inventario-del-slice-actual.md  # cada VM, interfaz, enlace, ruta y hallazgo verificado
│   │   ├── 01-perfil-base.md                  # cómo verificar que el esqueleto BASE funciona
│   │   ├── 02-lista-de-verificacion.md        # los 37 permisos, qué se verificó y qué falta
│   │   ├── 03-el-controlador-sus-tareas.md    # descubrimiento, topología, rutas y adaptividad de ONOS
│   │   └── 04-autenticacion-y-autorizacion.md # los tres reinos reales, TOTP en dos pasos, sesión y flujos
│   └── runbooks/                # procedimientos operativos; se llenan al operar
│
├── policy/                      # la política de autorización: quién puede qué
│   ├── permissions.yaml         # roles, perfiles, permisos, condiciones, asignaciones
│   ├── profiles.yaml            # vista derivada por generate_profiles.py
│   └── tools/
│       ├── generate_matrix.py   # genera la matriz rol × permiso desde el YAML
│       ├── generate_profiles.py # deriva profiles.yaml desde el YAML
│       └── validate.py          # valida el YAML contra el esquema y sus referencias
│
├── services/                    # un directorio por servicio propio
│   ├── common/                  # esqueleto compartido: app, salud, eventos, bus, autorización por la política
│   │   ├── sdn_common/
│   │   │   ├── app.py           # fábrica de FastAPI con /health
│   │   │   ├── authz.py         # require_permission: SSO contra el IAM + decisión por permissions.yaml
│   │   │   ├── bus.py           # publicar con confirmación; consumir con cola, DLQ e idempotencia
│   │   │   └── events.py        # envoltura, validación contra los esquemas y reloj UTC
│   ├── portal/                  # formularios de las poblaciones (I3): login, logout, elevación
│   │                           #  el dispositivo lo resuelve la red (I2 /associations), nunca el usuario
│   ├── iam/                     # tres reinos (RADIUS/bcrypt+TOTP/registro efímero), sesiones por perfil, MAC_Moved
│   ├── registry/                # dispositivos, historial, DeviceRegistered/Revoked
│   ├── monitor/                 # ubicaciones → MAC_Moved, MetricSample, verificación de mitigaciones
│   ├── detection/               # línea base por destino → AnomalyDetected
│   ├── incidents/               # apertura por AnomalyDetected → IncidentOpened; evidencia y aprobación P32
│   ├── policies/                # IncidentOpened → MitigationRequired; elevaciones y umbrales (I7)
│   ├── audit/                   # consume todo el catálogo (#); huecos de secuencia declarados; I7 de solo lectura
│   ├── console/                 # alertas en vivo con SSO del operador (IAM)
│   ├── sensor_adapter/          # EVE de Suricata → MetricSample reales por ventana
│   └── controller_adapter/      # I2 sobre ONOS: órdenes → flujos con la escalera del LLD
│
└── tests/                       # pruebas por nivel
    ├── contract/                # cada pieza cumple su contrato (RNF-12)
    ├── integration/             # piezas juntas contra dependencias reales
    └── e2e/                     # el flujo completo en el slice
```

## 4. Ruta de lectura

Se lee en este orden; cada paso dura poco y se apoya en el anterior:

1. **Este mapa, §3 y §5** — el árbol para ubicarse y las capas para entender qué es cada pieza. Es el recorrido de reconocimiento.
2. **Este mapa, §6** — los hilos: cómo se conectan las capas entre sí. Es el recorrido de comprensión.
3. **[`02-estado.md`](02-estado.md)** — qué está hecho y qué falta. Es el punto de partida para trabajar.
4. **[`03-formatos.md`](03-formatos.md)** — solo si un YAML, un JSON o un OpenAPI no se entiende a primera vista.

Y una tabla de respuesta rápida para ubicarse sin leer todo:

| ¿Qué quieres saber o hacer? | Ve a |
|---|---|
| Quién puede qué en el sistema | [`policy/`](../policy/) |
| Qué mensajes se envían los servicios y con qué forma | [`contracts/events/`](../contracts/events/) |
| Qué API exponen el controlador y los servicios | [`contracts/api/`](../contracts/api/) |
| Cómo llega todo esto a las 14 VMs del slice | [`deploy/`](../deploy/) |
| Dónde vivirá el código de cada servicio | [`services/`](../services/) |
| Cómo se demuestra que algo funciona | [`tests/`](../tests/) |
| Cómo se prueba en el slice actual (inventario, perfil base, verificación) | [`docs/pruebas/`](pruebas/) |
| Qué está hecho y qué falta | [`docs/02-estado.md`](02-estado.md) |

## 5. Las capas, a fondo

### 5.1 `policy/` — la política de autorización

**Qué es:** el documento ejecutable que decide **quién puede qué** en el sistema: cuatro roles (académico, TI, administrador de red, superadministrador), 36 permisos (P01–P36), condiciones que los matizan (C1–C11) y 78 asignaciones que los conectan. Nació en la etapa 0 del plan y es la pieza más cerrada del proyecto. Los valores de dominio están en inglés (`academic`, `network_admin`, `pre_session`, …); el corpus los conserva en español y la correspondencia completa está en [`policy/README.md`](../policy/README.md).

**Por qué existe:** porque la autorización no puede estar dispersa en el código de diez servicios — cada uno decidiría distinto. Un solo archivo, validado y versionado, es la única fuente de verdad: el IAM, las Políticas y la Auditoría consultan lo mismo.

**Qué contiene:**

| Archivo | Qué es | Para qué se usa |
|---|---|---|
| [permissions.yaml](../policy/permissions.yaml) | La política completa, en YAML: roles, perfiles, recursos, condiciones, permisos, asignaciones, reglas, delegaciones y prioridades | Es la fuente de verdad; todo lo demás de esta capa se deriva de él |
| [permissions.schema.json](../contracts/policy/permissions.schema.json) | La **forma** que el YAML debe cumplir, en JSON Schema | Para que una máquina rechace un YAML mal escrito antes de que lo use un servicio |
| [validate.py](../policy/tools/validate.py) | El validador: aplica el esquema y además comprueba que cada referencia exista (toda asignación nombra un rol, un permiso y una condición reales) | Se ejecuta tras cada cambio: `python3 policy/tools/validate.py` |
| [generate_matrix.py](../policy/tools/generate_matrix.py) | El generador de la matriz rol × permiso (Markdown y LaTeX) | Produce la vista humana que se publica en los documentos; `--check` falla si el documento y el YAML divergen |
| [profiles.yaml](../policy/profiles.yaml) | La vista de perfiles que los servicios consumen por separado | Derivada por `generate_profiles.py`; la prueba de contrato evita que diverja del YAML |

**Cómo se lee:** el archivo se recorre de lo general a lo particular — véase [`03-formatos.md`](03-formatos.md) §6, que lo explica bloque a bloque con un ejemplo.

### 5.2 `contracts/` — los contratos entre servicios

**Qué es un contrato:** la promesa formal de qué mensajes acepta y emite cada parte, fijada **antes** de escribir el código. El sistema tiene dos formas de comunicarse, y cada una tiene su contrato: lo **asíncrono** (eventos por el bus, que informan sin esperar respuesta) y lo **síncrono** (APIs, que piden y esperan respuesta). La regla del corpus es *el evento informa; el comando ejecuta*.

**Por qué existe:** porque dos personas pueden escribir un productor y un consumidor en paralelo sin romperse: ambos codifican contra la misma promesa, y una máquina la verifica. Sin contrato, cada servicio inventaría su formato y la integración sería un rompecabezas.

**Qué contiene:**

| Archivo | Qué es | Para qué se usa |
|---|---|---|
| [events/envelope.schema.json](../contracts/events/envelope.schema.json) | La envoltura que todo evento lleva: identificador único, tipo, emisor, marca de tiempo y correlación | Para validar el mensaje completo; el `payload` lo valida el esquema del tipo |
| [events/*.schema.json](../contracts/events/) (16) | Un esquema por tipo de evento (`session-opened`, `anomaly-detected`, …), cada uno con su productor y consumidores anotados | Cada servicio valida lo que publica y lo que consume contra el suyo |
| [events/README.md](../contracts/events/README.md) | El índice del catálogo: qué servicio produce y consume cada tipo | Para ubicar un evento por nombre |
| [api/i2-controller.openapi.yaml](../contracts/api/i2-controller.openapi.yaml) | La API del plano de control (I2): las órdenes que los servicios mandan al controlador | Para implementar o simular el controlador |
| [api/i7-administration.openapi.yaml](../contracts/api/i7-administration.openapi.yaml) | Las APIs de administración (I7) de los seis servicios que la Consola agrega | Para implementar cada servicio administrativo |
| [api/README.md](../contracts/api/README.md) | Índice de las dos APIs | Para elegir cuál leer |

**Cuándo se usan:** ahora mismo, en las pruebas de contrato (validar un evento de ejemplo contra su esquema, RNF-12); en el paso 4, para escribir los servicios; y en el slice, para que la Auditoría acepte solo eventos bien formados.

### 5.3 `deploy/` — cómo la solución llega al slice

**Qué es:** todo lo que convierte este repositorio en un sistema corriendo en las 14 VMs del slice. No contiene lógica de negocio: contiene el **transporte** (imágenes), la **configuración** (Compose, entorno) y la **ejecución** (Ansible).

**Por qué existe:** porque levantar catorce máquinas a mano no es reproducible: el orden importa, los errores se acumulan y nadie recuerda el paso 37. Aquí cada paso es un archivo, cada frente una etiqueta, y repetir no rompe nada (idempotencia).

**Qué contiene, por subcapa:**

| Pieza | Qué es | Para qué se usa |
|---|---|---|
| [images/images.lock](../deploy/images/images.lock) | La lista de las ocho imágenes con su **digest** (huella única del contenido) | Es la fuente única de qué versión exacta se usa en todas partes |
| [images/pull.sh](../deploy/images/pull.sh) | Descarga cada imagen y fija su digest la primera vez | En la laptop con internet; deja el lock completo |
| [images/verify.sh](../deploy/images/verify.sh) | Compara lo descargado con el lock | Para detectar una imagen cambiada o incompleta |
| [images/save.sh](../deploy/images/save.sh) | Empaqueta las imágenes en `bundles/*.tar` con su suma | Para transportarlas al slice sin depender de internet |
| [images/load.sh](../deploy/images/load.sh) | Verifica la suma y carga los bundles en la VM | En cada VM, una vez copiados los bundles |
| [compose/onos.yml](../deploy/compose/onos.yml) | Un contenedor ONOS por VM (con `cluster.json` para el clúster de 3 nodos) y el adaptador I2, ambos en red host | Para levantar el plano de control y su fachada I2 |
| [compose/s1-identity.yml](../deploy/compose/s1-identity.yml) | El stack completo de S1: Portal, IAM y Registry (construidos) sobre FreeRADIUS y OpenLDAP (imágenes del lock) | Para levantar el corte vertical de identidad con un comando |
| [compose/s2-observability.yml](../deploy/compose/s2-observability.yml) | Prometheus, Grafana y Suricata de S2 (la NIC del espejo se confirma en H0) | Para levantar la observabilidad con un comando |
| [compose/prometheus.yml](../deploy/compose/prometheus.yml) | Configuración de rastreo de Prometheus (objetivos del slice se añaden al desplegar) | Archivo extra que el rol `platform` copia junto al Compose |
| [compose/s3-response.yml](../deploy/compose/s3-response.yml) | El stack de S3: PostgreSQL con la base `bd_politicas` | Para levantar la base de datos con un comando |
| [compose/s4-governance.yml](../deploy/compose/s4-governance.yml) | El stack de S4: RabbitMQ, el bus de eventos | Para levantar el bus con un comando |
| [ansible/inventory/slice.example.yml](../deploy/ansible/inventory/slice.example.yml) | La plantilla del inventario: las 14 VMs, sus IPs y qué le toca a cada una (qué imágenes, qué Compose) | Se copia a `slice.yml` (ignorado por git) con los datos reales |
| [ansible/playbooks/site.yml](../deploy/ansible/playbooks/site.yml) | El sitio de despliegue: qué plays se ejecutan, sobre qué grupos | Es lo que corre `make deploy` |
| [ansible/roles/*](../deploy/ansible/roles/) | Un rol por frente (`base`, `images`, `platform`, `onos`, `switches`, `identity`, `verify`), cada uno con sus tareas y etiquetas | Para ejecutar o repetir un frente sin tocar los demás |
| [env/.env.example](../deploy/env/.env.example) | La plantilla de secretos y variables de entorno | Se copia a `.env` (ignorado) y se completa; sin él, Compose se niega a arrancar |

**Por qué los bundles no están en git:** una imagen pesa cientos de MB; git no es un registro de imágenes. El lock más los scripts reproducen cualquier bundle en cualquier máquina.

### 5.4 `services/` — el código de los servicios propios

**Qué es:** el lugar de los diez servicios que el equipo escribe (los de terceros — ONOS, RabbitMQ, PostgreSQL… — llegan como imágenes, no como código). Se llenan en el orden del plan: **`common/` y `portal/` ya existen**; `iam/` y `registry/` son los siguientes del corte vertical de identidad; el resto son reservas declaradas.

**Por qué existe:** para que nadie se pregunte dónde vive cada servicio, y para que cada uno crezca en su propio espacio con sus propias pruebas.

| Carpeta | Qué contiene |
|---|---|
| [common/](../services/common/) | **Construido** — el paquete `sdn_common`: fábrica de apps con `/health`, construcción y validación de eventos, publicación al bus |
| [portal/](../services/portal/) | **Construido** — los formularios de las poblaciones (I3): login, logout y elevación |
| [iam/](../services/iam/) | **Construido** — tres reinos (comunidad por RADIUS contra el IdP, F-03 §2; operadores por repositorio propio bcrypt + TOTP, F-03 §3; invitados por registro efímero con TTL que se borra solo); sesiones con vigencia por perfil e invalidación por `MAC_Moved` |
| [registry/](../services/registry/) | **Construido** — dispositivos, historial, `DeviceRegistered`/`DeviceRevoked` |
| [monitor/](../services/monitor/) | **Construido** — consume `DeviceConnected`/`MitigationApplied`; publica `MAC_Moved`, `MetricSample` y `MitigationVerified` |
| [detection/](../services/detection/) | **Construido** — consume `MetricSample`; mantiene la línea base y publica `AnomalyDetected` |
| [incidents/](../services/incidents/) | **Construido** — consume `AnomalyDetected`; publica `IncidentOpened`; evidencia, aprobación P32 y cierre |
| [policies/](../services/policies/) | **Construido** — consume `IncidentOpened`; publica `MitigationRequired`; elevaciones y umbrales por I7 |
| [audit/](../services/audit/) | **Construido** — consume el catálogo completo (`#`); los huecos de secuencia quedan declarados (P11); I7 de solo lectura |
| [console/](../services/console/) | **Construido** — alertas en vivo; SSO del operador contra el IAM |
| [sensor_adapter/](../services/sensor_adapter/) | **Construido** — agrega el EVE de Suricata en `MetricSample` reales por destino y ventana |
| [controller_adapter/](../services/controller_adapter/) | **Construido** — implementa I2: `APPLY_PROFILE`, `APPLY_MITIGATION` y `WITHDRAW` como flujos ONOS con la escalera del LLD (prioridades 1000/200, cookies por tipo, `hard_timeout = ttl`, retiro por cookie); confirma con `MitigationApplied` |

### 5.5 `tests/` — la evidencia por niveles

**Qué es:** las pruebas, organizadas por la pregunta que responden. Cada nivel se construye sobre el anterior: si el contrato no se cumple, no tiene sentido probar la integración.

| Carpeta | Pregunta que responde | Qué hay hoy |
|---|---|---|
| [contract/](../tests/contract/) | ¿Cada pieza cumple su promesa? | 49 pruebas: 16 eventos + envoltura + rechazos, política y su sincronía con el corpus, I3, y el constructor de eventos de `sdn_common` (RNF-12) |
| [integration/](../tests/integration/) | ¿Las piezas funcionan juntas? | Pruebas de servicio del IAM y del Registry con TestClient (eventos capturados, credenciales jamás publicadas); contra LDAP/RADIUS reales llega con el slice |
| [e2e/](../tests/e2e/) | ¿El sistema cumple su propósito? | (pendiente) el flujo completo de un incidente en el slice |

**Por qué existe:** porque las campañas de la etapa 3 (R4, permisos, resiliencia) necesitan evidencia reproducible, no demostraciones manuales.

### 5.6 `docs/` — la documentación de este repositorio

| Archivo | Qué es |
|---|---|
| [01-mapa.md](01-mapa.md) | Este documento: la estructura y sus hilos |
| [02-estado.md](02-estado.md) | Avances y pendientes, con fechas — se actualiza en cada cierre |
| [03-formatos.md](03-formatos.md) | Tutorial de YAML, JSON, OpenAPI y Compose para quien nunca los vio |
| [adr/](adr/) | Decisiones de código que no se deducen del código (se llenan al decidir) |
| [runbooks/](runbooks/) | Procedimientos operativos paso a paso: [01-despliegue-del-slice.md](runbooks/01-despliegue-del-slice.md) — el día-D, de las VMs recién entregadas al entorno verificado |

El corpus de arquitectura **no** está aquí: vive en [`../../docs/fases/`](../../docs/fases/) y se enlaza, no se copia. Los nombres de estos archivos sí están en español y numerados por orden de lectura — es la excepción deliberada a la regla de idioma, documentada en [`../CLAUDE.md`](../CLAUDE.md).

## 6. Los hilos: cómo se conecta todo

Cinco flujos cruzan las capas. Cada pieza existe porque uno de ellos la necesita.

### 6.1 El hilo de la política — de la decisión a la ejecución

```text
implementation/policy/permisos.yaml  (etapa 0, corpus; nombre del corpus)
        │  copia operativa
        ▼
policy/permissions.yaml ──► contracts/policy/permissions.schema.json  (la forma)
        │                          │
        │                          ▼
        │                  policy/tools/validate.py  (cumple la forma y
        │                          sus referencias existen)
        ▼
policy/tools/generate_matrix.py ──► matriz rol × permiso (vista humana)
        ▼
services/* (paso 4): el IAM decide, las Políticas aplican, la Auditoría
registra — todos leen el mismo archivo
```

Si un permiso cambia: se edita el YAML, el validador avisa si algo quedó roto, la matriz se regenera y los servicios leen el mismo documento. Nadie vuelve a escribir permisos en código.

### 6.2 El hilo de los contratos — de la promesa a la implementación

```text
corpus: LLD 02_eventos.md ──► contracts/events/*.schema.json
corpus: LLD 01_apis.md   ──► contracts/api/*.openapi.yaml
                    │
                    ▼
        tests/contract/: eventos de ejemplo contra su esquema (RNF-12)
                    ▼
        services/*: publicadores y consumidores que ya saben, antes de
        escribir una línea, qué forma tiene cada mensaje
```

El contrato va primero y el servicio después. Es la diferencia entre integrar por promesa y por ensayo y error.

### 6.3 El hilo de las imágenes — de la descarga a la VM

```text
laptop con internet                      slice (cuando exista)
images.lock (qué imagen, qué digest)
  pull.sh  ──► descarga y fija digests
  verify.sh ──► lo local coincide con el lock
  save.sh  ──► bundles/*.tar + .sha256 ──(ansible)──►  load.sh: verifica
                (disco, no git)                          y carga en la VM
compose/*.yml (referencia por etiqueta; el digest ya quedó
              garantizado por el lock)
```

El digest es la garantía de reproducibilidad: hoy y mañana se usa exactamente la misma imagen.

### 6.4 El hilo del despliegue — de la orden al sistema corriendo

```text
Makefile (puerta única: make deploy, make up, make status…)
   │
   ▼
Ansible site.yml (qué: un play por frente, con etiquetas)
   │  base · images · platform · onos · switches · identity · verify
   ▼
inventory/slice.yml (dónde: las 14 VMs, sus IPs y sus variables)
   ▼
roles/* (cómo: tareas idempotentes por frente)
   ▼
VMs del slice, por SSH sobre ens3
```

La laptop es solo el nodo de control: no ejecuta las VMs, las configura. Las etiquetas permiten repetir un frente sin tocar los demás (`make deploy TAGS=platform`).

### 6.5 El hilo de las pruebas — de la promesa a la evidencia

```text
contract ──► cada pieza cumple su promesa (esquemas, RNF-12)
integration ──► piezas juntas contra dependencias reales
e2e ──► el flujo completo en el slice (R4, permisos, resiliencia)
```

Cada nivel responde a una pregunta distinta y se apoya en el anterior; juntos son la evidencia de la etapa 3.

## 7. Reglas de convivencia

Las reglas completas están en [`../CLAUDE.md`](../CLAUDE.md); aquí el resumen:

- **Idioma:** carpetas, archivos e identificadores de código en inglés; documentación, comentarios y mensajes en español; `docs/` en español y numerado.
- **Toda tarea se ejecuta por `make`**; no hay pasos manuales fuera del Makefile y de Ansible.
- **Nada secreto en el repositorio:** `.env`, `slice.yml` y el vault están ignorados por git.
- **`policy/permissions.yaml` es la copia operativa**, con valores en inglés; su gemelo histórico vive en [`implementation/policy/`](../../implementation/policy/) y la correspondencia de valores está en [`policy/README.md`](../policy/README.md). Se cambian juntos y versionados.
- **Un asunto por archivo:** cada esquema, cada Compose y cada documento tiene un solo tema.

## 8. Trazabilidad

| Documento | Relación |
|---|---|
| [`../README.md`](../README.md) | Puerta de entrada y reglas |
| [`../CLAUDE.md`](../CLAUDE.md) | Reglas de implementación y documentación |
| [`02-estado.md`](02-estado.md) | Qué está avanzado y qué pendiente, con fechas |
| [`03-formatos.md`](03-formatos.md) | Cómo leer YAML, JSON, OpenAPI y Compose |
| [`../../implementation/09_plan_de_construccion.md`](../../implementation/09_plan_de_construccion.md) | El plan que ordena la construcción de todo lo anterior |
