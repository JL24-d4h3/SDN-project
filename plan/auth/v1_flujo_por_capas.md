# Flujo de autenticación y autorización por capas

**Proyecto:** Solución de seguridad para una red de campus académico
**Plan:** Autenticación y autorización — flujo detallado por capas
**Estado:** Borrador formal para revisión

---

El recorrido completo —capa por capa (1 a 7) y mensaje a mensaje— desde que un cable se conecta hasta que el switch tiene instaladas las reglas de la sesión. Implementa las decisiones ya cerradas: la autenticación según [01](../../docs/componentes/01_autenticacion.md) y [04](../../docs/componentes/04_identidades_y_poblaciones.md); la autorización según [02](../../docs/componentes/02_autorizacion.md). La vista de pila (qué protocolo vive en qué capa) está en [access/01](../../access/01_autenticacion_por_capas.md); la mecánica de red original, en [flows/03](../../flows/03_flujo_autenticacion_autorizacion.md).

## 1. Las decisiones que este flujo implementa

| Decisión | Estado | Detalle |
|---|---|---|
| Tres reinos de identidad: comunidad → IdP institucional · operadores → repositorio propio · invitados → fuera | Decidido | [doc 04](../../docs/componentes/04_identidades_y_poblaciones.md) §1–2 |
| **I4 = RADIUS** contra el IdP institucional (FreeRADIUS en el prototipo) | **Decidido** | AAA completo: autentica, autoriza y registra (accounting) |
| **Directorio LDAP** del IdP, detrás de RADIUS | **Decidido** | las cuentas y los atributos viven ahí |
| Portal I3 = HTTPS + formulario, redirección vía OpenFlow | Decidido | la técnica concreta de redirección: detalle de implementación |
| MFA = **TOTP**, obligatorio para todos los operadores | **Decidido** | no para académicos ([doc 04](../../docs/componentes/04_identidades_y_poblaciones.md) §4) |
| Perfiles: **BASE** mínimo (DHCP/DNS/portal) y **ACADÉMICO** nuevo | Decidido | [doc 02](../../docs/componentes/02_autorizacion.md) §4 |
| Autorización: dos planos (RBAC en servicios + motor ABAC-like en el Policy Engine) | Decidido | [doc 02](../../docs/componentes/02_autorizacion.md) §1 |
| Escalera de prioridades | Decidido | el valor exacto del peldaño académico: al implementar (§5.3) |
| Forma de la sesión (cookie o token) y ligadura al dispositivo | Fase F | no cambia el flujo |

## 2. El escenario del flujo

```text
                     ┌────────────────────────────────────────────┐
                     │              PLANO DE CONTROL              │
                     │   Controlador SDN · Policy Engine ·        │
                     │   Auditoría · broker de eventos (I5)       │
                     └───────────────────┬────────────────────────┘
                                         │ OpenFlow (TCP 6653)
   HostA                                 │
   MAC A1 ────── p1 ┌──────────┐ pG ─────┘
                    │    S1    │   (switches Pica8/PicOS)
                    └────┬─────┘
                         │
        ┌────────────────┼───────────────────────┐
        ▼                ▼                       ▼
   Portal + IAM      DHCP/DNS                 SRV-1
   10.0.0.5          10.0.2.1                 10.0.2.10
   (red de gestión)  (red de servicios)       (red de servicios)

   Redes:  10.0.0.0/24 gestión · 10.0.1.0/24 acceso · 10.0.2.0/24 servicios
```

## 3. Vista macro: el flujo entero sobre las capas

