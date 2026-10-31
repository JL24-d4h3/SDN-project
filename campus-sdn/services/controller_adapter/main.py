"""Controller adapter: I2 sobre ONOS — órdenes a flujos (LLD 06_reglas §3).

Implementa el contrato I2 (contracts/api/i2-controller.openapi.yaml):
traduce APPLY_PROFILE, APPLY_MITIGATION y WITHDRAW a flujos del plano de
datos vía la API REST de ONOS, con la escalera: mitigación 1000 con
hard_timeout = ttl, sesión 200 con idle y tope, retiro siempre por
cookie. Las cookies siguen la convención del LLD (0x01 sesión, 0x02
incidente). Confirma las mitigaciones con MitigationApplied por el bus.
Sin ONOS alcanzable, las órdenes responden 503 y nada queda a medias.
"""

import json
import os
import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException

from sdn_common.app import create_app
from sdn_common.bus import publish_event
from sdn_common.events import build_event, utc_now, validate_event

SERVICE = "controller_adapter"
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "events"

SESSION_COOKIE_BASE = 0x0100000000000000
INCIDENT_COOKIE_BASE = 0x0200000000000000

cookie_registry: dict[str, str] = {}   # clave → hex del cookie en ONOS
order_registry: dict[str, dict] = {}   # cookie de la orden → estado
services: dict[str, dict] = {}         # inventario de servicios declarados

app = create_app(SERVICE)


def _bus_url() -> str:
    return os.environ.get("BUS_URL", "")


def _switch_dpids() -> dict[str, str]:
    return json.loads(os.environ.get("SWITCH_DPIDS", "{}"))


def _publish(event) -> None:
    validate_event(event, SCHEMAS_DIR)
    publish_event(_bus_url(), event)


def _cookie_hex(base: int, key: str) -> str:
    if key not in cookie_registry:
        cookie_registry[key] = f"0x{base + len(cookie_registry) + 1:016x}"
    return cookie_registry[key]


