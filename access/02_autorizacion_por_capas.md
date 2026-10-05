# Autorización por capas

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Control de acceso — 2
**Estado:** Borrador formal para revisión

---

Dónde vive la autorización en el modelo de capas: por qué no tiene ni un protocolo, dónde se decide y con qué campos de varias capas se expresa en la red. Complementa a [`01_autenticacion_por_capas.md`](01_autenticacion_por_capas.md) (la pregunta «¿quién eres?»), a [`02_autorizacion.md`](../docs/componentes/02_autorizacion.md) (los dos planos y los perfiles) y a [`00_auth_controller.md`](00_auth_controller.md) (quién decide, traduce y ejecuta). El flujo completo, mensaje a mensaje, está en [`plan/auth`](../plan/auth/v1_flujo_por_capas.md).

## 1. La pila de la autorización

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ CAPA 7 · APLICACIÓN — aquí se decide                                       │
│                                                                            │
│   la decisión — Policy Engine (motor ABAC-like)                            │
│     evalúa: identidad + rol + dispositivo + ubicación + contexto           │
│              + recurso + acción + vigencia                                 │
│     produce: perfil + duración  (la denegación también se decide)          │
│                                                                            │
│   los dos planos                                                           │
│     RBAC ......... rol → permisos P01–P30, dentro de los servicios (I7)    │
│     ABAC-like .... condiciones + vigencia → la conectividad de la sesión   │
│                                                                            │
│   los perfiles — la decisión materializada                                 │
│     BASE · ACADÉMICO · LABORATORIO (TTL) · TI · ADMIN_RED · SUPER_ADMIN    │
├────────────────────────────────────────────────────────────────────────────┤
│ CAPAS 5/6 · SESIÓN/PRESENTACIÓN                                            │
│     sin protocolo propio: la decisión no se negocia — se ordena            │
│     (el TLS del portal y de I4 pertenece a la autenticación, doc 1)        │
├────────────────────────────────────────────────────────────────────────────┤
│ CAPA 4 · TRANSPORTE — los puertos como condición                           │
│     tcp 22/443 hacia la gestión (sesión de rol) · UDP 67/68/53 (BASE)      │
│     un puerto no autoriza: es un campo del match                           │
├────────────────────────────────────────────────────────────────────────────┤
│ CAPA 3 · RED — las direcciones como condición y como vínculo               │
│     ip_dst=10.0.0.5 (el portal) · ip_dst=red de gestión (denegada)         │
│     ip_src — el par MAC/IP aprendido: la identidad de red anti-spoofing    │
├────────────────────────────────────────────────────────────────────────────┤
│ CAPA 2 · ENLACE — la MAC como identidad de dispositivo                     │
│     eth_src — el dispositivo (atributo y clave de correlación,             │
│               jamás una credencial)                                        │
│     in_port — el punto de ingreso: la ubicación                            │
├────────────────────────────────────────────────────────────────────────────┤
│ CAPA 1 · FÍSICA — el puerto como ubicación                                 │
│     la regla se ancla al switch y puerto de ingreso (S1:p1):               │
│     la autorización se instala donde el dispositivo está conectado         │
└────────────────────────────────────────────────────────────────────────────┘
```

## 2. El conteo

| Capa | Protocolos de autorización | Qué hay en su lugar |
|---|---|---|
| **7 · Aplicación** | **0** — no hay nada que negociar | la **decisión**: Policy Engine (ABAC-like), RBAC de los servicios, perfiles |
| 5/6 · Sesión/Presentación | 0 | nada: la decisión se ordena, no se negocia |
| 4 · Transporte | 0 | puertos como **condición** (22/443; 67/68/53) |
| **3 · Red** | **0** | direcciones como **condición** + el par MAC/IP (anti-spoofing) |
| **2 · Enlace** | **0** | la MAC como **identidad de dispositivo**; `in_port` como ubicación |
| 1 · Física | — | el **puerto** como ancla de toda regla |

Lectura del conteo: a diferencia de la autenticación (seis protocolos en aplicación y uno en enlace), **la autorización no tiene ni un protocolo**: no hay veredicto que negociar — hay una decisión y una expresión. La decisión vive en aplicación (una sola: el Policy Engine, con sus dos planos); la expresión vive en las capas 1–4 como campos de match: MAC, IP y puertos, más el puerto físico de ingreso.

## 3. La escalera de prioridades: el solapamiento resuelto

Varias autorizaciones pueden coincidir sobre el mismo paquete (el DROP del BASE y la regla de una sesión, por ejemplo). El árbitro es la **prioridad**: gana el peldaño más alto, sin importar el orden en que las reglas se instalaron.

```text
1000 ─ mitigación                (R4: vence a todo)
 200 ─ sesión privilegiada       (operadores hacia la gestión)
 150 ─ portal                    (la única puerta pre-sesión)
 120 ─ par MAC/IP correcto       (ALLOW del anti-spoofing)
 110 ─ IP con MAC ajena          (DROP del anti-spoofing)
 100 ─ red de gestión            (DROP del BASE — deny by default)
  10 ─ DHCP y DNS                (vida pre-sesión)
  ── ─ sesión académica          (servicios + Internet — peldaño a fijar al implementar)
