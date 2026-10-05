# Estilo(s) arquitectónico(s)

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

## 1. Decisión

La solución no adopta un único estilo arquitectónico: es una **arquitectura híbrida de cuatro estilos**, cada uno con un rol definido y no intercambiable:

| Estilo | Rol en la arquitectura |
|---|---|
| **Capas (Layered)** | Estructura global: organiza el sistema en niveles de responsabilidad. |
| **Orientado a eventos** | Mecanismo transversal: modela la reacción dinámica ante anomalías, ataques y cambios de estado (R3, R4). |
| **Cliente-Servidor** | Interacción externa: consolas, APIs y sistemas externos que solicitan operaciones. |
| **Microservicios** | Descomposición interna: los componentes de seguridad como unidades desplegables independientes. |

```text
                    ARQUITECTURA HÍBRIDA
                            │
          ┌─────────────┬───┴────┬────────────────┐
          │             │        │                │
       Capas       Orientada a  Cliente-     Microservicios
                   eventos      Servidor
          │             │        │                │
     estructura     reacción   interacción    descomposición
      global        dinámica    externa          interna
```

La decisión responde a una observación sobre la naturaleza del problema: se construye simultáneamente una **plataforma de software de seguridad** y un **sistema SDN que actúa sobre una infraestructura de red**. Un solo estilo no cubre ambas naturalezas: las capas no explican la reactividad; los eventos no organizan la estructura; el cliente-servidor no representa la comunicación interna asíncrona; los microservicios no definen cómo se reacciona. La combinación de los cuatro cubre el dominio completo sin forzarlo.

---

## 2. Candidatos evaluados

| Estilo | Veredicto | Motivo |
|---|---|---|
| **Capas** | Adoptado | El dominio separa naturalmente interacción, lógica de seguridad, decisión y acceso a infraestructura. Hace explícita la frontera entre la lógica de seguridad y la infraestructura SDN (RP-02). |
| **Orientado a eventos** | Adoptado | R3 y R4 exigen reaccionar ante eventos de red. El estilo desacopla detección, análisis y mitigación, y permite incorporar nuevos consumidores de eventos sin modificar a los productores. |
| **Cliente-Servidor** | Adoptado | Los administradores y los sistemas externos solicitan operaciones al sistema: es una relación de petición-respuesta clara. |
| **Microservicios** | Adoptado | La cadena de seguridad está compuesta por componentes con responsabilidades y ciclos de vida distintos (IAM, monitor, detección, incidentes, políticas, auditoría). El estilo habilita su independencia de despliegue y escalamiento (D-12). |
| **Pipe-and-Filter** | Descartado como estilo | Describe la cadena captura → proceso → detección, pero no el sistema completo. La cadena de detección se modela mejor como flujo de eventos que como tubería de filtros. |
| **Master-Slave** | Descartado como estilo | El controlador mantiene una relación centralizada con los switches, pero eso no convierte a toda la arquitectura en master-slave. Esa relación pertenece al modelo de control SDN, no al estilo global. |
| **Message-Queueing** | No es un estilo | Es un mecanismo de transporte de eventos, candidato dentro del estilo orientado a eventos. Su elección es una decisión tecnológica de la Fase F. |

---

## 3. Rol de cada estilo

### 3.1 Capas — estructura global

Las capas organizan el sistema de arriba hacia abajo según la distancia al problema de red:

```text
┌───────────────────────────────────────────────┐
│        Capa de interacción                    │
│  Consola de administración · Portal cautivo   │
│  Northbound API                               │
├───────────────────────────────────────────────┤
│        Capa de aplicación                     │
│  IAM/AAA · Registro de dispositivos           │
│  Gestión de incidentes · Monitoreo            │
├───────────────────────────────────────────────┤
│        Capa de seguridad                      │
│  Detección · Políticas · Decisión             │
│  (Monitor, Detection, Incident, Policy)       │
├───────────────────────────────────────────────┤
│        Capa de control SDN                    │
│  Controlador SDN                              │
├───────────────────────────────────────────────┤
│        Capa de infraestructura                │
│  Switches · hosts · servidores protegidos     │
└───────────────────────────────────────────────┘
```

**Justificación**

- Cada capa depende únicamente de la inmediatamente inferior: la consola no habla con los switches; el Policy Engine no abre sockets contra los hosts. La dependencia se expresa como contratos entre capas.
- La frontera entre la **capa de seguridad** y la **capa de control SDN** materializa RP-02: la lógica de seguridad decide; el controlador traduce; la infraestructura ejecuta.
- La capa de interacción concentra a los actores humanos y a los sistemas externos, que nunca operan directamente sobre el plano de datos.

