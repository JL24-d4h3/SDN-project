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

# Patrones arquitectónicos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

## 1. Decisión

La arquitectura adopta **tres patrones**, cada uno resuelve una dimensión distinta del problema y ninguno intenta describir el sistema completo:

| Patrón | Alcance | Dimensión que resuelve |
|---|---|---|
| **Broker** (con message queueing como su mecanismo de entrega) | Transversal, entre componentes | Comunicación reactiva y desacoplada entre productores y consumidores de eventos de seguridad. |
| **Pipe-and-Filter** | Localizado en el subsistema de detección | Estructura del procesamiento que transforma la observación cruda en un evento de amenaza. |
| **Repository** | Localizado en la persistencia | Desacoplamiento entre la lógica de seguridad y el mecanismo concreto de almacenamiento. |

Se descartan explícitamente **CQRS** y **Master-Slave** (sección 4). La selección no se hace por catálogo: cada patrón se justifica contra una necesidad estructural real de R1–R5, en particular R3 y R4, y contra RP-07 (ninguna complejidad sin justificación).

Los tres patrones **operan dentro de los estilos** decididos en [`01_estilo(s)_arquitectonico(s).md`](01_estilo(s)_arquitectonico(s).md): el Broker es el mecanismo del estilo orientado a eventos, el Pipe-and-Filter estructura el interior del servicio de detección, y el Repository organiza la persistencia dentro de los microservicios.

---

## 2. Broker — patrón principal

### 2.1 El problema que resuelve

La solución tiene muchos productores y consumidores de eventos de seguridad. Sin intermediación, cada productor debería conocer a cada consumidor:

```text
Monitor ──────► Detection Engine
Monitor ──────► Incident Manager
Detection ────► Incident Manager
Incident ─────► Policy Engine
Policy ───────► Controlador SDN
```

Cada nueva necesidad de consumo —por ejemplo, que la auditoría también reciba los eventos de detección— obligaría a modificar a los productores. Con tres o más componentes, ese acoplamiento domina el diseño.

### 2.2 La solución

Un **broker** intermedia la comunicación por eventos: los productores publican, los consumidores se suscriben, y ninguno conoce la dirección del otro.

```text
  Monitor ──────────►┐
  Detection Engine ─►│        ┌───────────┐
  Incident Manager ─►│───────►│  BROKER   │
  Policy Engine ────►│        └─────┬─────┘
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
              Incident Manager   Consola     Auditoría
              Policy Engine      (alertas)   (registro)
```

El catálogo de eventos definido en el documento de estilos (`DeviceConnected`, `AnomalyDetected`, `IncidentOpened`, `MitigationRequired`, `MitigationVerified`…) es el contrato que circula por el broker.

### 2.3 El mecanismo de entrega: message queueing

El message queueing **no se trata como patrón independiente**: es el mecanismo de entrega del broker. El evento no se entrega directamente al consumidor; se deposita en una cola y el consumidor lo toma cuando está listo.

```text
Detection Engine ──► [colas del broker] ──► Incident Manager
```

Ese paso intermedio aporta el desacoplamiento temporal que R4 exige:

- el detector **no espera** a que el Incident Manager termine de procesar: publica y sigue observando;
- las ráfagas de eventos se absorben: un ataque volumétrico dispara muchos eventos en poco tiempo, y la cola los amortigua;
- si un consumidor está caído o lento, los eventos **no se pierden**: quedan encolados y se reintentan;
- la entrega es asíncrona por diseño, coherente con una cadena donde la detección debe ser más rápida que la reacción.

### 2.4 Lo que NO pasa por el broker

La cola no es la columna vertebral de toda la comunicación. Las interacciones de petición-respuesta siguen siendo síncronas y directas: un administrador que consulta políticas lo hace por la API, no encolando una pregunta. El broker transporta **eventos y órdenes**; las **consultas** pertenecen al cliente-servidor. La frontera exacta entre ambas se fija en [`08_comunicacion.md`](08_comunicacion.md).

---

## 3. Pipe-and-Filter — localizado en la detección

### 3.1 El problema que resuelve

Convertir la observación cruda de la red en una decisión no es un paso único: es una sucesión de transformaciones. El monitor recibe contadores; el detector necesita un veredicto; entre ambos hay normalización, extracción de características y clasificación. Modelar eso como un bloque monolítico esconde las etapas que R3 y R4 exigen poder explicar.

### 3.2 La solución

La cadena de procesamiento se organiza como **filtros conectados**: cada etapa transforma la salida de la anterior y solo la de la anterior.

```text
Tráfico / counters
      │
      ▼
┌────────────┐
│  Captura   │   lectura de contadores (OFPMP_PORT / OFPMP_FLOW)
└─────┬──────┘
      ▼
┌────────────┐
│Normalización│  tasas por destino, ventana temporal, línea base
└─────┬──────┘
      ▼
┌────────────┐
│  Features  │   pps, bps, nº de fuentes, conexiones nuevas
└─────┬──────┘
      ▼
┌────────────┐
│ Detección  │   comparación contra umbrales y línea base
└─────┬──────┘
      ▼
┌────────────┐
│Clasificación│ flood volumétrico / brute-force / severidad
└─────┬──────┘
      ▼
 AnomalyDetected ──► Broker
```

La cadena materializa exactamente la distinción del requerimiento: tráfico → métricas → características → detección → clasificación → evento de seguridad (R4.2–R4.4).

### 3.3 Por qué cada filtro es un filtro

- **Sustituible:** cambiar el método de clasificación no toca la normalización.
- **Verificable:** cada etapa se prueba aislada con entradas sintéticas (un umbral no puede ocultar un error de captura).
- **Explicable:** la exposición puede mostrar qué ocurre en cada etapa, que es lo que R3/R4 piden demostrar.

### 3.4 Su límite

El patrón **no describe la arquitectura completa**. En cuanto la cadena produce `AnomalyDetected`, la dinámica cambia: el resto es una cadena de *eventos* entre componentes (Incident Manager → Policy Engine → Controlador → Switch), no una tubería de transformaciones. Por eso el Pipe-and-Filter se declara **localizado en el subsistema de detección**, nunca como patrón global.

---

## 4. Repository — patrón complementario

### 4.1 El problema que resuelve

Varios datos persistentes son centrales para la solución: políticas, permisos, roles, dispositivos privilegiados, incidentes, eventos de auditoría y configuraciones. Si cada componente de dominio habla directamente con la base de datos, la lógica de seguridad queda atada al mecanismo de almacenamiento: cambiar de motor, replicar para auditoría o simular la persistencia en el prototipo obligaría a tocar la lógica.

### 4.2 La solución

Cada dominio accede a sus datos a través de un **repositorio** que aísla la persistencia:

```text
Policy Engine ──► PolicyRepository ──► Base de datos
```

No existe "un Repository" gigantesco: existe un repositorio por dominio o agregado:

```text
PolicyRepository      IncidentRepository     PermissionRepository
DeviceRepository      AuditRepository
```

El `DeviceRepository` es particularmente directo en esta solución: el **registro de dispositivos privilegiados** (fase A) es exactamente eso — un agregado con su propio repositorio, que sirve tanto a la decisión de acceso como a la auditoría de altas.

### 4.3 Su alcance

El Repository es **complementario**: resuelve el acceso a datos, no la reacción ante amenazas. Por eso su peso en la arquitectura es menor que el del Broker y el del Pipe-and-Filter, aunque su presencia es lo que permite que los servicios sean desplegables de forma independiente.

---

## 5. Patrones descartados

| Patrón | Motivo del descarte |
|---|---|
| **CQRS** | Separa modelo de escritura y de lectura. La solución tendrá muchas consultas (incidentes, políticas, dispositivos, eventos), pero no existe una divergencia real entre los modelos de lectura y escritura que lo justifique. Introducirlo añadiría sofisticación sin resolver un problema real, contra RP-07, y oscurecería la explicación de lo que ocurre en la red. |
| **Master-Slave** | La relación controlador ↔ switches es centralizada, pero pertenece al **modelo de control SDN** (RP-02), no es un patrón de toda la arquitectura. Elevarla a patrón global daría una imagen falsa del sistema: las aplicaciones de seguridad no son "esclavas" del controlador; son componentes que le ordenan decisiones. |

---

## 6. Integración de los tres patrones

```text
                  CLIENTE-SERVIDOR (borde)
                          │
                          ▼
                  APIs / Consolas
                          │
                          ▼
      ┌───────────────────────────────────┐
      │         COMPONENTES               │
      │  IAM · Incidentes · Políticas     │
      └───────┬───────────────┬───────────┘
              │               │
        Repository         eventos
              │               │
              ▼               ▼
          Base de datos   ┌────────┐
                          │ BROKER │
                          └───┬────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        Incident Manager  Consola        Auditoría

   PIPE-AND-FILTER (dentro del subsistema de detección)
   tráfico → captura → normalización → features
           → detección → clasificación
           → AnomalyDetected ──► BROKER ──► Incident Manager
                                             → Policy Engine
                                             → Controlador SDN
                                             → FLOW_MOD
                                             → Switch
```

La idea central: **cada patrón resuelve una dimensión que los otros no tocan** — el Broker, la comunicación reactiva; el Pipe-and-Filter, el procesamiento de detección; el Repository, la persistencia desacoplada. Juntos preparan los siguientes documentos del HLD: por qué los componentes se conectan por eventos, cuáles interacciones son síncronas y cuáles asíncronas ([`08_comunicacion.md`](08_comunicacion.md)), y dónde tiene sentido la descomposición en microservicios ([`04_descomposición_arquitectónica.md`](04_descomposición_arquitectónica.md)).

---

## 7. Cuestiones abiertas

- **Tecnología del broker.** El patrón no elige producto: broker dedicado, colas embebidas o bus de eventos se decide en la Fase F, contra las capacidades del entorno del prototipo.
- **Frontera entre repositorios.** El número y los límites exactos de los repositorios se fijan junto con la descomposición en servicios ([`04_descomposición_arquitectónica.md`](04_descomposición_arquitectónica.md)).
- **Auditoría por eventos o por escritura síncrona.** Si la auditoría consume del broker (eventual) o se escribe en la misma transacción de la acción (inmediata): es una decisión de consistencia que pertenece a [`08_comunicacion.md`](08_comunicacion.md).

# Principios arquitectónicos

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

## 1. Naturaleza y uso

Un **principio arquitectónico** es una regla de diseño de cumplimiento obligatorio, derivada de los requerimientos y restricciones del proyecto, con la que se juzga cada decisión de arquitectura. No describe *cómo* se organiza el sistema (eso es el estilo, [`01_estilo(s)_arquitectonico(s).md`](01_estilo(s)_arquitectonico(s).md)) ni *cómo* se resuelve un problema local (eso son los patrones, [`02_patrones_arquitectonicos.md`](02_patrones_arquitectonicos.md)): establece **qué decisiones son aceptables y cuáles no**.

Cada principio se define con tres elementos:

- **Enunciado:** la regla, en una frase.
- **Origen:** los requerimientos, restricciones o drivers de los que deriva — ningún principio se inventa.
- **Implicaciones:** qué obliga en el diseño concreto de esta solución.

Los principios se agrupan en estructurales, de seguridad y operacionales. Toda decisión de los documentos siguientes del HLD se justifica contra ellos; cuando dos principios tiran en direcciones opuestas, la sección 5 fija el orden de precedencia.

---

## 2. Principios estructurales

### P1 — Separación de planos

**Enunciado:** toda decisión de seguridad nace en el plano de control y se ejecuta en el plano de datos; la red no se administra dispositivo por dispositivo.

**Origen:** RP-02, RA-02, RA-03, RT-03, RT-05.

**Implicaciones**

- Cualquier cambio de política de acceso o de mitigación se materializa como mensajes southbound (FLOW_MOD, METER_MOD, GROUP_MOD), nunca como configuración manual sobre un switch.
- El plano de datos no decide: ejecuta lo instalado y reporta (PACKET_IN, PORT_STATUS, FLOW_REMOVED, contadores).
- Las capacidades reales del switch limitan el diseño: nada puede asumirse sin verificarlo contra PicOS (RP-11).

### P2 — Decisión centralizada, ejecución distribuida

**Enunciado:** el controlador decide una vez; los switches ejecutan en todos los puntos donde la decisión deba aplicarse.

**Origen:** D-06, R2.10, RT-03, RT-04, RNF-04.

**Implicaciones**

- Una mitigación que afecta a varios orígenes se instala **en cada switch de ingreso correspondiente**, no en un único punto central.
- El controlador nunca es el camino del tráfico: los paquetes fluyen por el plano de datos; el controlador solo procesa novedades.
- La latencia de las decisiones críticas (RNF-04) se resuelve empujando la ejecución al plano de datos — meters y timeouts nativos — no acelerando al controlador.

### P3 — Responsabilidad única de los componentes

**Enunciado:** cada componente de la plataforma tiene una responsabilidad delimitada, una interfaz clara y puede evaluarse por separado.

**Origen:** RT-02, RNF-07, D-12, RA-04.

**Implicaciones**

- La cadena de R4 respeta la división: monitor observa, detector clasifica, incidentes gestiona, política decide, controlador traduce, switch ejecuta, auditoría registra. Ningún componente asume la tarea del siguiente.
- Cada componente es sustituible y verificable aislado (patrón Pipe-and-Filter en la detección).
- La separación entre identidad, autorización, detección, mitigación, monitoreo y administración es explícita en la descomposición ([`04_descomposición_arquitectónica.md`](04_descomposición_arquitectónica.md)).

### P4 — Complejidad justificada

**Enunciado:** ninguna tecnología, componente o mecanismo se incorpora si no responde a una necesidad concreta y evaluable del proyecto.

**Origen:** RP-07, RP-09.

**Implicaciones**

- Patrones descartados por no responder a una necesidad real (CQRS, Master-Slave como patrón global — ver [`02_patrones_arquitectonicos.md`](02_patrones_arquitectonicos.md)).
- El número de microservicios lo define la necesidad, no el catálogo: cada frontera de servicio debe poder justificarse contra un requerimiento.
- Las primitivas OpenFlow que se usan son exactamente las que los escenarios exigen (groups para inundación, meters para rate limiting, contadores para monitoreo); el resto se deja declarado y sin usar.

---

## 3. Principios de seguridad

### P5 — Mínimo privilegio con denegación por defecto

**Enunciado:** todo dispositivo conectado recibe el perfil mínimo; lo que no esté explícitamente permitido queda denegado.

**Origen:** R1.5, R1.6, R2.5.

**Implicaciones**

- El perfil BASE permite solo DHCP, DNS y el portal; todo acceso a infraestructura tiene una entrada DROP por defecto con prioridad sobre el forwarding.
- La regla del registro de dispositivos privilegiados es inversa a un catálogo total: **no match → BASE**. La población académica no requiere alta alguna.
- Ningún rol hereda permisos por acumulación: cada permiso se concede explícitamente.

