# Identidad, sesiones y portal

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

Cuatro decisiones en un documento: el **producto de I4** (RADIUS + directorio), el **repositorio de operadores con TOTP** (I6), la **forma de la sesión** —cookie o token, y si se liga al dispositivo— y la **distinción de población en el portal** (I3). Las tres últimas estaban declaradas como cuestiones abiertas en [`componentes/01`](../../componentes/01_autenticacion.md) §8 y [`componentes/04`](../../componentes/04_identidades_y_poblaciones.md) §8; la forma de I7 —la API de administración— se decide aquí porque depende de la sesión.

## 1. Qué exige la arquitectura

| Exigencia | Origen |
|---|---|
| Autenticación de la comunidad contra el IdP institucional por I4; los operadores, contra el repositorio propio con segundo factor | R1.2, D-07 I4/I6, [componentes/04](../../componentes/04_identidades_y_poblaciones.md) §4 |
| Un solo portal (I3), tres reinos de identidad; la población se distingue **antes** de validar | [componentes/04](../../componentes/04_identidades_y_poblaciones.md) §3 |
| Sesión con vigencia e `idle_timeout`; toda acción queda en accounting y auditoría | P10, R1.9 |
| La sesión es el SSO del operador: abre la consola y las APIs con su rol (I7) | I7, [componentes/04](../../componentes/04_identidades_y_poblaciones.md) §5 |
| El robo de sesión está en la superficie de ataque: la ligadura al dispositivo quedó **a evaluar** | [componentes/03](../../componentes/03_seguridad.md) §4 |

## 2. I4: FreeRADIUS con directorio LDAP detrás

**Decisión.** El IAM es cliente RADIUS; el IdP simulado del prototipo es **FreeRADIUS** con un directorio **OpenLDAP** detrás. En un despliegue real, I4 apunta al IdP institucional —el mismo protocolo y el mismo rol—; el prototipo **simula al IdP, no al protocolo**.

```text
IAM (cliente RADIUS) ── Access-Request ──► FreeRADIUS ──► OpenLDAP
                       Accounting-Request    (IdP simulado: cuentas y atributos)
                       (Start · Interim · Stop)
```

- **Verificación:** `Access-Request`/`Access-Accept` con las cuentas de prueba del directorio; es lo que corre una universidad real (eduroam), así que el prototipo no inventa un mecanismo.
- **Accounting:** el IAM reporta a RADIUS el ciclo de cada sesión de la comunidad (`Start`, `Interim` periódico, `Stop`) con `Acct-Session-Id`; es el registro AAA que R1.9 exige, y alimenta la correlación de la auditoría.
- **Límite:** la integración con el SSO institucional real (delegación del login) queda para un despliegue posterior al prototipo, ya declarado en [componentes/04](../../componentes/04_identidades_y_poblaciones.md) §5.

## 3. Reino operadores: repositorio propio, credenciales y TOTP

**Decisión.** Las identidades privilegiadas (TI, Admin, SA) viven en el repositorio propio de la plataforma (I6): credenciales **hasheadas** (bcrypt) en el esquema del servicio IAM, nunca en claro ni reversibles; segundo factor **TOTP** (RFC 6238) obligatorio para todos los operadores.

### El aprovisionamiento del TOTP

El secreto nace en el **registro del dispositivo privilegiado**, no en el primer login —el registro es el acto administrativo que habilita (P7)—:

```text
1. TI registra el dispositivo del operador en la consola (rol autorizado)
2. el IAM genera el secreto TOTP del operador y lo muestra UNA vez
   como QR (otpauth://totp/…) en la propia consola
3. el operador lo carga en su app autenticadora y verifica un código
4. recién entonces el par (dispositivo, operador) queda habilitado
5. el alta completa —quién, qué, cuándo— queda en auditoría (R1.9)
```

- **Sin internet ni servicios externos:** TOTP es local por definición; encaja con RP-06 (entorno controlado).
- **Verificación del segundo factor en I6, siempre:** el login de operador no tiene una variante sin TOTP. Código perdido = re-aprovisionamiento por la cadena SA→Admin, auditado.
- **Alcance:** obligatorio para operadores; **no** para académicos ([componentes/04](../../componentes/04_identidades_y_poblaciones.md) §4).

## 4. Forma de la sesión: cookie ligada al dispositivo

**Decisión.** Sesión **con cookie opaca** —un identificador sin datos, `HttpOnly`, `Secure`, `SameSite`— emitida por el portal/IAM y validada **del lado del servidor** contra la tabla de sesiones del IAM; y **ligada al dispositivo**: la sesión nace atada a la asociación MAC ↔ switch:puerto ↔ IP que el controlador aprendió, y solo es válida desde esa ubicación.

