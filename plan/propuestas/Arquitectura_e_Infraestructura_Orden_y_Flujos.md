# Arquitectura e infraestructura: justificación, orden y flujos

**Proyecto:** Solución de seguridad para una red de campus académico
**Propósito:** Material de exposición — arquitectura (estilos y patrones), infraestructura (servicios, servidores, switches, hosts, topología) y los flujos con su orden exacto
**Estado:** Borrador formal para revisión

---

## 0. Cómo leer este documento

El documento se lee en tres bloques, y ese orden es parte del mensaje:

1. **La arquitectura** (§1) — los estilos y patrones, y el porqué de cada uno. Es lo que sostiene todo lo demás.
2. **La infraestructura** (§2) — qué piezas existen, dónde viven y por qué están ahí. Cada pieza se justifica.
3. **Los flujos** (§3) — quién participa y **en qué momento exacto**, paso a paso. Es la parte que manda en la exposición.

La frase que resume la solución entera:

> **La plataforma decide; el controlador traduce; los switches ejecutan.**
> **Observar → detectar → decidir → traducir → ejecutar → verificar.**

Cada decisión de este documento responde a una de esas dos líneas. Si una pieza no encaja en ellas, no debería estar.

---

## 1. La arquitectura: estilos y patrones, con su porqué

### 1.1 La decisión central: separación estricta de planos

La solución separa tres planos con responsabilidades que jamás se cruzan:

| Plano | Quién vive ahí | Responsabilidad | Por qué separarlo |
|---|---|---|---|
| **Gestión** | Los diez servicios, la consola, la persistencia | Observa y decide | La decisión de seguridad es lógica y auditable; no puede mezclarse con el aparato que la ejecuta |
| **Control** | ONOS y el canal OpenFlow | Traduce y coordina | Convertir órdenes en reglas es un problema de red; mezclarlo con la política haría inauditable la decisión |
| **Datos** | Los ocho switches y el tráfico | Ejecuta y reporta | La ejecución debe ser a velocidad de línea en hardware; si la decisión tardara lo que tarda el software, el ataque ya pasó |

**Por qué esto es lo primero que se justifica:** es la razón de existir de una solución SDN. En una red tradicional, la decisión y la ejecución están pegadas en cada equipo; aquí están separadas para que la decisión sea una sola, central, auditable — y la ejecución sea distribuida, en el punto de ingreso de cada atacante (P2: decisión centralizada, ejecución distribuida).

El canal de control es **out-of-band** (interfaces `ma1`, medio físico separado del plano de datos): un ataque volumétrico que sature los enlaces de datos no puede competir por el mismo cable por el que viaja la respuesta (RA-09).

### 1.2 Los cuatro estilos y su función: ninguno sobra

La solución no «elige» un estilo y descarta los otros. Usa **cuatro estilos ortogonales**, cada uno respondiendo a una dimensión distinta del problema:

| Estilo | Dimensión que resuelve | Por qué se adoptó | Dónde se ve |
|---|---|---|---|
| **Capas** | Estructura global | Separa responsabilidades por nivel: interacción, aplicación, control, infraestructura. Cada capa solo habla con su vecina | La figura de conjunto (§2.1) |
| **Orientado a eventos (Broker)** | Dinámica y reacción | Un ataque es un suceso que debe propagarse a varios interesados sin que el emisor sepa quiénes son ni espere respuesta. Desacopla productores de consumidores | Todo el catálogo de eventos (§3) |
| **Cliente–servidor** | Interacción en el borde | El login, la consola y las órdenes exigen respuesta inmediata; no se pueden encolar | Portal↔IAM, Consola↔servicios, I2 |
| **Microservicios** | Descomposición interna | Cada responsabilidad tiene dueño, contrato y persistencia propia; se evoluciona y escala por separado | Los diez servicios (§2.2) |

**Por qué no basta con «capas»:** las capas explican dónde vive cada cosa, pero no explican cómo reacciona el sistema a un ataque. **Por qué no todo es eventos:** el evento *informa*; el comando *ejecuta*. Una mitigación debe aplicarse con confirmación — por eso viaja como comando síncrono (I2) y publica su eco al bus para que Auditoría y Consola la vean. Convertir todo en eventos sacrificaría la confirmación; convertir todo en llamadas acoplaría los servicios entre sí.

