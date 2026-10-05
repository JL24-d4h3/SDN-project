# Modelo de Dominio

# Marco del proyecto SDN

**Curso:** TEL354 — Redes Definidas por Software
**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** A — Modelo de dominio
**Fecha:** 17 de septiembre de 2026

---

Este documento establece el marco del proyecto: qué se propone, por qué y con qué límites.

Continúa en documentos separados:

- **Requisitos** — funcionales, transversales, no funcionales, arquitectónicos y de pruebas: [`../B-Drivers/01_Requisitos_y_Restricciones_SDN_v0.1.md`](../B-Drivers/01_Requisitos_y_Restricciones_SDN_v0.1.md)
- **Restricciones** — condiciones impuestas al proyecto: [`../B-Drivers/02_restricciones.md`](../B-Drivers/02_restricciones.md)
- **Actores, roles y agentes**: [`01_actores-roles_y_agentes.md`](01_actores-roles_y_agentes.md)
- **Recursos y servicios**: [`02_recursos_y_servicios.md`](02_recursos_y_servicios.md)

---

## 1. Propósito

Diseñar una solución de seguridad basada en SDN para una red de campus académico, a partir de los cinco requerimientos del proyecto:

- **R1:** Controlar el acceso a la red: perfil mínimo por defecto para todo dispositivo conectado, y privilegios superiores solo mediante autenticación y autorización (acorde con el rol y el contexto).
- **R2:** Restringir el acceso a recursos privilegiados solo a usuarios autorizados.
- **R3:** Detectar y mitigar ataques encubiertos en la intranet.
- **R4:** Detectar y mitigar ataques DDoS brute-force en la intranet.
- **R5:** Proteger a la red de ataques externos mediante seguridad perimetral.

> **Criterio de alcance:** la arquitectura deberá considerar integralmente los cinco requerimientos. La implementación detallada se concentrará en los tres requerimientos asignados al grupo. Las decisiones marcadas como propuestas deberán validarse durante HLD, LLSD y pruebas.

---

## 2. Contexto y problema

Una red de campus académico integra numerosos usuarios, dispositivos y servicios que requieren conectividad permanente. Los usuarios tienen distintas responsabilidades y, por tanto, diferentes necesidades de acceso. Asimismo, existen recursos que requieren protección diferenciada y amenazas que pueden originarse tanto dentro como fuera de la red.

La solución deberá proporcionar mecanismos para:

1. controlar el acceso según dispositivo, perfil y contexto, con identidad solo para elevar privilegios;
2. proteger recursos privilegiados;
3. detectar comportamientos maliciosos dentro de la intranet;
4. preservar la disponibilidad ante ataques de saturación;
5. controlar amenazas provenientes del exterior.

El problema se formula como la necesidad de **gestionar y proteger una red de campus mediante mecanismos programables y coherentes con una arquitectura SDN**.

---

## 3. Objetivo general

Diseñar una solución de seguridad basada en SDN que permita controlar el acceso de usuarios, proteger recursos privilegiados, detectar y mitigar amenazas internas y externas y preservar la disponibilidad de los servicios de red.

La arquitectura deberá permitir que las decisiones de seguridad puedan traducirse en políticas y acciones aplicables sobre la infraestructura SDN.

---

## 4. Alcance

### 4.1 Alcance funcional

La solución deberá contemplar:

- control de acceso;
- autorización sobre recursos;
- monitoreo de tráfico;
- detección de amenazas;
- mitigación;
- seguridad perimetral;
- gestión de políticas;
- registro y auditoría;
- recuperación;
- evaluación cuantitativa.

### 4.2 Alcance de implementación

El grupo deberá implementar los tres requerimientos asignados por el proyecto del curso.

La arquitectura global deberá mostrar cómo los cinco requerimientos podrían coexistir e interactuar dentro de una solución única.

### 4.3 Entorno de referencia

El prototipo estará orientado a una red de campus académico representativa. No será necesario reproducir físicamente la escala real de la universidad; el entorno deberá ser suficiente para validar los escenarios y métricas definidos.

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

**Función:** consumir servicios de red y aplicaciones institucionales. Es el perfil por defecto de todo dispositivo conectado que no haga match con el registro de dispositivos privilegiados.

**Puede**

- Conectarse y obtener el perfil BASE sin autenticación digital (presencia física, RP-13).
- Obtener configuración de red (DHCP), resolución de nombres (DNS) y acceso al portal.
- Autenticarse en el portal contra el IdP institucional y obtener el perfil ACADÉMICO (servicios académicos e Internet).
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

**Cómo accede:** su dispositivo figura en el registro de dispositivos privilegiados y, para ejercer el rol, debe autenticarse (portal cautivo / AAA) con credenciales propias y código TOTP (MFA obligatorio). Sin login, su equipo tiene perfil BASE.

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

**Cómo accede:** dispositivo registrado + autenticación con credenciales propias y código TOTP (MFA obligatorio). Aplica el mismo principio: sin login, su PC es una PC con perfil BASE, aunque esté en la sala de administración.

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

**Cómo accede:** dispositivo registrado + autenticación con MFA obligatorio; se contempla además el acceso remoto a la plataforma, sujeto a política.

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
    (perfil BASE;           (registro + login)
     ACADÉMICO con login)       │
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

Dispone de acceso legítimo a la red —presencia física; perfil BASE y, tras el login, ACADÉMICO— pero genera actividad maliciosa. Es el caso que obliga a separar acceso de confianza: un actor con acceso legítimo puede convertirse en origen de tráfico malicioso en cualquier momento.

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
| AAA / RADIUS | Agente del sistema | Autentican y autorizan a operadores |
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

# Recursos de red, servidores y servicios

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** A — Modelo de dominio
**Estado:** Borrador formal para revisión

---

## 1. Criterio de clasificación

**Recurso:** entidad con valor para la institución que el sistema debe proteger. Incluye servidores, datos, dispositivos, configuraciones y registros.

**Servicio:** recurso que se ofrece a un actor a través de la red. Un servicio es, por tanto, un recurso con consumidores identificables.

El catálogo se organiza en **tres clases de destino** —según quién los consume y qué privilegio exigen— y cada recurso recibe además un nivel de protección según el impacto de su compromiso:

| Clase de destino | Definición |
|---|---|
| **Recursos de usuario** | Servicios que consume el usuario académico con su perfil ACADÉMICO tras autenticarse: servicios académicos e Internet. Ninguno es alcanzable en BASE: allí solo existe la habilitación mínima del dispositivo (DHCP, DNS y portal). |
| **Recursos restringidos** | Servicios que exigen una elevación aprobada: laboratorios, repositorios e investigación. |
| **Infraestructura** | Los componentes que sostienen la propia solución: plano de control, gestión de identidad y observabilidad. El usuario académico tiene el acceso denegado por defecto. |

| Nivel | Significado | Equivalencia con R2.2 |
|---|---|---|
| **Crítico** | Su compromiso afecta a toda la red o a la autoridad del sistema. | Crítico |
| **Alto** | Contiene información sensible o habilita la operación de la red. | Privilegiado |
| **Medio** | Sirve a un grupo de usuarios; su caída degrada el servicio. | General |
| **Bajo** | Servicio de uso general, sin información sensible. | General |

---

## 2. Catálogo

### 2.1 Recursos de usuario

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Conectividad base del dispositivo | Servicio | Habilitación inicial del perfil BASE, como lista cerrada: DHCP, ARP y el segmento de acceso. No da acceso a los servicios de la intranet — eso lo decide la autenticación. | Bajo |
| Acceso a Internet | Servicio | Salida a redes externas, si la arquitectura lo contempla. | Bajo |
| Resolución de nombres (DNS) | Servicio | Servicio de nombres; forma parte de la lista cerrada del perfil BASE. | Bajo |
| Servicios públicos e institucionales | Servicio | Servicios abiertos a toda la comunidad autenticada. | Medio |
| Servicios y servidores académicos | Servicio | Plataformas de apoyo a la docencia y al estudio (LMS y equivalentes) y otros recursos de la universidad, como la nube privada. | Medio |
| Servicios administrativos | Servicio | Sistemas de gestión institucional. | Alto |
| Base de datos institucional | Recurso | Almacenamiento de la información de los servicios anteriores. | Crítico |

### 2.2 Recursos restringidos

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Repositorios y recursos de investigación | Servicio | Repositorios especiales y recursos de los grupos de investigación. | Alto |
| Servicios técnicos internos | Servicio | Servicios internos no disponibles para el perfil BASE. | Alto |

### 2.3 Infraestructura

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Controlador SDN | Recurso | Plano de control; concentra las decisiones de la red. | Crítico |
| Consola de administración SDN | Servicio | Interfaz de gestión del controlador y de las políticas. | Crítico |
| Dispositivos de red (switches) | Recurso | Plano de datos; ejecutan las reglas instaladas. | Crítico |
| Reglas de flujo y configuración de segmentación | Recurso | Estado de forwarding y aislamiento vigente en la red. | Alto |
| Segmentos de red (VLAN) | Recurso | Dominios de segmentación que separan poblaciones y recursos. | Alto |
| Canal de control (red de gestión) | Recurso | Conectividad entre controlador y switches; out-of-band, con la variante in-band como objetivo (ver flujo §2.6). | Crítico |

### 2.4 Seguridad y observabilidad

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Monitor | Recurso | Recopila counters y estadísticas del plano de datos. | Alto |
| Detection Engine | Recurso | Determina si existe comportamiento anómalo (R3, R4): la función de detección interna (IDS); la mitigación (función IPS) la ejecutan Policy Engine y controlador. El IDS/IPS perimetral de R5.2 es evaluación tecnológica. | Crítico |
| Incident Manager | Recurso | Registra y gestiona los incidentes de seguridad. | Alto |
| Policy Engine | Recurso | Decide la respuesta ante incidentes y solicitudes de elevación. | Crítico |
| Políticas de seguridad | Recurso | Reglas que definen el comportamiento permitido de la red. | Crítico |
| Consola de monitoreo | Servicio | Visualización de estado de red, eventos y alertas. | Alto |
| Logs de seguridad | Recurso | Registro de eventos y decisiones de seguridad. | Alto |
| Almacenamiento de registros | Recurso | Persistencia de logs para análisis e investigación. | Alto |
| Logs operativos | Recurso | Registro de operación y cambios administrativos. | Medio |

