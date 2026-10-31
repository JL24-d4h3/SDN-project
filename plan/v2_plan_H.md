# Método y mapa del despliegue

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

**Desplegar es asignar cada elemento lógico a una máquina, una red y un orden reales.** La fase G escribió qué corre **dentro** de cada componente; esta fase define **las máquinas, la red y la secuencia** sobre las que corre. Materializa el entorno que [`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) decidió: contenedores para los servicios, máquinas virtuales para quien necesita identidad de red propia, el switch físico como plano de datos.

El despliegue tiene **dos vistas**, y la distinción es la de [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md):

- **El prototipo** — lo que el proyecto **despliega** en el laboratorio y sobre lo que valida. Toda la serie lo describe al detalle de puerto y parámetro.
- **La referencia** — el campus que la solución describe. Se **analiza por diseño, no se despliega** ([`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md) §4): redundancia de nodos y enlaces, el clúster del controlador repartido en hosts físicos distintos, canal in-band, feeds externos de inteligencia, cifrado en reposo y política de respaldo — exactamente lo que [`F-09`](../F-Decisiones_tecnologicas/09_sintesis_y_trazabilidad.md) §5 dejó para esta fase. Cada documento la recoge en su sección final, con sus condiciones de habilitación.

**La regla de lectura** es la misma que en G ([`G-00`](../G-Diseno_de_bajo_nivel-LLD/00_metodo_y_mapa.md) §1): primero lo general —el plano, la jerarquía, el criterio— y luego lo particular —la máquina, el puerto, el valor.

## 2. El mapa de la serie

| Documento | Lo general | Lo particular |
|---|---|---|
| [`01`](01_infraestructura_fisica.md) | Asignar lo lógico a hardware real; separación física de planos | Inventario del laboratorio; la referencia analizada |
| [`02`](02_vms_y_contenedores.md) | Dos formas de ejecución: quien necesita identidad de red propia es VM | Inventario completo con versiones y recursos |
| [`03`](03_red.md) | Cuatro segmentos lógicos + canal de control fuera de banda | Direccionamiento IPv4 estático, tabla a tabla |
| [`04`](04_vlans_y_subredes.md) | El segmento lógico materializado; la política sigue en las reglas | Correspondencia VLAN ↔ segmento, tagged/untagged |
| [`05`](05_puertos.md) | El plano de puertos materializa los enlaces | Asignación puerto a puerto por switch |
| [`06`](06_dependencias.md) | El orden de arranque como grafo: tiempo → identidad → estado → política → observación | Secuencia, versiones fijadas, arranque degradado |

## 3. Invariantes del despliegue

