"""Pruebas de servicio del IAM: tres reinos, sesiones y MAC_Moved.

Modo stub (STUB_VERIFY=1) para la comunidad; el reino operador se prueba
contra el repositorio propio real (bcrypt + TOTP) y el de invitados
contra el registro efímero con TTL. El publicador del bus se sustituye
para capturar los eventos sin RabbitMQ.
"""

import time

import pyotp
import pytest
from fastapi.testclient import TestClient

from services.iam import main as iam_module


@pytest.fixture()
def iam_client(monkeypatch):
    monkeypatch.setenv("STUB_VERIFY", "1")
    monkeypatch.setenv("BUS_URL", "")
    monkeypatch.setenv("I2_URL", "")
    published = []
    monkeypatch.setattr(
        iam_module, "publish_event",
        lambda url, event: published.append((url, event)),
    )
    iam_module.sessions.clear()
    iam_module.operators.clear()
    iam_module.guests.clear()
    iam_module.devices.clear()
    return TestClient(iam_module.app), published


COMMUNITY = {"population": "university", "username": "a12345",
             "password": "x"}


def operator_credentials(username="op-1"):
    secret = pyotp.random_base32()
    iam_module.register_operator(username, "operator-password",
                                 "it_specialist", secret)
    return {"population": "operations", "username": username,
            "password": "operator-password",
            "totp": pyotp.TOTP(secret).now()}


def test_community_issues_session_and_event(iam_client):
    client, published = iam_client
    response = client.post("/verify", json=COMMUNITY)
    assert response.status_code == 200
    body = response.json()
    assert body["profile_or_role"] == "academic"

    event = published[0][1]
    assert event["type"] == "SessionOpened"
    assert event["payload"]["identity"] == "a12345"
    assert "password" not in str(event)


def test_operator_verifies_against_own_repository(iam_client, monkeypatch):
    monkeypatch.setenv("STUB_VERIFY", "0")
    _, _ = iam_client
    credentials = operator_credentials()
    profile = iam_module.verify_credentials(
        "operations", credentials["username"], credentials["password"])
    assert profile == "it_specialist"

    # Contraseña equivocada: rechazo.
    with pytest.raises(Exception):
        iam_module.verify_credentials("operations", credentials["username"],
                                      "wrong-password")

    # El segundo factor se verifica aparte: TOTP ausente o equivocado
    # no emite sesión.
    with pytest.raises(Exception):
        iam_module._verify_operator_totp(credentials["username"], "000000")
    iam_module._verify_operator_totp(credentials["username"],
                                     credentials["totp"])


def test_operator_login_is_two_steps(iam_client, monkeypatch):
    monkeypatch.setenv("STUB_VERIFY", "0")
    client, _ = iam_client
    credentials = operator_credentials()

    # Paso 1: credenciales reconocidas, sin TOTP → se pide el segundo
    # factor; jamás se muestra a quien no pasó las credenciales.
    first = client.post("/verify", json={
        "population": "operations", "username": credentials["username"],
        "password": credentials["password"]})
    assert first.status_code == 200
    assert first.json()["totp_required"] is True
    assert "session" not in first.json()

    bad = client.post("/verify", json={
        "population": "operations", "username": credentials["username"],
        "password": "wrong-password"})
    assert bad.status_code == 401

    # Paso 2: credenciales + TOTP → sesión.
    second = client.post("/verify", json={
        "population": "operations", "username": credentials["username"],
        "password": credentials["password"],
        "totp": credentials["totp"]})
    assert second.status_code == 200
    assert second.json()["profile_or_role"] == "it_specialist"
    assert "session" in second.json()


def test_one_session_per_device(iam_client):
    client, published = iam_client
    first = client.post("/verify", json={
        **COMMUNITY, "device": "52:54:00:01:01"}).json()
    published.clear()
    second = client.post("/verify", json={
        **COMMUNITY, "device": "52:54:00:01:01"}).json()

    # La sesión anterior quedó cerrada (reemplazada); una sola vive.
    assert client.get(f"/sessions/{first['session']}").status_code == 404
    assert client.get(f"/sessions/{second['session']}").status_code == 200
    reasons = [e[1]["payload"]["reason"] for e in published
               if e[1]["type"] == "SessionClosed"]
    assert reasons == ["replaced"]