### 2.5 Identidad y control de acceso

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Perfiles de acceso | Recurso | Definición de los perfiles (BASE, ACADÉMICO, LABORATORIO, INVESTIGACIÓN, TI, ADMIN_RED, SUPER_ADMIN) y sus reglas de red asociadas. | Crítico |
| Registro de dispositivos privilegiados | Recurso | Base de datos de los dispositivos de operadores (MAC, tipo, titular, rol, vigencia, responsable). Solo los dispositivos privilegiados se registran; lo que no hace match recibe perfil BASE. Sirve además de auditoría del alta de dispositivos. | Crítico |
| AAA / RADIUS | Recurso | Autenticación, autorización y accounting de las poblaciones: la comunidad (contra el IdP) y los operadores (contra el repositorio propio). No cataloga dispositivos: autentica personas. | Crítico |
| Portal cautivo | Servicio | Punto de autenticación de la red: la comunidad obtiene el perfil ACADÉMICO; los operadores, su sesión de rol. | Alto |
| Sistema de identidad institucional (IdP/LDAP) | Recurso externo | Backend de identidad consultado por AAA para verificar a la comunidad universitaria; no lo administra el proyecto. | Crítico |
| Roles y permisos | Recurso | Definición de autorizaciones del sistema. | Crítico |
| Sesiones y estado de acceso | Recurso | Sesiones activas, perfiles vigentes y su TTL. | Alto |

### 2.6 Dispositivos de usuario final

| Recurso o servicio | Tipo | Descripción | Nivel |
|---|---|---|---|
| Dispositivos de usuario | Recurso | Equipos que se conectan a la red; origen de los flujos. Los académicos no se registran; los de operadores figuran en el registro de dispositivos privilegiados. | Medio |

---

## 3. Recursos críticos

Los siguientes recursos concentran el mayor impacto y son los candidatos naturales a protección diferenciada (R2.8):

| Recurso | Nivel |
|---|---|
| Controlador SDN | Crítico |
| Consola de administración SDN | Crítico |
| Dispositivos de red | Crítico |
| Canal de control | Crítico |
| Detection Engine | Crítico |
| Policy Engine | Crítico |
| Políticas de seguridad | Crítico |
| Base de datos institucional | Crítico |
| Registro de dispositivos privilegiados | Crítico |
| AAA / RADIUS | Crítico |
| Sistema de identidad institucional | Crítico |
| Perfiles de acceso | Crítico |
| Roles y permisos | Crítico |
| Logs de seguridad | Alto |
| Segmentos de red (VLAN) | Alto |

---

## 4. Cuestiones abiertas

- **Frontera entre niveles.** La distinción exacta entre *medio* y *alto* —es decir, qué convierte a un recurso en privilegiado en el sentido de R2— todavía no está fijada.
- **Límite del sistema.** Si el firewall perimetral es parte de la solución o un sistema externo es materia de la Fase C. La cadena de detección (Monitor, Detection, Incident, Policy) sí es parte del sistema; el IdP institucional es externo.
- **Dispositivos de usuario final.** Definir si son recursos protegidos o únicamente orígenes de tráfico sujetos a observación.
- **Red inalámbrica y red de invitados.** Confirmar si están dentro del alcance del prototipo.
- **Retención de registros.** Dónde se almacenan los logs y por cuánto tiempo.
- **Acceso remoto.** Definir la política de acceso remoto de los operadores (contemplado para el Superadministrador).

---

La matriz Actor → Recurso se construye sobre este catálogo y se documenta en `03_permisos.md`.

# Modelo de Dominio — Permisos

## 1. Objetivo

Definir las acciones que pueden ejecutar los roles autorizados sobre los recursos y servicios de la solución SDN, aplicando el principio de mínimo privilegio.

Los permisos representan **acciones autorizadas**; no representan por sí mismos a los actores, roles ni recursos.

## 2. Catálogo de permisos

| ID | Permiso | Descripción |
|---|---|---|
| P01 | Autenticarse | Iniciar sesión y acreditar la identidad ante la plataforma. |
| P02 | Acceder a la red | Obtener acceso a los segmentos de red permitidos según el rol y las políticas vigentes. |
| P03 | Acceder a servicio | Utilizar un servicio autorizado. |
| P04 | Consultar recurso | Leer o consultar información de un recurso autorizado. |
| P05 | Ejecutar operación | Ejecutar una operación funcional sobre un servicio autorizado. |
| P06 | Consultar estado de red | Consultar el estado, disponibilidad y métricas operativas de la red. |
| P07 | Consultar tráfico | Consultar información y métricas asociadas al tráfico de red. |
| P08 | Consultar eventos y logs | Consultar eventos, registros y trazas autorizadas. |
| P09 | Consultar alertas | Visualizar alertas generadas por los mecanismos de seguridad. |
| P10 | Analizar incidente | Investigar y analizar un evento o incidente de seguridad. |
| P11 | Gestionar alerta | Clasificar, confirmar, descartar o escalar una alerta. |
| P12 | Ejecutar mitigación | Aplicar una medida de contención o mitigación previamente autorizada. |
| P13 | Aislar nodo | Restringir o aislar un dispositivo identificado como comprometido o malicioso. |
| P14 | Gestionar usuario | Crear, modificar, bloquear, desbloquear o deshabilitar cuentas de usuario. |
| P15 | Asignar rol | Asignar o modificar el rol de un usuario. |
| P16 | Gestionar permisos | Crear, modificar o revocar permisos asociados a roles. |
| P17 | Gestionar políticas de acceso | Crear, modificar, activar, desactivar o eliminar políticas de autorización. |
| P18 | Gestionar políticas de seguridad | Configurar reglas de detección, prevención y mitigación. |
| P19 | Gestionar reglas de red | Crear, modificar o eliminar reglas de forwarding, filtrado o control de tráfico. |
| P20 | Gestionar segmentación | Crear, modificar o administrar segmentos/VLAN u otros mecanismos de aislamiento lógico. |
| P21 | Gestionar dispositivos de red | Registrar, configurar, actualizar, habilitar o deshabilitar dispositivos administrados. |
| P22 | Gestionar controlador SDN | Administrar la configuración y operación del controlador SDN. |
| P23 | Gestionar mecanismos de seguridad | Administrar IDS, IPS, firewall u otros mecanismos de protección integrados. |
| P24 | Gestionar administradores | Crear, modificar, bloquear, revocar o eliminar cuentas y privilegios de Administradores de Red y Especialistas de TI. |
| P25 | Auditar operaciones | Consultar y revisar las acciones realizadas por usuarios y administradores. |
| P26 | Gestionar configuración global | Modificar parámetros globales de la plataforma SDN y sus componentes críticos. |
| P27 | Gestionar recuperación | Ejecutar o administrar procedimientos de restauración y recuperación de la plataforma. |
| P28 | Solicitar elevación | Solicitar un perfil de acceso temporal (p. ej. LABORATORIO) con justificación, alcance y duración. |
| P29 | Aprobar elevación | Aprobar o rechazar solicitudes de elevación temporal; definir su alcance y TTL. |
| P30 | Registrar dispositivo privilegiado | Dar de alta, modificar o dar de baja dispositivos en el registro de dispositivos privilegiados, con su información completa (MAC, tipo, titular, rol, vigencia) y dejar constancia para auditoría. |

> Nota: P28–P30 se incorporan con la introducción del modelo de perfiles de acceso y del registro de dispositivos privilegiados (ver [`01_actores-roles_y_agentes.md`](01_actores-roles_y_agentes.md)); su asignación a roles queda pendiente de la matriz Rol × Permiso.

## 3. Principios de asignación

1. Un permiso debe concederse explícitamente a uno o más roles.
2. La posesión de un rol no implica acceso irrestricto a todos los recursos.
3. El acceso efectivo depende de **rol + permiso + recurso/servicio + política + contexto + vigencia**. Los privilegios concedidos mediante elevación son temporales: expiran por TTL o por cierre de sesión.
4. El acceso base de la red (perfil BASE) no depende de ningún permiso otorgado a una persona: se concede al dispositivo por presencia física y cubre solo lo mínimo (deny by default).
5. Los permisos administrativos deben mantenerse separados de los permisos de usuario final.
6. Las operaciones críticas deben quedar registradas mediante auditoría.
7. Las acciones de mitigación deben poder estar sujetas a políticas y condiciones de seguridad.
8. El Superadministrador posee control máximo, pero sus operaciones críticas también deben ser auditables.
9. Un atacante interno o externo y un nodo comprometido **no reciben permisos autorizados**; son entidades cuyo acceso o comportamiento debe ser detectado, restringido o bloqueado.

## 4. Niveles conceptuales

### Permisos de acceso
P01–P05, P28

Permiten autenticarse, acceder a la red, utilizar recursos o servicios autorizados y solicitar elevaciones temporales.

### Permisos de supervisión y seguridad
P06–P13, P25

Permiten observar la red, investigar eventos y ejecutar acciones de respuesta.

### Permisos de administración
P14–P23, P27, P29, P30

Permiten administrar usuarios, políticas, infraestructura y mecanismos de seguridad; aprobar elevaciones y registrar dispositivos privilegiados.

### Permisos de control maestro
P24, P26

Permiten administrar privilegios administrativos y configuración global de la plataforma.

> Nota: la asignación definitiva de estos permisos a cada rol se establece en la matriz **Rol × Permiso**. Esta lista define el catálogo de permisos, no sustituye dicha matriz.

# Modelo de Dominio — Relaciones entre Entidades

## 1. Objetivo

Definir las relaciones estructurales entre actores, roles, perfiles de acceso, permisos, recursos y servicios de la solución SDN.

## 2. Relaciones principales

### 2.1 Actor → Rol

**Un actor humano puede desempeñar un rol dentro de la plataforma.**

```text
Actor ── desempeña ──> Rol
```

Ejemplos:

```text
Usuario académico ──> Usuario académico (nivel 0; BASE por defecto, ACADÉMICO con login)
Especialista de TI ──> Especialista de TI (nivel 1, requiere registro + login)
Administrador de Red ──> Administrador de Red (nivel 2, requiere registro + login)
Superadministrador ──> Superadministrador (nivel 3, requiere registro + login)
```

Un mismo individuo podría tener más de un rol si la política de la plataforma lo permite, pero los privilegios efectivos deben determinarse de manera explícita.

### 2.2 Dispositivo → Perfil de acceso