### P6 — La identidad se exige solo para elevar privilegios

**Enunciado:** la presencia física confiere el perfil mínimo; cualquier privilegio superior exige autenticación y autorización con contexto y vigencia.

**Origen:** RP-13, R1.2, R1.3.

**Implicaciones**

- La comunidad se autentica en el portal contra el IdP institucional (perfil ACADÉMICO); los operadores, contra el repositorio propio con MFA (sesión de rol).
- La elevación se decide en el Policy Engine con identidad + dispositivo registrado + contexto + vigencia; la presencia física jamás justifica privilegios.
- La cadena de confianza es explícita: sin presencia → sin acceso; presencia → BASE; registro + login → identidad; política contextual → privilegios con TTL o sesión.

### P7 — La MAC es atributo, no credencial

**Enunciado:** la identidad de un dispositivo no se confía por su MAC; se observa, se asocia y se detecta su incoherencia.

**Origen:** R3.3, modelo de actores (fase A), flujo de autenticación (parte 3 de la serie de flujo).

**Implicaciones**

- La coincidencia con el registro de dispositivos privilegiados **habilita** el intento de elevación, nunca lo concede.
- La incoherencia (misma MAC en otro puerto, MAC con otra IP o con otra identidad) produce eventos MAC_MOVE con respuesta escalonada: alerta → bloqueo → cuarentena.
- Los mecanismos de puerto (port security, 802.1X) se reservan para puertos sensibles; ninguno sustituye a la identidad de la persona.

### P8 — El detector observa; la política decide; la red ejecuta

**Enunciado:** la detección, la decisión de respuesta y la ejecución son responsabilidades de componentes distintos, enlazados por una cadena trazable.

**Origen:** R3.7, R4.5, RT-08, RA-06, D-04.

**Implicaciones**

- El Detection Engine **nunca instala reglas**: produce eventos. Toda respuesta pasa por Incidente → Policy Engine → Controlador → Switch.
- La cadena completa debe poder trazarse como **evento → detección → evaluación → decisión → política → aplicación → resultado** (RA-06).
- La automatización (RT-08) se aplica a las decisiones del Policy Engine, no a saltos directos entre detección y red.

### P9 — Mitigar cerca del origen sin cortar el tráfico legítimo

**Enunciado:** la contención se aplica en el punto de ingreso del tráfico malicioso y debe preservar el servicio legítimo.

**Origen:** R4.8, RNF-02, D-09.

**Implicaciones**

- La regla de mitigación se instala en el switch de ingreso del origen, no junto a la víctima: el tráfico malicioso se descarta antes de atravesar la red.
- La escalera de respuestas (RATE_LIMIT → BLOCK → ISOLATE → QUARANTINE) elige la mínima intervención suficiente; el meter limita antes que el DROP total.
- Ninguna mitigación se da por buena sin verificación con contadores: si el tráfico legítimo no se recupera, la respuesta se ajusta.

---

## 4. Principios operacionales

### P10 — Todo privilegio y toda mitigación es temporal y reversible

**Enunciado:** ningún permiso excepcional ni regla de mitigación permanece por defecto: expira, se retira y la política original se restaura.

**Origen:** RT-10, R3.9, R4.9, D-07.

**Implicaciones**

- Elevaciones con TTL y sesiones con idle_timeout: el estado BASE es el punto de retorno obligatorio.
- Reglas de mitigación con hard_timeout/idle_timeout y cookie por incidente, retiradas con FLOW_MOD DELETE; FLOW_REMOVED informa la expiración.
- El incidente recorre estados explícitos hasta CLOSED; una mitigación sin cierre es un defecto, no un estado válido.

### P11 — Trazabilidad y observabilidad por diseño

**Enunciado:** toda decisión y acción relevante queda registrada y asociable a quién, qué, cuándo y por qué; la red expone la información necesaria para supervisarla.

**Origen:** R1.9, R2.9, RNF-08, RNF-09, RT-06, RT-07, D-08.

**Implicaciones**

- Los contadores OpenFlow son la única fuente de observación del plano de datos; el monitor los lee periódicamente y construye la línea base.
- El accounting AAA registra las acciones de los operadores; el registro de dispositivos privilegiados guarda la auditoría de altas (quién registró qué, cuándo).
- Cada cambio de política y cada mitigación es respondible: qué regla, en qué switch, originada por qué incidente o decisión, y cuándo se retiró.

### P12 — Sin métrica no hay decisión válida

**Enunciado:** toda funcionalidad crítica se evalúa con métricas objetivas definidas antes de implementarla; una alternativa sin medición no es una alternativa.

**Origen:** RP-10, RNF-12, R4.10, D-14.

**Implicaciones**

- Instrumentación temprana: línea base, umbrales y contadores se definen al diseñar, no al terminar.
- Toda elección entre alternativas de diseño (p. ej. group ALL vs PACKET_OUT, meters nativos vs degradación por controlador) se decide con resultados cuantitativos del prototipo.
- Los tiempos de detección, mitigación e impacto sobre el servicio de R4.10 se miden y se reportan.

### P13 — Comunicación por eventos entre componentes de seguridad

**Enunciado:** los componentes internos de la plataforma se comunican por eventos a través de un intermediario; las peticiones síncronas quedan confinadas al borde.

**Origen:** estilos (doc 01), patrones (doc 02), RT-08, RA-05, RA-06.

**Implicaciones**

- El catálogo de eventos (`DeviceConnected`, `AnomalyDetected`, `IncidentOpened`, `MitigationRequired`, …) es el contrato entre componentes; añadir un consumidor no modifica a ningún productor.
- Las ráfagas de eventos de un ataque se absorben en colas: el detector publica y sigue observando, sin esperar al consumidor.
- Las consultas administrativas (consolas, APIs) siguen siendo petición-respuesta directa: el broker transporta eventos y órdenes, no preguntas.

---

## 5. Conflictos entre principios

Cuando dos principios tiran en direcciones opuestas, la resolución es explícita y se documenta:

| Conflicto | Resolución |
|---|---|
| **P2** (decisión centralizada) vs **RNF-04** (latencia) | La ejecución se empuja al plano de datos: meters y timeouts nativos. El controlador decide en el plano de control; el switch aplica a velocidad de línea. |
| **P9** (preservar el tráfico legítimo) vs **P8** (automatización) | La escalera de respuestas resuelve: la severidad baja se limita (RATE_LIMIT) sin intervención; el bloqueo total de alto impacto exige aprobación humana. |
| **P12** (métricas primero) vs **RP-03** (tiempo del curso) | La instrumentación se acota a lo que R4.10 y RP-10 exigen: tiempos e impacto, no una plataforma de telemetría completa. |
| **P4** (complejidad justificada) vs **P13** (comunicación por eventos) | El broker se introduce como patrón, no como producto: la tecnología se elige en la Fase F contra el tamaño real del prototipo, no contra un despliegue de producción. |

---

## 6. Trazabilidad

| Principio | Origen directo |
|---|---|
| P1 Separación de planos | RP-02, RA-02, RA-03, RT-03, RT-05 |
| P2 Decisión centralizada, ejecución distribuida | D-06, R2.10, RT-03, RT-04, RNF-04 |
| P3 Responsabilidad única | RT-02, RNF-07, D-12, RA-04 |
| P4 Complejidad justificada | RP-07, RP-09 |
| P5 Mínimo privilegio | R1.5, R1.6, R2.5 |
| P6 Identidad solo para elevar | RP-13, R1.2, R1.3 |
| P7 MAC como atributo | R3.3, fase A (actores) |
| P8 Detectar / decidir / ejecutar | R3.7, R4.5, RT-08, RA-06, D-04 |
| P9 Mitigar cerca del origen | R4.8, RNF-02, D-09 |
| P10 Temporalidad y reversibilidad | RT-10, R3.9, R4.9, D-07 |
| P11 Trazabilidad y observabilidad | R1.9, R2.9, RNF-08, RNF-09, RT-06, RT-07, D-08 |
| P12 Métricas objetivas | RP-10, RNF-12, R4.10, D-14 |
| P13 Comunicación por eventos | Estilos (01), Patrones (02), RT-08, RA-05, RA-06 |

---

## 7. Cuestiones abiertas

- **Frontera síncrono/asíncrono.** Qué interacciones internas quedan fuera del broker y por qué: se fija en [`08_comunicacion.md`](08_comunicacion.md).
- **Precedencia entre P9 y P12 en caso extremo.** Si una mitigación que preserva el servicio legítimo no alcanza las métricas exigidas, decidir si prima la disponibilidad (P9) o el resultado medido (P12); depende de los umbrales que se fijen en la Fase F.

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
| **IAM/AAA** | Autenticar y autorizar a las poblaciones (la comunidad contra el IdP; los operadores contra el repositorio propio) y gestionar sus sesiones | Identidades privilegiadas con sus credenciales, sesiones y perfiles | `SessionOpened`, `SessionClosed` | — |
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

La decisión de qué servicios se despliegan separados pertenece a la Fase H.

## 7. Cuestiones abiertas

- **Monitor y Detección.** Se presentan como dos servicios con frontera clara (el Monitor observa; la Detección juzga); si el prototipo los consolida en un módulo, la frontera lógica se mantiene documentada.
- **Despliegue físico.** Qué servicios corren en qué máquina del laboratorio (Fase H).

# Componentes principales

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Descripción detallada de cada componente de la descomposición ([`04_descomposición_arquitectonica.md`](04_descomposición_arquitectonica.md)): qué hace, qué recibe, qué produce, qué estado mantiene y qué mecanismos usa internamente. Las responsabilidades formales (qué sí y qué no) están en [`06_responsabilidades.md`](06_responsabilidades.md).

## 1. Controlador SDN

**Propósito:** traducir las decisiones de la plataforma a reglas del plano de datos y mantener el conocimiento de la red.

- **Entradas:** órdenes de política (instalar/retirar reglas, consultar estado); mensajes OpenFlow de los switches (PACKET_IN, PORT_STATUS, FLOW_REMOVED, FEATURES_REPLY).
- **Salidas:** mensajes OpenFlow (FLOW_MOD, METER_MOD, GROUP_MOD, PACKET_OUT, MULTIPART); topología y estado a la plataforma.
- **Estado:** grafo de topología (switches, enlaces, atributos), **inventario de servicios** (los anclajes declarados: servicio, IP, switch y puerto), asociaciones host ↔ MAC ↔ IP ↔ switch ↔ puerto, inventario de reglas instaladas (con sus cookies), capacidades declaradas por cada switch.
- **Mecanismos internos:** descubrimiento LLDP (inyección por PACKET_OUT y deducción de enlaces por cruce de metadatos); cálculo de caminos por destino sobre el grafo e instalación **proactiva** hacia los servicios declarados, además de la instalación reactiva ante PACKET_IN (FLOW_MOD + PACKET_OUT); respuesta ARP desde sus asociaciones; retirada de reglas por cookie; lectura de contadores por MULTIPART. Detalle completo en la serie de flujo (partes 1, 2 y 5).

## 2. Monitor

**Propósito:** observar el plano de datos y construir la línea base sobre la que se detecta.

- **Entradas:** contadores OpenFlow (por puerto y por flujo), leídos periódicamente a través del controlador; eventos de mitigación aplicada (para verificar).
- **Salidas:** métricas normalizadas (tasas por destino, por origen, nº de fuentes); eventos `MitigationVerified` / `MitigationExpired`.
- **Estado:** series temporales de contadores, línea base por destino protegido.
- **Mecanismos internos:** sondeo periódico (MULTIPART `OFPMP_PORT_STATS` / `OFPMP_FLOW`); normalización a tasas (pps, bps) por ventana temporal; comparación contra línea base para emitir materia prima de detección.

## 3. Detection Engine

**Propósito:** decidir si existe comportamiento anómalo y clasificarlo.

- **Entradas:** métricas normalizadas del Monitor (por el broker).
- **Salidas:** evento `AnomalyDetected` con tipo, destino, fuentes, tasas y desviación.
- **Estado:** umbrales y reglas de clasificación.
- **Mecanismos internos:** cadena Pipe-and-Filter — captura → normalización → extracción de features → comparación contra umbrales y línea base → clasificación (flood volumétrico vs brute-force de solicitudes) → emisión del evento. Nunca instala reglas (P8).

## 4. Incident Manager

**Propósito:** registrar cada incidente y gestionar su ciclo de vida.

- **Entradas:** `AnomalyDetected`; resultados de verificación (`MitigationVerified` / `MitigationExpired`).
- **Salidas:** `IncidentOpened`, `IncidentClosed`; consultas de la consola (estado del incidente).
- **Estado:** `IncidentRepository`: por incidente, tipo, objetivo, orígenes, severidad, estados (DETECTED → MITIGATING → MITIGATED → RECOVERED → CLOSED) y acciones asociadas.
- **Mecanismos internos:** correlación de anomalías con incidentes existentes (evitar duplicados); transición de estados según eventos recibidos; exposición del historial para auditoría.

## 5. Policy Engine

**Propósito:** decidir la respuesta ante incidentes y la concesión de elevaciones.

- **Entradas:** `IncidentOpened` (con severidad y contexto); `ElevationRequested` (solicitud aprobada por el Administrador de Red); consultas del IAM/AAA (perfil de una sesión).
- **Salidas:** `MitigationRequired` (comando al controlador vía northbound); `ElevationGranted` / `ElevationExpired`.
- **Estado:** `PolicyRepository` (políticas de acceso y de mitigación), `PermissionRepository` (permisos y vigencia de las elevaciones).
- **Mecanismos internos:** evaluación de condiciones ABAC-like — identidad + dispositivo + ubicación + contexto + recurso + acción + vigencia — para permitir/denegar; escalera de respuestas por severidad (RATE_LIMIT → BLOCK_SOURCE → ISOLATE_DEVICE → QUARANTINE); programación de expiraciones (TTL) para elevaciones y mitigaciones.

## 6. IAM/AAA (con portal cautivo)

**Propósito:** autenticar a las poblaciones (la comunidad contra el IdP; los operadores contra su repositorio propio) y autorizar sus sesiones.

- **Entradas:** credenciales de la población (portal cautivo o acceso remoto); atributos del IdP institucional para la comunidad; código TOTP para operadores.
- **Salidas:** identidad autenticada + perfil o rol al Policy Engine; `SessionOpened` / `SessionClosed`; registros de accounting.
- **Estado:** identidades privilegiadas con sus credenciales propias y su segundo factor, sesiones activas y su vigencia. No almacena credenciales de la comunidad: las valida el IdP; el servicio AAA no las guarda.
- **Mecanismos internos:** diálogo RADIUS (Authentication, Authorization, Accounting): contra el IdP para la comunidad, y contra el repositorio propio con TOTP para los operadores; gestión del ciclo de sesión (login → perfil ACADÉMICO o sesión de rol → logout/inactividad → retorno a BASE, vía idle_timeout).

