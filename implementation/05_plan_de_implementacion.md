# Plan de implementación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Etapa 2
**Estado:** Borrador formal para revisión

---

## 1. Propósito

Definir cómo se lleva la solución al slice de la nube privada de la universidad sin perder los estilos, los patrones ni los requisitos de calidad de la arquitectura de referencia. El plan reduce el número de dispositivos, conserva la redundancia y la disponibilidad, concentra el esfuerzo en el switch y deja explícito qué se automatiza con Ansible y qué se implementa como servicio.

Este documento es el **diseño de la etapa 2**. La secuencia ejecutable —paquetes de trabajo, dependencias, entregables y criterios de aceptación— está en [`06_plan_de_trabajo_etapa_2.md`](06_plan_de_trabajo_etapa_2.md); la campaña de ejecución y medición está en [`07_plan_de_trabajo_etapa_3.md`](07_plan_de_trabajo_etapa_3.md). La construcción del repositorio de código y su automatización están en [`09_plan_de_construccion.md`](09_plan_de_construccion.md).

## 2. Relación con la arquitectura de referencia

La arquitectura de referencia usa diez switches Pica8: dos de núcleo, dos de distribución, cuatro de acceso, dos de control y servicios. El slice no necesita diez switches para demostrar la solución. El plan adopta un **perfil de despliegue de cuatro switches** y un **mínimo de tres**, conservando:

- dos nodos de núcleo con enlace directo;
- acceso dual-homed a ambos núcleos;
- el borde externo y el espejo del sensor en puertos de NC2;
- servidores de servicios conectados a los accesos;
- clúster ONOS de tres nodos;
- las mismas políticas, perfiles y prioridades.

La reducción es de despliegue, no de arquitectura: los roles, los planos y las decisiones se mantienen. La diferencia se documenta en la tabla de adaptaciones.

| Elemento de referencia | En el slice | Motivo |
|---|---|---|
| 10 switches | 4 switches (mínimo 3) | Recursos del slice; se conservan núcleo y acceso |
| C1/C2 como bloque de servicios | Servidores S1–S4 conectados a A1/A2 | Menos switches; la separación se mantiene por VLAN y NIC |
| A1–A4 | A1 y A2 | Dos accesos dual-homed bastan para redundancia y crecimiento |
| A3 libre | Puerto libre en NC1/NC2 | Crecimiento |
| A4 p47 espejo | NC2: puerto de espejo al sensor | El borde ve el tráfico externo que interesa a R5 |
| Servidor único KVM | 14 VMs: 4 switches, 3 ONOS, 4 plataforma y 3 hosts | Se conserva la separación por afinidad |

## 3. Topología del slice

### 3.1 Perfil del slice

```text
                    Plano de gestión (ens3, 192.168.0.0/24)
                              ONOS-1/2/3

        ┌──────────────┐                    ┌──────────────┐
        │     NC1      │════════════════════│     NC2      │
        │    núcleo    │                    │ núcleo+borde │
        └───┬──────┬───┘                    └───┬──────┬───┘
            │      │                            │      │
         ┌──┴──┐ ┌─┴───┐                 ┌──────┘      └──────┐
         │ A1  │ │ A2  │                 │                    │
         └──┬──┘ └──┬──┘              h3 (VLAN 30)      S2 espejo
            │       │
        h1 + S1/S2  h2 + S3/S4
```

A1 y A2 son dual-homed a NC1 y NC2; el diagrama muestra un enlace por acceso para no cruzar líneas. NC2 concentra el borde y el espejo: es el compromiso del perfil de cuatro switches, que conserva la redundancia de núcleo y de acceso y sacrifica el switch de borde dedicado.

### 3.2 Enlaces

| Enlace | Extremo A | Extremo B | Función | Redundancia |
|---|---|---|---|---|
| L01 | NC1 | NC2 | Núcleo | Sí |
| L02 | NC1 | A1 | Acceso | Sí, con L03 |
| L03 | NC2 | A1 | Acceso | Sí, con L02 |
| L04 | NC1 | A2 | Acceso | Sí, con L05 |
| L05 | NC2 | A2 | Acceso | Sí, con L04 |
| L06 | A1 | S1/S2 | Servicios | Según NIC |
| L07 | A2 | S3/S4 | Servicios | Según NIC |
| L08 | NC2 | h3 | Frontera | No |
| L09 | NC2 | S2 | Espejo | No |
| L10 | NC1/NC2 | ONOS | Gestión | Según NIC |

