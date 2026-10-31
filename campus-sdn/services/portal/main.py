"""Portal (I3): la única API que hablan las poblaciones.

El selector no concede nada: solo elige la ruta de verificación (LLD
01_apis §5). El portal nunca decide sesiones ni conecta la red: verifica
por el IAM, retira por el IAM y publica la solicitud de elevación al
bus. Las credenciales jamás se registran ni se publican.
"""

import os
from pathlib import Path

import httpx
from fastapi import HTTPException

from sdn_common.app import create_app
from sdn_common.bus import publish_event
from sdn_common.events import build_event, validate_event

SERVICE = "portal"
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "events"
IAM_URL = os.environ.get("IAM_URL", "http://127.0.0.1:8001")
BUS_URL = os.environ.get("BUS_URL", "")

app = create_app(SERVICE)


@app.get("/login")
def login_selector():
    """Selector explícito de población: «Comunidad universitaria»,
    «Personal de operación» e «Invitados» (tres reinos)."""
    return {"populations": ["university", "operations", "guest"]}


@app.post("/login")
def login(credentials: dict):
    """Credenciales (+ TOTP si operación); la sesión la decide el IAM."""
    try:
        response = httpx.post(f"{IAM_URL}/verify", json=credentials, timeout=5)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="identity unavailable")
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return response.json()


@app.post("/logout")
def logout(session: dict):
    """Retiro por cookie y SessionClosed inmediatos: lo ejecuta el IAM."""
    try:
        response = httpx.post(f"{IAM_URL}/logout", json=session, timeout=5)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="identity unavailable")
    return response.json()


@app.post("/guest-register")
def guest_register(body: dict):
    """Autoregistro efímero de invitados: la cuenta se borra sola."""
    try:
        response = httpx.post(f"{IAM_URL}/guest-register", json=body,
                              timeout=5)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="identity unavailable")
    return response.json()


@app.get("/elevation")
def elevation_form():
    """Alcances elevables disponibles para la población autenticada."""
    return {"scopes": ["laboratory"]}


@app.post("/elevation")
def request_elevation(body: dict):
    """Publica ElevationRequested al bus; la decisión es de Políticas."""
    if not BUS_URL:
        raise HTTPException(status_code=503, detail="bus unavailable")
    event = build_event(
        "ElevationRequested",
        {
            "requester": body["requester"],
            "requested_profile": body.get("requested_profile", "laboratory"),
            "scope": body.get("scope", "laboratory"),
            "duration": int(body.get("duration", 1800)),
        },
        sender=SERVICE,
        correlation={"session": body.get("session")} if body.get("session") else None,
    )
    validate_event(event, SCHEMAS_DIR)
    publish_event(BUS_URL, event)
    return {"status": "accepted", "event_id": event["event_id"]}
