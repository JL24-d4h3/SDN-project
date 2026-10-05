# Enrutamiento óptimo: del grafo a los caminos

**Proyecto:** Solución de seguridad para una red de campus académico
**Serie:** Descripción del flujo — parte 5 de 6
**Estado:** Borrador formal para revisión

---

La [parte 2](02_flujo_base_arranque.md) dejó el grafo de topología construido y una decisión explícita: las rutas se calculaban e instalaban **solo cuando el tráfico las exigía**. Esta parte la revisa y la completa: el controlador instala **caminos por destino hacia los servicios declarados** en cuanto conoce el grafo y el inventario —antes de que exista tráfico— y reserva la instalación reactiva para los hosts y lo desconocido. Decide además quién resuelve ARP y fija los **tres niveles** de la topología de referencia. El vocabulario de reglas y mensajes está en las partes [0](00_anatomia_del_sistema.md) y [1](01_primitivas_openflow.md); la autorización que usa estos caminos, en la [parte 3](03_flujo_autenticacion_autorizacion.md) y en [`access/02`](../access/02_autorizacion_por_capas.md).

## 1. Dos familias de reglas

Todo lo que el controlador instala pertenece a una de dos familias:

| | **Reglas de camino** | **Reglas de política** |
|---|---|---|
| Dónde viven | en todos los switches del camino | solo en el switch de acceso |
| Qué miran | el **destino** (prefijo, protocolo) | la **identidad** (MAC, puerto, perfil) |
| Quién las origina | el controlador, por cálculo sobre el grafo | la decisión del Policy Engine, traducida por el controlador (I2) |
| Cuándo | proactivas hacia servicios declarados; reactivas hacia hosts | por dispositivo (esqueleto BASE) y por sesión |
| Ejemplo | `ip_dst=10.0.2.0/24 → salida hacia el núcleo` | `eth_src=MAC A1, udp 67/68 y 53 → salida hacia el núcleo (10)` |

La frase que ordena el diseño: **la autorización decide en el borde; el encaminamiento optimiza el centro.** El interior no conoce usuarios —solo destinos— y confía en que el acceso ya filtró: ningún paquete sin regla de identidad sale del switch de acceso.

## 2. La topología de referencia: tres niveles

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

- **Acceso** — donde está el dispositivo. Aquí vive la política: perfil BASE, esqueleto, escalera de prioridades, anti-spoofing, portal.
- **Distribución** — agregación. Une los accesos entre sí y con el núcleo; es el ámbito natural de los caminos.
- **Núcleo** — la troncal. Conecta los servicios de infraestructura y los caminos principales.

Cuántos switches tiene cada nivel, cómo se conectan entre sí y qué redundancia existe **no se decide aquí** (§8): la referencia fija los tres niveles, no las cantidades ni la resiliencia. El escenario de trabajo de las partes 2–4 (tres switches en cadena) es el caso mínimo del prototipo, no la forma de la referencia.

## 3. El grafo y la métrica

La parte 2 §5 dejó el grafo: nodos (switches), enlaces dirigidos confirmados en ambos sentidos y atributos por enlace — **estado, capacidad y costo**. Falta dar sentido al costo: la métrica del camino.

- La **mejor ruta** entre dos puntos es el camino de **menor costo acumulado** sobre el grafo. El cálculo es por destino: para cada destino, el controlador obtiene, en cada switch, **el puerto de salida del siguiente salto**.
- La métrica concreta (capacidad, inverso de la capacidad, uso, valor manual) se fija al implementar (§8). Lo que esta parte decide es que **existe una métrica y el camino se calcula con ella**: «óptimo» significa el menor costo según esa métrica, no el primero que funcione.
- El cálculo se rehace cuando el grafo cambia. Un enlace que cae se elimina del grafo (parte 2 §5.7, `PORT_STATUS`); el efecto de un fallo sobre los caminos ya instalados se aborda con la resiliencia (§8).

## 4. Los anclajes: el inventario de servicios

El grafo no ve extremos: LLDP conecta switches, no hosts ni servidores. Y sin embargo el controlador debe saber **dónde está cada servicio** para calcular la ruta hacia él.

- **Los servicios son infraestructura: se declaran.** Su IP es estática —configurada, no negociada— y su anclaje (switch y puerto) se registra en un **inventario de servicios**, que la administración de la red entrega al controlador por el plano de gestión.
- **La observación verifica.** Cuando el servicio transmite, el controlador contrasta lo observado con lo declarado (el par MAC↔IP aprendido, parte 2 §7); una incoherencia se audita.
- Esto desata la paradoja del arranque: **la IP de un servidor no viaja por la red — se configura**; no necesita ninguna regla previa. La única regla que existe antes que todo es la table-miss (parte 2 §4), y existe precisamente para que el primer paquete de cualquier dispositivo tenga un destino: el controlador.

```text
inventario (declarado)              grafo (LLDP + métrica)
  servicio · IP · switch:puerto       enlaces · costo
        └──────────────┬──────────────────────┘
                       ▼
            cálculo de caminos por destino
                       ▼
     reglas de camino en todos los switches del camino
```