**Todo dispositivo conectado recibe un perfil de acceso; el perfil determina las reglas de red que se le aplican.**

```text
Dispositivo ── recibe ──> Perfil de acceso (BASE, ACADÉMICO, LABORATORIO, TI, ADMIN_RED, …)
```

- **Perfil BASE:** automático por presencia física (RP-13). Todo dispositivo que **no hace match con el registro de dispositivos privilegiados** lo recibe. Deny by default: DHCP, DNS y el portal — el mínimo del dispositivo; los servicios académicos e Internet llegan con el login.
- **Perfil ACADÉMICO:** la comunidad universitaria lo obtiene al autenticarse en el portal contra el IdP institucional (sin MFA): servicios académicos e Internet.
- **Perfiles elevados (LABORATORIO, INVESTIGACIÓN, TI, ADMIN_RED, SUPER_ADMIN):** requieren justificación. Los temporales de usuario académico exigen solicitud aprobada y TTL; los de operadores exigen dispositivo registrado + autenticación con MFA.

La relación entre dispositivo y perfil no es permanente: los perfiles temporales expiran y las sesiones privilegiadas se cierran (idle_timeout).

### 2.3 Rol → Permiso

**Un rol posee uno o más permisos.**

```text
Rol ── posee/concede ──> Permiso
```

Ejemplos:

```text
Usuario académico ──> Acceder a la red
Usuario académico ──> Acceder a servicio
Usuario académico ──> Solicitar elevación (P28)

Especialista de TI ──> Consultar alertas
Especialista de TI ──> Analizar incidente
Especialista de TI ──> Ejecutar mitigación autorizada

Administrador de Red ──> Gestionar políticas de acceso
Administrador de Red ──> Gestionar reglas de red
Administrador de Red ──> Aprobar elevación (P29)
Administrador de Red ──> Registrar dispositivo privilegiado (P30)

Superadministrador ──> Gestionar administradores
Superadministrador ──> Gestionar permisos
Superadministrador ──> Gestionar configuración global
```

### 2.4 Permiso → Recurso

**Un permiso determina qué acción puede realizarse sobre un recurso.**

```text
Permiso ── se aplica sobre ──> Recurso
```

Ejemplos:

```text
Consultar recurso ──> Servidor académico
Gestionar reglas de red ──> Reglas de flujo
Gestionar dispositivos de red ──> Switch SDN
Gestionar controlador SDN ──> Controlador SDN
Registrar dispositivo privilegiado ──> Registro de dispositivos privilegiados
Consultar logs ──> Logs de seguridad
```

La relación debe especificar, cuando corresponda, el alcance del recurso.

### 2.5 Permiso → Servicio

**Un permiso puede habilitar una acción sobre un servicio.**

```text
Permiso ── habilita ──> Servicio
```

Ejemplos:

```text
Acceder a servicio ──> Servicio académico
Ejecutar operación ──> Servidor de laboratorio
Consultar alertas ──> Servicio de monitoreo
Autenticarse ──> Portal cautivo
Gestionar políticas de acceso ──> Servicio de administración SDN
```

### 2.6 Rol → Recurso/Servicio

Esta relación no debe utilizarse como sustituto de Rol → Permiso.

Conceptualmente:

```text
Rol
 │
 └── mediante un permiso ──> Recurso/Servicio
```

Por tanto:

```text
Rol + Permiso + Recurso/Servicio
        ↓
   Acción autorizada
```

Esto evita modelar simplemente:

```text
Usuario académico ──> Servidor académico
```

sin especificar qué puede hacer sobre dicho servidor.

### 2.7 Recurso → Servicio

**Un servicio puede depender de uno o más recursos, y un recurso puede soportar uno o más servicios.**

```text
Servicio ── utiliza/depende de ──> Recurso
```

Ejemplo:

```text
Servicio académico
    ├── depende de ──> Servidor académico
    ├── depende de ──> Base de datos institucional
    └── depende de ──> Segmento de servidores
```

---

## 3. Relaciones de seguridad y administración

### 3.1 Actor/Dispositivo → Recurso/Servicio

El acceso de un actor o dispositivo a un recurso o servicio **no debe considerarse una relación directa permanente**. Debe resolverse mediante autorización:

```text
Actor / Dispositivo
  ↓
Perfil de acceso
  ↓
Rol (si la identidad está autenticada)
  ↓
Permiso
  ↓
Recurso/Servicio
  ↓
Política de acceso (contexto + vigencia)
  ↓
Decisión: PERMITIR / DENEGAR
```

La cadena tiene dos entradas, según el caso:

- **Sin autenticación:** Dispositivo → perfil BASE → políticas por defecto (deny by default).
- **Con autenticación:** Dispositivo + identidad → perfil ACADÉMICO (comunidad) o rol (operadores) → permisos → políticas contextuales, con vigencia explícita (TTL o sesión).

### 3.2 Evento → Alerta → Incidente

Cuando un evento de seguridad satisface las condiciones definidas por las políticas de detección:

```text
Evento ── puede generar ──> Alerta
Alerta ── puede derivar en ──> Incidente
```

La cadena técnica completa (R3, R4):

```text
Tráfico ──> Switch (counters) ──> Monitor ──> Detection Engine
     ──> Incident Manager (incidente) ──> Policy Engine (decisión)
     ──> Controlador SDN (FLOW_MOD) ──> Switch (enforcement)
```

### 3.3 Incidente → Mitigación

Un incidente puede desencadenar una acción de respuesta:

```text
Incidente ── desencadena ──> Mitigación
```

Ejemplo:

```text
Detección de flood hacia el servidor
        ↓
     Incidente
        ↓
RATE_LIMIT / BLOCK / ISOLATE / QUARANTINE
        ↓
Regla temporal con prioridad alta (+ meter), con hard/idle_timeout
```

### 3.4 Nodo → Tráfico

```text
Nodo ── genera ──> Tráfico
```

El tráfico puede ser observado y analizado por los mecanismos de seguridad:

```text
Tráfico
   ↓
Switch (counters por puerto y por flujo)
   ↓
Monitor → Detection Engine
   ↓
Evento / Alerta
```

### 3.5 Sesión privilegiada → Reglas de red

La sesión de un operador autenticado produce reglas concretas y reversibles:

```text
Sesión (identidad + dispositivo + contexto)
   ↓
Controlador instala FLOW_MOD con prioridad alta
   ↓
Al cerrar la sesión (logout o idle_timeout), las reglas se retiran
```

---

## 4. Relación de administración jerárquica

La administración de privilegios refleja la jerarquía definida:

```text
Superadministrador
       │
       ├── administra ──> Administrador de Red
       │
       └── administra ──> Especialista de TI
```

El Administrador de Red administra principalmente:

```text
Administrador de Red
       ├── administra ──> Políticas
       ├── administra ──> Reglas de red
       ├── administra ──> Dispositivos
       ├── registra ────> Dispositivos privilegiados (P30)
       └── aprueba ─────> Elevaciones temporales (P29)
```

El Especialista de TI administra principalmente el ciclo de seguridad:

```text
Especialista de TI
       ├── supervisa ──> Eventos
       ├── analiza ──> Alertas
       ├── gestiona ──> Incidentes
       └── ejecuta ──> Mitigaciones autorizadas
```

---

## 5. Modelo integrado

La relación conceptual completa puede representarse como:

```text
                         ACTOR
                           │
                       desempeña
                           ▼
                          ROL
                           │
                     posee/concede
                           ▼
                        PERMISO
                       /         \
                    /               \
                   ▼                 ▼
        se aplica a RECURSO       habilita SERVICIO
                   ▲                  │
                   │                  │
                   └──── depende ─────┘

          DISPOSITIVO ── recibe ──> PERFIL DE ACCESO
                                        │
                                        ▼
                                  REGLAS DE RED
                                        │
                                     aplica el
                                   CONTROLADOR

NODO ── genera ──> TRÁFICO
                     │
               observado por
                     ▼
          SWITCH (counters) → MONITOR
                     │
                     ▼
              DETECTION ENGINE
                     │
                  genera
                     ▼
             INCIDENT MANAGER
                     │
                     ▼
               POLICY ENGINE
                     │
                  decide
                     ▼
               CONTROLADOR
                     │
                  FLOW_MOD
                     ▼
                  SWITCH
                     │
                     ▼
        MITIGACIÓN / RESTAURACIÓN
```

---

## 6. Regla central de autorización

La relación fundamental del modelo debe entenderse como:

```text
Actor / Dispositivo
  → Perfil de acceso
  → Rol (si hay identidad autenticada)
  → Permiso
  → Recurso/Servicio
  → Política (contexto + vigencia)
  → Decisión de acceso
```

Por tanto, **tener un rol no significa tener acceso absoluto, y estar conectado no significa tener privilegios**. El acceso efectivo resulta de la combinación entre el perfil vigente, el rol, los permisos asignados, el recurso o servicio solicitado, el contexto y la vigencia de la política. Todo lo que no esté explícitamente permitido queda denegado.

# Drivers

# 5. Casos de uso mínimos

## CU-01 — Acceso autorizado
Un dispositivo se conecta y recibe el perfil BASE (el mínimo); un miembro de la comunidad se autentica en el portal y obtiene el perfil ACADÉMICO; un operador, con credenciales y segundo factor, obtiene los permisos correspondientes a su rol, con vigencia acotada.

## CU-02 — Acceso no autorizado
Un dispositivo intenta alcanzar recursos por encima de su perfil y el sistema rechaza la solicitud y registra el evento.

## CU-03 — Acceso autorizado a recurso privilegiado
Un usuario autorizado solicita un recurso privilegiado y el acceso es permitido y registrado.

## CU-04 — Acceso no autorizado a recurso privilegiado
Un usuario sin privilegios suficientes intenta acceder y el sistema bloquea la solicitud.

## CU-05 — Port scanning
Un host genera múltiples intentos de conexión; el sistema detecta el patrón y aplica la respuesta definida.

## CU-06 — IP spoofing
Se detecta tráfico inconsistente con las condiciones de origen esperadas y se aplica la respuesta definida.

## CU-07 — DDoS interno
El tráfico hacia un servidor supera el comportamiento esperado; el sistema detecta, mitiga y posteriormente recupera la política normal.

## CU-08 — Ataque externo
El tráfico externo es inspeccionado; una amenaza identificada genera alerta, bloqueo o mitigación.

