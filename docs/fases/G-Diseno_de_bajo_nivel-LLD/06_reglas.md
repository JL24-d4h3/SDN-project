# Reglas

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La **regla es la unidad de política materializada**: cada entrada del pipeline del switch es una decisión de la plataforma convertida en match y acción ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §1). El orden de evaluación es una **jerarquía de autoridad**: a mayor prioridad, mayor poder de decidir sobre el paquete. La jerarquía es fija y es la misma en toda la red:

```text
mitigación (1000)   >   sesión y elevación (200)   >   esqueleto BASE (150–100)
>   caminos (20)    >   servicios básicos (10)     >   table-miss (aprendizaje / portal)
(en el diseño in-band —referencia—, por encima de todo: canal de control p65000)
```

La mitigación manda sobre todo — es la respuesta al ataque; la sesión manda sobre el esqueleto — es el privilegio otorgado; el esqueleto manda sobre los caminos — es la línea base de cualquier dispositivo. **La política se aplica en el switch de ingreso**; los tramos siguientes solo resuelven caminos (P9: mitigar cerca del origen; [`flows/05`](../../../flows/05_enrutamiento.md) §2).

## 2. El pipeline lógico: dos etapas

**Decisión de esta fase** (cierra la cuestión de [`flows/01`](../../../flows/01_primitivas_openflow.md)): el pipeline lógico es de **dos etapas** — *política* (¿este paquete puede?) y *caminos* (¿por dónde sale?):

```text
paquete ──► ETAPA POLÍTICA (por switch de ingreso)          ──► ETAPA CAMINOS (todos los tramos)
            1000  mitigaciones (meter / drop)    ──►            20  ipv4_dst → puerto de salida
            200   sesión y elevación (allow)     ──►             5  inundación DHCP (broadcast)
            150   portal (pre-login)             ──►             table-miss → PACKET_IN
            120   par MAC/IP aprendido           ──►
            110   anti-spoofing          DROP
            100   destino gestión        DROP
            10    DHCP/DNS               ──►
            table-miss → PACKET_IN (aprendizaje / redirección al portal)
```

- Si la verificación **V1 confirma multi-tabla** ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4), cada etapa es una tabla física (con `GOTO`).
- Si **no**, el controlador compone entradas únicas: match de política + instrucción de salida — la especificación lógica no cambia, cambia la materialización. **El cómo es responsabilidad del controlador** (I2, D-07); este LLD fija el qué.

### 2.1 Qué llega al controlador y qué no

El `PACKET_IN` es la **excepción**, no el mecanismo de reenvío. Si cada paquete subiera al controlador, el plano de datos dependería de él y la latencia y la carga lo harían inviable (P2). La lista de causas es **cerrada** y tiene tres entradas:

| Causa | Qué la dispara | Qué hace el controlador |
|---|---|---|
| Table-miss | Primer paquete de un flujo que ninguna entrada conoce | Aprende el par MAC/IP y decide: esqueleto, redirección al portal o descarte |
| ARP sin resolver | Consulta ARP de un dispositivo que aún no tiene par | Responde o instala el camino; nunca inunda a ciegas |
| LLDP | Anuncio de vecindad del switch | Construye la topología; no instala flujos |

Todo lo demás se resuelve **antes** del table-miss, por una de tres vías: una entrada proactiva del pipeline, un camino estático fuera de la política, o el canal de gestión. Las familias principales:

| Familia | Protocolo / puerto | Extremos | Vía |
|---|---|---|---|
| DHCP | UDP 67/68 | dispositivo ↔ servidor DHCP | entrada 10 + inundación de broadcast (prioridad 5) |
| DNS | UDP/TCP 53 | dispositivo ↔ DNS `10.0.0.28` | entrada 10 |
| Portal | TCP 443 | dispositivo ↔ portal `10.0.0.5` | entrada 150; el controlador no está en el camino |
| Identidad | RADIUS 1812/1813 · LDAP 389/636 | IAM ↔ FreeRADIUS `.23` · directorio `.24` | camino estático en la VLAN 100 |
| Mensajería y persistencia | AMQP 5672 · PostgreSQL 5432 | servicios ↔ RabbitMQ `.21` · PostgreSQL `.22` | camino estático en la VLAN 100 |
| Operación | SSH 22 · SNMP 161 · syslog 514 · NTP 123 | operadores y nodos ↔ plataforma y switches | OOB (`ma1`) o VLAN 100; sesión 200 cuando va por VLAN 20 |
| Observación | sFlow/NetFlow · métricas HTTP | switch y nodos ↔ colector | muestreo o consulta; no genera packet-in |
| Control | OpenFlow 6653 | switches ↔ ONOS `.20/.30/.40` | OOB en el prototipo; entrada 65000 en el diseño in-band |
| Ataque | el del escenario R4 | atacante → objetivo | camino normal; match por política y mitigación 1000 |
| Túnel | GRE / IPsec | — | **fuera del diseño**; si se usara, regla estática que coincide con la IP externa |

La identidad, la mensajería y la persistencia **no atraviesan el pipeline**: son tráfico este-oeste dentro de la VLAN 100, resuelto por los caminos estáticos del segmento. El switch no los inspecciona y el controlador no los ve; su protección es la del segmento y la de TLS ([`G-04`](04_interfaces.md) §3).

**El modo de fallo del pipeline es seguro.** El switch se configura con `fail mode secure`: si el controlador deja de responder, las entradas instaladas **permanecen** y un paquete sin match se **descarta** — el switch no vuelve a conmutación normal ni inunda. La red no se abre por la caída del controlador; se degrada a la última política conocida. El clúster de tres nodos y la re-elección de maestro ([`G-04`](04_interfaces.md) §2) cubren la continuidad del plano de control; el modo seguro cubre el intervalo.

## 3. Las prioridades, entrada a entrada

| Prioridad | Entrada | Match (etapa política) | Acción | Cookie | Vigencia |
|---|---|---|---|---|---|
| **65000** | Canal de control (solo diseño in-band) | TCP 6653 ↔ ONOS · LLDP | reenviar hacia/desde la zona de control | canal | permanente |
| **1000** | Mitigación `RATE_LIMIT` | origen → objetivo | `meter` (banda de descarte a la tasa) → caminos | `INC-…` | `hard_timeout = ttl` (300 s inicial) |
| **1000** | Mitigación `BLOCK_SOURCE` | origen (→ cualquier destino) | DROP | `INC-…` | `hard_timeout = ttl` |
| **1000** | `ISOLATE_DEVICE` / `QUARANTINE` | dispositivo | DROP (todo) | `INC-…` | TTL corto (10 min) / TTL de la aprobación |
| **200** | Sesión de perfil | dispositivo → alcance del perfil | → caminos | `SES-…` | `idle_timeout` y tope de la sesión |
| **200** | Elevación | dispositivo → alcance elevado | → caminos | `SES-…` (sesión temporal) | TTL de la elevación |
| **150** | Portal | dispositivo → portal | → caminos | esqueleto | permanente |
| **120** | Par aprendido | `eth_src = MAC ∧ ip_src = IP` | → caminos | esqueleto | permanente |
| **110** | Anti-spoofing | `ip_src = IP ∧ eth_src ≠ MAC` | DROP | esqueleto | permanente |
| **100** | Denegación a gestión | dispositivo → red de gestión | DROP | esqueleto | permanente |
| **20** | Caminos | `ipv4_dst` | → puerto/vía calculada | camino | mientras valga la topología |
| **10** | DHCP y DNS | UDP 67/68, 53 | → caminos | esqueleto | permanente |
| — | Table-miss | — | `PACKET_IN` → aprendizaje o redirección al portal | — | — |

**El esqueleto BASE** (150–10) es la línea base que todo dispositivo lleva **antes de autenticarse**: portal, par MAC/IP, anti-spoofing, denegación a gestión y DHCP/DNS — la lista cerrada de [`access/00`](../../../access/00_auth_controller.md) §3. La sesión **no reemplaza** al esqueleto: convive y lo vence por prioridad (la escalera); el DROP de un académico hacia la gestión es permanente — su sesión nunca lo abre.

