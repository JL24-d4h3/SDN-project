# El controlador en el flujo de autenticación y autorización

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Control de acceso — 0
**Estado:** Borrador formal para revisión

---

La serie de flujo y las partes 1 y 2 de esta serie describen las capas y los mensajes, pero el **controlador** —quien observa el tráfico, mantiene las asociaciones y materializa cada decisión— aún no aparecía en el recorrido. Este documento lo pone en su lugar: el flujo completo de autenticación y autorización con sus tres ejecutores —**servicios**, **controlador** y **switch**— y la relación exacta entre ellos. Las capas están en [`01_autenticacion_por_capas.md`](01_autenticacion_por_capas.md) y [`02_autorizacion_por_capas.md`](02_autorizacion_por_capas.md); el detalle mensaje a mensaje de los protocolos, en [`plan/auth`](../plan/auth/v1_flujo_por_capas.md); la mecánica de red original, en [`flows/03`](../flows/03_flujo_autenticacion_autorizacion.md).

## 1. Tres actores, tres papeles

| Actor | Su papel en el flujo | Lo que jamás hace |
|---|---|---|
| **Servicios** — portal, IAM/AAA, Policy Engine, registro de dispositivos, auditoría | **Autentican** (el IAM: contra el IdP o el repositorio propio), **deciden** (el Policy Engine), **habilitan** (el registro, P7) y **registran** (auditoría y accounting). | Tocar la red: ningún servicio instala reglas ni habla con el switch. |
| **Controlador SDN** | **Aprende** las asociaciones desde el tráfico (`PACKET_IN`), mantiene topología y asociaciones, **traduce** cada decisión a reglas (`FLOW_MOD`) y **retira** lo que expira. | Autenticar; decidir políticas; ver credenciales. |
| **Switch** (Pica8/PicOS) | **Ejecuta** las reglas a la velocidad del plano de datos y **reporta** eventos y contadores. | Decidir; juzgar tráfico; autenticar. |

La relación, en una frase: **los servicios deciden, el controlador traduce, el switch ejecuta**; en el sentido inverso, **el switch observa, el controlador aprende, los servicios registran** ([`06_responsabilidades.md`](../docs/fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/06_responsabilidades.md): cada componente tiene responsabilidad y no-responsabilidad explícitas).

```text
   SERVICIOS (portal · IAM/AAA · Policy Engine · registro · auditoría)
   autentican · deciden · registran
        ▲ │
        │ ▼   ← I2 · northbound: la orden de política (el «qué»)
   CONTROLADOR SDN
   aprende · traduce · retira
        ▲ │
        │ ▼   ← I1 · southbound: OpenFlow (el «cómo»)
   SWITCH (Pica8/PicOS)
   ejecuta · reporta
```

**Lo que nunca cruza.** Las credenciales viajan entre el navegador y el portal (I3) y entre el IAM y el IdP (I4) o el repositorio propio (I6): rutas internas de los servicios. **Por I1 ni por I2 cruza ningún secreto**: el controlador no ve un usuario, una contraseña ni un código TOTP, y el switch solo transporta TLS. Su relación con la autenticación es de **ausencia deliberada**; con la autorización, de **traducción fiel**: recibe una decisión ya tomada y la convierte en reglas — no la decide ni la altera.

## 2. El escenario que el controlador construye

Antes de que exista cualquier identidad, el controlador ya montó lo que el flujo necesita (serie de flujo, [`02_flujo_base_arranque.md`](../flows/02_flujo_base_arranque.md)):

- **El canal de control** con cada switch — handshake HELLO/FEATURES, latidos ECHO: el medio por el que viajarán todas las órdenes.
- **La topología** (LLDP por puerto): cómo llegar desde el acceso hasta el portal, el DHCP/DNS y los servicios.
- **La table-miss**: todo paquete que ninguna entrada sepa encaminar llega al controlador — la red avisa antes de que nadie decida.
- **El aprendizaje**: el primer tráfico de cada dispositivo le da su MAC y su puerto; el DHCP, su IP. Con eso mantiene la asociación `host ↔ MAC ↔ IP ↔ switch ↔ puerto` —la fuente del anti-spoofing ([`03_seguridad.md`](../docs/componentes/03_seguridad.md) §2)— y publica `DeviceConnected` (→ registro, monitor, auditoría).

