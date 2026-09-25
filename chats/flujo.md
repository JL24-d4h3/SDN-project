Bien, quiero me ayudes a describir con total exactitud el flujo de los requisitos solicitados en el proyecto. Haré mención a algunos puntos y dejaré al aire algunos en los que te pediré que me ayudes a explorar. Ok, para empezar, los roles definidos antes eran estudiante, profesor, especialista de TI, administrador de red y super administrador. Se hicieron las distinciones, pero como equipo notamos algo importante ... ¿realmente existen esos servicios que diferenciar de aquello a lo que puede acceder un docente que no puede ser accedido por un estudiante? En el sentido estricto, todo parece indicar que no, aunque sí consideras que sí, tendrás que proporcionarne claramente cuáles serían y si es que son relevantes. En general, la distinción la hacemos a nivel de servicio y/u opciones dentro del servicio porque imaginamosque según la plataforma uno puede hacer o una u otra cosa, pero esta distinción es dentro de plataformas educativas en las asumimos docentes y alumnos, pero no todo suele ser así, aunque claramente está enfocado a eso, pero a lo que voy es que a nivel de servicio y al tener muchos se puede tener hasta multi rol y en vez de llamar en el servicio X al rol profesor como profesor, alguien tranquilamente puede poner docente, o al estudiante oe pone alumno, o simplemente en el servicio podría no existir roles. En general estamos apuntando a ver que aquellos que consumen solo servicios tenga un nombre diferente para su rol, algo estilo tal vez "usuario académico". Por otro lado ... el profesor se centra muchísimo en la red y no tanto en los servicios. Todas las decisiones debendee responder a un por qué. Ahora bien, lo primero que te mencionaría porque será esencial en la explicación ... Imagina que la red en principio está completamente apagada, las conexiones existen, pero son sólo físicas, no se ha hecho ninguna configuración más que todo lo necesario en el controlador SDN. Entonces te pido que me describas que pasa a nivel de red de forma detallada lo que sucede cuando de repente yo enciendo toda la red y pongo en ejecución al controlador SDN. Yo imagino que todo empieza con un LLDP desde el controlador que le permite conocer la topología y las rutas óptimas y que después hay algo que gatita un evento que inicia el ARP asumo que desde los hosts, pero qué exactamente, porque el host podría no hacer absolutamente nada, ni abrir el navegador y ya haberse hecho esaespecied de MAC Learning en los switches o algo por el estilo, luego el packet in, packet out, etc. ... quiero total detalle (olvida la autenticación y autorización por el momento y solo centrémonos en todo este flujo con total detalle). Posiblemente este olvidando varias cosas del proceso u omitiendo cosas que podrían pasar si ahora hubiera autenticación y autorización, pero centrémonos en esto. Luego te diré los cambios en los flujos ya que será diferente a lo que imaginas

Sí. Y conviene separar dos cuestiones que en tu planteamiento están mezclándose:

1. **El modelo de roles/servicios de la plataforma.**
2. **El flujo de inicialización y operación de la red SDN**, que es lo que quieres estudiar primero.

Voy a centrarme ahora exclusivamente en **la red**, sin autenticación ni autorización. Pero haré explícitos los puntos donde posteriormente esas funciones podrían insertar nuevos pasos.

## 1. Primero: sobre los roles

Tu observación es importante: **“profesor” y “estudiante” no necesariamente necesitan constituir dos roles de red diferentes**.

Si ambos consumen esencialmente los mismos servicios de red —por ejemplo, DNS, DHCP, acceso a Internet, aplicaciones institucionales, servidores internos, etc.— entonces no existe una razón arquitectónica fuerte para crear:

* `ROL_ESTUDIANTE`
* `ROL_PROFESOR`

como categorías distintas **a nivel de control de acceso de red**, solamente porque en la plataforma educativa tengan capacidades diferentes.

La diferencia podría existir **dentro de los servicios de aplicación**:

```text
Usuario académico
       │
       ├── Plataforma educativa
       │       ├── capacidades de estudiante
       │       └── capacidades de docente
       │
       ├── DNS
       ├── DHCP
       ├── Internet
       └── Servicios institucionales
```

Y eso permite que un mismo usuario incluso tenga múltiples roles de aplicación.

Por tanto, preliminarmente me parece más limpio separar:

```text
ROLES DE IDENTIDAD / NEGOCIO
    ├── Usuario académico
    ├── Especialista TI
    ├── Administrador de red
    └── Superadministrador

ROLES / PERFILES DE SERVICIO
    └── determinados por cada aplicación o servicio
```

Pero **no cerraría todavía esta decisión**, porque cuando introduzcamos el control SDN aparecerá una pregunta mucho más importante:

> ¿La red necesita distinguir al docente del estudiante para aplicar una política de conectividad diferente?

Si la respuesta es no, no hay motivo para hacerlo.

---

# 2. Ahora sí: red completamente apagada → SDN operativo

Voy a asumir una arquitectura razonablemente típica:

```text
                    ┌─────────────────────┐
                    │   Controlador SDN    │
                    │                     │
                    │ Topology / Host     │
                    │ Discovery / Routing │
                    │ Flow Management      │
                    └──────────┬──────────┘
                               │
                        OpenFlow / etc.
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
              Switch 1                    Switch 2
                 │                           │
            ┌────┴────┐                 ┌────┴────┐
           Host A    Host B             Host C    Host D
```

Y hay una precisión fundamental:

> **LLDP no descubre “las rutas óptimas”.**

LLDP permite descubrir **la topología física/lógica de los enlaces entre dispositivos SDN**. El controlador posteriormente puede construir un grafo y calcular rutas sobre él.

Es una distinción importante para la explicación del proyecto.

---

# 3. Estado inicial: red físicamente conectada pero apagada

Tenemos:

```text
Host ─── Switch ─── Switch ─── Switch ─── Server
```

Los cables están conectados.

Pero:

* switches apagados;
* hosts apagados;
* controlador apagado.

Por tanto:

```text
Conectividad física:
        EXISTE

Conectividad lógica:
        NO EXISTE

Flujos OpenFlow:
        NO EXISTEN

Topología conocida por controlador:
        NO

ARP:
        NO

DNS:
        NO

DHCP:
        NO
```

Los switches pueden tener configuraciones persistentes de fábrica o mínimas, pero para el escenario conceptual que propones asumamos que **no existe todavía una política dinámica instalada por el controlador**.

---

# 4. Encendemos la infraestructura

El orden temporal importa.

Supongamos:

```text
t0 → switches se encienden
t1 → controlador SDN inicia
t2 → enlaces de control se establecen
t3 → controlador descubre topología
t4 → controlador instala reglas base
t5 → hosts comienzan a generar tráfico
```

No necesariamente ocurrirá exactamente así en una implementación real, pero es una buena abstracción arquitectónica.

---

# 5. El switch arranca

Cuando un switch SDN se enciende, realiza su proceso de boot.

Entre otras cosas:

* inicializa interfaces;
* inicializa la tabla de forwarding;
* inicializa el agente/protocolo SDN;
* intenta establecer conexión con el controlador configurado.

Por ejemplo:

```text
Switch 1
   │
   │ "Necesito conectarme al controlador"
   ▼
Controlador SDN
```

Dependiendo de la tecnología/protocolo:

* OpenFlow;
* NETCONF/gNMI;
* P4Runtime;
* OVSDB;
* etc.

En vuestro proyecto probablemente la explicación se centre en **OpenFlow**, si ese es el protocolo elegido.

---

# 6. Se establece el canal Switch ↔ Controlador

Supongamos OpenFlow.

El switch establece una conexión con el controlador.

Aquí sucede el handshake del protocolo.

Conceptualmente:

```text
Switch                         Controller
  │                                │
  │──── conexión ────────────────►│
  │                                │
  │──── HELLO ───────────────────►│
  │◄─── HELLO ────────────────────│
  │                                │
  │──── FEATURES / negociación ──►│
  │◄─── respuesta ────────────────│
  │                                │
  │       canal de control         │
  │◄══════════════════════════════►│
```

A partir de aquí el controlador puede comenzar a interactuar con el switch.

**Todavía no significa que el controlador conozca toda la red.**

Solo conoce que existe ese switch y sus capacidades/información disponible.

---

# 7. El controlador comienza a descubrir la topología

Aquí entra LLDP.

El controlador necesita descubrir:

```text
¿Quién está conectado con quién?
```

Imaginemos:

```text
       S1
      /  \
     /    \
   S2──────S3
```

El controlador no necesariamente conoce inicialmente esa estructura.

Entonces puede generar paquetes LLDP y hacer que los switches los transmitan por sus puertos.

Conceptualmente:

```text
Controller
    │
    │ LLDP
    ▼
   S1
  /  \
LLDP LLDP
 /      \
S2       S3
```

Cuando los switches reciben esos LLDP, el controlador puede inferir relaciones del tipo:

```text
S1:port2 ─── S2:port1
S1:port3 ─── S3:port1
S2:port4 ─── S3:port4
```

Así construye una representación de la topología.

---

# 8. El controlador construye el grafo

Este punto es especialmente importante para vuestra arquitectura.

El controlador transforma la información descubierta en algo conceptualmente parecido a:

```text
             10
       S1 ─────── S2
       │           │
      20           5
       │           │
       └──── S3 ───┘
             15
```

Es decir:

```text
G = (V, E)
```

donde:

* `V` = switches/nodos;
* `E` = enlaces.

Y cada enlace puede tener atributos:

```text
capacidad
latencia
utilización
pérdida
estado
costo
```

Esto permite posteriormente ejecutar un algoritmo de selección de rutas.

Por ejemplo:

```text
Ruta A: S1 → S2 → S3
costo = 10 + 5

Ruta B: S1 → S3
costo = 20
```

El controlador puede determinar:

```text
Ruta óptima = Ruta A
```

**Pero todavía no necesariamente instala esa ruta como flujos para todos los hosts.**

Ese detalle es crucial.

---

# 9. ¿El controlador instala algo inmediatamente?

Aquí aparece una de las partes que estabas intuyendo correctamente.

Puede existir una **política o regla de table-miss**.

Por ejemplo:

```text
Tabla de flujo del switch

┌──────────────┬──────────────┐
│ Match        │ Action       │
├──────────────┼──────────────┤
│ ...          │ ...          │
│ table-miss   │ CONTROLLER   │
└──────────────┴──────────────┘
```

Es decir:

> Si llega un paquete para el cual el switch no tiene una regla específica, envíalo al controlador mediante `PACKET_IN`.

Esto es fundamental para el comportamiento reactivo.

---

# 10. Y aquí aparece tu duda importante: ¿qué hace un host si no hace nada?

Supongamos que:

```text
Host A
```

está encendido.

No abre navegador.

No hace ping.

No intenta acceder a un servidor.

Entonces **no existe ninguna razón para que el host genere tráfico IP arbitrario simplemente porque la red SDN haya sido encendida**.

Esto corrige una posible interpretación:

> El controlador no necesariamente provoca un ARP de todos los hosts.

ARP normalmente aparece porque **algún host necesita resolver una dirección IPv4 → MAC**.

Por ejemplo:

```text
Host A quiere enviar a:
192.168.1.20
```

pero solamente conoce:

```text
192.168.1.20
```

y necesita:

```text
MAC de 192.168.1.20
```

Entonces genera:

```text
ARP Request
```

Pero si el host está completamente inactivo, podría no ocurrir.

---

# 11. Entonces ¿qué puede ocurrir antes de ARP?

Hay algo muy importante:

## DHCP

Si los hosts están configurados para obtener su IP mediante DHCP, entonces **al arrancar el host sí puede aparecer tráfico inmediatamente**, aunque el usuario no abra ninguna aplicación.

Por ejemplo:

```text
Host A arranca
      │
      ▼
DHCPDISCOVER
      │
      ▼
Switch
      │
      ▼
Controlador / reglas / DHCP server
      │
      ▼
DHCPOFFER
      │
      ▼
DHCPREQUEST
      │
      ▼
DHCPACK
```

Por tanto, si vuestro escenario utiliza DHCP, el host **sí comienza a generar tráfico como consecuencia de su propio arranque**.

Y eso puede iniciar toda una cadena de aprendizaje y forwarding.

---

# 12. ¿Existe “MAC learning” en SDN?

Sí, pero aquí hay que distinguir dos conceptos.

En un switch Ethernet tradicional:

```text
Ethernet frame
     │
     ▼
Source MAC
     │
     ▼
MAC address table
```

El switch aprende:

```text
MAC_A → Port 1
MAC_B → Port 7
```

Esto es **MAC learning tradicional**.

Pero en un diseño SDN/OpenFlow, el comportamiento puede ser diferente.

El controlador puede mantener un conocimiento de:

```text
Host A → MAC_A → S1:Port1
Host B → MAC_B → S2:Port3
```

y utilizar esa información para instalar reglas.

Por tanto, no deberíamos decir simplemente:

> “El controlador aprende las MAC”.

Es más preciso decir:

> **El plano de control puede construir y mantener una asociación entre hosts, direcciones MAC/IP, puertos y switches, utilizando información obtenida del tráfico y/o mecanismos de descubrimiento.**

---

# 13. Supongamos ahora que Host A arranca y utiliza DHCP

Aquí comienza un flujo interesante.

Host A genera:

```text
DHCPDISCOVER
```

Es un broadcast:

```text
Ethernet
Destination MAC:
ff:ff:ff:ff:ff:ff
```

El frame llega al switch.

```text
Host A
  │
  │ DHCPDISCOVER
  ▼
 S1
```

El switch busca una regla que coincida.

Puede ocurrir:

```text
Match:
EtherType = IPv4
UDP
port 67/68
```

o simplemente que no exista una regla adecuada.

Entonces:

```text
S1
 │
 │ PACKET_IN
 ▼
Controller
```

---

# 14. PACKET_IN

Este es uno de los puntos centrales de vuestra explicación.

El switch encapsula información del paquete y envía al controlador:

```text
PACKET_IN
```

Conceptualmente:

```text
Host A
   │
   │ DHCPDISCOVER
   ▼
Switch S1
   │
   │ PACKET_IN
   ▼
Controller
```

El controlador recibe:

* switch de origen;
* puerto de entrada;
* información del paquete;
* motivo del envío al controlador;
* metadatos correspondientes.

Ahora puede determinar:

> “Existe un host conectado al puerto X de S1 y está generando este tráfico.”

---

# 15. ¿Qué hace el controlador con ese PACKET_IN?

Depende completamente de vuestra aplicación SDN.

Podría:

### Opción A — procesar el paquete

El controlador puede decidir:

```text
este paquete debe salir por ciertos puertos
```

y enviar un:

```text
PACKET_OUT
```

### Opción B — instalar una regla

Puede decir:

```text
Para este tipo de tráfico:
    si entra por X
    entonces enviar por Y
```

mediante:

```text
FLOW_MOD
```

### Opción C — ambas

Esto es muy común en diseños reactivos:

```text
PACKET_IN
     │
     ├──► FLOW_MOD
     │
     └──► PACKET_OUT
```

El `FLOW_MOD` evita que futuros paquetes equivalentes tengan que volver al controlador.

El `PACKET_OUT` permite procesar el paquete actual.

---

# 16. ¿Y qué pasa con DHCP broadcast?

Supongamos que el DHCP server está en otra red.

El controlador podría determinar que el tráfico debe atravesar:

```text
S1 → S2 → S4
```

y establecer las reglas correspondientes.

Entonces:

```text
Host A
   │
   ▼
S1
   │
   ▼
S2
   │
   ▼
S4
   │
   ▼
DHCP Server
```

Y el camino de retorno se configura de forma equivalente.

---

# 17. Después DHCP entrega una IP

Supongamos:

```text
Host A
MAC = AA:AA:AA:AA:AA:AA
IP  = 10.0.1.25
```

Ahora el controlador y/o sus aplicaciones pueden conocer:

```text
Host A
   │
   ├── MAC = AA:AA...
   ├── IP  = 10.0.1.25
   ├── Switch = S1
   └── Port = 3
```

Esto es extremadamente útil para vuestra futura política de acceso.

Pero todavía estamos ignorando autenticación/autorización, como pediste.

---

# 18. Ahora aparece ARP

Supongamos que Host A quiere comunicarse con:

```text
10.0.1.40
```

y no conoce su MAC.

Entonces:

```text
Host A
   │
   │ ARP Request:
   │ "Who has 10.0.1.40?"
   ▼
Switch S1
```

ARP Request es broadcast.

Si no existe una regla específica, nuevamente:

```text
S1
 │
 │ PACKET_IN
 ▼
Controller
```

El controlador puede decidir qué hacer.

Por ejemplo:

```text
PACKET_IN
    │
    ▼
Analizar ARP
    │
    ▼
Determinar puertos relevantes
    │
    ├──── FLOW_MOD
    │
    └──── PACKET_OUT
```

---

# 19. El ARP Request finalmente llega al host destino

Supongamos:

```text
Host B = 10.0.1.40
```

Host B recibe:

```text
Who has 10.0.1.40?
```

y responde:

```text
ARP Reply

10.0.1.40 is at
BB:BB:BB:BB:BB:BB
```

Ahora Host A aprende:

```text
10.0.1.40
       ↓
BB:BB:BB:BB:BB:BB
```

Y puede comenzar a enviar tráfico directamente.

---

# 20. ¿Entonces el navegador es irrelevante para el descubrimiento inicial?

No exactamente, pero conceptualmente sí para **la inicialización de la red**.

Un navegador simplemente puede ser uno de los eventos que genera tráfico.

Por ejemplo:

```text
Host arranca
   ↓
DHCP
   ↓
DNS
   ↓
ARP
   ↓
TCP
   ↓
TLS
   ↓
HTTP/HTTPS
```

Pero también podría ocurrir:

```text
Host arranca
   ↓
DHCP
   ↓
ARP
   ↓
ninguna aplicación
   ↓
silencio
```

La red no necesita esperar al navegador.

---

# 21. Pero hay otra fuente de tráfico que debemos considerar: IPv6

Si vuestro proyecto contempla IPv6, el modelo cambia considerablemente.

Un host puede generar automáticamente tráfico de:

* Neighbor Discovery;
* Router Solicitation;
* Router Advertisement;
* Duplicate Address Detection;
* etc.

Es decir, incluso sin abrir ninguna aplicación puede haber tráfico de control.

Si vuestro proyecto trabajará exclusivamente con IPv4, podemos dejar esto fuera del modelo principal.

