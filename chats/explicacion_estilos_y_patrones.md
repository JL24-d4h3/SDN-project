Los documentos del proyecto han sido analizados por completo y quedan guardados como contexto.

En la Fase D (Arquitectura de Alto Nivel - HLD), la solución no adopta un único estilo arquitectónico, sino una **arquitectura híbrida compuesta por cuatro estilos**. Esta decisión responde a que el sistema actúa simultáneamente como una **plataforma de software de seguridad** y como un **sistema SDN que gobierna infraestructura de red**. Como ningún estilo individual cubre ambas facetas, se articulan bajo la premisa de que *«las capas contienen, los microservicios dividen, los eventos conectan y el cliente-servidor expone»*.

A continuación se detalla cada uno de estos estilos según lo definido en los documentos:

---

### 1. Estilo en Capas (Layered Architecture)

* **Qué es:**
Es un estilo arquitectónico que organiza el sistema de forma jerárquica y vertical en niveles de abstracción y responsabilidad de arriba hacia abajo, según la distancia al problema de red. Cada capa depende únicamente de la inmediatamente inferior y la interacción entre ellas se rige por contratos explícitos.


* **Para qué se usa:**
Proporciona la **estructura global del sistema** y define formalmente las fronteras de dependencia en cinco niveles:


1. *Capa de interacción:* Consola de administración, portal cautivo y Northbound API.


2. *Capa de aplicación:* IAM/AAA, Registro de dispositivos, Gestión de incidentes y Monitoreo.


3. *Capa de seguridad:* Detección, Políticas y Decisión (Monitor, Detection, Incident, Policy).


4. *Capa de control SDN:* Controlador SDN.


5. *Capa de infraestructura:* Switches OpenFlow (PicOS), servidores protegidos y hosts.




* **Cuándo se usa:**
Se aplica al definir la organización estructural del código y de los módulos, garantizando que los niveles superiores de interacción nunca se acoplen ni abran sockets directos con los conmutadores del plano de datos.


* **Por qué este y no otros:**
Porque el dominio del problema separa con claridad la interacción del usuario, la lógica de seguridad, la decisión de políticas y el control de hardware. Este estilo materializa la restricción de **separación de planos SDN (RP-02 y P1)**: la capa de seguridad decide, el controlador traduce y la infraestructura ejecuta. Un esquema monolítico o una arquitectura plana romperían esta separación de responsabilidades.


* **Alcance y limitaciones:**
* *Alcance:* Establece la jerarquía estática, las dependencias permitidas y el orden de mando descendente.


* *Limitaciones:* No modela la reactividad en tiempo real ante amenazas ni describe la comunicación asíncrona horizontal entre componentes de una misma capa.





---

### 2. Estilo Orientado a Eventos (Event-Driven Architecture)

* **Qué es:**
Es un estilo donde los componentes se comunican de manera reactiva mediante la emisión, propagación y consumo asíncrono de sucesos o cambios de estado («eventos») a través de un intermediario (*Broker*).


* **Para qué se usa:**
Modela la **reacción dinámica** ante anomalías de tráfico, ataques y novedades de acceso (especialmente los requerimientos R3 y R4). Da forma a la cadena técnica de respuesta:


$$\text{Monitor } (\textit{AnomalyDetected}) \to \text{Detection Engine } (\textit{IncidentOpened}) \to \text{Incident Manager } (\textit{MitigationRequired}) \to \text{Policy Engine } (\textit{MitigationRequested}) \to \text{Controlador SDN } (\textit{FLOW\_MOD}) \to \text{Switch } (\textit{MitigationApplied}) \to \text{Monitor } (\textit{MitigationVerified / Expired})$$



* **Cuándo se usa:**
En todos los flujos operacionales donde el sistema debe observar contadores, juzgar anomalías, disparar mitigaciones o gestionar el ciclo de vida de los incidentes y sesiones (`DeviceConnected`, `MAC_Moved`, `IncidentOpened`, `MitigationApplied`, etc.).


* **Por qué este y no otros:**
* Permite **desacoplamiento total**: el detector emite `AnomalyDetected` sin saber quién lo consumirá; agregar un nuevo consumidor (como auditoría o una consola SIEM) no altera a los emisores.


* Proporciona **trazabilidad por diseño**: cada evento es un punto auditable para cumplir con los requerimientos R1.9, R2.9 y RNF-09.


* Permite **absorber ráfagas**: durante un ataque DDoS volumétrico (R4), las colas del intermediario amortiguan el tráfico de eventos sin bloquear al motor de detección.




* **Alcance y limitaciones:**
* *Alcance:* Resuelve la comunicación interna reactiva y asíncrona entre los servicios de seguridad.


* *Limitaciones:* No define la tecnología de transporte concreta (si se usará RabbitMQ, Kafka o colas en memoria, lo cual es decisión de Fase G), ni es aplicable a consultas síncronas que demandan respuesta inmediata en el borde.





---

### 3. Estilo Cliente-Servidor (Client-Server Architecture)