## 7. Registro de dispositivos privilegiados

**Propósito:** mantener el catálogo de dispositivos de los operadores y su auditoría.

- **Entradas:** altas, modificaciones y bajas ordenadas por el Administrador de Red o el Superadministrador (P30).
- **Salidas:** consultas de pertenencia al Policy Engine (¿este dispositivo está registrado y para qué rol?); historial de cambios para auditoría.
- **Estado:** `DeviceRepository`: MAC, tipo, titular, rol asociado, vigencia, responsable del registro.
- **Mecanismos internos:** regla inversa — todo lo que **no** hace match queda fuera del registro y recibe perfil BASE; el match solo habilita el intento de elevación (P7). Los dispositivos académicos no se registran.

## 8. Auditoría

**Propósito:** registrar toda decisión y acción relevante para responder quién, qué, cuándo y por qué.

- **Entradas:** todos los eventos del catálogo (suscripta al broker); acciones administrativas (quién registró qué dispositivo, quién aprobó qué elevación).
- **Salidas:** consultas de la consola para operadores autorizados (P25).
- **Estado:** `AuditRepository` (eventos, acciones, cambios de política, mitigaciones con su origen y su retirada).
- **Mecanismos internos:** consumo pasivo del broker — nunca participa en la cadena de decisión (P11); asociación de cada acción con el incidente, la política o el operador que la originó (RNF-09).

## 9. Switches (plano de datos)

**Propósito:** ejecutar las reglas instaladas y reportar.

- **Entradas:** mensajes del controlador (FLOW_MOD, METER_MOD, GROUP_MOD, PACKET_OUT, MULTIPART).
- **Salidas:** PACKET_IN, PORT_STATUS, FLOW_REMOVED, contadores, tráfico reenviado.
- **Estado:** pipeline de tablas de flujo, group table, meter table, contadores, búfer de paquetes (anatomía: serie de flujo, parte 0).
- **Mecanismos internos:** evaluación por prioridad de las entradas; ejecución de instrucciones (output, drop, meter, group); expiración por hard/idle_timeout; captura por table-miss y por regla explícita (OFPR_NO_MATCH / OFPR_ACTION).

## 10. Consola de administración

**Propósito:** interfaz de operación de la plataforma para los operadores.

- **Entradas:** acciones del operador autenticado.
- **Salidas:** peticiones a los servicios (consultas, aprobaciones, altas, cambios de política).
- **Estado:** ninguno propio: es un cliente (cliente-servidor, doc 01).
- **Mecanismos internos:** renderiza estado consultado; aplica los permisos del rol de la sesión (P-catálogo, fase A).

## 11. Qué no es un componente de esta lista

- **El IdP institucional** es un sistema externo (SE-02, fase C): se consulta, no se administra.
- **Los hosts y servidores protegidos** son activos protegidos, no componentes de la plataforma.
- **El firewall perimetral** queda por definir (R5 no está asignado a este grupo; fase C).

# Responsabilidades

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Este documento fija, por componente, qué responsabilidad tiene y qué **explícitamente no tiene** (P3), y qué rol humano opera cada componente. Complementa a [`05_componentes_principales.md`](05_componentes_principales.md) (descripción funcional) con la dimensión de autoridad.

## 1. Responsabilidad y no-responsabilidad por componente

| Componente | Responsable de | No es responsable de |
|---|---|---|
| **Monitor** | Obtener contadores; construir la línea base; verificar el efecto de las mitigaciones. | Detectar ataques; decidir respuestas; instalar reglas. |
| **Detection Engine** | Determinar si hay anomalía; clasificarla. | Registrar incidentes; decidir la mitigación; tocar la red. |
| **Incident Manager** | Registrar el incidente; llevar su ciclo de vida hasta CLOSED. | Calcular umbrales; elegir la respuesta; ejecutar reglas. |
| **Policy Engine** | Decidir la respuesta ante incidentes y las elevaciones de privilegios, con contexto y vigencia. | Observar el tráfico; ejecutar la decisión; administrar usuarios. |
| **Controlador SDN** | Traducir decisiones a reglas; mantener topología y asociaciones; retirar reglas. | Decidir políticas; juzgar si hay ataque; autenticar operadores. |
| **IAM/AAA** | Autenticar a las poblaciones; autorizar sesiones; registrar accounting. | Catalogar dispositivos; decidir mitigaciones; gestionar políticas. |
| **Registro de dispositivos** | Mantener el catálogo de dispositivos privilegiados y su auditoría de altas. | Conceder privilegios por sí mismo (P7); registrar dispositivos académicos. |
| **Auditoría** | Registrar acciones y decisiones; responder quién, qué, cuándo y por qué. | Participar en la cadena de decisión; bloquear o permitir (P11). |
| **Switches** | Ejecutar las reglas instaladas; reportar eventos y contadores. | Decidir qué reglas instalar; juzgar tráfico. |
| **Consola** | Exponer operación y consultas según el rol de la sesión. | Guardar estado; aplicar permisos por su cuenta. |

## 2. La cadena de R4 como cadena de responsabilidades

La tabla anterior se recorre de extremo a extremo en R4 — cada eslabón entrega el trabajo al siguiente y ninguno lo retiene:

```text
Monitor            observa y entrega métricas
   → Detection     juzga y entrega AnomalyDetected
   → Incident      registra y entrega IncidentOpened
   → Policy        decide y entrega MitigationRequired
   → Controlador   traduce y entrega FLOW_MOD
   → Switch        ejecuta y entrega contadores de vuelta
   → Monitor       verifica y entrega MitigationVerified
   → Incident      cierra el ciclo
   → Auditoría     registra todo el recorrido
```

Esta cadena cumple RA-06 (evento → detección → evaluación → decisión → política → aplicación → resultado) con un responsable identificable por etapa.

## 3. Matriz de roles humanos sobre los componentes

Qué puede hacer cada rol sobre cada componente, según los permisos de la fase A:

| Componente | Usuario académico | Especialista de TI | Administrador de Red | Superadministrador |
|---|---|---|---|---|
| Monitor / Detección | — | Consultar métricas y eventos (P06–P09) | Consultar y ajustar umbrales | Todo + política global |
| Incident Manager | — | Analizar, clasificar, escalar (P10, P11) | Gestionar incidentes | Todo |
| Policy Engine | Solicitar elevación (P28) | Ejecutar mitigaciones autorizadas (P12) | Crear/modificar políticas; aprobar elevaciones (P17, P29) | Todo (P26) |
| Controlador SDN | — | — (no opera) | Administrar reglas y topología (P19, P22) | Todo |
| IAM/AAA | Autenticarse en el portal (perfil ACADÉMICO) | Autenticarse como operador | Autenticarse como operador | Autenticarse como operador |
| Registro de dispositivos | — | — | Registrar dispositivos (P30) | Registrar + auditar (P30, P25) |
| Auditoría | — | Consultar eventos y logs (P08) | Consultar | Consultar y auditar todo (P25) |
| Consola | — (no la usa) | Uso con su rol | Uso con su rol | Uso con su rol |

El usuario académico solo aparece en dos celdas: **autenticarse en el portal** y **solicitar elevación**. Todo lo demás le está denegado —en BASE y en ACADÉMICO— y la red lo garantiza con entradas DROP hacia la infraestructura, no con la buena voluntad de la consola.

## 4. Separación de funciones entre roles

Ningún rol concentra definir, aplicar y evaluar una política sin control (fase A, §2.6), y la asignación de componentes la refuerza:

```text
Administrador de Red   crea la política (Policy Engine)
Superadministrador     puede modificarla o revocarla (mismo componente, más permiso)
Especialista de TI     detecta sus efectos y gestiona el incidente
                       (no la modifica)
Auditoría              registra quién hizo qué, independiente de ambos
```

El mismo componente puede ser operado por dos roles con permisos distintos: la separación la imponen los permisos y su registro, no la duplicación de componentes (P4).

## 5. Acciones que exigen intervención humana

La automatización (RT-08) tiene un tope deliberado (P8, P9):

| Acción | Quién la ejecuta | Condición |
|---|---|---|
| RATE_LIMIT ante anomalía leve | Sistema (Policy → Controlador) | Automático, notificado |
| BLOCK ante DDoS severo | Sistema + supervisión del Especialista de TI | Automático con notificación |
| Aislar un segmento completo | Administrador de Red | **Requiere aprobación** |
| Elevación temporal de un académico | Administrador de Red | **Requiere aprobación** (P29) |
| Alta en el registro de dispositivos | Administrador de Red / Superadministrador | Requiere registro formal (P30) |
| Política global de la plataforma | Superadministrador | Solo el SA |

## 6. Cuestiones abiertas

- **Delegación del registro de Especialistas de TI.** Si el Administrador de Red puede darlos de alta en IAM/AAA o solo el Superadministrador (fase A).
- **Umbrales como política o como configuración técnica.** Quién ajusta los umbrales de detección: el Especialista de TI (operación) o el Administrador de Red (política). La tabla 3 los deja en el Administrador; ajustable.

# Interfaces principales

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Cada interfaz define **qué fluye entre qué partes**, con qué sincronía y bajo qué contrato. Los protocolos concretos que no están decididos se marcan como Fase F; los fijados son el southbound (OpenFlow, RP-11) y la identidad (I4 = RADIUS, contra el directorio del IdP). El mapa completo de comunicación está en [`08_comunicacion.md`](08_comunicacion.md).

## 1. Registro de interfaces

| ID | Interfaz | Entre | Tipo | Sincronía |
|---|---|---|---|---|
| I1 | Southbound SDN | Controlador ↔ Switches | Protocolo de control (OpenFlow) | Mixta (petición-respuesta + asíncronos) |
| I2 | Northbound | Servicios ↔ Controlador | API del controlador | Petición-respuesta |
| I3 | Portal cautivo | Poblaciones ↔ IAM/AAA | Interfaz web de autenticación | Petición-respuesta |
| I4 | Identidad institucional | IAM/AAA ↔ IdP (externo) | RADIUS (directorio LDAP detrás) | Petición-respuesta |
| I5 | Broker de eventos | Servicios ↔ Servicios | Publicación-suscripción | Asíncrona |
| I6 | Persistencia | Servicios ↔ Repositorios | Acceso a datos del propio servicio | Síncrona local |
| I7 | API de administración | Consola ↔ Servicios | API de la plataforma | Petición-respuesta |
| I8 | Observación del plano de datos | Monitor → Controlador → Switches | Consulta de contadores (vía I2 + I1) | Petición-respuesta periódica |

## 2. Fichas

### I1 — Southbound: Controlador ↔ Switches

- **Protocolo:** OpenFlow 1.3 sobre TCP 6653, por el canal de control out-of-band (RP-11; variante in-band en la serie de flujo, parte 2).
- **Qué fluye:** instalación y retirada de estado (FLOW_MOD, METER_MOD, GROUP_MOD), emisión de paquetes (PACKET_OUT), lectura de contadores (MULTIPART), eventos del switch (PACKET_IN, PORT_STATUS, FLOW_REMOVED), latidos (ECHO), negociación (HELLO, FEATURES).
- **Contrato:** las capacidades las declara el switch en FEATURES_REPLY; el controlador no puede ordenar más de lo declarado (P1, RP-11). Las reglas llevan cookie y timeouts para su gestión y reversión (P10).
- **Sincronía:** los comandos son petición-respuesta con `xid`; los eventos del switch son asíncronos.

### I2 — Northbound: Servicios ↔ Controlador

- **Protocolo:** API del controlador (forma concreta en Fase F; típicamente REST o similar).
- **Qué fluye:** órdenes de política —instalar/retirar reglas de acceso, de elevación y de mitigación— y consultas —topología, asociaciones host↔puerto, contadores, estado de reglas—.
- **Contrato:** la orden expresa **qué** se quiere (bloquear tráfico de X hacia Y, limitar tasa a Z); el **cómo** (FLOW_MOD concreto, prioridades, meters) es responsabilidad del controlador (P2, P8).
- **Sincronía:** petición-respuesta con confirmación de aplicación. La plataforma espera la confirmación antes de dar la acción por ejecutada.

### I3 — Portal cautivo: Poblaciones ↔ IAM/AAA

- **Protocolo:** interfaz web de autenticación (HTTPS).
- **Qué fluye:** credenciales de la población (usuario y contraseña; código TOTP para operadores) y la respuesta de sesión.
- **Contrato:** el portal autentica a **las dos poblaciones**: la comunidad contra el IdP institucional (perfil ACADÉMICO); los operadores contra el repositorio propio con MFA (sesión de rol). La sesión resultante la decide el Policy Engine; el portal no conecta nada por sí mismo.
- **Sincronía:** petición-respuesta.

### I4 — Identidad institucional: IAM/AAA ↔ IdP

- **Protocolo:** RADIUS contra el backend de identidad del IdP (directorio LDAP detrás; producto en Fase F).
- **Qué fluye:** verificación de credenciales de la comunidad universitaria y atributos para el perfil.
- **Contrato:** el IdP es el dueño de la identidad de la comunidad (SE-02, fase C); el IAM/AAA la consume y no almacena credenciales de usuarios. Las de operadores viven en el repositorio propio del IAM. El resultado llega al Policy Engine como identidad + atributos.
- **Sincronía:** petición-respuesta.

### I5 — Broker de eventos: Servicios ↔ Servicios

- **Protocolo:** publicación-suscripción con colas (producto en Fase F; patrón Broker, doc 02).
- **Qué fluye:** el catálogo de eventos (`DeviceConnected`, `AnomalyDetected`, `IncidentOpened`, `MitigationRequired`, `MitigationApplied`, `MitigationVerified`, `MitigationExpired`, `SessionOpened/Closed`, `ElevationGranted/Expired`, `DeviceRegistered/Revoked`).
- **Contrato:** cada evento declara productor, consumidores y payload (ver [`08_comunicacion.md`](08_comunicacion.md) §3). Publicar no espera al consumidor; los eventos se encolan y no se pierden ante un consumidor caído (P13).
- **Sincronía:** asíncrona, con desacoplamiento temporal.

### I6 — Persistencia: Servicios ↔ Repositorios

- **Protocolo:** acceso a datos a través del repositorio del propio servicio (patrón Repository, doc 02).
- **Qué fluye:** lectura y escritura de las entidades del dominio del servicio (incidentes, políticas, dispositivos, eventos).
- **Contrato:** **ningún servicio accede a la base de datos de otro** (doc 04). El cambio de motor de persistencia no puede afectar la lógica del servicio.
- **Sincronía:** síncrona, local al servicio.

### I7 — API de administración: Consola ↔ Servicios

