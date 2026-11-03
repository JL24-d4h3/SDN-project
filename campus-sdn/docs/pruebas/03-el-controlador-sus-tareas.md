# El controlador — qué hace y cómo se ve

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Pruebas sobre el slice del laboratorio
**Estado:** Borrador formal para revisión

---

Antes del perfil BASE, la sesión o la mitigación, el controlador tiene tareas propias: **descubrir** la red, **representarla** y **decidir caminos**. Este documento dice qué hace ONOS en cada tarea, con qué mecanismo, y el comando exacto para verlo en el slice. Todo lo marcado *verificado* se ejecutó y se observó en este slice.

La solución es **out of band**: el canal OpenFlow (TCP 6653) y el SSH de gestión van por la red roja (192.168.0.0/24); el plano de datos (red gris, 10.0.0.0/24) solo lleva tráfico de usuario. El diseño in-band (entrada 65000 del LLD 06_reglas) queda en el papel: no aplica aquí.

## 1. Descubrimiento de switches y enlaces (LLDP)

ONOS inyecta paquetes **LLDP** por cada puerto de cada switch conectado (los ves salir: `dump-flows` muestra el punteo `dl_type=0x88cc → CONTROLLER` a prioridad 40000). Cuando el LLDP de un switch llega por el puerto de otro, ONOS deduce el **enlace** entre ambos extremos y arma el grafo.

*Verificado*: los dos enlaces del slice — sw1:2↔sw2:1 y sw1:3↔sw3:3 — fueron descubiertos así.

```bash
# controller: enlaces y estado
curl -s -u karaf:karaf http://127.0.0.1:8181/onos/v1/links | python3 -m json.tool
# switches conectados
curl -s -u karaf:karaf http://127.0.0.1:8181/onos/v1/devices | python3 -m json.tool
# grafo completo (devices, links, hosts)
curl -s -u karaf:karaf http://127.0.0.1:8181/onos/v1/topology | python3 -m json.tool
```

También hay interfaz gráfica: túnel `ssh -L 8181:192.168.0.10:8181 -p 5800 ubuntu@10.20.11.147` y `http://localhost:8181/onos/ui` (usuario `karaf`/`karaf`): la vista de topología dibuja los switches, los enlaces y los hosts.

## 2. Descubrimiento de dispositivos (hosts)

El punteo `arp → CONTROLLER` (prioridad 40000, lo instala `hostprovider`) sube cada consulta ARP del plano de datos. De cada una, ONOS aprende **MAC, IP y ubicación** (switch y puerto) del que pregunta. Así supo, sin configuración, dónde está cada host (h1→sw2:2, etc.).

*Verificado* además con un dispositivo **nuevo**: se añadió la IP 10.0.0.9 a h4, se provocó un ARP con esa dirección y ONOS la incorporó solo:

```bash
# h4
sudo ip addr add 10.0.0.9/32 dev ens4
sudo arping -I ens4 -s 10.0.0.9 -c 2 10.0.0.1
sudo ip addr del 10.0.0.9/32 dev ens4
# controller: el nuevo extremo aparece en la lista de hosts
curl -s -u karaf:karaf http://127.0.0.1:8181/onos/v1/hosts | python3 -m json.tool
# FA:16:3E:41:9B:6D  ['10.0.0.4', '10.0.0.9']  ← aprendida sin configuración
```

Es la pieza de la que cuelga la autenticación: el portal resuelve «quién se conecta» por esta tabla (I2 `/associations`). Un host que se **mueve** de puerto se re-aprende con su ubicación nueva (el `MAC_Moved` de la plataforma se apoya en eso).

Límite de este slice: una **MAC** totalmente nueva no entra al plano de datos — la VNRT filtra MACs no conocidas ([`00-inventario`](00-inventario-del-slice-actual.md) §7). El mecanismo de ONOS es el correcto; la VNRT es la que restringe la demostración a IPs nuevas.

## 3. Rutas: cómo decide el controlador

Con el grafo (switches + enlaces), ONOS calcula **caminos más cortos** por defecto (costo de 1 salto por enlace; el LLD fija penalizaciones configurables por enlace saturado):

```bash
# camino entre h1 (sw2) y h3 (sw3)
curl -s -u karaf:karaf http://127.0.0.1:8181/onos/v1/paths/of:00001a749039894a/of:0000ca272d265744 | python3 -m json.tool
# devuelve la secuencia de switches (y su costo)
```

Qué hace el diseño con ese camino (LLD 06_reglas §4): las entradas de **caminos** (prioridad 20) — una por destino en cada switch del camino, con grupos fast-failover si el switch los soporta — las instala el controlador y las recalcula cuando el grafo cambia (`PORT_STATUS`, caída de enlace). **En la prueba mínima no se instalan**: el reenvío usa la acción `NORMAL` (aprendizaje L2 dentro del switch), y las entradas 20 llegan con el despliegue completo. La jerarquía no cambia: política (1000/200/150–100) decide *si puede*, caminos (20) decide *por dónde sale*.

## 4. Observación continua

```bash
curl -s -u karaf:karaf http://127.0.0.1:8181/onos/v1/statistics/ports | python3 -m json.tool
```

Contadores por puerto por switch: el material para la verificación de mitigaciones y para el llenado de tablas (RNF-05).

## 5. Qué NO hace el controlador (y quién lo hace)

- **No responde el ARP de todo**: lo responde solo por los hosts aprendidos (`proxyarp`); lo demás muere en el punteo.
- **No instala la política por su cuenta**: la escalera (esqueleto, sesión, mitigación) la ordena la plataforma por I2 — el adaptador traduce cada orden a flujos. ONOS es el ejecutor del plano de control; la decisión es de la plataforma.
- **No aprende con PACKET_IN para reenviar**: el PACKET_IN queda para las tres causas cerradas (table-miss de aprendizaje, ARP sin resolver, LLDP); el reenvío es proactivo.

## 6. Criterios

| Observación | Qué confirma |
|---|---|
| `/links` muestra los enlaces y `/hosts` las ubicaciones | el descubrimiento funciona |
| La IP nueva aparece en `/hosts` tras el `arping` | el sistema es adaptativo ante dispositivos nuevos |
| `/paths` devuelve la secuencia esperada | el cálculo de rutas funciona |
| Los punteos ARP/LLDP en `dump-flows` | el canal de aprendizaje está instalado |

Con esto verificado, el perfil base (manual [`01`](01-perfil-base.md)) y la autenticación se apoyan en terreno conocido.