En esta etapa el controlador no sabe —ni pregunta— quién es la persona: sabe dónde está y cómo se llama su hardware.

## 3. El flujo completo, fase por fase

### 3.1 Fase 1 — El dispositivo aparece: el aprendizaje

```text
(1) el primer paquete del dispositivo (DHCPDISCOVER) llega a S1
(2) ninguna entrada coincide → table-miss → PACKET_IN
      motivo OFPR_NO_MATCH · in_port = p1 · buffer_id
(3) el controlador aprende:  MAC A1 ↔ S1:p1
    publica:                 DeviceConnected (I5) → registro · monitor · auditoría
    instala:                 esqueleto BASE (FLOW_MOD) y responde el paquete (PACKET_OUT)
(4) … el DHCP completa en el plano de datos …
    la IP aparece → el controlador suma los pares 120/110 (anti-spoofing)
```

El esqueleto del perfil BASE, tal como queda instalado en el switch (perspectiva del pipeline):

```text
S1: match eth_src=MAC A1, ip_dst=10.0.0.5, tcp=443  → ALLOW   (prioridad 150 — portal)
S1: match eth_src=MAC A1, ip_src=IP A1              → ALLOW   (prioridad 120 — par MAC/IP)
S1: match ip_src=IP A1, eth_src≠MAC A1              → DROP    (prioridad 110 — IP con MAC ajena)
S1: match eth_src=MAC A1, ip_dst=red_de_gestion     → DROP    (prioridad 100 — deny by default)
S1: match eth_src=MAC A1, UDP 67/68 y 53            → ALLOW   (prioridad 10 — DHCP y DNS)
```

Nada de esto tiene que ver con la identidad: es el controlador construyendo su inventario de dispositivos, igual para todos.

### 3.2 Fase 2 — BASE: la red mínima

Con el esqueleto instalado, el dispositivo vive en el mínimo: DHCP, DNS y el portal. Un intento de navegación pre-login no tiene entrada que lo permita → `PACKET_IN` → el controlador materializa la **redirección al portal** (redirección vía OpenFlow, [`01_autenticacion.md`](../docs/componentes/01_autenticacion.md) §7). Todo lo que apunte a la red de gestión: DROP (100).

En régimen, el controlador **no está en el camino**: los paquetes viajan por las entradas ya instaladas.

### 3.3 Fase 3 — El login: los servicios autentican

```text
navegador ── HTTPS (regla 150) ──► portal (10.0.0.5) ──► IAM
                                    IAM ── RADIUS (I4) ──► IdP        ← comunidad
                                    IAM ── repositorio (I6) + TOTP    ← operadores
                                                        │
                        sesión creada ◄─────────────────┘
                        SessionOpened (I5) → Policy Engine · Auditoría
```

Tres cosas que conviene fijar de esta fase:

- **El controlador no está en el camino.** La regla 150 ya lleva el HTTPS al portal; la conexión fluye por el plano de datos sin consultarle nada. (El controlador solo recibe por `PACKET_IN` los paquetes que ninguna regla sepa encaminar — y el tráfico del portal no es uno de ellos.)
- **El switch no ve las credenciales.** Transporta TLS: ve MAC, IP y puertos (los campos de sus reglas), nunca el contenido. Las credenciales cruzan I3 y, del lado de los servicios, I4 o I6.
- **La autenticación no conecta nada por sí sola.** Su producto —identidad + rol— entra al Policy Engine, que decide ([`01_autenticacion.md`](../docs/componentes/01_autenticacion.md) §1).

### 3.4 Fase 4 — La decisión se vuelve reglas: aquí entra el controlador

El Policy Engine evalúa su tupla y decide perfil y vigencia; la orden viaja por la API northbound (I2) y el controlador la traduce — el **«cómo»** (match exacto, prioridad, cookie, timeouts) es responsabilidad suya ([`07_interfaces_principales.md`](../docs/fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md), I2).