## CU-09 — Gestión de política
Un administrador se autentica, modifica una política y la aplica mediante el sistema.

## CU-10 — Recuperación
Después de un incidente, el sistema elimina o modifica las reglas temporales y retorna a la política normal.

---
#
# 6. Flujos operativos

## 11.1 Operación normal

**Dispositivo → perfil BASE (presencia física) → política por defecto → recurso → monitoreo → registro. Con login: autenticación → perfil ACADÉMICO (comunidad) o identidad/rol (operadores) → política contextual → recurso.**

## 11.2 Acceso no autorizado

**Solicitud por encima del perfil → política deniega → rechazo → registro → alerta cuando corresponda.**

## 11.3 Incidente de seguridad

**Tráfico → monitoreo → detección → clasificación → decisión → mitigación → registro → recuperación.**

## 11.4 Administración

**Administrador → autenticación → gestión de política → validación → aplicación → auditoría.**

---
#
# 7. Políticas de seguridad

### PS-01 — Mínimo privilegio
Cada usuario deberá disponer únicamente de los permisos necesarios.

### PS-02 — Denegación por defecto
Una solicitud sin autorización explícita deberá considerarse no autorizada, salvo justificación del diseño final.

### PS-03 — Separación por roles
Los privilegios deberán asociarse principalmente a roles.

### PS-04 — Protección diferenciada
Los recursos críticos deberán recibir controles superiores.

### PS-05 — Respuesta proporcional
La mitigación deberá corresponder al tipo y nivel de amenaza.

### PS-06 — Trazabilidad
Las decisiones relevantes deberán poder auditarse.

### PS-07 — Reversibilidad
Las acciones temporales deberán poder revertirse.

---
#
# 8. Criterios de éxito

La solución deberá evaluarse mediante criterios cualitativos y cuantitativos.

## Seguridad

- tasa de bloqueo de accesos inválidos;
- precisión en la restricción de recursos;
- tasa de detección;
- tasa de falsos positivos.

## Rendimiento

- latencia de autenticación;
- latencia de autorización;
- tiempo de detección;
- tiempo de mitigación;
- throughput;
- solicitudes por segundo.

## Disponibilidad y resiliencia

- disponibilidad durante ataques;
- tiempo de recuperación;
- impacto sobre tráfico legítimo.

## Escalabilidad

- usuarios concurrentes;
- sesiones concurrentes;
- eventos por segundo;
- cantidad de políticas/reglas gestionadas.

## Consumo de recursos

- CPU;
- memoria;
- ancho de banda;
- utilización de recursos de dispositivos SDN;
- TCAM, cuando corresponda.

---
#
# 9. Requisitos de pruebas

### PT-01 — Pruebas funcionales
Cada requerimiento implementado deberá contar con pruebas positivas.

### PT-02 — Pruebas negativas
Deberán probarse condiciones en las que el sistema debe rechazar, bloquear o mitigar.

### PT-03 — Rendimiento
Deberá medirse el comportamiento bajo diferentes cargas.

### PT-04 — Ataques
Los escenarios de seguridad deberán ejecutarse en el entorno controlado.

### PT-05 — Recuperación
Deberá comprobarse el retorno a operación normal.

### PT-06 — Escalabilidad
Cuando resulte viable, deberán incrementarse progresivamente usuarios, flujos, solicitudes o eventos.

### PT-07 — Comparación de alternativas
Cuando existan alternativas de diseño, deberán compararse mediante métricas objetivas.

---
#
# 10. Administración y observabilidad

### ADM-01
El administrador deberá poder consultar las políticas activas.

### ADM-02
El administrador deberá poder identificar eventos de seguridad relevantes.

### ADM-03
La solución deberá proporcionar información suficiente para investigar incidentes.

### ADM-04
Los cambios de política deberán poder registrarse.

### ADM-05
Las acciones automáticas de mitigación deberán poder identificarse posteriormente.

# Especificación de Requisitos
## Solución de seguridad para una red de campus basada en SDN

**Curso:** TEL354 — Redes Definidas por Software  
**Proyecto:** Solución de seguridad para una red de campus académico  
**Versión:** 0.2 — Segunda versión  
**Fecha:** 16 de septiembre de 2026  
**Estado:** Borrador formal para revisión

---

#
# 1. Requerimientos funcionales

## R1 — Control de acceso según rol

El control de acceso parte del **perfil BASE por defecto**: todo dispositivo conectado recibe privilegios mínimos por presencia física (RP-13), sin autenticación digital. La identidad solo se exige para salir de ese mínimo —el login de la comunidad (perfil ACADÉMICO) o el de un operador (sesión de rol)—; los privilegios resultantes se traducen en reglas de red concretas y reversibles.

### R1.1 Identificación
El sistema deberá identificar el dispositivo que solicita acceso y su contexto de conexión: MAC, puerto, switch y ubicación. La MAC es un atributo del dispositivo, no una credencial.

### R1.2 Autenticación
El sistema deberá exigir autenticación para salir del perfil BASE, mediante el portal cautivo: el usuario académico se autentica contra el IdP institucional (perfil ACADÉMICO); los operadores, con credenciales propias y segundo factor (sesión de rol).

### R1.3 Asignación de perfil
El sistema deberá asociar cada dispositivo con el perfil de acceso que le corresponde: BASE por defecto; perfiles elevados solo tras autenticación o elevación aprobada.

### R1.4 Política de acceso
El sistema deberá determinar el acceso según identidad, atributos, contexto, recurso, acción y vigencia, y traducirlo a reglas de red.

### R1.5 Mínimo privilegio
Los dispositivos y usuarios deberán recibir únicamente los permisos necesarios; todo lo demás queda denegado por defecto.

### R1.6 Denegación
Los accesos inválidos o no autorizados deberán ser rechazados, en particular todo acceso a la infraestructura desde el perfil base.

### R1.7 Administración
La solución deberá permitir gestionar roles, perfiles y el registro de dispositivos privilegiados.

### R1.8 Superusuarios
Deberá contemplarse un rol administrativo con privilegios superiores cuando sea necesario, restringiendo su uso.

### R1.9 Trazabilidad
Los eventos relevantes de autenticación, autorización y elevación de privilegios deberán poder registrarse.

### R1.10 Escalabilidad
La arquitectura deberá considerar crecimiento de dispositivos y accesos concurrentes; el registro de dispositivos privilegiados debe mantenerse acotado (no se registra a los usuarios académicos).

---

## R2 — Protección de recursos privilegiados

### R2.1 Inventario
Deberán identificarse los recursos que requieren protección.

### R2.2 Clasificación
Los recursos deberán poder clasificarse, como mínimo, en generales, privilegiados y críticos.

### R2.3 Asociación de políticas
Cada recurso privilegiado deberá estar asociado a una política de acceso.

### R2.4 Autorización
El sistema deberá verificar que el usuario o rol esté autorizado antes de permitir el acceso.

### R2.5 Denegación
Los accesos no autorizados deberán ser bloqueados.

### R2.6 Segmentación
La arquitectura deberá permitir segmentar recursos según su nivel de protección cuando corresponda.

### R2.7 Actualización
Las políticas deberán poder actualizarse ante cambios en usuarios, roles o infraestructura.

### R2.8 Protección crítica
Los recursos críticos deberán disponer de controles superiores a los recursos generales.

### R2.9 Auditoría
Los accesos a recursos privilegiados deberán poder registrarse.

### R2.10 Aplicación SDN
Deberá definirse cómo las decisiones de autorización se traducen en reglas o políticas sobre la infraestructura SDN.

---

## R3 — Ataques encubiertos en la intranet

El requerimiento contempla, entre otros, network scanning, port scanning, IP spoofing y ataques distribuidos mediante solicitudes maliciosas.

### R3.1 Monitoreo
La solución deberá obtener información suficiente del tráfico para detectar comportamientos sospechosos.

### R3.2 Scanning
Deberá poder identificarse comportamiento compatible con network/port scanning.

### R3.3 Spoofing
Deberán contemplarse mecanismos para identificar tráfico cuyo origen sea inconsistente con las políticas definidas.

### R3.4 Anomalías
La solución deberá identificar comportamientos que se aparten de la referencia establecida.

### R3.5 Ataques distribuidos
Deberá contemplarse la detección de múltiples orígenes contra un mismo recurso.

### R3.6 Clasificación
Los eventos deberán clasificarse por tipo y, cuando sea posible, nivel de riesgo.

### R3.7 Mitigación
Una amenaza confirmada deberá poder activar una acción de mitigación.

### R3.8 Acciones
Podrán contemplarse bloqueo, rate limiting, aislamiento, redirección y/o alerta, según el diseño.

### R3.9 Recuperación
Las medidas temporales deberán poder revertirse cuando finalice el evento.

### R3.10 Registro
Los eventos deberán quedar registrados para análisis posterior.

---

## R4 — DDoS brute-force en la intranet

### R4.1 Línea base
Deberá definirse una referencia del comportamiento esperado del servicio protegido.

### R4.2 Detección
La solución deberá identificar incrementos anómalos del tráfico hacia un servidor o nodo.

### R4.3 Indicadores
Podrán utilizarse paquetes/s, solicitudes/s, conexiones/s, ancho de banda, número de fuentes, latencia u otros indicadores pertinentes.

### R4.4 Umbrales
Deberán establecerse criterios cuantitativos para distinguir tráfico normal y potencialmente malicioso.

### R4.5 Mitigación
La solución deberá aplicar una política de mitigación ante un evento detectado.

### R4.6 Rate limiting
Deberá evaluarse la limitación de tráfico por origen, destino, flujo u otra dimensión pertinente.

### R4.7 Bloqueo
Deberá poder bloquearse tráfico identificado como malicioso cuando corresponda.

### R4.8 Disponibilidad
La mitigación deberá procurar preservar el servicio legítimo.

### R4.9 Recuperación
La política normal deberá poder restaurarse después del incidente.

### R4.10 Medición
Deberán medirse tiempo de detección, tiempo de mitigación e impacto sobre el servicio.

---

## R5 — Seguridad perimetral

### R5.1 Perímetro
La solución deberá definir mecanismos de control entre redes externas e internas.

### R5.2 IDS/IPS
Deberá evaluarse el uso de IDS, IPS o ambos.

### R5.3 Inspección
El tráfico externo relevante deberá poder analizarse para identificar actividad maliciosa.

