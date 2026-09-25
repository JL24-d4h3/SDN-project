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