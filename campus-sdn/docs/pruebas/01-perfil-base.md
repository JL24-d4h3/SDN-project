# Perfil base — manual de verificación

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Pruebas sobre el slice del laboratorio
**Estado:** Borrador formal para revisión

---

El **perfil base** (el esqueleto BASE del LLD 06_reglas §3) es la línea de entrada que todo dispositivo lleva **antes de autenticarse**: puede llegar al Portal, recibe DHCP y DNS, y jamás alcanza la red de gestión. Es lo primero que debe demostrarse: si el perfil base no se cumple, ninguna sesión se apoya en algo sólido. Este manual dice cómo verificarlo, qué esperar en cada paso y cómo dejarlo limpio.

## 1. Qué se verifica

| Propiedad | Cómo se observa |
|---|---|
| El switch descarta lo que no conoce | `fail_mode: secure` en el bridge |
| El esqueleto está instalado por el controlador | 5 entradas por switch por la API REST de ONOS |
| Solo el Portal es alcanzable sin sesión | ping/curl desde h1: el Portal responde, h2 no |
| La gestión es inalcanzable desde el plano de datos | ping a 192.168.0.10 desde `ens4`: 100% loss |
| El ARP lo resuelve el controlador | `proxyarp` activa; sin inundar a ciegas |

## 2. Prerrequisitos

- ONOS arriba en el controller y los 3 switches conectados:

  ```bash
  curl -s -u karaf:karaf http://127.0.0.1:8181/onos/v1/devices | python3 -m json.tool
  # deben aparecer los 3 datapaths con available: true
  ```

- `proxyarp` activa (el ARP es causa cerrada de PACKET_IN y lo responde el controlador):

  ```bash
  curl -u karaf:karaf -X POST \
    http://127.0.0.1:8181/onos/v1/applications/org.onosproject.proxyarp/active
  ```

- El Portal corriendo en el **controller** (contenedor `mini-portal`, 192.168.0.10:8080) y el `.env` de `/tmp/campus/` con `SWITCH_DPIDS` reales. En este slice el portal **no es alcanzable en banda** (la VNRT no entrega el retorno unicast del controller; [`00-inventario`](00-inventario-del-slice-actual.md) §7): la entrada 150 queda instalada apuntando a 192.168.0.10 y su alcance en banda se verifica con el slice real.

## 3. Instalar el esqueleto

```bash
# controller, con el script del repositorio
cd /tmp/campus
SWITCH_DPIDS=$(sed -n 's/^SWITCH_DPIDS=//p' .env) \
  SKELETON_PORTAL=192.168.0.10/32 ONOS_URL=http://127.0.0.1:8181 \
  python3 install_skeleton.py
```

El script imprime un `ok` por entrada (5 por switch). **Jamás** se instala por `ovs-ofctl`: ONOS purga los flujos que no instaló él (verificado en el slice; [`00-inventario`](00-inventario-del-slice-actual.md) §7). Si se reinstala, antes hay que retirar la app completa (el script suma, no reemplaza):

```bash
curl -u karaf:karaf -X DELETE \
  http://127.0.0.1:8181/onos/v1/flows/application/org.campus.sdn
```

## 4. Verificar las entradas en el switch

```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows swN
```

Lo esperado (además de los punteos ARP/LLDP de ONOS a prioridad 40000):

| Prioridad | Entrada | Match | Acción | Qué garantiza |
|---|---|---|---|---|
| 150 | al Portal | `ip,nw_dst=192.168.0.10` | NORMAL | el único destino fuera del plano de datos |
| 150 | del Portal | `ip,nw_src=192.168.0.10` | NORMAL | la respuesta del Portal vuelve |
| 100 | denegación a gestión | `ip,nw_dst=192.168.0.0/24` | drop | la gestión jamás se abre desde datos (salvo el Portal) |
| 10 | DHCP | `udp,tp_dst=67` | NORMAL | el dispositivo obtiene dirección |
| 10 | DNS | `udp,tp_dst=53` | NORMAL | resuelve nombres sin sesión |

