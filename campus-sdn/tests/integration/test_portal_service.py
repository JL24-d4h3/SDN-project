"""Pruebas de servicio del Portal: selector, reenvíos al IAM y elevación.

El IAM se simula con un httpx.post falso; el publicador del bus se
sustituye para capturar la solicitud de elevación validada. Las
credenciales jamás se registran ni se publican.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from services.portal import main as portal_module


class FakeIamResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.payload = payload or {}

    def json(self):
        return self.payload


@pytest.fixture()
def portal_client(monkeypatch):
    monkeypatch.setattr(portal_module, "IAM_URL", "http://iam:8001")
    monkeypatch.setattr(portal_module, "BUS_URL", "")
    published = []
    monkeypatch.setattr(
        portal_module, "publish_event",
        lambda url, event: published.append((url, event)),
    )
    return TestClient(portal_module.app), published


def test_selector_lists_three_realms(portal_client):
    client, _ = portal_client
    body = client.get("/login").json()
    assert body == {"populations": ["university", "operations", "guest"]}


def test_login_forwards_to_iam(portal_client, monkeypatch):
    client, _ = portal_client
    seen = []

    def fake_post(url, **kw):
        seen.append((url, kw["json"]))
        return FakeIamResponse(200, {"session": "SES-1"})

    monkeypatch.setattr(portal_module.httpx, "post", fake_post)
    response = client.post("/login", json={
        "population": "university", "username": "a12345", "password": "x"})
    assert response.status_code == 200
    assert response.json()["session"] == "SES-1"
    assert seen[0][0] == "http://iam:8001/verify"


def test_resolve_device_skips_loopback(portal_client):
    assert portal_module._resolve_device("127.0.0.1") is None
    assert portal_module._resolve_device("::1") is None
    assert portal_module._resolve_device("") is None
    assert portal_module._resolve_device("10.0.0.1") is None  # sin I2_URL


def test_resolve_device_asks_the_controller(portal_client, monkeypatch):
    monkeypatch.setattr(portal_module, "I2_URL", "http://adapter:8090")
    seen = []

    def fake_get(url, **kw):
        seen.append((url, kw["params"]))
        return FakeIamResponse(200, {"mac": "52:54:00:01:01", "ip": "10.0.0.1",
                                     "switch": "of:1", "port": "2"})

    monkeypatch.setattr(portal_module.httpx, "get", fake_get)
    device = portal_module._resolve_device("10.0.0.1")
    assert device["mac"] == "52:54:00:01:01"
    assert seen[0] == ("http://adapter:8090/associations",
                       {"ip": "10.0.0.1"})


def test_login_forwards_device_learned_by_the_network(portal_client,
                                                      monkeypatch):
    client, _ = portal_client
    monkeypatch.setattr(portal_module, "I2_URL", "http://adapter:8090")
    seen = []

    def fake_get(url, **kw):
        return FakeIamResponse(200, {"mac": "52:54:00:01:01",
                                     "ip": "testclient"})

    def fake_post(url, **kw):
        seen.append((url, kw["json"]))
        return FakeIamResponse(200, {"session": "SES-1"})

    monkeypatch.setattr(portal_module.httpx, "get", fake_get)
    monkeypatch.setattr(portal_module.httpx, "post", fake_post)
    client.post("/login", json={
        "population": "university", "username": "a12345", "password": "x"})
    assert seen[0][1]["device"] == "52:54:00:01:01"


def test_login_rejects_on_iam_401(portal_client, monkeypatch):
    client, _ = portal_client
    monkeypatch.setattr(portal_module.httpx, "post",
                        lambda url, **kw: FakeIamResponse(401))
    assert client.post("/login", json={
        "population": "university", "username": "a", "password": "x"
    }).status_code == 401


def test_login_503_when_iam_unreachable(portal_client, monkeypatch):
    client, _ = portal_client
    def unreachable(url, **kw):
        raise httpx.HTTPError("down")

    monkeypatch.setattr(portal_module.httpx, "post", unreachable)
    assert client.post("/login", json={
        "population": "university", "username": "a", "password": "x"
    }).status_code == 503


def test_logout_forwards_and_503(portal_client, monkeypatch):
    client, _ = portal_client
    monkeypatch.setattr(portal_module.httpx, "post",
                        lambda url, **kw: FakeIamResponse(200,
                                                          {"status": "closed"}))
    assert client.post("/logout",
                       json={"session": "SES-1"}).status_code == 200

    def unreachable(url, **kw):
        raise httpx.HTTPError("down")

    monkeypatch.setattr(portal_module.httpx, "post", unreachable)
    assert client.post("/logout",
                       json={"session": "SES-1"}).status_code == 503


def test_guest_register_forwards(portal_client, monkeypatch):
    client, _ = portal_client
    monkeypatch.setattr(portal_module.httpx, "post", lambda url, **kw: (
        FakeIamResponse(200, {"status": "registered",
                              "expires_at": 1793444494.0})))
    response = client.post("/guest-register",
                           json={"username": "guest-1", "password": "x"})
    assert response.status_code == 200
    assert response.json()["status"] == "registered"


def test_elevation_without_bus_returns_503(portal_client):
    client, _ = portal_client
    assert client.post("/elevation",
                       json={"requester": "a12345"}).status_code == 503


def test_elevation_publishes_validated_event(portal_client, monkeypatch):
    client, published = portal_client
    monkeypatch.setattr(portal_module, "BUS_URL", "amqp://test")
    response = client.post("/elevation", json={
        "requester": "a12345", "scope": "laboratory", "duration": 1800})
    assert response.status_code == 200

    event = published[0][1]
    assert event["type"] == "ElevationRequested"
    assert event["payload"]["requester"] == "a12345"
    assert event["sender"] == "portal"
    # La validación del contrato ya ocurrió: un payload inválido habría
    # fallado antes de publicar.
    assert "password" not in str(event)


def test_ui_serves_captive_page(portal_client):
    client, _ = portal_client
    response = client.get("/")
    assert response.status_code == 200
    assert "Portal cautivo" in response.text
    assert "Comunidad universitaria" in response.text
    # El dispositivo lo conoce la red: jamás se le pide al usuario.
    assert "MAC del dispositivo" not in response.text
    # El TOTP solo aparece después de reconocer las credenciales: el
    # campo arranca oculto y lo revela la respuesta totp_required.
    assert 'id="totp-row" style="display:none"' in response.text


def test_login_passes_totp_required_through(portal_client, monkeypatch):
    client, _ = portal_client
    monkeypatch.setattr(portal_module.httpx, "post", lambda url, **kw: (
        FakeIamResponse(200, {"totp_required": True, "username": "op-1"})))
    response = client.post("/login", json={
        "population": "operations", "username": "op-1", "password": "x"})
    assert response.status_code == 200
    assert response.json()["totp_required"] is True


def test_elevation_scope_form(portal_client):
    client, _ = portal_client
    assert client.get("/elevation").json() == {"scopes": ["laboratory"]}


def test_health(portal_client):
    client, _ = portal_client
    assert client.get("/health").status_code == 200
