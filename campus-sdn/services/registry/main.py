"""Registry: dispositivos registrados y su historial (I7).

El registro no concede confianza (regla R-REG-01): registrar un
dispositivo no otorga privilegios por sí mismo. Cada alta o revocación
publica su evento validado. El historial crece además con DeviceConnected
del controlador: ese consumidor llega con el trabajador del bus (paso 5).
"""

import os
from pathlib import Path

from fastapi import HTTPException

from sdn_common.app import create_app
from sdn_common.bus import publish_event
from sdn_common.events import build_event, utc_now, validate_event

SERVICE = "registry"
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "events"

# Prototipo: memoria; la persistencia llega con bd_politicas (paso 5).
devices: dict[str, dict] = {}
history: dict[str, list] = {}

app = create_app(SERVICE)


def _bus_url() -> str:
    return os.environ.get("BUS_URL", "")


def _publish(event) -> None:
    if _bus_url():
        publish_event(_bus_url(), event)


def _record(mac: str, entry: str) -> None:
    history.setdefault(mac, []).append({"entry": entry, "at": utc_now()})


@app.get("/devices")
def list_devices():
    """I7: lista de dispositivos registrados."""
    return {"devices": list(devices.values())}


@app.post("/devices")
def register_device(body: dict):
    """I7: registra un dispositivo; no concede confianza (R-REG-01)."""
    mac = body["mac"]
    device = {
        "mac": mac,
        "owner": body["owner"],
        "role": body["role"],
        "responsible": body["responsible"],
        "validity": body["validity"],
    }
    devices[mac] = device
    _record(mac, "registered")
    event = build_event("DeviceRegistered", device, sender=SERVICE)
    validate_event(event, SCHEMAS_DIR)
    _publish(event)
    return {"status": "registered", "mac": mac}


@app.get("/devices/{mac}/history")
def get_device_history(mac: str):
    """I7: historial de un dispositivo."""
    return {"mac": mac, "history": history.get(mac, [])}


@app.delete("/devices/{mac}")
def revoke_device(mac: str):
    """Revoca un dispositivo; publica DeviceRevoked."""
    device = devices.pop(mac, None)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    _record(mac, "revoked")
    event = build_event("DeviceRevoked", device, sender=SERVICE)
    validate_event(event, SCHEMAS_DIR)
    _publish(event)
    return {"status": "revoked", "mac": mac}
