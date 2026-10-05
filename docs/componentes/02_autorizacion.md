# Elementos de autorización

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Componentes del sistema — 2 de 6
**Estado:** Borrador formal para revisión

---

Qué vive dentro de cada pieza que responde a la pregunta **"¿qué puedes hacer?"**: los dos planos de autorización (servicios y red), el RBAC de los servicios y el motor de condiciones ABAC-like del Policy Engine. La autenticación está en [`01_autenticacion.md`](01_autenticacion.md); el mapa general, en [`00_mapa_de_componentes.md`](00_mapa_de_componentes.md).

## 1. Los dos planos de autorización

```text
                 identidad + rol + dispositivo (viene del IAM — doc 01)
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
 ┌─ PLANO DE SERVICIOS ──────────────┐   ┌─ PLANO DE RED ─────────────────────┐
 │  RBAC                             │   │  motor ABAC-like (Policy Engine)   │
 │  rol → permisos P01–P30           │   │  condiciones + vigencia (TTL)      │
 │  se aplica en cada servicio       │   │  decide el perfil de cada sesión   │
 │  (valida la API, no la consola)   │   │  y las elevaciones                 │
 └───────────────────────────────────┘   └───────────────┬────────────────────┘
                                                         │ orden northbound (I2)
                                                         ▼
                                          Controlador → FLOW_MOD en switches
```

- **Plano de servicios:** ¿qué puede hacer este rol *dentro* de la plataforma? (consultar incidentes, aprobar elevaciones, registrar dispositivos…). Modelo **RBAC**.
- **Plano de red:** ¿qué conectividad obtiene esta sesión? (qué destinos alcanza, con qué prioridad, hasta cuándo). Modelo **ABAC-like**.
- Son complementarios: la red distingue roles para la conectividad; los permisos finos distinguen dentro de lo conectado (doc 06 §6, doc 07).

Ni RBAC ni ABAC son componentes: son **modelos de decisión** que viven dentro de piezas ya existentes.

## 2. Plano de servicios: RBAC — qué vive dentro

```text
┌─ RBAC ───────────────────────────────────────────────────────────────────┐
│                                                                          │
│  roles (4):  académico · Especialista de TI · Administrador de Red ·     │
│              Superadministrador                                          │
│                                                                          │
│  catálogo de permisos P01–P30 (fase A), por niveles:                     │
│    acceso           P01–P05, P28   autenticarse, red, servicio, elevar  │
│    supervisión      P06–P13, P25   observar, mitigar, auditar            │
│    administración   P14–P23, P27, P29, P30                               │
│    control maestro  P24, P26                                             │
│                                                                          │
│  dónde se aplica:   en cada SERVICIO, al validar cada petición de la API │
│  dónde NO:          la consola solo renderiza según el rol;              │
│                     no es el guardián (el servicio valida, I7)           │
└──────────────────────────────────────────────────────────────────────────┘
```

Reglas de asignación que el RBAC respeta (fase A §3):

- Un permiso se concede explícitamente; **poseer un rol no implica acceso irrestricto**.
- El acceso efectivo = rol + permiso + recurso/servicio + política + contexto + vigencia.
- Los permisos administrativos se mantienen separados de los de usuario final.
- Operaciones críticas → auditadas; mitigaciones → sujetas a política.

La asignación definitiva rol × permiso es la **matriz Rol × Permiso** de la fase A (pendiente de completar).

## 3. Plano de red: el motor ABAC-like — qué vive dentro del Policy Engine

```text
┌─ Policy Engine ──────────────────────────────────────────────────────────┐
│                                                                          │
│  motor de condiciones (ABAC-like)                                        │
│    evalúa una tupla de atributos:                                        │
│      identidad + dispositivo + ubicación + contexto                      │
│      + recurso + acción + vigencia                                       │
│    entradas: IncidentOpened, ElevationRequested, consultas del IAM       │
│                                                                          │
│  PolicyRepository                                                        │
│    políticas de acceso    (qué perfil corresponde a qué caso)            │
│    políticas de mitigación (escalera por severidad: RATE_LIMIT →         │
│                             BLOCK_SOURCE → ISOLATE_DEVICE → QUARANTINE)  │
│                                                                          │
│  PermissionRepository                                                    │
│    elevaciones concedidas: alcance + TTL + responsable                   │
│                                                                          │
│  programador de expiraciones (TTL)                                       │
│    ElevationExpired · retiro de mitigaciones                             │
│                                                                          │
│  decide — no ejecuta:                                                    │
│    MitigationRequired  → controlador (comando, I2) + Auditoría           │
│    ElevationGranted / ElevationExpired → controlador + Auditoría         │
└──────────────────────────────────────────────────────────────────────────┘
```

