# Descomposición arquitectónica

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

## 1. Criterio de descomposición

La plataforma se descompone en unidades que cumplen, una a una, los principios P3 (responsabilidad única), P4 (complejidad justificada) y P13 (comunicación por eventos):

- **Una unidad, una responsabilidad.** Cada unidad corresponde a una responsabilidad delimitada de RT-02 (identidad, autorización, detección, mitigación, monitoreo, administración, auditoría), nunca a una mezcla de ellas.
- **Cada unidad es dueña de sus datos.** La persistencia se accede solo a través del repositorio de la propia unidad (patrón Repository): ningún servicio lee la base de otro.
- **Las unidades se conectan por eventos.** El contrato entre unidades es el catálogo de eventos que circula por el broker (P13); las órdenes directas quedan para el par Política → Controlador.
- **Desplegable de forma independiente.** Cada unidad es candidata a servicio (estilo Microservicios); la independencia de despliegue es la meta, no el despliegue separado obligatorio en el prototipo.

## 2. Las dos partes del sistema

La descomposición distingue dos partes que responden a reglas distintas:

```text
┌───────────────────────────────────────┐
│  PLATAFORMA DE SEGURIDAD (servicios)  │   ← reglas de microservicios:
│  IAM · Registro · Monitor ·           │     responsabilidad única, datos
│  Detección · Incidentes · Políticas · │     propios, eventos por broker
│  Auditoría                            │
└───────────────────┬───────────────────┘
                    │ órdenes (northbound)
                    ▼
┌───────────────────────────────────────┐
│  NÚCLEO SDN                           │   ← reglas del paradigma SDN:
│  Controlador SDN ── OpenFlow ──►      │     el controlador no es un
│  Switches (plano de datos)            │     microservicio (P1)
└───────────────────────────────────────┘
```

El **controlador SDN no es un microservicio**: es el componente que traduce decisiones a reglas del plano de datos y su relación con los switches pertenece al modelo de control SDN (P1, RP-02). Tampoco lo son los switches, que ejecutan; ni la consola, que es cliente; ni el IdP institucional, que es un sistema externo (fase C).

## 3. Los servicios

| Servicio | Responsabilidad | Datos que posee (repositorio) | Eventos que publica | Eventos que consume |
|---|---|---|---|---|
| **IAM/AAA** | Autenticar y autorizar a los operadores privilegiados; gestionar sus sesiones | Identidades privilegiadas, sesiones, credenciales (consulta al IdP, no las almacena) | `SessionOpened`, `SessionClosed` | — |
| **Registro de dispositivos** | Mantener el catálogo de dispositivos privilegiados y su auditoría de altas | `DeviceRepository` (MAC, tipo, titular, rol, vigencia, responsable) | `DeviceRegistered`, `DeviceRevoked` | — |
| **Monitor** | Leer contadores del plano de datos y mantener la línea base | Series de contadores y línea base | `AnomalyDetected` (materia prima), `MitigationVerified`, `MitigationExpired` | `MitigationApplied` (para verificar) |
| **Detección** | Determinar si existe comportamiento anómalo y clasificarlo | Modelos de línea base y umbrales | `AnomalyDetected` | — (recibe métricas del Monitor por el broker) |
| **Incidentes** | Registrar y gestionar el ciclo de vida de cada incidente | `IncidentRepository` (INC-xxxx, estados, acciones) | `IncidentOpened`, `IncidentClosed` | `AnomalyDetected`, `MitigationVerified`, `MitigationExpired` |
| **Políticas** | Decidir la respuesta ante incidentes y solicitudes; decidir la elevación de privilegios | `PolicyRepository`, `PermissionRepository` | `MitigationRequired`, `ElevationGranted`, `ElevationExpired` | `IncidentOpened`, `ElevationRequested` |
| **Auditoría** | Registrar acciones, decisiones y cambios para responder quién, qué, cuándo y por qué | `AuditRepository` | — (solo consume) | todos los eventos del catálogo |

El **portal cautivo** es la interfaz web del servicio IAM/AAA, no un servicio aparte. La **consola de administración** es un cliente de los servicios (consultas y órdenes por API), no un servicio.

## 4. Diagrama de descomposición

```text
                        ┌────────────────────────────┐
                        │        CONSOLA             │   (cliente)
                        └────────────┬───────────────┘
                                     │ peticiones (cliente-servidor)
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
        ▼                            ▼                            ▼
  ┌───────────┐               ┌───────────┐               ┌───────────┐
  │ IAM/AAA   │               │ Incidentes│               │ Políticas │
  │ + portal  │               └─────┬─────┘               └─────┬─────┘
  └─────┬─────┘                     │                           │
        │                           │                           │
        └───────────────┬───────────┴───────────┬───────────────┘
                        ▼                       ▼
              ┌─────────────────┐      ┌─────────────────┐
              │ Registro de     │      │  Monitor        │
              │ dispositivos    │      │  + Detección    │
              └─────────────────┘      └────────┬────────┘
                                                │ contadores (vía controlador)
                    ┌───────────────────────────┴────────────┐
                    │                                        │
                    ▼                                        ▼
          ┌──────────────────┐                     ┌──────────────────┐
          │    BROKER        │◄──── eventos ──────┤    Auditoría     │
          │  (eventos)       │                    │ (consume todo)   │
          └────────┬─────────┘                    └──────────────────┘
                   │
                   ▼
          ┌──────────────────┐          ┌──────────────────┐
          │ Controlador SDN  │─OpenFlow►│  Switches        │
          └──────────────────┘          │  (plano de datos)│
                                        └──────────────────┘
```

## 5. Fronteras que la descomposición respeta

- **El detector no ordena.** La Detección produce eventos; solo el par Políticas → Controlador → Switch produce reglas (P8).
- **El registro no concede.** El Registro de dispositivos habilita el intento de elevación; la decisión es de Políticas (P7).
- **La auditoría no altera.** Consume eventos y registra; nunca participa en la cadena de decisión (P11).
- **Ningún servicio habla con los switches.** Solo el controlador lo hace, por OpenFlow (P1). El Monitor obtiene contadores a través del controlador, no de los switches directamente.

## 6. Descomposición lógica vs despliegue del prototipo

La descomposición de esta sección es **lógica**. En el prototipo, los servicios pueden desplegarse consolidados en el servidor de control (RP-04, RP-07) sin que las fronteras cambien: lo que no puede consolidarse es la **responsabilidad** — un módulo desplegado junto a otro sigue teniendo su repositorio, su contrato de eventos y su límite de responsabilidad.

La decisión de qué servicios se despliegan separados pertenece a la Fase G/H.

## 7. Cuestiones abiertas

- **Monitor y Detección.** Se presentan como dos servicios con frontera clara (el Monitor observa; la Detección juzga); si el prototipo los consolida en un módulo, la frontera lógica se mantiene documentada.
- **Despliegue físico.** Qué servicios corren en qué máquina del laboratorio (Fase G/H).
