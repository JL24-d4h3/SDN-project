# Flujo base: encendido de la red

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Descripción del flujo — parte 2 de 6
**Estado:** Borrador formal para revisión

---

Encendido en frío de la red SDN y aparición del primer tráfico, sin autenticación ni seguridad. Topología de trabajo, con **tres switches** para mostrar el caso general (el escenario mínimo del prototipo; la topología de referencia tiene tres niveles — parte 5 §2):

```text
                        ┌──────────────────────┐
                        │  Controlador SDN     │
                        │  (red de gestión,    │
                        │   out-of-band)       │
                        └──────────┬───────────┘
                                   │ OpenFlow
                 ┌─────────┬───────┴──────┬─────────┐
                 │         │              │         │
              ┌──┴──┐   ┌──┴──┐        ┌──┴──┐   ┌──┴──┐
              │ S1  │───│ S2  │────────│ S3  │   │ SRV │ (DHCP/DNS)
              └──┬──┘   └──┬──┘        └──┬──┘   └─────┘
                 │         │              │
               HostA     HostB          HostC
```

## 1. Paso 1 — Estado inicial

Cables puestos, todo apagado: la conectividad física existe; la lógica no. No hay flujos, ni topología conocida, ni ARP, ni DHCP. Las tablas de flujos están vacías. Lo único configurado es el arranque: cada switch conoce la dirección de su controlador (configuración local, parte 0).

## 2. Paso 2 — El switch arranca

Secuencia de arranque de cada switch, en orden:

1. Inicializa sus puertos y detecta el estado de los enlaces.
2. Inicializa su pipeline de tablas: **vacío**.
3. Inicializa su agente OpenFlow.
4. Intenta abrir una conexión TCP hacia el controlador configurado, puerto 6653.

## 3. Paso 3 — El canal de control: handshake

El diálogo de establecimiento, mensaje por mensaje:

```text
Switch                              Controlador
   │──── TCP 6653 ──────────────────────►│
   │──── OFPT_HELLO (versión 1.3) ──────►│
   │◄──── OFPT_HELLO (versión 1.3) ──────│   (negocian la versión)
   │◄──── OFPT_FEATURES_REQUEST ─────────│
   │──── OFPT_FEATURES_REPLY ───────────►│
   │     datapath_id = DPID_S1 (64 bits) │
   │     n_tables = 2                    │
   │     n_buffers = 256                 │
   │     capabilities = (actions,        │
   │        groups?, meters?)            │
   │                                     │
   │◄════════ ECHO request/reply ════════╪═►  (latido periódico)
```

Dos detalles que el resto del flujo usa:

- **DPID:** cada switch se identifica con un Datapath ID de 64 bits (no con un nombre). Los puertos se identifican con números (`Port No`).
- **Capacidades:** aquí el switch declara cuántas tablas tiene y si soporta groups y meters. El diseño no puede asumir más de lo declarado (RP-11).

Al terminar, el controlador sabe que *existen* S1, S2 y S3 con sus capacidades. Todavía no sabe quién está conectado con quién.

## 4. Paso 4 — Reglas base: la table-miss

Lo único que el controlador instala ahora, en cada switch, es la table-miss entry (parte 1, §1): cualquier paquete sin regla específica se envía al controlador con un PACKET_IN de motivo `OFPR_NO_MATCH`. La red queda lista para reaccionar, pero nada ha fluido.

## 5. Paso 5 — Descubrimiento de topología con LLDP

El controlador responde: ¿quién está conectado con quién? El mecanismo es LLDP. Primero la **estructura de la información**, porque el procedimiento depende de separar dos capas que viajan juntas.

### 5.1 Estructura de la información

```text
METADATOS OPENFLOW (viajan por el canal de control)
  DPID del switch    (Datapath ID, 64 bits)
  Port No            (número del puerto)

TRAMA ETHERNET / LLDP (viaja por el cable)
  MAC destino   01:80:C2:00:00:0E   (multicast estándar de LLDP)
  EtherType     0x88CC              (identificador de protocolo LLDP)
  TLVs (Type-Length-Value):
    Chassis ID TLV   → DPID del switch emisor (DPID_origen)
    Port ID TLV      → número de puerto emisor (Port_origen)
    TTL TLV          → tiempo de vida de la entrada de topología
    (opcional) Vendor TLV → ID del controlador (ignorar LLDPs ajenos)
```

Los TLVs transportan **quién emitió la trama**; el envoltorio OpenFlow transporta **quién la recibió**. El cruce de ambas capas es lo que deduce el enlace.

### 5.2 Fase 0 — Regla proactiva de captura

