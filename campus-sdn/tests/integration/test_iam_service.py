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
        "operations", credentials["username"], credentials["password"],
        totp=credentials["totp"])
    assert profile == "it_specialist"

    # Contraseña equivocada y TOTP ausente: rechazo.
    with pytest.raises(Exception):
        iam_module.verify_credentials("operations", credentials["username"],
                                      "wrong-password")
    with pytest.raises(Exception):
        iam_module.verify_credentials("operations", credentials["username"],
                                      credentials["password"])


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