def test_listings_require_operator_session(iam_client, monkeypatch):
    client, _ = iam_client
    assert client.get("/sessions").status_code == 401

    token = client.post("/verify", json=COMMUNITY).json()["session"]
    assert client.get("/sessions").status_code == 401  # sin cabecera
    assert client.get("/sessions", params={
        "session": token}).status_code == 403  # académico sin rol

    credentials = operator_credentials()
    op_token = client.post("/verify", json={
        "population": "operations", "username": credentials["username"],
        "password": credentials["password"],
        "totp": credentials["totp"]}).json()["session"]
    assert client.get("/operators", params={
        "session": op_token}).status_code == 200
    body = client.get("/sessions", params={
        "session": op_token}).json()
    assert any(s["identity"] == "a12345" for s in body["sessions"])


def test_purge_closes_expired_sessions(iam_client):
    client, published = iam_client
    token = client.post("/verify", json={
        **COMMUNITY, "device": "52:54:00:01:01"}).json()["session"]
    iam_module.sessions[token]["expires_at"] = time.time() - 1
    published.clear()

    iam_module._purge_once()
    assert client.get(f"/sessions/{token}").status_code == 404
    assert published[-1][1]["payload"]["reason"] == "hard-timeout"


def test_login_registers_device_association(iam_client, monkeypatch):
    client, _ = iam_client
    monkeypatch.setenv("REGISTRY_URL", "http://registry:8002")
    seen = []

    class Response:
        status_code = 200

    monkeypatch.setattr("httpx.post",
                        lambda url, **kw: seen.append((url, kw["json"]))
                        or Response())
    client.post("/verify", json={**COMMUNITY, "device": "52:54:00:01:01"})
    assert seen and seen[0][0] == "http://registry:8002/devices"
    assert seen[0][1]["mac"] == "52:54:00:01:01"
    assert seen[0][1]["owner"] == "a12345"
    assert seen[0][1]["role"] == "academic"


def test_guest_register_verify_and_expiry(iam_client, monkeypatch):
    monkeypatch.setenv("STUB_VERIFY", "0")
    _, _ = iam_client
    expires_at = iam_module.register_guest("guest-1", "guest-password")
    assert expires_at > time.time()

    profile = iam_module.verify_credentials("guest", "guest-1",
                                            "guest-password")
    assert profile == "guest"

    # Vencido: se borra solo y rechaza.
    iam_module.guests["guest-1"]["expires_at"] = time.time() - 1
    with pytest.raises(Exception):
        iam_module.verify_credentials("guest", "guest-1", "guest-password")
    assert "guest-1" not in iam_module.guests


def test_guest_register_endpoint(iam_client):
    client, _ = iam_client
    response = client.post("/guest-register",
                           json={"username": "guest-2", "password": "x"})
    assert response.status_code == 200
    assert response.json()["status"] == "registered"


def test_mac_moved_invalidates_session(iam_client):
    client, published = iam_client
    token = client.post("/verify", json={
        **COMMUNITY, "device": "52:54:00:01:01"}).json()["session"]
    published.clear()

    accepted = iam_module.handle_event({
        "type": "MAC_Moved",
        "payload": {"mac": "52:54:00:01:01",
                    "previous_location": {"switch": "A1", "port": "p20"},
                    "new_location": {"switch": "A2", "port": "p4"}},
    })
    assert accepted
    assert client.get(f"/sessions/{token}").status_code == 404
    event = published[0][1]
    assert event["type"] == "SessionClosed"
    assert event["payload"]["reason"] == "mac-moved"


def test_session_has_profile_lifetimes(iam_client):
    client, _ = iam_client
    token = client.post("/verify", json=COMMUNITY).json()["session"]
    session = iam_module.sessions[token]
    assert session["idle_timeout_s"] == 1800   # ACADÉMICO, F-03 §5
    assert session["expires_at"] > session["created_at"]


def test_profile_order_sent_on_login(iam_client, monkeypatch):
    client, _ = iam_client
    orders = []
    monkeypatch.setattr(iam_module, "_send_profile_order",
                        lambda token, mac, profile: orders.append(
                            (token, mac, profile)))
    response = client.post("/verify", json={
        **COMMUNITY, "device": "52:54:00:01:01"})
    token = response.json()["session"]
    assert orders == [(token, "52:54:00:01:01", "academic")]


def test_no_profile_order_without_device(iam_client, monkeypatch):
    client, _ = iam_client
    orders = []
    monkeypatch.setattr(iam_module, "_send_profile_order",
                        lambda token, mac, profile: orders.append(
                            (token, mac, profile)))
    client.post("/verify", json=COMMUNITY)
    assert orders == []