```

El ejemplo que lo demuestra: un SSH de la PC del Administrador hacia `10.0.0.3` coincide con **dos** autorizaciones a la vez.

```text
S1: match eth_src=MAC_PC-ADMIN, ip_dst=red_gestion              → DROP    (100, BASE)
S1: match in_port=pX, eth_src=MAC_PC-ADMIN, ip_dst=red_gestion,
    tcp=22                                                       → OUTPUT  (200, sesión)
```

Gana la de 200: la identidad elevó el permiso. El mismo SSH desde un dispositivo académico coincide **solo** con el DROP del BASE: su peldaño no abre la gestión, nunca. Y una mitigación activa (1000) vence incluso a la sesión.

La escalera es, además, el punto donde los dos planos de autorización se vuelven uno solo: cada perfil es un peldaño ([`02_autorizacion.md`](../docs/componentes/02_autorizacion.md) §6).

## 4. El enforcement cruza capas: la regla que ejecuta la decisión

Una decisión se materializa como **una** regla que matchea campos de varias capas a la vez:

```text
decisión: ACADÉMICO · MAC A1 · S1:p1 · vigencia T
   │ orden northbound (I2)
   ▼
FLOW_MOD en S1:  match in_port=p1, eth_src=MAC A1, ip_src=10.0.1.25[, puertos]
                 acciones: OUTPUT — cookie=sesión · idle_timeout=T
```

| Campo | Capa | Qué expresa |
|---|---|---|
| `in_port` | 1/2 | dónde está conectado |
| `eth_src` | 2 | el dispositivo (junto a `ip_src`: anti-spoofing) |
| `ip_src` / `ip_dst` | 3 | la dirección aprendida / el destino autorizado |
| puerto TCP/UDP destino | 4 | qué servicio se alcanza |
| prioridad + cookie + timeout | — | precedencia, origen y vigencia de la autorización |

El canal que instala las reglas (OpenFlow, controlador ↔ switches, TCP 6653) es el **plano de control**, no un protocolo de autorización del usuario: la autorización se decide en aplicación y se ejecuta en el switch. Quién decide, quién traduce y quién ejecuta está en [`00_auth_controller.md`](00_auth_controller.md).

## 5. Dónde se cumple la autorización

La autorización **se cumple en el switch**, no en la consola ni en el portal: aunque alguien conociera una contraseña válida, sin la decisión del Policy Engine no hay reglas, y sin reglas no hay conectividad ([`02_autorizacion.md`](../docs/componentes/02_autorizacion.md) §5).

Los dos planos se cumplen en lugares distintos: el **RBAC** se valida en cada servicio, en cada petición de la plataforma (I7) — la red no distingue P06 de P07 —; la **conectividad** se cumple en el pipeline del switch, por prioridad. La red distingue perfiles; los servicios distinguen permisos.