- **Protocolo:** API de la plataforma (forma concreta en Fase F).
- **Qué fluye:** consultas (incidentes, políticas, dispositivos, eventos, estado) y órdenes administrativas (aprobar elevación, registrar dispositivo, modificar política).
- **Contrato:** la consola actúa con los permisos del rol de la sesión autenticada (P-catálogo); el servicio valida, no confía en la interfaz.
- **Sincronía:** petición-respuesta.

### I8 — Observación del plano de datos: Monitor → Controlador → Switches

- **Protocolo:** composición de I2 e I1: el Monitor consulta contadores al controlador, que los lee del switch con MULTIPART (`OFPMP_PORT_STATS`, `OFPMP_FLOW`).
- **Qué fluye:** contadores por puerto y por flujo, convertidos por el Monitor en métricas y línea base.
- **Contrato:** el Monitor **no habla con los switches** (P1): toda observación pasa por el controlador. La frecuencia de sondeo la define el Monitor y es configurable.
- **Sincronía:** petición-respuesta periódica (fondo).

## 3. Qué NO son interfaces de esta arquitectura

- **Conexiones directas servicio ↔ switch:** prohibidas por P1; solo el controlador habla OpenFlow.
- **Acceso de la consola a la base de datos:** prohibido por I6; todo pasa por la API.
- **Autenticación en el enlace (802.1X/EAPOL).** Fuera del prototipo: la autenticación de personas vive en aplicación (I3/I4); 802.1X queda reservado a puertos sensibles del despliegue real.

## 4. Cuestiones abiertas

- **Forma concreta de I2 e I7.** API REST, RPC o ambas: Fase F, con el controlador elegido.
- **Producto del broker (I5).** Broker dedicado vs colas embebidas: Fase F, contra el tamaño del prototipo.
- **Frecuencia de sondeo de I8.** Depende de los umbrales de detección que se fijen con mediciones del prototipo (Fase F).

# Comunicación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Cómo se comunican las partes del sistema: los tres canales que existen, la frontera entre lo síncrono y lo asíncrono (P13), el catálogo de eventos con sus payloads y la matriz completa de interacciones. Las interfaces formales están en [`07_interfaces_principales.md`](07_interfaces_principales.md).

## 1. Los tres canales

```text
┌─────────────────────────────────────────────────────────────────┐
│  BORDE EXTERNO (cliente-servidor)                               │
│  consola ──► API ──► servicios      portal ──► IAM/AAA           │
│  IdP ◄──► IAM/AAA                                                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│  BUS INTERNO DE LA PLATAFORMA                                   │
│  eventos (broker, asíncrono)  +  órdenes northbound (síncrono)  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│  CANAL DE CONTROL SDN (OpenFlow, out-of-band)                   │
│  controlador ◄──► switches                                      │
└─────────────────────────────────────────────────────────────────┘
```

- **Borde externo:** actores humanos y sistemas externos; siempre petición-respuesta.
- **Bus interno:** los servicios entre sí; dominan los eventos, con una excepción síncrona —las órdenes de Políticas al Controlador—.
- **Canal SDN:** protocolo de control con el plano de datos; comandos con confirmación y eventos asíncronos del switch.

## 2. La frontera síncrono/asíncrono

La regla (P13): **los eventos y las órdenes de reacción son asíncronos o de comando; las consultas son síncronas.** Criterios de decisión por interacción:

| Interacción | Sincronía | Por qué |
|---|---|---|
| Publicación de un evento (detección, incidente, verificación) | Asíncrona (broker) | El productor no espera ni conoce a los consumidores (P13); ráfagas del ataque se absorben en colas. |
| Orden de mitigación (Políticas → Controlador) | Síncrona (northbound) | La plataforma debe saber que la regla **se aplicó** antes de dar la acción por ejecutada (I2). |
| Instalación de reglas (Controlador → Switch) | Comando con confirmación | OpenFlow es petición-respuesta con `xid`; el resultado se confirma. |
| Consultas de consola (incidentes, políticas, dispositivos) | Síncrona (API) | El operador espera una respuesta; encolar preguntas no aporta nada (P4). |
| Login en el portal (IAM → IdP para la comunidad; repositorio propio + TOTP para operadores) | Síncrona | La persona espera el resultado de su autenticación. |
| Lectura de contadores (Monitor → Controlador → Switch) | Síncrona periódica | Sondeo con respuesta; no es un evento. |

El broker transporta **eventos y órdenes de reacción**, nunca preguntas (doc 02).

## 3. Catálogo de eventos

Cada evento declara productor, consumidores y payload mínimo. El catálogo es el contrato entre servicios (P13, doc 04).

| Evento | Productor | Consumidores | Payload mínimo |
|---|---|---|---|
| `DeviceConnected` | Controlador (primer PACKET_IN) | Registro, Monitor, Auditoría | MAC, IP, DPID, puerto, instante |
| `MAC_Moved` | Monitor | Incidentes, Políticas, Auditoría | MAC, ubicación anterior, ubicación nueva |
| `AnomalyDetected` | Detection Engine | Incidentes, Consola, Auditoría | tipo, destino, fuentes, tasas, línea base, desviación |
| `IncidentOpened` | Incident Manager | Políticas, Consola, Auditoría | INC-id, tipo, objetivo, severidad |
| `MitigationRequired` | Policy Engine | Controlador (comando, no broker), Auditoría | INC-id, acción (RATE_LIMIT/BLOCK/…), objetivo, orígenes, TTL |
| `MitigationApplied` | Controlador | Monitor, Incidentes, Auditoría | INC-id, reglas instaladas, switches |
| `MitigationVerified` | Monitor | Incidentes, Políticas, Auditoría | INC-id, tasas antes/después |
| `MitigationExpired` | Monitor / Controlador | Incidentes, Políticas, Auditoría | INC-id, regla, motivo (timeout/retirada) |
| `ElevationRequested` | IAM (solicitud del académico) | Políticas, Consola, Auditoría | solicitante, perfil pedido, alcance, duración |
| `ElevationGranted` | Policy Engine | Controlador (comando), Auditoría | solicitante, perfil, TTL |
| `ElevationExpired` | Policy Engine | Controlador (comando), Auditoría | solicitante, perfil, motivo |
| `SessionOpened` / `SessionClosed` | IAM/AAA | Políticas, Auditoría | identidad, perfil o rol, dispositivo, instante |
| `DeviceRegistered` / `DeviceRevoked` | Registro | Auditoría, Consola | MAC, titular, rol, responsable, vigencia |

**Nota sobre `MitigationRequired`, `ElevationGranted` y `ElevationExpired`:** son decisiones que deben **aplicarse con confirmación**, por eso además de publicarse (para que la Auditoría y la Consola los vean) viajan como comandos northbound al Controlador. El evento informa; el comando ejecuta.

## 4. Orden de eventos por incidente

La cadena de un incidente (INC-0042) puede emitir muchos eventos en poco tiempo. El orden se garantiza así:

- El payload de cada evento lleva el **id del incidente** y un **número de secuencia** monotónico por incidente.
- Los consumidores agregan por incidente y procesan en orden de secuencia; un evento fuera de orden se reordena o se descarta, nunca se aplica fuera de sitio.
- El mecanismo de entrega ordenada (colas por incidente, particionado) es decisión de la Fase F; el contrato de secuencia es de este documento.

## 5. Matriz de comunicación completa

| Par | Canal | Sincronía | Qué fluye |
|---|---|---|---|
| Switch → Controlador | SDN (I1) | Asíncrono | PACKET_IN, PORT_STATUS, FLOW_REMOVED |
| Controlador → Switch | SDN (I1) | Comando + confirmación | FLOW_MOD, METER_MOD, GROUP_MOD, PACKET_OUT, MULTIPART |
| Controlador ↔ Switch | SDN (I1) | Periódico | ECHO (latido) |
| Servicios → Controlador | Northbound (I2) | Síncrono | Órdenes de política, consultas de topología/estado |
| Monitor → Controlador → Switch | I8 (vía I2+I1) | Síncrono periódico | Contadores |
| Servicio → Broker → Servicios | Broker (I5) | Asíncrono | Eventos del catálogo (§3) |
| Consola → Servicios | API (I7) | Síncrono | Consultas y órdenes administrativas |
| Poblaciones → Portal → IAM | I3 | Síncrono | Credenciales, sesión |
| IAM → IdP | I4 | Síncrono | Verificación de identidad y atributos de la comunidad |
| Servicio → Repositorio | I6 | Síncrono local | Lectura/escritura de datos propios |

## 6. Cuestiones abiertas

- **Mecanismo de entrega ordenada** del broker (colas por incidente, particionado): Fase F.
- **Confirmación de los comandos northbound.** Si basta la confirmación de OpenFlow (regla instalada) o se exige además la verificación por contadores antes de declarar `MitigationApplied`.
- **Retención de eventos en el broker.** Cuánto tiempo se conservan los eventos consumidos; ligado a la retención de logs (fase A, cuestión abierta).

# Planos y capas

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Este documento distingue dos organizaciones que conviene no confundir: los **planos SDN** (dónde vive cada función respecto de la red) y las **capas** del estilo arquitectónico (cómo se organiza el software, doc 01). La superposición de ambas es el mapa completo del sistema.

## 1. Los tres planos SDN

| Plano | Función | Componentes |
|---|---|---|
| **Plano de datos** | Reenviar, descartar, limitar y medir el tráfico, según las reglas instaladas. | Switches (pipeline, groups, meters, contadores), hosts, servidores protegidos. |
| **Plano de control** | Mantener el conocimiento de la red y traducir decisiones a reglas. | Controlador SDN. |
| **Plano de gestión** | Definir políticas, observar, decidir y administrar; el cerebro de la seguridad. | Servicios de la plataforma (IAM, Registro, Monitor, Detección, Incidentes, Políticas, Auditoría), consola y portal. |

La separación de planos es P1: el plano de datos ejecuta, el de control traduce, el de gestión decide. Ningún componente cruza su plano: los servicios no hablan OpenFlow; los switches no deciden; el controlador no define políticas.

## 2. Las cinco capas del estilo

Las capas (doc 01, §3.1) organizan el software de arriba hacia abajo según la distancia al problema de red:

| Capa | Contenido |
|---|---|
| **Interacción** | Consola de administración, portal cautivo, northbound API. |
| **Aplicación** | IAM/AAA, Registro de dispositivos, gestión de incidentes, monitoreo. |
| **Seguridad** | Detección, políticas y decisión (Monitor, Detection, Incident, Policy). |
| **Control SDN** | Controlador SDN. |
| **Infraestructura** | Switches, hosts, servidores protegidos. |

La regla de dependencia entre capas: **cada capa depende solo de la inmediatamente inferior**, con una excepción explícita — los eventos cruzan capas a través del broker, sin crear dependencia directa (P13).

## 3. Superposición: capas × planos

```text
                     PLANO DE           PLANO DE          PLANO DE
                     GESTIÓN            CONTROL           DATOS
                ┌──────────────┐
 Interacción   │ Consola ·    │
               │ Portal · API │
               ├──────────────┤
 Aplicación    │ IAM · Regis- │
               │ tro · Inci-  │
               │ dentes ·     │
               │ Monitoreo    │
               ├──────────────┤
 Seguridad     │ Detección ·  │
               │ Políticas ·  │
               │ Decisión     │
               └──────┬───────┘
                      │ northbound
               ┌──────▼───────┐
 Control SDN   │ Controlador  │
               └──────┬───────┘
                      │ OpenFlow (canal de control)
               ┌──────▼───────┐
 Infraestructura│  Switches   │────────────► hosts y
               │  (pipeline)  │              servidores
               └──────────────┘
```

- Las tres capas superiores viven íntegramente en el **plano de gestión**.
- La capa de control SDN **es** el plano de control.
- La capa de infraestructura **es** el plano de datos (con los activos protegidos y los hosts).
- El tráfico de usuario cruza solo el plano de datos; las decisiones cruzan de gestión a control a datos; la observación sube en sentido inverso.

## 4. Por qué la separación gestión/control importa aquí

En SDN es común hablar solo de "plano de control y plano de datos", con las aplicaciones dentro del control. En esta solución, la plataforma de seguridad es demasiado grande para eso: tiene autenticación, registro, incidentes y auditoría que **no son** funciones de control de red. Separar el plano de gestión del plano de control:

- hace explícito que las aplicaciones **no tocan los switches** (P1) y que el controlador no define políticas (P8);
- permite desplegar los servicios como microservicios (doc 04) sin tocar el controlador;
- alinea la protección del plano de control (RA-09): solo el controlador y los operadores autenticados alcanzan la red de gestión; los servicios hablan con el controlador por la northbound API, no por el canal de datos.

## 5. La realización física de los planos

- **Plano de datos:** la red del campus del prototipo (tráfico de hosts y servidores).
- **Plano de control:** el canal OpenFlow por la **red de gestión out-of-band** (RP-11; variante in-band en la serie de flujo, parte 2).
- **Plano de gestión:** el servidor de control que aloja los servicios y la consola, alcanzable solo por operadores autenticados (RA-09).

La topología lógica que materializa estos planos está en [`10_topología_lógica.md`](10_topología_lógica.md).

## 6. Cuestiones abiertas

- **Ubicación de la consola.** Si la consola vive en la red de gestión (solo operadores) o es alcanzable desde la red académica con autenticación — la primera opción es la coherente con RA-09; decidir en Fase H.
- **In-band.** Si el canal de control comparte la infraestructura de datos (VLAN de gestión), los planos de datos y control comparten enlaces físicos aunque sigan lógicamente separados.

# Topología lógica

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

La topología lógica de referencia: los segmentos, el direccionamiento propuesto y el despliegue del prototipo. Es una **propuesta de referencia** — la definición definitiva de segmentación pertenece a la Fase H; aquí se fija la estructura mínima que los flujos (doc 12) necesitan.

## 1. Segmentos de referencia

| Segmento | Población | Propósito | Protección |
|---|---|---|---|
| **Acceso académico** | Usuarios académicos (BASE; ACADÉMICO tras el login) | Conectividad de consumo: en BASE, DHCP, DNS y portal; tras el login, servicios académicos e Internet | Perfil BASE + deny by default |
| **Servidores** | Servicios institucionales y académicos | Alojar los activos protegidos (R2) | Acceso según política; objetivo de R3/R4 |
| **Administración y gestión** | Controlador, servicios de la plataforma, consolas de operadores | Sostener el plano de control y de gestión | Solo operadores autenticados (RA-09) |
| **Perimetral** | Borde con redes externas | Punto de aplicación de R5 | Por definir (fase C) |

El canal de control (OpenFlow) usa una **red de gestión separada** (out-of-band); la variante in-band lo llevaría a una VLAN dedicada sobre los enlaces de datos (serie de flujo, parte 2).