- **Topología:** diez switches — dos núcleo, dos distribución, cuatro acceso y la zona de control y servicios C1/C2 — todo dual-homed, 18 enlaces ([`01`](01_infraestructura_fisica.md) §3): la redundancia del plano de datos **se despliega y se mide**; la del plano de control (clúster ONOS de tres nodos) **también se despliega**, con el límite honesto del host físico compartido ([`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §6, C-04 §4).
- **Canal de control fuera de banda** (RP-02): las interfaces de gestión de los switches nunca atraviesan el plano de datos; la variante in-band es un objetivo aspiracional analizado, no desplegado.
- **Todo tráfico de ataque es interno al entorno del proyecto** (RP-06, RP-08): nada malicioso hacia redes del campus ni de terceros.
- **IPv4** (RP-12): direccionamiento privado, estático donde la reproducibilidad lo exige.
- **Reproducibilidad** (RNF-11): el despliegue completo se levanta desde una definición versionada; recrear el entorno no es un procedimiento manual.
- **Alcance** (RP-04): el prototipo representa los escenarios, no reproduce el campus — las cifras de capacidad valen para el prototipo y así se reportan ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §6).

## 4. Fronteras

- **La medición** (prototipo): este despliegue es el instrumento de las verificaciones de F y G; los números finales salen de correr sobre él, no de este documento.
- **El campus real**: fuera del alcance del curso; la referencia de esta serie es el análisis que lo anticipa.

# Infraestructura física

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

La **infraestructura física es el soporte real del despliegue**: las máquinas, los cables y los puertos sobre los que todo lo demás se asigna. Su criterio rector es la **separación de planos**: el canal de control, el espejo del perímetro y el plano de datos son físicamente distintos — lo que no comparte cable no comparte fallo ni interfiere (RP-02, RA-09).

## 2. El prototipo: inventario del laboratorio

| Elemento | Cantidad | Papel | Dónde |
|---|---|---|---|
| Switches del plano de datos (Pica8/PicOS) | 10 (NC1, NC2, D1, D2, A1–A4, C1, C2) | Plano de datos SDN: esqueleto, sesiones, mitigaciones | Laboratorio (RP-11) |
| Servidor de laboratorio | 1 | Hipervisor: todas las VMs y los contenedores | Laboratorio |
| Interfaces de gestión (`ma1`) | 10 | Canal de control OpenFlow, fuera de banda | Red de gestión del laboratorio o puertos dedicados del servidor |
| Cableado de datos | 18 enlaces entre switches + accesos + espejo | La malla dual-homed con la zona de control y servicios ([`05`](05_puertos.md)) | Etiquetado por puerto |
| Cable del espejo | 1 | A4 p47 → NIC dedicada del sensor | Directo, sin pasar por ningún otro equipo |

**Sobre el hardware disponible.** Los diez switches son Pica8 del laboratorio —el único lugar donde las primitivas OpenFlow se verifican de verdad ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4)—. El servidor es una máquina del laboratorio con ≥ 32 GB de RAM y ≥ 8 núcleos; con 16 GB se recorta el escenario a 10 hosts de usuario y 2 servidores de servicio ([`02`](02_vms_y_contenedores.md) §4). Si el slice no reuniera los diez Pica8, el recorte evaluado es **ocho** —se prescinde de la zona C1/C2 y los servidores vuelven a un acceso (la topología anterior)—: se pierde la zona de servicios, no la demostración de failover. Las **ventanas de uso del laboratorio condicionan cuándo corre la verificación física**; fuera de ellas rige el apoyo virtual declarado en [`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §1 ([`06`](06_dependencias.md) §5).

## 3. La topología del prototipo

```text
   C1 ────── C2                        ← zona de control y servicios (plataforma, ONOS, servidores)
    │╲       ╱│
    │ ╲     ╱ │                         ← C1/C2, cada uno al núcleo por directo y cruzado
    │  ╲   ╱  │
    │   ╲ ╱   │
   NC1 ────── NC2                     ← núcleo, enlazados entre sí
    │╲       ╱│
    │ ╲     ╱ │
    │  ╲   ╱  │                         ← cada distribución conecta con NC1 Y con NC2
    │   ╳    │
   D1        D2                       ← distribución
    │╲       ╱│
    │ ╲     ╱ │
    │  ╲   ╱  │                         ← cada acceso conecta con D1 Y con D2 (dual-homed)
    │   ╲ ╱   │
   A1      A2      A3      A4         ← usuarios, usuarios, libre (crecimiento), borde + espejo

   18 enlaces entre switches; todo acceso, toda distribución, todo destino y
   la zona de servicios quedan a un fallo de enlace o de switch del resto de la red.
```

**Dos núcleo, dos distribución, cuatro acceso y la zona de control y servicios C1/C2**, con doble enlace desde cada acceso, doble enlace de cada distribución al núcleo, enlace directo entre núcleos y C1/C2 colgados del núcleo por enlaces directo y cruzado: la jerarquía de [`D-10`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/10_topología_lógica.md) materializada con su bloque de servicios. Cada corte cuenta una historia, y todas se miden:

| Falla | Qué ocurre | Qué se mide |
|---|---|---|
| Corte de un enlace de acceso (A1–D1) | `PORT_STATUS`; el tráfico sigue por D2 — con grupo *fast-failover* la conmutación es local del switch, sin controlador (P2); sin él, el controlador reinstala el camino alternativo ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4) | Tiempo de conmutación |
| Caída de un núcleo (NC1) | La red sigue completa por NC2; C1 sigue por su enlace cruzado; los caminos se recalculan | Tiempo de re-enrutamiento global |
| Caída de la zona (C1) | Servidores, plataforma y ONOS siguen por C2 (dual-homed a C1/C2) | Pérdida de paquetes |
| Caída de un acceso (A1) | Su segmento se aísla; el resto no se entera (E-04) | Aislamiento del fallo |
| Caída de un nodo ONOS | Sus switches piden MASTER a los otros dos (`ROLE_REQUEST`); las reglas instaladas quedan intactas y las decisiones nuevas continúan ([`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §6) | Tiempo de re-maestría (M3) |
| Caída de dos nodos ONOS (sin quórum) | Las reglas instaladas siguen hasta su timeout; las decisiones nuevas esperan (degradación declarada) | Duración de degradación |

**La redundancia no cuesta un protocolo de árbol.** No hay STP esperando a que converja un anillo: el controlador ya tiene el grafo, y el camino alternativo es un recálculo o una conmutación local del propio plano de datos — la demostración de P2 en vivo, con números (RA-07).

**El reparto de papeles.** A4 es el **borde**: concentra lo externo (segmento EXTERNA) y el espejo hacia el sensor ([`G-04`](../G-Diseno_de_bajo_nivel-LLD/04_interfaces.md) §5). A1 y A2 cargan la política de ingreso de usuarios; **A3 queda libre** —solo esqueleto, reservado para crecimiento—. La **zona C1/C2** cuelga la plataforma, el clúster ONOS y los servidores protegidos del núcleo (VLAN 100/20 por el trunk de NIC-A), y repite el DROP a gestión como segundo punto de control (defensa en profundidad). Con orígenes de ataque en A1, A2 y A4, un ataque distribuido se mitiga **simultáneamente en tres switches de ingreso** (P9) — la demostración de concurrencia, con cada maestro ONOS instalando en sus switches. La escala —diez switches, ~23 dispositivos, ≈ 420–520 reglas ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4)— hace creíbles los experimentos de capacidad, y el sondeo I8 deja de ser simbólico: barre los diez dispositivos.

## 4. La referencia: lo que se analiza, no se despliega

El campus que la solución describe, con sus condiciones de habilitación ([`F-09`](../F-Decisiones_tecnologicas/09_sintesis_y_trazabilidad.md) §5, [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md) §4):

| Elemento de la referencia | Análisis | Condición de habilitación |
|---|---|---|
| Jerarquía núcleo / distribución / acceso | El prototipo ya la materializa (§3); la referencia la lleva a la escala del campus: cantidades y enlaces según la red real | Topología definitiva del campus (D-10) |
| Redundancia de nodos y enlaces | El prototipo ya la **despliega y mide**; la referencia la extiende a doble enlace en todos los accesos y doble núcleo físico | Decisión de la administración de la red (E-04: es despliegue) |
| Clúster del controlador en hosts físicos distintos | El prototipo ya despliega los tres nodos (§3, [`F-01`](../F-Decisiones_tecnologicas/01_controlador_y_api_northbound.md) §6); la referencia los reparte en servidores de gestión separados — el prototipo tolera la caída de un nodo, no la del host | Topología definitiva de la administración (F-01 §6) |
| Canal in-band | VLAN de gestión priorizada sobre los enlaces de datos; los flujos del canal se instalan antes que nada | Aprobación de la administración; supervivencia verificada ante ataque volumétrico (C-04 §6) |
| Feeds externos de inteligencia | Listas de reputación para R5.6, con la regla de promoción del prototipo como filtro | Acuerdo con el proveedor del feed; fuera del entorno controlado (F-07 §4) |
| Cifrado en reposo y política de respaldo | Volúmenes de las bases cifrados; respaldo con retención y drill periódico | Procedimientos de la administración de la red |
| 802.1X en puertos sensibles | Accesos administrativos y zonas restringidas con autenticación de puerto | Reservado por diseño desde D-07 §3; fuera del prototipo |

La referencia **no** es una lista de tareas del proyecto: es la forma del diseño cuando el prototipo haya firmado sus decisiones con mediciones (P12).

## 5. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Inventario completo presente y conectado (10 switches, 18 enlaces, espejo, gestión) | Correspondencia con [`05`](05_puertos.md), puerto a puerto | C-04 §5 |
| Corte de un enlace de acceso (A1–D1) | Tiempo de conmutación al camino por D2 — grupo fast-failover o recálculo | RA-07, P2, E-04 |
| Caída de NC1 | La red sigue completa por NC2; tiempo de re-enrutamiento global | RA-07 |
| Caída de C1 (RD3) | Servidores, plataforma y ONOS siguen por C2; ninguna sesión se pierde | RA-07 |
| Caída de un nodo ONOS durante un login (RD2) | El login se completa: re-maestría y `FLOW_MOD` del nuevo maestro | M3, RA-07 |
| Caída de dos nodos ONOS (RD4) | Lo permitido sigue; lo nuevo espera (quórum) — degradación declarada | P2, P10 |
| Ataque distribuido desde A1, A2 y A4 | Mitigación simultánea en los tres switches de ingreso (P9), un maestro por switch | R3.5 |
| Canal de control activo por `ma1` con el plano de datos operando | Separación física de planos | RP-02, RA-09 |
| Ataque de carga contra el segmento de gestión durante un escenario | El canal out-of-band sostiene el control | RA-09, P2 |
| Ventanas de laboratorio planificadas | La verificación física corre en el hardware real | RP-11 |

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
| Hosts académicos | 16 | `52:54:00:01:01`–`52:54:00:01:10` | 10.1.0.10–.25 | 1 / 512 MB |
| Hosts de operadores | 2 | `52:54:00:04:01`–`.02` | 10.1.0.30–.31 | 1 / 1 GB |
| Atacante interno | 1 | `52:54:00:03:02` | 10.1.0.50 | 1 / 1 GB |
| Atacante externo | 1 | `52:54:00:03:01` | 10.3.0.10 | 1 / 1 GB |
| Servidores de servicio | 3 | `52:54:00:02:01`–`.03` | 10.2.0.10–.12 | 1 / 1 GB |
| Sensor perimetral (Suricata) | 1 | — (2 NIC: espejo RX + gestión) | 10.0.0.27 | 2 / 2 GB |

- **Convención de MAC** (`52:54:00:` local, tercer octeto = clase, cuarto = correlativo): legible en cualquier captura y en el registro de asociaciones. La clase de un dispositivo se ve en su MAC — útil para el reporte, jamás como criterio de seguridad (la política mira el catálogo y las reglas, no el prefijo).
- **Los servidores de servicio** representan los activos protegidos de R2; su clasificación (general / privilegiado / crítico) es la de [`A-02`](../A-Modelo_de_dominio/02_recursos_y_servicios.md).
- **El sensor** tiene dos NIC: la del espejo (solo recepción, sin IP) y la de gestión. Fuera del camino de reenvío (P8).
- **Las cinco NIC del servidor:** NIC-A ↔ C1/C2 p6 (trunk de gestión y servidores, VLAN 100 + 20) · NIC-B ↔ A1 p20 (hosts virtuales académicos) · NIC-C ↔ A4 p4 (atacante externo, VLAN 30) · NIC-D = el espejo desde A4 p47, entregada a la VM del sensor (su NIC de gestión va por el puente de NIC-A) · NIC-E ↔ A2 p6 (operadores, atacante interno y el puente de la demostración de `MAC_Moved` entre A1 y A2). El plano puerto a puerto está en [`05`](05_puertos.md).
- **Total del servidor:** 24 VMs (16 académicos a 512 MB = 8 GB · 7 de host a 1 GB = 7 GB · el sensor a 2 GB → ≈ 17 GB) y contenedores ≈ 12 GB (incluidos los **tres nodos ONOS a 2 GB cada uno**) → ≈ 29 GB de los 32 GB declarados en [`01`](01_infraestructura_fisica.md) §2 — margen estrecho; los académicos bajaron a 512 MB (imagen mínima) para que el clúster quepa. La variante recortada de 16 GB recorta el escenario a 10 hosts y 2 servidores.

## 5. La referencia: la misma regla a escala

En el campus real la regla no cambia, cambia el soporte: los servicios corren en servidores dedicados de la administración (no en un único hipervisor), los hosts son equipos reales de las personas, y el sensor perimetral es un equipo propio del punto de espejo. Lo que el prototipo demuestra —que cada pieza tiene identidad y responsabilidad separadas— es exactamente lo que el despliegue hereda.

## 6. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Recrear el entorno completo desde la definición versionada | Sin pasos manuales; mismo estado de partida | RNF-11 |
| Identidad de red de cada VM (MAC, IP, puerto) | Corresponde a [`05`](05_puertos.md) y al registro de asociaciones | R1.1 |
| Servicios alcanzables solo desde gestión | El portal es la única superficie visible desde BASE | RA-09 |
| Repetir un escenario con los mismos parámetros | Métricas comparables entre corridas | RNF-12 |

# Red

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

La **red del despliegue es la materialización de los segmentos lógicos** ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §2): cuatro dominios —externa, usuarios, gestión y servidores— más un **canal de control fuera de banda** que no es un segmento de datos sino el plano de gestión de los switches. Dos reglas de fondo:

- **El enrutamiento lo resuelve el plano de datos SDN.** No hay un router en el prototipo: entre segmentos reenvían los switches por las reglas de camino ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4), y la política se aplica en el switch de ingreso. La única «ruta» entre VLANs es una entrada del controlador.
- **Direccionamiento estático IPv4** (RP-12) en todo lo que la reproducibilidad exige: servicios, servidores protegidos y hosts del escenario tienen IP fija; nada depende de negociación (RNF-11).

```text
   A1      A2      A3      A4        ← acceso: usuarios, usuarios, servidores, borde
    │╲     ╱│       │╲     ╱│
    │ ╲   ╱ │       │ ╲   ╱ │         ← cada acceso conecta con D1 y con D2 (dual-homed)
    │  ╲ ╱  │       │  ╲ ╱  │
    │  ╱ ╲  │       │  ╱ ╲  │
    │╱     ╲│       │╱     ╲│
   D1        D2                      ← distribución
    │╲       ╱│
    │ ╲     ╱ │
    │  ╲   ╱  │
    │   ╲ ╱   │
    │    ╳    │                       ← cada distribución conecta con NC1 y con NC2
    │   ╱ ╲   │
    │  ╱   ╲  │
    │ ╱     ╲ │
    │╱       ╲│
   NC1 ────── NC2                     ← núcleo, enlazados entre sí

   A1: académicos (10.1.0.10–.25)          A3: libre (reservado para crecimiento)
   A2: operadores (.30–.31) + atacante interno (.50)     A4: atacante externo (10.3.0.10)
   ZONA C1/C2 (VLAN 100 y 20, por NIC-A del servidor, colgada del núcleo):
     GESTIÓN 10.0.0.0/24: portal .5 · servicios .10–.17 · adaptador .18 ·
     controlador ONOS .20 · .30 · .40 · intermediario .21 · persistencia .22 ·
     identidad .23/.24 · tiempo .25 · visualización .26 · sensor .27 · DNS .28
     SERVIDORES 10.2.0.0/24: general .10 · privilegiado .11 · crítico .12
   canal de control (OpenFlow): ma1 de cada uno de los diez switches ──► red de gestión
```

## 2. El direccionamiento, tabla a tabla

| Segmento | Subred | Hosts | Nota |
|---|---|---|---|
| GESTIÓN | `10.0.0.0/24` | **la plataforma:** portal `10.0.0.5` · IAM `.10` · registro `.11` · monitor `.12` · detección `.13` · incidentes `.14` · políticas `.15` · auditoría `.16` · consola `.17` · adaptador del sensor `.18` — **la infraestructura:** controlador (clúster ONOS: `.20` · `.30` · `.40`) · intermediario (RabbitMQ) `.21` · persistencia (PostgreSQL) `.22` · identidad institucional (FreeRADIUS `.23` + directorio `.24`) · tiempo (chrony) `.25` · visualización (Grafana) `.26` · DNS `.28` — **el sensor perimetral (Suricata, VM):** `.27` (gestión; el espejo no lleva IP) | El portal conserva la dirección de los flujos (`10.0.0.5`); es la única superficie que BASE alcanza, y solo por la regla 150 ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §3). Los tres nodos ONOS comparten la VLAN 100; su canal hacia los switches va por la red OOB (`ma1`), nunca por esta subred |
| USUARIOS | `10.1.0.0/24` | académicos `.10–.25` · operadores `.30–.31` · atacante interno `.50` | Política de ingreso en A1 y A2 |
| SERVIDORES | `10.2.0.0/24` | general `.10` · privilegiado `.11` · crítico `.12` | Los activos protegidos de R2; ingresan por la zona C1/C2 (VLAN 20, trunk de NIC-A) |
| EXTERNA | `10.3.0.0/24` | atacante `.10` · «red externa» representada por el puerto de A4 | Origen de los escenarios R5 |
| Canal de control | red de gestión del laboratorio (o puertos dedicados del servidor) | `ma1` de los diez switches → 2.ª NIC de cada nodo ONOS | Fuera de banda (RP-02); no es una subred del prototipo |

- **DNS interno:** `10.0.0.28` resuelve los nombres del entorno de laboratorio; el esqueleto BASE permite UDP 53 pre-login ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §3). Los hosts usan IP estáticas; DHCP queda reservado para la referencia — en el prototipo la regla de DHCP existe en el esqueleto, pero el direccionamiento no depende de ella.
- **El segmento de gestión es alcanzable por el plano de datos — y esa es la frontera que se demuestra.** El DROP del esqueleto (prioridad 100) usa exactamente esta ruta (R1.6, RA-09): BASE intenta, la regla niega, y la elevación del operador (200) la abre para quien corresponde. El canal de control, en cambio, **no** pasa por el plano de datos — son dos cosas distintas y ambas existen.
- **Todo timestamp, UTC** ([`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §5); el desfase entre nodos se mide (RNF-09).

## 3. La referencia: la misma lógica, otra escala

En el campus real los cuatro segmentos existen con su propia escala (edificios, servidores institucionales, perímetro real), el direccionamiento lo administra la institución y el canal de control puede adoptar la variante in-band con VLAN de gestión priorizada — el objetivo aspiracional ya registrado en [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md) §6 y analizado en [`01`](01_infraestructura_fisica.md) §4. Lo que no cambia es la lógica: política en el ingreso, caminos en los tramos, gestión protegida.

## 4. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| BASE alcanza el portal (150) y nada más de la gestión (100) | La frontera de RA-09 se demuestra en vivo | R1.6 |
| Elevación de operador abre el acceso a gestión (200) y expira al TTL | La escalera sobre la frontera | R1.8, P10 |
| Tráfico entre segmentos enruta por reglas de camino | Sin router: el plano de datos resuelve | flows/05 |
| Ataque de carga contra la gestión durante un escenario | El control y los servicios no se degradan | RA-09, P2 |
| Desfase de reloj entre nodos | El máximo observado | RNF-09 |

# VLANs y subredes

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

El **segmento lógico se materializa en una VLAN con su subred**: la VLAN agrupa en capa 2 y disciplina el direccionamiento; la subred le da el espacio IPv4 (RP-12). Es el mecanismo de despliegue que el modelo de dominio ya registró como recurso — «Segmentos de red (VLAN)», gestión P20 ([`A-02`](../A-Modelo_de_dominio/02_recursos_y_servicios.md))—. Y con una frontera explícita: **la VLAN no concede nada.** El aislamiento y los permisos viven en las reglas del pipeline ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md)); la VLAN es agrupación y direccionamiento — la política manda sobre ella, no al revés (P8).

