# Anatomía del sistema

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Descripción del flujo — parte 0 de 6
**Estado:** Borrador formal para revisión

---

Antes de describir cualquier flujo hay que fijar **dónde vive cada cosa**. Esta parte presenta el hardware de la solución y la anatomía interna de cada pieza: el switch con su pipeline y sus tablas, el canal de control y los componentes de software. Las partes siguientes usan este vocabulario.

## 1. Serie completa

| Parte | Archivo | Contenido |
|---|---|---|
| 0 | `00_anatomia_del_sistema.md` | Hardware, anatomía del switch, canal de control, componentes de software |
| 1 | `01_primitivas_openflow.md` | Estructura de las tablas, de las entradas, de los mensajes y las dos perspectivas del flujo |
| 2 | `02_flujo_base_arranque.md` | Encendido de la red: canal, LLDP con N switches, DHCP, ARP |
| 3 | `03_flujo_autenticacion_autorizacion.md` | Perfiles de acceso, registro de dispositivos, elevación |
| 4 | `04_flujo_seguridad_r4.md` | Ciclo completo de detección y mitigación (R4) |
| 5 | `05_enrutamiento.md` | Del grafo a los caminos: caminos por destino, ARP del controlador, tres niveles |

## 2. Hardware de referencia

```text
                          ┌─────────────────────────┐
                          │  Servidor de control    │
                          │  ┌───────────────────┐  │
                          │  │  Controlador SDN  │  │
                          │  │  + aplicaciones   │  │
                          │  │  de seguridad     │  │
                          │  └───────────────────┘  │
                          └───────────┬─────────────┘
                                      │ OpenFlow (TCP 6653)
              red de gestión ┌────────┴─────────┐  out-of-band
        ─────────────────────┼──────────────────┼──────────────────────
                             │                  │
                         ┌───┴───┐          ┌───┴───┐
                         │  S1   │──────────│  S2   │
                         │ Pica8 │   datos  │ Pica8 │
                         └───┬───┘          └───┬───┘
                             │                  │
                        ┌────┴────┐        ┌────┴────┐
                       HostA    HostB     HostC    SRV-D
                                            (DHCP/DNS/servicios)
```

- **Switches:** Pica8 con PicOS (RP-11). Ejecutan el plano de datos: tablas de flujos, grupos y medidores.
- **Servidor de control:** aloja el controlador SDN y las aplicaciones de seguridad (parte 3 de esta sección).
- **Canal de control:** red de gestión separada de la red de datos (out-of-band). La variante in-band se analiza en la sección 5.
- **Hosts y servidores:** generan y consumen el tráfico; no ejecutan ninguna lógica de la solución.

## 3. Anatomía del switch

Lo que se describe como "el switch" es en realidad un conjunto de piezas con ubicaciones distintas. Saber en cuál vive cada elemento evita el error más común de la exposición: ubicar los mensajes o las tablas donde no están.

```text
┌───────────────────────────────────────────────────────────────┐
│                          SWITCH                               │
│                                                               │
│   puertos ──► ┌─────────────────────────────────────────┐     │
│   (p1..pN)    │              PIPELINE                   │     │
│               │   tabla 0 ──► tabla 1 ──► ... ──► tabla N│    │
│               │   (flujos con prioridad, contadores,     │     │
│               │    instrucciones, timeouts)              │     │
│               └─────────────────────────────────────────┘     │
│                                                               │
│   ┌──────────────────┐        ┌──────────────────┐            │
│   │   GROUP TABLE    │        │   METER TABLE    │            │
│   │   (grupos de     │        │   (medidores de  │            │
│   │    acciones)     │        │    tasa)         │            │
│   └──────────────────┘        └──────────────────┘            │
│                                                               │
│   contadores: por puerto, por tabla, por flujo, por grupo,    │
│               por medidor                                     │
│                                                               │
│   ┌──────────────────┐        ┌──────────────────┐            │
│   │  AGENTE OPENFLOW │◄──────►│ Config. local    │            │
│   │  (habla con el   │  canal │  (dirección del  │            │
│   │   controlador)   │  6653  │   controlador)   │            │
│   └──────────────────┘        └──────────────────┘            │
└───────────────────────────────────────────────────────────────┘
```