**Qué no resuelve.** Las capas no describen cómo reacciona el sistema ante un ataque ni cómo se comunican los componentes de una misma capa. Eso corresponde a los otros tres estilos.

Las capas se detallan en [`09_planos_v_capas.md`](09_planos_v_capas.md).

### 3.2 Orientado a eventos — reacción dinámica

Es el estilo que da forma a R3 y R4. La cadena de reacción recorre el sistema completo como una sucesión de eventos:

```text
Tráfico de red
      │  observación (counters)
      ▼
   Monitor ──► AnomalyDetected
      │
      ▼
   Detection Engine ──► IncidentOpened
      │
      ▼
   Incident Manager ──► MitigationRequired
      │
      ▼
   Policy Engine ──► MitigationRequested
      │
      ▼
   Controlador SDN ──► FLOW_MOD
      │
      ▼
   Switch ──► MitigationApplied
      │
      ▼
   Monitor (verificación) ──► MitigationVerified / MitigationExpired
```

**Propiedades que aporta**

- **Desacoplamiento.** El detector no conoce a los componentes que reaccionarán ante su evento: publica `IncidentOpened` y quien lo consuma decide. Incorporar un nuevo consumidor (p. ej. una notificación al SIEM) no modifica al productor.
- **Trazabilidad.** Cada evento es un punto registrable de la cadena, alineado con R1.9, R2.9 y el accounting de R4 (quién detectó, quién decidió, quién aplicó, cuándo y por qué).
- **Correspondencia con la red.** El evento no se queda en el software: termina en una acción concreta del plano de datos (FLOW_MOD, meter, retirada de regla), que es exactamente lo que la exposición debe mostrar.

**Eventos principales del dominio**

| Evento | Origen | Consumidores |
|---|---|---|
| `DeviceConnected` | Controlador (primer PACKET_IN) | IAM/registro, monitor |
| `MAC_Moved` | Monitor | Incident Manager, Policy Engine |
| `AnomalyDetected` | Detection Engine | Incident Manager |
| `IncidentOpened` | Incident Manager | Policy Engine, consola, auditoría |
| `MitigationRequired` | Policy Engine | Controlador SDN |
| `MitigationApplied` | Controlador | Monitor, auditoría |
| `MitigationVerified` / `MitigationExpired` | Monitor | Policy Engine, Incident Manager |
| `ElevationGranted` / `ElevationExpired` | Policy Engine | Controlador SDN, auditoría |

**Qué no resuelve.** El estilo de eventos no define cómo se transportan los eventos (broker, colas, bus): eso es un mecanismo, no un estilo, y se decide en la Fase F. Tampoco define la estructura interna de los componentes.

### 3.3 Cliente-Servidor — interacción externa

Los actores humanos y los sistemas externos interactúan con la plataforma mediante peticiones:

```text
Administrador ──► Consola / API ──► Servicios de seguridad
Personas      ──► Portal cautivo ──► IAM/AAA
Sistema externo (IdP, inteligencia) ──► Northbound API ──► Plataforma
```

**Justificación.** Estas interacciones son petición-respuesta por naturaleza: autenticarse, consultar incidentes, aprobar una elevación, modificar una política. El estilo define quién sirve a quién y bajo qué contrato.

**Qué no resuelve.** El cliente-servidor no representa la comunicación interna reactiva: sería incorrecto modelar al detector llamando síncronamente al Policy Engine en medio de un ataque. Internamente manda el estilo de eventos (§3.2); el cliente-servidor se limita al borde del sistema.

### 3.4 Microservicios — descomposición interna

La capa de aplicación y la capa de seguridad se descomponen en **servicios con responsabilidad única, despliegue independiente y datos propios**. Los componentes ya definidos en el modelo de dominio son los candidatos naturales:

```text
Servicio IAM/AAA            (portal cautivo, autenticación de poblaciones)
Servicio de registro        (dispositivos privilegiados y su auditoría)
Servicio de monitoreo       (counters, línea base)
Servicio de detección       (anomalías, R3/R4)
Servicio de incidentes      (ciclo de vida del incidente)
Servicio de políticas       (decisiones de acceso y mitigación)
Servicio de auditoría       (trazabilidad de acciones y eventos)
```

**Justificación**

