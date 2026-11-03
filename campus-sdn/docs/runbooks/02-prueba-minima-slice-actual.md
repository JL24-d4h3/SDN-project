# Prueba mínima en el slice actual — con controlador y switch

**Proyecto:** Solución de seguridad para una red de campus académico
**Fase:** Implementación — Despliegue
**Estado:** Histórico — la prueba vigente del slice vive en [`docs/pruebas/`](../pruebas/)

---

> El procedimiento vigente para el slice actual está en [`../pruebas/`](../pruebas/): inventario (00), perfil base (01), lista de verificación (02) y tareas del controlador (03). Este runbook documenta el ciclo completo de autenticación que se ejecutó una vez (portal temporal en h3); con el portal de vuelta al controller y los hosts limpios, la autenticación se re-escribirá como manual en esa carpeta.

---

La solución es el controlador y el switch: esta prueba los pone en el centro. En el slice actual ---la VM controlador (10 GB de disco) y `sw1` (OVS ya sondeado)--- se levanta el ciclo completo de autenticación y autorización: el login termina en una **regla OpenFlow real en el switch**, visible con `dump-flows`, y la escalera se demuestra con la denegación a la gestión (prioridad 100) y la sesión (prioridad 200).

**Acceso.** La laptop entra por la puerta de enlace del slice: el controlador es `ssh -p 5800 ubuntu@10.20.11.147`; los switches, puertos 5801/5802/5803; los hosts, 5811–5814 (h1–h4). En la topología actual, h1 y h2 cuelgan de sw2; h3 y h4, de sw3; sw1 es la raíz. La red 192.168.0.0/24 es interna del slice: se alcanza desde las VMs, no desde la laptop; para ver la página cautiva desde el navegador se usa un túnel SSH (sección 4).

**Recursos:** ONOS necesita ~2 GB de RAM en la VM controlador. Si la VM tiene menos, se ejecuta primero la fase de identidad y la fase SDN cuando la memoria alcance. El slice no tiene internet: todo llega como bundles.

## 1. En la laptop

1. Construir las imágenes propias:

   ```bash
   cd campus-sdn && make build
   ```

2. Empaquetar lo que viaja:

   ```bash
   docker save campus-sdn-portal campus-sdn-iam campus-sdn-registry \
     campus-sdn-controller-adapter campus-sdn-console -o /tmp/campus-mini.tar
   ```

   Los bundles de RabbitMQ (`deploy/images/bundles/rabbitmq.tar`) y ONOS (`onos.tar`) ya existen.

## 2. En la VM controlador

1. Arrancar Docker (el inventario lo encontró apagado):

   ```bash
   sudo systemctl start docker && sudo systemctl enable docker
   # silencio = arrancó; se confirma con: sudo systemctl status docker
   ```

2. Copiar y cargar los bundles (desde la laptop):

   ```bash
   scp -P 5800 /tmp/campus-mini.tar deploy/images/bundles/rabbitmq.tar \
       deploy/images/bundles/onos.tar ubuntu@10.20.11.147:/tmp/
   scp -P 5800 deploy/compose/minimal-slice.yml ubuntu@10.20.11.147:/tmp/
   ssh usuario@<ip-controller> 'docker load -i /tmp/campus-mini.tar &&
       docker load -i /tmp/rabbitmq.tar && docker load -i /tmp/onos.tar'
   ```

3. **Levantar ONOS** (un solo nodo; el clúster de tres es para las 14 VMs):

   ```bash
   docker run -d --name onos --network host \
     -e ONOS_APPS=drivers,openflow,hostprovider \
     onosproject/onos:2.7.0
   # esperar ~60 s y verificar:
   curl -u karaf:karaf http://127.0.0.1:8181/onos/v1/devices
   ```

