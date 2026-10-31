# Matriz Rol × Permiso

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Etapa 0
**Estado:** Borrador formal para revisión

---

## 1. Roles

| Rol | Nivel | Población | Identidad | Sesión |
|---|---|---|---|---|
| Académico | 0 | Estudiantes y docentes | IdP institucional o LDAP del prototipo | Portal, sin MFA obligatorio |
| Especialista de TI | 1 | Soporte y operación de servicios | Repositorio propio + MFA TOTP | Consola o API, dispositivo registrado |
| Administrador de Red | 2 | Operación de la red y del controlador | Repositorio propio + MFA TOTP | Consola o API, dispositivo registrado |
| Superadministrador | 3 | Gobierno de la plataforma | Repositorio propio + MFA TOTP | Consola o API, dispositivo registrado |

Los roles son etiquetas RBAC. No son perfiles de red y no se asignan directamente a un switch.

## 2. Perfiles de red

| Perfil | Tipo | Origen | Ámbito | Prioridad de sesión |
|---|---|---|---|---|
| BASE | Fijo | Dispositivo no autenticado | Portal, DHCP, DNS | Portal 150; DHCP/DNS 10 |
| ACADÉMICO | Fijo | Usuario académico autenticado | Servicios académicos e Internet | 190 provisional; se fija con la medición de access/02 §3 |
| OPERADOR_TI | Derivado | Rol Especialista de TI | Consola y APIs de seguridad | 200 |
| OPERADOR_ADMIN | Derivado | Rol Administrador de Red | Red de gestión | 200 |
| OPERADOR_SA | Derivado | Rol Superadministrador | Red de gestión y acceso remoto | 200 |
| ELEVACIÓN(scope, TTL) | Parametrizado | P28 + aprobación P29 | Alcance y TTL de la solicitud | 200 |

`LABORATORIO` es una instancia de ELEVACIÓN con alcance de laboratorio y TTL corto; no es un perfil fijo. Los nombres `TI`, `ADMIN_RED` y `SUPER_ADMIN` se conservan como alias documentales de `OPERADOR_TI`, `OPERADOR_ADMIN` y `OPERADOR_SA`.

## 3. Convención de la matriz

| Símbolo | Significado |
|---|---|
| `P` | Permitido. Para operadores se aplica además C5; para todos, C6. |
| `C1`…`C11` | Permitido solo si se cumple la condición indicada. |
| `C1+C4` | Deben cumplirse ambas condiciones. |
| `—` | No concedido; la decisión es denegar. |
| `PRE` | Acción de pre-sesión; no es un permiso RBAC. |
| `RED` | Decisión de red; produce un perfil, no un permiso de servicio. |

C5 y C6 son obligatorias y no se repiten en cada celda:

- **C5** para todo permiso de un operador (TI, Administrador, Superadministrador).
- **C6** para todo permiso, incluido el académico.

## 4. Condiciones

| Código | Condición | Atributos |
|---|---|---|
| C1 | Ámbito | El recurso pertenece al ámbito asignado al rol. |
| C2 | Delegación vigente | Existe una delegación explícita, con alcance y vigencia. |
| C3 | Rango aprobado | El valor o la acción está dentro del rango aprobado. |
| C4 | Separación de funciones | El solicitante es distinto del aprobador. |
| C5 | Sesión privilegiada | MFA verificado, dispositivo registrado y canal de gestión. |
| C6 | Estado de seguridad | Sin compromiso, cuarentena o incidente que impida la acción. |
| C7 | Bajo impacto | La severidad no supera el umbral; si lo supera, se exige P32. |
| C8 | Sesión propia | El sujeto solo opera sus propias sesiones. |
| C9 | Recurso autorizado | El tipo y la instancia del recurso están en la lista del rol. |
| C10 | Contexto permitido | Ventana, ubicación y canal permitidos; la configuración crítica exige ventana de mantenimiento o emergencia declarada. |
| C11 | Solo lectura | El rol puede consultar y ejecutar operaciones autorizadas, no configurar. |

## 5. Matriz completa