### 1.3 Los patrones internos

| Patrón | Dónde | Por qué |
|---|---|---|
| **Broker** | Entre todos los servicios | Un intermediario de mensajería con colas durables, reintentos y cola de descarte (DLQ): ningún evento se pierde en silencio, y un consumidor caído no detiene al productor |
| **Pipe-and-Filter** | **Solo** dentro de Detección | La clasificación es una cadena: captura → normalización → extracción de características → detección estadística → clasificación. Cada etapa es reemplazable sin tocar las demás |
| **Repository** | Cada servicio con su base | Aísla la lógica de su persistencia. **Por qué una base por servicio y no una sola:** cada dueño controla su esquema, su evolución y su respaldo; la correlación entre servicios se hace por identificadores (sesión, incidente, dispositivo) en los eventos — jamás por JOIN entre bases de servicios distintos |

### 1.4 Cada pieza responde una pregunta

Esta tabla es la defensa más corta de la arquitectura: si un elemento no responde a una pregunta, sobra.

| Elemento | Pregunta que responde |
|---|---|
| IAM/AAA | ¿Quién es? |
| Portal | ¿Por dónde se acredita? |
| Registro | ¿Este dispositivo está habilitado para intentarlo? |
| Políticas | ¿Qué puede hacer, aquí y ahora? |
| Monitor | ¿Qué está pasando en la red? |
| Detección | ¿Eso que pasa es anómalo? |
| Incidentes | ¿Qué incidente tenemos y en qué estado está? |
| Auditoría | ¿Quién hizo qué, cuándo y por qué? |
| ONOS | ¿Cómo se traduce la decisión a reglas OpenFlow? |
| Switches | ¿Dónde se ejecuta, a velocidad de línea? |
| Broker | ¿Cómo se propaga lo que pasó sin acoplar a nadie? |
| TCAM | ¿Cuánta política cabe en el hardware? |

---

## 2. La infraestructura: qué existe y por qué está ahí

### 2.1 El mapa general

```text
        ACTORES                    INTERACCIÓN                 PLATAFORMA (10 servicios)
 académico · TI · Admin ·   ──►   Portal (.5) · Consola (.17)  ──►  IAM · Registro · Monitor
 Superadmin · atacantes          · API northbound (I2)             Detección · Incidentes ·
                                                                   Políticas · Auditoría ·
                                                                   Adaptador (.18)
                                        │ I5 (eventos, asíncrono)        ▲
                                        ▼                               │ I8 (contadores 5 s/60 s)
                              ═══ EVENT BROKER ═══ (RabbitMQ .21) ───────┘
                                        │
        I2: solo Políticas ──► orden síncrona con confirmación
                                        ▼
                              ┌─ CONTROL: ONOS (.20) ─┐
                              │  I1: OpenFlow 1.3     │
                              │  OOB por ma1 · tcp 6653
                              ▼
        PLANO DE DATOS: NC1═NC2 → D1·D2 → A1·A2·A3·A4 (13 enlaces, dual-homed)
                              │
                 VLAN 10 usuarios · VLAN 20 gestión · VLAN 30 servidores · VLAN 40 externa
                 A4 p47 → espejo → Suricata (.27, fuera de camino) → Adaptador → bus
```

Regla de lectura del mapa: **las flechas punteadas informan; la flecha sólida de Políticas a ONOS ejecuta.** Todo lo demás que se vea en la red es consecuencia de esa distinción.

### 2.2 Los diez servicios de la plataforma

La plataforma tiene **diez servicios, todos separados**. Siete forman el núcleo de decisión; tres completan las fronteras (interacción e integración). Ninguno se absorbe en otro — esa es una decisión cerrada del diseño.

