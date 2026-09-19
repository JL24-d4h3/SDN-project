Sí. El problema de la propuesta actual es que **los roles están definidos principalmente por “quién es la persona”**, pero R1 y R2 exigen definirlos por **qué puede hacer ese actor sobre qué recurso, bajo qué condiciones**.

Para vuestro SDN, yo separaría conceptualmente **identidad, rol, permisos y nivel de privilegio**. Así los roles dejan de ser etiquetas ambiguas.

### 1. Primero: no mezclar “actor” con “rol”

En realidad tenéis dos categorías distintas:

**Actores humanos**

* Alumno
* Docente
* Administrador de Red
* Especialista de TI
* Superadministrador

**Actores no humanos**

* Nodo comprometido
* Atacante externo
* Dispositivo de red
* Controlador SDN
* Servicios/servidores

Un *atacante* no debería ser considerado un “rol autorizado” equivalente a Alumno o Docente. Es una **entidad cuyo comportamiento el sistema debe detectar y controlar**.

---

# 2. Una jerarquía de privilegios mucho más clara

Podríais definir cinco niveles:

| Nivel | Rol                      | Propósito                | Puede acceder a usuarios              | Puede acceder a recursos                     | Puede modificar red              |
| ----- | ------------------------ | ------------------------ | ------------------------------------- | -------------------------------------------- | -------------------------------- |
| 0     | **Alumno**               | Usuario final            | Solo sus propios recursos             | Públicos + académicos autorizados            | No                               |
| 1     | **Docente**              | Usuario académico        | Solo sus propios recursos             | Públicos + académicos + docentes             | No                               |
| 2     | **Especialista de TI**   | Seguridad/monitoreo      | Información necesaria para investigar | Recursos de monitoreo/seguridad              | Limitado                         |
| 3     | **Administrador de Red** | Administración operativa | Todos los necesarios para administrar | Todos los recursos de red según autorización | Sí                               |
| 4     | **Superadministrador**   | Control maestro          | Todos                                 | Todos                                        | Sí, sin restricciones operativas |

Pero hay una distinción importante: **no necesariamente conviene que el Superadministrador sea simplemente “un Administrador de Red con más permisos”**. Puede representar una *cuenta de control superior de la solución*.

---

# 3. ¿Qué debería poder hacer exactamente cada uno?

Aquí empieza a tener sentido R1.

## 🟢 Alumno — Nivel 0

Su función es **consumir servicios**, no administrar infraestructura.

### Puede

* Autenticarse en la red.
* Obtener acceso a la intranet general.
* Acceder a servicios públicos/institucionales.
* Acceder a determinados recursos académicos.
* Generar tráfico normal hacia servicios permitidos.
* Utilizar Internet, si vuestra arquitectura lo contempla.

### No puede

* Modificar políticas de red.
* Modificar ACL/firewall.
* Administrar switches.
* Modificar VLAN/segmentación.
* Acceder a la consola SDN.
* Acceder a servidores administrativos.
* Modificar configuraciones de seguridad.
* Administrar otros usuarios.
* Deshabilitar mecanismos de seguridad.

**Idea fundamental:**

> El alumno tiene permisos orientados exclusivamente al consumo de servicios.

---

# 4. 🟡 Docente — Nivel 1

Tiene prácticamente el mismo modelo de acceso que un alumno, pero con **mayor acceso a recursos académicos**.

### Puede

Todo lo del alumno, más:

* Acceder a servidores/servicios exclusivos para docentes.
* Acceder a sistemas académicos administrativos que correspondan a su función.
* Acceder a recursos compartidos docentes.
* Posiblemente acceder a determinados servicios internos que un alumno no puede utilizar.

### No puede

Todo lo que un alumno tampoco puede, además de:

* Administrar usuarios.
* Administrar políticas.
* Modificar infraestructura.
* Acceder a la consola administrativa.
* Acceder a información de seguridad restringida.

La diferencia entre alumno y docente **no debería ser “el docente tiene más privilegios porque sí”**.

Debe ser:

> **Mismo principio de mínimo privilegio, diferente conjunto de recursos autorizados.**