Pero **documentaría la restricción explícitamente**:

> El flujo de inicialización descrito considera IPv4; IPv6/Neighbor Discovery se encuentra fuera del alcance.

Eso evita que posteriormente alguien cuestione por qué solo aparece ARP.

---

# 22. Y hay otro detalle: DNS

Una vez que el host tiene conectividad, una aplicación puede solicitar:

```text
www.ejemplo.com
```

Antes de conectarse necesita resolver:

```text
www.ejemplo.com
       ↓
DNS
       ↓
93.x.x.x
```

Entonces aparece otra cadena:

```text
Host
 │
 │ DNS Query
 ▼
Switch
 │
 ▼
Controller / forwarding
 │
 ▼
DNS Server
```

Dependiendo de las reglas instaladas, el primer paquete DNS también podría producir:

```text
PACKET_IN
```

y posteriormente:

```text
FLOW_MOD
```

para que el resto del tráfico siga directamente el camino establecido.

---

# 23. Finalmente llega tráfico normal

Supongamos:

```text
Host A → Web Server
```

El flujo conceptual podría terminar siendo:

```text
                CONTROL PLANE
                     │
                     ▼
              ┌─────────────┐
              │ Controlador │
              └──────┬──────┘
                     │
             Topología / reglas
                     │
                     ▼
                ───────────
                 DATA PLANE
                ───────────

Host A
  │
  ▼
 S1 ─────► S2 ─────► S3
                       │
                       ▼
                    Server
```

Una vez instaladas las reglas adecuadas, **no todos los paquetes necesitan pasar nuevamente por el controlador**.

Este es precisamente uno de los principios importantes de SDN:

```text
Controlador
     │
     │ decide / programa
     ▼
Switches
     │
     │ forwarding
     ▼
Tráfico
```

No:

```text
cada paquete
     ↓
controlador
     ↓
switch
```

porque eso sería un cuello de botella y destruiría buena parte de la ventaja del plano de datos distribuido.

---

# 24. El flujo completo que yo documentaría

Para vuestro proyecto, inicialmente lo representaría así:

```text
┌──────────────────────────────────────────────┐
│           INICIALIZACIÓN DE RED              │
└──────────────────────────────────────────────┘

Switches arrancan
       │
       ▼
Establecen canal con controlador
       │
       ▼
Handshake SDN
       │
       ▼
Controlador identifica switches
       │
       ▼
Descubrimiento de topología
       │
       │ LLDP
       ▼
Construcción del grafo de red
       │
       ▼
Cálculo de rutas / conocimiento topológico
       │
       ▼
Instalación de reglas base
       │
       ▼
┌──────────────────────────┐
│ Red lista para operar    │
└────────────┬─────────────┘
             │
             ▼
        Host arranca
             │
             ▼
       ¿Necesita DHCP?
          /       \
        sí         no
        │           │
        ▼           │
   DHCP traffic     │
        │           │
        └─────┬─────┘
              ▼
       ¿Genera tráfico?
              │
              ▼
        Frame llega
        al switch
              │
              ▼
     ¿Existe FLOW-MOD
      que coincida?
         /       \
       sí         no
       │           │
       ▼           ▼
  Forwarding    PACKET_IN
                   │
                   ▼
              Controlador
                   │
             ┌─────┴─────┐
             ▼           ▼
          FLOW_MOD   PACKET_OUT
             │           │
             └─────┬─────┘
                   ▼
               Forwarding
                   │
                   ▼
             Host / Server
```

Y después:

```text
Host necesita comunicarse
          │
          ▼
¿Conoce MAC destino?
      /          \
    no            sí
    │              │
    ▼              │
   ARP             │
    │              │
    ▼              │
MAC aprendida ◄────┘
    │
    ▼
Tráfico IP
    │
    ▼
Forwarding mediante flows
```

---

# 25. Hay una corrección conceptual especialmente importante

Yo **no explicaría vuestro sistema como**:

> “El controlador enciende la red, hace LLDP, descubre las rutas óptimas, luego inicia ARP y finalmente comienza el tráfico.”

Eso establece una causalidad que realmente no existe.

Lo expresaría como **dos procesos parcialmente independientes**:

### Proceso A — construcción del conocimiento de red

```text
Switches
   ↓
Conexión con controlador
   ↓
LLDP / descubrimiento
   ↓
Topología
   ↓
Grafo
   ↓
Rutas/políticas
   ↓
Flows iniciales
```

### Proceso B — aparición y procesamiento del tráfico

```text
Host / aplicación
      ↓
DHCP / ARP / DNS / etc.
      ↓
Frame
      ↓
Switch
      ↓
¿Existe flow?
   ↙          ↘
 sí            no
 ↓              ↓
forward      PACKET_IN
                 ↓
             Controller
                 ↓
          FLOW_MOD / PACKET_OUT
                 ↓
             forwarding
```

**A y B interactúan**, pero B no necesariamente empieza porque A haya terminado.

Un host puede generar tráfico mientras el controlador todavía está descubriendo/configurando la red. Y el controlador puede seguir descubriendo topología aunque ningún host esté generando tráfico.

---

## 26. Y esto será muy importante cuando introduzcamos vuestra seguridad

Cuando después metamos **autenticación y autorización**, no deberíamos simplemente agregar:

```text
PACKET_IN
   ↓
¿Usuario autorizado?
```

porque primero tendremos que decidir **qué identidad se está intentando asociar al tráfico**.

Ahí aparecen preguntas arquitectónicas mucho más interesantes:

```text
Host
  ↓
MAC
  ↓
IP
  ↓
Puerto / switch
  ↓
Identidad del usuario
  ↓
Rol/perfil
  ↓
Política
  ↓
Flow
```

Y tendremos que determinar si la autorización ocurre:

* antes de conceder conectividad;
* durante el descubrimiento;
* mediante una VLAN/segmentación inicial;
* mediante 802.1X/RADIUS;
* mediante el controlador SDN;
* mediante una combinación de estos mecanismos.

**Ese será realmente el punto donde vuestra distinción entre “usuario académico”, TI, administrador de red y superadministrador empieza a tener consecuencias arquitectónicas.**

Por ahora, sin seguridad, el flujo fundamental es: **el controlador descubre y programa; los hosts generan tráfico; los switches ejecutan los flows; los `PACKET_IN` aparecen cuando el plano de datos encuentra tráfico que no sabe procesar según sus reglas actuales; el controlador responde instalando o aplicando comportamiento; y posteriormente el tráfico puede circular directamente por el plano de datos.**

Mucho mejor, aunque me parece que estás asumiendo una comunicación out of band, pero podría darse el caso in band, entonces posiblemente la cosa cambia. Bien, ahora si te comento: no sólo se decidió que estudiantes y profesores pasen a ser un solo rol, el de usuario académico, sino que, al ser una solución alámbrica y dentro de un campus virtual que será emulado, entonces, para los "antes profesores y estudiantes", la autenticación ahora a verse más como, perdona que pudo entrar al campus en físico, entonces es persona autenticada. Puede sonar raro, pero en realidad no cualquiera puede entrar, entonces nos salteamos la antes autenticación digital para estos roles. ¿Por qué? En la práctica, un estudiante y un profesor pueden usar diferentes computadoras, sobre todo los estudiantes (lo de los docentes lo pondría un poquito en duda, pero asumiremos que sí). Bien, pasa que, al ser solo personas que consumirán servicios y necesitan autenticarse a nivel de serviciodondel puede haber multi rol o roles que no tienen nada que ver con los roles que nosotros hemos decidido incorporar, entonces no tiene sentido hacer una autenticación a nivel de red. ¿Entonces que pasará? Pues, ellos pueden usar cualquier computadora de la red, la cuestión es que son usuarios con mínimos privilegios en la red; sin embargo, esto no será tan estáticos, en cualquier caso se puede solicitar permisos para poder hacer algunas cosas fuera de lo que haría un usuario normal en la red, pero esto tiene que ser aprobado por los administradores de red. Lo importante aquí es "mínimos privilegios". Bien, puede haber usuarios especiales como estudiantes por ejemplo del pabellón V de las carreras de informática, telecomunicaciones o electrónica que requieran extender sus capacidades en la red temporalmente para hacer algo, por ejemplo, se les puede dar acceso a algún servicio adicional o recurso para hacer pruebas o lo que sea, lo mismo podría pasar con practicantes de DTI o investigadores de los grupos de Investigación de TICs. En sí quiero que haya cierta flexibilidad a partir del contexto, pero un usuario, por ejemplo de gestión o de economía o de mecánica, entre otros, no deberían de tener esos permisos que tienen algunos de forma temporal. Por ejemplo, en principio, para el rol de estudiante prohibiría el acceso vía remota a los servicios o recursos, pero con reglas flexibles por pabellón o usuario o lo que sea eso puede cambiar. Ahora bien, acciones como suplantación de MAC entre otras deberían de no poder realizarse por parte los usuarios, entonces deberían de haber un mecanismo que lo impida, y si no se puede, entonces detectar cambios para ver quién cambio algo y luego de actuar o lo que sea. En principio la topología ya está definida de forma rígidan se asume que no se aumentan más dispositivos, aunque en la práctica se podría, y de hecho nuestra solución también podría permitirlo, pero ese nuevo dispositivo tiene una MAC asociada, entonces, dependiendo de si la PC será para cierto rol importa definir los permisos que tendrá o no. Por otro lado, para los de TI, administradores de red y super administradores, ellos, salvó el SA seguramente, aunque también de seguro si podrán acceder a través de un portal cautivo donde coloquen sus credenciales, si están autorizados ingresen, o también poder conectarse remotamente, etc. ... En general, quiero que notes que habrá PCs en la práctica que son de roles asociados al plano de control que se supone que solo ellos pueden usar esas PCs, bien ... para hacerlo, tienen que loguearse. Si no lo hacen, sus permisos serán los mínimos como si fueran estudiantes, es decir, solo se escapa privilegios con autenticación y autorización. Esta es una descripción vaga que quiero que me ayudes a afinar con cosas más técnicas, tecnologías que de seguro estoy olvidando o considerando pero mal, tal vez RADIUS, ACLs, firewalls, protocolos, etc. ... Mucho estoy pasando por alto, pero quiero que lo detalles muchísimo más para ver si de paso me entendiste