| Servicio | Dir. | Responsabilidad (una frase) | Por qué existe como servicio propio |
|---|---|---|---|
| **Portal** | `.5` | Punto de entrada cautivo: login y solicitud de elevación | Es la única superficie que el perfil BASE alcanza (regla 150); si fuera parte de IAM, la frontera de red de IAM se expondría a usuarios no autenticados |
| **IAM/AAA** | `.10` | Autenticación y ciclo de vida de sesiones | Decide quién es: comunidad académica contra el IdP (RADIUS/LDAP), operadores contra `bd_iam` con bcrypt + TOTP. Liga la sesión al dispositivo: cookie ↔ (MAC, puerto, IP) |
| **Registro** | `.11` | Catálogo de dispositivos privilegiados | Regla inversa de P7: la MAC no es credencial; el registro solo habilita el *intento* de autenticación. Historial de altas y bajas (P30) |
| **Monitor** | `.12` | Observación pasiva: contadores y línea base | Único que lee el plano de datos (vía ONOS, I8). Mantiene μ y σ con EWMA y verifica que una mitigación *funcionó de verdad* |
| **Detección** | `.13` | Clasificación de anomalías | Separada del Monitor porque observar y juzgar son trabajos distintos (frecuencias, algoritmos y umbrales evolucionan solos). Pipe-and-Filter interno |
| **Incidentes** | `.14` | Ciclo de vida del incidente (`INC-xxxx`) | Da memoria al sistema: estados ABIERTO → EN_MITIGACION → MITIGADO → CERRADO (rama ESCALADO), secuencia monótona por incidente, reconciliación tras caídas |
| **Políticas** | `.15` | Motor de decisión: ABAC + escalera | **Único autorizado a emitir órdenes I2.** Si cualquier servicio pudiera ordenar reglas, no habría una sola voluntad sobre la red |
| **Auditoría** | `.16` | Quién, qué, cuándo, por qué | Ingiere todo el catálogo de eventos; exporta JSONL append-only con cadena SHA-256. La trazabilidad no puede depender de que otro servicio recuerde |
| **Consola** | `.17` | Interfaz de operación (I7) | Los operadores ven alertas, aprueban elevaciones y gestionan políticas; es cliente de los servicios, no parte de ellos |
| **Adaptador del sensor** | `.18` | Puente entre Suricata y el bus | Único que habla con el sensor: traduce alertas `eve.json` a `AnomalyDetected`. Si el formato del IDS cambia, solo cambia él |

**La defensa frente a «son muchos servicios»:** la separación lógica es innegociable porque es lo que hace auditable la cadena de decisión; lo que se ajusta es el despliegue. Los diez corren como contenedores en un único servidor, co-localizados por afinidad — identidad (Portal, IAM, Registro, IdP), observabilidad (Monitor, Detección, Adaptador, Grafana), respuesta (Incidentes, Políticas), gobierno (Auditoría, Consola). Mismo host no significa mismo servicio: fronteras intactas, y la descomposición queda lista para heredarse en un despliegue en nube sin cambios.

### 2.3 La infraestructura materializada: cada papel, un producto

La regla del corpus: primero el papel, luego el producto que lo materializa. Ningún producto aparece como par de un servicio de la plataforma.

| Papel | Producto | Por qué ese producto |
|---|---|---|
| Controlador SDN | **ONOS 2.7 LTS** | Controlador de producción con API northbound propia, OpenFlow 1.3, primitivas de grupo/medidor y clúster nativo (Raft/Atomix) para la referencia de alta disponibilidad. La plataforma no habla OpenFlow: habla con ONOS |
| Intermediario de eventos | **RabbitMQ 3.13** | Exchange topic, colas durables, acuses manuales, DLQ y colas dinámicas (`inc.<INC-id>`) — todo lo que el modelo de eventos exige, con entrega al menos una vez + idempotencia por `evento_id` |
| Persistencia | **PostgreSQL 16** | Una base por servicio (`bd_iam`, `bd_registro`, `bd_monitor`, `bd_incidentes`, `bd_politicas`, `bd_auditoria`). Relacional porque el dominio es relacional; por servicio por el patrón Repository |
| Identidad institucional (IdP simulado) | **FreeRADIUS 3.2 + OpenLDAP** | RADIUS es el protocolo AAA del campus: la comunidad académica se autentica contra el IdP **simulado con el protocolo real**. LDAP es el directorio. Simulado en el laboratorio, real en el campus |
| Sensor perimetral (IDS) | **Suricata 7** | IDS maduro con salida JSON (`eve.json`) y **fuera de camino**: ve una copia del tráfico por el espejo, jamás lo atraviesa. Por qué fuera de camino: si el IDS cae, la red sigue — degrada R5, no corta el campus |
| Tiempo | **chrony 4.5** | El reloj común (UTC) es lo que hace correlacionables los timestamps de eventos y auditoría |
| Visualización | **Grafana 11** | Dashboards en modo lectura para los operadores; no es vía de mando |
| DNS del entorno | **dnsmasq** | Nombres del laboratorio (`.28`); el esqueleto BASE permite UDP 53 pre-login |