---

# 5. 🔵 Especialista de TI — Nivel 2

Aquí vuestra propuesta original tiene una ambigüedad importante.

Decís:

> “monitorea alertas de seguridad, revisa y libera falsos positivos, decide sobre incidentes.”

Eso ya no es simplemente monitoreo. Es un **rol de seguridad/operaciones SOC**.

Yo lo definiría como:

> **Responsable de supervisar el estado de seguridad de la red y responder a eventos de seguridad, sin poseer necesariamente control administrativo completo sobre la infraestructura.**

### Puede

* Consultar tráfico y métricas de red.
* Consultar eventos del IDS/IPS.
* Consultar alertas del sistema.
* Investigar IPs/dispositivos sospechosos.
* Consultar registros (*logs*).
* Marcar una alerta como falso positivo.
* Escalar un incidente.
* Solicitar/ejecutar determinadas acciones de mitigación.
* Aislar un nodo comprometido **si vuestra arquitectura lo permite**.
* Aplicar medidas de contención predefinidas.

### No debería poder

* Crear/modificar libremente toda la política de red.
* Crear administradores.
* Cambiar la arquitectura SDN.
* Modificar configuraciones críticas del controlador.
* Revocar arbitrariamente las credenciales de todos los administradores.
* Eliminar logs de seguridad.
* Desactivar IDS/IPS.

Esto genera una separación interesante:

**Especialista de TI = seguridad**

**Administrador de Red = infraestructura**

---

# 6. 🔴 Administrador de Red — Nivel 3

Este es el verdadero operador de la infraestructura.

Su función es:

> **Configurar, mantener y administrar la red y sus políticas de acceso.**

### Puede

* Crear/modificar/eliminar políticas de acceso.
* Gestionar ACL.
* Administrar segmentación/VLAN.
* Administrar switches y dispositivos SDN.
* Gestionar reglas de forwarding.
* Configurar políticas de QoS.
* Administrar usuarios y asignación de roles.
* Habilitar/deshabilitar determinados servicios.
* Gestionar rutas.
* Configurar mecanismos de seguridad de red.
* Consultar logs operativos.
* Gestionar recursos de red.
* Aplicar medidas de mitigación autorizadas.

### Pero aquí pondría una restricción importante

El administrador **no debería poder hacer absolutamente todo**.

Por ejemplo:

> Administrador de Red → puede crear una política.

pero:

> Superadministrador → puede modificar o revocar la política del Administrador de Red.

Y posiblemente:

> Especialista de TI → puede detectar que la política está provocando un incidente, pero no modificarla directamente.

Eso crea **separación de funciones** (*Separation of Duties*).

---

# 7. ⚫ Superadministrador — Nivel 4

Aquí sí introduciría vuestro concepto, pero con cuidado.

No lo definiría simplemente como:

> “los creadores de la solución”.

Eso es una característica de vuestro proyecto, no necesariamente una característica del modelo de seguridad.

Lo definiría técnicamente como:

> **Entidad con privilegios máximos sobre el plano de administración de la solución SDN, incluyendo la gestión de administradores, políticas globales y mecanismos de seguridad.**

### Puede

Prácticamente todo:

* Crear/eliminar administradores.
* Crear/modificar/eliminar roles.
* Modificar permisos.
* Revocar privilegios.
* Configurar políticas globales.
* Modificar políticas de seguridad.
* Administrar el controlador SDN.
* Gestionar IDS/IPS.
* Gestionar mecanismos de mitigación.
* Administrar dispositivos de red.
* Consultar todos los logs.
* Auditar acciones de administradores.
* Recuperar configuraciones.
* Restablecer políticas.
* Bloquear/desbloquear usuarios.
* Aislar segmentos completos.
* Modificar parámetros críticos del sistema.

### Y algo especialmente importante:

**Puede administrar a los Administradores de Red.**

Por ejemplo:

```text
Superadministrador
       │
       ├── administra → Administrador de Red
       │                    │
       │                    ├── administra → infraestructura
       │                    └── administra → usuarios
       │
       └── administra → Especialista de TI
                            │
                            └── gestiona → incidentes
```

