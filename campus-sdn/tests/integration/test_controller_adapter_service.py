"""Pruebas de servicio del adaptador I2 con un ONOS falso.

El ONOS real llega con el slice; aquí un cliente falso registra flujos,
meters y borrados, y se verifican la escalera (prioridades, cookies,
timeouts) y el eco MitigationApplied.
"""

import pytest
from fastapi.testclient import TestClient

from services.controller_adapter import main as adapter_module


class FakeOnos:
    """Misma interfaz que OnosClient, sin red."""

    def __init__(self, fail=False):
        self.fail = fail
        self.flow_store = {}        # device_id → [flow]
        self.meters = []
        self.removed = []

    def _guard(self):
        if self.fail:
            raise adapter_module.HTTPException(status_code=503,
                                               detail="controller unavailable")

    def devices(self):
        self._guard()
        return ["of:0000000000000011", "of:0000000000000021"]

    def install_flow(self, device_id, flow):
        self._guard()
        flow["id"] = f"{device_id}:{flow.get('priority')}:{flow.get('cookie')}"
        self.flow_store.setdefault(device_id, []).append(dict(flow))
        return flow["id"]

    def flows(self, device_id):
        self._guard()
        return self.flow_store.get(device_id, [])

    def remove_flow(self, device_id, flow_id):
        self._guard()
        self.removed.append((device_id, flow_id))

    def install_meter(self, device_id, meter):
        self._guard()
        self.meters.append(dict(meter))
        return int(meter.get("meterId", 1))

    def hosts(self):
        self._guard()
        return [{
            "mac": "52:54:00:01:01",
            "ipAddresses": ["10.1.0.10"],
            "locations": [{"elementId": "of:0000000000000021",
                           "port": "20"}],
        }]

    def passthrough(self, path):
        self._guard()
        return {}


@pytest.fixture()
def adapter_client(monkeypatch):
    monkeypatch.setenv("BUS_URL", "")
    monkeypatch.setenv(
        "SWITCH_DPIDS",
        '{"A1": "of:0000000000000011", "A2": "of:0000000000000021"}')
    published = []
    monkeypatch.setattr(
        adapter_module, "publish_event",
        lambda url, event: published.append((url, event)),
    )
    adapter_module.cookie_registry.clear()
    adapter_module.order_registry.clear()
    adapter_module.services.clear()
    fake = FakeOnos()
    monkeypatch.setattr(adapter_module, "_onos", lambda: fake)
    return TestClient(adapter_module.app), published, fake


def mitigation_order(action="RATE_LIMIT"):
    return {
        "order": "APPLY_MITIGATION", "action": action,
        "target": {"type": "service", "ip": "10.2.0.10"},
        "origins": [{"mac": "52:54:00:03:02", "switch": "A2", "port": "6"}],
        "parameters": {"rate_pps": 1000, "ttl_s": 300},
        "context": {"cookie": "INC-0042", "incident": "INC-0042",
                    "requester": "policies", "reason": "flood",
                    "approval": None},
    }


def test_rate_limit_installs_ladder_and_publishes(adapter_client):
    client, published, fake = adapter_client
    response = client.post("/orders", json=mitigation_order())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "APPLIED"
    assert body["verification"] == "PENDING"

    flow = fake.flow_store["of:0000000000000021"][0]
    assert flow["priority"] == 1000
    assert flow["timeout"] == 300
    assert flow["cookie"].startswith("0x02")   # incidente (LLD §3)
    instructions = flow["treatment"]["instructions"]
    assert any(i["type"] == "METER" for i in instructions)
    assert fake.meters[0]["bands"][0]["rate"] == 1000

    event = published[0][1]
    assert event["type"] == "MitigationApplied"
    assert event["payload"]["incident"] == "INC-0042"


def test_block_source_drops(adapter_client):
    client, _, fake = adapter_client
    client.post("/orders", json=mitigation_order("BLOCK_SOURCE"))
    flow = fake.flow_store["of:0000000000000021"][0]
    assert flow["treatment"]["instructions"] == [{"type": "DROP"}]


def test_profile_installs_session_ladder(adapter_client):
    client, _, fake = adapter_client
    response = client.post("/orders", json={
        "order": "APPLY_PROFILE",
        "device": {"mac": "52:54:00:01:01", "switch": "A1", "port": "20"},
        "validity": {"idle_timeout_s": 1800, "hard_timeout_s": 43200},
        "context": {"cookie": "SES-000123", "requester": "iam",
                    "reason": "login-academic"},
        "profile": "academic",
    })
    assert response.status_code == 200
    flow = fake.flow_store["of:0000000000000011"][0]
    assert flow["priority"] == 200
    assert flow["cookie"].startswith("0x01")   # sesión (LLD §3)
    assert flow["timeout"] == 43200
    assert flow["idleTimeout"] == 1800


def test_withdraw_removes_only_own_cookie(adapter_client):
    client, _, fake = adapter_client
    client.post("/orders", json=mitigation_order())
    response = client.post("/orders", json={
        "order": "WITHDRAW",
        "context": {"cookie": "INC-0042", "requester": "policies"},
    })
    assert response.status_code == 200
    assert response.json()["status"] == "WITHDRAWN"
    assert len(fake.removed) == 1

    unknown = client.post("/orders", json={
        "order": "WITHDRAW",
        "context": {"cookie": "AJENA-0001", "requester": "policies"},
    })
    assert unknown.status_code == 404


def test_rate_limit_without_origins_applies_everywhere(adapter_client):
    client, _, fake = adapter_client
    order = mitigation_order()
    order["origins"] = []
    response = client.post("/orders", json=order)
    assert response.status_code == 200
    flow = fake.flow_store["of:0000000000000021"][0]
    criteria = flow["selector"]["criteria"]
    assert criteria == [{"type": "IPV4_DST", "ip": "10.2.0.10"}]


def test_block_without_origins_is_rejected(adapter_client):
    client, _, _ = adapter_client
    order = mitigation_order("BLOCK_SOURCE")
    order["origins"] = []
    assert client.post("/orders", json=order).status_code == 400


def test_unavailable_controller_returns_503(adapter_client, monkeypatch):
    client, _, _ = adapter_client
    monkeypatch.setattr(adapter_module, "_onos",
                        lambda: FakeOnos(fail=True))
    response = client.post("/orders", json=mitigation_order())
    assert response.status_code == 503


def test_association_from_hosts(adapter_client):
    client, _, _ = adapter_client
    body = client.get("/associations", params={"ip": "10.1.0.10"}).json()
    assert body["mac"] == "52:54:00:01:01"
    assert body["switch"] == "of:0000000000000021"
    assert client.get("/associations",
                      params={"ip": "10.9.9.9"}).status_code == 404


def test_services_inventory(adapter_client):
    client, _, _ = adapter_client
    assert client.post("/services", json={
        "name": "bd-academica", "class": "critico", "ip": "10.2.0.12",
        "switch": "A2", "port": "4", "declared_by": "ti",
    }).status_code == 200
    assert client.get("/services").json()["services"][0]["name"] == \
        "bd-academica"


def test_unknown_order_returns_400(adapter_client):
    client, _, _ = adapter_client
    response = client.post("/orders", json={
        "order": "OTRA_COSA",
        "context": {"cookie": "X", "requester": "test"},
    })
    assert response.status_code == 400


def test_health(adapter_client):
    client, _, _ = adapter_client
    assert client.get("/health").status_code == 200