### 2.4 El controlador SDN — la pieza de la exposición

**Qué hace ONOS:**
- Aprende la topología y las asociaciones (MAC, IP, puerto, switch) con cada `PACKET_IN`.
- Traduce órdenes de alto nivel a OpenFlow 1.3: `APLICAR_PERFIL`, `APLICAR_MITIGACION`, `RETIRAR` → `FLOW_MOD`/`METER_MOD`.
- Codifica **cookies** de 64 bits (`Tipo << 48 | ID`: 0x01 sesión, 0x02 incidente, 0x03 esqueleto, 0x04 caminos) — así cada regla sabe de quién es y puede retirarse quirúrgicamente.
- Confirma en dos niveles: `APLICADA` (regla instalada) y verificación posterior del efecto real en el tráfico.

**Qué NO hace ONOS:** no autentica usuarios (eso es IAM), no decide política de seguridad (eso es Políticas), no verifica mitigaciones (eso es Monitor). Es el traductor, no el juez.

**Instancia única vs. clúster (decirlo sin que suene a hueco):** el prototipo despliega una instancia; la referencia documenta un clúster de 3 nodos con consenso Raft, un maestro por dispositivo (`OFPT_ROLE_REQUEST`) y reconciliación tras caída (reinstala lo faltante, no barre lo vigente). La redundancia del **plano de datos** sí se despliega y se mide — ocho switches dual-homed; la del plano de control se analiza por diseño.

### 2.5 El servidor del laboratorio

Un único servidor físico (KVM/libvirt, ≥ 32 GB RAM) sostiene todo el plano de gestión:

- **La regla VM vs. contenedor:** lo que la red debe ver como un equipo real (MAC propia, IP propia, puerto propio) es una **VM**; lo que es un proceso de servicio sin identidad de red es un **contenedor**.
- **24 VMs:** 16 hosts académicos (`10.1.0.10–.25`) · 2 operadores (`.30–.31`) · atacante interno (`.50`) · atacante externo (`10.3.0.10`) · 3 servidores protegidos (`10.2.0.10–.12`) · el sensor Suricata (`.27`, con su NIC de espejo sin IP).
- **5 NIC físicas, y por qué cinco:** cada población entra por una NIC distinta para que la topología física coincida con la política —
  `NIC-A ↔ A3 p6` (trunk de gestión, VLAN 20) · `NIC-B ↔ A1 p20` (hosts académicos) · `NIC-C ↔ A4 p4` (atacante externo) · `NIC-D ← A4 p47` (espejo, solo recepción) · `NIC-E ↔ A2 p6` (operadores, atacante interno y el puente de la demo `MAC_Moved`).
- Los hosts virtuales comparten puerto por población; la red los distingue por MAC — y las reglas de política son por MAC, no por puerto.

### 2.6 Los switches y la topología (lo justo: la TCAM la detallan otros)

**8 switches Pica8/PicOS, jerarquía de tres niveles, 13 enlaces:**

```text
   NC1 ────────── NC2        núcleo: enlazados entre sí (p3↔p3)
   ╱ ╲             ╱ ╲
  D1  ╲           ╱  D2      distribución: cada uno llega a AMBOS núcleos
  ╱│╲  ╲         ╱  ╱│╲
 A1 A2 A3        A4          acceso: cada uno dual-homed (p1→D1, p2→D2)
```

**Por qué 8 y por qué así:** con 3 switches en cadena, un corte aísla media red y la «redundancia» es decorativa. Con esta jerarquía, **todo acceso, toda distribución y todo destino quedan a un fallo de enlace o de switch del resto de la red**: cae un enlace A1–D1 → el tráfico conmuta por D2 (grupo fast-failover si la verificación lo confirma, o recálculo del controlador); cae NC1 → la red queda completa por NC2; cae un acceso → solo ese acceso se aísla. La redundancia del plano de datos **se demuestra en vivo**, que es exactamente lo que la exposición necesita. Además, un ataque distribuido desde A1, A2 y A4 se mitiga simultáneamente en tres switches de ingreso — la demostración de concurrencia (P9).

