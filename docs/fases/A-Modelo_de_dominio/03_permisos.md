# Modelo de Dominio — Permisos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** A — Modelo de dominio
**Estado:** Borrador formal para revisión

---

## 1. Objetivo

Definir las acciones que pueden ejecutar los roles autorizados sobre los recursos y servicios de la solución SDN, aplicando el principio de mínimo privilegio.

Los permisos representan **acciones autorizadas**; no representan por sí mismos a los actores, roles ni recursos.

## 2. Catálogo de permisos

| ID | Permiso | Plano | Descripción |
|---|---|---|---|
| P01 | Autenticarse | Pre-sesión | Iniciar sesión y acreditar la identidad ante la plataforma. |
| P02 | Acceder a la red | Red | Obtener el perfil de red que corresponde al sujeto, dispositivo y contexto. |
| P03 | Acceder a servicio | Servicios | Utilizar un servicio autorizado. |
| P04 | Consultar recurso | Servicios | Leer o consultar información de un recurso autorizado. |
| P05 | Ejecutar operación | Servicios | Ejecutar una operación funcional sobre un servicio autorizado. |
| P06 | Consultar estado de red | Servicios | Consultar el estado, la disponibilidad y las métricas operativas de la red. |
| P07 | Consultar tráfico | Servicios | Consultar información y métricas asociadas al tráfico de red. |
| P08 | Consultar eventos y logs | Servicios | Consultar eventos, registros y trazas autorizadas. |
| P09 | Consultar alertas | Servicios | Visualizar alertas generadas por los mecanismos de seguridad. |
| P10 | Analizar incidente | Servicios | Investigar y analizar un evento o incidente de seguridad. |
| P11 | Gestionar alerta | Servicios | Clasificar, confirmar, descartar o escalar una alerta. |
| P12 | Ejecutar mitigación | Servicios | Aplicar una medida de contención o mitigación previamente autorizada. |
| P13 | Aislar nodo | Servicios | Restringir o aislar un dispositivo o segmento identificado como comprometido o malicioso. |
| P14 | Gestionar cuentas locales | Servicios | Crear, modificar, bloquear o deshabilitar cuentas locales de la plataforma. Excluye identidades institucionales, break-glass y cuentas de Superadministrador. |
| P15 | Asignar rol | Servicios | Asignar o modificar el rol de una identidad. |
| P16 | Gestionar permisos | Servicios | Crear, modificar o revocar permisos asociados a roles. |
| P17 | Gestionar políticas de acceso | Servicios | Crear, modificar, activar, desactivar o eliminar políticas de acceso y perfiles. |
| P18 | Gestionar políticas de seguridad | Servicios | Configurar reglas de detección, prevención y mitigación. |
| P19 | Gestionar reglas de red | Servicios | Crear, modificar o eliminar reglas de forwarding, filtrado o control de tráfico. |
| P20 | Gestionar segmentación | Servicios | Crear, modificar o administrar segmentos, VLANs u otros mecanismos de aislamiento lógico. |
| P21 | Gestionar dispositivos de red | Servicios | Registrar, configurar, actualizar, habilitar o deshabilitar dispositivos administrados. |
| P22-OP | Operar el controlador SDN | Servicios | Consultar topología, flujos y estado; ejecutar operaciones autorizadas sobre el controlador. |
| P22-CFG | Configurar el controlador SDN | Servicios | Configurar el clúster, sus aplicaciones y sus parámetros críticos. |
| P23 | Gestionar mecanismos de seguridad | Servicios | Administrar IDS, IPS, firewall u otros mecanismos de protección integrados, dentro del rango aprobado. |
| P24 | Gestionar administradores | Servicios | Crear, modificar, bloquear, revocar o eliminar cuentas y privilegios de administradores. |
| P25 | Auditar operaciones | Servicios | Consultar y verificar la auditoría de las acciones realizadas en la plataforma. |
| P26 | Gestionar configuración global | Servicios | Modificar parámetros globales de la plataforma SDN y sus componentes críticos. |
| P27 | Gestionar recuperación | Servicios | Ejecutar o administrar procedimientos de restauración y recuperación de la plataforma. |
| P28 | Solicitar elevación | Servicios | Solicitar una sesión temporal con alcance elevado, con justificación, alcance y duración. LABORATORIO es una instancia de esta solicitud. |
| P29 | Aprobar elevación | Servicios | Aprobar o rechazar solicitudes de elevación temporal; definir su alcance y TTL. |
| P30 | Registrar dispositivo privilegiado | Servicios | Dar de alta, modificar o dar de baja dispositivos en el registro de dispositivos privilegiados, con su información completa y constancia para auditoría. |
| P31 | Gestionar sesiones | Servicios | Consultar o revocar sesiones de la plataforma. |
| P32 | Aprobar acción de alto impacto | Servicios | Aprobar cuarentena, aislamiento u otra acción crítica, vinculada a una solicitud concreta. |
| P33 | Ajustar umbrales de detección | Servicios | Ajustar umbrales de detección dentro del rango aprobado. |
| P34 | Gestionar claves y certificados | Servicios | Crear, rotar o revocar claves y certificados de la plataforma. |
| P35 | Solicitar registro de dispositivo | Servicios | Solicitar el registro de un dispositivo; la solicitud no concede confianza ni privilegios. |
| P36 | Gestionar retención y exportación de auditoría | Servicios | Definir la retención y exportar registros de auditoría. |

