# Primitivas OpenFlow

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Descripción del flujo — parte 1 de 5
**Estado:** Borrador formal para revisión

---

Esta parte define la estructura interna de cada pieza del plano de datos antes de usarla: la tabla de flujos y sus entradas, la group table, la meter table, los contadores y los mensajes. Cierra con la distinción entre el flujo visto desde el paquete y el flujo visto desde el pipeline, que las partes 2–4 usan constantemente.

## 1. El pipeline: tablas de flujos en cadena

Un switch OpenFlow no tiene "una" tabla: tiene un **pipeline** de tablas numeradas, típicamente una o varias según el dispositivo.

```text
paquete entra por un puerto
        │
        ▼
┌─────────────┐  match  ┌─────────────┐  match  ┌─────────────┐
│   Tabla 0   ├────────►│   Tabla 1   ├────────►│   Tabla 2   │ ...
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │ instrucción goto-table│                       │
       │ o ejecución de acciones│                      │
```

- Cada tabla es una lista de **entradas de flujo (flow entries)**.
- El paquete se compara contra las entradas de la tabla 0 **en orden de prioridad**; la primera que coincide gana.
- La instrucción `goto-table` (o el orden implícito) decide si el paquete pasa a la tabla siguiente o sale del pipeline.
- La **table-miss entry** es la entrada especial de cada tabla que coincide cuando ninguna otra coincide; su acción típica en esta solución es `CONTROLLER` (enviar el paquete al controlador con un PACKET_IN de motivo `OFPR_NO_MATCH`).

El número de tablas y las acciones soportadas los declara el switch en el FEATURES_REPLY del handshake (parte 2): nada de esto puede asumirse sin verificarlo contra PicOS (RP-11).

## 2. Estructura de una flow entry

Una entrada de flujo es la unidad de estado del pipeline. Su estructura completa:

```text
┌──────────────────────────────────────────────────────────────┐
│ FLOW ENTRY                                                   │
│                                                              │
│  match fields   in_port, eth_src, eth_dst, eth_type,         │
│                 ipv4_src, ipv4_dst, tcp_src, tcp_dst, vlan…  │
│  priority       orden de evaluación (mayor gana)             │
│  counters       bytes y paquetes que han coincidido          │
│  instructions   apply-actions (output, drop, set-field…),    │
│                 goto-table, Meter(id), Group(id),            │
│                 write-metadata                               │
│  timeouts       hard_timeout, idle_timeout                   │
│  cookie         identificador opaco puesto por el controlador│
│  flags          (OFPFF_SEND_FLOW_REM, etc.)                  │
└──────────────────────────────────────────────────────────────┘
```

| Campo | Qué es | Uso en esta solución |
|---|---|---|
| **Match fields** | Con qué campos del paquete se compara la entrada. | `ip_dst = servidor` para proteger; `eth_src = MAC` para el perfil de un dispositivo. |
| **Priority** | Orden de evaluación: gana la entrada de mayor prioridad. | El forwarding normal usa prioridad baja (~10); el perfil BASE deniega con prioridad media (~100); la mitigación entra con prioridad alta (~1000). |
| **Counters** | Acumulado de bytes y paquetes que coincidieron con esta entrada. | La verificación de una mitigación relee el contador del flujo (parte 4). |
| **Instructions** | Qué hacer con el paquete: `apply-actions` (emitir por un puerto, descartar, modificar campos), `goto-table`, referenciar un **meter** o un **group**, escribir metadatos. | `output:p2` para forwarding, `drop` para denegar, `Meter(m1)` para rate limiting, `Group(g1)` para inundar. |
| **hard_timeout** | La entrada se elimina sola al cumplirse el tiempo, haya tráfico o no. | Las reglas de mitigación llevan hard_timeout: no quedan instaladas para siempre. |
| **idle_timeout** | La entrada se elimina si no coincide ningún paquete durante el tiempo. | Las reglas de sesión privilegiada expiran con la inactividad del operador. |
| **Cookie** | Identificador opaco que el controlador asocia a la entrada. | El controlador agrupa sus reglas (p. ej. "todas las del incidente INC-0042") y las retira con un solo FLOW_MOD DELETE. |
| **Flags** | Comportamiento opcional (p. ej. notificar al controlador cuando la entrada se elimina). | Con `OFPFF_SEND_FLOW_REM` el switch avisa con FLOW_REMOVED cuando expira una regla temporal. |

## 3. La group table

La group table es una tabla **separada del pipeline**. Guarda grupos, y cada grupo agrupa acciones en *buckets*:

```text
GROUP g1
  type = ALL                (ejecutar TODOS los buckets)
  buckets = [ output:p2, output:p3, output:p4 ]

GROUP g2
  type = SELECT             (elegir UN bucket)
  buckets = [ output:p2, output:p3 ]        ← balanceo de carga

GROUP g3
  type = FAST_FAILOVER     (bucket vivo según estado del puerto)
  buckets = [ output:p2 (vivo), output:p3 (respaldo) ]
```

