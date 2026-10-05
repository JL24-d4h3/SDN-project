# Entorno del prototipo

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** F — Decisiones tecnológicas
**Estado:** Borrador formal para revisión

---

La decisión de **virtualización o simulación** que activan los drivers D-06 y D-11 (B-03 §4), y con ella el entorno sobre el que todo lo decidido en esta fase se verifica. El marco ya está fijado por [`C-04`](../C-Contexto/04_alcance_de_la_infraestructura.md): la infraestructura del prototipo **representa** a la de referencia en los aspectos que los escenarios y las métricas necesitan, sin reproducir su escala (RP-04, RP-05).

## 1. Decisión: servicios en contenedores, hosts y atacantes en máquinas virtuales, plano de datos en el switch real

| Elemento del prototipo | Forma | Por qué |
|---|---|---|
| Servicios de la plataforma (IAM, registro, Monitor, Detección, Incidentes, Políticas, Auditoría, portal) | **Contenedores**, uno por servicio, en el segmento de gestión | Aislamiento y responsabilidad por servicio (P3); composición declarativa y reproducible (RNF-11); consolidación de despliegue permitida por RP-04/RP-07 |
| Controlador (ONOS) | Contenedor/VM propia en el segmento de gestión | Un plano de control separado del resto (P1); su ciclo de vida es distinto al de los servicios |
| Intermediario (RabbitMQ) y persistencia (PostgreSQL) | Contenedores en el segmento de gestión | Infraestructura de la plataforma; respaldo y operación simples |
| Hosts de usuario y servidores de servicio | **Máquinas virtuales** con su propia MAC e IP | Cada host debe ser un dispositivo real para la red: MAC propia, tráfico propio, conexión por un puerto distinto (R1.1); el contenedor compartiría identidad de red y no serviría |
| Atacante y «red externa» | VM en el segmento externo simulado | El atacante necesita su propia identidad de red y su punto de ingreso; los ataques se generan **solo dentro del entorno del proyecto** (RP-06/08) |
| Switches (plano de datos) | **Pica8/PicOS físicos** del laboratorio (RP-11) | Único lugar donde las primitivas OpenFlow y la capacidad de reglas se verifican de verdad ([`02`](02_plano_de_datos_pica8.md) §4) |
| Sensor perimetral (Suricata) | VM con la interfaz del espejo | Fuera del camino de reenvío ([`07`](07_perimetro_r5.md) §3) |
| Canal de control | Interfaces de gestión del switch, out-of-band (RP-02) | Aislado del tráfico de usuario (RA-09) |

**Conmutador virtual OpenFlow 1.3 como apoyo de desarrollo:** para el trabajo fuera de las ventanas de laboratorio y para la integración continua, la topología puede levantarse íntegramente virtual. Sus límites se declaran: las pruebas de primitivas y capacidad que deciden el diseño (§4 de [`02`](02_plano_de_datos_pica8.md)) se ejecutan **siempre contra el switch físico**; lo virtual sirve para construir y ensayar, no para firmar la verificación.

## 2. Segmentación del prototipo

La segmentación de referencia se representa con lo mínimo que la hace verificable (R2.6, C-04 §4):

```text
┌─────────────┐   ┌──────────────┐   ┌───────────────────────────────┐
│  EXTERNA    │   │  USUARIOS    │   │  GESTIÓN (out-of-band)        │
│  VM atacante│──►│  VMs host    │   │  controlador · servicios ·    │
│  (simulada) │   │  (académicos │   │  broker · BD · consola ·      │
│             │   │   y opera-   │   │  monitor · sensor IDS         │
├─────────────┤   │   dores)     │   ├───────────────────────────────┤
│ switch de   │   │              │   │  SERVIDORES                   │
│ BORDE       │   │  switches de │   │  VMs de servicio académico    │
│ (Pica8)     │   │  acceso      │   │  (representan los activos)    │
└─────────────┘   └──────────────┘   └───────────────────────────────┘
```

