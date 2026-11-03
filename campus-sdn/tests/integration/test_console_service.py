"""Pruebas de servicio de Console: alertas en vivo y SSO opcional."""

import pytest
from fastapi.testclient import TestClient

from services.console import main as console_module


@pytest.fixture()
def console_client(monkeypatch):
    monkeypatch.setenv("BUS_URL", "")
    monkeypatch.setenv("IAM_URL", "")
    console_module.alerts.clear()
    return TestClient(console_module.app)


def alert(event_type="AnomalyDetected"):
    return {"event_id": "id-1", "type": event_type, "sender": "detection",
            "timestamp": "2026-10-31T12:00:00Z", "payload": {}}


def test_registers_only_alerts(console_client):
    client = console_client
    assert console_module.handle_event(alert())
    assert console_module.handle_event(alert(event_type="IncidentOpened"))
    assert not console_module.handle_event(alert(event_type="SessionOpened"))
    data = client.get("/alerts").json()["alerts"]
    assert [item["type"] for item in data] == ["IncidentOpened",
                                               "AnomalyDetected"]


def test_without_iam_no_session_required(console_client):
    assert console_client.get("/alerts").status_code == 200


def test_with_iam_rejects_missing_session(monkeypatch, console_client):
    monkeypatch.setenv("IAM_URL", "http://iam:8001")
    assert console_client.get("/alerts").status_code == 401
    assert console_client.get("/alerts",
                              headers={"X-Session": "x"}).status_code == 503


def test_academic_session_gets_403(monkeypatch, console_client):
    monkeypatch.setenv("IAM_URL", "http://iam:8001")
    from sdn_common import authz

    monkeypatch.setattr(authz.httpx, "get", lambda url, **kw: type(
        "Response", (), {"status_code": 200,
                         "json": lambda self: {
                             "profile_or_role": "academic"}})())
    response = console_client.get("/alerts", headers={"X-Session": "s"})
    assert response.status_code == 403


def test_it_session_gets_200(monkeypatch, console_client):
    monkeypatch.setenv("IAM_URL", "http://iam:8001")
    from sdn_common import authz

    monkeypatch.setattr(authz.httpx, "get", lambda url, **kw: type(
        "Response", (), {"status_code": 200,
                         "json": lambda self: {
                             "profile_or_role": "it_specialist"}})())
    assert console_client.get(
        "/alerts", headers={"X-Session": "s"}).status_code == 200


def test_ui_serves_page(console_client):
    response = console_client.get("/")
    assert response.status_code == 200
    assert "Consola del operador" in response.text


def test_health(console_client):
    assert console_client.get("/health").status_code == 200
