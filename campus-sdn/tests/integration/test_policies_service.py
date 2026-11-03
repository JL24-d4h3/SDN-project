"""Pruebas de servicio de Policies: decisión de mitigación y elevaciones."""

import pytest
from fastapi.testclient import TestClient

from services.policies import main as policies_module


@pytest.fixture()
def policies_client(monkeypatch):
    monkeypatch.setenv("BUS_URL", "")
    monkeypatch.setenv("RATE_LIMIT_PPS", "1000")
    monkeypatch.setenv("MITIGATION_TTL_S", "300")
    published = []
    monkeypatch.setattr(
        policies_module, "publish_event",
        lambda url, event: published.append((url, event)),
    )
    policies_module.decisions.clear()
    policies_module.elevations.clear()
    policies_module.profiles.clear()
    policies_module.thresholds.clear()
    return TestClient(policies_module.app), published


def incident_opened(incident="INC-0042", incident_type="flood",
                    target="10.2.0.10", severity="high"):
    return {
        "type": "IncidentOpened",
        "payload": {"incident": incident, "type": incident_type,
                    "target": target, "severity": severity,
                    "opened_at": "2026-10-31T12:00:00Z"},
    }


def test_flood_decides_rate_limit(monkeypatch, policies_client):
    _, published = policies_client
    orders = []
    monkeypatch.setattr(policies_module, "_send_order",
                        lambda order: orders.append(order))
    assert policies_module.handle_event(incident_opened())

    assert len(published) == 1
    event = published[0][1]
    assert event["type"] == "MitigationRequired"
    assert event["payload"]["action"] == "RATE_LIMIT"
    assert event["payload"]["parameters"] == {"rate_pps": 1000, "ttl_s": 300}
    assert event["payload"]["ttl"] == 300
    assert event["correlation"]["incident"] == "INC-0042"

    # El comando viaja por I2 (síncrono); el bus lleva el eco.
    assert len(orders) == 1
    assert orders[0]["order"] == "APPLY_MITIGATION"
    assert orders[0]["action"] == "RATE_LIMIT"


def test_other_type_stays_pending(policies_client):
    _, published = policies_client
    assert policies_module.handle_event(
        incident_opened(incident_type="scan"))
    assert published == []
    assert policies_module.decisions["INC-0042"]["action"] is None


def test_verified_updates_decision(policies_client):
    _, _ = policies_client
    policies_module.handle_event(incident_opened())
    policies_module.handle_event({
        "type": "MitigationVerified",
        "payload": {"incident": "INC-0042",
                    "rates_before": {"pps": 5000.0, "bps": 3000000.0},
                    "rates_after": {"pps": 50.0, "bps": 40000.0},
                    "meets_objective": True},
    })
    assert policies_module.decisions["INC-0042"]["result"]["meets_objective"]


def test_elevation_stays_pending(policies_client):
    client, _ = policies_client
    policies_module.handle_event({
        "type": "ElevationRequested",
        "payload": {"requester": "a12345", "requested_profile": "laboratory",
                    "scope": "laboratory", "duration": 1800},
    })
    elevations = client.get("/elevations").json()["elevations"]
    assert len(elevations) == 1
    assert elevations[0]["state"] == "pending"


def test_thresholds_put_and_get(policies_client):
    client, _ = policies_client
    assert client.put("/thresholds",
                      json={"thresholds": {"sigma": 5}}).status_code == 200
    assert client.get("/thresholds").json()["thresholds"]["sigma"] == 5


def test_thresholds_put_requires_permission(monkeypatch, policies_client):
    client, _ = policies_client
    monkeypatch.setenv("IAM_URL", "http://iam:8001")
    from sdn_common import authz

    monkeypatch.setattr(authz.httpx, "get", lambda url, **kw: type(
        "Response", (), {"status_code": 200,
                         "json": lambda self: {
                             "profile_or_role": "academic"}})())
    response = client.put("/thresholds",
                          json={"thresholds": {"sigma": 5}},
                          headers={"X-Session": "s"})
    assert response.status_code == 403


def test_unknown_type_is_rejected(policies_client):
    _, _ = policies_client
    assert not policies_module.handle_event({"type": "NoExiste", "payload": {}})


def test_health(policies_client):
    client, _ = policies_client
    assert client.get("/health").status_code == 200
