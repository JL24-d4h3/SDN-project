# Modelo de contexto, estado de seguridad y vigencia

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Etapa 0
**Estado:** Borrador formal para revisión

---

## 1. Definición del permiso efectivo

El permiso efectivo no es una suma de atributos. Es el resultado de una evaluación en la que cada eje puede habilitar, acotar o anular la decisión:

```text
PERMISO EFECTIVO = SUJETO × ACCIÓN × RECURSO × CONTEXTO × ESTADO DE SEGURIDAD × VIGENCIA
```

| Eje | Pregunta que responde | Quién lo aporta |
|---|---|---|
| Sujeto | ¿Quién solicita y con qué identidad, rol, dispositivo y factores? | IAM, registro de dispositivos, sesión |
| Acción | ¿Qué permiso Pxx y qué verbo concreto se solicita? | Petición I7 o comando I2 |
| Recurso | ¿Sobre qué objeto, de qué tipo, con qué propietario y clasificación? | Catálogo de recursos, servicio destino |
| Contexto | ¿En qué circunstancias se solicita? | Sesión, red, tiempo, ubicación, recurso |
| Estado de seguridad | ¿El sujeto o el entorno están en una condición que impide conceder? | Detección, incidentes, cuarentena, IAM |
| Vigencia | ¿La autorización sigue siendo válida y hasta cuándo? | TTL, expiración, ventana de mantenimiento |

Los ejes no son intercambiables. Un contexto favorable no compensa un estado de seguridad comprometido; una vigencia expirada no se renueva por tener el rol correcto.

**Tipos de sujeto.** El modelo autoriza personas. Un servicio no recibe un rol humano: se autentica con su propia credencial y se autoriza por el contrato de su interfaz (mTLS, credencial de servicio y lista cerrada de operaciones). Un dispositivo tampoco es sujeto: es un atributo del sujeto persona (`device_id`, `device_trust`). Las identidades de servicio y sus secretos pertenecen a la seguridad de la plataforma, no a esta matriz.

## 2. Contexto

El contexto se divide en tres subdimensiones. Cada una tiene atributos propios, se evalúa en momentos distintos y puede proceder de fuentes distintas.

### 2.1 Contexto de sesión

Describe la sesión autenticada del sujeto.

| Atributo | Valores | Fuente |
|---|---|---|
| `session_id` | identificador opaco | IAM |
| `channel` | portal, consola, API, SSH, VPN | IAM / portal |
| `auth_method` | password, TOTP, certificado, break-glass | IAM |
| `mfa_verified` | verdadero / falso | IAM |
| `session_age_s` | segundos desde la autenticación | IAM |
| `device_id` | identificador del dispositivo registrado | Registro de dispositivos |
| `device_trust` | registrado, no registrado, cuarentena | Registro / Detección |
| `concurrent_sessions` | número de sesiones activas del sujeto | IAM |
| `privileged` | verdadero si la sesión es operativa | IAM |

El contexto de sesión es obligatorio para todo permiso de servicios. Sin sesión válida solo se evalúan P01 y las acciones de pre-sesión.

### 2.2 Contexto ambiental

Describe dónde y cuándo se solicita.

| Atributo | Valores | Fuente |
|---|---|---|
| `location` | campus, remoto, VPN, desconocido | Borde / portal |
| `switch_id`, `port_id` | identificador del punto de conexión | Controlador |
| `vlan` | 10, 20, 30, 100 | Controlador |
| `zone` | acceso, distribución, núcleo, servicios, gestión, externa | Topología |
| `time_window` | horario académico, horario administrativo, mantenimiento, fuera de ventana | chrony / política |
| `origin_ip` | dirección de origen observada | Controlador |
| `maintenance_mode` | verdadero / falso | Políticas |
| `network_profile` | BASE, ACADÉMICO, OPERADOR_*, ELEVACIÓN | Controlador |

El contexto ambiental se evalúa en el Policy Engine y, para las decisiones de red, en el controlador.

### 2.3 Contexto de recurso

Describe el objeto sobre el que se actúa.

| Atributo | Valores | Fuente |
|---|---|---|
| `resource_type` | servicio, host, switch, segmento, política, alerta, incidente, sesión, cuenta, clave | Catálogo |
| `resource_id` | identificador estable | Servicio destino |
| `owner` | identidad o unidad propietaria | Catálogo |
| `classification` | público, interno, restringido, crítico | Catálogo |
| `sensitivity` | baja, media, alta | Catálogo |
| `state` | activo, en mantenimiento, en cuarentena, retirado | Servicio / controlador |
| `scope` | ámbito al que pertenece el recurso | Catálogo |

El contexto de recurso impide que un permiso sobre un tipo se aplique a cualquier instancia. El permiso se concede sobre un recurso concreto, no sobre una categoría abierta.

### 2.4 Lo que no es contexto

No forman parte del contexto y se mantienen como ejes separados:

- **El estado de seguridad del sujeto y del entorno.** Puede anular la decisión; no es una circunstancia que se pondere.
- **La vigencia.** Es una condición temporal de la autorización, no una propiedad del entorno.
- **El rol.** Es una etiqueta del sujeto, no un atributo de la sesión.
- **El perfil de red.** Es el resultado de una decisión de red, no una entrada del contexto de servicios.

## 3. Estado de seguridad

El estado de seguridad es una condición evaluada antes de las reglas de permiso. Se divide en dos ámbitos.

### 3.1 Estado del sujeto

| Estado | Significado | Efecto |
|---|---|---|
| `normal` | sin hallazgos | evalúa reglas |
| `sospechoso` | anomalía o alerta de baja severidad | exige step-up o limita acciones |
| `comprometido` | evidencia de compromiso | deniega permisos privilegiados; permite acciones de respuesta |
| `cuarentena` | sujeto o dispositivo aislado | solo portal y acciones de remediación |
| `suspendido` | cuenta o dispositivo suspendido | deniega todo salvo P01 |

### 3.2 Estado del entorno

| Estado | Significado | Efecto |
|---|---|---|
| `normal` | sin incidente activo | evalúa reglas |
| `incidente_activo` | incidente abierto que afecta al recurso o a su ámbito | eleva el nivel de aprobación; puede denegar |
| `segmento_aislado` | segmento en cuarentena | deniega acceso al segmento; permite respuesta |
| `modo_emergencia` | procedimiento de emergencia declarado | habilita el procedimiento y exige auditoría reforzada |
| `mantenimiento` | ventana de mantenimiento | permite cambios planificados; deniega operaciones no previstas |

### 3.3 Regla de anulación

El estado de seguridad se evalúa como restricción dura:

```text
si estado_sujeto ∈ {comprometido, cuarentena, suspendido}
   y la acción no es de respuesta o remediación
   → DENEGAR

si estado_entorno = segmento_aislado
   y el recurso pertenece al segmento
   → DENEGAR salvo acción de respuesta

si estado_entorno = incidente_activo
   y la acción es de alto impacto
   → exigir P32 y aprobación humana

si estado_sujeto = sospechoso
   y la acción es privilegiada
   → ELEVAR (step-up) o DENEGAR si no es posible
```

El estado de seguridad no se pondera con el contexto: se aplica antes y por encima.

## 4. Vigencia

La vigencia delimita el tiempo durante el cual la autorización es válida.

| Tipo | Atributo | Ejemplo |
|---|---|---|
| Sesión | `session_max_age_s` | 8 h para académico, 4 h para operador |
| Elevación | `ttl_s` | 30 min para laboratorio, 60 min para diagnóstico |
| Mitigación | `ttl_s` | 15 min para cuarentena temporal |
| Aprobación | `approval_expires_at` | 10 min para confirmar una acción crítica |
| Delegación | `valid_from`, `valid_until` | 90 días para registro de TI |
| Ventana | `time_window` | mantenimiento programado |

Reglas:

- Toda elevación y toda mitigación exigen TTL explícito.
- La aprobación de P32 expira si no se ejecuta en la ventana.
- Una delegación vencida no se renueva automáticamente.
- La sesión expirada se trata como ausente: no se evalúan permisos de servicios.

## 5. Pipeline de decisión

```text
Petición
  │
  ├─ 1. ¿Sesión válida? ─────────────── no → DENEGAR (o permitir P01)
  │
  ├─ 2. ¿Sujeto y recurso identificados? ─ no → DENEGAR
  │
  ├─ 3. Estado de seguridad del sujeto ── anulación → DENEGAR / ELEVAR
  │
  ├─ 4. Estado de seguridad del entorno ─ anulación → DENEGAR / exigir P32
  │
  ├─ 5. Buscar reglas para (rol, Pxx, recurso)
  │       │
  │       ├─ sin regla → DENEGAR (default deny)
  │       ├─ regla deny → DENEGAR (deny-overrides)
  │       └─ regla permit → continúa
  │
  ├─ 6. Evaluar condiciones de contexto
  │       │
  │       ├─ condición falla → DENEGAR o ELEVAR según la condición
  │       └─ condición cumple → continúa
  │
  ├─ 7. Evaluar vigencia
  │       │
  │       ├─ expirada → DENEGAR
  │       └─ vigente → continúa
  │
  ├─ 8. Aplicar obligaciones (auditar, notificar, TTL, aprobación)
  │
  └─ 9. Decisión: PERMITIR / DENEGAR / ELEVAR / CUARENTENA
```

El pipeline se ejecuta en el Policy Engine para las decisiones de servicio y en el controlador para las decisiones de red. Ambos comparten el mismo archivo de políticas y la misma semántica.

## 6. Semántica de decisión

| Decisión | Significado | Efecto |
|---|---|---|
| `PERMITIR` | la acción se autoriza con las obligaciones aplicables | se ejecuta y se audita |
| `DENEGAR` | la acción no se autoriza | se rechaza y se registra el motivo |
| `ELEVAR` | se requiere un paso adicional | MFA, aprobación P32 o justificación |
| `CUARENTENA` | la acción se sustituye por una medida de contención | se aplica la política de cuarentena |