Antes de inyectar cualquier LLDP, el controlador instala en cada switch una regla **proactiva**:

```text
FLOW_MOD en S1, S2, S3:
  match  eth_type = 0x88CC
  action OUTPUT:CONTROLLER
```

Cuando un switch reciba una trama LLDP, esta regla la capturará y la enviará al controlador con motivo `OFPR_ACTION` — una regla explícita la capturó, no la table-miss. (Sin la regla el mecanismo funcionaría igual vía `OFPR_NO_MATCH`, pero la captura explícita distingue el tráfico LLDP del resto y evita que compita con el camino genérico.)

### 5.3 Fase 1 — Inyección del paquete (PACKET_OUT)

El controlador construye en memoria una trama Ethernet con los TLVs rellenos y la inyecta por cada puerto de cada switch:

```text
Para S1, puerto 2:
  Controlador genera:
    MAC destino = 01:80:C2:00:00:0E
    EtherType   = 0x88CC
    Chassis ID TLV = DPID_S1
    Port ID TLV    = 2
    TTL TLV        = 120 s
  Lo encapsula en:  OFPT_PACKET_OUT
                    actions = OUTPUT: port 2
  Lo envía a S1 por el canal de control.
```

S1 recibe el PACKET_OUT, **remueve la cabecera OpenFlow** y transmite la trama LLDP por su puerto físico 2. El paquete que viaja por el cable es una trama Ethernet común y corriente: el vecino no sabe que fue generada por un controlador.

### 5.4 Fase 2 — Recepción y reenvío (PACKET_IN)

S2 recibe la trama por su puerto 1 y la evalúa contra su pipeline:

1. La regla proactiva de la Fase 0 coincide (`eth_type = 0x88CC`).
2. S2 **no reenvía** la trama a otro puerto: la encapsula en un mensaje OpenFlow.
3. El PACKET_IN incluye:
   - `reason = OFPR_ACTION` (activado por la regla explícita, no por table-miss);
   - metadatos: `DPID_receptor = DPID_S2`, `in_port = 1`;
   - payload: la trama LLDP **intacta**.
4. S2 transmite el PACKET_IN al controlador por el canal de control.

### 5.5 Fase 3 — Deducción del enlace

El controlador recibe el PACKET_IN y cruza el envoltorio OpenFlow con la carga útil LLDP:

| Fuente | Campo extraído | Valor |
|---|---|---|
| Payload LLDP (TLVs) | `DPID_origen` | S1 |
| Payload LLDP (TLVs) | `Port_origen` | 2 |
| Metadatos OpenFlow | `DPID_destino` | S2 |
| Metadatos OpenFlow | `in_port_destino` | 1 |

Con los cuatro valores deduce el **enlace dirigido**:

```text
(S1, puerto 2) ──► (S2, puerto 1)
```

El enlace dirigido dice "S1:p2 llega a S2:p1". Para confirmar que el enlace es útil en ambos sentidos, el proceso corre **en paralelo en todos los puertos de todos los switches**: S2 también inyecta un LLDP por su puerto 1, que S1 captura y reporta, y el controlador deduce:

```text
(S2, puerto 1) ──► (S1, puerto 2)     ← confirmación bidireccional
```

### 5.6 Generalización a N switches

Con N switches no cambia nada del mecanismo: **el procedimiento es por puerto y en paralelo.**

- El controlador emite un PACKET_OUT por **cada puerto de cada switch** — con N switches y P puertos promedio, N×P inyecciones.
- Cada trama LLDP viaja hasta el vecino inmediato y se detiene ahí: ningún switch reenvía LLDP (la regla de captura lo impide), así que una trama inyectada por S1:p2 solo puede ser reportada por S2:p1.
- Cada vecino reporta un PACKET_IN; el controlador deduce un enlace dirigido por reporte.
- Con N switches totalmente interconectados se deducen N×(N−1) enlaces dirigidos, que se confirman bidireccionales cuando llegan los reportes inversos.

En la topología de trabajo (S1–S2, S2–S3, y el enlace S1–S3 si existiera), el grafo resultante es:

```text
G = (V, E)
V = {S1, S2, S3}
E = { (S1:p2 ↔ S2:p1), (S2:p2 ↔ S3:p1) }
```

Con atributos por enlace: estado, capacidad y costo. La escala del número de switches solo multiplica la cantidad de mensajes — que viajan por el canal de control —; no altera el procedimiento ni su lógica.

### 5.7 Mantenimiento y cambios dinámicos

