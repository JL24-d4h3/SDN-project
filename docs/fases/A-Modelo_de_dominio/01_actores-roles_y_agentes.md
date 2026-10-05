# Actores: roles y agentes

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** A — Modelo de dominio
**Estado:** Borrador formal para revisión

---

## 1. Marco conceptual

| Concepto | Definición |
|---|---|
| **Actor** | Entidad que interactúa con el sistema. Puede ser una persona, un dispositivo, un componente de infraestructura o una entidad maliciosa. |
| **Identidad** | Quién es el actor, establecido mediante autenticación. Solo se exige para salir del perfil BASE: el login de la comunidad (perfil ACADÉMICO) o el de un operador (sesión de rol). |
| **Rol** | Conjunto de permisos que el sistema concede a una identidad, definido por lo que puede hacer y sobre qué recursos. |
| **Perfil de acceso** | Conjunto concreto de reglas de red asociadas a un dispositivo o sesión en un momento dado (BASE, ACADÉMICO, LABORATORIO, TI, ADMIN_RED, …). Un perfil puede ser temporal y expirar. |
| **Nivel de privilegio** | Posición del rol dentro de la jerarquía de autoridad del sistema. |

**Un atacante no es un rol.** Un rol es una etiqueta autorizada que el sistema concede; un atacante es una entidad cuyo comportamiento el sistema debe detectar y controlar. Por eso los actores se separan en dos categorías: actores con roles autorizados (sección 2) y agentes sin rol autorizado (sección 3).

**Premisa de confianza física (RP-13).** El campus es de acceso controlado: la presencia física se considera condición de confianza inicial suficiente para obtener el **perfil BASE** sin autenticación digital. La consecuencia aceptada es que la seguridad física del campus forma parte del perímetro de seguridad. La presencia física jamás justifica privilegios elevados: solo el perfil mínimo.

El rol no define por sí solo el permiso efectivo: el acceso depende también del recurso, la acción, el contexto, la vigencia y el estado de seguridad (sección 4).

---

## 2. Actores con roles autorizados

### 2.1 Jerarquía de privilegios

| Nivel | Rol | Propósito | Cómo obtiene privilegios | Acceso a recursos | Modifica la red |
|---|---|---|---|---|---|
| 0 | Usuario académico | Consumir servicios | Presencia física (perfil BASE); login con el IdP (perfil ACADÉMICO); elevación temporal mediante solicitud aprobada | Públicos + académicos autorizados | No |
| 1 | Especialista de TI | Seguridad y monitoreo | Dispositivo registrado + autenticación | Recursos de monitoreo y seguridad | Limitado |
| 2 | Administrador de Red | Administración operativa | Dispositivo registrado + autenticación | Recursos de red según autorización | Sí |
| 3 | Superadministrador | Control de la plataforma | Dispositivo registrado + autenticación (acceso remoto contemplado) | Todos | Sí, sin restricciones operativas |

**Fusión de Alumno y Docente.** Los roles Alumno y Docente de la versión anterior desaparecen: a nivel de red ambos son el mismo actor, **usuario académico**. No existe ningún recurso de red que distinga a un docente de un estudiante; la distinción, si la hay, vive dentro de los servicios de aplicación y la red no necesita conocerla.

### 2.2 Usuario académico — Nivel 0

**Función:** consumir servicios de red y aplicaciones institucionales. Es el actor por defecto: todo dispositivo conectado que no haga match con el registro de dispositivos privilegiados pertenece a esta población.

**Puede**

- Conectarse y obtener el perfil BASE sin autenticación digital (presencia física, RP-13).
- Obtener configuración de red (DHCP), resolución de nombres (DNS) y acceso al portal con el perfil BASE.
- Autenticarse en el portal contra el IdP institucional y obtener el perfil ACADÉMICO (servicios académicos e Internet).
- Acceder a los servicios académicos e institucionales permitidos con su perfil ACADÉMICO.
- Generar tráfico normal hacia servicios permitidos.
- Solicitar una elevación temporal de privilegios (perfil LABORATORIO, INVESTIGACIÓN o similar) con justificación; la concesión depende del Administrador de Red y siempre expira.

**No puede**

- Acceder por defecto de forma remota a servicios o recursos internos; las excepciones se conceden por pabellón, usuario o contexto mediante elevación aprobada.
- Modificar políticas de red, ACL o reglas de flujo.
- Administrar switches, VLAN ni segmentación.
- Acceder a la consola SDN, al controlador ni a las interfaces de administración.
- Suplantar la MAC de su equipo; si lo hace, el sistema lo detecta (evento MAC_MOVE o incoherencia) y responde según severidad.
- Administrar otros usuarios ni deshabilitar mecanismos de seguridad.

### 2.3 Especialista de TI — Nivel 1

**Función:** supervisar el estado de seguridad de la red y responder a eventos de seguridad, sin poseer control administrativo completo sobre la infraestructura.