- **Independencia de despliegue.** El detector puede actualizarse sin tocar el motor de políticas; el monitor puede escalar solo ante una red con más switches (D-12).
- **Aislamiento de fallos.** Un fallo en la detección no arrastra a la autenticación; el incidente queda registrado aunque la consola caiga.
- **Escalabilidad asimétrica.** La detección crece con el tráfico; el registro de dispositivos, con la cantidad de operadores: necesidades distintas, unidades distintas.
- **Separación de datos.** Cada servicio es dueño de su estado (identidades, incidentes, políticas, eventos), sin bases de datos compartidas.

**Límites de esta decisión**

- Microservicios es el **estilo de descomposición**, no una lista cerrada: qué componentes se convierten en servicios y cuáles no se determina en [`04_descomposición_arquitectónica.md`](04_descomposición_arquitectónica.md), contra RP-07 (ninguna complejidad sin justificación).
- El **controlador SDN** no se rige por las reglas de los microservicios: su relación con los switches pertenece al modelo de control SDN, y se trata como un componente especial de la capa de control.
- El estilo no compromete tecnología: contenedores, orquestación y mecanismos de comunicación se deciden en la Fase F.

---

## 4. Composición del híbrido

Los cuatro estilos no compiten: ocupan dimensiones distintas y se superponen sin conflicto.

```text
                 CAPAS ──────────────────────────────┐
                 (estructura: cada componente vive   │
                  en una capa)                       │
                                                     ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Interacción        Consola · Portal · Northbound API        │
 │  Aplicación         IAM · Registro · Incidentes · Monitoreo  │
 │  Seguridad          Detección · Políticas · Decisión         │
 │  Control SDN        Controlador                              │
 │  Infraestructura    Switches · Hosts · Servidores            │
 └──────────────────────────────────────────────────────────────┘
        ▲                                          │
        │                                          │
 MICROSERVICIOS                          ORIENTADO A EVENTOS
 (los componentes de las                (los eventos cruzan las capas:
 capas de aplicación y                  ascienden los de observación,
 seguridad son servicios                descienden las órdenes de
 desplegables)                          enforcement)

 CLIENTE-SERVIDOR — en el borde:
 administradores y sistemas externos ──► consolas y APIs
```

- **Las capas contienen; los microservicios dividen; los eventos conectan; el cliente-servidor expone.**
- Un evento puede nacer en la infraestructura (`DeviceConnected`, contadores) y subir hasta la capa de seguridad; una decisión baja como orden hasta el plano de datos. El tráfico entre capas interiores es asíncrono y por eventos; el tráfico con el exterior es síncrono y por peticiones.
- El flujo R4 recorre los cuatro estilos de extremo a extremo: el monitor (servicio, capa de seguridad) observa counters (infraestructura), el incidente y la decisión viajan como eventos, la consola del Especialista de TI consulta por cliente-servidor, y la mitigación termina en un FLOW_MOD sobre el switch.

---

## 5. Lo que esta decisión no resuelve

- **Tecnología.** Ningún producto aparece aquí: broker de eventos, protocolos de servicio (REST, gRPC), controlador SDN concreto, contenedores u orquestación son decisiones de la Fase F. Confundir estilo con tecnología forzaría el dominio para justificar una herramienta.
- **Patrones internos.** Cómo se implementa cada estilo (publicador-suscriptor, sagas, API gateway) corresponde a [`02_patrones_arquitectonicos.md`](02_patrones_arquitectonicos.md).
- **El modelo de control SDN.** La relación controlador-switch no es master-slave de la solución: es el paradigma SDN (RP-02), y su tratamiento corresponde a [`08_comunicacion.md`](08_comunicacion.md) y [`10_topología_lógica.md`](10_topología_lógica.md).
- **La frontera síncrono/asíncrono.** Qué interacciones internas son peticiones y cuáles eventos se fija en [`08_comunicacion.md`](08_comunicacion.md).

---

## 6. Cuestiones abiertas

- **Granularidad de los microservicios.** Cuántos servicios y con qué fronteras exactas: el monitor y la detección podrían ser uno solo en el prototipo; la decisión se toma en [`04_descomposición_arquitectónica.md`](04_descomposición_arquitectónica.md), evaluando RP-07.
- **Tratamiento del controlador SDN.** Si el controlador forma parte del catálogo de servicios o es un componente externo a la plataforma de software, con su propio ciclo de vida.
- **Cadenas de eventos que requieren orden.** Si la cadena de mitigación exige entrega ordenada de eventos por incidente, y quién garantiza el orden (mecanismo, Fase F).
