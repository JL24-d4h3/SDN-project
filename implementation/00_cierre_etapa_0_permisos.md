# Cierre de la etapa 0 — Modelo de permisos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Etapa 0
**Estado:** Borrador formal para revisión

---

## 1. Propósito

Cerrar el modelo de permisos que gobierna la plataforma y dejar sus artefactos verificables: catálogo, matriz Rol × Permiso, archivo de políticas, modelo de contexto y plan de pruebas. La etapa no implementa código de producto; fija la fuente de verdad y los criterios de aceptación con los que se implementará y probará.

La etapa se cierra el 2026-10-28: las decisiones D1–D8 son vinculantes para la implementación y solo se revisan si una medición del prototipo obliga a un cambio explícito.

La etapa se apoya en tres separaciones:

1. **Roles** humanos (4) y **perfiles** de red (2 fijos, 3 derivados de rol y 1 parametrizado) son conceptos distintos.
2. **Autorización de servicios** (RBAC con condiciones) y **autorización de red** (ABAC que decide el perfil) son planos distintos; la primera se valida en cada servicio y la segunda se materializa en el switch.
3. **Contexto** (circunstancias de la solicitud) y **estado de seguridad** (condición del sujeto y del entorno) son ejes distintos; el segundo puede anular un permiso, no solo acotarlo.

## 2. Decisiones cerradas

### D1. Dos planos y dos reclasificaciones

- **P01 — Autenticarse** es una acción de pre-sesión, no un permiso RBAC. Se conserva el identificador por compatibilidad documental, pero no se concede en la matriz: se permite a todo sujeto antes de tener sesión.
- **P02 — Acceder a la red** es la decisión ABAC que produce un perfil, no un permiso RBAC. Se conserva el identificador y se etiqueta como decisión de red.
- El resto de P03–P36 pertenece al plano de servicios y se valida en cada petición de la API I7, salvo las acciones que el Policy Engine traduce a órdenes I2 y el switch ejecuta.

### D2. Seis ejes y contexto dividido

El permiso efectivo se evalúa con seis ejes:

```text
PERMISO EFECTIVO = SUJETO × ACCIÓN × RECURSO × CONTEXTO × ESTADO DE SEGURIDAD × VIGENCIA
```

- **Sujeto:** identidad, rol, dispositivo, registro y MFA.
- **Acción:** permiso Pxx y verbo concreto.
- **Recurso:** tipo, identificador, propietario, clasificación y estado.
- **Contexto:** sesión, ambiental y de recurso.
- **Estado de seguridad:** del sujeto y del entorno.
- **Vigencia:** TTL, expiración y ventana.

El contexto se divide en tres subdimensiones y el estado de seguridad se mantiene separado. La definición completa está en [`01_modelo_de_contexto_y_estado.md`](01_modelo_de_contexto_y_estado.md).

### D3. Roles y perfiles

**Roles (4):** académico, especialista de TI, administrador de red y superadministrador. Son las etiquetas RBAC que se asignan a identidades humanas.

**Perfiles de red:** BASE y ACADÉMICO son fijos; OPERADOR_TI, OPERADOR_ADMIN y OPERADOR_SA se derivan del rol del operador; ELEVACIÓN es un perfil parametrizado por alcance y TTL. LABORATORIO es una instancia de ELEVACIÓN, no un perfil fijo. Los nombres TI, ADMIN_RED y SUPER_ADMIN se conservan como alias documentales de los perfiles de operador.

La tabla de correspondencia está en [`02_matriz_rol_permiso.md`](02_matriz_rol_permiso.md) §2.

### D4. Catálogo y permisos nuevos

Se conserva P01–P30 y se añaden P31–P36. P22 se divide en P22-OP (operar) y P22-CFG (configurar). Las definiciones están en el catálogo de la fase A, [`03_permisos.md`](../docs/fases/A-Modelo_de_dominio/03_permisos.md).

| ID | Permiso | Decisión de alcance |
|---|---|---|
| P14 | Gestionar cuentas locales | Solo cuentas locales de la plataforma; excluye identidades institucionales, break-glass y cuentas de Superadministrador. El break-glass se administra por procedimiento offline con doble control. |
| P22-OP | Operar el controlador | Administrador de Red y Superadministrador; TI solo lectura y operaciones autorizadas. |
| P22-CFG | Configurar el controlador | Solo Superadministrador. |
| P24 | Gestionar administradores | Superadministrador; el Administrador de Red solo con delegación explícita y limitada a cuentas de TI. |
| P25 | Auditar operaciones | Superadministrador. El componente de Auditoría registra todas las acciones; un auditor externo de solo lectura es una delegación de despliegue de referencia, no un quinto rol del prototipo. |
| P31 | Gestionar sesiones | TI y Administrador dentro de su ámbito; Superadministrador sin restricción. |
| P32 | Aprobar acción de alto impacto | Administrador dentro de su ámbito; Superadministrador en todos los ámbitos; nunca el solicitante. |
| P33 | Ajustar umbrales de detección | TI dentro del rango aprobado; Administrador fija el rango; Superadministrador fija los límites globales. |
| P34 | Gestionar claves y certificados | Solo Superadministrador. |
| P35 | Solicitar registro de dispositivo | TI, Administrador y Superadministrador; la solicitud no concede confianza ni privilegios. |
| P36 | Gestionar retención y exportación de auditoría | Solo Superadministrador; fuera del alcance funcional del prototipo, pero cubierto por las pruebas de decisión. |

### D5. Separación de ejecución y aprobación

