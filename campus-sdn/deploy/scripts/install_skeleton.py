#!/usr/bin/env python3
"""Instala el esqueleto BASE (LLD 06_reglas §3) por la API REST de ONOS.

El switch en fail_mode secure descarta lo que ninguna entrada conoce y
ONOS purga los flujos que no instaló él mismo (verificado en el slice:
una entrada por `ovs-ofctl` vive segundos). El esqueleto entra entonces
por el controlador, como manda el diseño; aquí, en la prueba mínima, por
su API REST con la misma appId del adaptador (org.campus.sdn).

Entradas (la escalera, una por switch):
  150  tráfico al portal / tráfico del portal
  100  denegación a la red de gestión (jamás se abre)
  10   DHCP y DNS

El ARP no lleva entrada: es causa cerrada de PACKET_IN (LLD 06_reglas
§2.1) y lo responde el controlador con la aplicación proxyarp de ONOS
(org.onosproject.proxyarp), que contesta por los anfitriones aprendidos
sin reenviar IP — la escalera sigue mandando sobre el tráfico.

Variables: ONOS_URL, ONOS_USER, ONOS_PASSWORD (por defecto
127.0.0.1:8181, karaf/karaf), SWITCH_DPIDS (JSON {"nombre": "of:…"}) y
SKELETON_PORTAL (CIDR del portal en el plano de datos; por defecto
172.16.0.1/32). Uso:
  SWITCH_DPIDS='{"sw1": "of:…"}' SKELETON_PORTAL=10.0.0.3/32 \
    python3 install_skeleton.py
"""

import base64
import json
import os
import sys
import urllib.request

ONOS_URL = os.environ.get("ONOS_URL", "http://127.0.0.1:8181").rstrip("/")
ONOS_USER = os.environ.get("ONOS_USER", "karaf")
ONOS_PASSWORD = os.environ.get("ONOS_PASSWORD", "karaf")
DPIDS = json.loads(os.environ.get("SWITCH_DPIDS", "{}"))
PORTAL = os.environ.get("SKELETON_PORTAL", "172.16.0.1/32")
MANAGEMENT = "192.168.0.0/24"

CRITERIA = {
    "ip": {"type": "ETH_TYPE", "ethType": "0x0800"},
}
NORMAL = {"instructions": [{"type": "OUTPUT", "port": "NORMAL"}]}
DROP = {"instructions": []}


def _flow(device_id: str, number: int, priority: int, criteria: list,
          treatment: dict, name: str) -> dict:
    return {"priority": priority, "timeout": 0, "isPermanent": True,
            "deviceId": device_id,
            "selector": {"criteria": criteria},
            "treatment": treatment,
            "cookie": 0x0300000000000000 + number}


def _skeleton(device_id: str) -> list[tuple[str, dict]]:
    return [
        ("al portal", _flow(
            device_id, 3, 150,
            [CRITERIA["ip"], {"type": "IPV4_DST", "ip": PORTAL}],
            NORMAL, "to-portal")),
        ("del portal", _flow(
            device_id, 4, 150,
            [CRITERIA["ip"], {"type": "IPV4_SRC", "ip": PORTAL}],
            NORMAL, "from-portal")),
        ("denegación a gestión", _flow(
            device_id, 5, 100,
            [CRITERIA["ip"], {"type": "IPV4_DST", "ip": MANAGEMENT}],
            DROP, "management-drop")),
        ("DHCP", _flow(
            device_id, 6, 10,
            [CRITERIA["ip"], {"type": "IP_PROTO", "protocol": 17},
             {"type": "UDP_DST", "udpPort": 67}],
            NORMAL, "dhcp")),
        ("DNS", _flow(
            device_id, 7, 10,
            [CRITERIA["ip"], {"type": "IP_PROTO", "protocol": 17},
             {"type": "UDP_DST", "udpPort": 53}],
            NORMAL, "dns")),
    ]


def post_flow(device_id: str, flow: dict) -> int:
    token = base64.b64encode(
        f"{ONOS_USER}:{ONOS_PASSWORD}".encode()).decode()
    request = urllib.request.Request(
        f"{ONOS_URL}/onos/v1/flows/{device_id}?appId=org.campus.sdn",
        data=json.dumps(flow).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Basic {token}"},
        method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status


def main() -> int:
    if not DPIDS:
        print("SWITCH_DPIDS sin definir; nada que instalar.", file=sys.stderr)
        return 1
    failures = 0
    for name, device_id in sorted(DPIDS.items()):
        print(f"== {name} ({device_id})")
        for label, flow in _skeleton(device_id):
            try:
                post_flow(device_id, flow)
                print(f"   ok  {label} (prioridad {flow['priority']}, "
                      f"cookie {hex(flow['cookie'])})")
            except urllib.error.HTTPError as error:
                failures += 1
                print(f"   FALLO {label}: HTTP {error.code}")
            except OSError as error:
                failures += 1
                print(f"   FALLO {label}: {error}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