Criterio: las 5 entradas presentes en los 3 switches, con los contadores a cero antes de la prueba.

## 5. Probar el perfil base

1. **Nada del plano de datos es alcanzable sin sesión.** Desde h1 y desde h4:

   ```bash
   ping -c 2 -W 2 -I ens4 10.0.0.2
   # 2 packets transmitted, 0 received, 100% packet loss
   ```

   El ARP lo responde el controlador (por eso el ping llega a intentar), pero el paquete no tiene regla y `fail_mode secure` lo descarta. (Ping de h2 a sí mismo responde: es local, no pasa por el switch; eso es correcto, no un fallo de la prueba.)

2. **La gestión jamás**:

   ```bash
   ping -c 2 -W 2 -I ens4 192.168.0.10
   # 100% packet loss — en este slice cae antes de ser IP: la gestión
   # no está en el L2 del plano de datos y proxyarp no la conoce. La
   # entrada 100 queda como la garantía de política (cubre toda la
   # subred salvo el Portal, que es la excepción de la escalera).
   ```

3. **El Portal**: en este slice, desde el plano de datos el Portal **no es alcanzable** (limitación de la VNRT, [`00-inventario`](00-inventario-del-slice-actual.md) §7). Se verifica entonces lo que sí se puede: la entrada 150 existe en los tres switches y el resto de la subred de gestión sigue cubierto por la 100. El alcance en banda del Portal se demuestra con el slice real.

4. **DHCP y DNS — dónde se ven.** En este slice los hosts traen IP estática y **no hay servidores de DHCP ni DNS en el plano de datos** (llegan con el despliegue completo); las entradas 10 existen y se prueban por sus contadores. Desde h1, una consulta DNS a cualquier destino:

   ```bash
   dig @10.0.0.2 +time=1 +tries=1 10.0.0.1     # expira: no hay servidor DNS
   sudo ovs-ofctl -O OpenFlow13 dump-flows sw2 | grep 'tp_dst=53'
   # n_packets=1, n_bytes=91 — la entrada DNS dejó pasar la consulta
   # (el paquete murió en el destino porque no hay quien responda;
   # la entrada actuó, que es lo que se verifica)
   ```

   DHCP: la entrada `tp_dst=67` queda a cero — sin servidor no hay tráfico DHCP. Con el slice real, un `dhclient` en el host sube ese contador y la IP asignada aparece en el host.

5. **Los contadores cuentan la historia**: tras las pruebas, en sw2:

   ```bash
   sudo ovs-ofctl -O OpenFlow13 dump-flows sw2 | grep -E 'priority=(150|100|10)'
   ```

   La de DNS subió (paso 4); la de gestión sube solo si el ping llegó a ser IP (en este slice cae antes en ARP, también válido); la 150 queda a cero en este slice por la limitación del Portal.

## 6. Dejar limpio

```bash
# controller: retirar solo lo de la plataforma (appId org.campus.sdn)
curl -u karaf:karaf -X DELETE \
  http://127.0.0.1:8181/onos/v1/flows/application/org.campus.sdn
# verificar en cualquier switch: quedan solo los punteos de ONOS
sudo ovs-ofctl -O OpenFlow13 dump-flows swN
```

## 7. Criterios

| Resultado | Veredicto |
|---|---|
| Pings entre hosts y a gestión caen; las 5 entradas por switch con los contadores correctos; limpieza deja solo los punteos | **perfil base funciona** |
| Un ping entre hosts responde sin sesión | hay una regla ajena (revisar qué instaló qué) |
| El contador de DNS no sube tras el `dig` | la entrada 10 no está o el tráfico no pasó por ese switch (revisar dónde cuelga el host) |
| Los flujos desaparecen solos | se instalaron por CLI: ONOS los purgó (usar el script) |

Con el perfil base verificado se pasa al siguiente manual: la autenticación (login → regla de sesión → escalera → logout), que es la entrada de [`02-lista-de-verificacion.md`](02-lista-de-verificacion.md) P01/P02.