### R5.4 Bloqueo por IP
Deberá poder bloquearse tráfico desde direcciones IP identificadas como maliciosas.

### R5.5 Bloqueo hacia destinos
Deberá contemplarse el bloqueo de conexiones hacia destinos maliciosos cuando corresponda.

### R5.6 Inteligencia
Deberá definirse cómo se determinará que una IP, URL u otro indicador es malicioso.

### R5.7 Integración SDN
Los eventos perimetrales deberán poder generar políticas o acciones sobre la red SDN.

### R5.8 Registro
Los eventos deberán poder registrarse.

---

# 2. Requerimientos transversales

### RT-01 — Gestión centralizada de políticas
Deberá existir un mecanismo coherente para definir y administrar políticas.

### RT-02 — Separación de responsabilidades
Los componentes de identidad, autorización, detección, mitigación, monitoreo y administración deberán tener responsabilidades delimitadas.

### RT-03 — Integración SDN
Deberá definirse la interacción entre aplicaciones, controlador y dispositivos SDN.

### RT-04 — Northbound
Deberá definirse la interfaz mediante la cual las aplicaciones/administración interactúan con el controlador, cuando corresponda.

### RT-05 — Southbound
Deberá definirse el mecanismo mediante el cual el controlador comunica reglas a los dispositivos.

### RT-06 — Monitoreo
La solución deberá proporcionar información suficiente sobre estado de red y eventos.

### RT-07 — Auditoría
Los eventos relevantes deberán poder almacenarse para análisis.

### RT-08 — Respuesta automatizada
Las amenazas que cumplan las condiciones establecidas deberán poder activar acciones automáticas.

### RT-09 — Administración
Los administradores deberán disponer de mecanismos para consultar y modificar políticas.

### RT-10 — Recuperación
Las medidas temporales deberán poder revertirse.

---
#
# 3. Requerimientos de calidad

### RNF-01 — Seguridad
La solución deberá minimizar accesos no autorizados.

### RNF-02 — Disponibilidad
Los mecanismos de seguridad no deberán provocar indisponibilidad innecesaria.

### RNF-03 — Rendimiento
La sobrecarga introducida deberá mantenerse dentro de límites aceptables definidos experimentalmente.

### RNF-04 — Latencia
Las decisiones críticas deberán ejecutarse con latencia compatible con la operación prevista.

### RNF-05 — Escalabilidad
La arquitectura deberá admitir crecimiento de usuarios, dispositivos, sesiones y eventos.

### RNF-06 — Flexibilidad
Las políticas deberán poder modificarse sin rediseñar completamente la solución.

### RNF-07 — Modularidad
Los módulos deberán presentar responsabilidades e interfaces claras.

### RNF-08 — Observabilidad
Deberá existir información suficiente para supervisar la operación.

### RNF-09 — Trazabilidad
Las acciones relevantes deberán poder asociarse con usuarios, eventos, flujos o políticas cuando la información esté disponible.

### RNF-10 — Mantenibilidad
La estructura deberá facilitar correcciones y ampliaciones.

### RNF-11 — Reproducibilidad
Las pruebas deberán poder repetirse bajo condiciones controladas.

### RNF-12 — Verificabilidad
Los requisitos críticos deberán poder comprobarse mediante métricas objetivas.

---
#
# 4. Requisitos arquitectónicos

### RA-01 — Arquitectura integral
La arquitectura deberá representar la interacción de R1–R5.

### RA-02 — Plano de control
Deberá identificarse el controlador SDN y sus responsabilidades.

### RA-03 — Plano de datos
Deberán identificarse los dispositivos que ejecutan las decisiones.

### RA-04 — Aplicaciones de seguridad
Deberán identificarse los módulos de políticas, detección, mitigación, monitoreo y administración.

### RA-05 — Flujo de información
Deberá especificarse qué información intercambia cada componente relevante.

### RA-06 — Flujo de decisión
Deberá poder trazarse:

**evento → detección → evaluación → decisión → política → aplicación → resultado.**

### RA-07 — Fallos
Deberán identificarse puntos de fallo y sus efectos.

### RA-08 — Escalabilidad
Deberá evaluarse el comportamiento ante aumento de usuarios y tráfico.

### RA-09 — Protección del plano de control
El acceso al controlador y sus interfaces administrativas deberá estar restringido.

# Restricciones

**Proyecto:** Solución de seguridad para una red de campus académico
**Curso:** TEL354 — Redes Definidas por Software
**Fase:** B — Drivers
**Origen:** separado de [`01_Requisitos_y_Restricciones_SDN_v0.1.md`](01_Requisitos_y_Restricciones_SDN_v0.1.md)

---

Una restricción es una condición impuesta al proyecto que la arquitectura no puede decidir: debe cumplirla. A diferencia de un requerimiento, no admite alternativa de diseño, y por eso se evalúa como criterio de descarte de alternativas.

---

## 1. Alcance y entregables

### RP-01 — Requerimientos implementados

**Restricción:** el proyecto exige implementar tres de los cinco requerimientos. La calidad de esos tres tiene prioridad sobre funcionalidad adicional.

**Implicación:** la arquitectura debe cubrir R1–R5 de forma integral, pero el diseño detallado, la implementación y la evaluación se concentran en los tres requerimientos asignados. El criterio de alcance se establece en [`../A-Modelo_de_dominio/00_Proyecto_SDN.md`](../A-Modelo_de_dominio/00_Proyecto_SDN.md).

### RP-07 — Complejidad

**Restricción:** no deberán incorporarse tecnologías cuya complejidad no pueda justificarse, implementarse y evaluarse dentro del alcance.

**Implicación:** cada componente tecnológico debe responder a un requerimiento o atributo de calidad identificado; lo que no pueda justificarse ni evaluarse queda fuera.

---

## 2. Arquitectura y hardware

### RP-02 — Paradigma SDN

**Restricción:** la solución deberá ser coherente con el paradigma SDN y con la separación entre plano de control y plano de datos.

**Implicación:** las decisiones de seguridad deben expresarse como políticas aplicables desde el plano de control, no como configuración manual dispositivo por dispositivo.

### RP-11 — Hardware del laboratorio

**Restricción:** la solución deberá ejecutarse sobre los switches disponibles en el laboratorio del curso, de hardware **Pica8** con **PicOS**, y sobre las capacidades OpenFlow que ese sistema expone.

**Implicación:** el protocolo southbound es OpenFlow, y las capacidades del plano de datos (meters, groups, tipos de acción y tamaño de las tablas) quedan condicionadas a lo que PicOS soporte. Ningún mecanismo puede darse por disponible sin verificarlo contra el dispositivo: si una primitiva no está soportada, el diseño debe degradarla explícitamente (p. ej. rate limiting sin meters, por muestreo y reglas del controlador).

### RP-12 — Alcance de protocolo IPv4

**Restricción:** el flujo de operación de la solución considera exclusivamente IPv4. IPv6, Neighbor Discovery y sus protocolos asociados quedan fuera del alcance.

**Implicación:** los escenarios de inicialización se describen con ARP y DHCPv4; no se modela tráfico de control IPv6.

### RP-13 — Confianza física como condición de acceso base

**Restricción:** el acceso físico controlado al campus se considera condición de confianza inicial suficiente para la obtención del perfil mínimo de red (perfil BASE), sin autenticación digital.

**Implicación:** la seguridad física del campus forma parte del perímetro de seguridad. La autenticación digital se reserva para salir del perfil mínimo (el login de la comunidad o de un operador) y para las elevaciones temporales; la presencia física jamás justifica privilegios elevados.

### RP-09 — Coherencia tecnológica

**Restricción:** cada tecnología deberá responder a una necesidad concreta y tener una responsabilidad definida.

**Implicación:** no se admiten tecnologías solapadas ni componentes sin responsable claro dentro de la arquitectura.

---

## 3. Tiempo y recursos

### RP-03 — Tiempo

**Restricción:** el diseño e implementación deberán ajustarse al cronograma del curso.

**Implicación:** la priorización es la herramienta de control del alcance; no hay holgura para exploración tecnológica abierta.

### RP-04 — Recursos

**Restricción:** la solución deberá utilizar los recursos computacionales disponibles.

**Implicación:** el diseño se acota al laboratorio disponible; la escalabilidad se demuestra por diseño y medición, no por despliegue a escala real.

---

## 4. Entorno y ejecución de pruebas

### RP-05 — Entorno

**Restricción:** las validaciones deberán ejecutarse en un entorno de laboratorio o simulación controlado y representativo.

**Implicación:** no es necesario reproducir la escala real del campus, pero sí los escenarios y las métricas definidos.

### RP-06 — Seguridad de las pruebas

**Restricción:** los ataques simulados deberán ejecutarse únicamente sobre infraestructura controlada por el proyecto.

### RP-08 — Aislamiento

**Restricción:** las pruebas y los mecanismos de mitigación no deberán afectar sistemas ajenos al entorno del proyecto.

**Implicación:** RP-06 y RP-08 delimitan el alcance legítimo de los escenarios de ataque; ninguna prueba puede salir del entorno controlado por el proyecto.

---

## 5. Verificación

### RP-10 — Verificabilidad

**Restricción:** toda funcionalidad crítica deberá contar con un mecanismo objetivo de validación.

**Implicación:** un requisito sin métrica ni prueba asociada no puede considerarse satisfecho.

# Priorización de drivers

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** B — Drivers
**Estado:** Borrador formal para revisión

---

Un **driver arquitectónico** es un requisito que condiciona decisiones de arquitectura: obliga a elegir entre alternativas estructurales y no puede satisfacerse con una decisión local. Este documento identifica los drivers del proyecto, qué decisión abre cada uno y en qué orden deben resolverse.

---

## 1. Criterio de priorización

Los drivers se ordenan aplicando cuatro criterios, en este orden:

1. **Obligatoriedad** — lo que el proyecto exige implementar (RP-01) no es negociable.
2. **Impacto arquitectónico** — cuántas decisiones estructurales dependen del driver y cuánto cuesta cambiarlo después.
3. **Riesgo** — qué ocurre si el driver no se resuelve.
4. **Verificabilidad** — si permite o no producir las métricas que el curso exige (RP-10).

**Asignación del curso:** R1 y R2 son obligatorios para todos los grupos; R4 es el requerimiento adicional asignado a este grupo. Sobre esos tres se concentra la implementación. R3 y R5 deben quedar cubiertos por la arquitectura, pero no se implementan por completo.

