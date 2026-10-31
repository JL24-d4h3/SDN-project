"""Construcción y validación de eventos del bus (contratos de events/)."""

import datetime
import json
from pathlib import Path

import jsonschema
from uuid6 import uuid7

# Nombre del tipo en el catálogo → archivo de esquema (kebab-case).
# Misma correspondencia que tests/contract/test_eventos.py: si el
# catálogo cambia, cambia en ambos.
TYPE_TO_FILE = {
    "DeviceConnected": "device-connected",
    "MAC_Moved": "mac-moved",
    "AnomalyDetected": "anomaly-detected",
    "IncidentOpened": "incident-opened",
    "MitigationRequired": "mitigation-required",
    "MitigationApplied": "mitigation-applied",
    "MitigationVerified": "mitigation-verified",
    "MitigationExpired": "mitigation-expired",
    "ElevationRequested": "elevation-requested",
    "ElevationGranted": "elevation-granted",
    "ElevationExpired": "elevation-expired",
    "SessionOpened": "session-opened",
    "SessionClosed": "session-closed",
    "DeviceRegistered": "device-registered",
    "DeviceRevoked": "device-revoked",
    "MetricSample": "metric-sample",
}


def utc_now() -> str:
    """Marca de tiempo UTC con el formato del contrato (date-time)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def build_event(event_type: str, payload: dict, sender: str, *,
                sequence: int | None = None,
                correlation: dict | None = None) -> dict:
    """Construye un evento con la envoltura común del contrato.

    event_id es UUIDv7 (clave de idempotencia); sequence y correlation
    se omiten cuando no aplican. Nunca incluir secretos en payload ni
    en correlation (CLAUDE.md).
    """
    event = {
        "event_id": str(uuid7()),
        "type": event_type,
        "sender": sender,
        "timestamp": utc_now(),
        "payload": payload,
    }
    if sequence is not None:
        event["sequence"] = sequence
    if correlation:
        event["correlation"] = correlation
    return event


def validate_event(event: dict, schemas_dir: Path) -> None:
    """Valida la envoltura y el payload contra los esquemas del contrato.

    Lanza jsonschema.ValidationError si el evento no cumple su tipo.
    """
    envelope = json.loads((schemas_dir / "envelope.schema.json").read_text())
    jsonschema.validate(event, envelope)
    schema_file = TYPE_TO_FILE[event["type"]]
    payload_schema = json.loads((schemas_dir / f"{schema_file}.schema.json").read_text())
    jsonschema.validate(event["payload"], payload_schema)