El borde y el espejo se concentran en NC2 y no tienen redundancia; se documenta como límite. Los servidores S1/S2 se conectan a A1 y S3/S4 a A2 por puerto de acceso en VLAN 20; si el slice permite una segunda NIC de datos, se dual-homed. Los nodos ONOS usan la red de gestión del slice (ens3, 192.168.0.0/24); la VLAN 100 se conserva para el canal in-band del plano de datos.

### 3.3 Perfil mínimo

Si el slice se recorta a tres switches:

```text
        NC1 ═══════════════ NC2
         ║                   ║
         ╚════════ A1 ═══════╝
```

- NC1 y NC2 conservan el núcleo y la redundancia.
- A1 es el acceso dual-homed.
- El borde y el espejo se conservan en NC2.
- Los servidores S1–S4 se reparten entre NC1, NC2 y A1.
- El perfil mínimo sigue demostrando redundancia, disponibilidad y seguridad; pierde el segundo acceso y la capacidad de crecimiento, que se recupera al volver a cuatro switches.

## 4. Direccionamiento

Se conserva el direccionamiento lógico del corpus y se mapea al del slice.

| Red | Uso | Direcciones |
|---|---|---|
| 10.0.0.0/24 | Gestión | Portal .5, IAM .10, Registro .11, Monitor .12, Detección .13, Incidentes .14, Políticas .15, Auditoría .16, Consola .17, Adaptador .18, ONOS .20/.30/.40, RabbitMQ .21, PostgreSQL .22, FreeRADIUS .23, LDAP .24, chrony .25, Grafana .26, sensor .27, DNS .28, Prometheus .29 |
| 10.1.0.0/24 | Usuarios | Hosts académicos y de laboratorio |
| 10.2.0.0/24 | Servidores | Servidores protegidos |
| 10.3.0.0/24 | Externa | Atacante externo y frontera |
| VLAN 10 | Usuarios | 10.1.0.0/24 |
| VLAN 100 | Gestión | 10.0.0.0/24 |
| VLAN 20 | Servidores | 10.2.0.0/24 |
| VLAN 30 | Frontera | 10.3.0.0/24 |

La tabla de mapeo se completa en el primer laboratorio:

| Dirección lógica | Dirección en el slice | Interfaz | VLAN |
|---|---|---|---|
| 10.0.0.20 | | | 100 |
| 10.0.0.30 | | | 100 |
| 10.0.0.40 | | | 100 |
| 10.0.0.10 | | | 20 |
| 10.1.0.10 | | | 10 |
| 10.3.0.10 | | | 30 |

La gestión del slice usa ens3 en la red del proveedor (192.168.0.0/24); la VLAN 100 (10.0.0.0/24) se conserva para el canal in-band del plano de datos.

## 5. VMs del slice y afinidad

El slice asignado es de catorce VMs: cuatro switches, tres controladores, cuatro de plataforma y tres hosts. Los recursos no tienen sabor fijo y se piden según esta tabla; los valores son el objetivo, no una cuota del proveedor.

| VM | Papel | Servicios | NIC | vCPU | RAM | Disco |
|---|---|---|---|---|---|---|
| NC1 | Núcleo | Open vSwitch | 4 | 1 | 1 GB | 8 GB |
| NC2 | Núcleo, borde y espejo | Open vSwitch | 6 | 1 | 1 GB | 8 GB |
| A1 | Acceso | Open vSwitch | 6 | 1 | 1 GB | 8 GB |
| A2 | Acceso | Open vSwitch | 6 | 1 | 1 GB | 8 GB |
| ONOS-1/2/3 | Controladores | ONOS 2.7, un nodo por VM | 3 × 1 | 3 × 2 | 3 × 2 GB | 3 × 10 GB |
| S1 Identidad | Plataforma | Portal, IAM, Registro, FreeRADIUS, OpenLDAP | 2 | 2 | 4 GB | 12 GB |
| S2 Observabilidad | Plataforma | Monitor, Detección, Adaptador, Prometheus, Grafana, Suricata | 3 | 2 | 6 GB | 20 GB |
| S3 Respuesta | Plataforma | Incidentes, Políticas, Auditoría, PostgreSQL, servidores protegidos | 2 | 2 | 4 GB | 15 GB |
| S4 Gobierno | Plataforma | Consola, RabbitMQ, chrony, DNS | 2 | 2 | 4 GB | 12 GB |
| h1 | Usuario académico | Operador (contenedor macvlan) | 2 | 1 | 1 GB | 8 GB |
| h2 | Atacante interno | — | 2 | 1 | 1 GB | 8 GB |
| h3 | Atacante externo | — | 2 | 1 | 1 GB | 8 GB |