**La TCAM en una frase** (el detalle es de los compañeros): cada regla de política ocupa una entrada de tabla del switch; el peor switch (A1) acumula 188 entradas en el escenario extremo, contra ~2.000 que admite el hardware (≈ 9.4 % de utilización). La envolvente global del diseño es 350–450 reglas en los ocho switches. El límite físico existe, y el diseño lo respeta con margen — el número exacto se mide en el laboratorio.

**El espejo y el canal de control:** A4 p47 replica el ingreso externo hacia el sensor (solo recepción, fuera del camino); las interfaces `ma1` de los ocho switches forman el canal OpenFlow, físicamente separado del tráfico de datos.

### 2.7 Los segmentos: la VLAN no concede nada

| VLAN | Subred | Segmento | Quién vive ahí |
|---|---|---|---|
| 10 | 10.1.0.0/24 | USUARIOS | académicos, operadores, atacante interno |
| 20 | 10.0.0.0/24 | GESTIÓN | los diez servicios, ONOS, broker, bases, identidad, tiempo, visualización, DNS |
| 30 | 10.2.0.0/24 | SERVIDORES | los activos protegidos: general `.10`, privilegiado `.11`, crítico `.12` |
| 40 | 10.3.0.0/24 | EXTERNA | borde y atacante externo |

**Por qué importa decirlo:** la VLAN agrupa y direcciona, **no concede permisos**. El permiso vive en las reglas del pipeline (la denegación a gestión es la prioridad 100; la sesión es la 200). Un host en la VLAN correcta sin la regla correcta no llega a nada.

---

## 3. Los flujos, paso a paso — el corazón de la exposición

Regla de lectura: cada flujo se cuenta como narrativa numerada. El número es el **orden**: lo que pasa en el paso 4 pasó después del 3 y antes del 5. Si en la exposición te preguntan «¿y en qué momento entra X?», la respuesta es el número de paso.

### 3.0 Quién habla con quién (la tabla maestra de interacciones)

| Servicio | Habla con | Por qué interfaz | Modo |
|---|---|---|---|
| Portal | IAM | I3 (HTTP) | Síncrono — el login espera respuesta |
| IAM | IdP (FreeRADIUS/LDAP) | I4 (RADIUS 1812/1813 + LDAP) | Síncrono |
| IAM | bus | I5 | Asíncrono (publica sesiones, elevaciones solicitadas) |
| Registro | bus | I5 | Asíncrono |
| Monitor | ONOS (contadores) | I8 | Síncrono, sondeo 5 s / 60 s |
| Monitor | bus | I5 | Asíncrono (`MetricSample`, `MitigationVerified`) |
| Detección | bus | I5 | Asíncrono (consume métricas, publica anomalías) |
| Incidentes | bus | I5 | Asíncrono |
| Políticas | bus | I5 | Asíncrono (consume) |
| **Políticas** | **ONOS** | **I2 (REST, TLS)** | **Síncrono — el único canal de órdenes** |
| ONOS | Switches | I1 (OpenFlow 1.3, OOB) | Síncrono, tcp 6653 |
| Auditoría | bus | I5 | Asíncrono (cola `#`: todo el catálogo) |
| Consola | servicios | I7 (REST) | Síncrono |
| Adaptador | Suricata (eve.json) → bus | I5 | Asíncrono |
| Servicios | bases propias | I6 | Síncrono |

### 3.1 Flujo de conexión y login (CU-01) — aquí está tu respuesta

**El orden exacto que preguntabas:** Portal → IAM → IdP → *entonces* Políticas → ONOS → switch. Detección y Monitor **no participan** en este flujo; su momento es el flujo R4.

```text
dispositivo ──► switch ──► ONOS ──► Portal ──► IAM ──► IdP ──► IAM ──► bus ──► Políticas ──► ONOS ──► switch
  conecta      table-miss  aprende   cautivo   valida  RADIUS/  crea   Session  evalúa     APLICAR_   reglas
               PACKET_IN   MAC/IP/   (regla    creds   LDAP o   sesión Opened   ABAC       PERFIL     prioridad
                           puerto    150)              TOTP     ligada                        (I2)       200
```

