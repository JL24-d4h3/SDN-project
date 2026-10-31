# Plan de construcción del repositorio campus-sdn

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Etapa 2
**Estado:** Borrador formal para revisión

---

## 1. Propósito

Fijar cómo se construye la solución: el repositorio [`campus-sdn`](../campus-sdn/), su estructura, el modelo de imágenes y el orden de trabajo. Este plan aterriza el despliegue de [`05`](05_plan_de_implementacion.md) y los paquetes de trabajo de [`06`](06_plan_de_trabajo_etapa_2.md) y [`07`](07_plan_de_trabajo_etapa_3.md) en código reproducible: cada tarea manual del diseño se convierte en un script, un rol de Ansible o un objetivo de Makefile.

La automatización se escribe completa en la laptop y se ejecuta contra el slice cuando las VMs estén disponibles. Ninguna etapa queda como tarea manual pendiente: lo que no se puede ejecutar hoy se deja preparado y se verifica hasta donde el entorno local lo permite.

## 2. Principio de la automatización

La laptop es el nodo de control: se conecta por SSH a las 14 VMs, copia archivos e imágenes, instala paquetes, levanta contenedores y configura los switches. La laptop no ejecuta las VMs ni crea la topología; eso lo hace el slice.

| La laptop automatiza | Cómo |
|---|---|
| Instalar Docker, Compose y dependencias | rol `base` |
| Copiar repositorio, Compose y entorno | rol `platform` |
| Copiar y cargar las imágenes | rol `images` |
| Levantar y detener los servicios | rol `platform` |
| Configurar OVS en los cuatro switches | rol `switches` |
| Arrancar el clúster ONOS y sus apps | rol `onos` |
| Instalar flujos base F1–F3 por la API de ONOS | rol `switches` |
| Ejecutar salud y verificación | rol `verify` |

| El slice y la universidad proveen | Cuándo |
|---|---|
| Las 14 VMs, sus sabores y NICs | antes de H0 |
| La NIC de espejo hacia el sensor | H0 |
| Acceso VPN/SSH y credenciales | antes de H0 |
| Un switch PicOS físico por su propia CLI, si el slice no es OVS | H0 |

Decisiones:

- Ansible es el único ejecutor; el Makefile es la única puerta de entrada.
- Todo es idempotente: repetir el playbook no rompe nada.
- La verificación es una etiqueta del playbook (`verify`), no un paso manual.

## 3. Alcance y nombre

El repositorio se llama **campus-sdn** y vive en `project/campus-sdn/`, dentro del repositorio Git actual: un solo historial, sin `.git` anidado. El corpus de diseño no se mueve.

| Estructura | Qué contiene | Dónde vive |
|---|---|---|
| Corpus de diseño | Fases A–H, flujos, acceso, planes | `docs/`, `flows/`, `access/`, `implementation/` |
| Repositorio de construcción | Contratos, servicios, política, despliegue, pruebas | `campus-sdn/` |

## 4. Estructura del repositorio

```text
campus-sdn/
├── README.md
├── Makefile
├── .gitignore
├── contracts/
│   ├── events/                 # esquemas de eventos del catálogo D-08
│   ├── api/                    # OpenAPI de I2 e I7
│   └── policy/                 # esquema JSON de la política
├── services/
│   ├── common/                 # esqueleto compartido por los diez servicios
│   ├── portal/
│   ├── iam/
│   ├── registry/
│   ├── monitor/
│   ├── detection/
│   ├── incidents/
│   ├── policies/
│   ├── audit/
│   ├── console/
│   └── sensor_adapter/
├── policy/
│   ├── permissions.yaml        # fuente de verdad operativa (etapa 0)
│   ├── profiles.yaml           # derivación por generar
│   └── tools/                  # generate_matrix.py y validate.py
├── deploy/
│   ├── compose/                # un archivo por VM de plataforma y ONOS
│   ├── images/
│   │   ├── images.lock         # referencia y digest de cada imagen
│   │   ├── pull.sh             # descarga y fija digests
│   │   ├── verify.sh           # compara digests locales con el lock
│   │   ├── save.sh             # empaqueta bundles con suma
│   │   ├── load.sh             # carga y verifica en la VM
│   │   └── bundles/            # tarballs; ignorado por git
│   ├── ansible/
│   │   ├── ansible.cfg
│   │   ├── inventory/          # slice.example.yml versionado; slice.yml ignorado
│   │   ├── playbooks/          # site.yml con etiquetas por frente
│   │   └── roles/              # base, images, platform, onos, switches, identity, verify
│   └── env/                    # .env.example; el .env real se ignora
├── tests/
│   ├── contract/               # contratos y esquemas
│   ├── integration/            # servicios contra dependencias reales
│   └── e2e/                    # extremo a extremo en el slice
└── docs/
    ├── estado.md               # avances y pendientes del proyecto
    ├── runbooks/               # procedimientos operativos
    └── adr/                    # decisiones de código
```