Total: 21 vCPU, 31 GB de RAM y unos 145 GB de disco. Los switches y los hosts son ligeros; el peso está en ONOS (6 GB) y en la plataforma (18 GB).

Las catorce VMs las entrega el slice; el proyecto no crea VMs anidadas. Todo lo que no es una de esas VMs es un contenedor dentro de una de ellas:

- Los **servidores protegidos** son tres contenedores macvlan en S3, con MAC e IP propias en VLAN 20. El switch los ve como hosts; es la forma de conservar R2 sin una VM por servidor.
- El **operador** es un contenedor macvlan en h1, con identidad propia en VLAN 10.
- El **sensor** es un contenedor Suricata en S2, con la NIC de espejo que llega desde NC2. Si el hipervisor no expone esa NIC, se aplica el reemplazo de [`04`](04_capacidades_del_switch.md) §4.3.
- La **frontera** se resuelve con flujos L3 del controlador en NC2; no se dedica una VM ni un contenedor al gateway.

Cada nodo ONOS ocupa su propia VM y corre como un contenedor dentro de ella. Agrupar los tres en una sola VM solo demuestra quórum de proceso; una caída de la VM apaga el clúster y RD4 deja de probar disponibilidad. Si el slice no ofrece tres VMs separadas, se documenta como límite y se solicita antiafinidad.

El disco es el recurso que más aprieta: el controlador actual tiene 5.9 GB con 429 MB libres y la imagen de ONOS ronda 1 GB. Las VMs de ONOS necesitan 10 GB y las de plataforma 12–20 GB; con discos de 6 GB el reparto no entra.

Si el proveedor recorta RAM, el orden es: bajar S2 a 5 GB, fusionar S3 y S4 en una VM de 6 GB y reducir el sensor a 1 GB. El clúster ONOS no baja de tres nodos.

La afinidad es una decisión de despliegue, no de arquitectura. Los diez servicios siguen siendo visibles y separados; viven juntos en una VM por comodidad operativa, no porque formen un solo componente.

## 6. Servicios: construir o adoptar

| Servicio | Estrategia | Base | Notas |
|---|---|---|---|
| Portal | Construir | FastAPI + plantillas o React | I3; pre-sesión y sesión |
| IAM | Construir la orquestación | FreeRADIUS, OpenLDAP, pyotp | I4/I6; RADIUS + LDAP + TOTP |
| Registro | Construir | FastAPI + PostgreSQL | CRUD pequeño; P30/P35 |
| Monitor | Construir el colector | Prometheus, cliente ONOS | I8; métricas y estado |
| Detección | Construir | Python, numpy/pandas | EWMA con piso e histéresis |
| Incidentes | Construir | FastAPI + PostgreSQL | Máquina de estados |
| Políticas | Construir | FastAPI + YAML; OPA opcional | PDP; perfiles y condiciones |
| Auditoría | Construir | FastAPI + PostgreSQL | Cadena de hash; exportación |
| Consola | Construir | React o plantillas | I7; cliente de operación |
| Adaptador del sensor | Construir | Suricata EVE JSON | I5; normaliza eventos |

Productos que se adoptan: ONOS, RabbitMQ, PostgreSQL, Prometheus, Grafana, FreeRADIUS, OpenLDAP, Suricata, chrony, Docker y Ansible. No se adopta una plataforma de microservicios completa: los servicios son pequeños, el equipo es reducido y el foco está en el switch.

## 7. Orquestación

La orquestación es **Docker Compose por servidor + Ansible para aprovisionar**. Es suficiente para cuatro VMs de plataforma y diez servicios, y mantiene el despliegue legible.

```text
deploy/
  compose/
    s1_identidad.yml
    s2_observabilidad.yml
    s3_respuesta.yml
    s4_gobierno.yml
  ansible/
    inventory/
      hosts.yml
      group_vars/
    playbooks/
      00_bootstrap.yml
      01_switches.yml
      02_onos.yml
      03_services.yml
      04_verify.yml
      05_backup.yml
    roles/
      common/
      switch/
      onos/
      service/
      verify/
```

Cada archivo de Compose declara redes, volúmenes, variables de entorno y dependencias. Las credenciales se inyectan desde Ansible Vault o desde variables de entorno; no se escriben en el repositorio.

Kubernetes no se usa en el prototipo: añade un plano de control, un scheduler y un modelo de red que no se necesitan para cuatro VMs, y desvía el esfuerzo del switch. Si más adelante se requiere orquestación multi-nodo, k3s es la transición natural; el diseño de servicios no cambia.