```text
tiempo
  │ CAPA 1 · FÍSICA
  │  (1) el cable se conecta — presencia física ────────────► condición de confianza (RP-13)
  │
  │ CAPA 2 · ENLACE
  │  (2) primer tráfico: PACKET_IN ──► el controlador aprende MAC A1 en S1:p1
  │  (3) el switch instala el esqueleto del perfil BASE:
  │        DROP hacia gestión (100) · par MAC/IP (120/110) · DHCP/DNS (10)
  │
  │ CAPA 3 · RED
  │  (4) DHCP: el dispositivo obtiene IP ──► asociación MAC ↔ IP ↔ puerto
  │  (5) DNS resuelve el portal; cualquier HTTP/S a otro destino
  │        sale redirigido: la única puerta abierta es el portal (150)
  │
  │ CAPAS 4/5/6 · TRANSPORTE + TLS
  │  (6) TCP 443 + TLS contra 10.0.0.5 — las credenciales viajan cifradas
  │
  │ CAPA 7 · APLICACIÓN — el login
  │  (7) credenciales en el portal (I3) ──► el IAM verifica:
  │        académico → RADIUS (I4) ──► directorio LDAP del IdP
  │        operador  → repositorio propio (I6) + TOTP (2.º paso)
  │  (8) sesión creada ──► SessionOpened ──► broker ──► Políticas + Auditoría
  │
  │ AUTORIZACIÓN (doc 02)
  │  (9) el Policy Engine evalúa identidad + dispositivo + contexto
  │        ──► perfil + vigencia
  │ (10) FLOW_MOD al switch: reglas de sesión con cookie e idle_timeout
  │        académico → servicios + Internet · operador → reglas hacia gestión (200)
  │
  ▼ ... la sesión vive hasta logout, inactividad (idle_timeout) o MAC_MOVE
```

## 4. Capa por capa, en detalle

### 4.1 Capa 1 — Física: la presencia

Conectar el cable es el único "acto de autenticación" que la red acepta sin más: la presencia física (RP-13) habilita el perfil **BASE** — el mínimo del dispositivo, no un privilegio. No hay protocolo aquí; hay una condición de confianza cuya seguridad depende del control de acceso físico del campus.

### 4.2 Capa 2 — Enlace: el aprendizaje y el esqueleto del BASE

El primer tráfico del dispositivo genera un `PACKET_IN`; el controlador aprende la asociación y el switch instala el esqueleto del BASE:

```text
S1: match eth_src=A1, ip_dst=10.0.0.0/24   → DROP      (prioridad 100 — deny by default hacia gestión)
S1: match ip_src=10.0.1.25, eth_src=A1     → ALLOW     (prioridad 120 — par MAC/IP correcto)
S1: match ip_src=10.0.1.25, eth_src≠A1     → DROP      (prioridad 110 — IP con MAC ajena: anti-spoofing)
S1: match eth_src=A1, UDP 67/68 y 53       → ALLOW     (prioridad 10 — DHCP y DNS)
```

El controlador es la fuente de los pares MAC/IP ([doc 03](../../docs/componentes/03_seguridad.md) §2); la MAC es un **atributo y clave de correlación** (MAC_MOVE), nunca una credencial. **EAPOL/802.1X no interviene**: reservado a puertos sensibles del despliegue real ([access/01](../../access/01_autenticacion_por_capas.md) §3).

### 4.3 Capa 3 — Red: DHCP y la asociación MAC ↔ IP ↔ puerto

```text
dispositivo                        DHCP (10.0.2.1)
    │ DISCOVER (broadcast) ────────────►│
    │◄──────────── OFFER 10.0.1.25      │
    │ REQUEST ─────────────────────────►│
    │◄──────────── ACK                  │
    │   el controlador asocia: MAC A1 ↔ IP 10.0.1.25 ↔ S1:p1
```

Con la IP asignada nacen los pares 120/110 de §4.2. En capa 3 **no hay autenticación**: la IP es un localizador, jamás una credencial. Su papel en el flujo es doble: permitir llegar al portal y alimentar el anti-spoofing (`ip_src` en las reglas).

### 4.4 Capa 4 — Transporte: los puertos que se abren

