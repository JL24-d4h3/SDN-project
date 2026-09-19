# Actores: roles y agentes

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** A — Modelo de dominio
**Estado:** Borrador formal para revisión

---

## 1. Marco conceptual

| Concepto | Definición |
|---|---|
| **Actor** | Entidad que interactúa con el sistema. Puede ser una persona, un dispositivo, un componente de infraestructura o una entidad maliciosa. |
| **Identidad** | Quién es el actor, establecido mediante autenticación. |
| **Rol** | Conjunto de permisos que el sistema concede a una identidad, definido por lo que puede hacer y sobre qué recursos. |
| **Nivel de privilegio** | Posición del rol dentro de la jerarquía de autoridad del sistema. |

**Un atacante no es un rol.** Un rol es una etiqueta autorizada que el sistema concede; un atacante es una entidad cuyo comportamiento el sistema debe detectar y controlar. Por eso los actores se separan en dos categorías: actores con roles autorizados (sección 2) y agentes sin rol autorizado (sección 3).

Además, el rol no define por sí solo el permiso efectivo: el acceso depende también del recurso, la acción, el contexto y el estado de seguridad (sección 4).

---

## 2. Actores con roles autorizados

### 2.1 Jerarquía de privilegios

| Nivel | Rol | Propósito | Acceso a usuarios | Acceso a recursos | Modifica la red |
|---|---|---|---|---|---|
| 0 | Alumno | Usuario final | Solo sus propios recursos | Públicos + académicos autorizados | No |
| 1 | Docente | Usuario académico | Solo sus propios recursos | Públicos + académicos + docentes | No |
| 2 | Especialista de TI | Seguridad y monitoreo | Información necesaria para investigar | Recursos de monitoreo y seguridad | Limitado |
| 3 | Administrador de Red | Administración operativa | Todos los necesarios para administrar | Todos los recursos de red según autorización | Sí |
| 4 | Superadministrador | Control de la plataforma | Todos | Todos | Sí, sin restricciones operativas |

### 2.2 Alumno — Nivel 0

**Función:** consumir servicios. No administra infraestructura.

**Puede**

- Autenticarse en la red.
- Obtener acceso a la intranet general.
- Acceder a servicios públicos e institucionales.
- Acceder a los recursos académicos autorizados para su rol.
- Generar tráfico normal hacia servicios permitidos.
- Utilizar Internet, si la arquitectura lo contempla.

**No puede**

- Modificar políticas de red, ACL o firewall.
- Administrar switches, VLAN ni segmentación.
- Acceder a la consola SDN ni a servidores administrativos.
- Modificar configuraciones de seguridad.
- Administrar otros usuarios.
- Deshabilitar mecanismos de seguridad.

### 2.3 Docente — Nivel 1

Mismo principio de mínimo privilegio que el alumno, con un conjunto distinto de recursos autorizados. La diferencia entre ambos roles no es la cantidad de privilegio, sino qué recursos alcanza cada uno.

**Puede** — todo lo del alumno, más:

- Acceder a servidores y servicios exclusivos para docentes.
- Acceder a los sistemas académicos administrativos que correspondan a su función.
- Acceder a recursos compartidos docentes.
- Acceder a determinados servicios internos no disponibles para alumnos.

**No puede** — todo lo que el alumno tampoco puede, más:

- Administrar usuarios ni políticas.
- Modificar infraestructura.
- Acceder a la consola administrativa.
- Acceder a información de seguridad restringida.

### 2.4 Especialista de TI — Nivel 2

**Función:** supervisar el estado de seguridad de la red y responder a eventos de seguridad, sin poseer necesariamente control administrativo completo sobre la infraestructura.

Este rol separa la seguridad de la infraestructura: el Administrador de Red administra la red; el Especialista de TI la vigila y responde ante incidentes.

**Puede**

- Consultar tráfico, métricas de red y registros.
- Consultar eventos del IDS/IPS y alertas del sistema.
- Investigar direcciones IP y dispositivos sospechosos.
- Marcar una alerta como falso positivo.
- Escalar un incidente.
- Solicitar o ejecutar acciones de mitigación predefinidas.
- Aislar un nodo comprometido, si la arquitectura lo permite.
- Aplicar medidas de contención predefinidas.

**No puede**

- Crear o modificar libremente la política de red completa.
- Crear administradores.
- Cambiar la arquitectura SDN ni configuraciones críticas del controlador.
- Revocar credenciales de administradores.
- Eliminar registros de seguridad.
- Desactivar IDS/IPS.

### 2.5 Administrador de Red — Nivel 3

**Función:** configurar, mantener y administrar la red y sus políticas de acceso. Es el operador de la infraestructura.

**Puede**

- Crear, modificar y eliminar políticas de acceso; gestionar ACL.
- Administrar segmentación y VLAN.
- Administrar switches y dispositivos SDN, reglas de forwarding y políticas de QoS.
- Administrar usuarios y la asignación de roles.
- Habilitar o deshabilitar determinados servicios.
- Gestionar rutas y configurar mecanismos de seguridad de red.
- Consultar registros operativos y gestionar recursos de red.
- Aplicar medidas de mitigación autorizadas.

**No puede** — su autoridad no es absoluta:

- Modificar o revocar políticas por encima de la autoridad del Superadministrador.
- Alterar la definición de roles y permisos administrativos.
- Omitir el registro y la auditoría de sus cambios de política.

### 2.6 Superadministrador — Nivel 4

**Función:** privilegios máximos sobre el plano de administración de la solución SDN, incluyendo la gestión de administradores, las políticas globales y los mecanismos de seguridad.