---

# 8. Pero hay algo todavía más importante: el Superadministrador no debería ser un “usuario normal”

Para vuestro proyecto, yo incluso consideraría distinguir:

**Usuario de la red**

vs.

**Usuario administrativo de la plataforma**

Porque sería extraño que el “Superadministrador” navegue por la intranet como un usuario normal.

Podéis modelarlo así:

```text
                 SISTEMA SDN
                     │
          ┌──────────┴──────────┐
          │                     │
      PLANO DE DATOS        PLANO DE CONTROL
          │                     │
    Usuarios finales       Administradores
          │                     │
     ┌────┴────┐          ┌─────┴─────┐
     │         │          │           │
  Alumno    Docente      TI      Admin. Red
                                  │
                                  │
                           Superadministrador
```

Esto hace que vuestra arquitectura sea conceptualmente mucho más limpia.

---

# 9. Y entonces aparece una cuestión fundamental: ¿qué significa realmente “acceder a la red”?

R1 dice:

> “Controlar el acceso a la RED de los usuarios válidos, acorde con su rol.”

No debería significar simplemente:

> Alumno → entra
> Docente → entra

Eso sería demasiado superficial para un proyecto SDN.

Podríais tener:

```text
                         RED
                          │
             ┌────────────┴────────────┐
             │                         │
       Intranet general          Recursos restringidos
             │                         │
      ┌──────┴──────┐            ┌─────┴─────┐
      │             │            │           │
   Alumno        Docente       Docente      TI/Admin
```

El **rol determina qué puede alcanzar el usuario**, no solamente si puede conectarse.

Por ejemplo:

| Recurso                    | Alumno | Docente |         TI |     Admin | Superadmin |
| -------------------------- | -----: | ------: | ---------: | --------: | ---------: |
| Intranet general           |      ✓ |       ✓ |          ✓ |         ✓ |          ✓ |
| Servicios académicos       |      ✓ |       ✓ |          ✓ |         ✓ |          ✓ |
| Recursos docentes          |      ✗ |       ✓ |          ✓ |         ✓ |          ✓ |
| Consola de monitoreo       |      ✗ |       ✗ |          ✓ |         ✓ |          ✓ |
| Configuración SDN          |      ✗ |       ✗ | ✗/limitado |         ✓ |          ✓ |
| Políticas de seguridad     |      ✗ |       ✗ |  consultar | modificar |  modificar |
| Gestión de administradores |      ✗ |       ✗ |          ✗ |         ✗ |          ✓ |
| Configuración global       |      ✗ |       ✗ |          ✗ |  limitado |          ✓ |

**Esto es justamente lo que os falta definir antes de cerrar los casos de uso.**

---

# 10. Incluso podéis separar RBAC de las restricciones de seguridad

No todo debería depender exclusivamente del rol.

Por ejemplo:

```text
PERMISO EFECTIVO
      =
ROL
+
RECURSO
+
ACCIÓN
+
CONTEXTO
+
ESTADO DE SEGURIDAD
```

Un docente normalmente podría acceder al servidor académico:

```text
Docente + servidor académico + HTTPS → PERMITIR
```

Pero si su dispositivo está comprometido:

```text
Docente + servidor académico + tráfico anómalo
→ AISLAR/BLOQUEAR
```

Y un alumno:

```text
Alumno + servidor administrativo
→ DENEGAR
```

Aunque tenga credenciales válidas.

Esto es especialmente importante para **R3, R4 y R5**, porque significa que:

> **Autenticación ≠ autorización ≠ confianza permanente.**

Un usuario legítimo puede convertirse en un origen de tráfico malicioso.

---

# 11. Yo dejaría vuestros roles preliminares así

Para el documento formal:

| Rol                      | Responsabilidad principal                                                                                       |
| ------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Alumno**               | Acceso mínimo a servicios generales y académicos autorizados.                                                   |
| **Docente**              | Acceso a servicios generales y recursos académicos/docentes adicionales.                                        |
| **Especialista de TI**   | Monitoreo, análisis y respuesta ante eventos e incidentes de seguridad.                                         |
| **Administrador de Red** | Administración operativa de usuarios, políticas, dispositivos y configuración de red.                           |
| **Superadministrador**   | Administración integral de la plataforma SDN, incluyendo roles, permisos, políticas globales y administradores. |

