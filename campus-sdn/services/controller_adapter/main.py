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
    mitigar cerca del origen). El nombre del switch (llave de
    `SWITCH_DPIDS`) o el propio dpid valen; sin origen identificado, la
    mitigación por destino se aplica en todos los bordes disponibles."""
    dpids = _switch_dpids()
    names = set()
    for origin in order.get("origins", []):
        if origin.get("switch"):
            names.add(origin["switch"])
    if order.get("device", {}).get("switch"):
        names.add(order["device"]["switch"])
    result = []
    for name in sorted(names):
        if name in dpids:
            result.append(dpids[name])
        elif name in dpids.values():
            result.append(name)
    if not result:
        result = _onos().devices()
    if not result:
        raise HTTPException(status_code=400, detail="unknown switch")
    return result


def apply_mitigation(order: dict) -> tuple[list[str], list[str]]:
    incident = order["context"]["incident"]
    cookie = _cookie_hex(INCIDENT_COOKIE_BASE, incident)
    ttl = order["parameters"].get("ttl_s", 300)
    origins = order.get("origins", [])
    if not origins and order["action"] != "RATE_LIMIT":
        # Bloquear sin origen identificado bloquearía todo el borde: se
        # rechaza; la decisión espera un origen real.
        raise HTTPException(status_code=400, detail="origins required")
    device_ids = _switches_for(order)
    rule_ids = []
    selectors = []
    for device_id in device_ids:
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
            "treatment": treatment, "cookie": int(cookie, 16),
        }))
        selectors.append({"priority": 1000, "criteria": criteria})
    return rule_ids, device_ids, selectors


def _normalize_mac(mac: str) -> str:
    """ONOS entrega las MAC en minúsculas y con dos puntos; el formulario
    puede traerlas en mayúsculas o con guiones. La comparación y el flujo
    usan la forma canónica."""
    return mac.strip().lower().replace("-", ":")


def _resolve_location(mac: str) -> dict:
    """Ubicación aprendida del dispositivo (anfitriones del controlador);
    404 si el dispositivo aún no se aprendió."""
    normalized = _normalize_mac(mac)
    for host in _onos().hosts():
        if (host.get("mac", "").lower() == normalized
                and host.get("locations")):
            location = host["locations"][0]
            return {"switch": location.get("elementId"),
                    "port": str(location.get("port"))}
    raise HTTPException(status_code=404, detail="device not learned")


def apply_profile(order: dict) -> tuple[list[str], list[str], list[dict]]:
    """La sesión en el switch, según la escalera (LLD 06_reglas §3):
    ida con el alcance del perfil (fuera de él, el DROP a gestión sigue
    mandando) y vuelta al dispositivo. El ARP no lleva entrada: es causa
    cerrada de PACKET_IN y lo responde el controlador (proxyarp)."""
    key = order["context"]["cookie"]
    cookie = _cookie_hex(SESSION_COOKIE_BASE, key)
    device = order.get("device", {})
    mac = _normalize_mac(device["mac"])
    if device.get("switch") and device.get("port"):
        device_ids = _switches_for(order)
        in_port = device["port"]
    else:
        # El dispositivo se ubica por lo aprendido en el controlador:
        # el solicitante expresa el qué, no el cómo.
        location = _resolve_location(mac)
        device_ids = [location["switch"]]
        in_port = location["port"]
    scopes = order.get("scope") or []
    rule_ids = []
    selectors = []
    for device_id in device_ids:
        outbound = [{"type": "IN_PORT", "port": in_port},
                    {"type": "ETH_SRC", "mac": mac}]
        if scopes:
            outbound += [{"type": "ETH_TYPE", "ethType": "0x0800"},
                         {"type": "IPV4_DST", "ip": scopes[0]}]
        session_flows = [
            {"priority": 200, "timeout": order["validity"]["hard_timeout_s"],
             "idleTimeout": order["validity"]["idle_timeout_s"],
             "isPermanent": False, "deviceId": device_id,
             "selector": {"criteria": outbound},
             "treatment": {"instructions": [
                 {"type": "OUTPUT", "port": "NORMAL"}]},
             "cookie": int(cookie, 16)},
            {"priority": 200, "timeout": order["validity"]["hard_timeout_s"],
             "idleTimeout": order["validity"]["idle_timeout_s"],
             "isPermanent": False, "deviceId": device_id,
             "selector": {"criteria": [
                 {"type": "ETH_DST", "mac": mac}]},
             "treatment": {"instructions": [
                 {"type": "OUTPUT", "port": "NORMAL"}]},
             "cookie": int(cookie, 16)},
        ]
        for flow in session_flows:
            rule_ids.append(_onos().install_flow(device_id, flow))
            selectors.append({"priority": flow["priority"],
                              "criteria": flow["selector"]["criteria"]})
    return rule_ids, device_ids, selectors


def _normalize_criterion(criterion: dict) -> dict:
    """ONOS devuelve los criterios normalizados (puertos como enteros,
    MAC en mayúsculas, etherType sin ceros a la izquierda): ambos lados
    de la comparación pasan por la misma forma."""
    normalized = dict(criterion)
    if "port" in normalized and normalized["port"] is not None:
        normalized["port"] = str(int(normalized["port"]))
    if "mac" in normalized and normalized["mac"] is not None:
        normalized["mac"] = str(normalized["mac"]).lower()
    if "ethType" in normalized and normalized["ethType"] is not None:
        normalized["ethType"] = f"0x{int(str(normalized['ethType']), 16):x}"
    if "ip" in normalized and normalized["ip"] is not None:
        normalized["ip"] = str(normalized["ip"])
    return normalized


def _flow_matches(flow: dict, selector: dict) -> bool:
    """El flujo de ONOS lleva el selector instalado por la orden."""
    if flow.get("priority") != selector["priority"]:
        return False
    criteria = [_normalize_criterion(item)
                for item in flow.get("selector", {}).get("criteria", [])]
    wanted = [_normalize_criterion(item) for item in selector["criteria"]]
    return all(item in criteria for item in wanted)


def withdraw(order: dict) -> int:
    """Retiro de solo lo instalado por la orden, siempre (P10). ONOS
    asigna su propia cookie a los flujos de la app (verificado en el
    slice: la cookie del JSON se sustituye por la del appId), así que el
    registro de la orden guarda los selectores instalados y el retiro
    los busca exactos, por switch. Devuelve cuántos flujos se retiraron.
    Nada ajeno se toca."""
    key = order["context"]["cookie"]
    state = order_registry.get(key, {})
    selectors = state.get("selectors")
    if not selectors:
        raise HTTPException(status_code=404, detail="cookie not found")
    removed = 0
    for device_id in state.get("switches", []):
        for flow in _onos().flows(device_id):
            if any(_flow_matches(flow, selector) for selector in selectors):
                _onos().remove_flow(device_id, flow["id"])
                removed += 1
    return removed


# ---------------------------------------------------------------------------
# I2
# ---------------------------------------------------------------------------

@app.post("/orders")
def submit_order(order: dict):
    """Ejecuta una orden (APPLY_PROFILE, APPLY_MITIGATION, WITHDRAW)."""
    name = order.get("order")
    context = order.get("context", {})
    if name == "WITHDRAW":
        removed = withdraw(order)
        order_registry[context["cookie"]] = {"status": "WITHDRAWN",
                                             "removed": removed}
        return {"status": "WITHDRAWN", "removed": removed}

    if name == "APPLY_MITIGATION":
        rule_ids, switch_ids, selectors = apply_mitigation(order)
        incident = context["incident"]
        order_registry[context["cookie"]] = {"status": "APPLIED",
                                             "switches": switch_ids,
                                             "selectors": selectors}
        _publish(build_event(
            "MitigationApplied",
            {"incident": incident, "rules": rule_ids,
             "switches": switch_ids,
             "applied_at": utc_now()},
            sender=SERVICE,
            correlation={"incident": incident},
        ))
        return {"status": "APPLIED", "rules": rule_ids,
                "confirmed_at": utc_now(), "verification": "PENDING"}

    if name == "APPLY_PROFILE":
        rule_ids, switch_ids, selectors = apply_profile(order)
        order_registry[context["cookie"]] = {"status": "APPLIED",
                                             "switches": switch_ids,
                                             "selectors": selectors}
        return {"status": "APPLIED", "rules": rule_ids,
                "switches": switch_ids, "confirmed_at": utc_now()}

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