Pista académico:

```text
decisión: ACADÉMICO · MAC A1 · S1:p1 · vigencia T
   │ orden northbound (I2) — aplicada con confirmación
   ▼
FLOW_MOD en S1:  match in_port=p1, eth_src=MAC A1, ip_src=10.0.1.25[, puertos]
                 acciones: OUTPUT — cookie=sesión · idle_timeout=T
```

Pista operador (la regla de sesión vence al DROP del BASE por prioridad):

```text
FLOW_MOD en S1:  match in_port=pX, eth_src=MAC_PC-ADMIN, ip_dst=red_gestion, tcp=22/443
                 → OUTPUT pG     (prioridad 200 · cookie=sesión · idle_timeout = duración de sesión)

Antes (BASE), el mismo tráfico:  match eth_src=MAC_PC-ADMIN, ip_dst=red_gestion → DROP (100)
```

La regla de sesión **no reemplaza** al esqueleto: convive con él y lo vence por prioridad (la escalera). El DROP del académico hacia la gestión es permanente — su sesión nunca la abre ([`03_flujo_autenticacion_autorizacion.md`](../flows/03_flujo_autenticacion_autorizacion.md) §6).

### 3.5 Fase 5 — La sesión vive

- El tráfico de la sesión fluye por las entradas instaladas: el controlador no participa.
- El switch cuenta por flujo, puerto y tabla; el monitor los lee (I8: monitor → controlador → switches) para su línea base.
- El IAM registra el accounting; para operadores, la misma sesión abre la consola y las APIs con su rol (I7): **la sesión es el SSO**.

### 3.6 Fase 6 — El cierre: del hecho al registro

```text
logout        portal → IAM → SessionClosed (I5) · orden al controlador (I2)
              → retiro de las reglas por cookie → BASE
inactividad   el switch expira la entrada solo (cookie + idle_timeout,
              con FLOW_REMOVED activado) → FLOW_REMOVED → el controlador lo sabe primero → BASE
MAC_MOVE      la misma MAC aparece en otro puerto → el controlador detecta la
              incoherencia → evento → contención e investigación (historial de dispositivo)
```

En los tres casos el resultado es el mismo: las reglas de sesión desaparecen —por orden o por expiración— y el esqueleto BASE, que nunca se fue, vuelve a mandar.

### 3.7 La vía del operador: mismas piezas, un peldaño más

- La autenticación suma un segundo paso (TOTP contra el repositorio propio, I6); el controlador sigue ausente de esa conversación.
- La decisión es por rol y sus reglas alcanzan la red de gestión (prioridad 200, §3.4), además de la consola y las APIs (I7).
- El dispositivo debe hacer match con el registro privilegiado (P7): **el registro no concede; habilita el intento**. Credenciales correctas desde un dispositivo no registrado: cero reglas nuevas, la sesión queda en BASE y el hecho se audita.

## 4. La secuencia completa