## 2. La correspondencia segmento ↔ VLAN ↔ subred

| VLAN | Segmento | Subred | Vive en | Nota |
|---|---|---|---|---|
| 10 | USUARIOS | `10.1.0.0/24` | Puertos de acceso de A1 y A2; trunks hacia la distribución | Hosts académicos, operadores, atacante interno |
| 100 | GESTIÓN | `10.0.0.0/24` | Trunk del servidor en C1/C2; transita hacia la distribución y el núcleo | Los servicios de la plataforma; alcanzable por el plano de datos **solo** por la frontera de reglas ([`03`](03_red.md) §2) |
| 20 | SERVIDORES | `10.2.0.0/24` | Trunk del servidor en C1/C2; transita hacia la distribución y el núcleo | Los activos protegidos de R2 |
| 30 | EXTERNA | `10.3.0.0/24` | Puerto de A4 (y trunk del servidor para la VM atacante) | Origen de los escenarios R5 |

- **Tagging:** untagged en los puertos de acceso (los hosts no etiquetan); tagged (802.1Q) en los trunks, que transportan varias VLAN — los enlaces acceso–distribución llevan 10, 20 y 100 (30 en el borde); los enlaces distribución–núcleo y el enlace de núcleo llevan todas las VLAN de datos. La asignación puerto a puerto está en [`05`](05_puertos.md).
- **El tránsito de la VLAN 100 es deliberado:** el segmento de gestión cruza los trunks para que la frontera de reglas exista — BASE intenta alcanzarlo, la prioridad 100 lo niega, la elevación (200) lo abre para quien corresponde (R1.6, RA-09). El **canal de control**, en cambio, no es esta VLAN: son las interfaces `ma1`, fuera de banda (RP-02).
- **La VLAN 1 no se usa:** es la VLAN por defecto del switch, viaja sin etiquetar como nativa en los trunks, transporta los protocolos de control y es el punto de partida clásico del salto de VLAN. La gestión ocupa la VLAN 100 —fuera del rango de datos 10/20/30— y la VLAN 1 queda sin asignación.
- **DHCP:** los hosts del prototipo usan IP estática (reproducibilidad, RNF-11); DHCP queda reservado para la referencia. La regla de DHCP del esqueleto existe para que el diseño no dependa de esa reserva.

