# Identidades y poblaciones

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Componentes del sistema — 4 de 6
**Estado:** Borrador formal para revisión

---

El modelo de identidades: qué poblaciones existen, dónde vive cada una, quién crea sus cuentas y qué obtienen al autenticarse. Complementa a [01 (autenticación)](01_autenticacion.md) — la mecánica del login — y fija las decisiones de **MFA** y del alcance del **SSO**. El lado observable (los dispositivos) está en [05 (historial de dispositivo)](05_historial_de_dispositivo.md).

## 1. Tres poblaciones, tres fuentes de identidad

```text
 POBLACIÓN                        FUENTE DE IDENTIDAD
 ──────────────────────────────── ──────────────────────────────────────────
 comunidad universitaria          IdP institucional (SE-02, externo)
 (alumnos, profesores, personal)  la universidad las crea (matrícula/RRHH);
                                  la plataforma NO las gestiona
 ──────────────────────────────── ──────────────────────────────────────────
 operadores de la infraestructura repositorio de identidades privilegiadas
 (TI, Admin, SA — de la          de la PLATAFORMA (vive con el IAM);
 universidad o no)               las crea la cadena SA→Admin→TI (P24/P14);
                                  reino separado del institucional
 ──────────────────────────────── ──────────────────────────────────────────
 invitados                        registro efímero: autoregistro + TTL corto
                                  (fuera de alcance, pero el lugar queda)
```

| Población | Fuente | Quién crea las cuentas | Qué obtiene al autenticarse |
|---|---|---|---|
| Comunidad universitaria | IdP institucional | La universidad | Perfil ACADÉMICO: servicios de la comunidad + Internet |
| Operadores | Repositorio de identidades privilegiadas | Cadena SA→Admin→TI (+ dispositivo registrado, P30) | Sesión de rol: reglas hacia la gestión según el rol, y la consola/APIs con ese rol |
| Invitados | Registro efímero | Autoregistro | Fuera de alcance |

La plataforma **no gestiona** las cuentas de la comunidad (las crea y las borra la universidad) y **sí gestiona** las de operadores (es su población). Los invitados existen un momento y se borran por TTL.

## 2. Los tres reinos

### 2.1 Reino comunidad — el IdP institucional (SE-02)

- Dueño de las identidades de alumnos, profesores y personal; la plataforma las **consulta** (I4) y no las replica.
- Ciclo de vida externo (matrícula, RRHH): la plataforma no crea, no modifica y no borra estas cuentas.
- Prototipo: directorio simulado con cuentas académicas de prueba.

### 2.2 Reino operadores — el repositorio de identidades privilegiadas

- Vive **en la plataforma**, junto al IAM/AAA: la cadena de cuentas de la fase A (el SA crea Administradores; los Administradores crean Especialistas de TI — delegación exacta aún abierta en fase A) es su forma de gestión.
- **Separado del institucional aunque el operador sea de la universidad:** una cuenta de administrador nunca es la misma que la de alumno/profesor. Razones: radio de daño contenido, política distinta (MFA), auditoría limpia y baja/rotación controlada por el propio SA.
- Credenciales de operador: viven aquí (hasheadas). Es la única población en alcance cuyas credenciales administra la plataforma.
- El operador no basta por sí solo: para elevar necesita además un **dispositivo registrado** (P7, P30) — el lado de los dispositivos está en [05](05_historial_de_dispositivo.md).

### 2.3 Reino invitados — registro efímero

- Un invitado no es de la universidad y no puede vivir en el IdP institucional; se autoregistra y recibe acceso con TTL corto; al expirar, se borra.
- Fuera de alcance de la solución: se documenta el lugar que ocupará cuando se aborde.

## 3. El portal: un servicio, tres fuentes

```text
                    ┌───────────────────────────────┐
                    │          PORTAL (I3)          │
                    │     un solo servicio web      │
                    └───────────────┬───────────────┘
                                    │ ¿contra quién valida?
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
   ┌───────────────────┐ ┌─────────────────────┐ ┌──────────────────┐
   │ REINO COMUNIDAD   │ │ REINO OPERADORES    │ │ REINO INVITADOS  │
   │ IdP institucional │ │ repositorio de      │ │ registro efímero │
   │ (SE-02, externo)  │ │ identidades         │ │ autoregistro     │
   │                   │ │ privilegiadas       │ │ + TTL (fuera de  │
   │                   │ │ (en la plataforma)  │ │ alcance)         │
   └───────────────────┘ └─────────────────────┘ └──────────────────┘
```

- El portal (I3) sigue siendo **un solo servicio**; lo que hay detrás son tres fuentes de identidad.
- Cómo se distingue la población en el login — selector explícito, convención de identificador o URL separada — es **detalle de Fase F**: depende del IdP real y no cambia la arquitectura.
- No hay dos portales como sistemas separados: un solo servicio; si se quisieran dos páginas, serían dos vistas del mismo servicio.

## 4. MFA: decisión

- **Obligatorio para todos los operadores** (TI, Admin, SA) en el portal.
- Académicos: **no** en la solución (fricción sobre toda la población; si el IdP institucional exige segundo factor para sus cuentas, es decisión de la universidad).
- Invitados: no.
- Prototipo: segundo factor **TOTP** (app autenticadora) — sin dependencia de internet ni de servicios externos; la forma concreta, en Fase F.

## 5. SSO: el efecto ya existe; el protocolo no entra

- **Efecto SSO — sí, ya existe por diseño:** una sola autenticación abre lo que el rol permite. Para el operador: reglas de red **y** la consola/APIs (que operan con el rol de esa misma sesión, I7). No hace falta ningún protocolo adicional para eso: **la sesión es el SSO**.
- Para el académico el efecto es más acotado: su login da alcanzabilidad de red; los logins de aplicación (correo, campus virtual) son de cada aplicación, y el SSO institucional es del IdP — ajeno a esta solución.
- **Protocolo SSO — no entra.** Integrar el SSO institucional (el portal delega el login al SSO) queda para un despliegue posterior al prototipo.

## 6. Qué obtiene cada población en la red

| Recurso | Académico | Operadores |
|---|---|---|
| Infraestructura de red/seguridad (consola, APIs, controlador, switches, gestión) | **No** — DROP de la escalera | **Sí**, según rol (reglas de sesión prioridad 200, destinos por rol) |
| Servicios de la comunidad (académicos, SRV-1…) | **Sí** — alcanzabilidad de red; el login de la aplicación es de la aplicación | Sí |
| Internet | Sí | Sí |

Antes de autenticarse, toda población comparte el mismo estado: **BASE** (DHCP, DNS, portal). El mínimo privilegio tiene dos niveles — el del dispositivo (BASE) y el de la persona (ACADÉMICO para la comunidad; sesión de rol para operadores): doc [02 §4](02_autorizacion.md).

## 7. El alcance de I4

- **I4 = IAM ↔ IdP institucional**: la interfaz del reino comunidad.
- El repositorio de operadores **no usa I4**: es interno a la plataforma (persistencia propia, I6).
- Los invitados, cuando se aborden, tendrán su propio registro efímero — tampoco I4.
- **Producto decidido:** **RADIUS** (FreeRADIUS en el prototipo) contra el IdP institucional; el **directorio LDAP** simulado vive detrás de RADIUS.

## 8. Cuestiones abiertas

- **Distinción de población en el portal** (selector vs. convención de identificador vs. URL): Fase F, según el IdP real.
- **Vigencia de cuentas de operadores externos** (no universitarios): recomendable vigencia explícita y responsable, al estilo de P30 — por definir.
- **Invitados:** mecanismo completo, fuera de alcance.
