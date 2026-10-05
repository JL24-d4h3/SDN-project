# Reglas

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** G — Diseño de bajo nivel (LLD)
**Estado:** Borrador formal para revisión

---

La **regla es la unidad de política materializada**: cada entrada del pipeline del switch es una decisión de la plataforma convertida en match y acción ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §1). El orden de evaluación es una **jerarquía de autoridad**: a mayor prioridad, mayor poder de decidir sobre el paquete. La jerarquía es fija y es la misma en toda la red:

```text
mitigación (1000)   >   sesión y elevación (200)   >   esqueleto BASE (150–100)
>   caminos (20)    >   servicios básicos (10)     >   table-miss (aprendizaje / portal)
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

## 3. Las prioridades, entrada a entrada

| Prioridad | Entrada | Match (etapa política) | Acción | Cookie | Vigencia |
|---|---|---|---|---|---|
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

**Las cookies**, la convención ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §3): los 64 bits codifican tipo y correlativo — bits altos: `0x01` sesión, `0x02` incidente, `0x03` esqueleto, `0x04` camino —; el controlador mantiene el registro string ↔ valor y el retiro es **siempre por cookie**, en todas las tablas. Nada queda pegado (P10).

**Los meters**: un meter por par (origen, objetivo) limitado, con banda de descarte a la tasa del incidente; el controlador lleva el inventario de meters y los libera al retirar la mitigación. Si V2 no confirmara meters nativos, entra la **degradación documentada** de [`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4 — el diseño no depende de ella.

**La redirección al portal**: el `PACKET_IN` de un dispositivo sin sesión se responde redirigiendo al portal — por grupo `ALL` o por `PACKET_OUT` según lo que la medición V3/V4 firme (P12 decide con los números; este LLD define ambos tramos del pipeline).

## 4. Los caminos (cierre de flows/05 §8)

- **Prioridad fijada: 20** — por debajo de la escalera (que puede denegar un destino) y por encima de DHCP/DNS (10). El valor era la cuestión abierta de [`flows/05`](../../../flows/05_enrutamiento.md) §8; queda cerrado aquí.
- **Costo por enlace fijado: 1 salto por defecto**, con penalización manual configurable por enlace saturado o de menor capacidad. La métrica era la otra cuestión abierta; el valor fino sale del experimento de rutas.
- **Caminos alternativos — la redundancia del plano de datos.** La topología del prototipo es dual-homed ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §3): cada destino tiene dos caminos disjuntos. La conmutación sigue la regla de V3: si el switch confirma grupos *fast-failover*, cada destino lleva su grupo con puerto de vigía — la conmutación es **local, sin controlador** (P2)—; si no, el controlador reinstala el camino alternativo al recibir `PORT_STATUS`. El tiempo de conmutación se mide en ambos casos (RA-07).
- El cálculo se rehace cuando el grafo cambia (caída/alta de enlace por `PORT_STATUS`, alta de servicio en el inventario); un fallo elimina el enlace del grafo y los caminos afectados se reinstalan.
- **Presupuesto de entradas** ([`F-02`](../F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §5): esqueleto ~6 por dispositivo + sesión ~4 + una entrada de camino por destino en cada switch del camino (o un grupo fast-failover por destino) + mitigaciones simultáneas — ≈ **350–450 entradas repartidas en los ocho switches**. El llenado real se mide y se reporta (RNF-05, RA-08).

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
