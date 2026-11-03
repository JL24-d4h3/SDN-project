"""Portal (I3): la única API que hablan las poblaciones.

El selector no concede nada: solo elige la ruta de verificación (LLD
01_apis §5). El portal nunca decide sesiones ni conecta la red: verifica
por el IAM, retira por el IAM y publica la solicitud de elevación al
bus. Las credenciales jamás se registran ni se publican.
"""

import os
from pathlib import Path

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from sdn_common.app import create_app
from sdn_common.bus import publish_event
from sdn_common.events import build_event, validate_event

SERVICE = "portal"
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "events"
IAM_URL = os.environ.get("IAM_URL", "http://127.0.0.1:8001")
BUS_URL = os.environ.get("BUS_URL", "")
I2_URL = os.environ.get("I2_URL", "")

app = create_app(SERVICE)

UI_HTML = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Portal cautivo — campus-sdn</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:system-ui;max-width:34rem;margin:2rem auto;padding:0 1rem;
     background:#f4f4f5;color:#18181b}
h1{font-size:1.3rem}
.card{background:#fff;padding:1.2rem;border-radius:8px;margin-bottom:1rem}
label{display:block;margin:.6rem 0 .2rem;font-size:.9rem}
input,select{width:100%;padding:.5rem;box-sizing:border-box}
.hint{font-size:.8rem;color:#52525b;margin:.2rem 0 0}
button{margin-top:.8rem;padding:.55rem 1.1rem;cursor:pointer}
#result{white-space:pre-wrap;background:#18181b;color:#d4d4d8;
        padding:.8rem;border-radius:8px;font-size:.85rem;min-height:2rem}
</style>
</head>
<body>
<h1>Portal cautivo</h1>

<div class="card">
<h2>Entrar</h2>
<form id="login">
<label>Población</label>
<select name="population">
  <option value="university">Comunidad universitaria</option>
  <option value="operations">Personal de operación</option>
  <option value="guest">Invitado</option>
</select>
<label>Usuario</label><input name="username" autocomplete="username">
<label>Contraseña</label><input name="password" type="password"
                                   autocomplete="current-password">
<div id="totp-row" style="display:none">
<label>TOTP (operación)</label><input name="totp">
<p class="hint" id="totp-msg">Credenciales reconocidas — ingresa el código
TOTP para continuar.</p>
</div>
<button type="submit">Entrar</button>
</form>
</div>

<div class="card">
<h2>Invitado</h2>
<form id="guest">
<label>Usuario</label><input name="username">
<label>Contraseña</label><input name="password" type="password">
<button type="submit">Registrarse (cuenta efímera, TTL 24 h)</button>
</form>
</div>

<div class="card">
<h2>Elevación</h2>
<form id="elevation">
<label>Solicitante</label><input name="requester">
<label>Alcance</label><input name="scope" value="laboratory">
<label>Duración (s)</label><input name="duration" type="number" value="1800">
<button type="submit">Solicitar elevación</button>
</form>
</div>

<div class="card">
<button id="logout">Cerrar sesión</button>
</div>

<pre id="result"></pre>

<script>
const result = document.getElementById('result');
const show = (obj) => { result.textContent = JSON.stringify(obj, null, 2); };
const post = async (path, body) => {
  const response = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  });
  show({status: response.status, body: await response.json()});
};
document.getElementById('login').onsubmit = async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  const body = {population: f.get('population'), username: f.get('username'),
                password: f.get('password')};
  const totpRow = document.getElementById('totp-row');
  if (totpRow.style.display !== 'none') {
    // segundo paso: las credenciales ya fueron reconocidas
    body.totp = f.get('totp');
  }
  const response = await fetch('/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  });
  const data = await response.json();
  show({status: response.status, body: data});
  if (response.status === 200 && data.totp_required) {
    // solo quien ya pasó las credenciales ve el campo del segundo factor
    totpRow.style.display = 'block';
  }
};
document.getElementById('guest').onsubmit = (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  post('/guest-register', {username: f.get('username'),
                           password: f.get('password')});
};
document.getElementById('elevation').onsubmit = (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  post('/elevation', {requester: f.get('requester'),
                      scope: f.get('scope'),
                      duration: parseInt(f.get('duration'))});
};
document.getElementById('logout').onclick = () => {
  const session = prompt('Token de sesión');
  if (session) post('/logout', {session});
};
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def ui():
    """La página cautiva: formularios que llaman a esta misma API."""
    return UI_HTML


@app.get("/login")
def login_selector():
    """Selector explícito de población: «Comunidad universitaria»,
    «Personal de operación» e «Invitados» (tres reinos)."""
    return {"populations": ["university", "operations", "guest"]}


def _resolve_device(client_ip: str) -> dict | None:
    """El dispositivo lo conoce la red, no el usuario: la fuente de la
    conexión (IP) se traduce a la asociación MAC↔ubicación que el
    controlador aprendió del plano de datos (I2 /associations). Sin
    adaptador, sin asociación o tras un túnel (origen local), no hay
    dispositivo y el login sigue (sesión sin regla, declarado)."""
    if not client_ip or client_ip in ("127.0.0.1", "localhost", "::1"):
        return None
    if not I2_URL:
        return None
    try:
        response = httpx.get(f"{I2_URL}/associations",
                             params={"ip": client_ip}, timeout=5)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    return response.json()


@app.post("/login")
def login(credentials: dict, request: Request):
    """Credenciales (+ TOTP si operación); la sesión la decide el IAM.
    El dispositivo lo aporta la red: la MAC de la fuente de la conexión,
    resuelta por el controlador — jamás tecleada por el usuario."""
    body = dict(credentials)
    device = _resolve_device(request.client.host)
    if device:
        body["device"] = device["mac"]
    try:
        response = httpx.post(f"{IAM_URL}/verify", json=body, timeout=5)
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