---

## 2. Catálogo de drivers

| ID | Driver | Origen | Decisión arquitectónica que condiciona |
|---|---|---|---|
| D-01 | Control de acceso por dispositivo, perfil y contexto | R1 | Modelo de perfiles de acceso, política contextual (identidad + atributos + contexto + vigencia), registro de dispositivos privilegiados, y punto de la red donde se aplica la decisión. |
| D-02 | Protección diferenciada de recursos | R2 | Clasificación de recursos, segmentación y asociación recurso ↔ política. |
| D-03 | Detección de ataques encubiertos internos | R3 | Ubicación y tipo de sensores, qué se observa y con qué analítica. |
| D-04 | Mitigación de DDoS y brute-force | R4 | Cadena completa de detección → incidente → política → controlador → plano de datos; mecanismos de contención (meters para rate limiting, bloqueo, aislamiento), línea base y umbrales, y recuperación con timeouts. |
| D-05 | Seguridad perimetral | R5 | Control del borde, inspección del tráfico externo y determinación de indicadores maliciosos. |
| D-06 | Traducción de decisión a regla SDN | RT-03, RT-04, RT-05, R2.10 | Arquitectura northbound y southbound: cómo una decisión de seguridad se convierte en reglas sobre los dispositivos, con las primitivas OpenFlow disponibles en PicOS (flows, meters, groups, counters). |
| D-07 | Respuesta automatizada y reversible | RT-08, RT-10, PS-07 | Bucle detección → decisión → aplicación → reversión, y dónde reside el estado temporal. |
| D-08 | Trazabilidad y auditoría | R1.9, R2.9, RNF-09, RT-07 | Modelo de eventos y registros: qué se registra, con qué identificadores y dónde se persiste. |
| D-09 | Disponibilidad del servicio legítimo | RNF-02, R4.8 | Cómo se mitiga sin cortar el tráfico legítimo y con qué tolerancia a fallo del plano de control. |
| D-10 | Latencia de las decisiones críticas | RNF-04 | Dónde se decide (controlador, dispositivo o ambos) y qué presupuesto de latencia se admite. |
| D-11 | Escalabilidad | RNF-05, R1.10, RA-08 | Límites de usuarios, sesiones y reglas; capacidad del plano de control y de las tablas de los dispositivos. |
| D-12 | Modularidad y separación de responsabilidades | RT-02, RNF-07 | Descomposición en componentes y definición de sus interfaces: qué se separa y por qué. |
| D-13 | Administración y observabilidad | RT-06, RT-09, ADM-01–05 | Interfaz de administración e información mínima para operar, supervisar y auditar. |
| D-14 | Verificabilidad y comparación de alternativas | RNF-12, RP-10, PT-07 | Qué métricas se instrumentan y cómo se comparan las alternativas de diseño. |

---

## 3. Priorización

### P0 — Obligatorio: se implementa

| Driver | Por qué |
|---|---|
| **D-01** Control de acceso por dispositivo, perfil y contexto | R1 es obligatorio para todos los grupos; su modelo (perfiles, registro de dispositivos privilegiados, elevación temporal) condiciona el resto de la arquitectura. |
| **D-02** Protección de recursos | R2 es obligatorio para todos los grupos. |
| **D-04** Mitigación de DDoS y brute-force | R4 es el requerimiento asignado a este grupo; es el caso de uso que demuestra la cadena completa de extremo a extremo. |
| **D-06** Traducción de decisión a regla SDN | Habilitante: sin él, ninguno de los tres requerimientos puede aplicarse sobre la red ni satisfacer RP-02. |
| **D-07** Respuesta automatizada y reversible | R4 exige mitigar y recuperar; sin reversión, la mitigación bloquea tráfico legítimo. |
| **D-08** Trazabilidad mínima | R1.9 y R2.9 pertenecen a requerimientos obligatorios: hay que registrar autenticación, autorización y accesos a recursos privilegiados. |
| **D-09** Disponibilidad del servicio legítimo | R4.8 es parte del requerimiento asignado. |
| **D-14** Verificabilidad y métricas | Sin métricas no hay criterios de éxito ni comparación de alternativas, que el curso exige. |

### P1 — Alta prioridad: se diseña por completo, se implementa de forma parcial

| Driver | Por qué |
|---|---|
| **D-03** Detección de ataques internos | R3 no está asignado, pero sus escenarios (scanning, spoofing) deben ser demostrables. |
| **D-05** Seguridad perimetral | R5 no está asignado: se diseña la frontera y se demuestra el bloqueo si el entorno lo permite. |
| **D-10** Latencia de las decisiones | Se mide sobre los tres requerimientos implementados; se optimiza si los resultados lo exigen. |
| **D-11** Escalabilidad | Se evalúa con carga creciente; el resultado alimenta el análisis de riesgo del controlador. |
| **D-12** Modularidad | Se materializa en la descomposición funcional (Fase D) y se comprueba en la validación del HLD (Fase E). |
| **D-13** Administración y observabilidad | Consola mínima para consultar políticas, eventos y registros. |

### P2 — Diferencial

- Umbrales dinámicos y detección adaptativa (extiende D-03 y D-04).
- Automatización de la respuesta sin intervención del Especialista de TI (extiende D-07).
- Comparación sistemática de alternativas de mitigación con resultados cuantitativos (extiende D-14).
- Implementación parcial de R3 y R5 más allá del escenario mínimo demostrable.

Los entregables del proyecto se derivan de estos niveles; esta priorización reemplaza la lista de entregables P0/P1/P2 que figuraba en el documento de requisitos.

---

## 4. Decisiones arquitectónicas que cada driver obliga a tomar

| Driver | Decisiones pendientes que activa |
|---|---|
| D-01 | perfiles de acceso; política contextual; registro de dispositivos privilegiados; portal cautivo y AAA |
| D-02 | segmentación; ubicación de los componentes de seguridad |
| D-03 | mecanismo de monitoreo; algoritmo o método de detección |
| D-04 | umbrales estáticos o dinámicos; meters nativos de PicOS o degradación por controlador; bloqueo; algoritmo de detección |
| D-05 | IDS, IPS o ambos; determinación de indicadores maliciosos |
| D-06 | controlador SDN; protocolo southbound (OpenFlow sobre PicOS, RP-11); diseño de la API northbound; virtualización o simulación |
| D-07 | estrategia de recuperación |
| D-08 | almacenamiento de logs; visualización |
| D-09 | estrategia de recuperación; tolerancia a fallo del plano de control |
| D-11 | virtualización o simulación; capacidad del entorno de pruebas |
| D-13 | visualización; almacenamiento de logs |

D-10 y D-14 no activan decisiones de esa lista: fijan criterios de diseño (presupuesto de latencia y conjunto de métricas) que las demás decisiones deben respetar.

---

## 5. Riesgos que la priorización controla

| Riesgo | Driver que lo atiende |
|---|---|
| Complejidad excesiva | La propia priorización: P0 antes que P1 y P2 |
| Bloqueo de usuarios legítimos | D-07 (reversión) y D-09 (disponibilidad) |
| Sobrecarga del controlador | D-11 y D-10, con medición en el entorno del prototipo |
| Exceso de reglas SDN | D-11, contra la capacidad del dispositivo |
| Falsos positivos | D-14, mediante tasa de detección y de falsos positivos |
| Punto único de fallo | D-09 |
| Falta de métricas | D-14, instrumentado antes de implementar |
| Falta de tiempo | La priorización P0/P1/P2 |

---

## 6. Cuestiones abiertas

- **Alcance de R3 y R5.** Definir qué se considera suficiente: ¿diseño documentado, o diseño más un escenario demostrable en el prototipo?
- **Umbrales y línea base.** Dependen de mediciones previas en el entorno del prototipo, que aún no existe.
- **Presupuesto de latencia.** RNF-04 no fija un valor; hay que establecer el límite que se considerará aceptable.
- **Capacidad de reglas.** Cuántas reglas simultáneas admite el dispositivo elegido es asunto de la Fase C y de la Fase F.

----------------------------------------------------------------------------

# 11. Decisiones arquitectónicas pendientes

En esta primera versión no se consideran definitivas las siguientes decisiones:

- controlador SDN;
- protocolo southbound;
- diseño de northbound API;
- mecanismo de monitoreo;
- IDS, IPS o ambos;
- algoritmo/método de detección;
- umbrales estáticos o dinámicos;
- rate limiting;
- honeypot
- bloqueo;
- segmentación;
- ubicación de componentes de seguridad;
- almacenamiento de logs;
- visualización;
- virtualización/simulación;
- estrategia de recuperación.

Cada decisión deberá justificarse por requisitos, restricciones, complejidad y resultados cuantitativos.

---
#
# 12. Principios arquitectónicos

La solución deberá procurar:

1. mínimo privilegio;
2. separación de responsabilidades;
3. políticas centralizadas;
4. aplicación programable;
5. monitoreo continuo;
6. respuesta automatizada cuando corresponda;
7. trazabilidad;
8. modularidad;
9. escalabilidad;
10. reversibilidad;
11. verificabilidad;
12. integración de R1–R5.

---
#
# 13. Criterios de aceptación de la arquitectura

La arquitectura se considerará adecuada cuando:

- represente los cinco requerimientos;
- identifique actores y componentes;
- defina responsabilidades;
- muestre flujos de información y decisión;
- explique cómo las políticas llegan a la infraestructura SDN;
- contemple operación normal y escenarios de ataque;
- defina mecanismos de mitigación;
- considere restricciones;
- establezca criterios de éxito;
- permita derivar HLD y LLSD;
- sea viable dentro del alcance del curso.

Puede que falte solo momentáneamente. Seguramente el documento en otras partes ataca o resuelve estas.

----------------------------------------------------------------------------

# Contexto

# Límite del sistema

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** C — Contexto
**Estado:** Borrador formal para revisión

---

## 1. Qué es el sistema

El sistema es la **plataforma SDN de seguridad**: el conjunto de mecanismos que controla el acceso a la red, autoriza el uso de recursos, detecta y mitiga amenazas, y administra y registra esas decisiones, junto con la infraestructura SDN sobre la que se aplican.

El sistema no es la red del campus. Es la capa que decide qué ocurre en ella.

---

## 2. Criterio de delimitación