`ELEVAR` no es un permiso: es una respuesta que indica qué falta para completar la evaluación. Si el paso adicional no se completa, la decisión final es `DENEGAR`.

## 7. Ejemplos completos

### 7.1 Académico accede a un servicio académico

```text
SUJETO:     rol académico, sesión válida, dispositivo registrado
ACCIÓN:     P03 acceder a servicio
RECURSO:    servicio_academico, clasificación interno
CONTEXTO:   sesión de portal, campus, VLAN 10, horario académico
ESTADO:     sujeto normal, entorno normal
VIGENCIA:   sesión vigente
DECISIÓN:   PERMITIR con obligación de auditar
```

### 7.2 Especialista de TI ejecuta una mitigación

```text
SUJETO:     rol TI, sesión privilegiada con MFA, dispositivo registrado
ACCIÓN:     P12 ejecutar mitigación
RECURSO:    nodo del segmento de usuarios
CONTEXTO:   consola, VLAN 100, ventana administrativa
ESTADO:     sujeto normal, entorno con incidente activo
VIGENCIA:   TTL de 15 min
DECISIÓN:   PERMITIR si la acción es de bajo impacto; ELEVAR (P32) si es de alto impacto
```

### 7.3 Administrador aprueba una cuarentena

```text
SUJETO:     rol administrador, sesión privilegiada con MFA
ACCIÓN:     P32 aprobar acción de alto impacto
RECURSO:    solicitud de cuarentena de un segmento
CONTEXTO:   consola, ámbito del administrador
ESTADO:     sujeto normal, entorno con incidente activo
VIGENCIA:   aprobación válida por 10 min
DECISIÓN:   PERMITIR si el solicitante es distinto del aprobador; DENEGAR si es el mismo
```

### 7.4 Superadministrador configura el controlador

```text
SUJETO:     rol superadministrador, sesión privilegiada con MFA
ACCIÓN:     P22-CFG configurar el controlador
RECURSO:    controlador_sdn
CONTEXTO:   consola, VLAN 100, ventana de mantenimiento
ESTADO:     sujeto normal, entorno normal
VIGENCIA:   sesión vigente
DECISIÓN:   PERMITIR con obligaciones de auditar y registrar el cambio
```

### 7.5 Sujeto en cuarentena intenta acceder a un servicio

```text
SUJETO:     rol académico, dispositivo en cuarentena
ACCIÓN:     P03 acceder a servicio
RECURSO:    servicio_academico
CONTEXTO:   portal, VLAN 10
ESTADO:     sujeto en cuarentena
VIGENCIA:   sesión vigente
DECISIÓN:   DENEGAR; solo se permite el portal de remediación
```

## 8. Atributos obligatorios y fallo seguro

Si falta un atributo marcado como obligatorio, la evaluación no concede:

| Atributo faltante | Resultado |
|---|---|
| `session_id` o sesión expirada | DENEGAR |
| `role` del sujeto | DENEGAR |
| `resource_id` o `resource_type` | DENEGAR |
| `device_trust` para acción privilegiada | ELEVAR o DENEGAR |
| `security_state` del sujeto | DENEGAR si la acción es privilegiada |
| `security_state` del entorno | DENEGAR si la acción es de alto impacto |
| `ttl` para elevación o mitigación | DENEGAR |

El fallo seguro no se implementa como excepción no controlada: se implementa como decisión `DENEGAR` con motivo `atributo_faltante`, registrada en auditoría.

## 9. Relación con los perfiles de red

La decisión de red es un caso particular del pipeline:

1. El sujeto se autentica (P01).
2. El Policy Engine evalúa P02 con el contexto de sesión, ambiental y de recurso.
3. El resultado es un perfil: BASE, ACADÉMICO, OPERADOR_TI, OPERADOR_ADMIN, OPERADOR_SA o ELEVACIÓN(scope, TTL).
4. El controlador traduce el perfil a reglas y prioridades en el switch.
5. El estado de seguridad puede degradar el perfil a BASE o a cuarentena sin cambiar la identidad del sujeto.

El perfil no es un permiso de servicio. Un operador con perfil OPERADOR_ADMIN sigue necesitando P22-OP para operar el controlador y P32 para aprobar una acción crítica.

## 10. Trazabilidad

| Concepto | Artefacto |
|---|---|
| Catálogo de permisos | [`03_permisos.md`](../docs/fases/A-Modelo_de_dominio/03_permisos.md) |
| Matriz Rol × Permiso | [`02_matriz_rol_permiso.md`](02_matriz_rol_permiso.md) |
| Política ejecutable | [`policy/permisos.yaml`](policy/permisos.yaml) |
| Pruebas | [`03_plan_de_pruebas_permisos.md`](03_plan_de_pruebas_permisos.md) |
| Decisión de red y perfiles | [`../access/02_autorizacion_por_capas.md`](../access/02_autorizacion_por_capas.md) |