Y fuera de esos roles:

| Entidad                 | Naturaleza                                                                             |
| ----------------------- | -------------------------------------------------------------------------------------- |
| **Atacante externo**    | Actor no autorizado que intenta acceder o generar tráfico malicioso.                   |
| **Nodo comprometido**   | Dispositivo legítimo cuyo comportamiento ha sido comprometido o considerado malicioso. |
| **Controlador SDN**     | Componente de infraestructura que aplica las políticas del plano de control.           |
| **Dispositivos de red** | Switches/nodos que ejecutan las decisiones de forwarding y segmentación.               |
| **IDS/IPS**             | Componentes de detección/prevención de amenazas.                                       |

---

## Y aquí está la consecuencia para vuestro proyecto

Antes de seguir refinando los casos de uso, yo construiría **tres matrices**:

### A. Matriz Actor → Recurso

¿Qué puede alcanzar cada rol?

### B. Matriz Rol → Acción

¿Qué puede hacer cada rol?

Por ejemplo:

```text
Alumno → acceder
Docente → acceder
TI → monitorear / investigar / contener
Admin → configurar / administrar
Superadmin → administrar administradores / configurar globalmente
```

### C. Matriz Recurso → Nivel de protección

Aquí recién definís qué significa R2:

```text
Recurso                     Criticidad
────────────────────────────────────────
Intranet general             Baja
Servidor académico           Media
Servidor de notas            Alta
Consola SDN                  Crítica
Controlador SDN              Crítica
Base de datos                Crítica
Logs de seguridad            Alta
Sistema IDS/IPS              Crítica
```

Y entonces **R1 + R2 empiezan a encajar naturalmente**:

> **R1:** el rol determina qué recursos puede alcanzar un usuario y qué acciones puede ejecutar sobre ellos.

> **R2:** los recursos críticos solo pueden ser alcanzados por los roles explícitamente autorizados y mediante las acciones permitidas.

> **R3–R5:** incluso cuando un actor posee autorización legítima, el sistema puede restringir, aislar o bloquear su tráfico cuando detecta comportamiento anómalo o malicioso.

Ese encadenamiento es mucho más sólido arquitectónicamente que simplemente tener cinco tipos de usuario. Y además os permite que los seis casos de uso posteriores **se deriven de las matrices**, en lugar de inventar los permisos caso por caso.

----------------------------------

Sí, añadiría **Atacante interno** como actor distinto. De hecho, para vuestro proyecto es bastante útil distinguir:

* **Atacante externo:** no posee una identidad/autorización válida dentro de la red.
* **Atacante interno:** tiene acceso legítimo a la red —por ejemplo, mediante credenciales o un dispositivo autorizado— pero genera actividad maliciosa.
* **Nodo comprometido:** no necesariamente es una persona; es un dispositivo legítimo que ha sido comprometido y puede estar siendo utilizado por un atacante.

Eso os va a ayudar bastante en R3–R5.

---

## Sobre qué seguir ahora

Si ya tenéis aproximadamente **80% de casos de uso + requerimientos funcionales + calidad + restricciones**, yo **dejaría de seguir refinando requisitos por ahora**. Ya tenéis suficiente material para comenzar a tomar decisiones arquitectónicas.

El siguiente paso natural no es todavía dibujar microservicios o elegir tecnologías. Es pasar de:

> **¿Qué debe hacer el sistema?**

a:

> **¿Qué partes necesita el sistema para hacerlo y cómo se relacionan?**

Yo seguiría este orden:

```text
REQUISITOS
    ↓
ACTORES + RECURSOS + PERMISOS
    ↓
┌──────────────────────────────┐
│ 1. Modelo conceptual         │
│ 2. Drivers arquitectónicos   │
│ 3. Contexto del sistema      │
│ 4. Descomposición funcional  │
│ 5. Arquitectura lógica       │
│ 6. Flujos principales        │
│ 7. Decisiones tecnológicas   │
│ 8. Arquitectura física       │
│ 9. Seguridad                 │
│ 10. Calidad / validación     │
└──────────────────────────────┘
```

