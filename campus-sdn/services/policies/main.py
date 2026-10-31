"""Policies: decisiones de mitigación y perfiles.

Consume `IncidentOpened` y decide la mitigación (`MitigationRequired`:
flood → RATE_LIMIT, con ttl — toda mitigación expira sola, P10);
`MitigationVerified` y `MitigationExpired` cierran el seguimiento.
`ElevationRequested` se registra como pendiente: la concesión
(`ElevationGranted`, comando I2) llega con la Consola y su flujo de
aprobación (C4). Perfiles y umbrales se sirven por I7 y viven en memoria
hasta bd_politicas.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from sdn_common.app import create_app
from sdn_common.bus import consume_events, publish_event
from sdn_common.events import build_event, utc_now, validate_event

SERVICE = "policies"
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "events"
QUEUE = "policies"
BINDINGS = ["IncidentOpened", "MitigationVerified", "MitigationExpired",
            "ElevationRequested", "MAC_Moved"]

decisions: dict[str, dict] = {}      # incidente → decisión y resultado
elevations: dict[str, dict] = {}     # pendientes de elevación
profiles: dict = {}                  # I7: perfiles (bd_politicas después)
thresholds: dict = {}                # I7: umbrales


def _bus_url() -> str:
    return os.environ.get("BUS_URL", "")


def _rate_limit_pps() -> int:
    return int(os.environ.get("RATE_LIMIT_PPS", "1000"))


def _mitigation_ttl() -> int:
    return int(os.environ.get("MITIGATION_TTL_S", "300"))


def _publish(event) -> None:
    validate_event(event, SCHEMAS_DIR)
    publish_event(_bus_url(), event)


def _send_order(order: dict) -> None:
    """Envía la orden por I2 (comando síncrono al controlador); el bus
    lleva el eco. Sin I2 configurado, la orden queda en el eco."""
    i2_url = os.environ.get("I2_URL", "")
    if not i2_url:
        return
    import httpx

    httpx.post(f"{i2_url}/orders", json=order, timeout=10)


def handle_event(event: dict) -> bool:
    """Decide o registra; True si se aceptó."""
    event_type = event["type"]
    payload = event["payload"]

    if event_type == "IncidentOpened":
        incident_id = payload["incident"]
        if payload["type"] == "flood":
            action = "RATE_LIMIT"
            parameters = {"rate_pps": _rate_limit_pps(),
                          "ttl_s": _mitigation_ttl()}
        else:
            # Otros tipos esperan su regla (bd_politicas); se registra la
            # decisión pendiente, sin orden al controlador.
            action = None
            parameters = {}
        decisions[incident_id] = {
            "incident": incident_id, "action": action,
            "parameters": parameters, "result": None,
        }
        if action:
            _publish(build_event(
                "MitigationRequired",
                {
                    "incident": incident_id,
                    "action": action,
                    "target": payload["target"],
                    "origins": [],
                    "parameters": parameters,
                    "ttl": parameters["ttl_s"],
                },
                sender=SERVICE,
                correlation={"incident": incident_id},
            ))
            # El comando viaja por I2 (síncrono); el eco ya quedó en el
            # bus. El adaptador confirma con MitigationApplied.
            _send_order({
                "order": "APPLY_MITIGATION",
                "action": action,
                "target": {"type": "service", "ip": payload["target"]},
                "origins": [],
                "parameters": parameters,
                "context": {"cookie": incident_id, "incident": incident_id,
                            "requester": SERVICE, "reason": payload["type"],
                            "approval": None},
            })
        return True

    if event_type == "MitigationVerified":
        incident_id = payload["incident"]
        if incident_id in decisions:
            decisions[incident_id]["result"] = {
                "meets_objective": payload["meets_objective"],
                "at": utc_now(),
            }
        return True

    if event_type == "MitigationExpired":
        incident_id = payload["incident"]
        if incident_id in decisions:
            decisions[incident_id]["result"] = {
                "expired": payload["reason"], "at": utc_now(),
            }
        return True

    if event_type == "ElevationRequested":
        elevations[payload["requester"]] = {
            "requester": payload["requester"],
            "requested_profile": payload["requested_profile"],
            "scope": payload["scope"],
            "duration": payload["duration"],
            "requested_at": utc_now(),
            "state": "pending",
        }
        return True

    if event_type == "MAC_Moved":
        return True

    return False


@asynccontextmanager
async def lifespan(_app):
    if _bus_url():
        import threading

        threading.Thread(
            target=consume_events,
            args=(_bus_url(), QUEUE, BINDINGS, handle_event),
            daemon=True,
        ).start()
    yield


app = create_app(SERVICE, lifespan=lifespan)


@app.get("/elevations")
def list_elevations():
    """I7: elevaciones pendientes e históricas."""
    return {"elevations": list(elevations.values())}


@app.get("/profiles")
def get_profiles():
    """I7: perfiles de red."""
    return {"profiles": profiles}


@app.put("/profiles")
def update_profiles(body: dict):
    """I7: actualiza perfiles; quién lo cambió queda auditado (P12)."""
    profiles.clear()
    profiles.update(body.get("profiles", {}))
    return {"status": "updated", "profiles": profiles}


@app.get("/thresholds")
def get_thresholds():
    """I7: umbrales de detección."""
    return {"thresholds": thresholds}


@app.put("/thresholds")
def update_thresholds(body: dict):
    """I7: actualiza umbrales dentro del rango aprobado (P12, C3)."""
    thresholds.clear()
    thresholds.update(body.get("thresholds", {}))
    return {"status": "updated", "thresholds": thresholds}
