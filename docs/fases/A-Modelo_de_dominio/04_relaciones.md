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
