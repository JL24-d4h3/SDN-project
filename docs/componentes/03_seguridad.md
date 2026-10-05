# Elementos de seguridad

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Componentes del sistema — 3 de 6
**Estado:** Borrador formal para revisión

---

Qué vive dentro de cada pieza que hace la seguridad del sistema —prevención, detección, decisión, respuesta y registro— y cuál es la superficie de ataque del propio sistema de autenticación. Los mecanismos a nivel de red están en la serie de flujo; el mapa general, en [`00_mapa_de_componentes.md`](00_mapa_de_componentes.md). Los ataques cubiertos están en [`11.1_catalogo_de_ataques_y_amenazas.md`](../fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/11.1_catalogo_de_ataques_y_amenazas.md). La investigación de incidentes —el historial de dispositivo— está en [`05_historial_de_dispositivo.md`](05_historial_de_dispositivo.md).

## 1. Las funciones de seguridad y quién las cumple

```text
PREVENCIÓN    switches        perfil BASE + deny by default hacia gestión
              registro (P7)   match explícito; lo no registrado no eleva
              portal + IAM    identidad exigida para salir de BASE
DETECCIÓN     controlador     aprendizaje MAC↔IP↔puerto; MAC_MOVE
              Monitor         contadores y línea base
              Detección       clasificación de anomalías
DECISIÓN      Policy Engine   severidad → respuesta; contexto → elevación
RESPUESTA     controlador     FLOW_MOD con cookie y timeout
              switches        meter (limitar) y drop (bloquear)
VERIFICACIÓN  Monitor         contadores antes/después → MitigationVerified
REGISTRO      Auditoría       todo evento y toda acción, con su autor
```

Ninguna pieza hace dos funciones: el detector no ordena (P8), el registro no concede (P7), la auditoría no altera (P11).

## 2. Qué vive dentro de cada pieza de seguridad

```text
┌─ Controlador SDN ────────────────────────────────────────────────────────┐
│  asociaciones host ↔ MAC ↔ IP ↔ switch ↔ puerto  ← la fuente del anti-  │
│  spoofing (pares 120/110 de la escalera)                                 │
│  inventario de reglas instaladas: cookie + timeout + prioridad           │
│  detección de incoherencias de ubicación (MAC_MOVE)                      │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Monitor ────────────────────────────────────────────────────────────────┐
│  series temporales de contadores (pps, bps por destino y por origen)     │
│  línea base por destino protegido                                        │
│  verificación: ¿la tasa bajó tras la mitigación?                         │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Detección ──────────────────────────────────────────────────────────────┐
│  features: tasa, nº de fuentes, flujos nuevos por origen                 │
│  umbrales y reglas de clasificación (fijados con mediciones — Fase F)    │
│  clases: flood volumétrico · brute-force · scanning                      │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Incidentes ─────────────────────────────────────────────────────────────┐
│  IncidentRepository: INC-id, tipo, objetivo, severidad, acciones         │
│  máquina de estados: DETECTED → MITIGATING → MITIGATED →                 │
│                      RECOVERED → CLOSED                                  │
│  correlación: anomalías del mismo origen no duplican incidentes          │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Policy Engine ──────────────────────────────────────────────────────────┐
│  PolicyRepository: políticas de mitigación por severidad                 │
│  PermissionRepository: elevaciones con alcance + TTL + responsable       │
│  escalera de respuestas: RATE_LIMIT → BLOCK_SOURCE →                     │
│                          ISOLATE_DEVICE → QUARANTINE                     │
│  toda decisión genera evento → Auditoría                                 │
└──────────────────────────────────────────────────────────────────────────┘

┌─ Auditoría ──────────────────────────────────────────────────────────────┐
│  AuditRepository: eventos, acciones, cambios de política, mitigaciones    │
│  asociación: cada acción ← incidente, política u operador que la originó │
│  historial de dispositivo: la vista de investigación (doc 05)            │
│  consulta según rol (P08, P25); retención por definir                    │
└──────────────────────────────────────────────────────────────────────────┘
```

## 3. La jerarquía de confianza

```text
  sin presencia en campus   ──►  sin acceso
        │ (conectar un cable = presencia)
        ▼
  presencia física          ──►  perfil BASE (confianza mínima)
        │ (registro de operadores + login)
        ▼
  dispositivo registrado + login ──► identidad + rol
        │ (decisión contextual del Policy Engine)
        ▼
  autorización contextual   ──►  privilegios adicionales, con TTL
```

Cada peldaño habilita el siguiente; **ninguno se salta** (P6): la presencia jamás da privilegios, el registro jamás concede por sí solo, el login sin contexto vigente no produce reglas permanentes. Con la inclusión del académico, el peldaño "registro de dispositivos" queda solo para operadores: el académico pasa de BASE a su sesión **autenticándose, sin registrarse**.

## 4. La superficie de ataque del propio sistema de autenticación