- **Sondeo periódico.** El controlador repite el ciclo cada ~5 s. Si un LLDP deja de llegar antes de vencer su TTL, el controlador **elimina el enlace del grafo**.
- **Notificación de eventos.** Si un cable se desconecta, el chip del switch detecta la caída de portadora (link down) e informa de inmediato con un `OFPT_PORT_STATUS` de razón `OFPPR_MODIFY`. El enlace se invalida al instante, sin esperar a que expire el TTL de LLDP.

### 5.8 Qué ocurre con el grafo

Con el grafo completo, el controlador **no instala todavía caminos hacia hosts**: no sabe qué hosts existen. Lo que sí instala —en cuanto el inventario de servicios está declarado— son los **caminos por destino hacia la infraestructura** (portal, DHCP/DNS, servidores): reglas que no dependen de ningún host ni esperan tráfico (parte 5). Los caminos hacia hosts se instalan cuando el tráfico los exige (pasos siguientes).

## 6. Paso 6 — Un host arranca: DHCPDISCOVER

HostA se enciende con configuración dinámica. Sin que el usuario abra nada, el propio arranque genera el primer tráfico de datos:

```text
DHCPDISCOVER (HostA → broadcast)
  Ethernet dst = ff:ff:ff:ff:ff:ff
  IP src = 0.0.0.0 · IP dst = 255.255.255.255
  UDP src = 68 · UDP dst = 67
  DHCP Message Type = 1 (DISCOVER)
  + parámetros solicitados, identificador del cliente
```

La trama llega a S1. Pipeline: no hay ninguna entrada específica; la table-miss coincide (perspectiva del paquete, parte 1 §7).

## 7. Paso 7 — PACKET_IN y aprendizaje del host

S1 encapsula y reporta:

```text
OFPT_PACKET_IN
  DPID = S1 · in_port = p1 · reason = OFPR_NO_MATCH
  payload = DHCPDISCOVER (o buffer_id)
```

El controlador procesa el mensaje y aprende dos cosas (perspectiva del pipeline):

1. **Existe un host en S1:p1** con MAC `AA:AA…`. El plano de control mantiene la asociación host ↔ MAC ↔ IP ↔ switch ↔ puerto — el reemplazo del "MAC learning" tradicional: **el switch no aprende solo; el controlador construye ese conocimiento**.
2. Ese host está pidiendo configuración DHCP.

## 8. Paso 8 — El camino al servidor DHCP

El DHCPDISCOVER es broadcast en el origen, pero **no se inunda**: con el grafo (sección 5) y el anclaje del servidor declarado (parte 5 §4), el controlador calcula la ruta S1 → S2 → S3 → SRV y coloca el paquete en ella —una sola salida—. Instala por destino:

```text
S1: match eth_src=MAC A1, UDP 68/67 → output p2   (prioridad 10)
S2: match UDP 68/67 → output p2
S3: match UDP 68/67 → output p3
```

En el acceso la entrada queda ligada a la **identidad** del dispositivo (`eth_src`); en el interior basta el **destino**, expresado por protocolo (`udp dst=67`) porque el destino IP del DISCOVER es broadcast (parte 5 §1). La **inundación** —group ALL o `PACKET_OUT` (parte 1 §3)— queda como **respaldo** para los destinos que el controlador no puede resolver: no es el mecanismo del arranque (parte 5 §6).

## 9. Paso 9 — El diálogo DHCP completa

```text
DHCPOFFER  (SRV → HostA): IP ofrecida 10.0.1.25, máscara, gateway, DNS
DHCPREQUEST (HostA → broadcast): "acepto la oferta de 10.0.1.25"
DHCPACK    (SRV → HostA): concesión confirmada, lease time
```

Esos tres paquetes ya viajan por las entradas instaladas, **sin pasar por el controlador** (perspectiva del paquete). Al terminar:

```text
HostA:  MAC = AA:AA:AA:AA:AA:AA
        IP  = 10.0.1.25
        Switch = S1 · Puerto = p1
```

La asociación completa del host es la materia prima del control de acceso de la parte 3.

## 10. Paso 10 — ARP: lo responde el controlador

HostA quiere hablar con `10.0.1.40` y no conoce su MAC. Genera:

```text
ARP Request (broadcast)
  Ethernet dst = ff:ff:ff:ff:ff:ff · EtherType = 0x0806
  opcode = 1 (request)
  SHA = MAC de HostA · SPA = 10.0.1.25
  THA = 00:00:00:00:00:00 · TPA = 10.0.1.40   ("¿quién tiene 10.0.1.40?")
```

La solicitud llega al controlador —por una regla explícita de captura (`eth_type = 0x0806 → CONTROLLER`) o por table-miss— y **el controlador responde** con la asociación que ya mantiene (`MAC ↔ IP ↔ switch ↔ puerto`, paso 7): un `PACKET_OUT` en unicast al solicitante. Si la dirección pedida no está en sus asociaciones, la solicitud se inunda como respaldo.