4. **Levantar el resto** (bus, identidad, portal, registro y adaptador):

   ```bash
   mkdir -p /tmp/campus && cd /tmp/campus
   # copiar minimal-slice.yml desde la laptop
   printf 'RABBITMQ_PASSWORD=<secreto>\nSTUB_VERIFY=1\nI2_URL=http://controller_adapter:8090\nSWITCH_DPIDS={"sw1": "of:0000000000000001"}\n' > .env
   docker compose -f minimal-slice.yml up -d
   docker compose -f minimal-slice.yml ps     # los 5 en healthy
   ```

   Ajustar `SWITCH_DPIDS` con los datapaths reales (`ovs-ofctl show swN` en cada switch).

5. **Levantar la consola** (para la demostración de autorización):

   ```bash
   docker run -d --name mini-console --network host \
     -e IAM_URL=http://127.0.0.1:8001 campus-sdn-console
   ```

## 3. Los switches en el centro

Los switches del slice actual se alcanzan por los puertos 5801 (sw1), 5802 (sw2) y 5803 (sw3); los hosts, 5811–5814. La topología real, verificada con el controlador (hosts aprendidos por `hostprovider` y enlaces por LLDP):

```text
h1 10.0.0.1 ── sw2:2           h3 10.0.0.3 ── sw3:2
h2 10.0.0.2 ── sw2:3           h4 10.0.0.4 ── sw3:1
sw1:2 ↔ sw2:1        sw1:3 ↔ sw3:3        sw1 raíz
```

La arquitectura es la del curso (LAB5): red roja de gestión 192.168.0.0/24 (SSH, OpenFlow — el controlador vive solo ahí) y red gris de datos 10.0.0.0/24 (switches y hosts). **El controlador nunca es punto final del plano de datos: los servicios viven en los hosts** (LAB4: H3 es el «Servidor 3»). Por eso esta prueba levanta el portal en h3 y h1 lo alcanza en banda: h1 → sw2 → sw1 → sw3 → h3.

1. **El esqueleto entra por ONOS, jamás por el CLI del switch.** Verificado en el slice: ONOS purga en segundos cualquier flujo que no instaló él. El script [`deploy/scripts/install_skeleton.py`](../../deploy/scripts/install_skeleton.py) instala la escalera BASE (LLD 06_reglas §3) por la API REST de ONOS con la `appId` del adaptador:

   ```bash
   # en el controlador (con el .env del compose)
   scp -P 5800 deploy/scripts/install_skeleton.py ubuntu@10.20.11.147:/tmp/
   ssh -p 5800 ubuntu@10.20.11.147
   sudo mv /tmp/install_skeleton.py /tmp/campus/
   cd /tmp/campus && SWITCH_DPIDS=$(sed -n 's/^SWITCH_DPIDS=//p' .env) \
     SKELETON_PORTAL=10.0.0.3/32 ONOS_URL=http://127.0.0.1:8181 \
     python3 install_skeleton.py
   ```

   Instala por switch: portal (150, a y desde 10.0.0.3), denegación a gestión (100, 192.168.0.0/24), DHCP y DNS (10).

2. **El ARP lo responde el controlador** (causa cerrada de PACKET_IN, LLD 06_reglas §2.1): activar la aplicación `proxyarp` de ONOS, que contesta por los anfitriones aprendidos sin reenviar IP:

   ```bash
   curl -u karaf:karaf -X POST \
     http://127.0.0.1:8181/onos/v1/applications/org.onosproject.proxyarp/active
   ```

3. **El portal en h3** (h3 no tiene Docker ni salida a internet; el runtime viaja como tarballs desde la laptop):

   ```bash
   # laptop: empaquetar el venv del repo y el código del portal
   cd campus-sdn && tar -czf /tmp/portal-venv.tar.gz --exclude='__pycache__' .venv
   tar -czf /tmp/portal-src.tar.gz services/portal services/common contracts/events
   scp -P 5813 /tmp/portal-venv.tar.gz /tmp/portal-src.tar.gz ubuntu@10.20.11.147:/tmp/
   # h3: desempacar y arrancar
   mkdir -p /tmp/campus/portal-run && tar -xzf /tmp/portal-venv.tar.gz -C /tmp/campus/ \
     && mv /tmp/campus/.venv /tmp/campus/portal-venv \
     && tar -xzf /tmp/portal-src.tar.gz -C /tmp/campus/portal-run/
   cd /tmp/campus/portal-run && PYTHONPATH=/tmp/campus/portal-run/services/common:/tmp/campus/portal-run \
     IAM_URL=http://192.168.0.10:8001 I2_URL=http://192.168.0.10:8090 \
     BUS_URL=amqp://plataforma:<secreto>@192.168.0.10:5672 \
     nohup /tmp/campus/portal-venv/bin/python -m uvicorn services.portal.main:app \
     --host 0.0.0.0 --port 8080 > /tmp/campus/portal.log 2>&1 &
   ```