### 1. Cerraría primero el **modelo conceptual**

Esto probablemente sea lo que más les falta.

Definan qué entidades existen en vuestro dominio:

```text
Usuario
Rol
Permiso
Recurso
Dispositivo
Sesión
Política
Regla
Flujo de red
Alerta
Incidente
Evento
IP / MAC
Segmento de red
Servicio
```

Y, sobre todo, sus relaciones.

Por ejemplo:

```text
Usuario
   │
   └── posee → Rol
                  │
                  └── concede → Permiso
                                  │
                                  └── sobre → Recurso
```

Y paralelamente:

```text
Dispositivo
    │
    ├── genera → Flujo
    │              │
    │              └── analizado por → IDS/IPS
    │                                  │
    │                                  └── genera → Alerta
    │                                                 │
    │                                                 └── deriva en → Incidente
```

Esto les va a obligar a aclarar muchas ambigüedades que todavía tienen.

---

# 2. Identificar los **Architecture Drivers**

Este paso es especialmente importante para vuestro rol de arquitecto.

No todos los requisitos tienen el mismo peso arquitectónico.

Yo extraería aproximadamente **5–10 drivers principales**.

Por ejemplo:

| Driver                               | Proviene de | Impacto arquitectónico               |
| ------------------------------------ | ----------- | ------------------------------------ |
| Control de acceso por rol            | R1          | RBAC/ABAC, autorización              |
| Protección de recursos privilegiados | R2          | Segmentación + políticas             |
| Detección de ataques internos        | R3          | IDS/monitorización                   |
| Mitigación de DDoS/brute-force       | R4          | Rate limiting, aislamiento, reacción |
| Seguridad perimetral                 | R5          | Firewall + IDS/IPS                   |
| Disponibilidad                       | Calidad     | Redundancia/recuperación             |
| Escalabilidad                        | Calidad     | Arquitectura distribuida             |
| Trazabilidad                         | Calidad     | Logs/auditoría                       |
| Baja latencia de control             | Calidad     | Diseño SDN/controlador               |

Aquí aparece una idea muy importante:

**Los drivers son los que realmente deberían guiar la arquitectura.**

No deberían terminar diciendo:

> "Usaremos Kubernetes porque es moderno."

Sino:

> "Necesitamos aislamiento, escalabilidad y recuperación; por ello evaluamos Kubernetes como mecanismo para satisfacer esos drivers."

---

# 3. Hacer el **System Context Diagram**

Antes de entrar a componentes internos, dibujen el sistema desde fuera.

Algo conceptualmente así:

```text
                     ┌──────────────┐
                     │ Superadmin   │
                     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │              │
 Alumno ────────────►│              │◄──────── Admin. Red
                     │  Plataforma  │
 Docente ───────────►│     SDN      │◄──────── Especialista TI
                     │              │
 Atacante ──────────►│              │
                     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │ Infraestructura│
                     │    de red     │
                     └───────────────┘
```

Pero no necesariamente con ese nivel de detalle.

La pregunta que debe responder es:

> **¿Dónde empieza y termina nuestro sistema?**

Eso es fundamental para R5.

¿El firewall forma parte de vuestro sistema?

¿El IDS?

¿El controlador?

¿Los switches?

¿Los servidores protegidos?

¿La autenticación institucional?

¿Internet?

¿La base de datos?

Necesitáis establecer **el límite del sistema**.

---

# 4. Después: **descomposición funcional**

Aquí empezaría realmente vuestra arquitectura.

No piensen todavía en:

> microservicio A, microservicio B, microservicio C.

Primero piensen:

> **¿Qué capacidades necesita el sistema?**

Probablemente aparezcan cosas como:

```text
                    PLATAFORMA SDN
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
 Control de acceso   Gestión de red    Seguridad
       │                  │                  │
       ├─ Autenticación   ├─ Políticas       ├─ IDS
       ├─ Autorización    ├─ Flujos          ├─ IPS
       ├─ RBAC            ├─ Segmentación    ├─ Detección
       └─ Sesiones        └─ QoS             └─ Mitigación
```