| Carpeta | Qué guarda | Qué no guarda |
|---|---|---|
| `contracts/` | Esquemas de eventos, OpenAPI de I2/I7 y esquema de la política | Implementación |
| `services/` | Código, `Dockerfile` y pruebas de cada servicio; `common/`, lo compartido | Configuración del slice |
| `policy/` | `permissions.yaml`, `profiles.yaml` y herramientas de validación | Lógica de negocio |
| `deploy/` | Compose, lock de imágenes, scripts, Ansible y plantilla de entorno | Binarios de imágenes |
| `tests/` | Pruebas de contrato, integración y extremo a extremo | Datos reales |
| `docs/` | Estado, runbooks y decisiones de código | Corpus de arquitectura |

Mejoras respecto a la primera propuesta:

- `deploy/scripts/` se elimina: Makefile y Ansible son los ejecutores; menos capas y un solo camino.
- `services/common/` concentra lo compartido (configuración, healthcheck, cliente de RabbitMQ, acceso a PostgreSQL) para no escribirlo diez veces.
- `docs/02-estado.md` registra dentro del repositorio lo avanzado y lo pendiente.
- `images.lock` es JSON: lo leen los scripts con la biblioteca estándar, sin dependencias externas.

## 5. Imágenes y bundles

Git guarda la descripción de las imágenes, no los binarios. El lock fija nombre, referencia y digest; los bundles son el transporte hacia el slice y no se versionan.

```json
{
  "version": 1,
  "images": [
    {"name": "onos",       "ref": "onosproject/onos:2.7.0",                "digest": "", "used_by": ["onos-1", "onos-2", "onos-3"]},
    {"name": "rabbitmq",   "ref": "rabbitmq:3.13-management",              "digest": "", "used_by": ["s4"]},
    {"name": "postgres",   "ref": "postgres:16",                           "digest": "", "used_by": ["s3"]},
    {"name": "freeradius", "ref": "freeradius/freeradius-server:3.2.10",   "digest": "", "used_by": ["s1"]},
    {"name": "openldap",   "ref": "osixia/openldap:1.5.0",                 "digest": "", "used_by": ["s1"]},
    {"name": "prometheus", "ref": "prom/prometheus:v2.53.0",               "digest": "", "used_by": ["s2"]},
    {"name": "grafana",    "ref": "grafana/grafana:11.1.0",                "digest": "", "used_by": ["s2"]},
    {"name": "suricata",   "ref": "jasonish/suricata:7.0",                 "digest": "", "used_by": ["s2"]}
  ]
}
```

Los digests se completan en el primer `pull.sh`; a partir de ahí toda descarga y toda verificación usa el digest, no la etiqueta. chrony y DNS se instalan como paquetes del sistema en el rol `base`, no como imágenes de terceros. Los diez servicios propios se construyen con `Dockerfile` desde `python:3.12-slim`; no se descargan.

| Script | Qué hace | Dónde corre |
|---|---|---|
| `pull.sh` | Descarga cada imagen del lock y fija el digest que falta | laptop con internet |
| `verify.sh` | Compara el digest local con el fijado | laptop |
| `save.sh` | `docker save` a `bundles/` con `.sha256` | laptop |
| `load.sh` | Verifica la suma y `docker load` en la VM | cada VM |

```text
Laptop con internet                        Slice
  make images-pull  ──► digest fijado
  make images-verify──► OK
  make images-save  ──► bundles/*.tar
                            │  scp/rsync por ens3
                            ▼
                        make images-load (por VM)
                        make up SERVICE=s1
                        make status
```

- Los bundles se copian, se cargan y se borran de la VM: el disco es la restricción más ajustada del slice.
- No se monta un `registry:2` local: para ocho imágenes, `save/load` es más simple y no añade un servicio que debe estar sano antes que los demás. Si el ciclo de construcción de imágenes propias se vuelve frecuente, se revisa la decisión.

## 6. Política y contratos

- `policy/permissions.yaml` es la copia operativa del cierre de la etapa 0; la fuente histórica sigue en [`implementation/policy/`](policy/). Cualquier cambio se versiona en el YAML y se propaga a la matriz con el generador.
- `policy/profiles.yaml` se deriva del YAML cuando los servicios consuman perfiles por separado; queda listado en `docs/02-estado.md`.
- `contracts/policy/` guarda el esquema JSON que valida ambos archivos.
- Los contratos se congelan antes de escribir servicios: el orden es contrato → prueba de contrato → servicio.