- Las poblaciones ocupan sus VMs en el segmento de usuarios; la elevación de un operador se demuestra desde su propia VM, con reglas de sesión hacia la gestión (escalera, prioridad 200).
- El segmento de gestión no es alcanzable desde BASE: el DROP de la escalera usa exactamente esta frontera (R1.6, RA-09).
- Los «servidores de servicio» son las VMs que representan los activos protegidos de R2; su clasificación (general/privilegiado/crítico) es la de [`A-02`](../A-Modelo_de_dominio/02_recursos_y_servicios.md).

## 3. Generación de tráfico

| Tráfico | Desde | Herramientas | Escenario |
|---|---|---|---|
| Legítimo de fondo | VMs de usuarios | Cliente HTTP/DNS/DHCP scriptado; carga sostenida (p. ej. `iperf3`, bucles `curl`) | Línea base y tráfico concurrente durante mitigaciones (R4.8) |
| Flood volumétrico | VM atacante (externa o interna según el caso) | Generador de paquetes a tasa configurable (`hping3`, `Scapy`) | R4 completo |
| Ataque distribuido | Varias VMs origen | El mismo generador, coordinado | R3.5 |
| Brute-force de solicitudes | VM de usuario | Peticiones HTTP concurrentes al portal | R4 |
| Scanning | VM de usuario | Barrido de puertos/destinos (`nmap`-equivalente controlado) | R3.2 |
| Spoofing / `MAC_Moved` | VM de usuario | Tráfico con IP/MAC manipuladas; cambio de puerto | R3.3 |
| Ataque perimetral | VM en el segmento externo | Firmas dirigidas al sensor | R5 ([`07`](07_perimetro_r5.md) §7) |

Todo se ejecuta **dentro del entorno del proyecto** (RP-06, RP-08): sin tráfico malicioso hacia redes del campus ni de terceros. Cada escenario queda definido por parámetros (orígenes, tasa, duración, destino protegido) que se registran junto a la medición — sin ellos la métrica no es reproducible.

## 4. Reproducibilidad (RNF-11)

- **Composición declarativa:** el conjunto de servicios, broker, base de datos y hosts simulados se levanta desde una definición versionada; recrear el entorno no es un procedimiento manual.
- **Configuración del plano de datos scriptada:** la configuración base de los switches (modo OpenFlow, canal de control, espejo del borde) se aplica desde guiones versionados.
- **Escenarios como parámetros:** cada prueba de ataque y de carga se lanza con parámetros explícitos y deja su registro —repetición bajo condiciones controladas— junto a las métricas que produce.
- **Versiones fijadas:** los componentes del entorno se fijan por versión para que una repetición futura no compare contra otro software.

## 5. Verificación

| Prueba | Mide | Cierra |
|---|---|---|
| Recrear el entorno completo desde la definición versionada | Sin pasos manuales; mismo estado de partida | RNF-11 |
| Repetir un escenario de ataque con los mismos parámetros | Métricas comparables entre corridas | RNF-11, RNF-12 |
| Ejecutar la verificación de primitivas en el switch físico (V1–V7 de [`02`](02_plano_de_datos_pica8.md) §4) | Lo que se firma es del dispositivo real, no del apoyo virtual | C-04 §5 |
| Ataque de carga contra el segmento de gestión durante un escenario | El canal out-of-band sostiene el control | RA-09, P2 |

## 6. Límites

- **Escala (RP-04):** el prototipo no reproduce el campus; representa los escenarios. Las cifras de capacidad y rendimiento valen para el prototipo, y así se reportan.
- **Alta disponibilidad:** la redundancia del plano de datos **se despliega y se mide** — topología de ocho switches dual-homed fijada en la Fase H ([`H-01`](../H-Despliegue/01_infraestructura_fisica.md) §3); la del plano de control (clúster del controlador) se documenta, no se despliega (C-04 §4). Los mecanismos quedaron decididos en [`01`](01_controlador_y_api_northbound.md) §6 y [`04`](04_mensajeria_y_eventos.md) §6.
- **Canal in-band:** el prototipo usa out-of-band (RP-02); la variante in-band queda como objetivo aspiracional del despliegue, ya registrado en C-04 §6.
- **Hardware:** las ventanas de uso del laboratorio condicionan cuándo corre la verificación física; el resto del tiempo rige el apoyo virtual con sus límites declarados (§1).
