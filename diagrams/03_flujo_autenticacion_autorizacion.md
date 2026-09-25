# Flujo con autenticación y autorización

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Descripción del flujo — parte 3 de 5
**Estado:** Borrador formal para revisión

---

Esta parte añade la capa de identidad sobre el flujo base (parte 2). La decisión central del modelo:

> **La red no intenta identificar digitalmente a cada persona que consume servicios. Identifica y controla el dispositivo, su ubicación y su contexto. La identidad fuerte se exige únicamente cuando alguien pretende obtener privilegios superiores al perfil base.**

## 1. Premisa de confianza: la presencia física

El campus es de acceso controlado: para conectar un cable hay que haber entrado físicamente. El proyecto adopta como restricción (RP-13) que **la presencia física en el campus es condición de confianza inicial suficiente para el perfil base**. Por eso los usuarios académicos no pasan por 802.1X ni por RADIUS al conectar: su "autenticación" es haber entrado. La consecuencia aceptada es que la seguridad física del campus forma parte del perímetro de seguridad.

Esta premisa elimina la distinción estudiante/profesor a nivel de red: ambos son **usuario académico**, un consumidor ordinario de servicios sin privilegios de infraestructura. Si la plataforma educativa distingue internamente entre alumno y docente, es asunto de la aplicación, no de la red.

## 2. El perfil base y el principio de mínimo privilegio

Todo dispositivo que conecta recibe el **perfil BASE** — deny by default:

```text
PERMITIDO (perfil BASE)
  DHCP, DNS
  servicios académicos permitidos
  Internet según política

DENEGADO (por defecto)
  SSH/Telnet/NETCONF hacia infraestructura
  OpenFlow y cualquier acceso al controlador
  SNMP administrativo y consolas de gestión
  interfaces de administración
  servicios sensibles
```

En el plano de datos, esto se materializa como entradas concretas (perspectiva del pipeline, parte 1 §7). Para el dispositivo recién conectado el controlador instala:

```text
S1: match eth_src=MAC_host, ip_dst=red_de_gestion → DROP       (prioridad 100)
S1: match eth_src=MAC_host, UDP 67/68, 53, http/s  → OUTPUT... (prioridad 10)
```

## 3. El registro de dispositivos y la regla del "no match"

Decisión de diseño clave: **no se registra a todos los dispositivos; se registra solo a los dispositivos de los operadores privilegiados.** Los dispositivos académicos no figuran en ningún catálogo de red.

- El **registro de dispositivos privilegiados** guarda, por cada equipo de un Especialista de TI, Administrador de Red o Superadministrador: MAC, tipo de equipo, titular, rol asociado, vigencia y responsable del registro.
- La regla de aplicación es la inversa de un catálogo total: **todo dispositivo que no haga match con este registro es usuario académico con perfil BASE.** No hay que dar de alta nada más; el default cubre al 99% de la población.
- RADIUS **no** cataloga dispositivos: autentica a las *personas* privilegiadas (credenciales). El registro de dispositivos vive en un servicio de base de datos propio, separado, que además sirve de auditoría: quién registró qué equipo, cuándo y con qué vigencia.
- El registro no concede privilegios por sí solo: un dispositivo registrado **y** sin login sigue teniendo perfil BASE (§4). El match con el registro solo habilita la posibilidad de elevar.

## 4. La PC del operador sin login es una PC cualquiera

El punto más demostrable del modelo: la laptop del Administrador de Red, conectada en la sala de administración, **antes del login tiene perfil BASE**. La ubicación física no concede privilegios; la MAC tampoco (la MAC es un atributo del dispositivo, no una credencial: cualquiera puede falsificarla).

```text
PC-ADMIN conectada → S1 → el controlador aprende el dispositivo (PACKET_IN)
   identidad = desconocida
   perfil = BASE
   → SSH a switches: DROP · OpenFlow: DROP · consola: DROP
```

## 5. El login privilegiado: portal cautivo → RADIUS → Policy Engine

Cuando el operador necesita sus privilegios, se autentica a través del **portal cautivo** (o acceso remoto equivalente, para el Superadministrador):

```text
PC-ADMIN
  │ credenciales (usuario + contraseña + MFA si aplica)
  ▼
Portal cautivo
  │ RADIUS (Authentication, Authorization, Accounting)
  ▼
Servidor AAA / RADIUS
  │ consulta al backend de identidad
  ▼
IdP institucional (LDAP / AD / BD)
  │ identidad válida + atributos
  ▼
Policy Engine
  identidad autenticada + dispositivo (match con el registro)
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

La regla nueva tiene **mayor prioridad** que el DROP del perfil base, y un `idle_timeout` ligado a la sesión: si el operador cierra sesión o queda inactivo, el switch elimina la entrada solo y el dispositivo regresa a BASE. El mismo mecanismo sirve para el usuario académico:

```text
S1: match eth_src=MAC_academico, ip_dst=red_gestion → DROP  (siempre activo)
```

## 7. Elevación temporal de un usuario académico

El usuario académico puede pedir más de lo que le corresponde si lo justifica — por ejemplo, un estudiante del Pabellón V necesita acceder al servidor de laboratorio durante una práctica de dos horas:

```text
BASE
  │ solicitud: acceso LABORATORIO, 2 h, recursos X/Y/Z
  ▼
PENDING  (el Administrador de Red revisa la solicitud)
  │ aprobación
  ▼
ELEVATED (TTL = 2 h)   ← perfil BASE + LABORATORIO temporal
  │ expiración
  ▼
BASE
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
| LABORATORIO / INVESTIGACIÓN / PRACTICANTE_DTI | Usuarios académicos con necesidad justificada | Solicitud + aprobación | Temporal (TTL) |
| TI / ADMIN_RED / SUPER_ADMIN | Operadores privilegiados | Dispositivo registrado + login (portal/AAA) | Sesión (idle_timeout) |

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

La topología es rígida por diseño, pero la solución debe tolerar la aparición de un dispositivo nuevo. El flujo es exactamente el del default: el controlador detecta la MAC por el PACKET_IN del primer tráfico, el dispositivo **no hace match con el registro privilegiado** y recibe perfil BASE. Si ese dispositivo va a ser de un operador, se lo registra (§8) y desde entonces puede elevar. No hay configuración adicional para el caso académico: es el camino por defecto.

## 11. La jerarquía de confianza completa

```text
Sin presencia en campus           →  sin acceso
Presencia física en campus        →  perfil BASE (confianza inicial)
Registro privilegiado + login     →  identidad + rol
Policy Engine (contexto, vigencia) →  autorización contextual
                                      → privilegios adicionales (con TTL/sesión)
```

**Entrar físicamente al campus jamás justifica privilegios elevados; solo el perfil mínimo.** Todo lo demás exige autenticación y autorización.

## 12. Cuestiones abiertas

- **MFA.** Si el login privilegiado exige segundo factor y con qué mecanismo.
- **Delegación del registro de Especialistas de TI.** Si el Administrador de Red puede registrarlos o esa función queda solo en el Superadministrador.
- **Acceso remoto.** La política de acceso remoto de los operadores (contemplado para el Superadministrador).
