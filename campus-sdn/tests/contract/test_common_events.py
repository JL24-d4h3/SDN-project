"""Pruebas del constructor de eventos del esqueleto común.

Todo evento construido por sdn_common debe validar contra la envoltura y
contra el esquema de su tipo (RNF-12 en el lado del publicador).
"""

from pathlib import Path

import jsonschema
import pytest

from sdn_common.events import TYPE_TO_FILE, build_event, validate_event

SCHEMAS = Path(__file__).resolve().parents[2] / "contracts" / "events"

PAYLOADS = {
    "SessionOpened": {
        "identity": "a12345", "profile_or_role": "academic",
        "device": "52:54:00:01:01", "timestamp": "2026-10-31T12:00:00Z",
    },
    "ElevationRequested": {
        "requester": "a12345", "requested_profile": "laboratory",
        "scope": "laboratory", "duration": 1800,
    },
    "SessionClosed": {
        "identity": "a12345", "profile_or_role": "academic",
        "device": "52:54:00:01:01", "reason": "logout",
    },
}


@pytest.mark.parametrize("event_type", sorted(PAYLOADS))
def test_built_event_validates(event_type):
    event = build_event(event_type, PAYLOADS[event_type], sender="test")
    validate_event(event, SCHEMAS)


def test_event_with_correlation_validates():
    event = build_event(
        "SessionOpened", PAYLOADS["SessionOpened"], sender="iam",
        sequence=3, correlation={"session": "SES-000123"},
    )
    validate_event(event, SCHEMAS)
    assert event["sequence"] == 3
    assert event["correlation"]["session"] == "SES-000123"


def test_type_map_covers_catalog():
    envelope_schema = SCHEMAS / "envelope.schema.json"
    import json

    envelope = json.loads(envelope_schema.read_text())
    enum = set(envelope["properties"]["type"]["enum"])
    assert set(TYPE_TO_FILE) == enum


def test_rejects_invalid_payload():
    event = build_event(
        "SessionOpened", {"identity": "a12345"}, sender="test",
    )
    with pytest.raises(jsonschema.ValidationError):
        validate_event(event, SCHEMAS)
