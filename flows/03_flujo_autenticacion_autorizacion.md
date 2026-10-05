# Flujo con autenticación y autorización

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Descripción del flujo — parte 3 de 6
**Estado:** Borrador formal para revisión

---

Esta parte añade la capa de identidad sobre el flujo base (parte 2). La decisión central del modelo:

> **La red controla por defecto el dispositivo (perfil BASE: DHCP, DNS y el portal). Para obtener más —el acceso de persona (perfil ACADÉMICO) o una sesión de rol— se exige identidad: el académico se autentica contra el IdP institucional; el operador, contra el repositorio propio de la plataforma, con MFA y dispositivo registrado.**

## 1. Premisa de confianza: la presencia física

El campus es de acceso controlado: para conectar un cable hay que haber entrado físicamente. El proyecto adopta como restricción (RP-13) que **la presencia física en el campus es condición de confianza inicial suficiente para el perfil BASE** — el mínimo del dispositivo (DHCP, DNS y el portal), no un privilegio. Nadie pasa por 802.1X al conectar: la identidad se pide más arriba, en el portal (capa 7), cuando el dispositivo quiere salir del mínimo. La consecuencia aceptada es que la seguridad física del campus forma parte del perímetro de seguridad.

Esta premisa elimina la distinción estudiante/profesor a nivel de red: ambos son **usuario académico**, un consumidor ordinario de servicios sin privilegios de infraestructura. Si la plataforma educativa distingue internamente entre alumno y docente, es asunto de la aplicación, no de la red.

## 2. El perfil BASE y el principio de mínimo privilegio

Todo dispositivo que conecta recibe el **perfil BASE** — el mínimo pre-login:

```text
PERMITIDO (perfil BASE)
  DHCP y DNS (existir en la red)
  el portal (la única puerta hacia la red de gestión)

DENEGADO (por defecto)
  SSH/Telnet/NETCONF hacia infraestructura
  OpenFlow y cualquier acceso al controlador
  SNMP administrativo y consolas de gestión
  interfaces de administración
  servicios sensibles

CON SESIÓN (fuera del BASE)
  servicios académicos e Internet → perfil ACADÉMICO (§5)
  los destinos del rol → operadores (§5)
```

En el plano de datos, esto se materializa como entradas concretas (perspectiva del pipeline, parte 1 §7). Para el dispositivo recién conectado el controlador instala el esqueleto del BASE:

```text
S1: match eth_src=MAC_host, ip_dst=10.0.0.5, tcp=443 → ALLOW    (prioridad 150 — portal)
S1: match eth_src=MAC_host, ip_src=IP_host           → ALLOW    (prioridad 120 — par aprendido)
S1: match ip_src=IP_host, eth_src≠MAC_host           → DROP     (prioridad 110 — IP con otra MAC)
S1: match eth_src=MAC_host, ip_dst=red_de_gestion    → DROP     (prioridad 100)
S1: match eth_src=MAC_host, UDP 67/68 y 53           → ALLOW    (prioridad 10 — DHCP y DNS)
```

**El BASE es una lista cerrada:** esas entradas —y ninguna otra— son lo único alcanzable sin identidad; el resto de la intranet queda denegado por defecto y solo se abre con la autenticación y su autorización.

## 3. El registro de dispositivos y la regla del "no match"

Decisión de diseño clave: **no se registra a todos los dispositivos; se registra solo a los dispositivos de los operadores privilegiados.** Los dispositivos académicos no figuran en ningún catálogo de red.

- El **registro de dispositivos privilegiados** guarda, por cada equipo de un Especialista de TI, Administrador de Red o Superadministrador: MAC, tipo de equipo, titular, rol asociado, vigencia y responsable del registro.
- La regla de aplicación es la inversa de un catálogo total: **todo dispositivo que no haga match con este registro arranca en perfil BASE.** No hay que dar de alta nada más; el default cubre al 99% de la población, y su salida del mínimo (el login del académico, §5) no pasa por este registro.
- El registro **no** autentica a nadie: solo habilita el intento de elevación de los operadores. RADIUS autentica *personas* — a la comunidad contra el IdP (I4) y a los operadores contra el repositorio propio del IAM (I6). El registro vive en un servicio de datos propio, separado, que además sirve de auditoría: quién registró qué equipo, cuándo y con qué vigencia.
- El registro no concede privilegios por sí solo: un dispositivo registrado **y** sin login sigue teniendo perfil BASE (§4). El match con el registro solo habilita la posibilidad de elevar.

## 4. La PC del operador sin login es una PC cualquiera

