# Inventario del slice — guion de capacidades

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Etapa 1
**Estado:** Borrador formal para revisión

---

## 1. Propósito

El inventario recoge, en cada nodo del slice, lo que el diseño asume: versiones, recursos, interfaces y capacidades del plano de datos. Es la entrada de la tabla de verificación de [`04`](04_capacidades_del_switch.md) §7 y de la propuesta de slice; no sustituye las verificaciones V1–V7 de [`F-02`](../docs/fases/F-Decisiones_tecnologicas/02_plano_de_datos_pica8.md) §4 — las prepara y deja su evidencia en un formato comparable.

Se ejecuta una vez por nodo y la salida se conserva. El script es de solo lectura salvo que se pida `--probe`; las sondas activas corren sobre un bridge temporal que se elimina al terminar.

## 2. Qué recoge cada nodo

| Nodo | Bloques | Qué decide |
|---|---|---|
| Switch (PicOS u OVS) | Versión, bridges, datapath, protocolos OpenFlow, tablas, `fail_mode`, colas, espejo, VLAN | Si el pipeline del diseño se materializa y con qué reemplazos |
| Servidor de servicios | CPU, RAM, disco, NICs, drivers, Docker, módulos del kernel | Cuántos servicios caben y con qué aislamiento de red |
| Nodo del controlador | Java, RAM, Docker, reloj, NIC | Si el nodo ONOS cumple el mínimo y si el reloj está sincronizado |
| Gateway del slice | Reenvío, rutas, firewall, NICs | Si el borde del slice enruta y filtra como el diseño espera |

Los cuatro comparten los bloques de identidad, CPU, memoria y disco; lo específico se añade según el papel del nodo.

## 3. Cómo se ejecuta

El script vive en [`inventario/inventario_slice.sh`](inventario/inventario_slice.sh). Se copia al nodo, se ejecuta y se guarda la salida:

```bash
scp implementation/inventario/inventario_slice.sh usuario@nodo:/tmp/
ssh usuario@nodo 'chmod +x /tmp/inventario_slice.sh && /tmp/inventario_slice.sh' > inventario_nodo.txt
```

En un switch, las sondas requieren root y se ejecutan aparte:

```bash
ssh usuario@switch 'sudo /tmp/inventario_slice.sh --probe' > inventario_switch.txt
```

- El rol se detecta solo; `ROL=switch` (o `servidor`, `controlador`, `gateway`) lo fija en el resumen cuando la detección no basta.
- En un switch, el inventario pasivo también se ejecuta con `sudo`: sin root no se puede leer la base de Open vSwitch y la sección de bridges queda vacía — el script lo avisa. En los demás nodos basta el usuario normal.
- Si un comando necesita root y no se ejecutó como root, su bloque queda vacío; no es un fallo del script.
- El script no lee claves, variables de entorno ni `/etc/shadow`. La salida contiene direcciones internas y versiones; se comparte solo dentro del proyecto.

## 4. La salida y su lectura

Cada bloque empieza con `== NOMBRE ==` y termina en un bloque `== RESUMEN ==` de líneas `clave=valor`, que es el que se pega en la conversación. Los valores `no-verificado` significan que la capacidad existe pero no se sondeó (falta `--probe`, root o Open vSwitch en ese nodo).

| Línea del resumen | Campo de [`04`](04_capacidades_del_switch.md) §6 |
|---|---|
| `openflow` | `openflow_1_3` — la lista de versiones negociables |
| `tablas` | `tables` |
| `meters`, `groups`, `mirror`, `queues` | `meters`, `groups`, `mirror`, `queues` |
| `sflow`, `netflow` | `sflow`, `netflow` |
| `vlan_trunk`, `cookie_timeout` | No tienen campo propio: son supuestos de alta confianza que se confirman o se corrigen |
| `rol`, `hostname`, `vcpus`, `mem_total_mb`, `disco_libre_gb` | Dimensionamiento del slice, no del switch |
| `java`, `docker`, `docker_demonio`, `compose`, `kvm`, `chrony` | Requisitos de los nodos de servicios y del controlador |

## 5. Sondas activas

`--probe` crea el bridge `br-inv-<pid>` con dos puertos internos y ejecuta sobre él las pruebas que [`04`](04_capacidades_del_switch.md) §5 describe: tablas, `meter`, `group`, cookie y timeouts, trunk VLAN, espejo, colas, sFlow y NetFlow. Un `trap` elimina el bridge y las filas creadas al terminar, incluso si el script se interrumpe. Ningún bridge existente se toca.

| Resultado | Significado |
|---|---|
| `meters=si` | El datapath acepta `METER_MOD` con banda de descarte |
| `groups=si` | Acepta `GROUP_MOD` tipo `ALL`; `FAST_FAILOVER` se confirma en la etapa 2 |
| `mirror=si` | Acepta la configuración de espejo; que llegue a una NIC externa se prueba en [`04`](04_capacidades_del_switch.md) §5 |
| `queues=si` | Acepta QoS y colas |
| `cookie_timeout=parcial` | El flujo se instala pero la cookie no se lee en `dump-flows` |

Si una sonda falla, el script imprime el detalle del error. El resultado se interpreta con ese detalle: un `no` puede ser una limitación del switch o un fallo del propio test, y solo el mensaje distingue los dos casos.

Las sondas prueban que la primitiva se acepta; no miden escala ni latencia. El llenado de tablas y el tiempo de conmutación se miden en [`04`](04_capacidades_del_switch.md) §8 y en la etapa 3.

## 6. Qué no mide

- El punto de llenado de la tabla de flujos — es la prueba de carga de [`04`](04_capacidades_del_switch.md) §8.
- El espejo hacia la NIC del sensor — depende del hipervisor y se verifica en [`04`](04_capacidades_del_switch.md) §5.
- La CLI propia de PicOS más allá de lo que expone Open vSwitch.
- La asignación de NICs y recursos que hace el hipervisor: el script ve el resultado dentro del nodo, no la configuración del slice.

## 7. Trazabilidad

| Documento | Relación |
|---|---|
| [`04_capacidades_del_switch.md`](04_capacidades_del_switch.md) | Tabla de capacidades, guion de verificación y registro que este inventario alimenta |
| [`05_plan_de_implementacion.md`](05_plan_de_implementacion.md) | Dimensionamiento de servidores y hitos del slice |
| [`06_plan_de_trabajo_etapa_2.md`](06_plan_de_trabajo_etapa_2.md) | WP2.0 usa el inventario como condición de entrada |
| [`07_plan_de_trabajo_etapa_3.md`](07_plan_de_trabajo_etapa_3.md) | Pruebas que dependen de las capacidades confirmadas |