Sí. Ahora el modelo cambia bastante y, de hecho, empieza a tener una arquitectura de seguridad mucho más coherente con el escenario que plantean. La idea central que entiendo es esta:

> **La red no intenta identificar digitalmente a cada persona que consume servicios. La red identifica y controla el dispositivo, su ubicación/conectividad y su contexto; la identidad fuerte se exige solamente cuando alguien pretende obtener privilegios superiores a los mínimos.**

Eso permite que un estudiante pueda sentarse en una PC cualquiera del campus y utilizarla, mientras que una persona que necesita capacidades especiales debe demostrar una identidad autorizada.

Hay, sin embargo, varios detalles que debemos afinar.

---

# 1. Primero fijaría cuatro conceptos distintos

No conviene que "usuario", "PC", "rol" y "privilegio" sean la misma cosa.

Tenemos:

```text
PERSONA
   │
   │ puede autenticarse
   ▼
IDENTIDAD
   │
   │ posee
   ▼
ROL / ATRIBUTOS
   │
   │ determinan
   ▼
PERMISOS
   │
   │ producen
   ▼
POLÍTICAS DE RED
   │
   ▼
FLOW ENTRIES / ACL / FIREWALL / ETC.
```

Pero simultáneamente:

```text
DISPOSITIVO
   │
   ├── MAC
   ├── puerto físico
   ├── switch
   ├── VLAN
   ├── IP
   └── estado
```

Y finalmente:

```text
CONTEXTO
   ├── ubicación
   ├── pabellón
   ├── tipo de dispositivo
   ├── horario
   ├── servicio solicitado
   ├── identidad autenticada
   └── autorización temporal
```

El **controlador SDN** debería combinar estas dimensiones.

---

# 2. El rol base sería "Usuario académico"

Estoy de acuerdo con eliminar:

```text
Estudiante
Profesor
```

como roles de seguridad de red.

Quedaría:

```text
USUARIO ACADÉMICO
```

Y su característica fundamental no sería:

> "Es estudiante".

sino:

> **"Es un consumidor ordinario de los servicios de red del campus y no posee privilegios administrativos o de operación de infraestructura."**

Eso es mucho más robusto.

Además, el servicio educativo puede tener perfectamente:

```text
usuario académico
       │
       ├── estudiante
       ├── docente
       ├── investigador
       └── ...
```

sin que la red tenga que conocer esos roles.

---

# 3. El principio de mínimo privilegio

Este debería ser uno de los principios centrales de vuestra arquitectura:

> **Deny by default + least privilege.**

En términos prácticos:

```text
Dispositivo conectado
        │
        ▼
Perfil base
        │
        ▼
Privilegios mínimos
        │
        ├── DHCP
        ├── DNS
        ├── servicios académicos permitidos
        ├── Internet según política
        └── otros servicios básicos
```

Todo lo demás:

```text
DENEGADO
```

hasta que exista una política que explícitamente lo permita.

---

# 4. Entonces una PC de administrador no "es" automáticamente una PC de administrador

Este punto es importante.

Imaginemos:

```text
PC-ADMIN
   │
   └── conectada a la red
```

Antes de autenticarse:

```text
PC-ADMIN
   ↓
perfil mínimo
```

No:

```text
PC-ADMIN
   ↓
Administrador de red
   ↓
privilegios elevados
```

Eso sería peligroso.

La identidad del equipo o su ubicación puede aportar contexto, pero **no debería bastar por sí sola para conceder privilegios administrativos**.

Por tanto:

```text
PC del administrador
+
credenciales válidas
+
autenticación exitosa
+
autorización
=
privilegios administrativos
```

Mientras:

```text
PC del administrador
+
sin autenticación
=
perfil mínimo
```

Esta parte de tu planteamiento la considero fundamental.

---

# 5. ¿Dónde entra RADIUS?

Aquí **RADIUS sí tiene mucho sentido**, pero no como una solución mágica de autenticación.

RADIUS puede funcionar como **AAA**:

```text
Authentication
Authorization
Accounting
```

Por ejemplo:

```text
Usuario
   │
   ▼
Portal / Network Access Device
   │
   │ RADIUS
   ▼
RADIUS Server
   │
   ├── Authentication
   ├── Authorization attributes
   └── Accounting
```

Y detrás de RADIUS puede haber:

```text
LDAP
Active Directory
Base de datos
Identity Provider
etc.
```

Dependiendo de vuestra implementación.

---

# 6. Pero RADIUS no necesariamente debe autenticar a los usuarios académicos

Aquí está una distinción importante.

Podemos tener dos caminos.

### Usuario académico

```text
PC
 ↓
red
 ↓
perfil mínimo
 ↓
servicios permitidos
```

No necesitamos:

```text
PC
 ↓
802.1X
 ↓
RADIUS
 ↓
usuario
```

si vuestra premisa de diseño es que **el acceso físico al campus ya representa la condición de pertenencia suficiente para obtener el perfil base**.

### Usuario privilegiado

```text
PC
 ↓
Portal / mecanismo de autenticación
 ↓
RADIUS / IdP
 ↓
Authentication
 ↓
Authorization
 ↓
SDN Controller / Policy Engine
 ↓
privilegios adicionales
```

Esto coincide mucho mejor con lo que estás proponiendo.

---

# 7. Pero hay una consecuencia importante

Si permitimos que cualquier persona conectada físicamente tenga el perfil mínimo:

```text
Puerto activo
   ↓
Usuario académico / dispositivo no identificado
   ↓
acceso mínimo
```

entonces **la seguridad física del campus pasa a formar parte del perímetro de seguridad**.

Eso está bien si es una premisa deliberada.

Pero deberíamos escribirla como restricción:

> El acceso físico controlado al campus se considera una condición de confianza inicial para la obtención del perfil mínimo de red.

Porque, técnicamente, alguien que consiga conectar un dispositivo físicamente a un puerto de red estaría dentro del perímetro lógico inicial.

---

# 8. Ahora viene el problema de la PC "especial"

Supongamos:

```text
Pabellón V
   │
   ├── PC-01
   ├── PC-02
   ├── PC-03
   └── PC-ADMIN
```

No deberíamos decir:

> "PC-ADMIN pertenece al administrador".

La arquitectura debería manejar algo parecido a:

```text
Device Identity
       +
Network Location
       +
Authenticated Identity
       +
Context
       ↓
Policy Decision
```

Por ejemplo:

```text
PC-ADMIN
Switch S3
Port 12
Pabellón V
Usuario = admin01
Autenticado = sí
Rol = administrador de red
```

Entonces el Policy Engine podría producir:

```text
PERMITIR:
    SSH → switches
    HTTPS → SDN controller
    NETCONF → devices
    SNMP → monitoring
    etc.
```

Mientras:

```text
PC-ADMIN
Usuario = desconocido
```

produce:

```text
PERFIL BASE
```

---

# 9. Yo introduciría explícitamente el concepto de "perfil de acceso"

Esto les resolvería muchísimas cosas.

En lugar de convertir cada combinación en un rol:

```text
Estudiante-Pabellón-V
Estudiante-Pabellón-V-Investigación
Estudiante-Pabellón-V-Lab
Practicante-DTI
Investigador-TIC
...
```

tendrían:

```text
IDENTIDAD
+
ATRIBUTOS
+
CONTEXTO
→
ACCESS PROFILE
```

Ejemplo:

```text
Perfil BASE
Perfil LABORATORIO
Perfil INVESTIGACIÓN
Perfil PRACTICANTE_DTI
Perfil TI
Perfil ADMIN_RED
Perfil SUPER_ADMIN
```

Los perfiles pueden ser temporales.

---

# 10. Ejemplo: estudiante del Pabellón V

Inicialmente:

```text
Identidad:
no autenticada

Ubicación:
Pabellón V

Dispositivo:
PC-27

Perfil:
BASE
```

Tiene:

```text
ALLOW:
DHCP
DNS
Internet
servicios académicos
etc.
```

y:

```text
DENY:
SSH a infraestructura
OpenFlow
NETCONF
SNMP administrativo
interfaces de administración
servicios sensibles
etc.
```

Pero el estudiante necesita realizar una práctica.

Solicita:

```text
Acceso LABORATORIO
duración = 2 horas
recursos = X,Y,Z
```

Entonces:

