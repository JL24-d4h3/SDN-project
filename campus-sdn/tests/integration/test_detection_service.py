"""Pruebas de servicio de la Detección: línea base y AnomalyDetected."""

import pytest
from fastapi.testclient import TestClient

from services.detection import main as detection_module


@pytest.fixture()
def detection_client(monkeypatch):
    monkeypatch.setenv("BUS_URL", "")
    monkeypatch.setenv("DETECTION_SIGMA", "5")
    published = []
    monkeypatch.setattr(
        detection_module, "publish_event",
        lambda url, event: published.append((url, event)),
    )
    detection_module.baseline.clear()
    return TestClient(detection_module.app), published


def sample(destination, pps, bps=1000.0):
    return {
        "type": "MetricSample",
        "payload": {"destination": destination, "window": "5s",
                    "pps": pps, "bps": bps, "new_flows": 0,
                    "distinct_sources": 1},
    }


def test_normal_samples_build_baseline(monkeypatch, detection_client):
    _, published = detection_client
    for _ in range(10):
        assert detection_module.handle_event(sample("10.2.0.10", 100.0))
    assert published == []
    stats = detection_module.baseline["10.2.0.10"]
    assert stats["n"] == 10
    assert abs(stats["mean"] - 100.0) < 0.01


def test_burst_publishes_anomaly(detection_client):
    _, published = detection_client
    for _ in range(10):
        detection_module.handle_event(sample("10.2.0.10", 100.0))
    detection_module.handle_event(sample("10.2.0.10", 5000.0))

    assert len(published) == 1
    event = published[0][1]
    assert event["type"] == "AnomalyDetected"
    assert event["payload"]["type"] == "flood"
    assert event["payload"]["target"]["ip"] == "10.2.0.10"
    assert event["payload"]["rates"]["pps"] == 5000.0
    assert event["payload"]["proposed_severity"] == "high"


def test_anomaly_does_not_poison_baseline(detection_client):
    _, published = detection_client
    for _ in range(10):
        detection_module.handle_event(sample("10.2.0.10", 100.0))
    detection_module.handle_event(sample("10.2.0.10", 5000.0))
    stats = detection_module.baseline["10.2.0.10"]
    assert stats["n"] == 10  # la ráfaga no entró a la base
    assert abs(stats["mean"] - 100.0) < 0.01


def test_unknown_type_is_rejected(detection_client):
    _, _ = detection_client
    assert not detection_module.handle_event({"type": "NoExiste", "payload": {}})


def test_health(detection_client):
    client, _ = detection_client
    assert client.get("/health").status_code == 200
