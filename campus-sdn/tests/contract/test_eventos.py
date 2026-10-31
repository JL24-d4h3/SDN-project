"""Pruebas de contrato de los eventos del bus (RNF-12).

Cada tipo del catálogo (LLD 02_eventos.md §3) tiene un ejemplo válido que
debe pasar su esquema, un ejemplo envuelto en la envoltura común que debe
pasar la envoltura, y casos de rechazo que deben fallar. La prueba del
catálogo garantiza que la envoltura y los esquemas no se desincronizan.
Los nombres de campos están en inglés; el LLD los describe en español.
"""

import json
from pathlib import Path

import jsonschema
import pytest

EVENTS = Path(__file__).resolve().parents[2] / "contracts" / "events"


def load_schema(name):
    return json.loads((EVENTS / f"{name}.schema.json").read_text())


ENVELOPE = load_schema("envelope")

TS = "2026-10-31T12:00:00Z"
ORIGIN = {"mac": "52:54:00:03:02", "switch": "A2", "port": "p6"}

# Nombre de archivo (kebab-case) → nombre del tipo en el catálogo (LLD).
TYPE_NAMES = {
    "device-connected": "DeviceConnected",
    "mac-moved": "MAC_Moved",
    "anomaly-detected": "AnomalyDetected",
    "incident-opened": "IncidentOpened",
    "mitigation-required": "MitigationRequired",
    "mitigation-applied": "MitigationApplied",
    "mitigation-verified": "MitigationVerified",
    "mitigation-expired": "MitigationExpired",
    "elevation-requested": "ElevationRequested",
    "elevation-granted": "ElevationGranted",
    "elevation-expired": "ElevationExpired",
    "session-opened": "SessionOpened",
    "session-closed": "SessionClosed",
    "device-registered": "DeviceRegistered",
    "device-revoked": "DeviceRevoked",
    "metric-sample": "MetricSample",
}

SAMPLES = {
    "device-connected": {
        "mac": "52:54:00:01:01", "ip": "10.1.0.10",
        "switch": "A1", "port": "p20", "timestamp": TS,
    },
    "mac-moved": {
        "mac": "52:54:00:01:01",
        "previous_location": {"switch": "A1", "port": "p20"},
        "new_location": {"switch": "A2", "port": "p4"},
    },
    "anomaly-detected": {
        "type": "flood", "target": {"ip": "10.2.0.10", "service": "bd-academica"},
        "origins": [ORIGIN], "rates": {"pps": 5000.0, "bps": 3000000.0},
        "baseline": {"mean": 100.0, "sigma": 20.0}, "deviation": 50.0,
        "proposed_severity": "alta",
    },
    "incident-opened": {
        "incident": "INC-0042", "type": "flood",
        "target": "bd-academica", "severity": "alta", "opened_at": TS,
    },
    "mitigation-required": {
        "incident": "INC-0042", "action": "RATE_LIMIT",
        "target": "10.2.0.10", "origins": [ORIGIN],
        "parameters": {"rate_pps": 1000, "ttl_s": 300}, "ttl": 300,
    },
    "mitigation-applied": {
        "incident": "INC-0042", "rules": ["R-001"],
        "switches": ["A2"], "applied_at": TS,
    },
    "mitigation-verified": {
        "incident": "INC-0042",
        "rates_before": {"pps": 5000.0, "bps": 3000000.0},
        "rates_after": {"pps": 50.0, "bps": 40000.0},
        "meets_objective": True,
    },
    "mitigation-expired": {
        "incident": "INC-0042", "rule": "R-001", "reason": "timeout",
    },
    "elevation-requested": {
        "requester": "a12345", "requested_profile": "laboratory",
        "scope": "laboratorio", "duration": 1800,
    },
    "elevation-granted": {
        "requester": "a12345", "profile": "sa_operator", "ttl": 1800,
    },
    "elevation-expired": {
        "requester": "a12345", "profile": "sa_operator", "reason": "timeout",
    },
    "session-opened": {
        "identity": "a12345", "profile_or_role": "academic",
        "device": "52:54:00:01:01", "timestamp": TS,
    },
    "session-closed": {
        "identity": "a12345", "profile_or_role": "academic",
        "device": "52:54:00:01:01", "reason": "logout",
    },
    "device-registered": {
        "mac": "52:54:00:01:01", "owner": "a12345", "role": "academic",
        "responsible": "ti-operaciones", "validity": "2027-01-26",
    },
    "device-revoked": {
        "mac": "52:54:00:01:01", "owner": "a12345", "role": "academic",
        "responsible": "ti-operaciones", "validity": "2026-10-31",
    },
    "metric-sample": {
        "destination": "10.2.0.10", "window": "60s", "pps": 120.5,
        "bps": 800000.0, "new_flows": 3, "distinct_sources": 2,
    },
}


def wrap(name, payload):
    return {
        "event_id": "018f2abc-0000-7000-8000-000000000001",
        "type": TYPE_NAMES[name],
        "sender": "test",
        "timestamp": TS,
        "sequence": 7,
        "correlation": {"incident": "INC-0042"},
        "payload": payload,
    }


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_valid_payload(name):
    jsonschema.validate(SAMPLES[name], load_schema(name))


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_valid_envelope(name):
    event = wrap(name, SAMPLES[name])
    jsonschema.validate(event, ENVELOPE)
    jsonschema.validate(event["payload"], load_schema(name))


def test_rejects_unknown_field():
    bad = dict(SAMPLES["device-connected"], extra="no declarado")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, load_schema("device-connected"))


def test_rejects_missing_field():
    bad = {k: v for k, v in SAMPLES["device-connected"].items() if k != "mac"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, load_schema("device-connected"))


def test_rejects_unknown_type():
    bad = wrap("session-opened", SAMPLES["session-opened"])
    bad["type"] = "NoExiste"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, ENVELOPE)


def test_rejects_invalid_reason():
    bad = dict(SAMPLES["mitigation-expired"], reason="otro")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, load_schema("mitigation-expired"))


def test_catalog_is_complete():
    """La envoltura y los esquemas no deben desincronizarse."""
    enum = set(ENVELOPE["properties"]["type"]["enum"])
    files = {
        p.stem.removesuffix(".schema")
        for p in EVENTS.glob("*.schema.json") if p.name != "envelope.schema.json"
    }
    assert enum == {TYPE_NAMES[name] for name in files}
    assert len(enum) == 16
