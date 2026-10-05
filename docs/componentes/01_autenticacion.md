# Elementos de autenticación

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Componentes del sistema — 1 de 6
**Estado:** Borrador formal para revisión

---

Qué vive dentro de cada pieza que responde a la pregunta **"¿quién eres?"**: el portal cautivo, el servicio IAM/AAA y el IdP institucional. La autorización (qué puedes hacer) está en [`02_autorizacion.md`](02_autorizacion.md); el mapa general, en [`00_mapa_de_componentes.md`](00_mapa_de_componentes.md). El modelo de identidades (las tres poblaciones y sus fuentes) está en [`04_identidades_y_poblaciones.md`](04_identidades_y_poblaciones.md).

## 1. La cadena de autenticación

```text
  Persona / Dispositivo                                          (borde)
        │  I3 — portal cautivo (HTTPS)
        ▼
  ┌────────────────┐   I4 — identidad/AAA    ┌─────────────────────────┐
  │   IAM/AAA      │ ──────────────────────► │  IdP institucional      │
  │  (con portal)  │ ◄────────────────────── │  (SE-02, externo)       │
  └───────┬────────┘   veredicto + atributos └─────────────────────────┘
          │ identidad + rol + dispositivo + vigencia
          ▼
  Policy Engine → decide el perfil → controlador instala las reglas (doc 02)
```

Tres piezas, tres responsabilidades distintas:

| Pieza | Responsabilidad | Análogo PUCP |
|---|---|---|
| **Portal cautivo** | Recoger credenciales y entregar la sesión | La página que se abre al conectarte |
| **IAM/AAA** | Verificar, crear la sesión, registrar (accounting) | El servidor que valida código + contraseña |
| **IdP institucional** | Poseer las cuentas y los atributos | El directorio/SSO de la universidad |

La autenticación **no conecta nada por sí sola**: su resultado entra al Policy Engine, que decide qué reglas se instalan (contrato de I3).

## 2. Qué vive dentro del portal cautivo (I3)

```text
┌─ Portal cautivo ─────────────────────────────────────────────────────────┐
│  servidor HTTPS (TLS)                                                    │
│  formulario de credenciales (usuario + contraseña; MFA: solo operadores) │
│  punto de entrada obligatorio del perfil pre-sesión                      │
│    (la única puerta abierta: regla de prioridad 150 en el switch)        │
│  entrega de la sesión: cookie/token (forma concreta en Fase F)           │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Qué NO vive aquí:** la decisión de autenticar (es del IAM), las credenciales almacenadas (las de la comunidad, en el IdP; las de operadores, en el repositorio del IAM), las reglas de red (son del Policy Engine → controlador).
- No es un servicio aparte: es **la interfaz web del servicio IAM/AAA** (doc 04 §3).
- **Población:** toda la población — la comunidad universitaria (reino IdP) y los operadores (repositorio propio); el portal distingue ambos reinos (§6).

## 3. Qué vive dentro de IAM/AAA

```text
┌─ IAM/AAA ────────────────────────────────────────────────────────────────┐
│                                                                          │
│  repositorio de identidades privilegiadas (operadores — doc 04)          │
│                                                                          │
│  orquestador de autenticación                                            │
│    recibe las credenciales del portal y las verifica:                    │
│      comunidad → IdP (I4) · operadores → repositorio propio, con TOTP    │
│                                                                          │
│  cliente de identidad — el "cómo" de I4 (decidido)                       │
│    RADIUS contra el IdP institucional (FreeRADIUS en el prototipo);      │
│    el directorio LDAP del IdP vive detrás de RADIUS (ver §7)             │
│                                                                          │
│  gestor de sesiones                                                      │
│    alta (login) · vigencia · cierre (logout o inactividad)               │
│    no almacena las credenciales de la comunidad (las usa y las descarta) │
│                                                                          │
│  accounting                                                              │
│    registro de sesiones: quién, cuándo, desde qué dispositivo            │
│                                                                          │
│  publica → SessionOpened / SessionClosed (broker, I5)                    │
│  entrega → identidad + perfil/rol + atributos al Policy Engine           │
└──────────────────────────────────────────────────────────────────────────┘
```

**Una sesión es:** una entrada del IAM con identidad, perfil o rol, dispositivo, instante y vigencia. Lo que produce:

```text
sesión abierta
   ├──► evento SessionOpened ──► broker ──► Políticas + Auditoría
   ├──► identidad + perfil/rol ──► Policy Engine ──► decisión de perfil (doc 02)
   └──► registros de accounting (quién usó qué, cuándo)