## 3. La cuarentena y el canal in-band: dos reservas

- **VLAN de cuarentena:** la variante de contención que mueve un dispositivo a una VLAN aislada en vez de bloquearlo ([`flows/03`](../../../flows/03_flujo_autenticacion_autorizacion.md)) queda **analizada para la referencia** — en el prototipo la cuarentena es DROP con aprobación humana ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §3). Añadir la VLAN de cuarentena al prototipo es un cambio de alcance, no de arquitectura.
- **Canal in-band:** la variante que lleva el control por una VLAN de gestión priorizada sobre los enlaces de datos sigue siendo el objetivo aspiracional analizado en [`01`](01_infraestructura_fisica.md) §4; el prototipo es out-of-band (RP-02).

## 4. La referencia: la misma correspondencia a escala

En el campus real cada segmento existe como VLAN institucional con su subred administrada por la institución, y la correspondencia se multiplica (usuarios por edificio, servidores por servicio). Lo que no cambia es la regla: la segmentación es el mecanismo; la política es de las reglas. El permiso P20 (gestionar segmentación) queda en manos de la administración de la red — nunca de los servicios.

## 5. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Dispositivo en VLAN 10 sin alcanzar 10.0.0.0/24 salvo el portal | La frontera de reglas sobre la VLAN | R1.6, RA-09 |
| Elevación abre VLAN 100 para el operador y expira al TTL | La escalera sobre el tránsito | R1.8, P10 |
| Tráfico entre VLANs enruta por caminos del controlador | Sin router: el plano de datos resuelve | flows/05 |
| Etiquetado de trunks correcto (10/20/100 según enlace) | Correspondencia con [`05`](05_puertos.md) | R2.6 |