Y otro bloque:

```text
              OBSERVABILIDAD
                    │
             ┌──────┼──────┐
             │      │      │
            Logs   Métricas Alertas
```

Todavía **no son microservicios**.

Son **responsabilidades/capacidades**.

---

# 5. Recién después: arquitectura lógica

Ahora sí pueden decidir:

> ¿Qué componentes existen?

Por ejemplo, hipotéticamente:

```text
                 ┌──────────────────┐
                 │     Frontend     │
                 └────────┬─────────┘
                          │
                 ┌────────▼─────────┐
                 │ API / Gateway    │
                 └────────┬─────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
 ┌──────▼──────┐   ┌──────▼──────┐   ┌─────▼───────┐
 │Identity &   │   │Network      │   │Security     │
 │Access       │   │Policy       │   │Management   │
 └─────────────┘   └─────────────┘   └─────────────┘
                          │                 │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │ SDN Controller   │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │ Network Devices  │
                          └─────────────────┘
```

Aquí sí empieza la discusión de **monolito vs microservicios**, eventos, APIs, etc.

Y dado que vuestro profesor ya les ha indicado microservicios y eventos, esta etapa es donde deberán justificar **qué separan y por qué**.

---

# 6. Después haría algo que os va a servir muchísimo: **los 6 casos de uso como escenarios arquitectónicos**

No basta con tener los casos de uso.

Tomad cada uno y preguntad:

> ¿Qué componentes participan?

Por ejemplo:

```text
CU: Alumno intenta acceder a servidor restringido

Alumno
  ↓
Autenticación
  ↓
Identity
  ↓
Rol = Alumno
  ↓
Authorization
  ↓
Policy Engine
  ↓
SDN Controller
  ↓
Switch
  ↓
Servidor
```

Mientras que:

```text
CU: detectar ataque interno

Nodo
  ↓
Tráfico
  ↓
Sensor / IDS
  ↓
Detection Engine
  ↓
Alert
  ↓
Security Service
  ↓
Policy Engine
  ↓
SDN Controller
  ↓
Aislamiento del nodo
```

Esto es excelente para validar arquitectura porque revela **qué componentes realmente necesitan existir**.

---

# 7. Luego vienen los eventos

Como ya consideran arquitectura orientada a eventos, aquí yo definiría un **catálogo de eventos del dominio**.

Por ejemplo:

```text
UserAuthenticated
RoleAssigned
AccessDenied
SuspiciousTrafficDetected
PortScanDetected
BruteForceDetected
DDoSDetected
IncidentCreated
NodeIsolated
PolicyUpdated
FalsePositiveConfirmed
ThreatBlocked
```

Y entonces:

```text
IDS
 │
 └── SuspiciousTrafficDetected
              │
              ▼
       Security Service
              │
              ├── IncidentCreated
              │
              └── MitigationRequested
                           │
                           ▼
                     SDN Controller
                           │
                           ▼
                     NodeIsolated
```

Esto les permitirá justificar **por qué necesitan eventos**, en lugar de poner Kafka/RabbitMQ/etc. simplemente porque "la arquitectura debe usar eventos".

---

# 8. Después sí: decisiones tecnológicas

Aquí recién empezaría:

* qué controlador SDN;
* OpenFlow u otro mecanismo;
* qué IDS/IPS;
* firewall;
* autenticación;
* RBAC/ABAC;
* API Gateway;
* broker;
* base de datos;
* observabilidad;
* contenedores;
* Kubernetes;
* infraestructura;
* etc.

Y cada elección debería tener una pequeña justificación:

> **Problema → alternativa → decisión → consecuencia.**

Por ejemplo:

> Necesitamos distribuir eventos de seguridad entre detección, análisis y mitigación → comunicación síncrona generaría acoplamiento → se utiliza mensajería/eventos → aumenta resiliencia pero introduce complejidad operacional.

Eso es **arquitectura**, no simplemente selección de tecnologías.