```text
HostA (A1)           S1                    Controlador                Servicios
(MAC A1)             (Pica8/PicOS)         (SDN)                      (portal · IAM · Policy)
   │                 │                       │                         │
   │               ── FASE 1 · EL DISPOSITIVO APARECE ──               │
   │ (1) DHCPDISCOVER│                       │                         │
   │────────────────►│                       │                         │
   │                 │ (2) PACKET_IN         │                         │
   │                 │ sin match · in_port = p1                        │
   │                 │──────────────────────►│                         │
   │                 │                       │ (3) aprende A1 ↔ S1:p1  │
   │                 │                       │ → DeviceConnected (I5)  │
   │                 │◄──────────────────────│ (4) esqueleto BASE      │
   │                 │◄──────────────────────│ FLOW_MOD + PACKET_OUT   │
   │◄────────────────│  DHCPOFFER            │                         │
   │    … el DHCP completa en el plano de datos …                      │
   │                 │◄──────────────────────│ (5) pares 120/110       │
   │                 │                       │ (la IP 10.0.1.25        │
   │                 │                       │ apareció)               │
   │                 │                       │                         │
   │                ── FASE 2 · BASE: LA RED MÍNIMA ──                 │
   │ (6) navegación  │                       │                         │
   │────────────────►│──────────────────────►│ (7) redirección al      │
   │◄────────────────│◄──────────────────────│ portal (OpenFlow)       │
   │                 │                       │                         │
   │                      ── FASE 3 · EL LOGIN ──                      │
   │ (8) HTTPS al portal (TLS) — regla 150                             │
   │────────────────►│───────────────────────┼────────────────────────►│
   │                 │                       │ (9) el IAM verifica:    │
   │                 │                       │ RADIUS (I4) → IdP       │
   │                 │                       │ o repo (I6) + TOTP      │
   │                 │                       │ SessionOpened (I5)      │
   │                 │◄──────────────────────┼─────────────────────────│
   │◄────────────────│  sesión (cookie/token)│                         │
   │                 │                       │                         │
   │            ── FASE 4 · LA DECISIÓN SE VUELVE REGLAS ──            │
   │                 │                       │◄── (10) orden I2────────│
   │                 │◄──────────────────────│ (11) FLOW_MOD: reglas   │
   │                 │                       │cookie · idle_timeout = T│
   │                 │──────────────────────►│ confirmación            │
   │                 │                       │                         │
   │                   ── FASE 5 · LA SESIÓN VIVE ──                   │
   │ (12) servicios académicos + Internet                              │
   │────────────────►│───────────────────────┼────────────────────────►│
   │                 │ la regla de sesión los lleva                    │
   │                 │ (el controlador no participa)                   │
   │                 │                       │                         │
   │                     ── FASE 6 · EL CIERRE ──                      │
   │ (13) logout · inactividad (idle_timeout) · MAC_MOVE               │
   │                 │── FLOW_REMOVED ──────►│ (14) retira por cookie  │
   │                 │◄── FLOW_MOD (delete)──│ SessionClosed (I5)      │
   │ vuelta a BASE   │                       │                         │
```

En el diagrama, `┼` marca que el tráfico cruza esa columna sin involucrar al actor.

## 5. Qué cruza cada interfaz

| Interfaz | Entre | En este flujo cruza |
|---|---|---|
| **I1** — southbound (OpenFlow, TCP 6653) | controlador ↔ switches | `PACKET_IN` (aprendizaje, redirección, MAC_MOVE), `FLOW_MOD` (esqueleto BASE, reglas de sesión, retiro), `FLOW_REMOVED`, `PORT_STATUS`, consultas de contadores (I8) — **jamás credenciales** |
| **I2** — northbound (API del controlador) | servicios ↔ controlador | la orden de política («qué»: perfil X para la MAC Y en el puerto Z por T), aplicada con confirmación; consultas de topología, asociaciones y estado de reglas — **jamás credenciales** |
| **I3** — portal cautivo | poblaciones ↔ IAM/AAA | credenciales y sesión, bajo HTTPS (TLS) |
| **I4** — identidad institucional | IAM/AAA ↔ IdP | verificación de la comunidad (RADIUS; directorio LDAP detrás) y accounting |
| **I6** — persistencia | IAM ↔ repositorio propio | verificación de operadores, con TOTP |
| **I5** — broker de eventos | servicios ↔ servicios | `DeviceConnected` (lo publica el controlador), `SessionOpened` / `SessionClosed` (los publica el IAM) |

Las credenciales cruzan I3, I4 e I6. Ninguna cruza I1 ni I2: el controlador y el switch operan sobre identidades ya resueltas —MAC, perfil, puerto—, nunca sobre secretos.

## 6. Cuestiones abiertas

- **Forma concreta de la API northbound (I2)** y esquema de la orden de perfil: Fase F.
- **Técnica concreta de la redirección al portal** (qué captura el controlador y cómo responde): detalle de implementación.
- **Punto exacto de aprendizaje del par MAC ↔ IP** (la observación del DHCP o el primer paquete con la IP): detalle de implementación.