Lo que el Policy Engine **no** hace (doc 06): observar tráfico, ejecutar la decisión, administrar usuarios. Decide con contexto y vigencia; la ejecución es del controlador y del switch.

## 4. Los perfiles: la autorización de red, materializada

Un **perfil** es el conjunto de reglas que un dispositivo tiene instaladas en su switch de ingreso. No se "asigna" en abstracto: se materializa como FLOW_MOD con prioridad, cookie y timeout.

| Perfil | Quién lo recibe | Vigencia | Qué obtiene en la red |
|---|---|---|---|
| **BASE** | todo dispositivo conectado, antes de cualquier login | mientras está conectado | mínimo: DHCP, DNS y portal. Deny by default hacia la red de gestión |
| **ACADÉMICO** | usuario académico, tras autenticarse | sesión (idle_timeout) | servicios académicos e Internet, con la sesión atribuida a una identidad |
| **LABORATORIO** | académico con elevación aprobada (P28/P29) | TTL de la elevación | segmento o servicios del laboratorio, solo lo aprobado |
| **TI** | Especialista de TI autenticado | sesión | consola y APIs puntuales (entradas prioridad 200 acotadas) |
| **ADMIN_RED** | Administrador autenticado | sesión | toda la red de gestión (10.0.0.0/24) |
| **SUPER_ADMIN** | Superadministrador autenticado | sesión | igual que admin + acceso remoto (regla instalada en el switch del borde) |

Todos los perfiles se materializan igual: el Policy Engine decide, el controlador traduce a FLOW_MOD, el switch ejecuta y expira por timeout (P10).

## 5. De la sesión a la regla: el recorrido completo

```text
login OK (doc 01)
   → el IAM entrega al Policy Engine: identidad + rol + dispositivo + puerto
   → el Policy Engine evalúa las condiciones (¿rol? ¿dispositivo registrado?
     ¿contexto? ¿vigencia?) contra PolicyRepository y PermissionRepository
   → decisión: perfil + vigencia   (o denegación, también registrada)
   → orden northbound al controlador (I2), aplicada con confirmación
   → FLOW_MOD en el switch de ingreso: prioridad de sesión, cookie, idle_timeout
   → evento a la Auditoría: quién, qué, cuándo, por qué
```

La autorización **se cumple en el switch**, no en la consola ni en el portal: aunque alguien conociera una contraseña válida, sin la decisión del Policy Engine no hay reglas, y sin reglas no hay conectividad.

## 6. Dónde vive cada pieza

| Pieza | Dónde vive | Quién la evalúa | Qué produce |
|---|---|---|---|
| Roles y permisos P01–P30 (RBAC) | en los servicios (validación por API) | cada servicio, en cada petición | permitir/denegar una operación de plataforma |
| Políticas de acceso (ABAC-like) | Policy Engine — PolicyRepository | Policy Engine | perfil y vigencia de cada sesión |
| Elevaciones y sus TTL | Policy Engine — PermissionRepository | Policy Engine | ElevationGranted / ElevationExpired |
| Perfil efectivo de una sesión | reglas en los switches (decididas por Policy, traducidas por el controlador) | el switch, por prioridad | conectividad concreta (ALLOW/DROP/meter) |
| Mitigaciones | decide el Policy Engine; ejecuta el switch | Policy Engine → controlador | meter/drop temporales con cookie |
| Escalera de prioridades | pipeline de cada switch | el switch | orden de precedencia entre perfiles, mitigaciones y portal |

La **escalera de prioridades** (mitigación 1000 → sesión privilegiada 200 → portal 150 → par MAC/IP 120 → IP con MAC ajena 110 → gestión 100 → DHCP/DNS 10 → sesión académica) es el punto donde los dos planos se vuelven uno solo: cada perfil es un peldaño. El valor exacto del peldaño académico se fija al implementar (§7; ver [`flows/diagrams/04_flujo_usuario_generico.md`](../../flows/diagrams/04_flujo_usuario_generico.md) §6).

## 7. Cuestiones abiertas

- **Matriz Rol × Permiso definitiva** (fase A): la asignación completa de P01–P30 a los 4 roles.
- **Peldaño de la sesión académica** en la escalera de prioridades: valor exacto al implementar.
- **Alcance del motor ABAC-like:** el motor evalúa una tupla fija de atributos; un motor XACML completo sería complejidad injustificada (P4). Confirmar que basta.
- **Vigencia por defecto** de cada perfil (idle_timeout concreto): Fase F, con mediciones.

Documentos relacionados: [`06_responsabilidades.md`](../fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/06_responsabilidades.md) (quién puede qué, por componente), [`03_permisos.md`](../fases/A-Modelo_de_dominio/03_permisos.md) (catálogo P01–P30) y [`03_flujo_autenticacion_autorizacion.md`](../../flows/03_flujo_autenticacion_autorizacion.md) (mecánica a nivel de red).
