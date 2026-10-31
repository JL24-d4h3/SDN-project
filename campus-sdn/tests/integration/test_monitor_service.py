"""Pruebas de servicio del Monitor: ubicaciones, MAC_Moved y verificación."""

import pytest
from fastapi.testclient import TestClient

from services.monitor import main as monitor_module


@pytest.fixture()
def monitor_client(monkeypatch):
    monkeypatch.setenv("BUS_URL", "")
    published = []
    monkeypatch.setattr(
        monitor_module, "publish_event",
        lambda url, event: published.append((url, event)),
    )
    monitor_module.locations.clear()
    monitor_module.samples.clear()
    monitor_module.mitigations.clear()
    monitor_module.seen_events = 0
    return TestClient(monitor_module.app), published


def device_connected(mac, switch, port):
    return {
        "type": "DeviceConnected",
        "payload": {"mac": mac, "ip": "10.1.0.10", "switch": switch,
                    "port": port, "timestamp": "2026-10-31T12:00:00Z"},
    }


def test_first_connection_does_not_move(monitor_client):
    _, published = monitor_client
    assert monitor_module.handle_event(device_connected("52:54:00:01:01", "A1", "p20"))
    assert published == []


def test_second_connection_elsewhere_publishes_mac_moved(monitor_client):
    _, published = monitor_client
    monitor_module.handle_event(device_connected("52:54:00:01:01", "A1", "p20"))
    monitor_module.handle_event(device_connected("52:54:00:01:01", "A2", "p4"))

    assert len(published) == 1
    event = published[0][1]
    assert event["type"] == "MAC_Moved"
    assert event["payload"]["previous_location"] == {"switch": "A1", "port": "p20"}
    assert event["payload"]["new_location"] == {"switch": "A2", "port": "p4"}


def test_same_location_does_not_publish(monitor_client):
    _, published = monitor_client
    monitor_module.handle_event(device_connected("52:54:00:01:01", "A1", "p20"))
    monitor_module.handle_event(device_connected("52:54:00:01:01", "A1", "p20"))
    assert published == []


def test_unknown_type_is_rejected(monitor_client):
    _, _ = monitor_client
    assert not monitor_module.handle_event({"type": "NoExiste", "payload": {}})


def test_mitigation_is_registered_pending(monitor_client):
    _, _ = monitor_client
    monitor_module.handle_event({
        "type": "MitigationApplied",
        "payload": {"incident": "INC-0042", "rules": ["R-001"],
                    "switches": ["A2"], "applied_at": "2026-10-31T12:00:00Z"},
    })
    assert "INC-0042" in monitor_module.mitigations


def test_health(monitor_client):
    client, _ = monitor_client
    assert client.get("/health").status_code == 200
    assert client.get("/metrics").json() == {"metrics": []}
    assert client.get("/baselines").json()["baselines"]["aggregate"]["mean"] == 0.0