```text
Solicitud
   ↓
Administrador de red
   ↓
Revisión
   ↓
Aprobación
   ↓
Policy Engine
   ↓
SDN Controller
   ↓
Flow updates / ACL / firewall policy
```

Durante dos horas:

```text
BASE
   +
LABORATORIO_TEMPORAL
```

Después:

```text
LABORATORIO_TEMPORAL
        ↓
   expiración
        ↓
      BASE
```

Esto es mucho más potente que crear roles permanentes.

---

# 11. Incluso podríamos modelarlo como una política temporal

Por ejemplo:

```text
Subject:
    usuario X

Device:
    PC-27

Location:
    Pabellón V

Resource:
    servidor LAB-01

Protocol:
    SSH

Time:
    14:00–16:00

Decision:
    ALLOW
```

La política podría representarse conceptualmente como:

```text
IF
    identity = X
AND
    device ∈ authorized_devices
AND
    location = PAB_V
AND
    time ∈ [14:00,16:00]
AND
    destination = LAB_01
AND
    protocol = SSH
THEN
    ALLOW
ELSE
    DENY
```

Esto ya se parece mucho más a una **política de acceso contextual** que a RBAC puro.

---

# 12. RBAC probablemente no será suficiente

Aquí creo que vuestro modelo debería evolucionar de:

```text
Role → Permissions
```

hacia algo como:

```text
Role
+
Attributes
+
Context
+
Resource
+
Action
+
Temporal constraints
```

Eso se acerca a:

* RBAC;
* ABAC;
* políticas contextuales.

No necesariamente necesitan implementar un motor ABAC formal, pero **conceptualmente vuestro sistema tiene comportamiento ABAC**.

Por ejemplo:

```text
Rol = Usuario académico
Pabellón = V
Tipo = estudiante
Actividad = laboratorio
Horario = autorizado
```

puede producir una autorización diferente a:

```text
Rol = Usuario académico
Pabellón = Economía
Actividad = navegación general
```

sin crear nuevos roles.

---

# 13. Ahora: prohibir MAC spoofing

Aquí hay que ser especialmente cuidadosos.

**No podemos garantizar simplemente desde SDN que un usuario no pueda cambiar la MAC de su propia interfaz.**

La MAC puede ser modificada en muchos sistemas operativos.

Lo que sí podemos hacer es:

### Detectar

```text
MAC X
   ↓
Switch S1:p3
```

y posteriormente:

```text
MAC X
   ↓
Switch S5:p8
```

o:

```text
MAC X
   ↓
S1:p3
```

pero aparece:

```text
MAC X
IP diferente
```

o:

```text
MAC X
identidad diferente
```

Entonces generamos:

```text
EVENT:
MAC_MOVE
```

o una anomalía equivalente.

---

# 14. Mejor todavía: combinar mecanismos de acceso de puerto

Aquí aparecen tecnologías como:

### Port security

Permite restringir:

```text
puerto → MAC(s) permitidas
```

Por ejemplo:

```text
S1:p3

Allowed:
AA:AA:AA:AA:AA:AA
```

Si aparece:

```text
BB:BB:BB:BB:BB:BB
```

podemos:

* bloquear;
* generar alarma;
* limitar;
* mover a VLAN de cuarentena;
* notificar al controlador/SIEM.

Pero nuevamente:

> **Port security no demuestra quién es la persona.**

Solo controla características del dispositivo/puerto.

---

# 15. 802.1X podría ser útil, pero no necesariamente para todos

Aquí hay una cuestión interesante.

802.1X permitiría:

```text
Device
   │
   ▼
Switch
   │
   ▼
Authenticator
   │
   ▼
RADIUS
```

y mecanismos EAP.

Pero vuestro modelo dice:

> "No quiero autenticar digitalmente al usuario académico simplemente para permitirle usar una PC."

Entonces 802.1X podría reservarse para:

```text
puertos sensibles
dispositivos administrativos
equipos de infraestructura
zonas restringidas
```

o incluso utilizar **MAB (MAC Authentication Bypass)** en ciertos escenarios, aunque MAB tiene debilidades precisamente porque la MAC puede falsificarse.

Por tanto, no recomendaría meter 802.1X indiscriminadamente solamente porque "es una red segura".

---

# 16. Una arquitectura bastante coherente sería

```text
                         ┌────────────────────┐
                         │ Identity Provider   │
                         │ / LDAP / AD / etc.  │
                         └─────────┬──────────┘
                                   │
                                RADIUS
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ AAA / Auth Service │
                         └─────────┬──────────┘
                                   │
                                   ▼
┌─────────────┐           ┌────────────────────┐
│   Usuario   │           │ Policy Engine      │
└──────┬──────┘           └─────────┬──────────┘
       │                            │
       │                            │ policy
       ▼                            ▼
┌─────────────┐              ┌───────────────┐
│ Dispositivo │─────────────►│ SDN Controller│
└──────┬──────┘              └───────┬───────┘
       │                             │
       │                       OpenFlow
       ▼                             │
┌────────────────────────────────────┴───────┐
│              SDN SWITCHES                  │
│                                             │
│ Flow Tables / ACL / VLAN / QoS / Security  │
└─────────────────────────────────────────────┘
```

Y añadiría:

```text
             ┌─────────────────────┐
             │ Monitoring / SIEM   │
             └──────────┬──────────┘
                        │
             eventos / logs / alerts
                        │
                        ▼
                  Controller
```

---

# 17. Firewall vs ACL vs Flow Entries

Aquí también conviene no mezclarlos.

### Flow Entry

Control muy granular dentro del switch:

```text
match
   ↓
action
```

Ejemplo:

```text
src IP
dst IP
TCP dst port
in_port
VLAN
etc.
```

### ACL

Política de filtrado:

```text
ALLOW / DENY
```

normalmente asociada a interfaces/VLAN/ASIC.

### Firewall

Normalmente proporciona un control de seguridad más rico y stateful:

```text
connection tracking
state
NAT
application awareness
etc.
```

### SDN Controller

No necesariamente filtra directamente los paquetes.

Su función sería:

```text
Policy
 ↓
decisión
 ↓
programación
 ↓
Flow Entries / ACL / firewall rules
```

Es decir:

> **El controlador es el cerebro de la política; los switches/firewalls ejecutan la política.**

---

# 18. Para vuestro caso yo separaría los recursos

Por ejemplo:

```text
RECURSOS DE USUARIO
├── Internet
├── DNS
├── DHCP
├── LMS
├── servidores académicos
└── aplicaciones institucionales

RECURSOS RESTRINGIDOS
├── servidores de laboratorio
├── repositorios especiales
├── recursos de investigación
└── servicios técnicos

INFRAESTRUCTURA
├── switches
├── SDN Controller
├── RADIUS
├── firewalls
├── monitoring
├── SIEM
└── sistemas de gestión
```

Y los permisos serían radicalmente distintos.

---

# 19. Tus cuatro roles quedan entonces mucho más claros

Yo los dejaría conceptualmente así:

### Usuario académico

```text
Objetivo:
Consumir servicios.

Autenticación de red:
No requerida para perfil base.

Privilegio:
Mínimo.

Administración:
No.

Acceso remoto:
Por defecto no.

Elevación:
Posible mediante solicitud/aprobación.
```

### Especialista TI

```text
Objetivo:
Operación técnica.

Autenticación:
Requerida.

Privilegio:
Elevado pero limitado al ámbito autorizado.

Acceso remoto:
Sí, sujeto a política.

Acceso a infraestructura:
Según autorización.
```

### Administrador de red

```text
Objetivo:
Administración de infraestructura de red.

Autenticación:
Requerida.

Privilegio:
Alto.

Acceso:
Switches, controlador, servicios de red, etc.,
según autorización.
```

### Superadministrador

```text
Objetivo:
Administración global de la solución.

Autenticación:
Requerida.

Privilegio:
Máximo.

Capacidad:
Administrar políticas, usuarios privilegiados,
infraestructura y configuración global.
```

Pero nuevamente:

> **El rol no debería traducirse directamente en "permitir todo".**

Debe traducirse en un conjunto de políticas.

---

# 20. El caso particularmente interesante: administrador frente a su propia PC

Este es exactamente el tipo de escenario que vuestro proyecto puede demostrar muy bien.

### Sin login

```text
PC-ADMIN
   │
   ▼
Switch
   │
   ▼
Controller
   │
   ▼
IDENTIDAD = desconocida
   │
   ▼
PROFILE = BASE
```

Resultado:

```text
Internet       ALLOW
DNS            ALLOW
Servicios base ALLOW

SSH switches   DENY
NETCONF        DENY
OpenFlow       DENY
Management     DENY
```

### Después del login

```text
PC-ADMIN
   │
   ▼
Portal / AAA
   │
   ▼
RADIUS / IdP
   │
   ▼
Authentication
   │
   ▼
Authorization
   │
   ▼
ADMIN_RED
```

Ahora:

```text
SSH switches       ALLOW
Management         ALLOW
Monitoring         ALLOW
SDN Controller     ALLOW
Network services   ALLOW
```

Y el controlador puede instalar/modificar las Flow Entries correspondientes.

---

# 21. El punto más importante: no confiar en la MAC

Yo evitaría una arquitectura como:

```text
MAC de PC-ADMIN
        ↓
Administrador de red
        ↓
privilegios
```

Porque:

```text
MAC spoofing
```

rompería el modelo.

