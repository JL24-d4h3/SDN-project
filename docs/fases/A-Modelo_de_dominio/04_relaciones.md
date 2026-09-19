# Modelo de Dominio — Relaciones entre Entidades

## 1. Objetivo

Definir las relaciones estructurales entre actores, roles, permisos, recursos y servicios de la solución SDN.

## 2. Relaciones principales

### 2.1 Actor → Rol

**Un actor humano puede desempeñar un rol dentro de la plataforma.**

```text
Actor ── desempeña ──> Rol
```

Ejemplos:

```text
Alumno ──> Alumno
Docente ──> Docente
Especialista de TI ──> Especialista de TI
Administrador de Red ──> Administrador de Red
Superadministrador ──> Superadministrador
```

Un mismo individuo podría tener más de un rol si la política de la plataforma lo permite, pero los privilegios efectivos deben determinarse de manera explícita.

---

### 2.2 Rol → Permiso

**Un rol posee uno o más permisos.**

```text
Rol ── posee/concede ──> Permiso
```

Ejemplos:

```text
Alumno ──> Autenticarse
Alumno ──> Acceder a la red
Alumno ──> Acceder a servicio

Especialista de TI ──> Consultar alertas
Especialista de TI ──> Analizar incidente
Especialista de TI ──> Gestionar alerta

Administrador de Red ──> Gestionar políticas de acceso
Administrador de Red ──> Gestionar reglas de red
Administrador de Red ──> Gestionar dispositivos

Superadministrador ──> Gestionar administradores
Superadministrador ──> Gestionar permisos
Superadministrador ──> Gestionar configuración global
```

---

### 2.3 Permiso → Recurso

**Un permiso determina qué acción puede realizarse sobre un recurso.**

```text
Permiso ── se aplica sobre ──> Recurso
```

Ejemplos:

```text
Consultar recurso ──> Servidor de notas
Gestionar reglas de red ──> Reglas de red
Gestionar dispositivos de red ──> Switch SDN
Gestionar controlador SDN ──> Controlador SDN
Consultar logs ──> Logs de seguridad
```

La relación debe especificar, cuando corresponda, el alcance del recurso.

---

### 2.4 Permiso → Servicio

**Un permiso puede habilitar una acción sobre un servicio.**

```text
Permiso ── habilita ──> Servicio
```

Ejemplos:

```text
Acceder a servicio ──> Servicio académico
Ejecutar operación ──> Servicio de notas
Consultar alertas ──> Servicio de monitoreo
Gestionar políticas de acceso ──> Servicio de administración SDN
```

---

### 2.5 Rol → Recurso/Servicio

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
Alumno ──> Servidor de notas
```

sin especificar qué puede hacer el alumno sobre dicho servidor.

---

### 2.6 Recurso → Servicio

**Un servicio puede depender de uno o más recursos, y un recurso puede soportar uno o más servicios.**

```text
Servicio ── utiliza/depende de ──> Recurso
```

Ejemplo:

```text
Servicio de notas
    ├── depende de ──> Servidor de notas
    ├── depende de ──> Base de datos académica
    └── depende de ──> Segmento de servidores
```

---

## 3. Relaciones de seguridad y administración

### 3.1 Actor → Recurso/Servicio

El acceso de un actor a un recurso o servicio **no debe considerarse una relación directa permanente**.

Debe resolverse mediante autorización:

```text
Actor
  ↓
Rol
  ↓
Permiso
  ↓
Recurso/Servicio
  ↓
Política de acceso
  ↓
Decisión: PERMITIR / DENEGAR
```

---

### 3.2 Evento/Alerta → Incidente

Cuando un evento de seguridad satisface las condiciones definidas por las políticas de detección:

```text
Evento ── puede generar ──> Alerta
Alerta ── puede derivar en ──> Incidente
```

---

### 3.3 Incidente → Mitigación

Un incidente puede desencadenar una acción de respuesta:

```text
Incidente ── desencadena ──> Mitigación
```

Ejemplo:

```text
Detección de port scanning
        ↓
      Alerta
        ↓
    Incidente
        ↓
 Aislar nodo / bloquear tráfico
```

---

### 3.4 Nodo → Tráfico

```text
Nodo ── genera ──> Tráfico
```

El tráfico puede ser observado y analizado por los mecanismos de seguridad.

```text
Tráfico
   ↓
IDS/IPS / mecanismos de monitoreo
   ↓
Evento / Alerta
```

---

## 4. Relación de administración jerárquica

La administración de privilegios debe reflejar la jerarquía definida:

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
       ├── administra ──> Usuarios
       ├── administra ──> Políticas
       ├── administra ──> Reglas de red
       └── administra ──> Dispositivos
```

El Especialista de TI administra principalmente el ciclo de seguridad:

```text
Especialista de TI
       ├── supervisa ──> Eventos
       ├── analiza ──> Alertas
       ├── gestiona ──> Incidentes
       └── ejecuta ──> Mitigaciones autorizadas
```

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
                       /                        se aplica a     habilita
                    /                                 ▼                ▼
               RECURSO          SERVICIO
                   ▲                │
                   │                │
                   └──── depende ───┘

NODO ── genera ──> TRÁFICO
                     │
                  analiza
                     ▼
             IDS/IPS / MONITOREO
                     │
                  genera
                     ▼
                  ALERTA
                     │
                  deriva en
                     ▼
                 INCIDENTE
                     │
                 desencadena
                     ▼
                 MITIGACIÓN
                     │
             modifica/restringe
                     ▼
               RED / NODO / TRÁFICO
```

## 6. Regla central de autorización

La relación fundamental del modelo debe entenderse como:

```text
Actor
  → Rol
  → Permiso
  → Recurso/Servicio
  → Política/Condiciones
  → Decisión de acceso
```

Por tanto, **tener un rol no significa tener acceso absoluto**. El acceso efectivo resulta de la combinación entre el rol, los permisos asignados, el recurso o servicio solicitado y las políticas y condiciones de seguridad vigentes.