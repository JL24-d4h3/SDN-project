"""Console: alertas en vivo y agregación de las I7.

Consume las alertas del bus (`AnomalyDetected`, `IncidentOpened`,
`DeviceRegistered`, `DeviceRevoked`) y las sirve a la interfaz del
operador. La sesión del operador es el SSO (F-03 §4): con IAM_URL
configurado, cada petición valida su sesión contra el IAM; sin él, el
prototipo opera sin SSO (limitación declarada).
"""

import os
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import Depends, Header, HTTPException

from sdn_common.app import create_app
from sdn_common.bus import consume_events

SERVICE = "console"
QUEUE = "console"
BINDINGS = ["AnomalyDetected", "IncidentOpened", "DeviceRegistered",
            "DeviceRevoked"]

alerts = deque(maxlen=200)


def _bus_url() -> str:
    return os.environ.get("BUS_URL", "")


def _iam_url() -> str:
    return os.environ.get("IAM_URL", "")


def handle_event(event: dict) -> bool:
    if event["type"] in BINDINGS:
        alerts.appendleft(event)
        return True
    return False


def require_session(session: str = Header(default="", alias="X-Session")):
    """Valida la sesión contra el IAM; sin IAM_URL, modo prototipo."""
    iam_url = _iam_url()
    if not iam_url:
        return None
    if not session:
        raise HTTPException(status_code=401, detail="session required")
    try:
        response = httpx.get(f"{iam_url}/sessions/{session}", timeout=5)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="identity unavailable")
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="session expired")
    return session


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


@app.get("/alerts")
def get_alerts(_=Depends(require_session)):
    """Alertas en vivo para la interfaz del operador."""
    return {"alerts": list(alerts)}
