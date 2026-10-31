"""Pruebas de servicio de Incidents: apertura, aprobación y evidencia."""

import pytest
from fastapi.testclient import TestClient

from services.incidents import main as incidents_module


@pytest.fixture()
def incidents_client(monkeypatch):
    monkeypatch.setenv("BUS_URL", "")
    published = []
    monkeypatch.setattr(
        incidents_module, "publish_event",
        lambda url, event: published.append((url, event)),
    )
    incidents_module.incidents.clear()
    incidents_module.sequence = 0
    return TestClient(incidents_module.app), published


def anomaly_detected(ip="10.2.0.10", severity="high"):
    return {
        "type": "AnomalyDetected",
        "payload": {
            "type": "flood", "target": {"ip": ip, "service": ""},
            "origins": [], "rates": {"pps": 5000.0, "bps": 3000000.0},
            "baseline": {"mean": 100.0, "sigma": 0.0},
            "deviation": 4900.0, "proposed_severity": severity,
        },
    }


def test_anomaly_opens_incident_and_publishes(incidents_client):
    _, published = incidents_client
    assert incidents_module.handle_event(anomaly_detected())

    assert len(published) == 1
    event = published[0][1]
    assert event["type"] == "IncidentOpened"
    assert event["payload"]["incident"] == "INC-0001"
    assert event["payload"]["severity"] == "high"
    assert event["payload"]["target"] == "10.2.0.10"


def test_verification_adds_evidence(incidents_client):
    client, _ = incidents_client
    incidents_module.handle_event(anomaly_detected())
    incidents_module.handle_event({
        "type": "MitigationVerified",
        "payload": {"incident": "INC-0001",
                    "rates_before": {"pps": 5000.0, "bps": 3000000.0},
                    "rates_after": {"pps": 50.0, "bps": 40000.0},
                    "meets_objective": True},
        "correlation": {"incident": "INC-0001"},
    })

    incident = client.get("/incidents/INC-0001").json()["incident"]
    assert incident["evidence"][0]["type"] == "MitigationVerified"


def test_approve_and_close(incidents_client):
    client, _ = incidents_client
    incidents_module.handle_event(anomaly_detected())
    assert client.post("/incidents/INC-0001/approve",
                       json={"approver": "op-1"}).status_code == 200
    assert client.post("/incidents/INC-0001/close").status_code == 200
    incident = client.get("/incidents/INC-0001").json()["incident"]
    assert incident["approval"]["approver"] == "op-1"
    assert incident["state"] == "closed"


def test_unknown_incident(incidents_client):
    client, _ = incidents_client
    assert client.get("/incidents/INC-9999").status_code == 200
    assert "error" in client.get("/incidents/INC-9999").json()


def test_unknown_type_is_rejected(incidents_client):
    _, _ = incidents_client
    assert not incidents_module.handle_event({"type": "NoExiste", "payload": {}})


def test_health(incidents_client):
    client, _ = incidents_client
    assert client.get("/health").status_code == 200