| Momento | Puertos abiertos | Hacia |
|---|---|---|
| Pre-login (BASE) | UDP 67/68 (DHCP) · 53 (DNS) · TCP 443 | DHCP/DNS + **solo** el portal 10.0.0.5 |
| Post-login (sesión) | los que defina el perfil | servicios académicos + Internet; operadores: además gestión, según rol |

El transporte no autentica: solo entrega. El portal vive en la red de gestión (10.0.0.5); la regla **150** es la excepción quirúrgica al DROP 100 — únicamente `ip_dst=10.0.0.5, tcp=443`.

### 4.5 Capas 5/6 — Sesión/Presentación: TLS

```text
navegador ── ClientHello ──────────────► portal 10.0.0.5:443
navegador ◄─ ServerHello + certificado ─ portal
              (el certificado identifica al PORTAL, no a la persona)
navegador ── clave de sesión ──────────► ...
              desde aquí: credenciales cifradas en tránsito
```

TLS protege el canal (I3 y el tráfico interno de I4); no autentica personas por sí solo. La verificación de la contraseña ocurre en capa 7.

### 4.6 Capa 7 — Aplicación: el login, mensaje a mensaje

#### 4.6.1 La redirección al portal

Cualquier intento de navegación pre-login termina en el portal (redirección vía OpenFlow: `PACKET_IN` → regla). El portal es **la única puerta abierta** del BASE (I3); su formulario es el punto de entrada de las tres poblaciones.

#### 4.6.2 Pista académico — RADIUS contra el IdP institucional

```text
navegador         portal (I3)        IAM/AAA           IdP simulado (I4)
   │  POST usuario+contraseña (HTTPS)  │                     │
   │────────────────►│  credenciales   │                     │
   │                 │────────────────►│  Access-Request     │
   │                 │                 │────────────────────►│  (1) valida contra
   │                 │                 │                     │      el directorio LDAP
   │                 │                 │◄────────────────────│  (2) Accept + atributos
   │                 │◄────────────────│  sesión             │      (o Reject)
   │◄────────────────│  Set-Cookie (o token)                 │
```

El intercambio RADIUS, en detalle:

| Mensaje | Dirección | Campos que importan |
|---|---|---|
| **Access-Request** (UDP 1812) | IAM → IdP | `User-Name` (código/usuario) · `User-Password` (oculta con el secreto compartido) · `Calling-Station-Id` (**MAC A1** — el "desde qué dispositivo") · `NAS-Identifier` / `NAS-Port` (switch y puerto) |
| **Access-Accept** | IdP → IAM | veredicto positivo + atributos (grupo/rol, `Session-Timeout` sugerido) |
| **Access-Reject** | IdP → IAM | veredicto negativo — el portal muestra un error genérico; el intento queda auditado |
| **Accounting-Request** Start/Stop (UDP 1813) | IAM → IdP | registro de la sesión: quién, cuándo, desde dónde |

En el prototipo, el **IdP simulado = FreeRADIUS (la cara AAA) + directorio LDAP (las cuentas)**; en el despliegue real ese conjunto lo provee la universidad y el IAM no cambia (I4 es la interfaz). La contraseña: viaja del navegador al IAM por HTTPS, de allí al IdP por la red interna, y **el IAM la descarta tras verificar** — no la almacena ni la registra ([doc 01](../../docs/componentes/01_autenticacion.md) §5).

#### 4.6.3 Pista operador — repositorio propio + TOTP

El operador no usa I4: su identidad vive en el **repositorio de identidades privilegiadas** de la plataforma (I6). El login es en dos pasos:

```text
paso 1: usuario + contraseña ──► el IAM verifica contra el repositorio propio
paso 2: código TOTP ──────────► el IAM lo valida contra el secreto del operador
                                 (app autenticadora; sin internet — RFC 6238)
        ambos pasos OK ───────► sesión con el rol del operador
```