* **Qué es:**
Es un modelo de comunicación distribuido, típicamente síncrono, basado en un esquema estricto de petición-respuesta (*request-response*) entre clientes que solicitan operaciones y servidores que las despachan bajo contratos predefinidos.


* **Para qué se usa:**
Gestiona la **interacción externa en el borde del sistema**:


* Interacción de los administradores y especialistas de TI a través de la consola de administración hacia las APIs de la plataforma.


* Autenticación de operadores privilegiados mediante HTTPS en el portal cautivo.


* Consultas síncronas hacia sistemas externos, como la validación de credenciales contra el Identity Provider institucional (IdP/LDAP) o consultas de inteligencia de amenazas.




* **Cuándo se usa:**
Cuando un usuario o sistema externo requiere una respuesta inmediata: iniciar sesión, consultar el catálogo de políticas, inspeccionar un incidente o autorizar una solicitud de elevación temporal de privilegios.


* **Por qué este y no otros:**
Porque estas operaciones son transaccionales y de petición-respuesta por su propia naturaleza. Sería ineficiente e inadecuado que un operador encolara una consulta en un bus de eventos asíncrono para esperar a que la interfaz web reciba una notificación eventual.


* **Alcance y limitaciones:**
* *Alcance:* Confinado exclusivamente al borde externo del sistema (interacción de usuarios y APIs públicas).


* *Limitaciones:* No debe usarse para la reacción interna ante amenazas; resultaría crítico y propenso a bloqueos que el detector llamara síncronamente al Policy Engine en medio de una saturación por DDoS.





---

### 4. Estilo de Microservicios (Microservices Architecture)

* **Qué es:**
Es un estilo de descomposición interna donde las capacidades del sistema se dividen en un conjunto de servicios autónomos, con responsabilidad única, ciclo de vida independiente y almacenamiento de datos desacoplado (cada servicio es dueño de su estado y repositorio).


* **Para qué se usa:**
Estructura las capas de aplicación y seguridad dividiéndolas en unidades lógicas independientes:


* *IAM/AAA:* Autenticación y sesiones de operadores.


* *Registro de dispositivos:* Base de datos de equipos privilegiados y auditoría de altas.


* *Monitor:* Sondeo de contadores y mantenimiento de la línea base.


* *Detección:* Identificación de anomalías y clasificación de amenazas.


* *Incidentes:* Ciclo de vida y transición de estados del incidente.


* *Políticas:* Toma de decisiones contextuales de acceso y mitigación.


* *Auditoría:* Registro pasivo de todas las acciones del sistema.




* **Cuándo se usa:**
Durante el diseño y modularización de la lógica de seguridad para garantizar que cada componente pueda ser mantenido, probado, escalado o modificado de manera aislada.


* **Por qué este y no otros:**
* **Independencia y mantenibilidad (D-12):** Permite actualizar el algoritmo de detección sin tener que reiniciar el motor de políticas ni afectar el servicio IAM.


* **Aislamiento de fallos:** Si el servicio de incidentes se degrada, la autenticación de operadores o la auditoría pueden seguir operando.


* **Escalabilidad asimétrica:** La detección escala con el volumen de tráfico de red, mientras que el registro de dispositivos lo hace según el número de operadores.


* Se descarta el monolito tradicional porque acoplaría componentes con requerimientos de procesamiento completamente dispares.




* **Alcance y limitaciones:**
* *Alcance:* Rige la descomposición de la plataforma de software de seguridad.


* *Limitaciones:* Es una descomposición **lógica**; debido a las restricciones de tiempo y hardware de laboratorio (RP-04, RP-07), en el prototipo físico los microservicios pueden desplegarse consolidados en un único servidor de control. Asimismo, el **controlador SDN no es un microservicio**, sino un elemento de la capa de control de red sujeto a las reglas del paradigma OpenFlow.

---

---

Los documentos del proyecto han sido analizados por completo y quedan guardados como contexto.

En la Fase D (Arquitectura de Alto Nivel - HLD), la solución no adopta un único estilo arquitectónico, sino una **arquitectura híbrida compuesta por cuatro estilos**. Esta decisión responde a que el sistema actúa simultáneamente como una **plataforma de software de seguridad** y como un **sistema SDN que gobierna infraestructura de red**. Como ningún estilo individual cubre ambas facetas, se articulan bajo la premisa de que *«las capas contienen, los microservicios dividen, los eventos conectan y el cliente-servidor expone»*.

A continuación se detalla cada uno de estos estilos según lo definido en los documentos:

---

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

- **Tecnología del broker.** El patrón no elige producto: broker dedicado, colas embebidas o bus de eventos se decide en la Fase G, contra las capacidades del entorno del prototipo.
- **Frontera entre repositorios.** El número y los límites exactos de los repositorios se fijan junto con la descomposición en servicios ([`04_descomposición_arquitectónica.md`](04_descomposición_arquitectónica.md)).
- **Auditoría por eventos o por escritura síncrona.** Si la auditoría consume del broker (eventual) o se escribe en la misma transacción de la acción (inmediata): es una decisión de consistencia que pertenece a [`08_comunicacion.md`](08_comunicacion.md).