def test_login_includes_network_order_status(iam_client, monkeypatch):
    client, _ = iam_client
    monkeypatch.setattr(iam_module, "_send_profile_order",
                        lambda token, mac, profile: {"status": "applied",
                                                     "rules": ["r1"]})
    body = client.post("/verify", json={
        **COMMUNITY, "device": "52:54:00:01:01"}).json()
    assert body["network"] == {"status": "applied", "rules": ["r1"]}


def test_profile_order_skipped_without_i2(iam_client):
    result = iam_module._send_profile_order("token", "52:54:00:01:01",
                                            "academic")
    assert result == {"status": "skipped", "reason": "I2 not configured"}


def test_profile_order_reports_rejection(iam_client, monkeypatch):
    monkeypatch.setenv("I2_URL", "http://adapter:8090")

    class Response:
        status_code = 404

        def json(self):
            return {"detail": "device not learned"}

    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: Response())
    result = iam_module._send_profile_order("token", "52:54:00:01:01",
                                            "academic")
    assert result == {"status": "rejected", "code": 404,
                      "detail": "device not learned"}


def test_profile_order_carries_session_scope(iam_client, monkeypatch):
    monkeypatch.setenv("I2_URL", "http://adapter:8090")
    seen = []

    class Response:
        status_code = 200

        def json(self):
            return {"rules": ["r1"]}

    monkeypatch.setattr("httpx.post",
                        lambda url, **kwargs: seen.append((url, kwargs["json"]))
                        or Response())
    iam_module._send_profile_order("token", "52:54:00:01:01", "academic")
    order = seen[0][1]
    assert order["scope"] == ["10.0.0.0/24"]    # académico (demo)
    assert order["device"] == {"mac": "52:54:00:01:01"}
    assert order["order"] == "APPLY_PROFILE"

    seen.clear()
    iam_module._send_profile_order("token", "52:54:00:01:01",
                                   "it_specialist")
    assert seen[0][1]["scope"] == []            # operador sin restricción


def test_operator_provisioning_endpoint(iam_client):
    client, _ = iam_client
    response = client.post("/operators", json={
        "username": "op-2", "password": "x",
        "role": "network_admin"})
    assert response.status_code == 200
    assert response.json()["provisioning_uri"].startswith("otpauth://")
    assert iam_module.operators["op-2"]["role"] == "network_admin"
    assert client.post("/operators", json={
        "username": "op-3", "password": "x",
        "role": "academic"}).status_code == 400


def test_logout_withdraws_profile_flow(iam_client, monkeypatch):
    client, _ = iam_client
    withdrawn = []
    monkeypatch.setattr(iam_module, "_send_withdraw_order",
                        lambda token: withdrawn.append(token))
    token = client.post("/verify", json={
        **COMMUNITY, "device": "52:54:00:01:01"}).json()["session"]
    assert client.post("/logout",
                       json={"session": token}).status_code == 200
    assert withdrawn == [token]


def test_logout_closes_and_publishes(iam_client):
    client, published = iam_client
    token = client.post("/verify", json=COMMUNITY).json()["session"]
    published.clear()

    assert client.post("/logout", json={"session": token}).status_code == 200
    event = published[0][1]
    assert event["type"] == "SessionClosed"
    assert event["payload"]["reason"] == "logout"
    assert client.get(f"/sessions/{token}").status_code == 404


def test_admin_revocation_publishes_session_closed(iam_client):
    client, published = iam_client
    token = client.post("/verify", json=COMMUNITY).json()["session"]
    published.clear()

    assert client.delete(f"/sessions/{token}").status_code == 200
    assert published[0][1]["payload"]["reason"] == "admin"


def test_unknown_session_returns_404(iam_client):
    client, _ = iam_client
    assert client.delete("/sessions/no-existe").status_code == 404
    assert client.post("/logout",
                       json={"session": "no-existe"}).status_code == 404


def test_community_requires_radius_in_real_mode(iam_client, monkeypatch):
    client, _ = iam_client
    monkeypatch.setenv("STUB_VERIFY", "0")
    monkeypatch.setenv("RADIUS_HOST", "127.0.0.1")
    response = client.post("/verify", json=COMMUNITY)
    assert response.status_code == 503


def test_reprovision_totp(iam_client):
    client, _ = iam_client
    response = client.post("/devices/52:54:00:01:01/reprovision-totp")
    assert response.status_code == 200
    assert response.json()["provisioning_uri"].startswith("otpauth://")