## 2. Diagrama lógico

```text
                       ┌──────────────────────────────┐
                       │  SERVIDOR DE CONTROL         │
                       │  controlador SDN + servicios │
                       │  (plano de control y gestión)│
                       └──────────────┬───────────────┘
                                      │ canal de control out-of-band
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
      ┌──────┴──────┐          ┌──────┴──────┐          ┌──────┴──────┐
      │  SWITCH S1  │──────────│  SWITCH S2  │──────────│  SWITCH S3  │
      └──┬───────┬──┘          └──────┬──────┘          └──────┬──────┘
         │       │                    │                        │
    ┌────┴───┐   └─────────┐   ┌──────┴─────┐            ┌─────┴─────┐
    │ HostA  │  HostB      │   │  HostC     │            │  SRV-1    │
    │(académ.│  (académ.   │   │ (atacante  │            │ (servidor │
    │  p1)   │   p2)       │   │ controlado)│            │ protegido)│
    └────────┘             │   └────────────┘            └───────────┘
                     ┌─────┴──────────────┐
                     │  SRV-DHCP/DNS      │
                     │  (servicios base)  │
                     └────────────────────┘
```

- Los **hosts académicos** se conectan a puertos de acceso; reciben perfil BASE; tras el login en el portal, el perfil ACADÉMICO (o la sesión de rol, si son operadores).
- El **host atacante** es tráfico controlado dentro del entorno (RP-06, RP-08): se conecta como un académico más y genera el tráfico de ataque de R3/R4.
- **SRV-1** representa el activo protegido (destino de R2 y de los ataques).
- Los **servicios base** (DHCP/DNS) sirven al flujo de arranque (serie de flujo, parte 2).

### 2.1 Los tres niveles de la referencia

La topología de referencia se organiza en **tres niveles**:

```text
        ACCESO                 DISTRIBUCIÓN                NÚCLEO
   ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
   │  switches    │        │  switches    │        │  switches    │
   │  de acceso   │────────│  de distribu-│────────│  de núcleo   │──── servicios
   │              │        │  ción        │        │              │     (portal · DHCP/DNS ·
   └──────┬───────┘        └──────────────┘        └──────────────┘      servidores)
          │
       hosts
   (BASE · ACADÉMICO)
```

- **Acceso** — donde se conectan los dispositivos; aloja la política: perfil BASE, escalera de prioridades, anti-spoofing y portal.
- **Distribución** — agregación: une los accesos entre sí y con el núcleo; es el ámbito natural de los caminos.
- **Núcleo** — la troncal: conecta los servicios de infraestructura y los caminos principales.

Cuántos switches tiene cada nivel, cómo se conectan y qué redundancia existe quedó fijado en la Fase H: **ocho switches — dos núcleo, dos distribución, cuatro acceso — dual-homed, con 13 enlaces** ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §3). El diagrama de arriba es la vista de niveles; las cantidades y los enlaces concretos viven en la Fase H. El cálculo de caminos por destino que opera sobre estos niveles está en la serie de flujo, parte 5.

## 3. Direccionamiento propuesto

| Segmento | Subred propuesta | Nota |
|---|---|---|
| Acceso académico | 10.1.0.0/24 | Hosts con IP estática en el prototipo; el controlador aprende MAC/IP/puerto |
| Servidores | 10.2.0.0/24 | SRV-1 y servicios institucionales |
| Administración y gestión | 10.0.0.0/24 | Controlador y servicios; inalcanzable desde BASE |
| Canal de control (out-of-band) | red de gestión propia | Separada de las anteriores |

El direccionamiento definitivo del prototipo quedó fijado en la Fase H ([`H-03`](../H-Despliegue/03_red.md)); el diseño de reglas usa rangos por segmento (`ip_dst = 10.0.0.0/24` para denegar la gestión), no direcciones sueltas.

## 4. El prototipo: qué se despliega

| Elemento | Despliegue en el prototipo | Referencia |
|---|---|---|
| Controlador SDN | Se despliega (servidor de control) | Decisión tecnológica: Fase F |
| Switches | Se despliegan (Pica8/PicOS, virtuales o físicos) | RP-11 |
| Servicios de la plataforma | Se despliegan consolidados en el servidor de control | doc 04 §6, RP-04 |
| Hosts académicos | Se simulan (mínimo 2, para demostrar tráfico entre pares) | C-04 |
| Servidor protegido (SRV-1) | Se simula | Activo protegido |
| Servicios base (DHCP/DNS) | Del propio entorno virtual | C-04 |
| Host atacante | Se simula, tráfico controlado | RP-06, RP-08 |
| Segmento externo | Se representa | C-04 |

La topología rígida admite la aparición de dispositivos nuevos: todo lo que conecte y no esté en el registro privilegiado recibe perfil BASE (P5, P7).

## 5. Lo que esta topología garantiza

- **R1/R2 demostrables:** los DROP hacia 10.0.0.0/24 desde el segmento académico son medibles con contadores.
- **R3/R4 demostrables:** el host atacante y los académicos comparten el segmento; el ataque hacia SRV-1 recorre el camino real del plano de datos y la mitigación se instala en el switch de ingreso (P9).
- **Observación completa:** cada flujo relevante pasa por un switch con contadores (P11).

## 6. Cuestiones abiertas

- **Número de switches por nivel, conexiones y resiliencia** — cerrado en la Fase H: ocho switches dual-homed ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md)); el efecto de un fallo sobre los caminos instalados se resuelve con recálculo o grupos fast-failover ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4).
- **Hardware físico vs virtual.** La topología lógica es la misma; cambia el despliegue (Fase H).
- **Perímetro.** Si el segmento perimetral se representa con un firewall, con reglas de borde o no se representa (fase C).
- **In-band.** Si el canal de control adopta la VLAN de gestión sobre los enlaces de datos.

# Seguridad arquitectónica

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Cómo la arquitectura realiza la seguridad: la jerarquía de confianza, los puntos de enforcement, la protección del plano de control y la cobertura de amenazas. No repite los mecanismos (están en la serie de flujo); fija **dónde** actúa cada control y por qué.

## 1. La jerarquía de confianza

```text
Sin presencia en campus            →  sin acceso
Presencia física en campus         →  perfil BASE (confianza inicial, RP-13)
Login en el portal                 →  perfil ACADÉMICO (comunidad)
                                      o identidad + rol (operadores)
Autorización contextual            →  privilegios adicionales (TTL / sesión)
```

Cada peldaño habilita el siguiente y ninguno puede saltarse (P6): la presencia física jamás justifica privilegios; el registro de dispositivos jamás concede por sí solo; el login sin contexto vigente no produce reglas permanentes.

## 2. Puntos de enforcement

| Punto | Qué aplica | Mecanismo |
|---|---|---|
| **Switch de ingreso** | El perfil BASE: denegación por defecto hacia infraestructura y mínimo de conectividad (DHCP, DNS y portal) | Entradas de flujo con prioridades (DROP a red de gestión, prioridad 100) |
| **Portal cautivo / IAM** | La identidad de la población: perfil ACADÉMICO (comunidad) o sesión de rol (operadores) | Autenticación contra el IdP o contra el repositorio propio con MFA; sesión con vigencia |
| **Policy Engine** | La autorización contextual: qué perfil corresponde a cada sesión o elevación | Condiciones ABAC-like (identidad + dispositivo + contexto + recurso + acción + vigencia) |
| **Controlador** | La traducción de cada decisión a reglas concretas y reversibles | FLOW_MOD con cookie, prioridad y timeouts |
| **Plano de datos (meter/drop)** | La mitigación en el punto de ingreso | Meters para limitar; DROP para bloquear; ambos temporales (P10) |
| **Registro de dispositivos** | La pertenencia al catálogo privilegiado | Match explícito; no match → BASE (P7) |

La misma decisión atraviesa todos los puntos en orden: perfil por defecto → identidad (si eleva) → política contextual → regla → ejecución → verificación.

## 3. Protección del plano de control (RA-09)

El controlador y sus interfaces administrativas son el objetivo de mayor valor de la solución. La arquitectura los protege en tres niveles:

1. **Aislamiento de red.** El controlador vive en la red de gestión, separada del plano de datos (out-of-band). Desde el perfil BASE existe una entrada DROP explícita hacia esa red: ningún usuario académico la alcanza, ni siquiera para escanearla.
2. **Identidad exigida.** Solo los operadores autenticados (portal/AAA) obtienen entradas que permiten alcanzar la gestión, con prioridad mayor y con idle_timeout ligado a la sesión (P6, P10).
3. **Canal de control sano.** El canal OpenFlow usa TCP 6653 en la red de gestión; los switches solo aceptan a su controlador configurado. La variante in-band exige además priorización del tráfico de control (serie de flujo, parte 2 §14).

## 4. Cobertura de amenazas

El listado consolidado de ataques y amenazas, con su origen y descripción, está en [`11.1_catalogo_de_ataques_y_amenazas.md`](11.1_catalogo_de_ataques_y_amenazas.md). Aquí se fija el control que la arquitectura aplica a cada uno:

| Amenaza | Control arquitectónico | Referencia |
|---|---|---|
| Atacante externo (R5) | Segmento perimetral con inspección y bloqueo por indicadores; integración SDN de los eventos de borde | R5.x; perímetro por definir (fase C) |
| Atacante interno (R3) | Perfil BASE restrictivo + detección de scanning/spoofing + respuesta escalonada | R3.x, P8 |
| Nodo comprometido (R3/R4) | Detección por anomalía + aislamiento del dispositivo (ISOLATE_DEVICE / cuarentena) | R3.7, R4.5 |
| DDoS volumétrico (R4) | Línea base + detección de tasas + mitigación en el switch de ingreso (meter/drop) | R4.x, P9 |
| Brute-force de solicitudes (R4) | Detección de intentos/conexiones por segundo + RATE_LIMIT/BLOCK por origen | R4.x |
| Suplantación de MAC | MAC como atributo (P7) + eventos MAC_MOVE + port security/802.1X en puertos sensibles | R3.3, flujo parte 3 |
| Compromiso del IdP | Es externo: el IAM consume su veredicto y la auditoría registra toda sesión; la mitigación no depende del IdP una vez establecida la sesión | SE-02, fase C |

## 5. Controles administrativos

La seguridad no termina en la red: las acciones de los operadores están controladas y registradas:

- **Separación de funciones.** Ningún rol define, aplica y evalúa una política sin control (fase A §2.6, doc 06 §4).
- **Registro con aprobación.** Las altas de operadores y de dispositivos privilegiados exigen decisión de autorización, vigencia explícita y responsable identificado (P30).
- **Accounting.** Toda mitigación y cambio queda asociado a su autor, motivo e incidente (P11).
- **Reversión obligatoria.** Toda medida temporal expira o se retira; el estado BASE es el punto de retorno (P10).

## 6. Datos sensibles

| Dato | Dónde vive | Protección |
|---|---|---|
| Credenciales de la comunidad | IdP institucional (externo) | El IAM no las almacena: consulta y descarta |
| Credenciales de operadores | Repositorio propio del IAM | Almacenadas con hash; MFA obligatorio (TOTP) |
| Registro de dispositivos privilegiados | `DeviceRepository` | Acceso solo por el servicio y por operadores autorizados; cada cambio auditado |
| Incidentes y eventos | `IncidentRepository`, `AuditRepository` | Consulta según rol (P08, P25); retención por definir |
| Reglas instaladas | Pipeline de los switches | Solo el controlador las modifica (P1) |

## 7. Lo que la arquitectura no cubre

- **Seguridad física del campus.** Asumida como condición de confianza (RP-13); su compromiso degrada el modelo a perfil BASE generalizado, y por eso se documenta como restricción, no se ignora.
- **Cifrado extremo a extremo del tráfico de usuario.** No es objetivo de la solución: se controla *quién puede* alcanzar qué, no el contenido de lo permitido.
- **Red inalámbrica y red de invitados.** Fuera del alcance hasta que se confirme lo contrario (fase A).

## 8. Cuestiones abiertas

- **Integración con el firewall perimetral.** Si existe uno institucional con el que integrarse (R5, fase C).
- **Retención e integridad de logs.** Cuánto tiempo se conservan y si se protegen contra manipulación (ligado a la retención de eventos del doc 08).

# Catálogo de ataques y amenazas

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Listado consolidado de los ataques y amenazas de los que la solución debe defenderse, con su requerimiento de origen y su control arquitectónico. Complementa la sección 4 de [`11_seguridad_arquitectonica.md`](11_seguridad_arquitectonica.md); los requerimientos de origen están en [`../B-Drivers_de_arquitectura/01.1_RF_funcionales.md`](../B-Drivers_de_arquitectura/01.1_RF_funcionales.md).

## 1. Ataques

| Ataque | Qué es | Origen | Control arquitectónico |
|---|---|---|---|
| **Network / port scanning** | Sondeo de la red o de los puertos de un servidor para descubrir qué existe y qué está abierto. | R3.2 · CU-05 | Detección por anomalía (múltiples intentos de conexión a destinos distintos); respuesta escalonada RATE_LIMIT → BLOCK. |
| **IP spoofing** | Tráfico cuyo origen declarado no coincide con el origen real (inconsistente con la ubicación aprendida del dispositivo). | R3.3 · CU-06 | El controlador asocia MAC/IP/puerto en el aprendizaje; el tráfico incoherente genera evento y respuesta. La manipulación de DNS es un vector relacionado (SE-04). |
| **Suplantación de MAC** | Un dispositivo cambia su MAC para suplantar a otro o evadir su perfil. | R3.3 · flujo parte 3 | La MAC es atributo, no credencial (P7): evento MAC_MOVE ante la incoherencia; port security/802.1X en puertos sensibles. |
| **Ataques distribuidos** | Múltiples orígenes coordinados contra un mismo recurso. | R3.5 | Detección por número de fuentes contra la línea base; mitigación por switch de ingreso de cada origen. |
| **DDoS volumétrico (flood)** | Saturación del ancho de banda, de pps o de la capacidad del servidor objetivo. | R4 · CU-07 | Línea base + detección de tasas; mitigación en el switch de ingreso con meter o DROP; verificación por contadores; recuperación con timeouts. |
| **Brute-force de solicitudes** | Exceso de intentos/conexiones por segundo desde un origen (p. ej. adivinanza de credenciales). | R4 | Detección de solicitudes por segundo por origen; RATE_LIMIT o BLOCK del origen. |
| **Ataques desde el exterior** | Tráfico malicioso originado fuera del campus contra el perímetro o los servicios publicados. | R5 · CU-08 | Inspección perimetral, bloqueo por indicadores maliciosos (R5.6) e integración de los eventos de borde con la red SDN (R5.7). |