1. **Dispositivo conecta** → el paquete no encuentra regla (table-miss) → `PACKET_IN` al controlador.
2. **ONOS aprende** la asociación (MAC, IP, switch, puerto) y publica `DeviceConnected` al bus (lo ven Registro, Monitor y Auditoría).
3. **ONOS instala el esqueleto BASE** (prioridades 150–100): portal, par MAC/IP, anti-spoofing, denegación a gestión y DHCP/DNS. El dispositivo aún no es nadie.
4. **El usuario abre el navegador** → la regla 150 lo lleva al Portal (10.0.0.5) — la única superficie que BASE alcanza.
5. **El Portal pide credenciales** y llama a **IAM** (I3, síncrono). El Portal es solo la puerta; no valida nada.
6. **IAM valida contra el IdP** (I4): académicos por RADIUS contra el IdP institucional (FreeRADIUS + LDAP); operadores contra `bd_iam` con bcrypt + TOTP.
7. **IAM crea la sesión** ligada al dispositivo: cookie ↔ (MAC, switch:puerto, IP). La sesión no es solo «quién», es «quién, desde dónde».
8. **IAM publica `SessionOpened`** al bus.
9. **Políticas recibe el evento y evalúa la ecuación ABAC** — rol ∧ recurso ∧ acción ∧ contexto ∧ vigencia ∧ estado de seguridad — para decidir el perfil efectivo.
10. **Políticas emite `APLICAR_PERFIL`** por I2 (síncrono, con confirmación). Es la única ruta legal hacia la red.
11. **ONOS traduce e instala** las reglas de sesión (prioridad 200, cookie de sesión, `idle_timeout` 30 min y tope 12 h para ACADÉMICO; 15 min/8 h para operadores).
12. **ONOS confirma `APLICADA`**; Auditoría registra todo el camino. La sesión vence al esqueleto (200 > 150) pero **no lo reemplaza**: el DROP hacia la gestión es permanente.

**Lo que conviene decir en la exposición:** «la identidad se exige solo para elevar privilegios» (P6). Conectarse da el mínimo; salir del mínimo pasa por IAM y termina en una regla 200 que Políticas ordenó y ONOS tradujo.

### 3.2 Flujo de elevación temporal (P28/P29)

```text
académico ──► Portal ──► IAM ──► bus ──► Políticas ──► Consola ──► Admin aprueba ──► Políticas ──► ONOS ──► switch
  pide        I3        ElevationRequested  I7 (la ve)  con TTL         ElevationGranted (I2)   reglas 200
  acceso                                                                                       TTL de elevación
```

1. El académico pide elevación en el Portal con justificación, alcance y duración.
2. IAM publica `ElevationRequested` → lo ven Políticas, Consola y Auditoría.
3. El Administrador de Red aprueba (o rechaza) desde la Consola (I7), fijando el **TTL**.
4. Políticas emite `ElevationGranted` — comando I2 con eco al bus.
5. ONOS instala las reglas de alcance elevado (prioridad 200, TTL de la elevación: 1 h).
6. Al expirar: `ElevationExpired` → retiro quirúrgico por cookie → Auditoría. Nada elevado queda permanente (P10).

### 3.3 Flujo R4 — el bucle completo (la estrella)

```text
        OBSERVAR          DETECTAR          DECIDIR                   TRADUCIR        EJECUTAR     VERIFICAR
ataque ─► contadores ─► Monitor ─► Detección ─► Incidentes ─► Políticas ─► ONOS ─► switch de ─► Monitor
  en A1    OpenFlow     5 s/60 s    EWMA          INC-xxxx      escalera     I2       ingreso       siguiente
  o A2     (vía ONOS)    μ, σ       k=4σ, piso    ABIERTO       ABAC         cookie    METER/DROP    ventana (5 s)
                     ▲   MetricSample  AnomalyDetected  IncidentOpened  MitigationRequired  MitigationApplied │
                     └────────────────────────────────── MitigationVerified ────────────────────────────────┘
```