Este rol separa la seguridad de la infraestructura: el Administrador de Red administra la red; el Especialista de TI la vigila y responde ante incidentes.

**Cómo accede:** su dispositivo figura en el registro de dispositivos privilegiados y, para ejercer el rol, debe autenticarse en el portal (credenciales propias + código TOTP). Sin login, su equipo tiene perfil BASE.

**Puede**

- Consultar tráfico, métricas de red, counters y registros.
- Consultar eventos del sistema de detección y alertas.
- Investigar direcciones IP y dispositivos sospechosos.
- Marcar una alerta como falso positivo y escalar un incidente.
- Solicitar o ejecutar acciones de mitigación predefinidas.
- Aislar un nodo comprometido, si la política lo autoriza.

**No puede**

- Crear o modificar libremente la política de red completa.
- Crear administradores ni asignar roles.
- Cambiar la arquitectura SDN ni configuraciones críticas del controlador.
- Revocar credenciales de administradores.
- Eliminar registros de seguridad.
- Desactivar los mecanismos de detección.

### 2.4 Administrador de Red — Nivel 2

**Función:** configurar, mantener y administrar la red y sus políticas de acceso. Es el operador de la infraestructura.

**Cómo accede:** dispositivo registrado + autenticación. Aplica el mismo principio: sin login, su PC es una PC con perfil BASE, aunque esté en la sala de administración.

**Puede**

- Crear, modificar y eliminar políticas de acceso; gestionar ACL y reglas de flujo.
- Administrar segmentación y VLAN.
- Administrar switches y dispositivos SDN, reglas de forwarding y mecanismos de mitigación.
- Aprobar o rechazar solicitudes de elevación temporal de usuarios académicos.
- Registrar dispositivos en el registro de dispositivos privilegiados y gestionar Especialistas de TI, si se le delega.
- Habilitar o deshabilitar determinados servicios.
- Consultar registros operativos y aplicar medidas de mitigación autorizadas.

**No puede** — su autoridad no es absoluta:

- Crear Administradores de Red ni Superadministradores.
- Modificar o revocar políticas por encima de la autoridad del Superadministrador.
- Alterar la definición de roles y permisos administrativos.
- Omitir el registro y la auditoría de sus cambios de política.

### 2.5 Superadministrador — Nivel 3

**Función:** privilegios máximos sobre el plano de administración de la solución SDN, incluyendo la gestión de administradores, las políticas globales y los mecanismos de seguridad.

**Cómo accede:** dispositivo registrado + autenticación; se contempla además el acceso remoto a la plataforma, sujeto a política.

**Puede**

- Registrar Especialistas de TI, Administradores de Red y otros Superadministradores; revocar cuentas.
- Crear, modificar y eliminar roles y permisos.
- Configurar políticas globales y modificar políticas de seguridad.
- Administrar el controlador SDN, los dispositivos de red y los mecanismos de detección y mitigación.
- Consultar todos los registros y auditar las acciones de los administradores.
- Recuperar configuraciones, restablecer políticas y bloquear o desbloquear usuarios.
- Aislar segmentos completos y modificar parámetros críticos del sistema.

**Administra a los administradores:**

```text
Superadministrador
       │
       ├── administra → Administrador de Red
       │                    │
       │                    ├── administra → infraestructura
       │                    ├── administra → Especialistas de TI (si se delega)
       │                    └── aprueba → elevaciones temporales
       │
       └── administra → Especialista de TI
                            │
                            └── gestiona → incidentes
```

### 2.6 Separación de funciones

Ningún rol concentra la capacidad de definir una política, aplicarla y evaluarla sin control:

- El **Administrador de Red** puede crear una política, pero el **Superadministrador** puede modificarla o revocarla.
- El **Especialista de TI** puede detectar que una política está provocando un incidente, pero no modificarla directamente.
- Las acciones de mitigación automáticas del sistema (R4) se ejecutan sin intervención humana en severidad baja; las de alto impacto requieren aprobación del Administrador de Red.
- Los cambios de política y las acciones administrativas quedan registrados y son auditables (R1.9, R2.9, ADM-04).

### 2.7 Usuario de red y usuario administrativo

El sistema atiende dos poblaciones distintas, que conviene modelar por separado: sería inconsistente que un Superadministrador operara la intranet como un usuario final.

```text
                 SISTEMA SDN
                     │
          ┌──────────┴──────────┐
          │                     │
      PLANO DE DATOS        PLANO DE CONTROL
          │                     │
    Usuario académico        Operadores
    (perfil BASE;           (registro + login
     ACADÉMICO con login)    con MFA)
          │                ┌────┴─────┐
          │                │          │
     elevación temporal   TI      Admin. Red
     (solicitud + TTL)              │
                          Superadministrador
```

---

## 3. Agentes sin rol autorizado

Estas entidades no reciben roles ni permisos. El sistema las trata como orígenes de comportamiento que debe observar, clasificar y, cuando corresponda, contener.