# Puertos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

El **plano de puertos es la asignación física que materializa los enlaces**: cada puerto de cada switch tiene un papel, y el papel manda sobre su configuración. La convención del prototipo: puertos `p1–p44` de datos (trunks y accesos), `p45–p48` reservados para funciones especiales (el espejo vive en `p47` del borde), interfaz `ma1` de gestión. Todo enlace queda etiquetado en el plano y en este documento — un puerto sin papel es un fallo de despliegue.

## 2. La asignación, switch por switch

```text
        A1 (acceso usuarios)            A2 (acceso usuarios)           A3 (acceso libre)
        p1 trunk ↔ D1 · p2 ↔ D2         p1 ↔ D1 · p2 ↔ D2              p1 ↔ D1 · p2 ↔ D2
        p3–p19 acceso VLAN 10           p3–p5 acceso VLAN 10            p3–p19 reservados (crecimiento)
        p20 NIC-B (hosts virtuales)     p6 NIC-E (operadores,           ma1 gestión
        ma1 gestión                        atacante interno,
                                           puente demo MAC_Moved)
                                        ma1 gestión

        A4 (borde)                      D1 y D2 (distribución)          NC1 y NC2 (núcleo)
        p1 ↔ D1 · p2 ↔ D2               p1 ↔ NC1 · p2 ↔ NC2             p1 ↔ D1 · p2 ↔ D2
        p3 acceso VLAN 30               p3 ↔ A1 · p4 ↔ A2               p3 ↔ NC1–NC2 (enlace de núcleo)
        p4 NIC-C trunk VLAN 30             p5 ↔ A3 · p6 ↔ A4            p4 ↔ C1 (directo) · p5 ↔ C2 (cruzado)
           (atacante externo)           ma1 gestión                     ma1 gestión
        p47 espejo → NIC-D (sensor)
        ma1 gestión

        C1 y C2 (zona de control y servicios)
        p1 ↔ NC1 (C1 directo) · p2 ↔ NC2 (C1 cruzado)
        p1 ↔ NC2 (C2 directo) · p2 ↔ NC1 (C2 cruzado)
        p3 ↔ C2/C1 (enlace de la zona)
        p6 NIC-A trunk VLAN 100 + 20 (plataforma y servidores)
        ma1 gestión
```