1. **El ataque entra** por A1 o A2 (o A4) hacia un servicio protegido (p. ej. 10.2.0.10).
2. **Monitor sondea contadores** vía ONOS (I8): cada **5 s** los destinos protegidos y sus puertos de ingreso; cada **60 s** el barrido completo. Nunca habla directo con los switches.
3. **Monitor actualiza la línea base** (EWMA, α = 0.2) y publica `MetricSample`.
4. **Detección evalúa** el umbral: `x_t > μ_t + máx(k·σ_t, piso)`, con k = 4σ de entrada y piso absoluto de 200 pps (2 Mbps). Exige **N = 3 ventanas sostenidas (15 s)**; si la saturación es inmediata, vía rápida N = 1.
5. **Detección publica `AnomalyDetected`** (tipo, objetivo, orígenes, tasas, desviación).
6. **Incidentes abre el incidente** (`INC-xxxx`, estado ABIERTO, secuencia monótona) y publica `IncidentOpened`.
7. **Políticas decide la respuesta** con la escalera: `RATE_LIMIT` (meter a 35 Mbps inicial) → `BLOCK_SOURCE` → `ISOLATE_DEVICE` (TTL 10 min) → `QUARANTINE` (solo con aprobación humana).
8. **Políticas emite `MitigationRequired`** — comando I2 síncrono con TTL (300 s inicial).
9. **ONOS traduce** a `METER_MOD` o `FLOW_MOD` (DROP), prioridad **1000**, cookie de incidente (0x02), `BARRIER` de confirmación.
10. **Los switches de ingreso instalan** en hardware — la política se aplica donde el ataque entra, no junto al destino (P9).
11. **ONOS publica `MitigationApplied`** (eco al bus).
12. **Monitor verifica en la siguiente ventana (5 s):** mide el tráfico real — ¿bajó de 900 Mbps a la banda del meter? — y publica `MitigationVerified` con `cumple_objetivo`.
13. **Incidentes pasa a MITIGADO**; al expirar el timeout, `MitigationExpired` → **CERRADO**. Si la verificación falla o la brecha persiste: rama **ESCALADO** → nuevo peldaño.
14. Auditoría registró cada paso.

**Los dos momentos que hay que decir en voz alta:**
- **La regla instalada no es la mitigación efectiva.** ONOS confirma que instaló; solo el Monitor confirma que el tráfico bajó de verdad. Esa distinción es el bucle cerrado.
- **El presupuesto temporal** (de diseño, se mide en el laboratorio): `T_mitigate = T_detect (15 s) + T_event (15 ms) + T_policy (25 ms) + T_I2 (80 ms) + T_OF (45 ms) + T_ASIC (20 ms) ≈ 15.2 s` en el patrón lento; ≈ 5.2 s en la vía rápida. Casi todo el tiempo es *decidir con confianza*, no ejecutar.

### 3.4 Flujo R3 — spoofing y MAC_Moved

```text
VM cambia de A1 a A2 ─► Monitor detecta la incoherencia ─► MAC_Moved al bus ─► IAM invalida la sesión
(la MAC aparece en otro switch/puerto)      (determinista, sin umbral)        ─► Incidentes y Políticas reaccionan
                                                                              ─► el puerto retorna a BASE
```

- **Suplantación de IP:** ni llega al bus — la prioridad 110 (anti-spoofing) descarta en el ASIC todo paquete cuyo par (IP, MAC) no coincide con el aprendido (prioridad 120). Es determinista y sin latencia de decisión.
- **Movimiento físico (MAC_Moved):** el Monitor detecta la misma MAC en otro switch/puerto — no espera umbral estadístico porque es una incoherencia, no una anomalía — y publica `MAC_Moved`; **IAM invalida la sesión ligada** (la cookie ataba identidad a ubicación), y el puerto retorna a BASE. La demo del prototipo mueve la vNIC entre el puente de A1 (NIC-B) y el de A2 (NIC-E): cruza switches, el caso más fuerte.

### 3.5 Flujo R5 — el perímetro

```text
Internet ─► A4 (borde) ─► plano de datos ─► servicios        (el tráfico SIGUE su camino)
              │
              └─► espejo p47 ─► Suricata (fuera de camino) ─► eve.json ─► Adaptador ─► AnomalyDetected
                                                                                ─► misma cadena R4 ─► bloqueo en A4
```

