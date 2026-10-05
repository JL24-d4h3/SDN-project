# Mapa de componentes

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Componentes del sistema — 0 de 6
**Estado:** Borrador formal para revisión

---

Vista general del sistema: qué cajas existen, qué vive **dentro** de cada una y qué queda fuera. Es el mapa sobre el que hacen zoom los documentos [01 (autenticación)](01_autenticacion.md), [02 (autorización)](02_autorizacion.md), [03 (seguridad)](03_seguridad.md), [04 (identidades y poblaciones)](04_identidades_y_poblaciones.md) y [05 (historial de dispositivo)](05_historial_de_dispositivo.md). La descomposición formal está en [`04_descomposición_arquitectonica.md`](../fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/04_descomposición_arquitectonica.md); aquí se dibuja.

## 1. Las tres zonas

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  BORDE EXTERNO — se atiende, no se administra                            │
│    personas:  académico · TI · Admin de Red · Superadministrador         │
│    sistemas:  IdP institucional (SE-02, externo)                         │
│    clientes:  consola de administración                                  │
└─────────────┬─────────────────────────┬──────────────────┬───────────────┘
              │ I3 portal (HTTPS)       │ I4 identidad     │ I7 API admin
              ▼                         ▼                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  PLATAFORMA DE SEGURIDAD (servicios)                                     │
│    IAM/AAA (con portal) · Registro de dispositivos · Monitor ·           │
│    Detección · Incidentes · Políticas · Auditoría                        │
│    infraestructura interna: broker de eventos (I5)                       │
└─────────────┬────────────────────────────────────────────────────────────┘
              │ I2 northbound (órdenes de política)
              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  NÚCLEO SDN                                                              │
│    Controlador SDN ───── I1 OpenFlow ─────► Switches (plano de datos)    │
└──────────────────────────────────────────────────────────────────────────┘
```

- La **plataforma** son servicios: responsabilidad única, datos propios, contrato por eventos.
- El **núcleo SDN** no son servicios: el controlador traduce decisiones a reglas y los switches las ejecutan (P1).
- El **borde** no se administra: las personas se atienden por el portal y el IdP se consulta, nunca se toca.

## 2. Dentro de cada caja

### 2.1 Servicios de la plataforma

```text
┌─ IAM/AAA ────────────────────────────────────────────────────────────────┐
│  portal cautivo web (la interfaz I3)                                     │
│  orquestador de autenticación          gestor de sesiones                │
│  cliente AAA/directorio (la interfaz I4)   accounting                    │
│  publica → SessionOpened / SessionClosed                                 │
│  repositorio de identidades privilegiadas (operadores) — doc 04          │
│  no almacena credenciales académicas (viven en el IdP)                   │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Políticas (Policy Engine) ──────────────────────────────────────────────┐
│  motor de condiciones ABAC-like                                          │
│    identidad + dispositivo + ubicación + contexto + recurso              │
│    + acción + vigencia                                                   │
│  PolicyRepository (políticas de acceso y de mitigación)                  │
│  PermissionRepository (elevaciones concedidas, con TTL)                  │
│  decide → MitigationRequired · ElevationGranted · ElevationExpired       │
│  decide, no ejecuta; no observa tráfico; no administra usuarios          │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Registro de dispositivos privilegiados ─────────────────────────────────┐
│  DeviceRepository (MAC, tipo, titular, rol, vigencia, responsable)       │
│  matcher de pertenencia: ¿registrado? ¿para qué rol?                     │
│  regla inversa: lo que no hace match → perfil BASE (P7)                  │
│  NO registra dispositivos académicos                                     │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Monitor ────────────────────────────────────────────────────────────────┐
│  sondeo de contadores (MULTIPART, vía controlador — I8)                  │
│  series temporales y línea base por destino protegido                    │
│  verificación de mitigaciones (¿bajó la tasa?)                           │
│  publica → MAC_Moved · MitigationVerified · MitigationExpired            │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Detección (Detection Engine) ───────────────────────────────────────────┐
│  pipeline: captura → normalización → features → umbrales → clasificación │
│  clasifica: flood volumétrico · brute-force de solicitudes · scanning    │
│  publica → AnomalyDetected   (nunca instala reglas, P8)                  │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Incidentes (Incident Manager) ──────────────────────────────────────────┐
│  IncidentRepository (INC-xxxx, estados, acciones)                        │
│  máquina de estados: DETECTED → MITIGATING → MITIGATED →                 │
│                      RECOVERED → CLOSED                                  │
│  correlación de anomalías (evita incidentes duplicados)                  │
│  publica → IncidentOpened / IncidentClosed                               │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Auditoría ──────────────────────────────────────────────────────────────┐
│  AuditRepository (eventos, acciones, cambios, mitigaciones)              │
│  suscripción pasiva al broker (todos los eventos del catálogo)           │
│  historial de dispositivo: la vista de investigación (doc 05)            │
│  nunca participa en la cadena de decisión (P11)                          │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Broker de eventos (infraestructura interna, I5) ────────────────────────┐
│  publicación-suscripción con colas                                      │
│  transporta eventos y órdenes de reacción — nunca preguntas (P4/P13)     │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Núcleo SDN