| ID | Permiso | Académico | Especialista de TI | Administrador de Red | Superadministrador |
|---|---|---|---|---|---|
| P01 | Autenticarse | PRE | PRE | PRE | PRE |
| P02 | Acceder a la red | RED | RED | RED | RED |
| P03 | Acceder a servicio | C9 | C9 | C9 | P |
| P04 | Consultar recurso | C9 | C9 | C9 | P |
| P05 | Ejecutar operación | C9 | C7+C9 | C9 | P |
| P06 | Consultar estado de red | — | C1 | C1 | P |
| P07 | Consultar tráfico | — | C1 | C1 | P |
| P08 | Consultar eventos y logs | — | C1 | C1 | P |
| P09 | Consultar alertas | — | C1 | C1 | P |
| P10 | Analizar incidente | — | C1 | C1 | P |
| P11 | Gestionar alerta | — | C1 | C1 | P |
| P12 | Ejecutar mitigación | — | C7 | P | P |
| P13 | Aislar nodo | — | C7 | P | P |
| P14 | Gestionar cuentas locales | — | — | C1 | P |
| P15 | Asignar rol | — | — | — | P |
| P16 | Gestionar permisos | — | — | — | P |
| P17 | Gestionar políticas de acceso | — | — | P | P |
| P18 | Gestionar políticas de seguridad | — | — | — | P |
| P19 | Gestionar reglas de red | — | — | P | P |
| P20 | Gestionar segmentación | — | — | P | P |
| P21 | Gestionar dispositivos de red | — | — | P | P |
| P22-OP | Operar el controlador SDN | — | C1+C11 | P | P |
| P22-CFG | Configurar el controlador SDN | — | — | — | C10 |
| P23 | Gestionar mecanismos de seguridad | — | — | C3 | P |
| P24 | Gestionar administradores | — | — | C2 | P |
| P25 | Auditar operaciones | — | — | — | P |
| P26 | Gestionar configuración global | — | — | — | C10 |
| P27 | Gestionar recuperación | — | — | — | C10 |
| P28 | Solicitar elevación | C9 | — | — | — |
| P29 | Aprobar elevación | — | — | C4 | C4 |
| P30 | Registrar dispositivo privilegiado | — | — | C2 | P |
| P31 | Gestionar sesiones | — | C8 | C1 | P |
| P32 | Aprobar acción de alto impacto | — | — | C1+C4 | C4 |
| P33 | Ajustar umbrales de detección | — | C3 | C3 | P |
| P34 | Gestionar claves y certificados | — | — | — | P |
| P35 | Solicitar registro de dispositivo | — | P | P | P |
| P36 | Gestionar retención y exportación de auditoría | — | — | — | P |

## 6. Reglas de separación y delegación

| Regla | Permisos afectados | Consecuencia |
|---|---|---|
| Sin autoaprobación | P29, P32 | El solicitante no puede aprobar su propia solicitud; se deniega. |
| Sin autoelevación | P15, P16, P24 | Nadie se asigna a sí mismo un rol, permiso o cuenta administrativa. |
| Sin privilegio por unión | Todos | La combinación de roles no supera el mayor privilegio; la delegación es la única vía para ampliar. |
| Delegación acotada | P14, P24, P30 | Solo el Superadministrador delega; el Administrador de Red recibe delegación sobre cuentas y dispositivos de TI, con vigencia. |
| Configuración crítica | P22-CFG, P26, P27 | Solo Superadministrador y en contexto permitido; la emergencia se declara y se audita. |
| Detección separada de mitigación | P12, P13, P23 | TI mitiga y ajusta umbrales dentro de rango; no desactiva la detección. |
| Auditoría separada de operación | P25, P36 | El operador consulta logs (P08), pero no administra la auditoría. |
| Break-glass fuera de P14 | P14 | Las cuentas de emergencia se gestionan por procedimiento offline con doble control; no se crean ni modifican por API. |
| Registro no concede confianza | P35, P30 | La solicitud de registro no otorga privilegios; el registro efectivo y el historial del dispositivo son requisitos de C5. |

## 7. Lectura de la matriz

- **Académico:** solo P01, P02, P03, P04, P05 y P28. No opera la red ni la plataforma. Su acceso a servicios depende de C9, y su elevación de laboratorio es una instancia de ELEVACIÓN con aprobación P29.
- **Especialista de TI:** observa, analiza y mitiga dentro de su ámbito; no configura el controlador ni gestiona roles. Su operación sobre el controlador es de solo lectura (C11).
- **Administrador de Red:** opera la red, las políticas de acceso, la segmentación y los dispositivos; aprueba elevaciones y acciones de alto impacto dentro de su ámbito, nunca las propias.
- **Superadministrador:** gobierna la plataforma; conserva la configuración crítica, la gestión de roles y permisos, las claves, la auditoría y la recuperación. No se autoaprueba.

## 8. Generación y consistencia

La matriz es una vista del archivo [`policy/permisos.yaml`](policy/permisos.yaml). El archivo contiene los roles, perfiles, permisos, condiciones y asignaciones; la tabla se genera desde él y el plan de pruebas valida que no existan celdas sin condición, permisos duplicados ni referencias a condiciones inexistentes.

| Verificación | Regla |
|---|---|
| Cobertura | Los 37 identificadores aparecen exactamente una vez. |
| Condiciones | Toda celda `Cxx` referencia una condición definida en el YAML. |
| Denegación | Toda celda `—` tiene una regla de denegación explícita o cae en la denegación por defecto. |
| Separación | P29 y P32 exigen C4 en todos los roles que las poseen. |
| Delegación | P14, P24 y P30 exigen C2 en el Administrador de Red. |
| Auditoría | Todo permiso con efecto de cambio exige la obligación `auditar`. |

## 9. Trazabilidad

| Documento | Relación |
|---|---|
| [`03_permisos.md`](../docs/fases/A-Modelo_de_dominio/03_permisos.md) | Catálogo P01–P36 |
| [`01_modelo_de_contexto_y_estado.md`](01_modelo_de_contexto_y_estado.md) | Definición de contexto, estado y vigencia |
| [`policy/permisos.yaml`](policy/permisos.yaml) | Fuente de verdad |
| [`03_plan_de_pruebas_permisos.md`](03_plan_de_pruebas_permisos.md) | Casos de prueba de la matriz |
| [`../docs/componentes/02_autorizacion.md`](../docs/componentes/02_autorizacion.md) | Autorización en servicios y red |