- Una flow entry referencia un grupo con la instrucción `Group(id)`.
- **Uso principal en esta solución:** un grupo de tipo `ALL` con los puertos del segmento de acceso inunda los broadcast (DHCPDISCOVER, ARP) sin que el controlador enumere puertos en cada PACKET_OUT (parte 2). `SELECT` habilita caminos alternativos si el diseño lo exige.
- El controlador administra los grupos con mensajes `GROUP_MOD`; el switch declara en FEATURES si soporta la tabla.

## 4. La meter table

La meter table es la segunda tabla separada del pipeline. Guarda **medidores**, y cada medidor aplica **bandas** de tasa:

```text
METER m1
  bandas = [ rate = 10 Mbps, tipo = drop       ← lo que supere 10 Mbps se descarta ]
            rate = 20 Mbps, tipo = dscp_remark ← lo que supere 20 Mbps se remarca ]
```

- Una flow entry referencia un medidor con la instrucción `Meter(id)`.
- **Uso principal:** el rate limiting de R4. Con el medidor, la restricción se ejecuta **dentro del switch**, a velocidad de línea, sin que el controlador procese paquetes (parte 4).
- Si PicOS no soportara meters (RP-11), el rate limiting degrada a muestreo + reglas periódicas desde el controlador: una alternativa peor que conviene evitar. El soporte se verifica contra el dispositivo en la Fase G.

## 5. Contadores

OpenFlow mantiene contadores de bytes y paquetes en cinco lugares distintos:

| Contador | Qué acumula | Cómo se lee |
|---|---|---|
| Por puerto | Tráfico emitido y recibido por el puerto | `OFPMP_PORT_STATS` (MULTIPART) |
| Por tabla | Paquetes que coincidieron en cada tabla | `OFPMP_TABLE` |
| Por flujo | Paquetes y bytes que coincidieron con una entrada concreta | `OFPMP_FLOW` |
| Por grupo | Tráfico procesado por cada grupo | `OFPMP_GROUP` |
| Por medidor | Tráfico medido por cada banda | `OFPMP_METER` |

Son la única fuente de observación de la solución: sin ellos no hay línea base, ni detección, ni verificación de mitigaciones (parte 4). El monitor los lee periódicamente por el canal de control; los contadores son estado del switch, no mensajes.

## 6. Los mensajes OpenFlow

Los mensajes viven en el canal de control (parte 0). Se agrupan en tres categorías:

| Categoría | Mensajes | Propósito |
|---|---|---|
| **Simétricos** (cualquier lado los inicia) | HELLO, ECHO, ERROR, EXPERIMENTER | Negociar versión, latido del canal, reportar errores. |
| **Controller-to-switch** | FEATURES, CONFIG, MODIFY-STATE (FLOW_MOD, GROUP_MOD, METER_MOD, PORT_MOD), PACKET_OUT, MULTIPART (lectura de contadores), BARRIER | Gestionar el estado del switch: instalar y retirar entradas, emitir paquetes, leer estadísticas. |
| **Asíncronos** (el switch los inicia) | PACKET_IN, FLOW_REMOVED, PORT_STATUS | Reportar paquetes sin regla o capturados, entradas expiradas y cambios de puerto. |

Cada mensaje lleva una cabecera con versión, tipo, longitud e `xid` (identificador de transacción para emparejar petición y respuesta).

## 7. El flujo visto desde el paquete y el flujo visto desde el pipeline

La palabra "flujo" se usa con dos significados distintos, y la exposición los necesita a ambos:

**Perspectiva del paquete — el viaje de un paquete por el pipeline:**

```text
paquete entra por in_port
   → se compara con la tabla 0 en orden de prioridad
   → la entrada ganadora ejecuta sus instrucciones
        (output, drop, goto-table, meter, group, set-field…)
   → los contadores de la entrada y del puerto se incrementan
   → el paquete sale por un puerto, se descarta,
     o va al controlador (PACKET_IN)
```

Esta perspectiva explica el **forwarding**: qué le ocurre a cada paquete y por qué la red reenvía sin el controlador.

**Perspectiva del pipeline — el estado y su ciclo de vida:**

```text
el estado del pipeline son las entradas
   → el controlador las instala, modifica y elimina (FLOW_MOD)
   → se evalúan por prioridad, no por orden de llegada
   → expiran por hard_timeout / idle_timeout
   → la table-miss atrapa todo lo que no tiene entrada
   → FLOW_REMOVED avisa al controlador cuando una expira
```

Esta perspectiva explica el **control**: cómo las decisiones de seguridad se convierten en estado del plano de datos y cómo ese estado se retira.

Un mismo hecho se describe con las dos perspectivas: "el paquete de H1 fue descartado" (paquete) es la consecuencia de "existe una entrada con prioridad 1000 que hace match con H1→SERVER y aplica drop" (pipeline). Las partes 2–4 marcan explícitamente cuál perspectiva están usando en cada paso.

## 8. Cuestiones abiertas

- **Número de tablas del pipeline** del switch Pica8 disponible: condiciona si el diseño usa una tabla plana con prioridades o un pipeline multi-tabla.
- **Soporte de groups y meters en PicOS:** se verifica contra el dispositivo en la Fase G (RP-11).