La MAC debería ser **un atributo del dispositivo**, no una credencial.

Una arquitectura más robusta:

```text
MAC
+
Switch
+
Port
+
VLAN
+
IP
+
Device state
+
Authenticated identity
+
Context
       ↓
Policy Decision
```

Y si detectamos:

```text
MAC X
```

movida inesperadamente:

```text
S1:p4 → S7:p9
```

generamos un evento:

```text
MAC_MOVE
```

que puede llevar a:

```text
alerta
+
bloqueo
+
cuarentena
+
investigación
```

según severidad.

---

# 22. Y esto nos permite manejar dispositivos nuevos

Supongamos que aparece:

```text
Nuevo dispositivo
MAC = XX:XX
```

El controlador detecta:

```text
S4:p8
```

Pero todavía no sabe:

```text
¿quién?
¿qué dispositivo?
¿qué propósito?
¿qué permisos?
```

Por tanto:

```text
NEW_DEVICE
     ↓
DISCOVERY
     ↓
BASE PROFILE
     ↓
LIMITED ACCESS
```

Hasta que:

```text
identidad/contexto/autorización
```

permita elevar sus capacidades.

Esto es exactamente compatible con vuestra premisa de que **la topología puede considerarse estable, pero el sistema debe ser capaz de reaccionar ante nuevos dispositivos**.

---

# 23. Hay una última distinción que considero esencial

No mezclaría:

```text
"entrar físicamente al campus"
```

con:

```text
"estar autorizado para administrar la red".
```

El primero puede justificar:

```text
perfil mínimo
```

pero jamás debería justificar:

```text
privilegios elevados
```

Por tanto vuestra jerarquía de confianza podría ser:

```text
                 ┌─────────────────┐
                 │  Sin presencia   │
                 │    en campus     │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Acceso físico   │
                 │   al campus     │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Perfil mínimo   │
                 └────────┬────────┘
                          │
                    autenticación
                          │
                          ▼
                 ┌─────────────────┐
                 │ autorización    │
                 │ contextual      │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ privilegios     │
                 │ adicionales      │
                 └─────────────────┘
```

Y **la elevación puede ser temporal**:

```text
BASE
  │
  │ solicitud
  ▼
PENDING
  │
  │ aprobación
  ▼
ELEVATED(TTL)
  │
  │ expiración
  ▼
BASE
```

Ese `TTL` es importante: evita que un permiso excepcional concedido para una práctica se convierta accidentalmente en un privilegio permanente.

---

## En resumen, creo que el modelo que estás buscando es este

```text
                         ┌──────────────────┐
                         │      PERSONA     │
                         └────────┬─────────┘
                                  │
                      autenticación solo
                     cuando necesita elevar
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    IDENTIDAD     │
                         └────────┬─────────┘
                                  │
                                  ▼
        ┌──────────────────────────────────────────────┐
        │              POLICY ENGINE                   │
        │                                               │
        │ identidad + rol + atributos + contexto       │
        │ dispositivo + ubicación + tiempo + recurso   │
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
                       DECISIÓN DE ACCESO
                       ALLOW / DENY / QUARANTINE
                               │
                               ▼
                       SDN CONTROLLER
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
                OpenFlow              otros
                    │                 enforcement
                    ▼
              ┌──────────┐
              │ Switches │
              │          │
              │Flow Table│
              │ ACL      │
              │ VLAN     │
              │ QoS      │
              └────┬─────┘
                   │
                   ▼
                DEVICE
```

La idea más importante es que **no están construyendo simplemente un RBAC sobre SDN**. Están construyendo un sistema donde **el acceso base depende del contexto de conexión**, mientras que **los privilegios adicionales dependen de autenticación + autorización**, y las decisiones terminan materializándose en el plano de datos mediante **Flow Entries, ACL, segmentación y eventualmente firewalls**.

Y esto también explica por qué `Usuario académico` es mucho más adecuado que `Estudiante`/`Profesor`: **la red no necesita saber qué hace académicamente la persona para darle su conectividad base**. Esa distinción puede existir en los servicios de aplicación y aparecer ante el motor de políticas solamente cuando sea relevante para una excepción.

Estoy de acuerdo en muchos puntos. Ahora bien, cómo imaginas ese registro de especialistas de TI, administradores de red y SA? Describe ese flujo. Por otro lado, te comenté que al profesor le importa muchísimo que pasa a nivel de red más que de servicio, entonces también tendré que diseñar ese flujo. Del mismo modo, ahora te pido que me ayudes con el flujo de R4 completo, recuerda de iba y propónme algo respecto a esto

Sí. Y creo que aquí conviene hacer una separación importante: **el registro de Especialistas TI, Administradores de Red y Superadministradores no debería ser simplemente una tabla de usuarios**, porque para el profesor interesa demostrar cómo ese registro termina produciendo **estado y políticas reales en la red**.

Además, para R4 —**detectar y mitigar ataques DDoS/brute-force en la intranet cuando el tráfico hacia un servidor/nodo se dispara**— yo diseñaría un flujo que vaya desde la observación del tráfico hasta la instalación, activación y posterior retirada de reglas de mitigación en los switches.

---

# 1. Registro de Especialistas TI, Administradores de Red y Superadministradores

Yo lo modelaría como un **servicio de gestión de identidades privilegiadas**, separado conceptualmente del acceso normal de los usuarios académicos.

La idea central sería:

> **La existencia de una persona en el registro no significa que su PC tenga privilegios de administrador.**

Hay tres cosas diferentes:

1. **Identidad:** quién es la persona.
2. **Rol:** qué puede hacer esa persona.
3. **Sesión/dispositivo:** desde dónde y bajo qué contexto está ejerciendo ese rol.

Por ejemplo:

```text
Juan Pérez
    │
    ├── identidad: JPEREZ
    │
    ├── rol: ADMINISTRADOR_RED
    │
    ├── estado: ACTIVO
    │
    └── políticas permitidas:
          ├── consultar switches
          ├── consultar flujos
          ├── modificar políticas
          ├── activar mitigaciones
          └── etc.
```

Pero cuando Juan conecta su laptop:

```text
Laptop
   │
   │ conexión física
   ▼
Switch
   │
   ▼
Perfil BASE
   │
   │ autenticación de Juan
   ▼
AAA / RADIUS
   │
   ▼
Identity + Role
   │
   ▼
Policy Engine
   │
   ▼
Perfil privilegiado
   │
   ▼
SDN Controller
   │
   ▼
OpenFlow / ACL / políticas
```

Eso es mucho más defendible arquitectónicamente.

---

# 2. ¿Quién puede registrar a quién?

Aquí introduciría una **jerarquía administrativa**.

### Superadministrador

Tiene autoridad global:

```text
SUPERADMIN
   │
   ├── registra Especialistas TI
   ├── registra Administradores de Red
   ├── registra otros Superadministradores
   ├── modifica roles
   ├── revoca cuentas
   └── define políticas globales
```

### Administrador de Red

Puede administrar la infraestructura y posiblemente gestionar determinados operadores, pero **no debería poder crear arbitrariamente Superadministradores**.

```text
ADMIN_RED
   │
   ├── administra infraestructura
   ├── gestiona políticas de red autorizadas
   ├── supervisa eventos
   ├── ejecuta mitigaciones
   └── puede gestionar Especialistas TI
```

### Especialista TI

Tiene privilegios técnicos específicos, pero inferiores:

```text
ESPECIALISTA_TI
   │
   ├── diagnóstico
   ├── monitoreo
   ├── consulta de estado
   ├── determinadas operaciones técnicas
   └── determinadas acciones de mitigación
```

La matriz exacta de permisos la definiría después, pero conceptualmente:

```text
                    Especialista TI   Admin. Red   Superadmin
----------------------------------------------------------------
Consultar estado          ✓                ✓            ✓
Consultar flujos         ✓                ✓            ✓
Diagnóstico               ✓                ✓            ✓
Modificar políticas      limitado          ✓            ✓
Mitigación R4            según permiso     ✓            ✓
Registrar TI               -               ✓*           ✓
Registrar Admin. Red       -               -            ✓
Registrar Superadmin       -               -            ✓
```

`✓*` dependerá de si quieren delegar esa función.

---

# 3. Flujo completo de registro

Yo lo plantearía así.

## Fase A — Solicitud

Una persona necesita convertirse en operador privilegiado.

```text
Solicitante
    │
    │ solicitud de alta
    ▼
Sistema de gestión de identidades
```

La solicitud contiene, conceptualmente:

```text
IdentityRequest
├── persona
├── identificación institucional
├── rol solicitado
├── área/dependencia
├── justificación
├── vigencia
└── solicitante/aprobador
```

No recomiendo que el sistema simplemente permita:

> "Crear usuario → seleccionar ADMIN_RED → guardar".

Tiene que existir una **decisión de autorización**.

---

# 4. Fase B — Aprobación

Por ejemplo:

```text
Solicitud
    │
    ▼
¿Quién solicita?
    │
    ├── incorporación normal
    │
    └── cambio de privilegios
            │
            ▼
      autoridad correspondiente
            │
       ┌────┴────┐
       │         │
    APROBADA   RECHAZADA
       │
       ▼
  Crear identidad
```

Y el registro resultante podría tener:

```text
PrivilegedIdentity
-------------------------
id
username
identity_provider
role
status
valid_from
valid_until
created_by
approved_by
created_at
```