## 7. Orden de construcción

| Paso | Qué se construye | Se escribe | Se ejecuta | Hito / WP |
|---|---|---|---|---|
| 0 | Repositorio, Makefile, lock y scripts de imágenes | ahora | ahora, en la laptop | H2 / WP2.7 |
| 1 | Contratos, política y validación | ahora | ahora, validación local | H2 / WP2.4–2.5 |
| 2 | Stack base S3/S4: Compose, Ansible, healthchecks | ahora | VMs S3 y S4 | H2 / WP2.4 |
| 3 | ONOS y switches: clúster de 3 nodos, 4 OVS, flujos base | ahora | VMs ONOS y switches | H3 / WP2.2–2.3 |
| 4 | Identidad extremo a extremo | ahora | VM S1 o local | H5 / WP2.5 |
| 5 | Servicios restantes y flujos R4/R5 | ahora | todas las VMs | H4/H6 / WP2.6, WP3.x |

Reglas:

- La columna de hito dice cuándo se verifica en el slice, no cuándo se programa: todo se escribe ahora.
- El orden vertical evita depurar catorce VMs a la vez y respeta las dependencias reales.
- Los pasos 0 y 1 no dependen del slice; del 2 al 5 se prueba localmente lo que no exige topología.
- La identidad va primero porque valida los cuatro roles y es el flujo con más código propio.

## 8. Ejecución

| Objetivo | Acción |
|---|---|
| `make help` | Objetivos disponibles |
| `make images-pull` | Descarga y fija digests |
| `make images-verify` | Digests locales contra el lock |
| `make images-save` | Bundles en `deploy/images/bundles/` |
| `make images-load IMAGES=onos` | Carga uno o varios bundles en la VM |
| `make ping` | Conectividad con todas las VMs |
| `make deploy TAGS=platform` | Ejecuta `site.yml` completo o por etiqueta |
| `make up` / `make down` | Levanta o detiene los servicios |
| `make status` | Salud de contenedores y servicios |
| `make test` | Pruebas de contrato e integración |
| `make verify` | Verificación completa |

`site.yml` organiza los roles por etiqueta: `base`, `images`, `platform`, `onos`, `switches`, `identity`, `verify`; así un frente se ejecuta o se repite sin tocar los demás.

Prerrequisitos:

- Laptop: Docker, Ansible, clave SSH y `tmux` para ejecuciones largas; si la laptop se suspende, el playbook se corta.
- Slice: 14 VMs con SSH, Python 3 y `sudo`; las IPs de gestión en `ens3`; la NIC de espejo; acceso VPN.
- Secretos: Ansible Vault o variables de entorno; nunca en el repositorio. El `slice.yml` real y el `.env` están ignorados por git.
- Primera acción con el slice: H0 — inventario y capacidades según [`04`](04_capacidades_del_switch.md) y [`08`](08_inventario_del_slice.md), incluida la re-sonda de cookie/sFlow/NetFlow y el espejo hacia el sensor.

## 9. Decisiones cerradas

- Nombre del repositorio: **campus-sdn**.
- Un solo repositorio Git; sin `.git` anidado.
- `docker save/load` para llevar imágenes al slice; registro local solo si el ciclo de construcción lo exige.
- Lock de imágenes en JSON, con digests fijados en el primer pull.
- Ansible como único ejecutor y Makefile como única puerta.
- Corte vertical de identidad como primer flujo construido.
- Este documento es el plan; el estado vivo está en `campus-sdn/docs/estado.md`.

## 10. Trazabilidad

| Documento | Relación |
|---|---|
| [`05_plan_de_implementacion.md`](05_plan_de_implementacion.md) | Diseño del despliegue que este plan convierte en código |
| [`06_plan_de_trabajo_etapa_2.md`](06_plan_de_trabajo_etapa_2.md) | Paquetes de trabajo de despliegue |
| [`07_plan_de_trabajo_etapa_3.md`](07_plan_de_trabajo_etapa_3.md) | Paquetes de trabajo de ejecución y medición |
| [`04_capacidades_del_switch.md`](04_capacidades_del_switch.md), [`08_inventario_del_slice.md`](08_inventario_del_slice.md) | Verificación del slice que precede al despliegue |
| [`00_cierre_etapa_0_permisos.md`](00_cierre_etapa_0_permisos.md), [`policy/`](policy/) | Fuente de `campus-sdn/policy/` |
| [`../campus-sdn/README.md`](../campus-sdn/README.md) | Entrada al código y al estado |
