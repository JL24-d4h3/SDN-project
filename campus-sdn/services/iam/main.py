"""IAM: tres reinos de identidad, sesiones y SSO (F-03, componentes/04).

Reinos:
- comunidad universitaria → IdP institucional, por I4: el IAM es cliente
  RADIUS (Access-Request + accounting); el prototipo simula al IdP con
  FreeRADIUS/LDAP, no al protocolo (F-03 §2).
- operadores (TI, Admin, SA) → repositorio propio I6: credenciales
  bcrypt (jamás en claro) y TOTP obligatorio (F-03 §3).
- invitados → registro efímero: autoregistro con TTL corto que se borra
  solo; fuera de alcance, pero el lugar queda reservado
  (componentes/04 §2.3).

La sesión es un identificador opaco con vigencia por perfil (F-03 §5) y
se invalida si el dispositivo se mueve (MAC_Moved, cola iam). Las
credenciales jamás se registran ni se publican.
"""

import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import bcrypt
import pyotp
from fastapi import HTTPException

from sdn_common.app import create_app
from sdn_common.bus import consume_events, publish_event
from sdn_common.events import build_event, utc_now, validate_event

SERVICE = "iam"
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "events"
QUEUE = "iam"
BINDINGS = ["MAC_Moved"]

# Prototipo: los repositorios viven en memoria; la persistencia llega
# con bd_politicas (paso 5).
sessions: dict[str, dict] = {}
operators: dict[str, dict] = {}    # username → {password_hash, totp_secret, role}
guests: dict[str, dict] = {}       # username → {password_hash, expires_at}
devices: dict[str, dict] = {}      # mac → {totp_secret}

# F-03 §5: vigencia por perfil (idle_timeout y tope absoluto).
PROFILE_SESSION = {
    "academic": {"idle_timeout_s": 1800, "hard_timeout_s": 43200},
    "it_specialist": {"idle_timeout_s": 900, "hard_timeout_s": 28800},
    "network_admin": {"idle_timeout_s": 900, "hard_timeout_s": 28800},
    "super_admin": {"idle_timeout_s": 900, "hard_timeout_s": 28800},
    # Invitados: fuera de alcance; tope de 24 h alineado con su TTL.
    "guest": {"idle_timeout_s": 900, "hard_timeout_s": 86400},
}

# Alcance de red por perfil (LLD 06_reglas §3: la regla de sesión
# autoriza el dispositivo → alcance del perfil; fuera de él, el DROP a
# gestión de la escalera sigue mandando). El alcance real lo decide el
# motor de política (bd_politicas); aquí, el valor del demo: la red de
# datos del slice. Los operadores no llevan restricción de destino.
SESSION_SCOPE = {
    "academic": ["10.0.0.0/24"],
    "guest": ["10.0.0.0/24"],
    "it_specialist": [],
    "network_admin": [],
    "super_admin": [],
}

@asynccontextmanager
async def lifespan(_app):
    if _bus_url():
        threading.Thread(
            target=consume_events,
            args=(_bus_url(), QUEUE, BINDINGS, handle_event),
            daemon=True,
        ).start()
        threading.Thread(target=purge_loop, daemon=True).start()
    yield


app = create_app(SERVICE, lifespan=lifespan)


def _bus_url() -> str:
    return os.environ.get("BUS_URL", "")


def _i2_url() -> str:
    return os.environ.get("I2_URL", "")


def _send_profile_order(session_token: str, device_mac: str,
                        profile: str) -> dict:
    """Ordena el perfil al controlador (I2) al emitir la sesión. Devuelve
    el resultado de la orden para que el login lo muestre: un login sin
    red es un login a medias y debe verse. Sin I2 configurado o sin
    dispositivo, la orden no sale (limitación declarada: el plano de
    datos no se entera del login)."""
    i2_url = _i2_url()
    if not i2_url:
        return {"status": "skipped", "reason": "I2 not configured"}
    if not device_mac:
        return {"status": "skipped", "reason": "no device"}
    import httpx

    params = PROFILE_SESSION[profile]
    order = {
        "order": "APPLY_PROFILE",
        "device": {"mac": device_mac},
        "scope": SESSION_SCOPE.get(profile, []),
        "validity": {"idle_timeout_s": params["idle_timeout_s"],
                     "hard_timeout_s": params["hard_timeout_s"]},
        "context": {"cookie": session_token, "requester": SERVICE,
                    "reason": "login"},
        "profile": profile,
    }
    try:
        response = httpx.post(f"{i2_url}/orders", json=order, timeout=10)
    except httpx.HTTPError:
        # El login no depende del controlador: la sesión nace y el
        # resultado lo declara (degradación, no fallo del login).
        return {"status": "unreachable", "reason": "controller unavailable"}
    try:
        body = response.json()
    except ValueError:
        body = {}
    if response.status_code >= 400:
        return {"status": "rejected", "code": response.status_code,
                "detail": body.get("detail", "")}
    return {"status": "applied", "rules": body.get("rules", [])}