Para una universidad, incluso tendría sentido que la vigencia no sea necesariamente indefinida.

Por ejemplo:

```text
ESPECIALISTA_TI
vigencia: 2026-09-01 → 2027-09-01
```

---

# 5. Fase C — Autenticación

Aquí aparece algo fundamental para tu arquitectura:

**el registro no modifica directamente un Flow Entry.**

El usuario primero tiene que demostrar su identidad.

```text
Operador
   │
   │ username/password/MFA/etc.
   ▼
AAA / RADIUS / IdP
   │
   ├── Authentication
   │
   ├── Authorization
   │
   └── Accounting
   │
   ▼
Identidad autenticada
```

Después:

```text
Identidad
   +
Rol
   +
Contexto
   +
Estado del dispositivo
   ↓
Policy Engine
```

Y recién ahí se determina qué privilegios de red tiene.

---

# 6. ¿Qué pasa físicamente en la red?

Esta es probablemente la parte que más te interesa para la exposición.

Supongamos:

```text
                 SDN Controller
                       │
                 Policy Engine
                       │
                    RADIUS
                       │
                       │
                  ┌────┴────┐
                  │         │
                 S1         S2
                  │         │
               PC-Admin   PC-TI
```

Antes del login:

```text
PC-Admin
   │
   ▼
S1
   │
   ▼
Perfil BASE
```

Aunque sea una PC ubicada en la sala de administración.

Eso es importante porque:

> **ubicación física ≠ privilegio administrativo.**

Después del login:

```text
PC-Admin
   │
   │ autenticación
   ▼
RADIUS
   │
   ▼
ADMIN_RED
   │
   ▼
Policy Engine
   │
   ▼
SDN Controller
   │
   ▼
FLOW_MOD / ACL
   │
   ▼
S1
```

El controlador puede instalar, modificar o activar las reglas correspondientes.

Por ejemplo, conceptualmente:

```text
MATCH:
    source = IP_PC_ADMIN
    destination = management_network
    protocol = TCP

ACTION:
    ALLOW
```

mientras que el usuario académico tendría:

```text
MATCH:
    source = IP_ACADEMIC
    destination = management_network

ACTION:
    DROP
```

No significa que necesariamente implementemos esos dos Flow Entries literalmente así; depende del diseño final y de las capacidades de Pica8/PicOS. Pero **ese es el nivel de red que deberías mostrar**.

---

# 7. Ahora sí: R4

R4 lo tenemos definido como:

> **Detectar y mitigar ataques DDoS/brute-force en la intranet cuando el tráfico hacia un servidor o nodo se dispara.**

Yo evitaría modelarlo simplemente como:

```text
Ataque → IDS → bloqueo
```

Es demasiado superficial para un curso donde el profesor quiere ver SDN.

Lo convertiría en un **ciclo cerrado de detección → decisión → enforcement → recuperación**.

```text
                 ┌──────────────────────────┐
                 │      TRÁFICO NORMAL      │
                 └────────────┬─────────────┘
                              │
                              ▼
                      MONITOREO DE RED
                              │
                              ▼
                       DETECCIÓN R4
                              │
                    ¿comportamiento anómalo?
                         /          \
                       NO            SÍ
                       │             │
                       │             ▼
                       │       CLASIFICACIÓN
                       │             │
                       │             ▼
                       │       POLICY ENGINE
                       │             │
                       │             ▼
                       │      DECISIÓN MITIGACIÓN
                       │             │
                       │             ▼
                       │      SDN CONTROLLER
                       │             │
                       │          FLOW_MOD
                       │             │
                       │             ▼
                       │        SWITCHES
                       │             │
                       │             ▼
                       │      TRÁFICO MITIGADO
                       │             │
                       │             ▼
                       │       MONITOREO
                       │             │
                       └─────────────┘
```

Pero podemos hacerlo mucho más preciso.

---

# 8. R4 — Flujo detallado

Supongamos que tenemos:

```text
H1 ── S1 ── S2 ── S3 ── SERVIDOR
```

Y H1 comienza a generar una cantidad anormal de tráfico hacia el servidor.

## Paso 1 — Tráfico normal

Inicialmente:

```text
H1
 │
 ▼
S1
 │
 ▼
S2
 │
 ▼
S3
 │
 ▼
SERVER
```

Los switches están reenviando normalmente mediante sus Flow Entries.

Por ejemplo:

```text
S1:
match H1 → SERVER
action OUTPUT:p2

S2:
match H1 → SERVER
action OUTPUT:p4

S3:
match H1 → SERVER
action OUTPUT:p7
```

No necesitamos enviar cada paquete al controlador.

Ese punto es fundamental:

> **El SDN Controller no debe convertirse en el cuello de botella del plano de datos.**

---

# 9. Paso 2 — Monitorización

Ahora queremos detectar que algo está cambiando.

Hay varias posibilidades:

```text
Switches
   │
   ├── counters
   ├── byte counters
   ├── packet counters
   └── flow statistics
          │
          ▼
   SDN Controller / Monitor
```

Por ejemplo, el controlador observa:

```text
Destination: 10.0.0.50

normal:
    100 Mbps
    1 000 pkt/s

actual:
    900 Mbps
    12 000 pkt/s
```

Pero **un aumento de tráfico no necesariamente significa ataque**.

Podría ser:

* una clase virtual;
* una transferencia grande;
* una actualización;
* un servidor popular;
* una práctica de laboratorio.

Por eso no pondría:

```text
traffic > X → DDoS
```

como única condición.

---

# 10. Paso 3 — Detección

El detector puede analizar variables como:

```text
tasa de paquetes
tasa de bytes
número de fuentes
número de conexiones
destino
puerto
duración
frecuencia
distribución de IP/MAC origen
```

Y generar:

```text
DDoSDetected
```

Por ejemplo:

```text
Destination = Server A
TrafficRate = 950 Mbps
PacketRate = 18 000 pkt/s
Sources = 143
Baseline = 80 Mbps
Deviation = anomalous
```

O, para el caso de "brute-force":

```text
Source = H1
Destination = Server A
Requests/connections = anomalously high
```

Aquí haría una distinción conceptual importante:

### Flood/DDoS volumétrico

Busca saturar:

```text
ancho de banda
pps
capacidad del servidor
```

### Brute-force de solicitudes

Busca generar una cantidad excesiva de intentos:

```text
conexiones
solicitudes
intentos por segundo
```

Tu R4 puede contemplar ambos como **tráfico anómalo de alta tasa**, pero no conviene tratarlos como exactamente el mismo fenómeno.

---

# 11. Paso 4 — Crear incidente

El detector no debería bloquear directamente.

Genera:

```text
DDoSDetected
      │
      ▼
Incident Manager
      │
      ▼
Incident
```

Por ejemplo:

```text
Incident
---------------------------
id: INC-0042
type: TRAFFIC_FLOOD
target: SERVER_A
sources: H1,H2,H3...
severity: HIGH
detected_at: ...
status: DETECTED
```

Esto te permite introducir posteriormente auditoría.

---

# 12. Paso 5 — Policy Engine

Aquí está el corazón arquitectónico.

```text
Incident
   +
Network State
   +
Security Policy
   +
Context
   ↓
Policy Engine
```

El Policy Engine decide **qué hacer**.

No necesariamente:

> "Bloquear IP".

Puede decidir entre varias respuestas:

```text
NORMAL
   ↓
RATE_LIMIT
   ↓
BLOCK_SOURCE
   ↓
ISOLATE_DEVICE
   ↓
QUARANTINE
```

Dependiendo de la severidad.

---

# 13. Ejemplo de decisión

Supongamos:

```text
H1 → SERVER_A

5 000 pkt/s
```

El sistema puede decidir:

```text
SOURCE = H1
TARGET = SERVER_A
ACTION = RATE_LIMIT
```

Y generar:

```text
MitigationRequested
```

En cambio, si detecta:

```text
H1 → SERVER_A
50 000 pkt/s
multiple ports
persistent traffic
```

podría decidir:

```text
ACTION = BLOCK
```

o:

```text
ACTION = QUARANTINE
```

---

# 14. Paso 6 — SDN Controller

Aquí empieza el flujo puramente SDN.

```text
Policy Engine
      │
      │ MitigationRequest
      ▼
SDN Controller
```

El controlador conoce:

```text
Topology
+
Host location
+
Switch/port
+
Existing flows
+
Security policy
```

Entonces determina **dónde intervenir**.

Este punto es importantísimo.

Si:

```text
H1 ─ S1 ─ S2 ─ S3 ─ SERVER
```

y H1 está conectado a:

```text
S1:p5
```

no necesariamente necesitamos esperar hasta S3 para bloquearlo.

Podemos mitigar cerca del origen:

```text
H1
 │
 ▼
S1:p5
 │
 X  ← DROP/RATE LIMIT
 │
S2
 │
S3
 │
SERVER
```

Esto reduce el tráfico malicioso que sigue atravesando la red.

---

# 15. Paso 7 — FLOW_MOD

El controlador construye la regla de mitigación.

Conceptualmente:

```text
Match:
    in_port = S1:p5
    eth_src = MAC_H1
    ip_dst  = SERVER_A

Action:
    DROP
```

o:

```text
Match:
    ip_src = H1
    ip_dst = SERVER_A

Action:
    METER / RATE LIMIT
```