MFA es **obligatorio para todos los operadores** (TI, Admin, SA) y no existe para académicos ([doc 04](../../docs/componentes/04_identidades_y_poblaciones.md) §4). El producto concreto del segundo factor es TOTP; su aprovisionamiento, detalle de Fase F.

#### 4.6.4 La sesión

```text
sesión = identidad + rol + dispositivo (MAC) + punto de conexión (switch/puerto)
       + instante de apertura + vigencia
```

Su forma (cookie de sesión o token) es Fase F; lo decidido es su efecto: **la sesión es el SSO** — un solo login abre la red que el rol permite y, para operadores, la consola/APIs con ese rol (I7). El IAM publica `SessionOpened` → broker (I5) → **Policy Engine** (decide) + **Auditoría** (registra); el accounting guarda quién, cuándo y desde qué dispositivo.

## 5. La autorización: del veredicto a las reglas

### 5.1 La decisión (Policy Engine)

```text
Policy Engine evalúa la tupla:
  identidad (reino) + rol + dispositivo (¿registrado? P7) + ubicación (switch/puerto)
  + contexto (¿incidente activo?) + recurso + acción + vigencia
        │
        ▼
  perfil + duración        (la denegación también se decide y se audita)
```

Regla de oro del registro (P7): **el registro no concede; habilita el intento**. Un operador con credenciales válidas desde un dispositivo no registrado no eleva: su sesión queda en BASE y el hecho se audita (y para elevar, la vía es registrar el dispositivo — P30, un cambio de datos, no una regla de switch).

### 5.2 La traducción (controlador → FLOW_MOD)

```text
decisión: ACADÉMICO · MAC A1 · S1:p1 · vigencia T
   │ orden northbound (I2)
   ▼
FLOW_MOD en S1:  match in_port=p1, eth_src=A1, ip_src=10.0.1.25[, puertos]
                 acciones: OUTPUT — cookie=sesión, idle_timeout=T
```

Los campos del match **cruzan capas** — así se cumple la autorización en el switch:

| Campo | Capa | Qué expresa |
|---|---|---|
| `in_port` | 1/2 | dónde está conectado |
| `eth_src` | 2 | el dispositivo (junto a `ip_src`: anti-spoofing) |
| `ip_src` | 3 | la dirección aprendida por DHCP |
| puerto TCP/UDP destino | 4 | qué servicio se alcanza |
| prioridad + cookie + timeout | — | precedencia, origen y vigencia de la regla |

La autorización **se cumple en el switch**, no en el portal ni en la consola: sin decisión del Policy Engine no hay reglas, y sin reglas no hay conectividad ([doc 02](../../docs/componentes/02_autorizacion.md) §5).

### 5.3 La escalera de prioridades (estado)

```text
1000 ─ mitigación                (manda sobre todo — ciclo R4)
 200 ─ sesión privilegiada       (TI acotado · Admin/SA hacia gestión)
 150 ─ portal                    (la única puerta pre-sesión)
 120 ─ par MAC/IP correcto       (ALLOW del anti-spoofing)
 110 ─ IP con MAC ajena          (DROP del anti-spoofing)
 100 ─ red de gestión            (DROP del BASE — deny by default)
  10 ─ DHCP y DNS                (vida pre-sesión)
  ── ─ sesión académica          (servicios + Internet — peldaño a fijar al implementar)
```

| Peldaño | Estado |
|---|---|
| 1000 · 200 · 150 · 120 · 110 · 100 · 10 | Decididos |
| **ACADÉMICO** (servicios + Internet) | **A definir el valor al implementar** ([doc 02](../../docs/componentes/02_autorizacion.md) §6–7); ya reflejado en la serie de flujo ([diagrams/04](../../flows/diagrams/04_flujo_usuario_generico.md) §6) |

### 5.4 El ciclo de vida y el cierre

```text
sesión viva ──logout──► SessionClosed ──► retiro de reglas (cookie) ──► BASE
     │
     ├──idle_timeout──► el switch expira la regla solo ──► BASE
     └──MAC_MOVE──────► evento ──► contención/investigación ([doc 05](../../docs/componentes/05_historial_de_dispositivo.md))
```

