# VMs y contenedores

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

Hay **dos formas de ejecución, y la regla de decisión es una sola** ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §1): **quien necesita identidad de red propia es una máquina virtual; quien es un servicio sin identidad de red es un contenedor.**

- **Contenedor** — el servicio de la plataforma: un proceso aislado con su responsabilidad (P3), composición declarativa y reproducible (RNF-11). Un contenedor comparte la identidad de red de su anfitrión; no sirve para representar un dispositivo.
- **Máquina virtual** — todo lo que la red debe ver como un equipo real: MAC propia, IP propia, conexión por un puerto distinto (R1.1). Hosts, servidores, atacantes y el sensor perimetral son VMs.

El hipervisor es el del servidor del laboratorio (KVM/libvirt); los contenedores se componen de forma declarativa (Compose) — el conjunto completo se levanta desde la definición versionada.

## 2. Los contenedores, en dos familias (la vista general)

El plano de contenedores se lee **por jerarquía**: primero las dos familias que lo forman —los servicios de la plataforma y la infraestructura que los sostiene— y recién en §3 el producto concreto que materializa cada papel.

**La plataforma.** Los servicios que el diseño descompuso ([`D-04`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md) §3), uno por contenedor, imagen propia:

| Servicio | Responsabilidad | CPU / RAM |
|---|---|---|
| Portal | La única superficie que las poblaciones alcanzan (I3) | 1 / 512 MB |
| IAM | Identidad, sesiones y ligadura al dispositivo | 1 / 512 MB |
| Registro | Catálogo e historial de dispositivos privilegiados | 1 / 512 MB |
| Monitor | Observación del plano de datos y línea base (I8) | 1 / 1 GB |
| Detección | Clasificación de anomalías | 1 / 512 MB |
| Incidentes | Ciclo de vida de cada incidente | 1 / 512 MB |
| Políticas | Respuesta de la escalera y elevaciones | 1 / 512 MB |
| Auditoría | Registro de quién, qué, cuándo y por qué | 1 / 512 MB |
| Consola | El cliente administrativo (I7) | 1 / 512 MB |
| Adaptador del sensor | Lleva las alertas del sensor perimetral al bus | 1 / 256 MB |

**La infraestructura.** Los papeles que sostienen a los servicios, cada uno materializado por un producto — el producto es el detalle, el papel es lo que el sistema necesita:

| Papel | Se materializa con |
|---|---|
| Controlador SDN | ONOS |
| Intermediario de eventos | RabbitMQ |
| Persistencia | PostgreSQL |
| Identidad institucional (IdP simulado) | FreeRADIUS + OpenLDAP |
| Sensor perimetral (IDS) | Suricata — en máquina virtual, no contenedor (§4) |
| Tiempo | chrony |
| Visualización | Grafana |
| DNS del entorno | dnsmasq |

## 3. La materialización: producto, imagen y recursos (la vista particular)

La tabla de §2 nombra papeles; esta fija **con qué producto y qué recursos** queda cada uno en el prototipo. Las versiones se fijan en el primer despliegue y se registran en la definición versionada ([`06`](06_dependencias.md) §4):

| Papel → producto | Imagen (punto de partida) | CPU | RAM | Expone (solo gestión) |
|---|---|---|---|---|
| Controlador → ONOS | `onosproject/onos:2.7` | 2 | 2 GB | 6653 (southbound), 8181 (I2) |
| Intermediario → RabbitMQ | `rabbitmq:3.13-management` | 1 | 512 MB | 5672, 15672 |
| Persistencia → PostgreSQL | `postgres:16` | 1 | 1 GB | 5432 |
| Identidad → FreeRADIUS | `freeradius/freeradius-server:3.2` | 1 | 256 MB | 1812/1813 UDP |
| Identidad → OpenLDAP | `osixia/openldap:1.5` | 1 | 256 MB | 389 |
| Tiempo → chrony | `cturra/ntp:4.2`-equivalente | 0,5 | 128 MB | 123 UDP |
| Visualización → Grafana | `grafana/grafana:11` | 1 | 512 MB | 3000 |
| DNS → dnsmasq | `jpillora/dnsmasq`-equivalente | 0,5 | 128 MB | 53 UDP/TCP |