dependiendo de las capacidades disponibles.

Después:

```text
SDN Controller
      │
      │ FLOW_MOD
      ▼
S1
```

Y el switch instala la Flow Entry.

```text
S1 Flow Table

Priority 1000
------------------------------------
ip_src=H1
ip_dst=SERVER_A
        ↓
      DROP
```

Ahora los paquetes de H1 son descartados **en el plano de datos**.

No vuelven al controlador uno por uno.

---

# 16. ¿Y si el ataque entra por varios switches?

Ahí es donde realmente puedes demostrar la ventaja de SDN.

Supongamos:

```text
H1 ─ S1 ─┐
         │
H2 ─ S2 ─┼── S3 ─ SERVER
         │
H3 ─ S4 ─┘
```

El ataque viene desde:

```text
H1
H2
H3
```

El controlador conoce:

```text
H1 → S1:p5
H2 → S2:p3
H3 → S4:p8
```

Puede instalar las reglas en **los puntos de entrada correspondientes**:

```text
S1 → DROP H1 → SERVER
S2 → DROP H2 → SERVER
S4 → DROP H3 → SERVER
```

Eso es mucho más interesante que simplemente:

> "El firewall bloquea una IP".

Aquí estás mostrando **control centralizado de una red distribuida**.

---

# 17. Paso 8 — Verificación

Después de aplicar la mitigación:

```text
FLOW_MOD
   │
   ▼
Switch
   │
   ▼
Counters
   │
   ▼
Monitor
```

El controlador vuelve a consultar estadísticas.

Antes:

```text
900 Mbps
```

Después:

```text
35 Mbps
```

Entonces:

```text
MitigationVerified
```

Y el incidente cambia:

```text
DETECTED
   ↓
MITIGATING
   ↓
MITIGATED
```

---

# 18. Paso 9 — Recuperación

Esta parte yo **sí la incluiría en R4**, porque ya estaba implícita en el requerimiento de recuperación rápida.

No queremos que:

```text
ataque termina
      ↓
regla DROP permanece para siempre
```

porque podríamos bloquear accidentalmente al usuario legítimo.

Por eso las reglas de mitigación deberían tener, cuando sea posible:

```text
hard_timeout
idle_timeout
```

o un mecanismo equivalente gestionado por el controlador.

Por ejemplo:

```text
Mitigation Rule
TTL = 300 s
```

Después:

```text
              ataque
                 ↓
              bloqueo
                 ↓
           tráfico normal
                 ↓
          regla expira
                 ↓
        política original
```

Pero yo agregaría una segunda posibilidad:

```text
Mitigation Rule
      │
      ▼
Controller periodically verifies
      │
      ├── ataque continúa → mantener
      │
      └── ataque terminó → retirar
```

Esto es arquitectónicamente mejor que depender exclusivamente de un timeout.

---

# 19. Paso 10 — Restauración

Finalmente:

```text
SDN Controller
      │
      │ FLOW_MOD DELETE
      ▼
Switch
```

Se elimina la regla temporal:

```text
DROP H1 → SERVER_A
```

y queda nuevamente la política normal.

```text
H1
 │
 ▼
S1
 │
 ▼
S2
 │
 ▼
S3
 │
 ▼
SERVER
```

El incidente pasa a:

```text
MITIGATED
   ↓
RECOVERED
   ↓
CLOSED
```

---

# 20. ¿Dónde entran los Especialistas TI, Admin de Red y SA en R4?

Aquí conectamos ambos diseños.

Yo no haría que el sistema dependa obligatoriamente de una intervención humana para cada ataque.

Sería demasiado lento.

Lo diseñaría así:

```text
                   R4
                    │
             Detección automática
                    │
                    ▼
             Policy Engine
                    │
          ┌─────────┴─────────┐
          │                   │
    acción automática      requiere
                           autorización
          │                   │
          ▼                   ▼
       Controller       Operador autorizado
          │                   │
          │             TI / Admin / SA
          │                   │
          └─────────┬─────────┘
                    ▼
              SDN Controller
                    │
                 FLOW_MOD
                    │
                    ▼
                 SWITCH
```

Por ejemplo:

### Evento de baja criticidad

```text
anomalía leve
     ↓
RATE_LIMIT automático
```

### Evento de alta criticidad

```text
DDoS severo
     ↓
BLOCK automático
     +
notificación
```

### Acción de alto impacto

Por ejemplo, aislar un segmento entero:

```text
DDoS
 ↓
propuesta de aislamiento
 ↓
requiere autorización
 ↓
Administrador de Red
 ↓
confirmación
 ↓
Controller
```

El **Superadministrador** debería quedar para operaciones que realmente excedan el ámbito ordinario del administrador, no para cada mitigación.

---

# 21. Entonces el flujo completo de R4 quedaría

Este sería el flujo que yo llevaría al modelo de arquitectura:

```text
┌──────────────────────────────────────────────────────────────┐
│                         DATA PLANE                           │
└──────────────────────────────────────────────────────────────┘

Hosts
  │
  ▼
Switches
  │
  │ tráfico normal/anómalo
  ▼
Servidor / Nodo objetivo
  │
  │
  └────────────── estadísticas ───────────────┐
                                               ▼
┌──────────────────────────────────────────────────────────────┐
│                       CONTROL PLANE                          │
│                                                              │
│  Monitor ──► Detection Engine                               │
│                    │                                         │
│                    ▼                                         │
│              Incident Manager                               │
│                    │                                         │
│                    ▼                                         │
│              Policy Engine                                  │
│                    │                                         │
│          ┌─────────┴──────────┐                             │
│          │                    │                             │
│       permitir             mitigar                         │
│                               │                             │
│                               ▼                             │
│                       Mitigation Request                    │
│                               │                             │
│                               ▼                             │
│                       SDN Controller                        │
│                               │                             │
│                     FLOW_MOD / ACL                          │
└───────────────────────────────┼──────────────────────────────┘
                                │
                                ▼
                         ┌─────────────┐
                         │   SWITCH    │
                         │ Flow Table  │
                         └──────┬──────┘
                                │
                        DROP / LIMIT /
                        QUARANTINE
                                │
                                ▼
                         tráfico mitigado
                                │
                                ▼
                          monitorización
                                │
                       ┌────────┴────────┐
                       │                 │
                   continúa            termina
                       │                 │
                       ▼                 ▼
                  mantener          restaurar
                  mitigación        política
                                         │
                                         ▼
                                      CLOSED
```

---

# 22. Y hay una conexión interesante con tu registro de operadores

El mismo sistema puede registrar **quién hizo qué en la red**.

Por ejemplo:

```text
2026-09-24 10:32
Incident: INC-0042
Detection: automatic
Mitigation: RATE_LIMIT
Actor: SYSTEM
```

Luego:

```text
2026-09-24 10:35
Operator: jperez
Role: ADMINISTRADOR_RED
Action: BLOCK_SOURCE
Target: H1
Reason: continued_attack
```

Y:

```text
2026-09-24 10:48
Operator: jperez
Action: REMOVE_MITIGATION
Reason: incident_recovered
```

Esto te da **Accounting**, que además encaja naturalmente con AAA.

Y permite responder preguntas muy propias de una arquitectura de seguridad:

> ¿Quién modificó esta regla?

> ¿Qué regla se instaló?

> ¿En qué switch?

> ¿Cuándo?

> ¿Por qué?

> ¿Qué incidente originó la modificación?

> ¿Cuándo fue retirada?

Eso, en mi opinión, hace que el diseño deje de parecer simplemente "un SDN que bloquea IPs" y pase a ser una **arquitectura de seguridad de red gobernada por políticas**.

---

## 23. Una decisión que tomaría desde ahora

Para R4, **no pondría al IDS/Detector como el componente que ejecuta directamente el bloqueo**.

La cadena debería ser:

**Detección → Incidente → Política → Decisión → Controlador → Enforcement.**

Es decir:

```text
Detection Engine
       ≠
Policy Engine
       ≠
SDN Controller
       ≠
Switch
```

Cada uno tiene una responsabilidad distinta:

| Componente           | Responsabilidad                                          |
| -------------------- | -------------------------------------------------------- |
| **Monitor**          | Obtener métricas/estadísticas de red                     |
| **Detection Engine** | Determinar si existe comportamiento anómalo              |
| **Incident Manager** | Registrar y gestionar el incidente                       |
| **Policy Engine**    | Determinar qué respuesta corresponde                     |
| **SDN Controller**   | Traducir la decisión a mecanismos SDN                    |
| **Switch**           | Ejecutar la política en el plano de datos                |
| **Operador**         | Supervisar/autorización de acciones que lo requieran     |
| **AAA/Identity**     | Determinar quién puede realizar acciones administrativas |
| **Audit/Logging**    | Registrar las acciones y resultados                      |

Y esto conecta directamente con el flujo de registro que preguntabas: **los operadores no "entran a la red" como una entidad privilegiada; adquieren una identidad y una autorización que posteriormente se traduce en capacidades concretas sobre el plano de control y, mediante el controlador, en cambios del plano de datos.**

Para vuestro proyecto, yo haría que **R4 sea precisamente el caso de uso donde se vea toda esa cadena de extremo a extremo**, porque permite demostrar simultáneamente detección, política, SDN, OpenFlow, enforcement, privilegios y recuperación.