Un elemento pertenece al sistema si el proyecto lo despliega, lo configura y responde por él. Si existe con independencia del proyecto y el sistema solo intercambia información con él, queda fuera.

De ese criterio resultan cuatro categorías:

| Categoría | Definición |
|---|---|
| **Parte del sistema** | El proyecto lo despliega y lo opera; las decisiones de seguridad se aplican sobre él. |
| **Activo protegido** | Está fuera del sistema, pero es el objeto que el sistema protege. |
| **Sistema externo** | Existe con independencia del proyecto; el sistema se integra con él mediante una interfaz. |
| **Fuente de amenaza** | No coopera con el sistema: origina el tráfico o el comportamiento que debe detectarse y contenerse. |

---

## 3. Elementos en el límite

| Elemento | Categoría | Justificación |
|---|---|---|
| Controlador SDN | Parte del sistema | Es el plano de control; el proyecto lo despliega y lo configura. |
| Aplicaciones de seguridad (autorización, detección, mitigación, administración) | Parte del sistema | Implementan las decisiones que definen R1–R5. |
| Cadena de detección (Monitor, Detection Engine, Incident Manager, Policy Engine) | Parte del sistema | La observación y la decisión de respuesta son propias del proyecto: se despliegan en el prototipo y se conectan al controlador. |
| Dispositivos SDN administrados | Parte del sistema | Ejecutan las reglas que el plano de control instala. |
| Consola de administración | Parte del sistema | Interfaz de operación de la plataforma. |
| Portal cautivo | Parte del sistema | Punto de autenticación de la red: la comunidad (perfil ACADÉMICO) y los operadores. |
| AAA / RADIUS | Parte del sistema | El servidor AAA se despliega en el prototipo; autentica y autoriza a las poblaciones (comunidad contra el IdP; operadores contra el repositorio propio) y registra sus acciones (accounting). |
| Registro de dispositivos privilegiados | Parte del sistema | Base de datos propia con la información de los dispositivos de operadores; sostiene la regla del "no match → perfil BASE" y la auditoría de altas. |
| Registros y almacenamiento de logs | Parte del sistema | Sostienen la trazabilidad exigida por R1.9, R2.9 y RNF-09. |
| Sistema de identidad institucional (IdP/LDAP) | Sistema externo | El AAA lo consulta para verificar las credenciales de la comunidad universitaria; el proyecto no lo administra. |
| Firewall perimetral | Sistema externo o parte del sistema | **Por definir**: si el proyecto lo despliega, es parte del sistema; si ya existe, es un punto de integración (R5 no está asignado a este grupo). |
| Servidores y servicios institucionales | Activo protegido | El sistema no los administra: los protege. |
| Dispositivos de usuario final | Activo protegido | Están fuera del sistema, pero son el origen del tráfico que se controla y el punto donde puede aplicarse un aislamiento. Los académicos no se registran; los de operadores figuran en el registro de dispositivos privilegiados. |
| Internet y redes externas | Sistema externo y fuente de amenaza | Es a la vez origen de tráfico legítimo y de tráfico malicioso (R5). |
| Atacante externo, atacante interno y nodo comprometido | Fuente de amenaza | No cooperan con el sistema; su comportamiento es el objeto de R3–R5. |

---

## 4. Consecuencias de esta delimitación

- **El perfil BASE no depende de la identidad.** Su concesión se resuelve íntegramente dentro del sistema, por presencia física y por la regla del registro (no match → BASE). El IdP institucional solo se consulta cuando la comunidad se autentica; los operadores se verifican contra el repositorio propio del sistema.
- **R1 se satisface en el puerto de acceso.** La frontera entre *quién es* y *qué puede hacer* se traza en el switch de ingreso: el perfil por defecto niega todo lo que no esté explícitamente permitido, y las elevaciones instalan reglas adicionales, temporales y auditables.
- **La detección es propia.** La cadena Monitor → Detection → Incident → Policy es parte del sistema y su salida se traduce a reglas SDN; no se consume un IDS/IPS institucional. Si el proyecto decide integrar un IPS externo, sería un punto de integración adicional, no un reemplazo de la cadena.
- **R5 se satisface en el borde.** Si el firewall es externo, la solución debe integrarse con él, no sustituirlo.
- **Los activos protegidos quedan fuera del sistema pero dentro de su alcance de protección.** Al protegerlos, el sistema aplica políticas sobre la red que los conecta, no sobre los servidores mismos.
- **Un atacante no es un elemento del sistema ni un usuario de él.** Es una fuente de tráfico que el sistema observa, clasifica y contiene.

---

## 5. Cuestiones abiertas

- Ubicación del firewall perimetral: propio o institucional. Determina si es un componente del sistema o una interfaz con un sistema externo.
- Si el IdP institucional existe en el entorno del prototipo o debe simularse (ver [`04_alcance_de_la_infraestructura.md`](04_alcance_de_la_infraestructura.md)).
- Si la consola de administración y el almacenamiento de registros forman parte del prototipo o se representan de forma simplificada.

# Diagrama de contexto

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** C — Contexto
**Estado:** Borrador formal para revisión

---

## 1. Propósito y nivel

El diagrama representa el sistema como una caja negra y muestra **quién y qué intercambia información con él**. No describe componentes internos: la descomposición funcional y la arquitectura lógica corresponden a la Fase D.

Responde una sola pregunta: ¿dónde empieza y termina la solución? La respuesta está en [`01_limite_del_sistema.md`](01_limite_del_sistema.md).

---

## 2. Diagrama

```text
        ┌───────────────────────────┐        ┌────────────────────────────┐
        │  USUARIOS                 │        │  SISTEMAS EXTERNOS         │
        │  Usuario académico        │        │  Internet / red externa    │
        │  (BASE → ACADÉMICO)       │        │  Identidad (IdP/LDAP)      │
        ├───────────────────────────┤        │  Inteligencia de amenazas  │
        │  OPERADORES               │        └──────────────┬─────────────┘
        │  Especialista de TI       │                       │
        │  Administrador de Red     │                       │
        │  Superadministrador       │                       │
        └─────────────┬─────────────┘                       │
                      │                                     │
       acceso y uso de servicios          tráfico externo, verificación
       administración y supervisión       de identidad, indicadores
                      │                                     │
                      ▼                                     ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                                                             │
        │              PLATAFORMA SDN DE SEGURIDAD                    │
        │                                                             │
        │  perfiles de acceso · portal cautivo · AAA · detección      │
        │  mitigación · administración de políticas · auditoría       │
        │                                                             │
        └───────────────────────────────┬─────────────────────────────┘
                                        │
                        controla el acceso y protege
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │  ACTIVOS PROTEGIDOS           │
                        │  servidores y servicios       │
                        │  académicos y administrativos │
                        └───────────────────────────────┘

  ── FUENTES DE AMENAZA ────────────────────────────────────────────────
     Atacante externo   → actúa desde Internet
     Atacante interno   → opera con acceso legítimo a la red
     Nodo comprometido  → dispositivo legítimo bajo control ajeno
```

---

## 3. Interacciones

| Origen | Destino | Qué fluye | Propósito |
|---|---|---|---|
| Usuario académico | Plataforma | Solicitud de configuración (DHCP) y de uso de servicios | Conectividad base y autorización por defecto (R1, R2) |
| Usuario académico | Plataforma | Login en el portal (contra el IdP institucional) | Obtener el perfil ACADÉMICO: servicios académicos e Internet (R1) |
| Plataforma | Usuario académico | Perfil BASE y conectividad al servicio autorizado | Aplicar la política vigente |
| Usuario académico | Plataforma | Solicitud de elevación temporal | Elevación aprobada por el Administrador de Red, con TTL |
| Especialista de TI | Plataforma | Login (portal cautivo); consultas de tráfico y de eventos; acciones de mitigación autorizadas | Supervisión y respuesta ante incidentes (R3, R4) |
| Administrador de Red | Plataforma | Login (portal cautivo); cambios de políticas, de reglas y de segmentación; aprobación de elevaciones; altas en el registro de dispositivos | Administración operativa de la red |
| Superadministrador | Plataforma | Login (portal cautivo o acceso remoto); gestión de operadores, de roles y de configuración global | Control de la plataforma |
| Plataforma | Operadores | Alertas, eventos, estado de red y registros | Operación y auditoría |
| Internet | Plataforma | Tráfico entrante | Servicio legítimo e inspección perimetral (R5) |
| Plataforma | Internet | Tráfico saliente autorizado | Conectividad externa |
| Identidad institucional (IdP/LDAP) | Plataforma (AAA) | Verificación de credenciales y atributos de la comunidad universitaria | Autenticación de la comunidad (R1) |
| Inteligencia de amenazas | Plataforma | Indicadores de IP, URL u otros | Determinar qué es malicioso (R5.6) |
| Plataforma | Activos protegidos | Tráfico permitido; bloqueo del no autorizado | Protección de recursos (R2) |
| Activos protegidos | Plataforma | Registros y eventos de servicio | Detección y trazabilidad |
| Atacante externo | Plataforma | Tráfico malicioso desde redes externas | Objeto de R5 y, si atraviesa el perímetro, de R3 y R4 |
| Atacante interno, nodo comprometido | Plataforma | Tráfico anómalo originado dentro de la red | Objeto de R3 y R4 |

---

## 4. Qué no muestra el diagrama

- Los componentes internos de la plataforma y sus interfaces (Fase D).
- La topología física y la segmentación (Fase H; ver [`04_alcance_de_la_infraestructura.md`](04_alcance_de_la_infraestructura.md)).
- Las decisiones tecnológicas: controlador, IDS/IPS, broker o persistencia (Fase F).

---

## 5. Cuestiones abiertas

- Si la inteligencia de amenazas proviene de un servicio externo, de listas propias o de ambos (R5.6).

# Sistemas externos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** C — Contexto
**Estado:** Borrador formal para revisión

---

Un sistema externo existe con independencia del proyecto y el sistema se integra con él mediante una interfaz. No todos son dependencias: algunos son también origen de amenazas, y otros son aquello que el sistema protege.

---

## 1. Registro

