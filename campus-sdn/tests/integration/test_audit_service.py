"""Pruebas de servicio de Audit: registro completo y huecos declarados."""

import pytest
from fastapi.testclient import TestClient

from services.audit import main as audit_module


@pytest.fixture()
def audit_client(monkeypatch):
    monkeypatch.setenv("BUS_URL", "")
    audit_module.records.clear()
    audit_module.sequences.clear()
    return TestClient(audit_module.app)


def event(event_type="SessionOpened", sequence=None, incident=None):
    payload = {"identity": "a12345", "profile_or_role": "academic",
               "device": "52:54:00:01:01",
               "timestamp": "2026-10-31T12:00:00Z"}
    event_data = {"event_id": "id-1", "type": event_type, "sender": "iam",
              "timestamp": "2026-10-31T12:00:00Z", "payload": payload}
    if sequence is not None:
        event_data["sequence"] = sequence
    if incident:
        event_data["correlation"] = {"incident": incident}
    return event_data


def test_registra_todo_lo_que_llega(audit_client):
    client = audit_client
    assert audit_module.handle_event(event())
    assert audit_module.handle_event(event(event_type="SessionClosed"))
    data = client.get("/events").json()["data"]
    assert len(data) == 2


def test_hueco_de_secuencia_se_declara(audit_client):
    client = audit_client
    audit_module.handle_event(event(sequence=1, incident="INC-0042"))
    audit_module.handle_event(event(sequence=3, incident="INC-0042"))

    data = client.get("/events").json()["data"]
    gaps = [record for record in data if record.get("type") == "gap-declared"]
    assert len(gaps) == 1
    assert gaps[0]["expected"] == 2
    assert gaps[0]["received"] == 3


def test_filtros_de_consulta(audit_client):
    client = audit_client
    audit_module.handle_event(event())
    audit_module.handle_event(event(event_type="SessionClosed"))
    data = client.get("/events", params={"actor": "iam"}).json()["data"]
    assert len(data) == 2
    data = client.get("/events", params={"actor": "nadie"}).json()["data"]
    assert data == []


def test_paginacion_por_cursor(audit_client):
    client = audit_client
    for index in range(5):
        audit_module.handle_event(event())
    first = client.get("/events", params={"limit": 2}).json()
    assert len(first["data"]) == 2
    assert first["cursor"] == 2
    second = client.get("/events", params={"limit": 2, "cursor": 2}).json()
    assert len(second["data"]) == 2


def test_health(audit_client):
    assert audit_client.get("/health").status_code == 200