```

## 4. Qué vive dentro del IdP institucional (SE-02)

Es la fuente del **reino comunidad**; las otras dos poblaciones tienen su lugar propio ([doc 04](04_identidades_y_poblaciones.md)).

```text
┌─ IdP institucional — externo: se consulta, no se administra ─────────────┐
│                                                                          │
│  directorio de identidades (LDAP / AD / BD)                              │
│    cuentas de la comunidad: código/usuario + hash de contraseña          │
│    grupos y atributos: rol, dependencia, vigencia                        │
│                                                                          │
│  Prototipo (no hay IdP real):                                            │
│    directorio simulado con cuentas académicas de prueba                  │
│    (los operadores no viven aquí: tienen su repositorio — doc 04)        │
└──────────────────────────────────────────────────────────────────────────┘
```

Lo que el IAM le pregunta (I4) y lo que el IdP responde:

```text
IAM → IdP:  ¿estas credenciales son válidas?  y  ¿qué atributos tiene
            esta identidad? (rol, grupo, vigencia)
IdP → IAM:  veredicto (sí/no) + atributos
```

El IdP es el **dueño** de las identidades de la comunidad universitaria (SE-02): la plataforma las consume y no las replica.

## 5. El recorrido completo de un login

```text
dispositivo         portal (I3)        IAM/AAA              IdP (I4)
    │  HTTPS al portal  │                  │                    │
    │──────────────────►│  credenciales    │                    │
    │                   │─────────────────►│   verificar        │
    │                   │                  │───────────────────►│
    │                   │                  │◄───────────────────│ sí/no
    │                   │◄─────────────────│   + atributos      │
    │◄──────────────────│  sesión (cookie) │                    │
    │                   │                  │──► SessionOpened ──► broker
    │                   │                  │──► identidad+rol ──► Policy Engine
```

Y la contraseña, paso a paso:

```text
tecleada en el portal ──► viaja por HTTPS (I3) ──► el IAM la usa para
verificar contra el IdP (I4) ──► el IdP dice sí/no + atributos
──► el IAM la DESCARTA (no la almacena, no la registra)

  quién la ve:       portal e IAM, solo en tránsito
  quién la verifica: el IdP, contra el hash de su directorio
  quién la guarda:   nadie en la plataforma (solo el hash, en el IdP)
```

## 6. ¿Uno o varios mecanismos de login?

El estado documentado hoy es: **un solo portal (I3) para todos los roles**, y todos pasan por el mismo mecanismo — lo que cambia después del login es el **rol**, no la puerta:

```text
        todos los roles                    tras el login, el rol decide:
  ───────────────────────────►  portal ──┬──► académico → perfil ACADÉMICO
  académico · TI · Admin · SA  (mismo)   ├──► TI      → sesión TI (prioridad 200)
                                         ├──► Admin   → sesión de gestión
                                         └──► SA      → sesión de gestión (y remoto)
```

- **No hay portales distintos por rol:** un portal por población duplicaría la superficie de ataque y el mantenimiento sin agregar seguridad; la separación real ocurre en la autorización (doc 02).
- La variante "portal de invitados con autoregistro" es **otro mecanismo** (no un segundo portal de la misma población) y sigue fuera de alcance.
- El portal distingue la población (reino comunidad vs. reino operadores); el **cómo** — selector, convención de identificador o URL separada — es detalle de Fase F ([doc 04](04_identidades_y_poblaciones.md) §3).

## 7. Tecnologías por interfaz

Las cajas están decididas y la tecnología **dentro** de I3/I4 también (flujo detallado: [`plan/auth`](../../plan/auth/v1_flujo_por_capas.md)):

| Interfaz | Tecnología | Qué implica | Estado |
|---|---|---|---|
| I3 | **HTTPS + formulario web** | el portal como puerta única; redirección vía OpenFlow (PACKET_IN → regla) | Decidido |
| I4 | **RADIUS** (+ directorio detrás) | AAA completo: autentica, autoriza y registra (accounting); es lo que corre una universidad real (eduroam) | **Decidido — FreeRADIUS en el prototipo** |
| I4 | **LDAP(S)** | protocolo del directorio del IdP: las cuentas y los atributos viven ahí; en el prototipo queda **detrás de RADIUS** | Decidido (rol: directorio) |
| — | **MFA (TOTP)** | segundo factor de operadores | **Decidido: obligatorio para operadores**; no para académicos — doc 04 §4 |

## 8. Cuestiones abiertas

- **Distinción de población en el portal** (§6): selector vs. convención de identificador vs. URL — Fase F (doc 04 §3).
- **Forma de la sesión:** cookie de sesión vs. token; y si la sesión se liga al dispositivo (MAC/puerto) — Fase F.

Documentos relacionados: [`03_flujo_autenticacion_autorizacion.md`](../../flows/03_flujo_autenticacion_autorizacion.md) (mecánica a nivel de red) y [`04_descomposición_arquitectonica.md`](../fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md) (descomposición).