**Asignación del curso:** R4 es el requerimiento asignado al grupo y su ciclo completo es obligatorio; R3 y R5 quedan cubiertos por la arquitectura, con escenarios demostrables (scanning, spoofing) según la priorización P1.

## 2. Amenazas y fuentes

No son ataques en sí: son las entidades de las que proviene el tráfico malicioso o el estado que lo permite.

| Amenaza | Qué es | Implicación para la solución |
|---|---|---|
| **Atacante externo** | Entidad sin identidad válida que opera desde redes externas. | Objeto de R5 y, si atraviesa el perímetro, de R3/R4. |
| **Atacante interno** | Persona con acceso legítimo (presencia física; BASE y, tras el login, ACADÉMICO) que genera actividad maliciosa. | Obliga a separar acceso de confianza: el perfil BASE restringe y la detección vigila (R3/R4). |
| **Nodo comprometido** | Dispositivo legítimo bajo control ajeno, con o sin conocimiento de su usuario. | Su tráfico es objeto de R3/R4 aunque el usuario conserve credenciales válidas; se aísla o bloquea. |

## 3. Estados que habilitan ataques

- **Suplantación de identidad institucional comprometida (IdP):** si el IdP se compromete, se compromete la autenticación de la comunidad universitaria (SE-02). El IAM consume su veredicto; los operadores se verifican contra el repositorio propio, y la mitigación ya activa no depende del IdP.
- **Manipulación del servicio de nombres (DNS):** la suplantación de respuestas DNS es un caso de origen inconsistente (R3.3) y un vector para redirigir tráfico legítimo.
- **Desincronización de tiempo (NTP):** deteriora la correlación de eventos y la auditoría (RNF-09), sin ser un ataque en sí.

## 4. Cuestiones abiertas

- El desglose de técnicas concretas de R5 (qué ataques externos se demuestran, si se demuestra alguno) sigue abierto: R5 no está asignado al grupo.
- Los umbrales que separan tráfico legítimo de ataque (pps, Mbps, nº de fuentes) se fijan con mediciones del prototipo.

# Flujos arquitectónicos principales

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** D — Arquitectura de alto nivel (HLD)
**Estado:** Borrador formal para revisión

---

Los flujos de extremo a extremo de la arquitectura, a nivel de componentes y eventos. La exposición detallada paso a paso —con los mensajes OpenFlow exactos— vive en la serie de flujo (`flows/`, partes 0–5); este documento resume cada flujo como cadena de componentes y lo ancla a los requerimientos.

## F1 — Arranque y descubrimiento de la red

**Disparador:** encendido de switches y controlador.

```text
Switch (boot) → canal OpenFlow → FEATURES (capacidades declaradas)
Controlador → FLOW_MOD: table-miss → CONTROLLER
Controlador → FLOW_MOD: eth_type=0x88CC → CONTROLLER   (captura LLDP)
Controlador → PACKET_OUT (LLDP por cada puerto de cada switch)
Switches → PACKET_IN (LLDP del vecino, OFPR_ACTION)
Controlador → deducción de enlaces dirigidos + confirmación bidireccional
           → grafo de topología
Controlador → (+ inventario de servicios) FLOW_MOD por destino:
              caminos hacia los servicios (proactivo; parte 5)
```

**Resultado:** la red conoce su topología y sus caminos hacia los servicios; lista para reaccionar al tráfico. **Detalle:** serie de flujo, partes 2 §2–5 y 5. **Cubre:** RT-05, RP-02.

## F2 — Conexión de un dispositivo y perfil BASE

**Disparador:** primer paquete de un host (DHCPDISCOVER).

```text
Host → frame → Switch → table-miss → PACKET_IN (OFPR_NO_MATCH)
Controlador → aprende host (MAC, IP, switch, puerto) → evento DeviceConnected
Controlador → camino al servidor DHCP por la ruta calculada (sin inundación)
           → FLOW_MOD: identidad en el acceso, destino en el interior
Host ↔ DHCP → diálogo completo (sin pasar por el controlador)
Controlador → entradas del perfil BASE:
              PERMITIR DHCP, DNS y portal   (prioridad 10 / 150)
              DROP hacia red de gestión     (prioridad 100)
```

**Resultado:** el dispositivo opera con privilegios mínimos —DHCP, DNS y una sola puerta, el portal—; el resto llega con el login (P5, P6). **Detalle:** serie de flujo, partes 2 §6–10, 5 §6 y 3 §2. **Cubre:** R1, R2.

## F3 — Login en el portal y sesión privilegiada

**Disparador:** login en el portal cautivo.

```text
Académico → portal → credenciales → IAM/AAA → IdP (identidad válida)
          → perfil ACADÉMICO: servicios académicos e Internet (idle_timeout)
Operador  → portal → paso 1: repositorio propio · paso 2: TOTP
          → identidad + dispositivo (match con registro) + contexto
          → decisión: sesión de rol (p. ej. ADMIN_RED)
IAM → evento SessionOpened
Policy Engine → comando northbound al Controlador
Controlador → FLOW_MOD: acceso de persona y destinos del rol
              (ALLOW hacia red de gestión, prioridad 200,
               idle_timeout = sesión)
Sesión cerrada / inactividad → idle_timeout expira
→ el switch elimina la entrada solo → dispositivo regresa a BASE
→ evento SessionClosed (FLOW_REMOVED lo confirma)
```

**Resultado:** el privilegio dura lo que dura la sesión y es reversible sin intervención (P10). **Detalle:** serie de flujo, parte 3 §5–6. **Cubre:** R1.2, R1.9, RA-09.

## F4 — Solicitud y aprobación de elevación temporal

**Disparador:** solicitud de un usuario académico (P28).

```text
Usuario académico → solicitud (perfil, alcance, duración, justificación)
IAM → evento ElevationRequested → Consola (visible para el Admin. Red)
Administrador de Red → aprueba o rechaza (P29)
Policy Engine → política temporal ABAC-like con TTL
              → evento ElevationGranted → comando al Controlador
Controlador → FLOW_MOD: ALLOW al recurso pedido (prioridad 200, TTL)
TTL vence → Policy Engine emite ElevationExpired
          → Controlador retira la regla (FLOW_MOD DELETE)
```

**Resultado:** un permiso excepcional con fecha de caducidad, aprobado por quien administra la red y registrado en auditoría (P10, P11). **Detalle:** serie de flujo, parte 3 §7. **Cubre:** R1.3, R1.5, P28–P29.

## F5 — Registro de operador y de dispositivo privilegiado

**Disparador:** incorporación de un operador o de un equipo de operación.

```text
Fase A — Solicitud: persona, identificación, rol, área, justificación,
        vigencia, solicitante/aprobador
Fase B — Aprobación: según jerarquía (SA registra admins y TI;
        Admin registra dispositivos, P30)
        → alta en IAM (identidad + rol, con valid_from/valid_until)
        → alta en el Registro de dispositivos (MAC, titular, vigencia)
        → evento DeviceRegistered → Auditoría
Fase C — Autenticación: el alta NO produce reglas; el operador
        obtiene privilegios solo al hacer login (F3)
```

**Resultado:** el registro y la red quedan separados: el catálogo habilita, no concede (P7); la auditoría sabe quién registró qué (P11). **Detalle:** serie de flujo, parte 3 §8. **Cubre:** R1.7, P24, P30.

## F6 — Ciclo completo de R4: detección y mitigación

**Disparador:** tráfico anómalo hacia un servidor protegido.

```text
Monitor (fondo): sondeo de contadores (MULTIPART) → línea base
Monitor → métricas → Detection Engine (cadena Pipe-and-Filter)
Detection → evento AnomalyDetected (tipo, tasas, desviación)
Incident Manager → IncidentOpened (INC-0042, severidad)
Policy Engine → decisión según escalera (RATE_LIMIT → BLOCK → …)
              → evento MitigationRequired + comando northbound
Controlador → FLOW_MOD en el switch de INGRESO de cada origen:
              Meter(m1) o DROP (prioridad 1000, cookie=INC-0042,
              hard_timeout 300 s)
Switch → ejecuta en el plano de datos → MitigationApplied
Monitor → relee contadores: 900 → 35 Mbps → MitigationVerified
Incident Manager → MITIGATED
```

**Resultado:** la cadena completa detección → decisión → aplicación → verificación, con un responsable por eslabón (P8) y mitigación cerca del origen (P9). **Detalle:** serie de flujo, parte 4. **Cubre:** R4, RA-06, RT-08.

## F7 — Recuperación y restauración post-incidente

**Disparador:** verificación de que el ataque terminó (o expiración del timeout).

```text
Monitor: el flujo mitigado ya no supera umbrales → MitigationExpired
  (o hard_timeout expira → FLOW_REMOVED lo informa)
Incident Manager → RECOVERED
Policy Engine → comando de retirada al Controlador
Controlador → FLOW_MOD DELETE (por cookie INC-0042)
Switch → elimina la regla de mitigación → política original activa
Incident Manager → CLOSED
Auditoría → registro completo: quién detectó, quién decidió,
            quién aplicó, cuándo se retiró y por qué
```

**Resultado:** la regla vive exactamente lo que vive el ataque; el usuario legítimo recupera su conectividad sin intervención manual (P10). **Detalle:** serie de flujo, parte 4 §9–10. **Cubre:** R4.9, RT-10.

## Flujo de fondo: monitoreo continuo

Todos los flujos anteriores se apoyan en un flujo permanente: el Monitor sondea contadores, actualiza la línea base y verifica las mitigaciones activas. Sin él, F6 y F7 no existen. Su frecuencia es configurable y depende de los umbrales que se fijen en la Fase F.

## Cuestiones abiertas

- **Intervención humana en F6.** La aprobación del Administrador de Red para aislamientos de alto impacto está definida; queda fijar qué otras acciones la exigen con las mediciones del prototipo.
- **F7 sin F6.** Si la mitigación fue manual (operador), la restauración sigue el mismo camino: la regla se retira igual (cookie + FLOW_MOD DELETE), y la auditoría registra al operador como actor.

--------------------------------------------------------------------

# Método de validación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Esta fase no introduce arquitectura nueva: **comprueba que el HLD (Fase D) responde a los drivers (Fase B)** y deja registrado lo que todavía no tiene dueño. Cada comprobación termina en un veredicto con evidencia; los huecos quedan listados con la acción que los cierra.

## 1. Qué se comprueba

| Documento | Comprueba | Contra |
|---|---|---|
| `01_casos_de_uso_a_componentes.md` | Que cada caso de uso tiene componentes que lo realizan | [B-00](../B-Drivers_de_arquitectura/00_Proyecto_ConOps_y_CU.md) §5 (CU-01–CU-10) |
| `02_requisitos_a_componentes.md` | Que cada requisito tiene dueño arquitectónico | [B-01.1](../B-Drivers_de_arquitectura/01.1_RF_funcionales.md) (R1–R5) y [B-01.2](../B-Drivers_de_arquitectura/01.2_RQ_transversales-de_calidad-arquitectonicos.md) (RT, RNF, RA) |
| `03_atributos_de_calidad_a_decisiones.md` | Que cada atributo de calidad se resuelve en una decisión concreta | B-01.2 y los principios (D-03) |
| `04_escenarios_de_fallo.md` | Qué ocurre ante la caída de cada pieza y qué tolerancia a fallos existe por diseño | D-04, D-05 y las restricciones (C-04) |
| `05_escenarios_de_ataque.md` | Que cada amenaza del catálogo tiene detección y respuesta asignadas | D-11.1 y la serie de flujo |

## 2. Veredictos

- **Cubierto** — hay componente, mecanismo descrito y evidencia documental.
- **Parcial** — existe el mecanismo, pero falta una pieza o una precisión; se indica cuál y dónde se cierra.
- **Hueco** — no hay dueño; se registra con la acción y la fase que lo cierra.

Un hueco registrado no invalida el HLD: la validación existe para que nada quede sin dueño visible. La lista de huecos queda al final de cada documento.

## 3. Entradas

- Casos de uso y criterios de éxito: B-00 §5 y §8.
- Requisitos: B-01.1 (R1–R5) y B-01.2 (RT-01–RT-10, RNF-01–RNF-12, RA-01–RA-09).
- Arquitectura: D-01–D-12; catálogo de amenazas: D-11.1.
- Mecanismos paso a paso: la serie de flujo, partes 0–5 (`flows/`).

## 4. Salida

Los documentos de esta fase. Los huecos que resulten alimentan la fase de decisiones tecnológicas y el prototipo.

# Casos de uso → componentes

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Cada caso de uso de [B-00](../B-Drivers_de_arquitectura/00_Proyecto_ConOps_y_CU.md) §5, con los componentes del HLD que lo realizan y dónde está descrito su mecanismo. La secuencia detallada de cada flujo vive en la serie de flujo (partes 0–5); aquí se comprueba que **ningún caso queda sin dueño**.

## 1. Casos de uso y componentes

| Caso de uso | Componentes que lo realizan | Dónde está descrito | Veredicto |
|---|---|---|---|
| **CU-01 — Acceso autorizado** | Switches (perfil BASE y escalera de prioridades) · Controlador (FLOW_MOD; camino al portal y a los servicios) · IAM/AAA con portal (RADIUS: IdP para la comunidad; repositorio propio + TOTP para operadores) · Policy Engine (perfil o sesión) · Registro de dispositivos (habilitación del operador) · Auditoría | Partes 2 y 3 §5–6; D-05 §1, §6–7 | Cubierto |
| **CU-02 — Acceso no autorizado** | Switches (DROP por defecto) · Controlador (regla de denegación) · Policy Engine · Auditoría (registro) | Parte 3 §2 y §6; D-11 §2 | Cubierto |
| **CU-03 — Acceso autorizado a recurso privilegiado** | Policy Engine (elevación con TTL; P28/P29) · Controlador (regla de sesión con idle_timeout) · Switches · IAM/AAA · Auditoría | Parte 3 §7; D-05 §5 | Cubierto |
| **CU-04 — Acceso no autorizado a recurso privilegiado** | Policy Engine (denegación) · Switches (DROP) · Auditoría | Parte 3 §6–7 | Cubierto |
| **CU-05 — Port scanning** | Monitor (línea base) · Detection Engine (múltiples destinos) · Incident Manager · Policy Engine (RATE_LIMIT → BLOCK) · Controlador · Switches | D-11.1; parte 4 | Cubierto |
| **CU-06 — IP spoofing** | Controlador (asociaciones MAC↔IP↔switch↔puerto; detección de incoherencia) · Monitor y Detection Engine (evento) · Policy Engine (respuesta escalonada) · Switches (port security en puertos sensibles) | Parte 3 §9; D-11 §4 | Cubierto (la MAC no se impide — se detecta, P7) |
| **CU-07 — DDoS interno** | Monitor (línea base por destino) · Detection Engine (desviación sostenida) · Incident Manager · Policy Engine (escalera de mitigación) · Controlador (METER_MOD / FLOW_MOD) · Switches | Parte 4; D-11 §4 | Cubierto |
| **CU-08 — Ataque externo** | — (sin componente de frontera asignado) | D-11.1 (amenaza); C-04 §6 y D-10 §6 (perímetro por definir) | **Hueco** |
| **CU-09 — Gestión de política** | Consola (interfaz) · IAM/AAA (sesión de operador con MFA) · Policy Engine (PolicyRepository) · Controlador (aplicación) · Auditoría | D-06 §4; componentes/02; access/02 | Cubierto |
| **CU-10 — Recuperación** | Policy Engine (expiración de TTL; retiro) · Controlador (retirada por cookie) · Monitor (MitigationVerified / MitigationExpired) · Incident Manager (cierre) · Auditoría | Parte 4; D-04 §3 (P10) | Cubierto |