Los nodos ONOS tampoco se orquestan con Compose ni con Kubernetes. Cada VM ejecuta su instancia mediante `02_onos.yml` y la membresía la forma el propio clúster de ONOS (Atomix/Raft) sobre la red de gestión del slice (ens3, 192.168.0.0/24); en la referencia, sobre la VLAN 100. Un orquestador de contenedores no participa en ese quórum y no mejora la disponibilidad del controlador.

## 8. Estructura del código

```text
sdn-project/
├── contracts/
│   ├── events/            # esquemas de eventos del catálogo D-08
│   ├── api/               # OpenAPI de I2 e I7
│   └── policy/            # esquema del archivo de permisos
├── services/
│   ├── portal/
│   ├── iam/
│   ├── registro/
│   ├── monitor/
│   ├── deteccion/
│   ├── incidentes/
│   ├── politicas/
│   ├── auditoria/
│   ├── consola/
│   └── adaptador_sensor/
├── policy/
│   ├── permisos.yaml
│   └── perfiles.yaml
├── deploy/
├── tests/
├── docs/
└── implementation/
```

Cada servicio respeta las mismas capas:

```text
servicio/
  app/            # API, dependencias, arranque
  domain/         # entidades, reglas, interfaces de repositorio
  infra/          # PostgreSQL, RabbitMQ, cliente del controlador
  tests/
```

### 8.1 Pipe and filter

La cadena de detección y respuesta es una tubería de filtros:

```text
Monitor → Detección → Incidentes → Políticas → Controlador
   │          │            │            │            │
 métrica    alerta      incidente     decisión      FLOW_MOD
```

Cada filtro tiene una responsabilidad, recibe un evento, produce otro y no conoce los detalles internos del siguiente. El broker es la tubería; el contrato es el evento.

### 8.2 Broker

RabbitMQ con una cola por incidente y una cola de auditoría. Entrega al menos una vez, confirmación del consumidor, reentrega con límite y cola de mensajes muertos. Cada evento lleva `event_id`, `type`, `occurred_at`, `correlation_id`, `producer` y `payload`; el consumidor es idempotente por `event_id`. Los eventos no contienen secretos.

### 8.3 Repository

Cada servicio tiene su propia base o su propio esquema; no hay base compartida. El dominio define la interfaz del repositorio y la infraestructura la implementa. Las relaciones entre servicios se hacen por identificadores (`incident_id`, `session_id`, `device_id`), no por claves foráneas entre bases.

### 8.4 Capas

| Capa | Responsabilidad | Ejemplo |
|---|---|---|
| API | Validar la petición, autenticar, invocar el caso de uso | `POST /incidents/{id}/mitigate` |
| Aplicación | Orquestar el caso de uso y las transacciones | `MitigateIncident` |
| Dominio | Reglas y entidades | `Incident`, `Mitigation`, `Permission` |
| Infraestructura | Persistencia, mensajería, controlador | `PostgresIncidentRepository`, `OnosClient` |

## 9. Ansible

| Playbook | Qué hace | Qué no hace |
|---|---|---|
| `00_bootstrap.yml` | Usuarios, claves SSH, chrony, Docker, firewall, límites | No decide políticas |
| `01_switches.yml` | VLANs, puertos, OpenFlow, espejo, modo seguro, respaldo | No instala flujos de sesión |
| `02_onos.yml` | Java, ONOS, clúster, aplicaciones, claves | No decide perfiles |
| `03_services.yml` | Compose, imágenes, variables, secretos | No decide permisos |
| `04_verify.yml` | Pruebas de humo y capacidades | No corrige fallos |
| `05_backup.yml` | PostgreSQL, configuración de ONOS y de switches | No restaura sin autorización |

Ansible se usa donde el aprovisionamiento es repetible e idempotente. Las decisiones de runtime —qué perfil corresponde a una sesión, qué mitigación se aplica, qué permiso se concede— viven en los servicios y en el controlador, no en Ansible.

## 10. Modo seguro del switch

### 10.1 Plano de gestión

- SSH con claves; sin telnet ni HTTP.
- AAA contra RADIUS o TACACS+ si el switch lo soporta; si no, cuentas locales con clave fuerte y rotación.
- ACL de gestión: solo las direcciones de los servidores de operación.
- VLAN de gestión separada; el tráfico de usuarios no la alcanza.
- NTP/chrony, syslog centralizado y respaldo de configuración.
- Firmware firmado y actualizaciones programadas.
- Servicios no usados deshabilitados.

### 10.2 Plano de datos