1. El tráfico externo entra por A4 y **continúa su camino** — el sensor no es un cuello de botella: ve una copia por el espejo.
2. Suricata detecta la firma y escribe la alerta en `eve.json`.
3. **El Adaptador la traduce a `AnomalyDetected`** — a partir de aquí el sistema ya no distingue si la anomalía vino del interior o del perímetro: **reutiliza la cadena R4 completa**.
4. Políticas ordena y ONOS instala el bloqueo **en el borde** (A4), donde el tráfico malicioso entra.

### 3.6 Síntesis: en qué momento aparece cada servicio

| Servicio | CU-01 (login) | Elevación | R4 (ataque) | R3 (spoofing) | R5 (perímetro) |
|---|---|---|---|---|---|
| Portal | paso 4 | paso 1 | — | — | — |
| IAM | pasos 5–8 | paso 2 | — | invalida sesión | — |
| IdP (RADIUS/LDAP) | paso 6 | — | — | — | — |
| Registro | (escucha) | — | — | — | — |
| Monitor | (escucha) | — | pasos 2–3, 12 | detecta el movimiento | — |
| Detección | — | — | pasos 4–5 | — | — |
| Incidentes | — | — | pasos 6, 13 | reacciona | reacciona |
| Políticas | pasos 9–10 | pasos 3–4 | pasos 7–8 | reacciona | ordena bloqueo |
| ONOS | pasos 2–3, 11–12 | paso 5 | pasos 9–11 | — | instala en A4 |
| Switches | pasos 1, 11 | paso 5 | pasos 10–11 | ASIC (110/120) | A4 |
| Suricata + Adaptador | — | — | — | — | pasos 2–3 |
| Auditoría | todo | todo | todo | todo | todo |

---

## 4. Las respuestas de una frase (para las preguntas del jurado)

- **¿Por qué SDN?** Porque la decisión de seguridad debe ser una sola, central y auditable, y la ejecución debe ser instantánea y distribuida en el punto de ingreso del atacante.
- **¿Por qué un broker y no llamadas directas?** Porque el ataque es un suceso que muchos deben conocer sin que el emisor se acople a nadie; pero las órdenes que exigen confirmación van síncronas por I2.
- **¿Por qué tantos servicios?** Porque cada pregunta del sistema —quién es, qué puede, qué pasa, si es anómalo, qué incidente, cómo se aplica— tiene un dueño con contrato y persistencia propios; el despliegue los co-localiza, la lógica no los fusiona.
- **¿Por qué ONOS?** Porque la plataforma decide en términos de seguridad y ONOS traduce a red: API northbound, OpenFlow 1.3 y clúster de referencia.
- **¿Por qué ocho switches?** Para que la redundancia del plano de datos se demuestre en vivo: todo acceso dual-homed, doble núcleo, y un ataque distribuido mitigado en tres ingresos a la vez.
- **¿Por qué el IDS fuera de camino?** Para que su caída degrade la detección perimetral sin cortar la red.
- **¿Por qué OOB?** Para que un ataque que sature los datos no compita con la respuesta que viaja por el canal de control.
- **¿Por qué la TCAM importa?** Porque cada decisión de política es una entrada física en el switch: el peor caso (188 entradas ≈ 9.4 %) demuestra que el diseño cabe con margen en el hardware real.

---

## 5. Guion sugerido para 5 minutos

| Min | Bloque | Contenido |
|---|---|---|
| 0:00–0:45 | La frase | «La plataforma decide; el controlador traduce; los switches ejecutan.» Tres planos, y por qué separarlos. |
| 0:45–1:45 | Infraestructura | El servidor (24 VMs, 5 NIC, por qué cada una), los diez servicios en una frase cada uno, los papeles materializados (ONOS, RabbitMQ, PostgreSQL, IdP, Suricata). |
| 1:45–2:45 | El controlador | Qué hace ONOS y qué no hace; I2 como única ruta de órdenes; cookies; instancia única vs. clúster de referencia. |
| 2:45–4:30 | **El flujo** | Login en 12 pasos (Portal→IAM→IdP→Políticas→ONOS) y luego el bucle R4 completo con sus tiempos — la estrella. |
| 4:30–5:00 | Cierre | La tabla de síntesis (§3.6): cada servicio tiene su momento exacto, y Auditoría los mira a todos. |

Si sobra tiempo: la escalera de mitigación y el MAC_Moved cruzando switches. Si falta: recortar §4 y el detalle de TCAM (es de los compañeros).
