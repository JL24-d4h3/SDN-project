"""Pruebas de servicio del sensor adapter: agregación EVE → MetricSample."""

import pytest
from fastapi.testclient import TestClient

from services.sensor_adapter import main as adapter_module


@pytest.fixture()
def adapter_client(monkeypatch):
    monkeypatch.setenv("BUS_URL", "")
    monkeypatch.setenv("SENSOR_WINDOW_S", "10")
    published = []
    monkeypatch.setattr(
        adapter_module, "publish_event",
        lambda url, event: published.append((url, event)),
    )
    adapter_module.windows.clear()
    return TestClient(adapter_module.app), published


def flow_line(dest="10.2.0.10", src="10.1.0.5", flow_id="f1",
              pkts=100, bytes_=80000):
    return (
        '{"event_type":"flow","dest_ip":"%s","src_ip":"%s",'
        '"flow_id":"%s","flow":{"pkts_toserver":%d,'
        '"pkts_toclient":0,"bytes_toserver":%d,"bytes_toclient":0}}'
        % (dest, src, flow_id, pkts, bytes_)
    )


def test_flow_lines_accumulate(adapter_client):
    _, _ = adapter_client
    adapter_module.handle_line(flow_line())
    adapter_module.handle_line(flow_line(pkts=50, bytes_=40000))
    window = adapter_module.windows["10.2.0.10"]
    assert window["pkts"] == 150
    assert window["bytes"] == 120000


def test_non_flow_lines_are_ignored(adapter_client):
    _, _ = adapter_client
    adapter_module.handle_line('{"event_type":"stats"}')
    adapter_module.handle_line('no es json')
    assert adapter_module.windows == {}


def test_flush_publishes_correct_sample(adapter_client):
    _, published = adapter_client
    adapter_module.handle_line(flow_line())
    adapter_module.handle_line(flow_line(flow_id="f2", src="10.1.0.6",
                                         pkts=50, bytes_=40000))
    adapter_module.flush()

    assert len(published) == 1
    event = published[0][1]
    payload = event["payload"]
    assert event["type"] == "MetricSample"
    assert payload["destination"] == "10.2.0.10"
    assert payload["pps"] == 15.0      # 150 paquetes / 10 s
    assert payload["bps"] == 96000.0   # 120000 bytes × 8 / 10 s
    assert payload["new_flows"] == 2
    assert payload["distinct_sources"] == 2
    assert adapter_module.windows == {}


def test_health(adapter_client):
    client, _ = adapter_client
    assert client.get("/health").status_code == 200