### 3.1 Atacante externo

No posee identidad ni autorización válida dentro de la red. Origina actividad maliciosa desde redes externas. Es el sujeto de R5 y, si logra atravesar el perímetro, también de R3 y R4.

### 3.2 Atacante interno

Dispone de acceso legítimo a la red —presencia física o un dispositivo con perfil BASE— pero genera actividad maliciosa. Es el caso que obliga a separar acceso de confianza: un actor con acceso legítimo puede convertirse en origen de tráfico malicioso en cualquier momento.

### 3.3 Nodo comprometido

No es necesariamente una persona: es un dispositivo legítimo cuyo comportamiento ha sido comprometido o resulta indistinguible de un compromiso. Puede estar siendo utilizado por un atacante interno o externo sin que su usuario legítimo lo advierta.

### 3.4 Componentes de infraestructura

No son actores autorizados ni atacantes: son agentes del sistema que ejecutan decisiones o generan información.

| Entidad | Naturaleza |
|---|---|
| Controlador SDN | Componente de infraestructura que traduce las decisiones de política a reglas del plano de datos. |
| Dispositivos de red | Switches que ejecutan las decisiones de forwarding, filtrado y mitigación. |
| Monitor | Recopila counters y estadísticas del plano de datos. |
| Detection Engine | Determina si existe comportamiento anómalo. |
| Incident Manager | Registra y gestiona los incidentes de seguridad. |
| Policy Engine | Decide qué respuesta corresponde a cada incidente o solicitud. |
| AAA / RADIUS | Autentica y autoriza a las poblaciones: la comunidad contra el IdP; los operadores contra su repositorio propio. |
| Servicios y servidores | Origen y destino de los flujos protegidos; también generan registros. |

### 3.5 Resumen de entidades

| Entidad | Naturaleza | Relación con el sistema |
|---|---|---|
| Usuario académico | Actor con rol | Rol autorizado (nivel 0); perfil BASE por defecto, ACADÉMICO con login |
| Especialista de TI | Actor con rol | Rol autorizado (nivel 1); requiere registro + login |
| Administrador de Red | Actor con rol | Rol autorizado (nivel 2); requiere registro + login |
| Superadministrador | Actor con rol | Rol autorizado (nivel 3); requiere registro + login |
| Atacante externo | Entidad no autorizada | Sin identidad válida en la red |
| Atacante interno | Entidad no autorizada | Acceso legítimo, comportamiento malicioso |
| Nodo comprometido | Entidad no autorizada | Dispositivo legítimo comprometido |
| Controlador SDN | Agente del sistema | Traduce decisiones a reglas |
| Dispositivos de red | Agente del sistema | Ejecutan forwarding, filtrado y mitigación |
| Monitor / Detection / Incident / Policy | Agentes del sistema | Observan, detectan, registran y deciden |
| AAA / RADIUS | Agente del sistema | Autentican y autorizan a las poblaciones (comunidad y operadores) |
| Servicios y servidores | Agente del sistema | Proveen recursos y registros |

---

## 4. El rol no otorga confianza permanente

El permiso efectivo no depende solo del rol:

```text
PERMISO EFECTIVO = ROL + RECURSO + ACCIÓN + CONTEXTO + VIGENCIA + ESTADO DE SEGURIDAD
```

Combinaciones que el modelo debe admitir:

| Actor | Recurso | Condición | Resultado |
|---|---|---|---|
| Usuario académico | Servidor académico | Perfil ACADÉMICO, tráfico normal | Permitir |
| Usuario académico | Red de gestión | Perfil BASE, sin elevación | Denegar |
| Usuario académico | Servidor de laboratorio | Elevación temporal aprobada, dentro del TTL | Permitir |
| Usuario académico | Servidor de laboratorio | Elevación expirada | Denegar |
| Usuario académico | Servidor académico | Tráfico anómalo o dispositivo comprometido | Aislar o bloquear |
| Especialista de TI | Logs de seguridad | Dispositivo registrado + autenticado | Permitir |
| Especialista de TI | Política de red | No autorizado para modificarla | Denegar |
| Administrador de Red | Política SDN | Sesión administrativa activa | Permitir y auditar |
| Superadministrador | Política global | Autenticado, sesión privilegiada | Permitir y auditar |

Esto conecta R1 y R2 con R3–R5: la autorización habilita el acceso, pero no suspende la vigilancia. La detección puede restringir, aislar o bloquear el tráfico de un actor que sí posee autorización válida.

---

## 5. Cuestiones abiertas

- **Delegación del registro de Especialistas de TI.** Si el Administrador de Red puede registrar Especialistas de TI o esa función queda solo en el Superadministrador.
- **Matriz Actor → Recurso.** Se deriva de este documento y de [`02_recursos_y_servicios.md`](02_recursos_y_servicios.md); corresponde a `03_permisos.md`.