```text
┌─ Controlador SDN ────────────────────────────────────────────────────────┐
│  grafo de topología (switches, enlaces)                                  │
│  inventario de servicios (anclajes declarados: IP y switch:puerto)       │
│  asociaciones host ↔ MAC ↔ IP ↔ switch ↔ puerto                          │
│  inventario de reglas instaladas (con cookie y timeout)                  │
│  descubrimiento LLDP · caminos por destino · decisión → FLOW_MOD         │
│  lectura de contadores (MULTIPART) para el Monitor                       │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Switches (plano de datos) ──────────────────────────────────────────────┐
│  pipeline de tablas de flujo (escalera de prioridades)                   │
│  group table · meter table · búfer de paquetes                           │
│  contadores por puerto y por flujo                                       │
│  ejecuta y reporta; jamás decide                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Borde externo

```text
┌─ IdP institucional (SE-02) — una de las tres fuentes de identidad ───────┐
│  se consulta, no se administra — doc 04                                  │
│  directorio de identidades (LDAP / AD / BD)  ← cuentas de la comunidad   │
│  y/o servidor SSO institucional (Shibboleth / SAML2 / OIDC)              │
│  atributos de la identidad: rol, grupo, vigencia                         │
│  prototipo: directorio simulado con cuentas académicas de prueba         │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Consola de administración (cliente, no servicio) ───────────────────────┐
│  renderiza estado consultado · aplica los permisos del rol de la sesión  │
│  sin estado propio: todo pasa por la API de los servicios (I7)           │
└──────────────────────────────────────────────────────────────────────────┘
```

## 3. Fuera de las cajas

- **Activos protegidos** (hosts, servidores): son el objeto de la protección, no parte de la plataforma.
- **Firewall perimetral:** sistema del borde, por definir (R5, fase C).
- **Red inalámbrica y red de invitados:** fuera de alcance.
- **Credenciales de usuarios:** las de la comunidad viven en el IdP institucional; las de operadores, en el repositorio de identidades privilegiadas de la plataforma (doc 04).
- **Switches no administrables / equipos sin OpenFlow:** no aplican (RP-11, Pica8/PicOS).

## 4. Las interfaces que unen las cajas

| ID | Entre | Qué fluye |
|---|---|---|
| I1 | Controlador ↔ Switches | OpenFlow: FLOW_MOD, PACKET_IN, contadores… |
| I2 | Servicios ↔ Controlador | Órdenes de política y consultas (northbound) |
| I3 | Persona ↔ IAM/AAA | Portal cautivo: credenciales y sesión |
| I4 | IAM/AAA ↔ IdP | Verificación de identidad y atributos |
| I5 | Servicios ↔ Servicios | Eventos del catálogo (broker) |
| I6 | Servicio ↔ Repositorio propio | Acceso a datos de cada servicio |
| I7 | Consola ↔ Servicios | Consultas y órdenes administrativas |
| I8 | Monitor → Controlador → Switches | Contadores del plano de datos |

Detalle completo de cada interfaz en [`07_interfaces_principales.md`](../fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/07_interfaces_principales.md).

## 5. Cuestiones abiertas

- **Frontera Monitor/Detección:** pueden consolidarse en un módulo del prototipo conservando la frontera lógica (doc 04).
- **Productos concretos** de I2, I4 e I5: Fase F.