## 2. Huecos

- **CU-08 — Ataque externo.** El perímetro no tiene componente asignado: R5 no está asignado a ningún grupo y el firewall está por definir (C-04 §6, D-10 §6). Se cierra al fijar el alcance del perímetro —sistema externo con el que integrarse o componente propio— y en la fase de decisiones tecnológicas (R5.2 pide evaluar IDS/IPS). Es el único caso de uso sin dueño.

# Requisitos → componentes

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Cada requisito de [B-01.1](../B-Drivers_de_arquitectura/01.1_RF_funcionales.md) (R1–R5) y [B-01.2](../B-Drivers_de_arquitectura/01.2_RQ_transversales-de_calidad-arquitectonicos.md) (RT, RNF, RA), con el componente del HLD que lo asume y dónde está descrito su mecanismo. Un requisito sin dueño es un hueco; un requisito cuyo valor concreto depende de mediciones queda marcado como pendiente de cuantificación (se cierra con el prototipo).

## 1. Requisitos funcionales

### R1 — Control de acceso según rol

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| R1.1 Identificación | Switches (MAC, puerto, switch, ubicación) · Controlador (asociación dispositivo↔ubicación) | Parte 2; D-04 §3 | Cubierto |
| R1.2 Autenticación | IAM/AAA con portal (RADIUS: IdP institucional para la comunidad; repositorio propio + TOTP para operadores) | Parte 3 §5; D-05 §6 | Cubierto |
| R1.3 Asignación de perfil | Policy Engine (BASE por defecto; ACADÉMICO o sesión de rol tras autenticación) · IAM/AAA | Parte 3 §5–6; D-05 §5–6 | Cubierto |
| R1.4 Política de acceso | Policy Engine (identidad, atributos, contexto, recurso, acción y vigencia → decisión) · Controlador (traducción a reglas) | Parte 3 §6; D-05 §5 | Cubierto |
| R1.5 Mínimo privilegio | Switches (DROP por defecto; BASE como lista cerrada) · Controlador | Parte 3 §2; D-11 §2 | Cubierto |
| R1.6 Denegación | Switches (DROP) · Controlador (regla de denegación) | Parte 3 §6; D-11 §2 | Cubierto |
| R1.7 Administración | Consola · IAM/AAA · Registro de dispositivos privilegiados | D-06 §4; D-05 §10, §6–7 | Cubierto |
| R1.8 Superusuarios | IAM/AAA (perfiles ADMIN_RED y SUPER_ADMIN, uso restringido) | D-05 §6; A-01 | Cubierto |
| R1.9 Trazabilidad | Auditoría | Parte 3 §6; D-05 §8 | Cubierto |
| R1.10 Escalabilidad | Arquitectura (registro acotado a dispositivos privilegiados; crecimiento previsto en el diseño) | D-08; parte 0 | Cubierto (magnitud en prototipo) |

### R2 — Protección de recursos privilegiados

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| R2.1 Inventario | Catálogo de recursos (fase A) como entrada del Policy Engine | A-02; D-05 §5 | Cubierto |
| R2.2 Clasificación | Catálogo con niveles general/privilegiado/crítico (fase A) | A-02 §1 | Cubierto |
| R2.3 Asociación de políticas | Policy Engine (PolicyRepository: cada recurso restringido con su política) | D-05 §5; componentes/02 | Cubierto |
| R2.4 Autorización | Policy Engine · IAM/AAA (verificación antes de permitir) | Parte 3 §6–7 | Cubierto |
| R2.5 Denegación | Switches (DROP) · Controlador | Parte 3 §6; D-11 §2 | Cubierto |
| R2.6 Segmentación | Switches (VLAN y segmentos) · Controlador | D-10; A-02 §2.3 | Cubierto |
| R2.7 Actualización | Consola · Policy Engine (políticas editables sin rediseño) | D-06 §4; access/02 | Cubierto |
| R2.8 Protección crítica | Infraestructura inaccesible desde BASE y ACADÉMICO; canal de control separado; protección por perfil | D-11 §2–3; A-02 §3 | Cubierto |
| R2.9 Auditoría | Auditoría | D-05 §8 | Cubierto |
| R2.10 Aplicación SDN | Controlador (decisión de autorización → FLOW_MOD) | Parte 3 §6; D-12 | Cubierto |

### R3 — Ataques encubiertos en la intranet

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| R3.1 Monitoreo | Monitor (counters y estadísticas del plano de datos) | Parte 1; D-05 §2 | Cubierto |
| R3.2 Scanning | Detection Engine (patrón de múltiples destinos) | D-11.1; parte 4 | Cubierto |
| R3.3 Spoofing | Controlador (MAC↔IP↔switch↔puerto; incoherencia) · Monitor y Detection Engine | Parte 3 §9; D-11 §4 | Cubierto |
| R3.4 Anomalías | Monitor (línea base) · Detection Engine (desviación) | D-05 §2–3 | Cubierto |
| R3.5 Ataques distribuidos | Detection Engine (múltiples orígenes contra un mismo destino) | Parte 4; D-11.1 | Cubierto |
| R3.6 Clasificación | Detection Engine (tipo) · Incident Manager (riesgo y registro) | D-05 §3–4 | Cubierto |
| R3.7 Mitigación | Policy Engine (decisión) · Controlador (aplicación) | Parte 4; D-05 §5 | Cubierto |
| R3.8 Acciones | Policy Engine y Controlador (bloqueo, rate limiting, aislamiento, redirección, alerta) · Switches (ejecución) | D-11 §4; parte 4 | Cubierto |
| R3.9 Recuperación | Policy Engine (TTL; retiro) · Controlador (retirada por cookie) | Parte 4; D-04 §3 | Cubierto |
| R3.10 Registro | Auditoría · Incident Manager | D-05 §4, §8 | Cubierto |

### R4 — DDoS brute-force en la intranet

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| R4.1 Línea base | Monitor (referencia por servicio protegido) | Parte 4; D-05 §2 | Cubierto |
| R4.2 Detección | Detection Engine (incremento anómalo hacia un nodo) | Parte 4; D-11 §4 | Cubierto |
| R4.3 Indicadores | Monitor (paquetes/s, solicitudes/s, conexiones/s, ancho de banda, fuentes, latencia) | Parte 1; D-05 §2 | Cubierto (valores en prototipo) |
| R4.4 Umbrales | Policy Engine (criterio cuantitativo relativo a la línea base) | Parte 4; D-12 | Cubierto (valores en prototipo) |
| R4.5 Mitigación | Policy Engine (escalera de mitigación) · Controlador | Parte 4; D-05 §5 | Cubierto |
| R4.6 Rate limiting | Controlador (METER_MOD) · Switches (meters) | Parte 4; D-12 (soporte del dispositivo: Fase F) | Cubierto |
| R4.7 Bloqueo | Controlador (FLOW_MOD) · Switches | Parte 4 | Cubierto |
| R4.8 Disponibilidad | Diseño de mitigación proporcional (rate limiting antes que bloqueo; servicio legítimo preservado) | D-11 §4; parte 4 | Cubierto (diseño) |
| R4.9 Recuperación | Policy Engine (restauración de la política normal) · Monitor (verificación) | Parte 4; D-04 §3 | Cubierto |
| R4.10 Medición | Monitor y Auditoría (tiempos de detección y mitigación, impacto) | Prototipo | Pendiente de cuantificación |

### R5 — Seguridad perimetral

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| R5.1 Perímetro | — (sin componente asignado) | C-04 §6; D-10 §6 (perímetro por definir) | **Hueco** |
| R5.2 IDS/IPS | — (evaluación tecnológica) | R5.2; fase F | **Hueco** |
| R5.3 Inspección | — | Depende de R5.1 | **Hueco** |
| R5.4 Bloqueo por IP | Controlador y Switches podrían ejecutarlo; falta el productor del evento perimetral | D-11 §4 (vía interna lista) | **Hueco** (parcial) |
| R5.5 Bloqueo hacia destinos | Ídem R5.4 | Ídem | **Hueco** (parcial) |
| R5.6 Inteligencia | — (definir cómo se determina que un indicador es malicioso) | Fase F | **Hueco** |
| R5.7 Integración SDN | Policy Engine y Controlador aceptan eventos externos como cualquier otro evento; falta la fuente | D-05 §5; D-08 | Parcial (vía lista, fuente ausente) |
| R5.8 Registro | Auditoría (receptora lista); falta la fuente | D-05 §8 | Parcial (vía lista, fuente ausente) |

## 2. Requerimientos transversales

| Requisito | Componente(s) que lo realizan | Dónde | Veredicto |
|---|---|---|---|
| RT-01 Gestión centralizada de políticas | Policy Engine (repositorio único) · Consola | D-05 §5, §10 | Cubierto |
| RT-02 Separación de responsabilidades | Los diez componentes con responsabilidades delimitadas | D-05; D-06 | Cubierto |
| RT-03 Integración SDN | Controlador · interfaces I2/I3 | D-07 | Cubierto |
| RT-04 Northbound | Controlador (API northbound de las aplicaciones); forma concreta: Fase F | D-07; access/00 | Cubierto (forma en F) |
| RT-05 Southbound | Controlador (OpenFlow hacia los switches) | D-07; D-12 | Cubierto |
| RT-06 Monitoreo | Monitor · Consola de monitoreo | D-05 §2, §10 | Cubierto |
| RT-07 Auditoría | Auditoría · almacenamiento de registros | D-05 §8 | Cubierto |
| RT-08 Respuesta automatizada | Policy Engine (condiciones → acción) · Incident Manager | Parte 4; D-05 §4–5 | Cubierto |
| RT-09 Administración | Consola · IAM/AAA (sesión de operador) | D-06 §4; access/02 | Cubierto |
| RT-10 Recuperación | Policy Engine (TTL y retiro) · Controlador | Parte 4; D-04 §3 | Cubierto |

## 3. Requerimientos de calidad

| Requisito | Cómo se resuelve | Dónde | Veredicto |
|---|---|---|---|
| RNF-01 Seguridad | Modelo por capas: mínimo privilegio, segmentación, detección y mitigación | D-11 completo | Cubierto |
| RNF-02 Disponibilidad | Mitigación proporcional; el mecanismo de seguridad no bloquea el servicio legítimo | D-11 §4 | Cubierto (diseño) |
| RNF-03 Rendimiento | Sobrecarga dentro de límites «definidos experimentalmente» | Prototipo | Pendiente de cuantificación |
| RNF-04 Latencia | Decisiones críticas con latencia compatible con la operación | Prototipo | Pendiente de cuantificación |
| RNF-05 Escalabilidad | Diseño admite crecimiento de usuarios, dispositivos, sesiones y eventos | D-08; parte 0 | Cubierto (magnitud en prototipo) |
| RNF-06 Flexibilidad | Políticas modificables sin rediseño (repositorio y consola) | D-05 §5, §10 | Cubierto |
| RNF-07 Modularidad | Diez componentes con responsabilidades e interfaces claras | D-05; D-06; D-07 | Cubierto |
| RNF-08 Observabilidad | Monitor · Consola de monitoreo · Auditoría | D-05 §2, §8, §10 | Cubierto |
| RNF-09 Trazabilidad | Auditoría (correlación usuario/evento/flujo/política) | D-05 §8 | Cubierto |
| RNF-10 Mantenibilidad | Modularidad por componentes y fases | D-05; D-06 | Cubierto |
| RNF-11 Reproducibilidad | Pruebas repetibles bajo condiciones controladas | Prototipo | Pendiente de cuantificación |
| RNF-12 Verificabilidad | Requisitos críticos comprobables con métricas objetivas | Prototipo | Pendiente de cuantificación |

## 4. Requisitos arquitectónicos

| Requisito | Cómo se resuelve | Dónde | Veredicto |
|---|---|---|---|
| RA-01 Arquitectura integral | Interacción de R1–R5 representada en el HLD y la serie de flujo | D-01–D-12; partes 0–5 | Cubierto |
| RA-02 Plano de control | Controlador SDN identificado con sus responsabilidades | D-05 §1 | Cubierto |
| RA-03 Plano de datos | Switches identificados como ejecutores | D-05 §9 | Cubierto |
| RA-04 Aplicaciones de seguridad | Módulos de política, detección, mitigación, monitoreo y administración identificados | D-05 §2–6, §8, §10 | Cubierto |
| RA-05 Flujo de información | Interfaces y comunicación entre componentes especificadas | D-07; D-08 | Cubierto |
| RA-06 Flujo de decisión | Cadena evento → detección → evaluación → decisión → política → aplicación → resultado trazable | Partes 3–4; D-08 | Cubierto |
| RA-07 Fallos | Puntos de fallo y sus efectos identificados | `04_escenarios_de_fallo.md` (esta fase) | Cubierto (en E-04) |
| RA-08 Escalabilidad evaluada | Comportamiento ante aumento de usuarios y tráfico | D-08; prototipo | Cubierto (diseño); magnitud en prototipo |
| RA-09 Protección del plano de control | Canal de control separado; acceso al controlador restringido a operadores con MFA | D-11 §3; access/02 | Cubierto |

## 5. Huecos y pendientes

**Huecos** — el bloque R5 completo: el perímetro no tiene componente asignado (R5.1–R5.6). La vía de integración hacia la red SDN ya existe (R5.7: un evento perimetral entra al Policy Engine como cualquier otro), pero falta la fuente —sistema externo con el que integrarse o componente propio— y la evaluación IDS/IPS de R5.2. Se cierra en la fase de decisiones tecnológicas.

**Pendientes de cuantificación** — se cierran con el prototipo, no con más diseño: R4.10 y RNF-03/04 (tiempos, latencia, sobrecarga), RNF-11/12 (reproducibilidad y verificación con métricas), y los valores concretos de R4.3/R4.4 y de la escalabilidad (R1.10, RA-08).