**La entrada 65000 existe solo en el diseño in-band** (referencia): el canal de control jamás debe caer en table-miss —o se forma el bucle `PACKET_IN` → ONOS → …—; se marca DSCP CS6 y se encola en una cola estricta para que el tráfico de usuario no lo desplace. Suma +4 reglas por switch (ida, vuelta y LLDP); el prototipo OOB no la necesita.

**Las cookies**, la convención ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §3): los 64 bits codifican tipo y correlativo — bits altos: `0x01` sesión, `0x02` incidente, `0x03` esqueleto, `0x04` camino —; el controlador mantiene el registro string ↔ valor y el retiro es **siempre por cookie**, en todas las tablas. Nada queda pegado (P10).

**Los meters**: un meter por par (origen, objetivo) limitado, con banda de descarte a la tasa del incidente; el controlador lleva el inventario de meters y los libera al retirar la mitigación. Si V2 no confirmara meters nativos, entra la **degradación documentada** de [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4 — el diseño no depende de ella.

**La redirección al portal**: el `PACKET_IN` de un dispositivo sin sesión se responde redirigiendo al portal — por grupo `ALL` o por `PACKET_OUT` según lo que la medición V3/V4 firme (P12 decide con los números; este LLD define ambos tramos del pipeline).

## 4. Los caminos (cierre de flows/05 §8)

- **Prioridad fijada: 20** — por debajo de la escalera (que puede denegar un destino) y por encima de DHCP/DNS (10). El valor era la cuestión abierta de [`flows/05`](../../../flows/05_enrutamiento.md) §8; queda cerrado aquí.
- **Costo por enlace fijado: 1 salto por defecto**, con penalización manual configurable por enlace saturado o de menor capacidad. La métrica era la otra cuestión abierta; el valor fino sale del experimento de rutas.
- **Caminos alternativos — la redundancia del plano de datos.** La topología del prototipo es dual-homed ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §3): cada destino tiene dos caminos disjuntos. La conmutación sigue la regla de V3: si el switch confirma grupos *fast-failover*, cada destino lleva su grupo con puerto de vigía — la conmutación es **local, sin controlador** (P2)—; si no, el controlador reinstala el camino alternativo al recibir `PORT_STATUS`. El tiempo de conmutación se mide en ambos casos (RA-07).
- El cálculo se rehace cuando el grafo cambia (caída/alta de enlace por `PORT_STATUS`, alta de servicio en el inventario); un fallo elimina el enlace del grafo y los caminos afectados se reinstalan.
- **Presupuesto de entradas** ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §5): esqueleto ~6 por dispositivo + sesión ~4 + una entrada de camino por destino en cada switch del camino (o un grupo fast-failover por destino) + mitigaciones simultáneas — ≈ **420–520 entradas repartidas en los diez switches** (nominal ≈ 440; peor caso concurrente ≈ 665; C1/C2 ≈ 44 cada uno, A3 solo esqueleto ≈ 22). El diseño in-band suma +4 por switch (canal de control y LLDP). El llenado real se mide y se reporta (RNF-05, RA-08).

## 5. Determinismo

Las prioridades, la estructura de cookies y la división política/caminos son **constantes del LLD**, no configuración libre: la jerarquía de autoridad no se negocia por parámetro. Lo configurable es lo que las reglas **parametrizan** —tasas, TTL, alcances, umbrales— y eso vive en `bd_politicas` con su auditoría ([`03`](03_datos.md) §3).

## 6. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Instalación del esqueleto en un dispositivo nuevo | Las 6 entradas con sus prioridades | R1.1, P5 |
| Sesión que vence al DROP (académico → servicios) y que nunca abre gestión | La escalera manda | R1.3, R1.6 |
| Mitigación sobre tráfico de sesión en curso | 1000 manda sobre 200 | R4.8, P9 |
| Retiro por cookie de una sesión y de una mitigación | Solo lo propio se retira; nada queda pegado | P10 |
| Caída de un enlace con caminos alternativos | Conmutación (grupo o recálculo) y su tiempo | flows/05 §8, E-04, RA-07 |
| Llenado por lotes hasta `TABLE_FULL` | La capacidad real por tabla | RNF-05, RA-08 |