| Puerto | Papel | VLANs | Nota |
|---|---|---|---|
| A1 p1/p2 ↔ D1/D2 | Trunk de acceso | 10, 100 (tagged) | El camino alternativo nace aquí: dos uplinks; la 100 transita para alcanzar el portal (.5) |
| A1 p3–p19 | Acceso de usuarios | 10 (untagged) | Equipos físicos del laboratorio |
| A1 p20 | NIC-B del servidor | 10 (untagged) | **Los hosts virtuales académicos** comparten este puerto |
| A2 p1/p2 ↔ D1/D2 | Trunk de acceso | 10, 100 (tagged) | Dual-homed |
| A2 p3–p5 | Acceso de usuarios | 10 (untagged) | Equipos físicos |
| A2 p6 | NIC-E del servidor | 10 (untagged) | Operadores, atacante interno y el **puente de la demostración de `MAC_Moved`** |
| A3 p1/p2 ↔ D1/D2 | Trunk de acceso | 10 (tagged) | Dual-homed; **libre en v2** — reservado para crecimiento |
| A3 p3–p19 | Reservados | — | Solo esqueleto; sin poblaciones |
| A4 p1/p2 ↔ D1/D2 | Trunk del borde | 30 (tagged) | Dual-homed |
| A4 p3 | Acceso externo | 30 (untagged) | Equipo externo real, si el laboratorio lo ofrece |
| A4 p4 | NIC-C del servidor | 30 (tagged) | La VM atacante externa, por el servidor |
| A4 p47 → NIC-D | **Espejo del perímetro** | — | Replica el ingreso del segmento externo (p3+p4) hacia el sensor; el sensor solo recibe, nunca emite por esta interfaz ([`G-04`](../G-Diseno_de_bajo_nivel-LLD/04_interfaces.md) §5) |
| D1/D2 p1/p2 ↔ NC1/NC2 | Trunks de distribución | 10, 100, 30 (tagged) | Cada distribución llega a ambos núcleos |
| D1/D2 p3–p6 ↔ A1–A4 | Trunks de acceso | según el acceso | La agregación de los cuatro accesos |
| NC1 p3 ↔ NC2 p3 | Enlace de núcleo | 10, 100, 30 (tagged) | El núcleo es un par enlazado, no un anillo |
| NC1/NC2 p4/p5 ↔ C1/C2 | Trunks de la zona de servicios | 100, 20 (tagged) | Directo y cruzado: cada C llega a ambos núcleos |
| C1 p3 ↔ C2 p3 | Enlace de la zona | 100, 20 (tagged) | C1/C2 son un par enlazado, igual que el núcleo |
| C1/C2 p6 ↔ NIC-A | Trunk de la plataforma | 100, 20 (tagged) | Por aquí entran los diez servicios, el clúster ONOS, las bases, el IdP y los tres servidores protegidos |
| `ma1` ×10 | Canal de control | — | OpenFlow fuera de banda (RP-02); whitelist de los tres controladores ([`G-04`](../G-Diseno_de_bajo_nivel-LLD/04_interfaces.md) §2) |

