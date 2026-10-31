"""Pruebas de servicio del Registry: registro, historial y revocación."""

import pytest
from fastapi.testclient import TestClient

from services.registry import main as registry_module


@pytest.fixture()
def registry_client(monkeypatch):
    monkeypatch.setenv("BUS_URL", "amqp://test")
    published = []
    monkeypatch.setattr(
        registry_module, "publish_event",
        lambda url, event: published.append((url, event)),
    )
    registry_module.devices.clear()
    registry_module.history.clear()
    return TestClient(registry_module.app), published


DEVICE = {
    "mac": "52:54:00:01:01", "owner": "a12345", "role": "academic",
    "responsible": "ti-operaciones", "validity": "2027-01-26",
}


def test_registration_publishes_event(registry_client):
    client, published = registry_client
    response = client.post("/devices", json=DEVICE)
    assert response.status_code == 200
    assert response.json()["status"] == "registered"

    event = published[0][1]
    assert event["type"] == "DeviceRegistered"
    assert event["payload"]["mac"] == DEVICE["mac"]


def test_list_and_history(registry_client):
    client, _ = registry_client
    client.post("/devices", json=DEVICE)

    devices = client.get("/devices").json()["devices"]
    assert len(devices) == 1
    assert devices[0]["owner"] == "a12345"

    history = client.get("/devices/52:54:00:01:01/history").json()["history"]
    assert [entry["entry"] for entry in history] == ["registered"]


def test_revocation_publishes_event(registry_client):
    client, published = registry_client
    client.post("/devices", json=DEVICE)
    published.clear()

    response = client.delete("/devices/52:54:00:01:01")
    assert response.status_code == 200
    assert published[0][1]["type"] == "DeviceRevoked"

    history = client.get("/devices/52:54:00:01:01/history").json()["history"]
    assert [entry["entry"] for entry in history] == ["registered", "revoked"]


def test_revoke_unknown_returns_404(registry_client):
    client, _ = registry_client
    assert client.delete("/devices/00:00:00:00:00:00").status_code == 404
