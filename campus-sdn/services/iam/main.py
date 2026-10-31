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


def _stub_verify() -> bool:
    return os.environ.get("STUB_VERIFY", "") == "1"


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
        dictionary = pyrad.dictionary.Dictionary(
            os.path.join(os.path.dirname(pyrad.__file__), "dictionary"))
        client = pyrad.client.Client(server=host, secret=secret.encode(),
                                     dict=dictionary)
        request = client.CreateAuthPacket(code=pyrad.packet.AccessRequest,
                                          User_Name=username)
        request["User-Password"] = request.PwCrypt(password)
        reply = client.SendPacket(request)
        if reply.code != pyrad.packet.AccessAccept:
            raise HTTPException(status_code=401, detail="invalid credentials")

        # Accounting (R1.9): Start al abrir la sesión; el Interim y el
        # Stop acompañan el ciclo en la sesión.
        acct = client.CreateAcctPacket(User_Name=username,
                                       Acct_Session_Id=str(uuid.uuid4()))
        acct["Acct-Status-Type"] = "Start"
        client.SendPacket(acct)
        return "academic"
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="radius unavailable")


def _verify_operator(username: str, password: str, totp: str | None) -> str:
    """Reino operadores: repositorio propio, bcrypt + TOTP (F-03 §3)."""
    operator = operators.get(username)
    if operator is None or not bcrypt.checkpw(password.encode(),
                                              operator["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid credentials")
    if not totp or not _check_totp(operator["totp_secret"], totp):
        raise HTTPException(status_code=401, detail="totp required")
    return operator["role"]


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


def verify_credentials(population: str, username: str, password: str,
                       totp: str | None = None) -> str:
    """Devuelve el profile_or_role concedido; 401 si no verifica."""
    if _stub_verify():
        # Modo de pruebas: acepta cualquier par. Jamás activar con el
        # slice real.
        return {"university": "academic", "operations": "it_specialist",
                "guest": "guest"}[population]
    if population == "university":
        return _verify_community(username, password)
    if population == "operations":
        return _verify_operator(username, password, totp)
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
    _publish(build_event(
        "SessionClosed",
        {"identity": session["identity"],
         "profile_or_role": session["profile_or_role"],
         "device": session["device"], "reason": reason},
        sender=SERVICE,
        correlation={"session": token},
    ))
    return session


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


def purge_loop() -> None:
    """Los invitados vencidos se borran solos (TTL)."""
    while True:
        time.sleep(60)
        now = time.time()
        for username in [u for u, g in guests.items()
                         if g["expires_at"] < now]:
            del guests[username]


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.post("/verify")
def verify(credentials: dict):
    """Verifica credenciales y emite la sesión (lo llama el Portal)."""
    population = credentials.get("population", "university")
    username = credentials["username"]
    password = credentials["password"]
    profile = verify_credentials(population, username, password,
                                 credentials.get("totp"))
    token = _issue_session(username, profile, credentials.get("device", ""))
    return {"session": token, "profile_or_role": profile}


@app.post("/logout")
def logout(body: dict):
    """Retiro por cookie y SessionClosed inmediatos (lo llama el Portal)."""
    _close_session(body["session"], "logout")
    return {"status": "closed"}


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