P22 designa la familia del controlador; P22-OP y P22-CFG son sus dos permisos. P01 se conserva como acción de pre-sesión y P02 como decisión de red: ninguno de los dos se asigna como permiso RBAC en la matriz.

## 3. Principios de asignación

1. Un permiso debe concederse explícitamente a uno o más roles.
2. La posesión de un rol no implica acceso irrestricto a todos los recursos.
3. El acceso efectivo se evalúa con seis ejes: `SUJETO × ACCIÓN × RECURSO × CONTEXTO × ESTADO DE SEGURIDAD × VIGENCIA`. El contexto se divide en sesión, ambiental y recurso; el estado de seguridad se evalúa como restricción dura y puede anular un permiso.
4. El acceso base de la red (perfil BASE) no depende de ningún permiso otorgado a una persona: se concede al dispositivo por presencia física y cubre solo lo mínimo (deny by default).
5. Los permisos administrativos deben mantenerse separados de los permisos de usuario final.
6. Las operaciones críticas deben quedar registradas mediante auditoría.
7. Las acciones de mitigación deben poder estar sujetas a políticas y condiciones de seguridad.
8. El Superadministrador posee control máximo, pero sus operaciones críticas también deben ser auditables.
9. Un atacante interno o externo y un nodo comprometido **no reciben permisos autorizados**; son entidades cuyo acceso o comportamiento debe ser detectado, restringido o bloqueado.

## 4. Niveles conceptuales

### Permisos de acceso
P01–P05, P28, P35

Permiten autenticarse, acceder a la red, utilizar recursos o servicios autorizados y solicitar elevaciones o registros.

### Permisos de supervisión y respuesta
P06–P13

Permiten observar la red, investigar eventos y ejecutar acciones de respuesta.

### Permisos de administración
P14–P21, P22-OP, P23, P27, P29–P31, P33

Permiten administrar cuentas locales, políticas, infraestructura y mecanismos de seguridad; operar el controlador; aprobar elevaciones; registrar dispositivos y ajustar umbrales.

### Permisos de gobierno
P22-CFG, P24–P26, P32, P34, P36

Permiten configurar el controlador, administrar privilegios administrativos, aprobar acciones de alto impacto, gestionar claves y administrar la auditoría.

## 5. Matriz y política

La asignación definitiva de estos permisos a cada rol se establece en la matriz **Rol × Permiso** de [`implementation/02_matriz_rol_permiso.md`](../../../implementation/02_matriz_rol_permiso.md). La fuente de verdad ejecutable es [`implementation/policy/permisos.yaml`](../../../implementation/policy/permisos.yaml); la matriz es su vista generada. Este catálogo define los permisos, no sustituye la matriz.