# Atributos de calidad → decisiones

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Los atributos de calidad de [B-01.2](../B-Drivers_de_arquitectura/01.2_RQ_transversales-de_calidad-arquitectonicos.md) (RNF-01–RNF-12), frente a la decisión arquitectónica concreta que los resuelve: los principios (D-03), el estilo (D-01), los patrones (D-02) y las decisiones del HLD (D-04–D-12). Un atributo sin decisión es un hueco; un atributo cuya comprobación depende de mediciones queda pendiente de cuantificación (P12: sin métrica no hay decisión válida).

## 1. Atributo por atributo

| Atributo | Decisión arquitectónica que lo resuelve | Dónde | Veredicto |
|---|---|---|---|
| RNF-01 Seguridad | Mínimo privilegio con denegación por defecto (P5), identidad solo para elevar (P6), MAC como atributo (P7) y modelo por capas | D-11; D-03 §3 | Cubierto |
| RNF-02 Disponibilidad | Mitigar cerca del origen sin cortar el tráfico legítimo (P9): escalera RATE_LIMIT → BLOCK → ISOLATE → QUARANTINE; el bloqueo total exige aprobación humana | D-03 §3 y §5; D-11 §4 | Cubierto (diseño); verificación con contadores |
| RNF-03 Rendimiento | El controlador no es camino del tráfico (P2): los paquetes fluyen por el plano de datos y la sobrecarga se acota por diseño | D-03 §2 | Pendiente de cuantificación (límite «experimental») |
| RNF-04 Latencia | Decisión centralizada con ejecución en el plano de datos: meters y timeouts nativos ejecutan a velocidad de línea (resolución explícita del conflicto P2 vs RNF-04) | D-03 §5 | Cubierto (diseño); medición en prototipo |
| RNF-05 Escalabilidad | Comunicación por eventos con colas que absorben ráfagas (P13); cadena de detección como pipeline; el registro solo contiene dispositivos privilegiados | D-03 §4; D-08 | Cubierto (diseño); magnitud en prototipo |
| RNF-06 Flexibilidad | Gestión centralizada de políticas (RT-01): una política se cambia en el repositorio y se aplica sin tocar los componentes | D-05 §5; D-06 §4 | Cubierto |
| RNF-07 Modularidad | Responsabilidad única (P3): diez componentes con interfaz clara, evaluables y sustituibles por separado | D-05; D-07 | Cubierto |
| RNF-08 Observabilidad | Trazabilidad y observabilidad por diseño (P11): los contadores OpenFlow son la fuente del plano de datos; monitor y consola la exponen | D-03 §4; D-05 §2, §10 | Cubierto |
| RNF-09 Trazabilidad | P11: accounting AAA, cookie por incidente y estados explícitos hasta CLOSED; cada mitigación es respondible | D-03 §4; D-05 §8 | Cubierto |
| RNF-10 Mantenibilidad | P3 + P13: añadir un consumidor de eventos no modifica a ningún productor; cada componente se verifica aislado | D-03 §2, §4 | Cubierto |
| RNF-11 Reproducibilidad | Instrumentación temprana (P12): línea base, umbrales y contadores se definen al diseñar; pruebas bajo condiciones controladas | D-03 §4 | Pendiente de cuantificación (prototipo) |
| RNF-12 Verificabilidad | P12: toda funcionalidad crítica se evalúa con métricas objetivas definidas antes de implementarla | D-03 §4; R4.10 | Cubierto (métricas definidas); valores en prototipo |

## 2. Conflictos entre atributos, ya resueltos

La precedencia está fijada en D-03 §5 y no queda a interpretación:

| Conflicto | Resolución |
|---|---|
| Decisión centralizada (P2) vs latencia (RNF-04) | La ejecución se empuja al plano de datos: meters y timeouts nativos. |
| Preservar el servicio legítimo (P9) vs automatización (P8) | Escalera de respuestas: la severidad baja se limita sola; el bloqueo total de alto impacto exige aprobación humana. |
| Métricas primero (P12) vs tiempo del curso (RP-03) | La instrumentación se acota a lo que R4.10 exige: tiempos e impacto. |
| Complejidad justificada (P4) vs comunicación por eventos (P13) | El broker se introduce como patrón, no como producto: la tecnología se elige en la Fase F contra el tamaño real del prototipo. |

## 3. Pendientes

Los cuatro pendientes de cuantificación (RNF-03, RNF-04, RNF-11, RNF-12) no son huecos de arquitectura: la decisión existe y la métrica está definida; falta el número, que produce el prototipo. Es el insumo natural de la fase de decisiones tecnológicas y del análisis experimental.

# Escenarios de fallo

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Qué ocurre cuando cada pieza deja de responder. La pregunta no es «¿se cae?» —toda pieza se cae— sino «¿qué sostiene la red mientras tanto, con qué se recupera y qué queda fuera del alcance del prototipo?». Cierra el requisito RA-07 (puntos de fallo y sus efectos). Dos mecanismos estructurales responden primero: **el plano de datos conserva lo instalado** (P2 — el controlador no es camino del tráfico) y **todo privilegio y toda mitigación expira por sí solo** (P10 — ningún estado pegado sobrevive a su timeout).

## 1. Plano de control y plano de datos

| Pieza que falla | Efecto inmediato | Qué sostiene el diseño | Veredicto |
|---|---|---|---|
| **Controlador SDN** | No hay decisiones nuevas: dispositivos nuevos se quedan en BASE sin portal resuelto; elevaciones y mitigaciones pendientes sin resolver | El tráfico ya instalado sigue fluyendo (P2); los switches conservan sus reglas y sus timeouts; al reconectar, el switch se re-registra y las reglas se reinstalan | Cubierto por diseño; la **redundancia del plano de control** se decide en la Fase F (clúster del controlador / switches con más de un controlador) |
| **Canal de control (red de gestión)** | Se pierde el control y la observación de los switches | El plano de datos queda intacto: es un canal separado (out-of-band) y no transporta tráfico de usuarios | Cubierto por diseño |
| **Un switch** | Se pierde su segmento; el resto de la red no se ve afectado | Decisión centralizada, ejecución distribuida (P2): el fallo queda aislado a su dominio; la caída se detecta por eventos de puerto | Cubierto (aislamiento del fallo); la **redundancia de nodos y enlaces** pertenece al despliegue (Fase H) |

## 2. Cadena de detección y respuesta

| Pieza que falla | Efecto inmediato | Qué sostiene el diseño | Veredicto |
|---|---|---|---|
| **Monitor** | No hay observación nueva: la línea base deja de actualizarse; la detección queda ciega a partir de ahí | Las mitigaciones ya activas siguen vigentes y expiran por timeout (P10); al volver, la observación se reanuda sin estado que reparar | Cubierto por diseño (degradación, no pérdida) |
| **Detection Engine** | No hay detección nueva de anomalías | Las mitigaciones activas expiran solas; los eventos en tránsito quedan en las colas del intermediario (P13) | Cubierto por diseño; la garantía de entrega depende del producto de mensajería (Fase F) |
| **Incident Manager** | Incidentes sin registrar ni cerrar | Las mitigaciones no dependen de él para expirar: el timeout y FLOW_REMOVED cierran igual; al volver, reconcilia el estado | Cubierto por diseño; reconciliación a especificar con el producto (Fase F) |
| **Policy Engine** | No hay decisiones nuevas: ni elevaciones ni mitigaciones nuevas; el resto de la cadena observa sin poder actuar | Las reglas vigentes y sus TTL son el estado seguro (P10); la red ya decidida sigue operando | Cubierto por diseño; es el componente crítico junto con el controlador — su redundancia se decide en la Fase F |
| **Intermediario de eventos** | Los componentes de seguridad dejan de intercambiar eventos | Los publicadores absorben ráfagas en colas locales (P13) mientras el intermediario se recupera | Parcial: el comportamiento exacto (persistencia, reintentos) se fija con el producto elegido en la Fase F |

## 3. Identidad, administración y registros

| Pieza que falla | Efecto inmediato | Qué sostiene el diseño | Veredicto |
|---|---|---|---|
| **IAM/AAA** | No hay nuevos logins ni elevaciones nuevas | Las sesiones vigentes continúan hasta su TTL (P10); el fallo del IdP institucional no impide el login de operadores (repositorio propio) ni al revés — las dos fuentes son independientes | Cubierto por diseño (degradación acotada) |
| **IdP institucional** (externo) | La comunidad no puede autenticarse: nadie nuevo obtiene perfil ACADÉMICO | Lo ya autenticado sigue hasta su TTL; los operadores entran por el repositorio propio; la mitigación activa no depende del IdP | Cubierto (el diseño no depende del IdP para operar) |
| **Registro de dispositivos privilegiados** | No se habilitan nuevos dispositivos de operador | Los ya registrados siguen operando; sin match, el perfil es BASE (P5): el fallo degrada hacia el lado seguro | Cubierto por diseño |
| **Consola** | No hay administración interactiva | Las políticas vigentes siguen; la consola no es camino de datos ni de decisión | Cubierto por diseño (degradación operativa) |
| **Auditoría y almacenamiento** | Los eventos de seguridad dejan de persistirse | Nada operativo depende de ella en el momento; sí la trazabilidad (RNF-09) | Parcial: retención y recuperación de registros a definir (Fase F) |

## 4. Redundancia y recuperación: qué es diseño y qué es despliegue

- **Garantizado por diseño (ya validado en esta fase):** el plano de datos no depende del controlador en régimen; toda mitigación y privilegio expira por timeout; el aislamiento de fallos es por segmento y por switch; el estado de retorno es siempre BASE.
- **Decisión de la Fase F:** la redundancia del plano de control —clúster del controlador elegido y/o switches conectados a más de un controlador— con su mecanismo de failover. El insumo está dicho: el diseño no la exige para operar, la exige para no degradar durante la caída.
- **Despliegue (Fase H):** redundancia física de nodos y enlaces. El alcance de la infraestructura (C-04) ya declara que estos escenarios **se analizan por diseño y no se despliegan** en el prototipo.
- **Cuantificación (prototipo):** tiempo de recuperación y de reinstalación de reglas tras la vuelta del controlador (R4.10, RA-07).

## 5. Cierre del requisito

RA-07 quedaba como el requisito «deberán identificarse puntos de fallo y sus efectos»: queda cerrado con §1–§3. Lo que no cierra aquí no es un hueco de arquitectura sino una frontera de alcance: redundancia del controlador (Fase F), redundancia física (Fase H) y sus tiempos (prototipo).

# Escenarios de ataque → detección y respuesta

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** E — Validación del HLD
**Estado:** Borrador formal para revisión

---

Cada amenaza del catálogo ([`11.1_catalogo_de_ataques_y_amenazas.md`](../D-ARQUITECTURA_DE_ALTO_NIVEL-HLD/11.1_catalogo_de_ataques_y_amenazas.md)), con el punto donde se detecta, la respuesta que produce y el componente que la ejecuta. La cadena es siempre la misma (P8): **detector observa → Policy Engine decide → Controlador traduce → Switch ejecuta → Auditoría registra**; lo que cambia por amenaza es dónde se engancha.

## 1. Ataques

| Ataque | Detección | Respuesta | Componentes | Veredicto |
|---|---|---|---|---|
| **Network / port scanning** (R3.2 · CU-05) | Múltiples intentos de conexión a destinos distintos desde un origen | Escalera: RATE_LIMIT → BLOCK | Monitor · Detection Engine · Incident Manager · Policy Engine · Controlador · Switches | Cubierto (flujo parte 4) |
| **IP spoofing** (R3.3 · CU-06) | Incoherencia origen declarado vs. ubicación aprendida (MAC/IP/puerto) | Evento y respuesta escalonada; la incoherencia sostenida bloquea | Controlador (asociaciones) · Policy Engine | Cubierto (parte 3 §9; D-11 §4) |
| **Suplantación de MAC** (R3.3) | Evento MAC_MOVE: misma MAC en otro puerto o con otra identidad | Alerta → bloqueo → cuarentena; port security/802.1X en puertos sensibles | Controlador · Policy Engine · Switches | Cubierto (P7; D-11 §4) |
| **Ataques distribuidos** (R3.5) | Número de fuentes contra un mismo destino sobre la línea base | Mitigación por switch de ingreso de cada origen | Detection Engine · Policy Engine · Controlador | Cubierto (D-11.1) |
| **DDoS volumétrico / flood** (R4 · CU-07) | Tasas (pps, Mbps) muy por encima de la línea base del servicio | Meter en el switch de ingreso (RATE_LIMIT → DROP); verificación por contadores; recuperación por timeout | Monitor · Detection Engine · Incident Manager · Policy Engine · Controlador (METER_MOD) | Cubierto — **es el requerimiento asignado del curso; ciclo completo obligatorio** |
| **Brute-force de solicitudes** (R4) | Solicitudes/s por origen sobre el umbral | RATE_LIMIT o BLOCK del origen | Monitor · Detection Engine · Policy Engine | Cubierto (misma cadena que el flood) |
| **Ataques desde el exterior** (R5 · CU-08) | — sin punto de detección perimetral definido | — (la vía hacia la red SDN existe: R5.7) | — | **Hueco** — se cierra en la Fase F (evaluación IDS/IPS de R5.2 y definición del perímetro) |

## 2. Amenazas y fuentes

| Amenaza | Cómo la trata el diseño | Veredicto |
|---|---|---|
| **Atacante externo** | Objeto de R5 (hueco declarado); si atraviesa el perímetro, cae en la cadena R3/R4 como cualquier origen | Parcial (depende del perímetro) |
| **Atacante interno** | El perfil BASE restringe (lista cerrada) y la detección vigila R3/R4 sobre cualquier origen, autenticado o no | Cubierto |
| **Nodo comprometido** | Su tráfico es objeto de R3/R4 aunque el usuario tenga credenciales válidas; la respuesta lo aísla o bloquea sin depender de la identidad de la persona | Cubierto (D-11.1 §2) |

## 3. Estados que habilitan ataques

- **IdP institucional comprometido:** el IAM consume su veredicto, pero los operadores se verifican contra el repositorio propio y las mitigaciones activas no dependen del IdP: el compromiso degrada la autenticación de la comunidad, no la operación de la defensa (D-11.1 §3).
- **Manipulación de DNS:** tratada como caso de origen inconsistente (R3.3) y como vector de redirección.
- **Desincronización de tiempo (NTP):** no es ataque; deteriora la correlación de eventos y la auditoría (RNF-09) — su tratamiento (fuente de tiempo común) es insumo de la Fase F.

## 4. Cierre

Todos los ataques tienen detección y respuesta asignadas salvo el bloque perimetral, que es el mismo hueco ya registrado en `01_casos_de_uso_a_componentes.md` (CU-08) y `02_requisitos_a_componentes.md` (R5): la arquitectura interna está lista para recibir eventos perimetrales (R5.7), falta la fuente. Los umbrales concretos de cada detección se fijan con mediciones del prototipo.