Los servicios de §2 corren sobre imagen propia — Python 3.12, un solo ecosistema ([`G-07`](../G-Diseno_de_bajo_nivel-LLD/07_detalles_de_implementacion.md) §1)— y exponen sus puertos solo en el segmento de gestión. El sensor no aparece en esta tabla: no es un contenedor, vive en su máquina virtual (§4).

**Reglas del plano de contenedores.** Ningún contenedor se publica fuera del segmento de gestión: el portal es la única superficie que las poblaciones alcanzan, y lo alcanzan **a través del plano de datos**, no por exposición directa. Las versiones se fijan en el primer despliegue y se registran — una repetición futura no compara contra otro software ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §4).

## 4. Las máquinas virtuales: los dispositivos de la red

| Grupo | VMs | MAC (convención) | IP | vCPU / RAM |
|---|---|---|---|---|
| Hosts académicos | 16 | `52:54:00:01:01`–`52:54:00:01:10` | 10.1.0.10–.25 | 1 / 1 GB |
| Hosts de operadores | 2 | `52:54:00:04:01`–`.02` | 10.1.0.30–.31 | 1 / 1 GB |
| Atacante interno | 1 | `52:54:00:03:02` | 10.1.0.50 | 1 / 1 GB |
| Atacante externo | 1 | `52:54:00:03:01` | 10.3.0.10 | 1 / 1 GB |
| Servidores de servicio | 3 | `52:54:00:02:01`–`.03` | 10.2.0.10–.12 | 1 / 1 GB |
| Sensor perimetral (Suricata) | 1 | — (2 NIC: espejo RX + gestión) | 10.0.0.27 | 2 / 2 GB |

- **Convención de MAC** (`52:54:00:` local, tercer octeto = clase, cuarto = correlativo): legible en cualquier captura y en el registro de asociaciones. La clase de un dispositivo se ve en su MAC — útil para el reporte, jamás como criterio de seguridad (la política mira el catálogo y las reglas, no el prefijo).
- **Los servidores de servicio** representan los activos protegidos de R2; su clasificación (general / privilegiado / crítico) es la de [`A-02`](../A-Modelo_de_dominio/02_recursos_y_servicios.md).
- **El sensor** tiene dos NIC: la del espejo (solo recepción, sin IP) y la de gestión. Fuera del camino de reenvío (P8).
- **Las cinco NIC del servidor:** NIC-A ↔ A3 p6 (trunk de gestión, VLAN 20) · NIC-B ↔ A1 p20 (hosts virtuales académicos) · NIC-C ↔ A4 p4 (atacante externo, VLAN 40) · NIC-D = el espejo desde A4 p47, entregada a la VM del sensor (su NIC de gestión va por el puente de NIC-A) · NIC-E ↔ A2 p6 (operadores, atacante interno y el puente de la demostración de `MAC_Moved` entre A1 y A2). El plano puerto a puerto está en [`05`](05_puertos.md).
- **Total del servidor:** 24 VMs (23 de host a 1 GB + el sensor a 2 GB, ≈ 25 GB) y contenedores ≈ 8 GB → dimensionamiento de 32 GB declarado en [`01`](01_infraestructura_fisica.md) §2, con la variante recortada de 16 GB.

## 5. La referencia: la misma regla a escala

En el campus real la regla no cambia, cambia el soporte: los servicios corren en servidores dedicados de la administración (no en un único hipervisor), los hosts son equipos reales de las personas, y el sensor perimetral es un equipo propio del punto de espejo. Lo que el prototipo demuestra —que cada pieza tiene identidad y responsabilidad separadas— es exactamente lo que el despliegue hereda.

## 6. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Recrear el entorno completo desde la definición versionada | Sin pasos manuales; mismo estado de partida | RNF-11 |
| Identidad de red de cada VM (MAC, IP, puerto) | Corresponde a [`05`](05_puertos.md) y al registro de asociaciones | R1.1 |
| Servicios alcanzables solo desde gestión | El portal es la única superficie visible desde BASE | RA-09 |
| Repetir un escenario con los mismos parámetros | Métricas comparables entre corridas | RNF-12 |