**Puede**

- Crear y eliminar administradores; crear, modificar y eliminar roles y permisos.
- Revocar privilegios.
- Configurar políticas globales y modificar políticas de seguridad.
- Administrar el controlador SDN, los dispositivos de red, el IDS/IPS y los mecanismos de mitigación.
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
       │                    └── administra → usuarios
       │
       └── administra → Especialista de TI
                            │
                            └── gestiona → incidentes
```

### 2.7 Separación de funciones

Ningún rol concentra la capacidad de definir una política, aplicarla y evaluarla sin control:

- El **Administrador de Red** puede crear una política, pero el **Superadministrador** puede modificarla o revocarla.
- El **Especialista de TI** puede detectar que una política está provocando un incidente, pero no modificarla directamente.
- Los cambios de política y las acciones administrativas quedan registrados y son auditables (R1.9, R2.9, ADM-04).

### 2.8 Usuario de red y usuario administrativo

El sistema atiende dos poblaciones distintas, que conviene modelar por separado: sería inconsistente que un Superadministrador operara la intranet como un usuario final.

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
                           Superadministrador
```

---

## 3. Agentes sin rol autorizado

Estas entidades no reciben roles ni permisos. El sistema las trata como orígenes de comportamiento que debe observar, clasificar y, cuando corresponda, contener.

### 3.1 Atacante externo

No posee identidad ni autorización válida dentro de la red. Origina actividad maliciosa desde redes externas. Es el sujeto de R5 y, si logra atravesar el perímetro, también de R3 y R4.

### 3.2 Atacante interno

Dispone de acceso legítimo a la red —credenciales válidas o un dispositivo autorizado— pero genera actividad maliciosa. Es el caso que obliga a separar autenticación de confianza: un actor autorizado puede convertirse en origen de tráfico malicioso.

### 3.3 Nodo comprometido

No es necesariamente una persona: es un dispositivo legítimo cuyo comportamiento ha sido comprometido o resulta indistinguible de un compromiso. Puede estar siendo utilizado por un atacante interno o externo sin que su usuario legítimo lo advierta.

### 3.4 Componentes de infraestructura

No son actores autorizados ni atacantes: son agentes del sistema que ejecutan decisiones o generan información.

| Entidad | Naturaleza |
|---|---|
| Controlador SDN | Componente de infraestructura que aplica las políticas del plano de control. |
| Dispositivos de red | Switches y nodos que ejecutan las decisiones de forwarding y segmentación. |
| IDS/IPS | Componentes de detección y prevención de amenazas; generan eventos y alertas. |
| Servicios y servidores | Origen y destino de los flujos protegidos; también generan registros. |

### 3.5 Resumen de entidades

| Entidad | Naturaleza | Relación con el sistema |
|---|---|---|
| Alumno | Actor con rol | Rol autorizado (nivel 0) |
| Docente | Actor con rol | Rol autorizado (nivel 1) |
| Especialista de TI | Actor con rol | Rol autorizado (nivel 2) |
| Administrador de Red | Actor con rol | Rol autorizado (nivel 3) |
| Superadministrador | Actor con rol | Rol autorizado (nivel 4) |
| Atacante externo | Entidad no autorizada | Sin identidad válida en la red |
| Atacante interno | Entidad no autorizada | Acceso legítimo, comportamiento malicioso |
| Nodo comprometido | Entidad no autorizada | Dispositivo legítimo comprometido |
| Controlador SDN | Agente del sistema | Aplica políticas |
| Dispositivos de red | Agente del sistema | Ejecutan forwarding y segmentación |
| IDS/IPS | Agente del sistema | Detectan y reportan |
| Servicios y servidores | Agente del sistema | Proveen recursos y registros |

---

## 4. El rol no otorga confianza permanente

El permiso efectivo no depende solo del rol:

```text
PERMISO EFECTIVO = ROL + RECURSO + ACCIÓN + CONTEXTO + ESTADO DE SEGURIDAD
```

Combinaciones que el modelo debe admitir:

| Actor | Recurso | Condición | Resultado |
|---|---|---|---|
| Alumno | Servidor académico | Autorizado por rol | Permitir |
| Alumno | Servidor de notas | Credenciales válidas, sin autorización | Denegar |
| Docente | Servidor académico | HTTPS, tráfico normal | Permitir |
| Docente | Servidor académico | Tráfico anómalo o dispositivo comprometido | Aislar o bloquear |
| Especialista de TI | Logs de seguridad | Autenticado + MFA | Permitir |
| Administrador de Red | Política SDN | Sesión administrativa | Permitir y auditar |
| Superadministrador | Política global | MFA + sesión privilegiada | Permitir y auditar |

Esto conecta R1 y R2 con R3–R5: la autorización habilita el acceso, pero no suspende la vigilancia. La detección puede restringir, aislar o bloquear el tráfico de un actor que sí posee autorización válida.

---

## 5. Cuestiones abiertas

- **Personal administrativo.** La primera versión de requisitos lo listaba como actor. Este modelo no lo incluye: definir si constituye un rol propio —con qué nivel de privilegio y qué recursos— o si queda cubierto por los roles existentes.
- **Matriz Actor → Recurso.** Se deriva de este documento y de [`02_recursos_y_servicios.md`](02_recursos_y_servicios.md); corresponde a `03_permisos.md`.
- **Autenticación y MFA.** El mecanismo concreto y si MFA es obligatorio para los roles administrativos es una decisión arquitectónica pendiente.