El portal y el IAM son ahora infraestructura crítica (los usan todos): su superficie de ataque entra al análisis.

```text
      phishing ─────────────►  [ portal cautivo ]  ◄── credential stuffing
      (roba credenciales)             │               (fuerza bruta al login)
                                      │ credenciales válidas
                                      ▼
                              [ sesión activa ]  ◄── robo de cookie/token
                                      ▲               o MAC_MOVE sobre
                                      │               la sesión en curso
                              [ IdP externo ]
                              (si se compromete, se compromete la
                               autenticación de toda la población)
```

| Vector | Contra qué ataca | Control arquitectónico |
|---|---|---|
| **Phishing al portal** | credenciales de la persona | No se previene desde la red (es del lado del usuario). La mitigación estructural: la sesión es temporal y auditada (P10) y la credencial sola no da privilegios permanentes |
| **Credential stuffing / brute-force** | portal | Ya cubierto: detección de solicitudes por segundo por origen → RATE_LIMIT o BLOCK (catálogo 11.1, R4) |
| **Robo de sesión** (cookie/token) | sesión activa | idle_timeout ligado a la sesión (P10); retiro de reglas por cookie; toda sesión queda en accounting y auditoría. *Ligar la sesión al dispositivo (MAC/puerto) — a evaluar* |
| **Suplantación de MAC sobre sesión viva** | reglas de sesión | MAC_MOVE → bloqueo/cuarentena en el puerto nuevo (flujo parte 3 §5); la MAC original no se reasocia |
| **Compromiso del IdP** | toda la autenticación | El IdP es externo (SE-02): el IAM consume su veredicto. Una mitigación ya activa no depende del IdP; las sesiones nuevas sí — sube la criticidad de SE-02 con la inclusión del académico |
| **Sesión olvidada** (equipo desatendido) | reglas de sesión | idle_timeout devuelve el equipo a BASE automáticamente (P10) |

> Al implementar la inclusión del académico, estas filas (phishing, robo de sesión) se incorporan al catálogo [`11.1`](../fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/11.1_catalogo_de_ataques_y_amenazas.md), que hoy cubre R3–R5.

## 5. Dónde viven los datos sensibles

| Dato | Dónde vive | Protección |
|---|---|---|
| Credenciales de la comunidad | IdP institucional (externo) | La plataforma no las almacena: las usa en tránsito y las descarta |
| Credenciales de operadores | Repositorio de identidades privilegiadas (plataforma) | Hasheadas; gestión por la cadena SA→Admin (doc 04) |
| Sesiones activas | IAM/AAA | Vigencia, idle_timeout, accounting; cierre explícito o por inactividad |
| Registro de dispositivos privilegiados | `DeviceRepository` | Acceso solo por su servicio; cada cambio auditado |
| Incidentes y eventos | `IncidentRepository`, `AuditRepository` | Consulta según rol (P08, P25) |
| Historial de dispositivo | Auditoría + sesiones del IAM | Consulta según rol; retención por definir (doc 05) |
| Reglas instaladas | pipeline de los switches | Solo el controlador las modifica (P1) |

## 6. Protección del plano de control (síntesis)

El controlador es el objetivo de mayor valor y se protege en tres niveles (doc 11 §3): **aislamiento** (red de gestión separada, DROP explícito desde BASE), **identidad exigida** (solo operadores autenticados obtienen reglas hacia la gestión, con idle_timeout) y **canal sano** (OpenFlow en out-of-band; switches solo aceptan a su controlador).

## 7. Lo que la seguridad no cubre

- **Seguridad física del campus:** condición de confianza (RP-13); si se compromete, el modelo degrada a BASE generalizado.
- **Cifrado extremo a extremo del tráfico de usuario:** se controla *quién alcanza qué*, no el contenido de lo permitido.
- **Red inalámbrica y de invitados:** fuera de alcance.
- **Ataques externos (R5):** perímetro por definir (fase C).

## 8. Cuestiones abiertas

- **MFA:** resuelto — obligatorio para operadores ([doc 04](04_identidades_y_poblaciones.md) §4); no contemplado para académicos.
- **Sesión ligada al dispositivo:** si la cookie de sesión se vincula a MAC/puerto para dificultar el robo de sesión — Fase F.
- **Retención e integridad de logs:** cuánto se conservan y si se protegen contra manipulación (doc 11 §8) — ahora con motivo forense concreto: el historial de dispositivo (doc 05 §6).
- **Umbrales de detección:** se fijan con mediciones del prototipo.

Documentos relacionados: [`11_seguridad_arquitectonica.md`](../fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/11_seguridad_arquitectonica.md) (puntos de enforcement y jerarquía), [`04_flujo_seguridad_r4.md`](../../flows/04_flujo_seguridad_r4.md) (mecánica del ciclo R4) y [`11.1_catalogo_de_ataques_y_amenazas.md`](../fases/D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/11.1_catalogo_de_ataques_y_amenazas.md) (catálogo).