| ID | Elemento externo | Categoría | Criticidad si falla |
|---|---|---|---|
| SE-01 | Internet y redes externas | Sistema externo y fuente de amenaza | Alta: sin él no hay servicio externo ni tráfico que inspeccionar |
| SE-02 | Sistema de identidad institucional (IdP/LDAP) | Sistema externo | Alta: sin él no hay autenticación de la comunidad universitaria (R1) |
| SE-03 | Fuente de inteligencia de amenazas | Sistema externo | Media: degrada R5.6, no detiene la operación |
| SE-04 | Servicio de nombres (DNS) | Sistema externo | Alta: su manipulación es un vector de ataque (R3.3) |
| SE-05 | Sincronización de tiempo (NTP) | Sistema externo | Media: afecta la correlación de eventos y la auditoría |
| SE-06 | Servidores y servicios institucionales | Activo protegido | Alta: son el objeto de la protección (R2) |
| SE-07 | Dispositivos de usuario final | Activo protegido | Media: su compromiso los convierte en origen de amenaza |

---

## 2. Fichas

### SE-01 — Internet y redes externas

- **Qué se intercambia:** tráfico entrante hacia los servicios publicados y tráfico saliente autorizado.
- **Interfaz esperada:** el borde perimetral de la red (R5.1).
- **Condición de amenaza:** es el origen del atacante externo y de tráfico malicioso dirigido al perímetro.
- **En el prototipo:** se representa mediante un segmento externo controlado; el tráfico ofensivo se genera dentro del entorno (RP-06, RP-08).

### SE-02 — Sistema de identidad institucional (IdP/LDAP)

- **Qué se intercambia:** verificación de credenciales y atributos de la **comunidad universitaria** (alumnos y profesores) cuando inician sesión en el portal.
- **Interfaz esperada:** consulta desde el servidor AAA del sistema (portal cautivo).
- **Qué no es:** no participa en la conexión ni en el perfil BASE — se concede por presencia física (RP-13) sin consultar ningún sistema de identidad. Tampoco autentica a los operadores: su reino es el repositorio propio de la plataforma.
- **Condición de amenaza:** no ataca, pero es objetivo: si se compromete, se compromete la autenticación de la comunidad que depende de él.
- **En el prototipo:** se simula o se integra, según lo que exista en el entorno.
- **Nota:** determina el límite del sistema en la autenticación de R1 (ver [`01_limite_del_sistema.md`](01_limite_del_sistema.md)).

### SE-03 — Fuente de inteligencia de amenazas

- **Qué se intercambia:** indicadores (direcciones IP, URLs u otros) considerados maliciosos.
- **Interfaz esperada:** consulta o actualización periódica de listas (R5.6).
- **Condición de amenaza:** no; su corrupción produciría bloqueos erróneos o falsos negativos.
- **En el prototipo:** puede representarse con un conjunto de indicadores propio y controlado.

### SE-04 — Servicio de nombres (DNS)

- **Qué se intercambia:** resolución de nombres para el tráfico legítimo.
- **Interfaz esperada:** servicio de resolución de la red.
- **Condición de amenaza:** sí, indirectamente: la suplantación de respuestas es un caso de origen inconsistente (R3.3).
- **En el prototipo:** servicio de nombres del propio entorno.

### SE-05 — Sincronización de tiempo (NTP)

- **Qué se intercambia:** referencia temporal para los registros.
- **Interfaz esperada:** servicio de tiempo de la red.
- **Condición de amenaza:** no, pero su ausencia o manipulación deteriora la trazabilidad (RNF-09) y la investigación de incidentes (ADM-03).
- **En el prototipo:** servicio de tiempo del entorno virtual.

### SE-06 — Servidores y servicios institucionales

- **Qué se intercambia:** el tráfico autorizado que los alcanza y los registros que generan.
- **Condición de amenaza:** no; son el objeto de protección de R2 y el destino de los ataques de R3 y R4.
- **En el prototipo:** se representan mediante equivalentes controlados, no con los servicios reales de la institución.

### SE-07 — Dispositivos de usuario final

- **Qué se intercambia:** tráfico de los usuarios legítimos.
- **Condición de amenaza:** un dispositivo comprometido se convierte en nodo comprometido, y su tráfico pasa a ser objeto de R3 y R4 aunque el usuario conserve credenciales válidas.
- **En el prototipo:** hosts simulados que representan al usuario académico. Los dispositivos académicos **no se registran** en ningún catálogo: reciben perfil BASE por defecto; solo los dispositivos de operadores figuran en el registro de dispositivos privilegiados (parte del sistema).

---

## 3. Dependencias que el prototipo debe resolver

| Dependencia | Alternativa si no existe en el entorno |
|---|---|
| Identidad institucional (IdP/LDAP) | Directorio simulado con cuentas de la comunidad de prueba |
| Inteligencia de amenazas | Conjunto de indicadores propio, definido por el proyecto |
| Internet | Segmento externo controlado dentro del laboratorio |
| Servicios institucionales | Servidores equivalentes desplegados en el prototipo |
| DNS y NTP | Servicios del propio entorno de virtualización |

---

## 4. Cuestiones abiertas

- Si el firewall perimetral es un sistema externo institucional o un componente del propio sistema (ver [`01_limite_del_sistema.md`](01_limite_del_sistema.md)). La cadena de detección ya está resuelta: es parte del sistema.
- Si la inteligencia de amenazas se alimenta de un servicio real, de listas propias o de ambos.
- Si los dispositivos de usuario final se modelan como activos protegidos o solo como orígenes de tráfico sujetos a observación.

# Alcance de la infraestructura

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** C — Contexto
**Estado:** Borrador formal para revisión

---

## 1. Dos infraestructuras

- **Infraestructura de referencia** — la red de campus que la solución describe: qué poblaciones, segmentos y servicios existen.
- **Infraestructura del prototipo** — lo que el proyecto despliega y sobre lo que valida.

RP-05 exige un entorno controlado y representativo: la segunda debe representar a la primera en los aspectos que los escenarios y las métricas necesitan, sin reproducir su escala real (RP-04).

---

## 2. Infraestructura de referencia

| Elemento | Descripción | Relación con los requerimientos |
|---|---|---|
| Segmento de usuarios finales | Usuarios académicos conectados (BASE; ACADÉMICO tras el login) | Origen de R1 y del tráfico observado en R3 y R4 |
| Segmento de servidores | Servicios académicos y administrativos | Objeto de R2 |
| Segmento de administración | Consola, controlador y planos de gestión | Protegido según RA-09 |
| Segmento perimetral | Borde con redes externas | Punto de aplicación de R5 |
| Servicios institucionales | Académicos, administrativos y base de datos | Activos protegidos (ver [`03_sistemas_externos.md`](03_sistemas_externos.md)) |
| Dispositivos de usuario final | Equipos de usuarios académicos y de operadores | Origen del tráfico; candidatos a aislamiento |

La segmentación anterior es una propuesta de referencia. Su definición definitiva pertenece a la arquitectura lógica (Fase D) y a la topología (Fase H).

---

## 3. Infraestructura del prototipo

| Elemento | Se despliega o se simula | Nota |
|---|---|---|
| Controlador SDN | Se despliega | Decisión tecnológica pendiente (Fase F) |
| Switches SDN | Se despliegan (virtuales o físicos) | Hardware del laboratorio: **Pica8 con PicOS** (RP-11); deben soportar la instalación dinámica de reglas y las primitivas OpenFlow que el diseño exija (meters, groups, counters) |
| Canal de control | Se configura | Out-of-band (red de gestión); la variante in-band es un objetivo aspiracional (ver flujo §2.6) |
| Hosts de usuario | Se simulan | Representan al usuario académico; generan tráfico legítimo; no se registran en ningún catálogo |
| Servidores de servicio | Se simulan | Representan los activos protegidos |
| Portal cautivo y AAA/RADIUS | Se despliegan | Autenticación de la comunidad y de los operadores; el backend de identidad (IdP) se simula o se integra (SE-02) |
| Registro de dispositivos privilegiados | Se despliega | Base de datos propia: dispositivos de operadores y su auditoría |
| Cadena de detección (Monitor, Detection, Incident, Policy) | Se despliega | Lee counters del plano de datos y alimenta al controlador |
| Segmentación | Se configura | Necesaria para R2 y para separar poblaciones |
| Tráfico de ataque | Se genera de forma controlada | Solo dentro del entorno del proyecto (RP-06, RP-08) |
| Perímetro | Se representa | Alcance por definir (ver cuestiones abiertas) |

---

## 4. Dentro y fuera del alcance

**Dentro**

- lo necesario para implementar R1, R2 y R4, los tres requerimientos obligatorios, y para demostrar los escenarios de R3 y R5;
- la segmentación mínima que haga verificable R2;
- los escenarios de ataque controlados que las pruebas exijan.

**Fuera**

- la escala real del campus: número de usuarios, de dispositivos y de enlaces;
- hardware de red específico, cuando el entorno virtual permita validar lo mismo;
- alta disponibilidad real y redundancia física: se analizan por diseño, no se despliegan;
- servicios institucionales reales: se representan mediante equivalentes controlados.

---

## 5. Supuestos

- El entorno disponible admite virtualización de hosts, switches y controlador.
- Los switches del prototipo son Pica8/PicOS (RP-11) y soportan la instalación dinámica de reglas; las primitivas OpenFlow concretas (meters, groups, counters) se verifican contra el dispositivo antes de comprometer el diseño.
- El canal de control es out-of-band (RP-02); si el prototipo adopta la variante in-band, exige VLAN de gestión y priorización del tráfico de control.
- El prototipo opera solo con IPv4 (RP-12).
- La topología es rígida por diseño, pero el sistema tolera la aparición de dispositivos nuevos: todo dispositivo que no haga match con el registro de dispositivos privilegiados recibe perfil BASE (RP-13).
- Existe conectividad de laboratorio suficiente para generar tráfico de carga y de ataque sin salir del entorno.

---

## 6. Cuestiones abiertas

- Número de switches y de hosts del prototipo: depende de la capacidad disponible y de los escenarios que se quieran reproducir.
- Capacidad de las tablas de flujo de PicOS: condiciona cuántas reglas simultáneas admite la solución (riesgo de exceso de reglas SDN) y si meters/groups están disponibles.
- Representación del perímetro: firewall simulado, componente del propio entorno o solo reglas en el borde.
- Si habrá acceso a hardware físico o el prototipo será íntegramente virtual.
- Si el canal in-band se implementa en el prototipo y en qué fase: es más complejo (VLAN de gestión, priorización, prueba de supervivencia ante un ataque volumétrico), pero valorado por el profesor.
