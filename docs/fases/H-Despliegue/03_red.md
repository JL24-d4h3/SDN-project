# Red

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** H — Despliegue
**Estado:** Borrador formal para revisión

---

La **red del despliegue es la materialización de los segmentos lógicos** ([`F-08`](../F-Decisiones_tecnologicas/08_entorno_del_prototipo.md) §2): cuatro dominios —externa, usuarios, gestión y servidores— más un **canal de control fuera de banda** que no es un segmento de datos sino el plano de gestión de los switches. Dos reglas de fondo:

- **El enrutamiento lo resuelve el plano de datos SDN.** No hay un router en el prototipo: entre segmentos reenvían los switches por las reglas de camino ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §4), y la política se aplica en el switch de ingreso. La única «ruta» entre VLANs es una entrada del controlador.
- **Direccionamiento estático IPv4** (RP-12) en todo lo que la reproducibilidad exige: servicios, servidores protegidos y hosts del escenario tienen IP fija; nada depende de negociación (RNF-11).

```text
   A1      A2      A3      A4        ← acceso: usuarios, usuarios, servidores, borde
    │╲     ╱│       │╲     ╱│
    │ ╲   ╱ │       │ ╲   ╱ │         ← cada acceso conecta con D1 y con D2 (dual-homed)
    │  ╲ ╱  │       │  ╲ ╱  │
    │  ╱ ╲  │       │  ╱ ╲  │
    │╱     ╲│       │╱     ╲│
   D1        D2                      ← distribución
    │╲       ╱│
    │ ╲     ╱ │
    │  ╲   ╱  │
    │   ╲ ╱   │
    │    ╳    │                       ← cada distribución conecta con NC1 y con NC2
    │   ╱ ╲   │
    │  ╱   ╲  │
    │ ╱     ╲ │
    │╱       ╲│
   NC1 ────── NC2                     ← núcleo, enlazados entre sí

   A1: académicos (10.1.0.10–.25)          A3: servidores (10.2.0.10–.12)
   A2: operadores (.30–.31) + atacante interno (.50)     A4: atacante externo (10.3.0.10)
   GESTIÓN 10.0.0.0/24 cuelga de A3 (VLAN 20, por el servidor):
     portal .5 · servicios .10–.17 · adaptador .27 · controlador .20 ·
     intermediario .21 · persistencia .22 · identidad .23/.24 · tiempo .25 ·
     visualización .26 · DNS .28
   canal de control (OpenFlow): ma1 de cada uno de los ocho switches ──► red de gestión
```

## 2. El direccionamiento, tabla a tabla

| Segmento | Subred | Hosts | Nota |
|---|---|---|---|
| GESTIÓN | `10.0.0.0/24` | **la plataforma:** portal `10.0.0.5` · IAM `.10` · registro `.11` · monitor `.12` · detección `.13` · incidentes `.14` · políticas `.15` · auditoría `.16` · consola `.17` · adaptador del sensor `.27` — **la infraestructura:** controlador (ONOS) `.20` · intermediario (RabbitMQ) `.21` · persistencia (PostgreSQL) `.22` · identidad institucional (FreeRADIUS `.23` + directorio `.24`) · tiempo (chrony) `.25` · visualización (Grafana) `.26` · DNS `.28` | El portal conserva la dirección de los flujos (`10.0.0.5`); es la única superficie que BASE alcanza, y solo por la regla 150 ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §3) |
| USUARIOS | `10.1.0.0/24` | académicos `.10–.25` · operadores `.30–.31` · atacante interno `.50` | Política de ingreso en A1 y A2 |
| SERVIDORES | `10.2.0.0/24` | general `.10` · privilegiado `.11` · crítico `.12` | Los activos protegidos de R2; ingreso por A3 |
| EXTERNA | `10.3.0.0/24` | atacante `.10` · «red externa» representada por el puerto de A4 | Origen de los escenarios R5 |
| Canal de control | red de gestión del laboratorio (o puertos dedicados del servidor) | `ma1` de los ocho switches | Fuera de banda (RP-02); no es una subred del prototipo |

- **DNS interno:** `10.0.0.28` resuelve los nombres del entorno de laboratorio; el esqueleto BASE permite UDP 53 pre-login ([`G-06`](../G-Diseno_de_bajo_nivel-LLD/06_reglas.md) §3). Los hosts usan IP estáticas; DHCP queda reservado para la referencia — en el prototipo la regla de DHCP existe en el esqueleto, pero el direccionamiento no depende de ella.
- **El segmento de gestión es alcanzable por el plano de datos — y esa es la frontera que se demuestra.** El DROP del esqueleto (prioridad 100) usa exactamente esta ruta (R1.6, RA-09): BASE intenta, la regla niega, y la elevación del operador (200) la abre para quien corresponde. El canal de control, en cambio, **no** pasa por el plano de datos — son dos cosas distintas y ambas existen.
- **Todo timestamp, UTC** ([`F-05`](../F-Decisiones_tecnologicas/05_persistencia_auditoria_y_tiempo.md) §5); el desfase entre nodos se mide (RNF-09).

## 3. La referencia: la misma lógica, otra escala

En el campus real los cuatro segmentos existen con su propia escala (edificios, servidores institucionales, perímetro real), el direccionamiento lo administra la institución y el canal de control puede adoptar la variante in-band con VLAN de gestión priorizada — el objetivo aspiracional ya registrado en [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md) §6 y analizado en [`01`](01_infraestructura_fisica.md) §4. Lo que no cambia es la lógica: política en el ingreso, caminos en los tramos, gestión protegida.

## 4. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| BASE alcanza el portal (150) y nada más de la gestión (100) | La frontera de RA-09 se demuestra en vivo | R1.6 |
| Elevación de operador abre el acceso a gestión (200) y expira al TTL | La escalera sobre la frontera | R1.8, P10 |
| Tráfico entre segmentos enruta por reglas de camino | Sin router: el plano de datos resuelve | flows/05 |
| Ataque de carga contra la gestión durante un escenario | El control y los servicios no se degradan | RA-09, P2 |
| Desfase de reloj entre nodos | El máximo observado | RNF-09 |