---

# 9. Finalmente: arquitectura física/de despliegue

Ahí conectarían todo con la red real:

```text
                    INTERNET
                        │
                  ┌─────▼─────┐
                  │ Firewall  │
                  └─────┬─────┘
                        │
                ┌───────▼────────┐
                │   SDN Network  │
                │                │
                │  Controller    │
                └───────┬────────┘
                        │
          ┌─────────────┼─────────────┐
          │             │             │
       VLAN 10       VLAN 20       VLAN 30
       Alumnos       Docentes      Servidores
```

Y allí aparecerán naturalmente preguntas que ahora todavía están abiertas:

* ¿Dónde está el controlador?
* ¿Dónde se ubica el IDS?
* ¿Qué tráfico observa?
* ¿Dónde se aplica el bloqueo?
* ¿Qué segmento puede alcanzar cada rol?
* ¿Cómo se aísla un nodo?
* ¿Qué ocurre si falla el controlador?
* ¿Qué componente tiene autoridad para cambiar una regla?
* ¿Qué pasa si un administrador es comprometido?

---

## El punto donde yo pondría vuestro proyecto **ahora mismo**

No seguiría directamente con microservicios.

Haría esta secuencia de entregables:

### **Fase A — Modelo de dominio**

1. Actores.
2. Roles.
3. Recursos.
4. Servicios.
5. Permisos.
6. Relaciones entre ellos.

### **Fase B — Drivers**

7. Requerimientos arquitectónicamente relevantes.
8. Atributos de calidad.
9. Restricciones.
10. Priorización de drivers.

### **Fase C — Contexto**

11. Límite del sistema.
12. System Context Diagram.
13. Sistemas externos.
14. Infraestructura que está dentro/fuera del alcance.

### **Fase D — Arquitectura funcional**

15. Capacidades.
16. Responsabilidades.
17. Descomposición funcional.

### **Fase E — Arquitectura lógica**

18. Componentes.
19. Interfaces.
20. Dependencias.
21. Comunicación síncrona/asíncrona.
22. Eventos.

### **Fase F — Escenarios**

23. Secuencia de los 6 casos de uso.
24. Interacción entre componentes.
25. Escenarios de fallo.
26. Escenarios de ataque.

### **Fase G — Tecnología**

27. Controlador SDN.
28. IDS/IPS.
29. Firewall.
30. IAM.
31. Broker.
32. Persistencia.
33. Observabilidad.
34. Contenedores/orquestación.

### **Fase H — Despliegue**

35. Topología física.
36. Segmentación.
37. Plano de datos/control/gestión.
38. Ubicación de componentes.
39. Alta disponibilidad.
40. Recuperación.

---

### Y hay una cosa que yo haría **antes de todo eso**

Construiría una matriz central:

**Actor → Rol → Permiso → Acción → Recurso → Condición → Respuesta**

Porque actualmente están intentando definir roles sin haber terminado de definir **qué recursos existen**. Y tienes razón: ambas cosas están acopladas.

Por ejemplo:

```text
Alumno
  → acceder
  → Servidor académico
  → HTTPS
  → PERMITIR

Alumno
  → acceder
  → Servidor de notas
  → no autorizado
  → DENEGAR

Especialista TI
  → consultar
  → Logs de seguridad
  → autenticado + MFA
  → PERMITIR

Administrador
  → modificar
  → Política SDN
  → sesión administrativa
  → PERMITIR + AUDITAR

Superadministrador
  → modificar
  → Política global
  → MFA + sesión privilegiada
  → PERMITIR + AUDITAR
```

Cuando tengan esto, **los roles, recursos, R1 y R2 empiezan a encajar en un único modelo**. Y luego R3–R5 pueden reutilizar exactamente ese mismo modelo para responder algo mucho más interesante:

> **¿Qué ocurre cuando un actor que inicialmente tenía autorización empieza a comportarse de manera maliciosa?**

Ese, en mi opinión, debería ser uno de los ejes centrales de vuestra arquitectura SDN: **control de acceso + observación del comportamiento + decisión + aplicación dinámica de políticas**.