```text
login (I3) ──► IAM crea sesión ──► consulta I2: ¿asociación vigente de esta IP?
                                   │
             sesión SES-… = { usuario, rol, MAC, S1:p1, IP,
                              idle_timeout, hard_timeout }
                                   │
cada petición: IP de origen == IP de la sesión        ← verificación barata, siempre
evento MAC_Moved del dispositivo de la sesión         ← la sesión se invalida
   └─► SessionClosed · auditoría · investigación (historial de dispositivo)
```

- **Por qué cookie y no token portador:** la cookie no lleva datos (no hay nada que robar del contenido), la validez vive en el servidor y el retiro es inmediato —coherente con P10. Para llamadas desde herramientas, el IAM emite un **token de vida corta derivado de la misma sesión**, con la misma vigencia y la misma ligadura: una sola fuente de verdad, dos formas de presentarla.
- **La ligadura cierra el robo de sesión por reubicación:** una cookie robada presentada desde otro dispositivo tiene otra MAC, otro puerto y otra IP; el acceso se rechaza, la sesión se cierra y el hecho se audita. Es la respuesta concreta a la fila «robo de sesión» de [componentes/03](../../componentes/03_seguridad.md) §4.
- **El costo no existe:** la asociación ya la mantiene el controlador (P7); ligar la sesión es consultarla (I2, [`01`](01_controlador_y_api_northbound.md) §5).
- **I7 queda definido por esto:** las APIs de administración de cada servicio son **REST/JSON** validadas del lado del servidor contra la sesión y el rol —nunca del lado del cliente—; la consola es un cliente de esas APIs, no un servicio con credenciales propias. La sesión es el SSO ([componentes/04](../../componentes/04_identidades_y_poblaciones.md) §5).

## 5. Vigencias por perfil (valores iniciales)

Dos relojes por sesión, ambos configurables: el **`idle_timeout`** de la regla en el switch (el dispositivo la expira solo, `FLOW_REMOVED` lo informa) y el **tope absoluto** en el IAM (la sesión no se renueva más allá). El valor de la regla y el de la sesión son **el mismo**: una sola cifra por perfil, sin desincronización posible.

| Perfil | `idle_timeout` | Tope absoluto | Nota |
|---|---|---|---|
| BASE | — | — | sin sesión: no hay nada que expirar |
| ACADÉMICO | 30 min | 12 h | la sesión acompaña la jornada académica; el idle devuelve el equipo a BASE |
| Operador (TI/Admin/SA) | 15 min | 8 h | más estricto: la sesión abre la red de gestión, la consola y las APIs (R1.8, RA-09) |
| Elevación temporal | según la elevación | 1 h por defecto | vive en `PermissionRepository`; el tope es parte de la decisión del Policy Engine (P10) |

Los valores son el punto de partida del prototipo; su efecto se mide (expiración observada, regreso a BASE, ausencia de sesiones pegadas) y el resultado se reporta con RNF-12. Un logout explícito no espera a ningún reloj: retiro por cookie y `SessionClosed` inmediatos ([`access/00`](../../../access/00_auth_controller.md) §3.6).

## 6. Distinción de población en el portal: selector explícito

**Decisión.** El portal —un solo servicio— presenta un **selector explícito de población** en su entrada: «Comunidad universitaria» y «Personal de operación». Cada opción determina la **ruta de verificación** (RADIUS/LDAP o repositorio propio + TOTP); el mismo formulario sirve a ambas.

- **Por qué selector y no convención de identificador:** una convención (`usuario@dominio`) entrena al usuario a revelar su reino con cada intento y convierte el formato del identificador en información pública; el selector lo declara sin ambigüedad y sin inferencias.
- **Por qué no URLs separadas:** serían dos vistas del mismo servicio con doble superficie de mantenimiento y de phishing sin ganancia de seguridad —misma razón por la que no hay dos portales ([componentes/01](../../componentes/01_autenticacion.md) §6).
- **El selector no concede nada:** solo elige la ruta de verificación. El rol y los privilegios provienen siempre de la fuente de identidad, jamás de lo que el usuario eligió en pantalla. Un intento de operador con credenciales de comunidad —o al revés— falla en la verificación, y queda auditado.
- La población elegida es un dato de auditoría del intento de login (R1.9), útil en la investigación del historial de dispositivo.

## 7. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Login de comunidad completo (I3 → IAM → RADIUS → LDAP) con accounting | Sesión creada, reglas instaladas, registro AAA | R1.2, R1.9, I4 |
| Login de operador con TOTP; código incorrecto | Rechazo del segundo factor y auditoría | R1.2, MFA |
| Cookie presentada desde otro dispositivo (otra MAC/IP) | Rechazo, invalidación y evento auditado | RNF-01, componentes/03 §4 |
| `MAC_Moved` del dispositivo con sesión viva | `SessionClosed` inmediato y regreso a BASE | R3.3, P10 |
| Inactividad: `idle_timeout` vencido | `FLOW_REMOVED`, cierre y BASE sin intervención | R4.9, P10 |
| Selector de población cruzado (credenciales en la ruta equivocada) | Falla de verificación y registro | RNF-01 |