class OnosClient:
    """Cliente mínimo de la API REST de ONOS."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)

    def _request(self, method: str, path: str, **kwargs):
        try:
            response = httpx.request(method, f"{self.base_url}{path}",
                                     auth=self.auth, timeout=10, **kwargs)
        except httpx.HTTPError:
            raise HTTPException(status_code=503,
                                detail="controller unavailable")
        if response.status_code >= 400:
            raise HTTPException(status_code=503,
                                detail=f"controller error {response.status_code}")
        return response

    def devices(self) -> list[str]:
        data = self._request("GET", "/onos/v1/devices").json()
        return [d["id"] for d in data.get("devices", [])
                if d.get("available")]

    def install_flow(self, device_id: str, flow: dict) -> str:
        self._request("POST", f"/onos/v1/flows/{device_id}?appId=org.campus.sdn",
                      json=flow)
        return f"{device_id}:{flow.get('priority')}:{flow.get('cookie')}"

    def flows(self, device_id: str) -> list[dict]:
        data = self._request("GET", f"/onos/v1/flows/{device_id}").json()
        return data.get("flows", [])

    def remove_flow(self, device_id: str, flow_id: str) -> None:
        self._request("DELETE", f"/onos/v1/flows/{device_id}/{flow_id}")

    def install_meter(self, device_id: str, meter: dict) -> int:
        self._request("POST", f"/onos/v1/meters/{device_id}", json=meter)
        return int(meter.get("meterId", 1))

    def hosts(self) -> list[dict]:
        data = self._request("GET", "/onos/v1/hosts").json()
        return data.get("hosts", [])

    def passthrough(self, path: str) -> dict:
        return self._request("GET", path).json()


def _onos() -> OnosClient:
    return OnosClient(
        os.environ.get("ONOS_URL", "http://127.0.0.1:8181"),
        os.environ.get("ONOS_USER", "karaf"),
        os.environ.get("ONOS_PASSWORD", "karaf"),
    )


def _switches_for(order: dict) -> list[str]:
    """Los dpid de los switches donde vive el origen del tráfico (P9:
    mitigar cerca del origen). Sin origen identificado, la mitigación por
    destino se aplica en todos los bordes disponibles."""
    dpids = _switch_dpids()
    names = set()
    for origin in order.get("origins", []):
        if origin.get("switch"):
            names.add(origin["switch"])
    if order.get("device", {}).get("switch"):
        names.add(order["device"]["switch"])
    result = [dpids[name] for name in sorted(names) if name in dpids]
    if not result:
        result = _onos().devices()
    if not result:
        raise HTTPException(status_code=400, detail="unknown switch")
    return result


def apply_mitigation(order: dict) -> list[str]:
    incident = order["context"]["incident"]
    cookie = _cookie_hex(INCIDENT_COOKIE_BASE, incident)
    ttl = order["parameters"].get("ttl_s", 300)
    origins = order.get("origins", [])
    if not origins and order["action"] != "RATE_LIMIT":
        # Bloquear sin origen identificado bloquearía todo el borde: se
        # rechaza; la decisión espera un origen real.
        raise HTTPException(status_code=400, detail="origins required")
    rule_ids = []
    for device_id in _switches_for(order):
        criteria = []
        if origins:
            criteria += [
                {"type": "IN_PORT", "port": origins[0]["port"]},
                {"type": "ETH_SRC", "mac": origins[0]["mac"]},
            ]
        action = order["action"]
        if action == "RATE_LIMIT":
            criteria.append({"type": "IPV4_DST", "ip": order["target"]["ip"]})
            meter_id = _onos().install_meter(device_id, {
                "deviceId": device_id,
                "meterId": 1,
                "unit": "PKTS_PER_SEC",
                "bands": [{"type": "DROP",
                           "rate": order["parameters"].get("rate_pps", 1000)}],
            })
            treatment = {"instructions": [
                {"type": "METER", "meterId": meter_id},
                {"type": "OUTPUT", "port": "NORMAL"},
            ]}
        else:  # BLOCK_SOURCE, ISOLATE_DEVICE, QUARANTINE
            treatment = {"instructions": [{"type": "DROP"}]}
        rule_ids.append(_onos().install_flow(device_id, {
            "priority": 1000, "timeout": ttl, "isPermanent": False,
            "deviceId": device_id,
            "selector": {"criteria": criteria},
            "treatment": treatment, "cookie": cookie,
        }))
    return rule_ids


def apply_profile(order: dict) -> list[str]:
    key = order["context"]["cookie"]
    cookie = _cookie_hex(SESSION_COOKIE_BASE, key)
    rule_ids = []
    for device_id in _switches_for(order):
        rule_ids.append(_onos().install_flow(device_id, {
            "priority": 200,
            "timeout": order["validity"]["hard_timeout_s"],
            "idleTimeout": order["validity"]["idle_timeout_s"],
            "isPermanent": False,
            "deviceId": device_id,
            "selector": {"criteria": [
                {"type": "IN_PORT", "port": order["device"]["port"]},
                {"type": "ETH_SRC", "mac": order["device"]["mac"]},
            ]},
            "treatment": {"instructions": [{"type": "OUTPUT", "port": "NORMAL"}]},
            "cookie": cookie,
        }))
    return rule_ids


def withdraw(order: dict) -> None:
    """Retiro por cookie, siempre (P10): nada ajeno se toca."""
    key = order["context"]["cookie"]
    cookie = cookie_registry.get(key)
    if not cookie:
        raise HTTPException(status_code=404, detail="cookie not found")
    for device_id in _switch_dpids().values():
        for flow in _onos().flows(device_id):
            if flow.get("cookie") == cookie:
                _onos().remove_flow(device_id, flow["id"])


# ---------------------------------------------------------------------------
# I2
# ---------------------------------------------------------------------------

@app.post("/orders")
def submit_order(order: dict):
    """Ejecuta una orden (APPLY_PROFILE, APPLY_MITIGATION, WITHDRAW)."""
    name = order.get("order")
    context = order.get("context", {})
    if name == "WITHDRAW":
        withdraw(order)
        order_registry[context["cookie"]] = {"status": "WITHDRAWN"}
        return {"status": "WITHDRAWN"}

    if name == "APPLY_MITIGATION":
        rule_ids = apply_mitigation(order)
        incident = context["incident"]
        order_registry[context["cookie"]] = {"status": "APPLIED"}
        _publish(build_event(
            "MitigationApplied",
            {"incident": incident, "rules": rule_ids,
             "switches": list({rid.split(":")[0] for rid in rule_ids}),
             "applied_at": utc_now()},
            sender=SERVICE,
            correlation={"incident": incident},
        ))
        return {"status": "APPLIED", "rules": rule_ids,
                "confirmed_at": utc_now(), "verification": "PENDING"}

    if name == "APPLY_PROFILE":
        rule_ids = apply_profile(order)
        order_registry[context["cookie"]] = {"status": "APPLIED"}
        return {"status": "APPLIED", "rules": rule_ids,
                "confirmed_at": utc_now()}

    raise HTTPException(status_code=400, detail="unknown order")


@app.get("/orders")
def get_order_status(cookie: str):
    """Estado de una orden anterior (idempotencia y reconciliación)."""
    state = order_registry.get(cookie)
    if state is None:
        raise HTTPException(status_code=404, detail="cookie not found")
    return state


@app.get("/associations")
def get_association(ip: str):
    """Asociación vigente MAC ↔ switch:puerto ↔ IP (ligadura de sesión)."""
    for host in _onos().hosts():
        if ip in host.get("ipAddresses", []):
            return {"mac": host.get("mac"), "ip": ip,
                    "switch": host.get("locations", [{}])[0].get("elementId"),
                    "port": host.get("locations", [{}])[0].get("port")}
    raise HTTPException(status_code=404, detail="association not found")


@app.get("/rules")
def get_rules(cookie: str = "", switch: str = ""):
    """Reglas instaladas (reconciliación de incidentes)."""
    dpids = _switch_dpids()
    device_ids = [dpids[switch]] if switch in dpids else list(dpids.values())
    rules = []
    for device_id in device_ids:
        for flow in _onos().flows(device_id):
            if not cookie or flow.get("cookie") == cookie_registry.get(cookie):
                rules.append(flow)
    return {"rules": rules}


@app.get("/topology")
def get_topology():
    return _onos().passthrough("/onos/v1/topology")


@app.get("/counters")
def get_counters():
    return _onos().passthrough("/onos/v1/statistics/ports")


@app.post("/services")
def declare_service(body: dict):
    """Declara un servicio en el inventario (privilegio administrativo)."""
    services[body["name"]] = body
    return {"status": "declared", "name": body["name"]}


@app.get("/services")
def list_services():
    return {"services": list(services.values())}