def _send_withdraw_order(session_token: str) -> dict:
    """Retira la regla de sesión por cookie (I2) al cerrar la sesión.
    Sin I2 configurado no hay nada que retirar; el resultado se declara
    para que el logout lo muestre."""
    i2_url = _i2_url()
    if not i2_url:
        return {"status": "skipped", "reason": "I2 not configured"}
    import httpx

    order = {
        "order": "WITHDRAW",
        "context": {"cookie": session_token, "requester": SERVICE,
                    "reason": "logout"},
    }
    try:
        response = httpx.post(f"{i2_url}/orders", json=order, timeout=10)
    except httpx.HTTPError:
        return {"status": "unreachable", "reason": "controller unavailable"}
    if response.status_code >= 400:
        return {"status": "rejected", "code": response.status_code}
    return {"status": "withdrawn"}


def _stub_verify() -> bool:
    return os.environ.get("STUB_VERIFY", "") == "1"


def _registry_url() -> str:
    return os.environ.get("REGISTRY_URL", "")


def _guest_ttl() -> int:
    return int(os.environ.get("GUEST_TTL_S", "86400"))


def _publish(event) -> None:
    validate_event(event, SCHEMAS_DIR)
    publish_event(_bus_url(), event)


def _check_totp(secret: str, totp: str) -> bool:
    return pyotp.TOTP(secret).verify(totp)


# ---------------------------------------------------------------------------
# Aprovisionamiento (la cadena SA→Admin→TI lo invoca con rol autorizado)
# ---------------------------------------------------------------------------

def register_operator(username: str, password: str, role: str,
                      totp_secret: str | None = None) -> str:
    """Crea una credencial de operador (bcrypt + TOTP). Devuelve la URI
    de aprovisionamiento: se muestra UNA vez, como QR (F-03 §3.1)."""
    secret = totp_secret or pyotp.random_base32()
    operators[username] = {
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()),
        "totp_secret": secret,
        "role": role,
    }
    return pyotp.TOTP(secret).provisioning_uri(name=username,
                                               issuer_name="campus-sdn")


def register_guest(username: str, password: str) -> str:
    """Autoregistro efímero: la cuenta se borra sola al vencer el TTL."""
    guests[username] = {
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()),
        "expires_at": time.time() + _guest_ttl(),
    }
    return guests[username]["expires_at"]


# ---------------------------------------------------------------------------
# Verificación por reino
# ---------------------------------------------------------------------------

def _verify_community(username: str, password: str) -> str:
    """Reino comunidad: RADIUS contra el IdP (F-03 §2)."""
    try:
        import pyrad.client
        import pyrad.dictionary
        import pyrad.packet

        host = os.environ.get("RADIUS_HOST", "")
        secret = os.environ.get("RADIUS_SECRET", "")
        # pyrad 2.4 no incluye su diccionario en el paquete pip: se usa
        # el que acompaña al servicio (services/iam/dictionary).
        dictionary = pyrad.dictionary.Dictionary(
            str(Path(__file__).parent / "dictionary"))
        client = pyrad.client.Client(server=host, secret=secret.encode(),
                                     dict=dictionary)
        request = client.CreateAuthPacket(code=pyrad.packet.AccessRequest,
                                          User_Name=username,
                                          message_authenticator=True)
        request["User-Password"] = request.PwCrypt(password)
        reply = client.SendPacket(request)
        if reply.code != pyrad.packet.AccessAccept:
            raise HTTPException(status_code=401, detail="invalid credentials")

        # Accounting (R1.9): Start al abrir la sesión; el Interim y el
        # Stop acompañan el ciclo en la sesión.
        acct = client.CreateAcctPacket(User_Name=username,
                                       Acct_Session_Id=str(uuid.uuid4()),
                                       message_authenticator=True)
        acct["Acct-Status-Type"] = "Start"
        client.SendPacket(acct)
        return "academic"
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="radius unavailable")


