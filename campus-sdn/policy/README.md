# La política de permisos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Contratos
**Estado:** Borrador formal para revisión

---

[`permissions.yaml`](permissions.yaml) es la copia operativa de la etapa 0, con los valores de dominio en inglés. El corpus conserva el modelo en español ([`implementation/policy/permisos.yaml`](../../implementation/policy/permisos.yaml)) y ambas copias se cambian juntas y versionadas; las pruebas de contrato verifican que sigan sincronizadas en estructura. Los nombres, descripciones y notas se mantienen en español en ambas: son texto para personas, no identificadores.

## 1. Correspondencia de valores

### 1.1 Roles

| Corpus (español) | Repositorio (inglés) |
|---|---|
| `academico` | `academic` |
| `especialista_ti` | `it_specialist` |
| `administrador_red` | `network_admin` |
| `superadministrador` | `super_admin` |

### 1.2 Perfiles y alias

| Corpus | Repositorio |
|---|---|
| `academico` | `academic` |
| `operador_ti` | `it_operator` |
| `operador_admin` | `admin_operator` |
| `operador_sa` | `sa_operator` |
| `elevacion` | `elevation` |
| instancia `laboratorio` | `laboratory` |
| tipo `fijo` / `derivado` / `parametrizado` | `fixed` / `derived` / `parameterized` |
| alias `TI` / `ADMIN_RED` | `IT` / `NETWORK_ADMIN` |

### 1.3 Planos y estados

| Corpus | Repositorio |
|---|---|
| plano `pre_sesion` / `red` / `servicios` | `pre_session` / `network` / `services` |
| `sospechoso` / `comprometido` / `cuarentena` / `suspendido` | `suspicious` / `compromised` / `quarantine` / `suspended` |
| `incidente_activo` / `segmento_aislado` / `modo_emergencia` / `mantenimiento` | `active_incident` / `isolated_segment` / `emergency_mode` / `maintenance` |
| `respuesta` / `remediacion` (exceptuados) | `response` / `remediation` |

### 1.4 Tipos de recurso

| Corpus | Repositorio | Corpus | Repositorio |
|---|---|---|---|
| `servicio_academico` | `academic_service` | `recurso_red` | `network_resource` |
| `servicio_publico` | `public_service` | `alerta` / `alerta_red` | `alert` / `network_alert` |
| `servicio_seguridad` | `security_service` | `incidente` / `incidente_red` | `incident` / `network_incident` |
| `recurso_propio` | `own_resource` | `log_seguridad` / `log_operativo` | `security_log` / `operational_log` |
| `recurso_seguridad` | `security_resource` | `evento` / `metrica` / `trafico` | `event` / `metric` / `traffic` |
| `red_gestion` | `management_network` | `controlador_sdn` | `sdn_controller` |
| `dispositivo_red` | `network_device` | `segmento` / `vlan` | `segment` / `vlan` |
| `regla_red` / `flujo` | `network_rule` / `flow` | `politica_acceso` / `politica_seguridad` | `access_policy` / `security_policy` |
| `perfil` / `regla_deteccion` | `profile` / `detection_rule` | `regla_mitigacion` / `mitigacion` | `mitigation_rule` / `mitigation` |
| `deteccion` / `nodo` | `detection` / `node` | `umbral_deteccion` / `rango_umbral` | `detection_threshold` / `threshold_range` |
| `cuenta_local` / `cuenta_local_ti` | `local_account` / `local_it_account` | `cuenta_administrativa` / `cuenta_administrativa_ti` | `administrative_account` / `administrative_it_account` |
| `rol` / `permiso` | `role` / `permission` | `solicitud_elevacion` | `elevation_request` |
| `solicitud_accion_critica` | `critical_action_request` | `solicitud_registro_dispositivo` | `device_registration_request` |
| `dispositivo_privilegiado` / `dispositivo_privilegiado_ti` | `privileged_device` / `privileged_it_device` | `sesion` / `auditoria` | `session` / `audit` |
| `configuracion_global` / `configuracion` | `global_configuration` / `configuration` | `plataforma` / `clave_certificado` | `platform` / `key_certificate` |
| `consola` / `api_seguridad` / `api_red` | `console` / `security_api` / `network_api` | `operacion_red` / `respuesta_autorizada` | `network_operation` / `authorized_response` |

### 1.5 Obligaciones y prioridades

| Corpus | Repositorio | Corpus | Repositorio |
|---|---|---|---|
| `auditar` | `audit` | `notificar` | `notify` |
| `justificar` | `justify` | `registrar_cambio` | `record_change` |
| `vincular_aprobacion` | `link_approval` | `registrar_valores` | `record_values` |
| `no_registrar_secreto` | `no_secret_logging` | `mitigacion` | `mitigation` |
| `sesion_privilegiada` | `privileged_session` | `mac_ip_correctos` | `correct_mac_ip` |
| `ip_con_mac_ajena` | `ip_with_foreign_mac` | `gestion_drop` | `management_drop` |
| `caminos` | `paths` | `sesion_academica` | `academic_session` |

### 1.6 Lo que no se tradujo

- Los IDs **P01–P36, C1–C11, HC-01–04, A001–A034, T001–T015, R001–R025, S001–S034, R-SOD/DEL/CFG/DET/AUD/BG/REG y D-TI-01** son idénticos en ambas copias: son neutrales al idioma.
- `name` va en inglés en el repositorio y sin tildes (`ACADEMIC`, `ELEVATION`, `IT_OPERATOR`, `ADMINISTRATOR_OPERATOR`, `SUPER_ADMINISTRATOR_OPERATOR`); el corpus conserva las etiquetas en español. El rol antes llamado «Especialista de TI» pasa a **IT Operator** («Operador en TI»); su identificador sigue siendo `it_specialist`.
- `description`, `population` y `notes` quedan en español en ambas copias: son prosa para personas.
- Los predicados y condiciones van en inglés en ambas copias.

## 2. Archivos de esta capa

| Archivo | Papel |
|---|---|
| [permissions.yaml](permissions.yaml) | Fuente de verdad operativa (valores en inglés) |
| [permissions.schema.json](../contracts/policy/permissions.schema.json) | La forma estructural que el YAML debe cumplir |
| [tools/validate.py](tools/validate.py) | Valida forma e integridad referencial |
| [tools/generate_matrix.py](tools/generate_matrix.py) | Genera la matriz rol × permiso y la compara con el corpus |