## 4. La cadena completa, visible

1. **El login en banda, sin teclear la MAC.** En h1:

   ```bash
   curl -s -X POST http://10.0.0.3:8080/login \
     -H 'Content-Type: application/json' \
     -d '{"population":"university","username":"a12345","password":"x"}'
   ```

   El portal resuelve el dispositivo desde la fuente de la conexión (IP 10.0.0.1 → asociación que ONOS aprendió del plano de datos) y el IAM ordena el perfil: la respuesta trae `device` (MAC aprendida), `profile_or_role` y `network` (resultado de la orden I2). Con el stub, cualquier usuario/contraseña vale (simula al IdP).

2. **La regla de sesión en el switch del anfitrión** (sw2 para h1):

   ```bash
   sudo ovs-ofctl -O OpenFlow13 dump-flows sw2 | grep 'priority=200'
   ```

   Dos entradas por sesión: ida con el alcance del perfil (`in_port=2, dl_src=h1, nw_dst=10.0.0.0/24` — el académico no abre la gestión) y vuelta (`dl_dst=h1`).

3. **La escalera decide:**

   ```bash
   ping -c 2 -I ens4 10.0.0.2      # pre-login: cae; post-login: pasa por la 200
   ping -c 2 -I ens4 192.168.0.10  # siempre cae: la sesión no abre gestión
   ```

4. **El retiro exacto:** `curl -X POST …/logout` cierra la sesión y el adaptador retira los flujos de la orden por sus selectores (ONOS asigna su propia cookie; el registro de la orden guarda lo instalado) — `dump-flows` los ve desaparecer y el ping vuelve a caer.

### Hallazgos del slice (verificados con capturas)

- **ONOS purga los flujos ajenos**: toda entrada debe entrar por su API REST; la cookie del JSON se sustituye por la del appId — el retiro de la orden se hace por selectores exactos, no por cookie.
- **El enlace de datos del controlador (ens4 ↔ sw1:1) entrega broadcasts pero no unicasts de retorno** hacia la MAC de un host (la VNRT filtra MACs). No afecta esta prueba — el controlador no es punto final del plano de datos — pero limita cualquier diseño que lo ponga en banda: queda pendiente con el panel o los JPs.

## 5. Hoy, por la ruta de gestión

Con el retorno de la VNRT pendiente, la identidad y la autorización se prueban completas por gestión (el login llega por 192.168.0.10, sin plano de datos):

- **Portal** (túnel `ssh -L 8080:192.168.0.10:8080 -p 5800 …` → `http://localhost:8080/`): login de las tres poblaciones. La respuesta declara `device: null` y `network.skipped` (el origen es el túnel: sin asociación en el controlador) — es la limitación declarada, no un fallo.
- **Consola** (túnel 8008 → `http://localhost:8008/`): pegar el token del login — académico 403 (sin P09), operador 200 (con P09). Es la política de autorización decidiendo en vivo.
- **IAM** (8001): `POST /operators` (la URI TOTP se muestra una vez), `GET /sessions/{id}`.

## 6. Después de esta prueba

- Corregir el retorno unicast de la VNRT (regla en su controlador, panel o JPs) y repetir la sección 4 tal cual.
- Apagar `STUB_VERIFY` y apuntar `RADIUS_HOST` al FreeRADIUS: el reino comunidad pasa a RADIUS real.
- El esqueleto manual se sustituye por la aplicación del controlador en el despliegue completo.
- El despliegue de las 14 VMs sigue [`01-despliegue-del-slice.md`](01-despliegue-del-slice.md).