## 5. Del grafo a la tabla de caminos

**Lo proactivo: los caminos hacia los servicios.** Al completarse el grafo y con el inventario declarado, el controlador calcula e instala los caminos hacia los destinos de infraestructura **antes de que exista tráfico**. Con el ejemplo de una ruta de varios niveles:

```text
Servicio X · IP 10.0.2.10 · anclaje M:pX
Camino de menor costo: H → A → E → G → M → X

Reglas de camino instaladas (por destino, sin identidad):
  A: ip_dst=10.0.2.0/24 → salida hacia E
  E: ip_dst=10.0.2.0/24 → salida hacia G
  G: ip_dst=10.0.2.0/24 → salida hacia M
  M: ip_dst=10.0.2.10   → salida pX
```

- Cada switch interior solo necesita saber «por dónde sale lo que va a este destino» — su **siguiente salto**. No conoce usuarios ni sesiones.
- El costo es **por destino, no por flujo**: el número de reglas de camino crece con los destinos declarados, no con los hosts.
- El **retorno** es otra regla por destino, no un caso aparte: en los switches del camino, `hacia 10.0.1.0/24` (la red de acceso); en el acceso, hacia el host aprendido.
- Las reglas de camino **no compiten con la escalera de política**: en el acceso manda la escalera —la identidad vence al destino—; en el interior no hay identidad que las dispute.

**Lo reactivo: los hosts.** Un host no está declarado: aparece. Su primer paquete no tiene regla → table-miss → `PACKET_IN` → el controlador aprende (MAC y puerto; después, la IP) e instala lo suyo **en el switch de acceso**: el esqueleto BASE y el par MAC/IP, con el **siguiente salto ya calculado** hacia cada destino declarado. Es el mismo patrón de la parte 2, ahora con el camino resuelto desde el primer momento.

```text
acceso      · reglas de política: identidad + siguiente salto (por dispositivo y sesión)
interior    · reglas de camino: por destino (por prefijo y protocolo)
```

## 6. ARP y el arranque sin inundación

- **ARP lo responde el controlador.** La solicitud llega al controlador (regla explícita de captura o table-miss) y este responde con la asociación que ya mantiene (`MAC ↔ IP ↔ switch ↔ puerto`), en unicast al solicitante. Queda cerrada la cuestión abierta de la parte 2 §15.
- **La inundación queda de respaldo**: solo para direcciones que el controlador no conoce. En régimen, **ni ARP ni DHCP se inundan**.
- **El DHCP viaja por ruta exacta.** El DHCPDISCOVER es broadcast en el origen, pero el switch de acceso lo entrega al controlador (primer paquete del dispositivo) y este lo coloca en el camino calculado —una sola salida—; los switches interiores lo reenvían por sus reglas de camino, por **protocolo** (`udp dst=67`), porque el destino IP es broadcast. Las respuestas encuentran al host por su MAC (`eth_dst=MAC A1 → p1`), regla instalada al aprenderlo.
- **Sinergia con el anti-spoofing**: una respuesta ARP mentirosa no prospera — el controlador responde con la verdad que aprendió del DHCP, y la mentira declarada es contrastable y auditable.

## 7. En qué momento del flujo entra

```text
parte 2 · arranque
  canal → LLDP → grafo                                   (ya descrito)
  + inventario declarado                                  (§4)
  + caminos hacia los servicios calculados e instalados   ← el enrutamiento entra aquí
parte 2 · primer dispositivo
  primer paquete → PACKET_IN → aprendizaje → BASE con el siguiente salto exacto
  ARP → lo responde el controlador
parte 3 · sesión
  decisión → reglas de política en el acceso; el interior ya tenía los caminos
parte 4 · seguridad
  la mitigación se instala en el switch de ingreso; los caminos no cambian
cambios de topología
  PORT_STATUS invalida el enlace (parte 2 §5.7); el efecto sobre los caminos instalados: §8
```

El enrutamiento no es una etapa del recorrido del usuario: es un estado que se prepara al arrancar y que el resto del flujo da por hecho.

## 8. Cuestiones abiertas

- **La métrica del costo por enlace** (capacidad, uso, valor manual): a fijar al implementar.
- **Cantidades, conexiones y resiliencia de la topología**: cuántos switches por nivel, cómo se enlazan y qué redundancia existe — se abordará al definir la topología; esta parte fija los tres niveles, no las cantidades. Incluye el efecto de un fallo sobre los caminos ya instalados (recálculo y reemplazo).
- **La vía y el rol que declaran el inventario de servicios** (forma de la API northbound, I2/I7): fase G.
- **El mecanismo de la inundación de respaldo** (group ALL o `PACKET_OUT`): depende del soporte de PicOS (RP-11).
- **La prioridad concreta de las reglas de camino** frente a los peldaños: por debajo de la escalera; el valor se fija al implementar.