El punto más demostrable del modelo: la laptop del Administrador de Red, conectada en la sala de administración, **antes del login tiene perfil BASE**. La ubicación física no concede privilegios; la MAC tampoco (la MAC es un atributo del dispositivo, no una credencial: cualquiera puede falsificarla).

```text
PC-ADMIN conectada → S1 → el controlador aprende el dispositivo (PACKET_IN)
   identidad = desconocida
   perfil = BASE
   → SSH a switches: DROP · OpenFlow: DROP · consola: DROP
```

## 5. El login: dos pistas en el mismo portal

Salir del BASE exige identidad, y la identidad se pide en **un solo portal cautivo** (I3), con dos pistas según la población:

```text
académico:  usuario + contraseña ──► IAM ──RADIUS (I4)──► IdP institucional
                                                          (directorio LDAP detrás)
operador:   paso 1, usuario + contraseña ──► repositorio de identidades
                                             privilegiadas (I6, en la plataforma)
            paso 2, código TOTP ──► validado contra el secreto del operador
                                    (MFA obligatorio para todos los operadores)
```

El operador **no usa el IdP institucional**: su reino es el repositorio propio de la plataforma (doc 04 §2). El académico, en cambio, no toca el registro privilegiado: su login obtiene el perfil ACADÉMICO sobre la misma maquinaria (portal, RADIUS, Policy Engine). Con la identidad verificada:

```text
PC-ADMIN
  ▼
Policy Engine
  identidad autenticada + dispositivo (match con el registro, P7)
  + ubicación + contexto + vigencia
  ▼
Decisión: perfil ADMIN_RED para esta sesión, desde esta MAC, en este puerto
```

El Policy Engine combina **identidad + atributos + contexto + recurso + acción + vigencia** — más ABAC que RBAC puro: el rol es solo uno de los atributos de la decisión.

## 6. Traducción a la red: FLOW_MOD

Con la decisión tomada, el controlador la materializa en el switch donde está conectada la PC:

```text
S1: match in_port=pX, eth_src=MAC_PC-ADMIN, ip_dst=red_gestion, tcp=22/443
    → OUTPUT pG        (prioridad 200, idle_timeout = duración de sesión)

Antes (perfil BASE), el mismo tráfico:
S1: match eth_src=MAC_PC-ADMIN, ip_dst=red_gestion
    → DROP             (prioridad 100)
```

La regla nueva tiene **mayor prioridad** que el DROP del perfil BASE, y un `idle_timeout` ligado a la sesión: si el operador cierra sesión o queda inactivo, el switch elimina la entrada solo y el dispositivo regresa a BASE. La sesión académica usa el mismo mecanismo (cookie + idle_timeout) para sus reglas de servicios e Internet — con una diferencia: su DROP hacia la gestión es permanente, la sesión académica nunca la abre:

```text
S1: match eth_src=MAC_academico, ip_dst=red_gestion → DROP  (siempre activo)
```

En todos los casos, las reglas de la sesión se instalan **solo en el switch de acceso**: el interior no conoce identidades — reenvía por destino, sobre los caminos ya instalados (parte 5 §1 y §5).

## 7. Elevación temporal de un usuario académico

El usuario académico puede pedir acceso temporal a recursos que su perfil no cubre si lo justifica — por ejemplo, un estudiante del Pabellón V necesita acceder al servidor de laboratorio durante una práctica de dos horas, o un estudiante de telecomunicaciones necesita la nube privada de la universidad:

```text
ACADÉMICO
  │ solicitud: acceso LABORATORIO, 2 h, recursos X/Y/Z
  ▼
PENDING  (el Administrador de Red revisa la solicitud)
  │ aprobación
  ▼
ELEVATED (TTL = 2 h)   ← perfil ACADÉMICO + LABORATORIO temporal
  │ expiración
  ▼
ACADÉMICO
```

La política temporal se modela como condición (ABAC-like):

```text
SI  identity = usuario X
Y  device ∈ dispositivos autorizados del pabellón
Y  location = Pabellón V
Y  time ∈ [14:00, 16:00]
Y  destination = LAB-01
Y  protocol = SSH
ENTONCES  ALLOW (con TTL)
SINO  DENY
```

El TTL es esencial: un permiso excepcional concedido para una práctica no puede convertirse en un privilegio permanente por olvido. Los **perfiles de acceso** resultantes del modelo:

| Perfil | Quién | Cómo se obtiene | Duración |
|---|---|---|---|
| BASE | Cualquier dispositivo conectado | Automático (presencia física) | Indefinida mientras esté conectado |
| ACADÉMICO | Comunidad universitaria (alumno o profesor) | Login en el portal (IdP institucional, sin MFA) | Sesión (idle_timeout) |
| LABORATORIO / INVESTIGACIÓN / PRACTICANTE_DTI | Usuarios académicos con necesidad justificada | Solicitud + aprobación | Temporal (TTL) |
| TI / ADMIN_RED / SUPER_ADMIN | Operadores privilegiados | Dispositivo registrado + login con MFA (portal/AAA) | Sesión (idle_timeout) |

## 8. El registro de los operadores privilegiados

La existencia de una persona en el registro no significa que su PC tenga privilegios. Son tres cosas distintas: la **identidad** (quién es), el **rol** (qué puede hacer) y la **sesión/dispositivo** (desde dónde y bajo qué contexto lo ejerce). El flujo de registro tiene tres fases:

**Fase A — Solicitud.** Un alta o cambio de privilegios se pide con: persona, identificación institucional, rol solicitado, área, justificación, vigencia y solicitante/aprobador. No existe el "crear usuario → elegir rol → guardar": tiene que haber una decisión de autorización.

**Fase B — Aprobación.** La jerarquía define quién registra a quién:

| Acción | Especialista de TI | Administrador de Red | Superadministrador |
|---|---|---|---|
| Registrar Especialista de TI | — | ✓* | ✓ |
| Registrar Administrador de Red | — | — | ✓ |
| Registrar Superadministrador | — | — | ✓ |
| Registrar dispositivo en el registro privilegiado | — | ✓ | ✓ |

`✓*` según se delegue la función. El registro resultante incluye `valid_from`/`valid_until`: la vigencia no es indefinida (p. ej. un Especialista de TI puede estar habilitado solo por un ciclo).

**Fase C — Autenticación.** El registro **no modifica ningún flujo**. El operador solo obtiene sus privilegios cuando se autentica (§5) y el Policy Engine decide. La cadena completa:

```text
Registro (identidad + rol + dispositivo, con vigencia)
        ≠
Privilegios activos (solo tras login + decisión del Policy Engine
                     + traducción a flujos por el controlador)
```

## 9. Suplantación de MAC: detectar, no confiar

Desde SDN no se puede impedir que un usuario cambie la MAC de su interfaz. La MAC no es una credencial. Lo que sí se puede hacer es detectar la incoherencia y reaccionar:

```text
MAC X vista en S1:p3  →  luego vista en S5:p8       →  evento MAC_MOVE
MAC X con IP distinta a la asociada                 →  evento de incoherencia
MAC X con identidad distinta a la asociada          →  evento de incoherencia
```

Según la severidad, la respuesta escala: alerta → bloqueo del puerto → VLAN de cuarentena → investigación. Para puertos sensibles (infraestructura, zonas restringidas) se añaden mecanismos de puerto: **port security** (puerto → MACs permitidas) y **802.1X** en los accesos administrativos. Ninguno demuestra quién es la persona: controlan el dispositivo; la identidad la demuestra el login.

## 10. Dispositivo nuevo: el default lo cubre

La topología es rígida por diseño, pero la solución debe tolerar la aparición de un dispositivo nuevo. El flujo es exactamente el del default: el controlador detecta la MAC por el PACKET_IN del primer tráfico, el dispositivo **no hace match con el registro privilegiado** y recibe perfil BASE. Si ese dispositivo va a ser de un operador, se lo registra (§8) y desde entonces puede elevar. El caso académico no requiere registro ni configuración: arranca en BASE como cualquiera y su login (§5) es el camino por defecto hacia ACADÉMICO.

## 11. La jerarquía de confianza completa

```text
Sin presencia en campus           →  sin acceso
Presencia física en campus        →  perfil BASE (el mínimo del dispositivo)
Login de la comunidad (IdP)       →  perfil ACADÉMICO (el acceso de persona)
Registro privilegiado + login+MFA →  identidad + rol (sesión de operador)
Policy Engine (contexto, vigencia) →  autorización contextual
                                      → privilegios adicionales (con TTL/sesión)
```

**Entrar físicamente al campus jamás justifica privilegios elevados; solo el perfil mínimo.** Todo lo demás exige autenticación y autorización.

## 12. Cuestiones abiertas

- **Delegación del registro de Especialistas de TI.** Si el Administrador de Red puede registrarlos o esa función queda solo en el Superadministrador.
- **Acceso remoto.** La política de acceso remoto de los operadores (contemplado para el Superadministrador).