```text
ARP Reply (del controlador a HostA)
  opcode = 2 (reply)
  SHA = MAC del destino · SPA = 10.0.1.40
```

HostA aprende la MAC en su caché ARP y ya puede enviar tráfico IP directo; el host destino no participó. En régimen, el ARP no se inunda: se contesta (parte 5 §6).

## 11. Paso 11 — Primer tráfico de aplicación

El primer paquete de una sesión nueva (por ejemplo TCP hacia un servicio) probablemente tampoco tiene entrada: table-miss → PACKET_IN → el controlador instala el camino con FLOW_MOD → el resto de la sesión fluye por el plano de datos. Es el mismo patrón reactivo de DHCP, generalizado a cualquier flujo.

**DNS.** Decidido: el DNS comparte el peldaño 10 con DHCP en el esqueleto BASE (serie de acceso, [`02_autorizacion_por_capas.md`](../access/02_autorizacion_por_capas.md)). Su tráfico sigue el mismo camino por destino que cualquier servicio declarado (parte 5 §5).

## 12. Paso 12 — Tráfico estable: el controlador sale del camino

Con las entradas instaladas, el tráfico circula exclusivamente por los switches. El controlador solo interviene ante novedades: tráfico sin regla, cambio de topología (PORT_STATUS), expiración de entradas (FLOW_REMOVED) o eventos de seguridad (parte 4).

## 13. Los dos procesos independientes

La corrección conceptual central de la exposición: **no existe la cadena causal "el controlador enciende la red → hace LLDP → descubre rutas → inicia ARP → comienza el tráfico".** El controlador no inicia ARP ni tráfico —el ARP lo contesta él mismo (paso 10) y el tráfico lo generan los hosts—, pero sí deja instalados los **caminos hacia los servicios declarados** en cuanto completa el grafo (parte 5). Son dos procesos que se superponen:

```text
Proceso A — construcción del conocimiento de red
  switches → canal → reglas proactivas → LLDP por puerto (paralelo)
           → enlaces dirigidos → confirmación bidireccional → grafo
           → (+ inventario declarado) caminos hacia los servicios:
             se calculan e instalan al completar el grafo (parte 5)
           → caminos hacia hosts: se instalan SOLO cuando el tráfico los exige

Proceso B — aparición y procesamiento del tráfico
  host/aplicación → DHCP / ARP / sesión → frame → switch
                 → ¿existe entrada? → sí: forwarding (perspectiva del paquete)
                                  → no: PACKET_IN → FLOW_MOD + PACKET_OUT
                                    (perspectiva del pipeline)
```

B no espera a que A termine: un host puede generar tráfico mientras el controlador sigue descubriendo enlaces, y el controlador sigue descubriendo aunque ningún host transmita. **El controlador no provoca tráfico en los hosts; los hosts y sus aplicaciones lo generan.**

## 14. Variante in-band del canal

Si el canal de control fuera in-band (parte 0 §5), cambia lo siguiente:

1. **VLAN de gestión dedicada.** El canal OpenFlow viaja por la misma infraestructura que los datos, en una VLAN reservada con su propio direccionamiento. El controlador debe instalar **antes que nada** los flujos que encaminan esa VLAN entre el puerto de gestión de cada switch y él mismo.
2. **El tráfico de control nunca cae en la table-miss.** Los flujos del canal llevan prioridad máxima, por encima de cualquier regla de datos; de lo contrario una regla mal priorizada reenviaría el propio tráfico OpenFlow al controlador por PACKET_IN, creando un bucle.
3. **Riesgo de saturación.** En un ataque volumétrico (parte 4), el plano de datos comparte ancho de banda con el canal; si el ataque satura los enlaces, el controlador puede perder el canal justo cuando más lo necesita. La variante exige QoS que priorice el tráfico de control.
4. **LLDP por el mismo camino.** El descubrimiento es idéntico en procedimiento, pero las tramas LLDP compiten con el tráfico de usuario.

## 15. Cuestiones abiertas

- **IPv4.** El flujo descrito usa ARP y DHCPv4. IPv6 (Neighbor Discovery, Router Advertisement, DAD) queda fuera del alcance (RP-12).
- **La inundación de respaldo.** Qué mecanismo la implementa (group ALL o `PACKET_OUT`): depende del soporte de groups en PicOS (RP-11). En régimen no se usa (parte 5 §6).
- **Los caminos instalados ante fallos de topología.** Qué ocurre con las reglas de camino ya instaladas cuando un enlace cae (parte 5 §8).
