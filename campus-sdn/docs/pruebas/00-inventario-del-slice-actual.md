# Inventario del slice actual

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Pruebas sobre el slice del laboratorio
**Estado:** Vivo — se actualiza cuando el slice cambia

---

Todo lo que aquí se afirma fue **verificado en el slice** (sesiones SSH, capturas de paquetes, contadores de puertos y flujos, API de ONOS), no asumido. Cuando el slice nuevo reemplace a este, el documento se actualiza entero; sirve además como catálogo de lo que se puede encontrar en una nube privada como la del curso (VNRT): NICs sin usar, restos de instalaciones, configuraciones de prácticas anteriores.

## 1. Acceso

| Puerta | Dirección | Puertos |
|---|---|---|
| Gateway | `10.20.11.147` | SSH puerto 22 |
| controller | vía gateway | 5800 |
| sw1 / sw2 / sw3 | vía gateway | 5801 / 5802 / 5803 |
| h1 / h2 / h3 / h4 | vía gateway | 5811 / 5812 / 5813 / 5814 |

Credenciales: `ubuntu` / `ubuntu` en todas las VMs (también para `sudo`); ONOS: `karaf` / `karaf`; RabbitMQ del corte mínimo: `plataforma` / el secreto del `.env` (en `/tmp/campus/.env` del controller). La red 192.168.0.0/24 es interna del slice: se alcanza desde las VMs; desde la laptop, por túneles SSH.

## 2. Las redes

| Red | Uso (según el LAB5 del curso) | Presente en el slice |
|---|---|---|
| Roja — ACCESS, 192.168.0.0/24 | Gestión: SSH de Ansible y canal OpenFlow (OOB) | ✓ `ens3` de todas las VMs |
| Gris — SDN, 10.0.0.0/24 | Plano de datos: switches OVS y hosts | ✓ `ens4` de h1–h4 y los puertos de los bridges |
| 172.16.0.0/24 | **No documentada en el curso** | ✓ en interfaces sueltas (ver §5) |

## 3. Las VMs

| VM | vCPU | RAM | Disco | Interfaces (MAC) | Rol en la prueba |
|---|---|---|---|---|---|
| controller | 2 | 1.9 GiB | 9.8 G (1.7 G libres) | `ens3` 192.168.0.10 (fa:16:3e:f6:07:ad) · `ens4` 172.16.0.1 (fa:16:3e:2a:ca:75) | ONOS, corte mínimo, consola |
| sw1 | 1 | 961 MiB | 5.9 G (2.4 G libres) | `ens3` 192.168.0.11 · `ens4/5/6` al bridge · interno `sw1` 172.16.0.1 (a2:23:f2:c0:45:47) | raíz del plano de datos |
| sw2 | 1 | 961 MiB | 5.9 G (2.4 G libres) | `ens3` 192.168.0.12 · `ens4/5/6` al bridge · interno `sw2` 172.16.0.2 (1a:74:90:39:89:4a) | acceso de h1 y h2 |
| sw3 | 1 | 961 MiB | 5.9 G (2.4 G libres) | `ens3` 192.168.0.13 · `ens4/5/6` al bridge · interno `sw3` 172.16.0.3 (ca:27:2d:26:57:44) | acceso de h3 y h4 |
| h1 | 1 | 961 MiB | 5.9 G (2.4 G libres) | `ens3` 192.168.0.21 · `ens4` 10.0.0.1 (fa:16:3e:88:05:79) | el usuario que entra |
| h2 | 1 | 961 MiB | 5.9 G (2.4 G libres) | `ens3` 192.168.0.22 · `ens4` 10.0.0.2 (fa:16:3e:a6:2d:a9) | destino de la escalera |
| h3 | 1 | 961 MiB | 5.9 G (2.3 G libres) | `ens3` 192.168.0.23 · `ens4` 10.0.0.3 (fa:16:3e:05:4c:50) | el «Servidor 3»: corre el Portal |
| h4 | 1 | 961 MiB | 5.9 G (2.4 G libres) | `ens3` 192.168.0.24 · `ens4` 10.0.0.4 (fa:16:3e:41:9b:6d) | disponible |

El disco del controller está apretado (1.7 G libres): las capas de Docker de las imágenes que se han ido cargando ocupan la diferencia.

## 4. Enlaces y topología (verificados)

ONOS aprendió los enlaces por LLDP y las ubicaciones de los hosts por ARP:

```text
                 sw1 (raíz)
        sw1:2 ↔ sw2:1        sw1:3 ↔ sw3:3
       /          \          /           \
h1 ── sw2:2   h2 ── sw2:3   h3 ── sw3:2   h4 ── sw3:1
10.0.0.1    10.0.0.2      10.0.0.3     10.0.0.4
```

- Puertos OF de sw2: 1=`ens4` (hacia sw1), 2=`ens5` (h1), 3=`ens6` (h2).
- Puertos OF de sw3: 1=`ens6` (h4), 2=`ens5` (h3), 3=`ens4` (hacia sw1).
- sw1: puerto 1=`ens4` (el cable de datos del controller, ver §7), 2=`ens5` (hacia sw2), 3=`ens6` (hacia sw3).
- El bridge OVS se llama como el switch (`sw1`, `sw2`, `sw3`), `fail_mode: secure`, OpenFlow 1.3, controlador `tcp:192.168.0.10:6653`. Los datapaths: sw1 `0000a223f2c04547`, sw2 `00001a749039894a`, sw3 `0000ca272d265744`.
- El controller está aprendido por ONOS como anfitrión en sw1:1 (su ARP por `ens4` entra al plano de datos).