- Puertos no usados deshabilitados y en VLAN de cuarentena.
- Port security por MAC.
- DHCP snooping y ARP inspection si están disponibles.
- Storm control y BPDU guard/root guard.
- VLAN 1 no usada: es la VLAN por defecto, viaja sin etiquetar como nativa y es la superficie clásica de salto de VLAN; la gestión usa la VLAN 100 y el tráfico de usuarios la VLAN 10.

### 10.3 Plano de control

- OpenFlow aceptado solo desde las direcciones del clúster ONOS.
- TLS si el switch y el controlador lo soportan; si no, red de gestión aislada.
- Claves y certificados propios, rotados.
- Mínimo privilegio para las cuentas de automatización.

En el slice virtual se verifica qué funciones existen. Si alguna no está, se prioriza el aislamiento de gestión, las claves SSH, las ACL y el registro; las reglas SDN cubren la seguridad del usuario y el modo seguro cubre el switch.

## 11. Requisitos de calidad

| Requisito | Cómo se cumple | Cómo se prueba |
|---|---|---|
| Redundancia | NC1↔NC2; acceso dual-homed; 3 ONOS | Fallo de enlace, de switch y de nodo |
| Disponibilidad | Reconciliación, reelección de maestro, reinicio de servicios | Corte controlado y recuperación |
| Escalabilidad | Añadir A3 y hosts; mismos perfiles | Alta de host y de switch; TCAM |
| Seguridad | Anti-spoofing, aislamiento, mitigación, permisos, auditoría | Pruebas de permisos y de flujo |
| Observabilidad | Prometheus, Grafana, espejo/IDS, auditoría | Panel y alerta de prueba |
| Rendimiento | Presupuesto de mitigación y de instalación | Medición de latencia y convergencia |

## 12. Hitos

| Hito | Semana | Entregable |
|---|---|---|
| H0 | 1 | Slice verificado; capacidades y direcciones mapeadas |
| H1 | 1–2 | Etapa 0 cerrada: matriz, YAML y pruebas |
| H2 | 2–3 | Esqueleto de servicios, contratos, Compose y CI |
| H3 | 3–4 | Clúster ONOS, switches, I2 y flujos base |
| H4 | 4–5 | Perfiles, elevación, mitigación y prioridades |
| H5 | 5–6 | Extremo a extremo, auditoría, detección y sensor |
| H6 | 6–7 | Medición de requisitos y ajuste |
| H7 | 7–8 | Documentación, demostración y defensa |

## 13. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| El slice no soporta espejo | Media | Alto | Verificar en H0; sFlow/NetFlow o tap; degradar R5 |
| RAM insuficiente | Media | Alto | Perfil mínimo; medir y recortar servicios |
| El IdP no es alcanzable | Media | Medio | FreeRADIUS + OpenLDAP locales |
| Las tres VMs ONOS caen en el mismo hipervisor | Media | Medio | Solicitar antiafinidad; si no se puede, documentar el límite |
| Tiempo insuficiente | Alta | Alto | Priorizar permisos, flujos y switch; posponer P35/P36 y la interfaz |
| Cambios del slice | Media | Medio | Inventario y mapa de puertos versionados |
| Imágenes no disponibles | Media | Medio | Registro local o `docker save/load` |
| Alcance excesivo | Media | Alto | Sin Kubernetes, sin SIEM, sin NAC, sin inalámbrico |

## 14. Fuera de alcance

- La topología completa de diez switches; queda como referencia.
- Mininet y la emulación de gran escala.
- Kubernetes y la orquestación multi-nodo.
- La integración con el IdP institucional en producción.
- 802.1X en puertos sensibles; queda documentado y fuera del prototipo.
- P35 y P36 a nivel funcional.
- Un quinto rol de auditor.

## 15. Trazabilidad

| Documento | Relación |
|---|---|
| [`00_cierre_etapa_0_permisos.md`](00_cierre_etapa_0_permisos.md) | Decisiones de permisos |
| [`02_matriz_rol_permiso.md`](02_matriz_rol_permiso.md) | Matriz que los servicios aplican |
| [`03_plan_de_pruebas_permisos.md`](03_plan_de_pruebas_permisos.md) | Pruebas de aceptación |
| [`04_capacidades_del_switch.md`](04_capacidades_del_switch.md) | Verificación del slice |
| [`01_infraestructura_fisica.md`](../docs/fases/H-Despliegue/01_infraestructura_fisica.md) | Infraestructura de referencia |
| [`02_vms_y_contenedores.md`](../docs/fases/H-Despliegue/02_vms_y_contenedores.md) | Servicios y afinidad |
| [`03_red.md`](../docs/fases/H-Despliegue/03_red.md) | Direccionamiento y VLANs |