- **Los hosts virtuales comparten un puerto por población** — es la concesión práctica del laboratorio: cada grupo de VMs entra por una NIC del servidor (A1 p20 para académicos, A2 p6 para operadores y atacante interno, NIC-A para plataforma y servidores). La red las ve como MAC distintas en el mismo puerto; las reglas del esqueleto y de sesión son por MAC, no por puerto, así que la política no se entera.
- **La zona C1/C2 es el segundo punto de control** ([`01`](01_infraestructura_fisica.md) §3): repite el DROP a gestión (p100) y solo acepta hacia VLAN 20 lo que llega por los caminos instalados — defensa en profundidad.
- **El portal es alcanzable por BASE a través del plano de datos:** por eso la VLAN 100 transita A→D→NC→C1/C2 hasta NIC-A — la única superficie que BASE alcanza (regla 150).
- **La demostración de `MAC_Moved` cruza switches:** mover la vNIC de una VM del puente de A1 (NIC-B) al de A2 (NIC-E) hace que la MAC aparezca en **otro switch** — el movimiento más fuerte que el prototipo puede producir, y el `MAC_Moved` determinista de [`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4 lo aísla.
- **El espejo no comparte cable con nada** ([`01`](01_infraestructura_fisica.md) §2): A4 p47 → NIC dedicada del sensor, directo.
- **Reservas de la referencia:** puertos sensibles (infraestructura, zonas restringidas) con port security y 802.1X — reservados por diseño desde D-07 §3, fuera del prototipo ([`01`](01_infraestructura_fisica.md) §4).

## 3. El plano de puertos en la operación

El plano de puertos es la entrada de la topología: el controlador aprende por `PORT_STATUS` y LLDP quién está conectado dónde ([`flows/05`](../../../flows/05_enrutamiento.md) §3), y la caída de un enlace rehace el grafo — con la malla dual-homed, el grafo resultante sigue conexo salvo caída de un acceso. Un puerto movido **sin actualizar este documento** es un fallo de despliegue detectable: la topología aprendida dejará de corresponder con el plano — la verificación siguiente lo cierra comparando ambas.

## 4. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Correspondencia puerto a puerto entre el plano y la topología aprendida | Sin puertos sin papel | R2.6 |
| Espejo activo: tráfico externo generado llega íntegro al sensor | Copia fiel, sin interponerse | R5, P8 |
| `PORT_STATUS` al desconectar un enlace de acceso | El grafo se rehace y el camino alternativo toma el relevo — tiempo medido | E-04, RA-07 |
| Conexión de control rechazada desde un puerto de datos | El canal es solo `ma1` (V6) | RA-09 |
| Movimiento de MAC entre A1 y A2 | `MAC_Moved` determinista y aislamiento | R3.3, P7 |

# Dependencias

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

El **orden de arranque es un grafo de dependencias**, y el grafo sigue un principio de capas: **tiempo → identidad → estado → política → observación.** Primero lo que firma los registros (el tiempo), después lo que guarda y transporta (persistencia e intermediario), después lo que gobierna la red (controlador y switches), después lo que decide (identidad y servicios), después lo que observa y muestra. El apagado es el inverso, con una excepción: la auditoría exporta su retención antes de detenerse.

La razón de fondo es el **arranque degradado** (P2): la red no depende de los servicios — un servicio que no arranca no tumba lo que ya está instalado en los switches. El grafo describe quién espera a quién **para arrancar correctamente**, no quién detiene a quién al fallar. El grafo y las tablas hablan de **papeles**; los productos que materializan cada papel están en la columna «Se materializa con» y en §4.

## 2. El grafo

```text
TIEMPO ──────────────► PERSISTENCIA ────────► IDENTIDAD (IdP simulado)
   │                       │                        │
   │                       ├──────► INTERMEDIARIO   │
   │                       │           │            │
   ▼                       ▼           ▼            ▼
(todos los nodos     CONTROLADOR + switches    SERVICIOS DE LA PLATAFORMA
 con hora común)     (canal de control)        (IAM · Registro · Incidentes ·
                                               Políticas · Auditoría · Monitor ·
                                               Detección · Portal · Consola)
                                                        │
                                SENSOR PERIMETRAL + VISUALIZACIÓN ──► verificación
```

| Componente | Se materializa con | Depende de | Si falta su dependencia |
|---|---|---|---|
| Tiempo | chrony | nada | Los servicios que firman tiempo **esperan** — no se firma tiempo falso (P11) |
| Persistencia | PostgreSQL | Tiempo (timestamps de transacción) | Los servicios quedan en *not ready*; la red opera igual (P2) |
| Intermediario | RabbitMQ | Tiempo | Los publicadores operan con buffer local y huecos declarados ([`G-02`](../G-Diseno_de_bajo_nivel-LLD/02_eventos.md) §5) |
| Controlador + switches | ONOS + PicOS | red de gestión | Sin controlador, los switches conservan lo instalado y todo expira por timeout (P2, P10) — no hay decisiones nuevas hasta el re-registro |
| Identidad institucional | FreeRADIUS + OpenLDAP | Persistencia (sus datos) | El login de la comunidad falla; el reino operadores (repositorio propio) sigue |
| IAM | imagen propia | Persistencia, Intermediario, Identidad | Sin sesiones nuevas; las vigentes siguen hasta su timeout |
| Registro, Incidentes, Políticas, Auditoría | imagen propia | Persistencia, Intermediario | Sin su base no arrancan (*not ready*); la cadena de detección espera, la red no |
| Monitor, Detección | imagen propia | Intermediario (Monitor además: I2) | Sin observación no hay detección nueva; las mitigaciones vigentes siguen |
| Portal, Consola | imagen propia | IAM (sesiones), sus bases | Sin login ni consola; el plano de datos no se entera |
| Sensor perimetral y su adaptador | Suricata + adaptador propio | espejo activo, Intermediario | Sin sensor, el perímetro pierde detección (R5) — declarado, no silencioso |
| Visualización | Grafana | bd_monitor, bd_auditoria (lectura) | Sin tableros; la observación cruda sigue |

## 3. La secuencia de arranque

1. **Tiempo (chrony)** — todos los nodos sincronizan antes de operar; el desfase se verifica (RNF-09).
2. **Persistencia (PostgreSQL)** — las seis bases; chequeo `pg_isready` por base.
3. **Intermediario (RabbitMQ)** — vhost `plataforma`, exchange, colas y políticas ([`G-02`](../G-Diseno_de_bajo_nivel-LLD/02_eventos.md) §4).
4. **Controlador (clúster ONOS) + switches (PicOS)** — primero se forma el clúster (tres nodos, Atomix con quórum, I9); recién entonces se conectan los switches (`HELLO`/`FEATURES_REPLY`, `ROLE_REQUEST`, whitelist de los tres endpoints) y se reinstala el esqueleto de dispositivos conocidos. En el diseño in-band (referencia), el arranque es escalonado desde C1 — cada tramo instala el canal del siguiente (p65000) antes de cualquier regla de usuario ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §3).
5. **Identidad institucional (FreeRADIUS + OpenLDAP)** — cuentas de prueba, `radtest` de control.
6. **Servicios de la plataforma** — IAM, Registro, Incidentes, Políticas, Auditoría, Monitor, Detección, Portal, Consola; cada uno declara `/health` *ready*.
7. **Sensor perimetral + visualización** — el sensor confirma el espejo; los tableros cargan sus datasources.
8. **Verificación de arranque** — un `PACKET_IN` de prueba recorre aprendizaje → esqueleto → portal; un evento de prueba recorre el bus end-to-end. Recién entonces el entorno se declara operativo.

**El apagado** invierte el orden, con la auditoría antes que su base: export JSONL del rango pendiente, cierre del bus (drenaje de colas), parada de servicios, del controlador y de la persistencia.

## 4. Versiones fijadas

Cada papel se materializa con un producto, y cada producto queda **fijado por versión** en la definición versionada del despliegue (RNF-11) — punto de partida, registrado en el primer despliegue:

| Papel | Producto | Versión (punto de partida) |
|---|---|---|
| Controlador | ONOS | 2.7 LTS |
| Persistencia | PostgreSQL | 16 |
| Intermediario | RabbitMQ | 3.13 |
| Identidad | FreeRADIUS · OpenLDAP | 3.2 · 2.6 |
| Sensor | Suricata | 7 |
| Tiempo | chrony | 4.5 |
| Visualización | Grafana | 11 |
| Servicios propios | Python | 3.12 |

Una repetición futura no compara contra otro software ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §4); un cambio de versión es un cambio de despliegue, registrado como tal.

## 5. Las ventanas del laboratorio

El hardware del laboratorio no está siempre disponible (RP-11): la secuencia de arranque **física** corre dentro de las ventanas planificadas ([`01`](01_infraestructura_fisica.md) §2); fuera de ellas, el apoyo virtual ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §1) levanta la misma secuencia con sus límites declarados — las pruebas de primitivas y capacidad se firman siempre contra el switch físico.

## 6. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Arranque completo desde cero con la secuencia de §3 | Tiempo total; todo *ready* en orden | RNF-11 |
| Apagado ordenado y re-arranque | Nada corrupto; auditoría exportada antes de detenerse | F-05 |
| Arranque degradado: sin intermediario | Publicadores con buffer local; huecos declarados | P13, E-04 |
| Arranque degradado: sin controlador | Lo instalado sigue operando y expira por timeout | P2, P10 |
| Caída y retorno del Incident Manager | Reconciliación contra el plano de datos | E-04, P10 |
| Desfase de reloj tras el arranque | Todos los nodos con hora común | RNF-09 |