def _verify_operator_password(username: str, password: str) -> str:
    """Primer paso del reino operador: solo las credenciales (F-03 §3).
    El TOTP se pide después, cuando el sistema ya reconoció al usuario —
    jamás antes (el formulario no muestra el campo a desconocidos)."""
    operator = operators.get(username)
    if operator is None or not bcrypt.checkpw(password.encode(),
                                              operator["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return operator["role"]


def _verify_operator_totp(username: str, totp: str) -> None:
    if not _check_totp(operators[username]["totp_secret"], totp):
        raise HTTPException(status_code=401, detail="totp required")


def _verify_guest(username: str, password: str) -> str:
    """Reino invitados: registro efímero con TTL (componentes/04 §2.3)."""
    guest = guests.get(username)
    if guest is None:
        raise HTTPException(status_code=401, detail="invalid credentials")
    if time.time() > guest["expires_at"]:
        del guests[username]  # se borra solo al vencer
        raise HTTPException(status_code=401, detail="guest expired")
    if not bcrypt.checkpw(password.encode(), guest["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return "guest"


def verify_credentials(population: str, username: str, password: str) -> str:
    """Primer paso de la verificación: credenciales solas. Para el reino
    de operadores devuelve el rol (el TOTP se exige en el segundo paso);
    401 si no verifica."""
    if _stub_verify():
        # Modo de pruebas: acepta cualquier par. Jamás activar con el
        # slice real.
        return {"university": "academic", "operations": "it_specialist",
                "guest": "guest"}[population]
    if population == "university":
        return _verify_community(username, password)
    if population == "operations":
        return _verify_operator_password(username, password)
    if population == "guest":
        return _verify_guest(username, password)
    raise HTTPException(status_code=401, detail="unknown population")


# ---------------------------------------------------------------------------
# Sesiones
# ---------------------------------------------------------------------------

def _issue_session(username: str, profile: str, device: str) -> str:
    params = PROFILE_SESSION[profile]
    token = str(uuid.uuid4())
    now = time.time()
    sessions[token] = {
        "identity": username,
        "profile_or_role": profile,
        "device": device,
        "created_at": now,
        "last_seen": now,
        "expires_at": now + params["hard_timeout_s"],
        "idle_timeout_s": params["idle_timeout_s"],
    }
    _publish(build_event(
        "SessionOpened",
        {"identity": username, "profile_or_role": profile,
         "device": device, "timestamp": utc_now()},
        sender=SERVICE,
        correlation={"session": token},
    ))
    return token


def _close_session(token: str, reason: str) -> dict:
    session = sessions.pop(token, None)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    network = (_send_withdraw_order(token) if session.get("device")
               else {"status": "skipped", "reason": "no device"})
    _publish(build_event(
        "SessionClosed",
        {"identity": session["identity"],
         "profile_or_role": session["profile_or_role"],
         "device": session["device"], "reason": reason},
        sender=SERVICE,
        correlation={"session": token},
    ))
    return {**session, "network": network}


def _valid_session(token: str) -> dict:
    """Sesión vigente tras aplicar tope e idle (F-03 §5)."""
    session = sessions.get(token)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    now = time.time()
    if now > session["expires_at"]:
        _close_session(token, "hard-timeout")
        raise HTTPException(status_code=404, detail="session not found")
    if now - session["last_seen"] > session["idle_timeout_s"]:
        _close_session(token, "idle-timeout")
        raise HTTPException(status_code=404, detail="session not found")
    session["last_seen"] = now
    return session


def handle_event(event: dict) -> bool:
    """Cola iam: un MAC_Moved del dispositivo invalida su sesión."""
    if event["type"] != "MAC_Moved":
        return False
    mac = event["payload"]["mac"]
    for token, session in list(sessions.items()):
        if session["device"] == mac:
            _close_session(token, "mac-moved")
    return True


def _purge_once() -> None:
    """Una pasada del barrido: invitados vencidos y sesiones pasadas de
    tope. Las reglas de red de esas sesiones ya expiraron solas en el
    switch (hard_timeout); el retiro de la orden declara lo que queda."""
    now = time.time()
    for username in [u for u, g in guests.items()
                     if g["expires_at"] < now]:
        del guests[username]
    for token in [t for t, s in sessions.items()
                  if s["expires_at"] < now]:
        _close_session(token, "hard-timeout")


def purge_loop() -> None:
    while True:
        time.sleep(60)
        _purge_once()


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.post("/verify")
def verify(credentials: dict):
    """Verifica credenciales y emite la sesión (lo llama el Portal).
    Operadores: dos pasos — primero credenciales, luego TOTP; el campo
    solo se muestra cuando el sistema ya reconoció al usuario."""
    population = credentials.get("population", "university")
    username = credentials["username"]
    password = credentials["password"]
    profile = verify_credentials(population, username, password)
    if population == "operations" and not credentials.get("totp"):
        if not _stub_verify():
            # Credenciales reconocidas: ahora sí, el segundo factor.
            return {"totp_required": True, "username": username,
                    "profile_or_role": profile}
    if population == "operations" and not _stub_verify():
        _verify_operator_totp(username, credentials.get("totp", ""))
    device_mac = credentials.get("device", "")
    # Una sola sesión por dispositivo: la nueva reemplaza a la anterior
    # (la red admite al usuario, no duplica su presencia).
    for token in [t for t, s in sessions.items()
                  if s.get("device") == device_mac and device_mac]:
        _close_session(token, "replaced")
    token = _issue_session(username, profile, device_mac)
    if device_mac and _registry_url():
        _associate_device(device_mac, username, profile)
    network = (_send_profile_order(token, device_mac, profile)
               if device_mac else {"status": "skipped",
                                   "reason": "no device"})
    return {"session": token, "profile_or_role": profile,
            "device": device_mac or None, "network": network}


def _associate_device(device_mac: str, username: str, profile: str) -> None:
    """El dispositivo de la sesión queda registrado en el Registry
    (no concede confianza por sí mismo; es la asociación observable)."""
    import httpx

    try:
        httpx.post(f"{_registry_url()}/devices", json={
            "mac": device_mac, "owner": username, "role": profile,
            "responsible": SERVICE, "validity": "session"},
            timeout=5)
    except httpx.HTTPError:
        # La sesión no depende del registro (degradación declarada).
        return


@app.post("/logout")
def logout(body: dict):
    """Retiro por cookie y SessionClosed inmediatos (lo llama el Portal)."""
    session = _close_session(body["session"], "logout")
    return {"status": "closed", "network": session["network"]}


@app.post("/operators")
def provision_operator(body: dict):
    """Aprovisiona un operador (cadena SA→Admin→TI, P24/P14): la URI del
    secreto TOTP se muestra UNA vez (F-03 §3.1)."""
    role = body.get("role", "it_specialist")
    if role not in ("it_specialist", "network_admin", "super_admin"):
        raise HTTPException(status_code=400, detail="invalid role")
    provisioning_uri = register_operator(
        body["username"], body["password"], role)
    return {"status": "registered", "provisioning_uri": provisioning_uri}


@app.post("/guest-register")
def guest_register(body: dict):
    """Autoregistro efímero (componentes/04 §2.3): la cuenta se borra
    sola al vencer el TTL."""
    expires_at = register_guest(body["username"], body["password"])
    return {"status": "registered", "expires_at": expires_at}


@app.get("/sessions/{id}")
def get_session(id: str):
    """I7: consulta de una sesión; aplica tope e idle (rol mínimo: TI)."""
    session = _valid_session(id)
    return {"session": id, **session}


def _require_operator(session: str) -> dict:
    """Las rutas de revisión exigen una sesión de operador vigente."""
    if not session:
        raise HTTPException(status_code=401, detail="session required")
    try:
        record = _valid_session(session)
    except HTTPException:
        raise HTTPException(status_code=401, detail="session not found")
    if record["profile_or_role"] not in ("it_specialist", "network_admin",
                                         "super_admin"):
        raise HTTPException(status_code=403, detail="insufficient role")
    return record


@app.get("/operators")
def list_operators(session: str = ""):
    """I7: operadores registrados (sin secretos ni hashes)."""
    _require_operator(session)
    return {"operators": [
        {"username": name, "role": data["role"]}
        for name, data in sorted(operators.items())]}


@app.get("/guests")
def list_guests(session: str = ""):
    """I7: invitados efímeros registrados (sin hashes)."""
    _require_operator(session)
    return {"guests": [
        {"username": name, "expires_at": data["expires_at"]}
        for name, data in sorted(guests.items())]}


@app.get("/sessions")
def list_sessions(session: str = ""):
    """I7: sesiones vigentes (aplica topes e idle)."""
    _require_operator(session)
    return {"sessions": [
        {"session": token, "identity": s["identity"],
         "profile_or_role": s["profile_or_role"], "device": s["device"],
         "created_at": s["created_at"], "expires_at": s["expires_at"]}
        for token, s in list(sessions.items())]}


@app.delete("/sessions/{id}")
def revoke_session(id: str):
    """I7: logout administrativo (rol mínimo: TI)."""
    _close_session(id, "admin")
    return {"status": "revoked"}


@app.post("/devices/{mac}/reprovision-totp")
def reprovision_totp(mac: str):
    """I7: reaprovisiona el TOTP de un dispositivo (rol mínimo: TI)."""
    secret = pyotp.random_base32()
    devices[mac] = {"totp_secret": secret}
    provisioning_uri = pyotp.TOTP(secret).provisioning_uri(
        name=mac, issuer_name="campus-sdn")
    return {"mac": mac, "provisioning_uri": provisioning_uri}