| Pieza | Qué guarda | Quién la usa |
|---|---|---|
| **Pipeline (tablas de flujo)** | Las entradas de flujo (flow entries): match, prioridad, instrucciones, contadores, temporizadores. | El plano de datos, para decidir qué hacer con cada paquete. |
| **Group table** | Grupos de acciones en *buckets* (inundación, balanceo, failover). Es una tabla **separada** del pipeline: una entrada de flujo la referencia con la instrucción `Group`. | El plano de datos, cuando una entrada manda ejecutar un grupo. |
| **Meter table** | Medidores con bandas de tasa (descartar o remarcar al superar X). También **separada**: una entrada la referencia con la instrucción `Meter`. | El plano de datos, para limitar la tasa de un flujo. |
| **Contadores** | Acumulados de bytes y paquetes por puerto, tabla, flujo, grupo y medidor. | El monitor, que los lee por el canal de control. |
| **Agente OpenFlow** | El proceso que habla con el controlador: abre el canal, ejecuta los mensajes que recibe y reporta los eventos. | El controlador. |
| **Configuración local** | La dirección del controlador y los parámetros de arranque. | El propio switch, al encender. |

Las estructuras exactas de cada tabla y de cada entrada se detallan en la parte 1.

## 4. El canal de control: dónde viven los mensajes

**Los mensajes OpenFlow no viven en ninguna tabla.** Las tablas guardan *estado* (entradas, grupos, medidores, contadores); los mensajes *viajan* por el canal de control, que es una conexión TCP —típicamente el puerto 6653— entre el agente del switch y el controlador, por la red de gestión.

Por el canal circula todo el diálogo:

- **Handshake:** HELLO, FEATURES (identificación del switch y sus capacidades).
- **Instalación de estado:** FLOW_MOD, GROUP_MOD, METER_MOD, PORT_MOD.
- **Paquetes:** PACKET_IN (del switch al controlador, con el paquete o su referencia) y PACKET_OUT (del controlador al switch, con el paquete a emitir).
- **Estadísticas:** peticiones y respuestas MULTIPART (lectura de contadores).
- **Eventos asíncronos:** PACKET_IN, PORT_STATUS (puerto que sube o baja), FLOW_REMOVED (entrada que expiró).
- **Latidos:** ECHO request/reply.

Cuando un paquete se envía al controlador, no es que el paquete "se guarde en una tabla": queda en el **búfer del switch** (identificado por un `buffer_id` que viaja en el PACKET_IN) o se copia embebido en el mensaje. El controlador responde con un PACKET_OUT que referencia ese búfer o lleva el paquete de vuelta.

## 5. Canal out-of-band e in-band

- **Out-of-band (asumido):** el canal usa una red de gestión separada físicamente de la red de datos. El tráfico de los usuarios no compite con el protocolo SDN, y un ataque volumétrico sobre el plano de datos no satura el canal de control.
- **In-band (variante aspiracional, valorada por el profesor):** el canal viaja por la misma infraestructura que los datos, típicamente en una VLAN de gestión dedicada. Es más compleja: los switches deben priorizar el tráfico de control y el controlador debe instalar los flujos del canal **antes** de operar. Se analiza en la parte 2, sección del canal.

## 6. Componentes de software y dónde viven

La plataforma de software no vive en los switches: vive en el servidor de control, junto al controlador SDN. Cada componente del modelo de dominio (fase A) ocupa su lugar:

| Componente | Vive en | Se comunica con |
|---|---|---|
| Consola de administración | Servidor de control (capa de interacción) | Operadores, por peticiones |
| Portal cautivo + IAM/AAA | Servidor de control | Operadores (login); IdP institucional (externo) |
| Registro de dispositivos privilegiados | Servidor de control (base de datos propia) | IAM, Policy Engine, auditoría |
| Monitor | Servidor de control | Switches (lee contadores por el canal) |
| Detection Engine | Servidor de control | Monitor (eventos) |
| Incident Manager | Servidor de control | Detection Engine (eventos) |
| Policy Engine | Servidor de control | Incident Manager, IAM, registro |
| Controlador SDN | Servidor de control | Policy Engine (órdenes); switches (OpenFlow) |
| Auditoría | Servidor de control | Todos (eventos y acciones) |

Esta distribución sigue el estilo híbrido de la fase D: componentes en capas, descompuestos como servicios, conectados internamente por eventos y expuestos al exterior por cliente-servidor.

## 7. Cuestiones abiertas

- **In-band.** Si el prototipo adopta la variante y en qué fase (ver parte 2).
- **Número de switches y hosts del prototipo.** Depende de la capacidad del laboratorio y de los escenarios; no cambia la anatomía descrita.