## 5. Restos y cosas fuera de uso (con cuidado: no borrar sin confirmar)

- **IP duplicada 172.16.0.1**: la tiene el `ens4` del controller y el puerto interno del bridge de sw1. No se ve tráfico que dependa de ninguna de las dos; el LAB5 no documenta la red 172.16.0.0/24 en absoluto. sw2 (172.16.0.2) y sw3 (172.16.0.3) completan el patrón: probablemente un esquema de los JPs para algo que no llegó a usarse.
- **h2 tiene Open vSwitch instalado** con los bridges `sw1` y `sw2` **DOWN** (`ovs-vswitchd` corriendo): restos de una instalación anterior de h2 que ya no se usa. h1, h3 y h4 no tienen OVS.
- **Imagen `ghcr.io/nohafeynman/tel354-onos:2026-2`** en el controller: es la imagen oficial del LAB5 (836 MB, derivada de `onosproject/onos:2.7.0`). El contenedor `onos` que corre usa la oficial; la del curso está descargada pero sin usar.
- **`~/v1.2.zip` en el controller**: fuentes de Floodlight 1.2 (material del LAB4).
- **`docker0` DOWN** en el controller: el bridge de Docker por defecto; los contenedores del corte mínimo viven en `br-9a8e0267c457` (172.18.0.0/16).
- `multipathd` y `unattended-upgrades` en todas las VMs: paquetes normales de Ubuntu, no son restos.
- Los hosts no corren ningún servicio salvo SSH (22) — en el LAB4 h3 era el «Servidor 3» conceptual; no hay servidor real levantado. En esta prueba, el Portal corre en h3 (uvicorn, puerto 8080) por decisión de la prueba.

## 6. Rutas

- **Hosts**: `default via 192.168.0.1 dev ens3` (puerta de enlace de gestión); `10.0.0.0/24 dev ens4`; `192.168.0.0/24 dev ens3`. **No** conocen 172.16.0.0/24 por `ens4` (en la prueba se añadió y se retiró; quedó como estaba).
- **Switches**: solo la subred de gestión por `ens3` y la 172.16.0.0/24 por el puerto interno del bridge.
- **Controller**: `default via 192.168.0.1 dev ens3`; `172.16.0.0/24 dev ens4`; las subredes de Docker (172.17/172.18).

## 7. Comportamiento verificado de la nube privada (VNRT)

Son hechos medidos en este slice y valen para interpretar cualquier falla rara:

1. **ONOS purga los flujos que no instala él.** Una entrada puesta por `ovs-ofctl` vive segundos; todo flujo debe entrar por la API REST de ONOS (así lo hace [`install_skeleton.py`](../../deploy/scripts/install_skeleton.py) y el adaptador).
2. **ONOS sustituye la cookie del JSON** por la suya (derivada del `appId`). El retiro exacto de lo instalado se hace por selectores, no por cookie (verificado en el adaptador).
3. **El cable de datos del controller es asimétrico**: `ens4` del controller ↔ sw1:1 entrega broadcasts (su ARP llega y ONOS lo aprende) pero **no entrega unicast de retorno hacia la MAC de un host** (el SYN-ACK del portal moría en el camino, con capturas simultáneas en ambos extremos). El unicast hacia la MAC interna de un switch sí cruza (ping 3/3). Esto no afecta la arquitectura del curso (el controller nunca es punto final del plano de datos), pero descarta cualquier diseño que lo ponga en banda.
4. **La VNRT filtra MACs no conocidas**: una MAC nueva en h1 ni siquiera entró a la fábrica. Cambios de MAC en los hosts requieren que la red virtual la conozca.
5. El `rx_dropped` de `ens4` del controller descarta la gran mayoría de lo que recibe esa interfaz (conteo del kernel, no de la fábrica): otra señal de que ese enlace no está pensado para tráfico de datos.

## 8. Estado actual de la plataforma en el slice

- **controller**: ONOS 2.7.0 (contenedor `onos`, red host) con apps `hostprovider`, `lldpprovider`, `proxyarp`, `openflow`, `drivers` activas; corte mínimo de 8 contenedores (`mini-rabbitmq`, `mini-iam`, `mini-portal`, `mini-adapter`, `mini-registry`, `mini-console`, `mini-freeradius`, `mini-openldap`) sanos; `.env` en `/tmp/campus/` con los datapaths reales y los secretos de RADIUS/LDAP; `STUB_VERIFY=0` (autenticación real). El Portal (I3) corre en el `mini-portal` del controller (192.168.0.10:8080, gestión) — **no es alcanzable en banda** desde el plano de datos (limitación de la VNRT, §7).
- **h1–h4**: hosts limpios, sin servicios (solo SSH). El portal que corrió en h3 durante la prueba del ciclo completo se retiró; h3 quedó como un host más.
- **sw1/sw2/sw3**: solo las reglas de punteo de ONOS (ARP/LLDP) salvo cuando un manual instala el esqueleto. Las reglas de la plataforma se instalan y se retiran con los manuales de esta carpeta.