La elevación temporal (LABORATORIO, P28/P29) sigue el mismo ciclo: `PENDING → ELEVATED(TTL) → expira → BASE`, decidida por el Policy Engine y registrada en Auditoría.

## 6. Los dos recorridos completos

### 6.1 Académico (alumno o profesor)

```text
dispositivo         red (S1 + controlador)        portal + IAM (I3)      IdP simulado (I4)
    │  (1) cable ───►│ aprende MAC A1 en p1        │                      │
    │                 │ BASE: 100/120/110/10        │                      │
    │  (2) DHCP ─────►│ IP 10.0.1.25                │                      │
    │  (3) HTTPS a cualquier destino ─────────────►│                      │
    │      ◄── redirección: solo el portal (150) ──│                      │
    │  (4) usuario + contraseña (TLS) ────────────►│  (5) Access-Request ►│
    │                 │                             │◄── Accept+atributos ─│
    │◄── Set-Cookie · sesión ──────────────────────│  (6) SessionOpened   │
    │                 │◄── identidad + rol ─────────│      → broker        │
    │                 │  (7) Policy Engine decide: ACADÉMICO               │
    │                 │  (8) FLOW_MOD: cookie + idle_timeout               │
    │◄── servicios académicos + Internet ──────────│                      │
```

### 6.2 Operador (TI, Admin o SA)

```text
PC del operador     red (S1 + controlador)        portal + IAM (plataforma)
    │  (1) cable ───►│ BASE — igual que cualquier dispositivo
    │  (2) HTTPS al portal ───────────────────────►│
    │                 │  (3) paso 1: usuario + contraseña (repositorio propio, I6)
    │                 │  (4) paso 2: código TOTP (app autenticadora)
    │                 │  (5) sesión: identidad + rol de operador
    │                 │  (6) Policy Engine: ¿dispositivo registrado? (P7)
    │                 │        sí ──► perfil del rol (reglas hacia gestión, 200)
    │                 │        no ──► elevación denegada: sigue en BASE (auditado)
    │◄── consola/APIs con el rol (I7) + reglas de red ──│
```

## 7. Lo que este flujo no incluye

| Elemento | Estado |
|---|---|
| EAPOL/802.1X + EAP (EAP-TLS, PEAP…) | Fuera del prototipo (decisión); puertos sensibles del despliegue real |
| SSO federado (delegar el login al SSO institucional) | Fuera del prototipo; reevaluable en despliegue real |
| Invitados (autoregistro + TTL) | Fuera de alcance; el lugar queda reservado |
| Red inalámbrica | Fuera de alcance |
| Acceso remoto del SA | Contemplado ([diagrams/03](../../flows/diagrams/03_flujo_superadministrador.md) §3); su secuencia no entra aquí |
| Forma de la sesión (cookie/token) y ligadura al dispositivo | Fase F |
| Valor del peldaño académico en la escalera | Al implementar (§5.3) |

## 8. Referencias

- [01 — Elementos de autenticación](../../docs/componentes/01_autenticacion.md) · [02 — Elementos de autorización](../../docs/componentes/02_autorizacion.md) · [03 — Elementos de seguridad](../../docs/componentes/03_seguridad.md)
- [04 — Identidades y poblaciones](../../docs/componentes/04_identidades_y_poblaciones.md) · [05 — Historial de dispositivo](../../docs/componentes/05_historial_de_dispositivo.md)
- [access/01 — Autenticación por capas](../../access/01_autenticacion_por_capas.md)
- [flows/03 — Flujo con autenticación y autorización](../../flows/03_flujo_autenticacion_autorizacion.md) · [flows/diagrams/04](../../flows/diagrams/04_flujo_usuario_generico.md)
- [D-07 — Interfaces principales](../../docs/fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md) (I2–I7)