- P12 (ejecutar mitigación) y P13 (aislar nodo) no incluyen la aprobación de acciones de alto impacto.
- P32 aprueba cuarentena, aislamiento de segmento y otras acciones críticas. La aprobación se vincula a una solicitud concreta, con alcance, motivo, solicitante, aprobador y expiración.
- La cuarentena de un nodo puede ser automática si la política lo autoriza; el aislamiento de un segmento exige aprobación humana, salvo procedimiento de emergencia definido y auditado.
- Ningún sujeto aprueba su propia solicitud. Ninguna aprobación sustituye las comprobaciones de seguridad obligatorias.

### D6. Delegación

La delegación es explícita, delimitada, temporal y auditada. El Superadministrador puede delegar en el Administrador de Red:

- el registro de Especialistas de TI en el registro de dispositivos (P30) y la gestión de sus cuentas (P24), limitada a cuentas de TI;
- la gestión de cuentas locales no administrativas (P14), dentro de su ámbito.

La delegación no permite crear otros Administradores de Red, elevar los privilegios propios ni transferir la facultad de configuración crítica (P22-CFG, P24 sobre Administradores o Superadministradores, P34).

### D7. Política como código

El archivo [`policy/permisos.yaml`](policy/permisos.yaml) es la fuente de verdad. La matriz Rol × Permiso es una vista generada desde ese archivo; no se mantiene como segunda fuente. Las pruebas leen el mismo archivo.

### D8. Semántica de decisión

- **Denegación por defecto:** si no hay regla aplicable, se deniega.
- **Precedencia de denegación:** si una regla aplicable deniega, la decisión es denegar aunque otra permita.
- **Restricciones duras:** una sesión inválida, un dispositivo en cuarentena o un incidente activo pueden denegar antes de evaluar las reglas de permiso.
- **Obligaciones:** auditar, notificar, exigir aprobación, fijar TTL, justificar, doble control, no registrar material secreto.
- **Fallo seguro:** si no se pueden obtener atributos críticos de seguridad, se deniega o se exige step-up; no se concede por defecto.

## 3. Criterios de aceptación de la etapa

1. El catálogo P01–P36 está completo y cada permiso tiene plano, alcance y descripción.
2. La matriz cubre los 37 identificadores (P01–P36 más P22-CFG) para los cuatro roles, sin celdas ambiguas.
3. Cada celda condicional apunta a una condición definida en el YAML.
4. El archivo de políticas valida contra su esquema y no tiene identificadores duplicados ni referencias inválidas.
5. El plan de pruebas cubre allow y deny para cada permiso, las invariantes de separación de funciones, la vigencia y la auditoría.
6. Las pruebas de enforcement verifican que la decisión se materializa como regla en el switch para BASE, ACADÉMICO, operador, elevación y mitigación.
7. La matriz y las tablas LaTeX se generan desde el YAML.

**Verificación (2026-10-28):** catálogo 37/37; matriz de 37 filas × 4 roles; YAML con 4 roles, 37 permisos, 78 asignaciones y 11 condiciones, sin identificadores duplicados ni referencias inválidas; `python3 implementation/policy/generar_matriz.py --check` devuelve OK para la matriz Markdown y para la tabla LaTeX del documento consolidado.

## 4. Fuera de alcance

- La implementación de los servicios y del portal.
- La verificación real de las capacidades del switch; se estiman en [`04_capacidades_del_switch.md`](04_capacidades_del_switch.md) y se confirman en el primer laboratorio.
- La integración con el IdP institucional; el prototipo despliega FreeRADIUS y OpenLDAP si el slice no alcanza el IdP.
- P35 y P36 a nivel funcional; su lógica de decisión sí se prueba.
- Un quinto rol de auditor; se mantiene como delegación de referencia.

## 5. Trazabilidad

| Artefacto | Contenido |
|---|---|
| [`01_modelo_de_contexto_y_estado.md`](01_modelo_de_contexto_y_estado.md) | Definición de contexto, estado de seguridad, vigencia y pipeline de decisión |
| [`02_matriz_rol_permiso.md`](02_matriz_rol_permiso.md) | Matriz completa, condiciones y reglas de separación |
| [`03_plan_de_pruebas_permisos.md`](03_plan_de_pruebas_permisos.md) | Niveles de prueba, casos y criterios de aceptación |
| [`policy/permisos.yaml`](policy/permisos.yaml) | Fuente de verdad de roles, permisos, condiciones y asignaciones |
| [`policy/generar_matriz.py`](policy/generar_matriz.py) | Valida la política y verifica que la matriz del documento coincida con el YAML |
| [`04_capacidades_del_switch.md`](04_capacidades_del_switch.md) | Estimación y verificación de las capacidades del switch del slice |
| [`05_plan_de_implementacion.md`](05_plan_de_implementacion.md) | Plan de despliegue, servicios, orquestación y hitos |
| [`03_permisos.md`](../docs/fases/A-Modelo_de_dominio/03_permisos.md) | Catálogo de la fase A, actualizado a P01–P36 |

Las etapas siguientes se planifican en [`04_capacidades_del_switch.md`](04_capacidades_del_switch.md), [`05_plan_de_implementacion.md`](05_plan_de_implementacion.md), [`06_plan_de_trabajo_etapa_2.md`](06_plan_de_trabajo_etapa_2.md) y [`07_plan_de_trabajo_etapa_3.md`](07_plan_de_trabajo_etapa_3.md); el mapa completo está en [`README.md`](README.md).
