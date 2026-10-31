"""Monitor: métricas, líneas base y verificación de mitigaciones (F-06).

Consume del bus `DeviceConnected` (ubicaciones → `MAC_Moved`) y
`MitigationApplied` (verificación → `MitigationVerified`); publica
`MetricSample` hacia la Detección. Las tasas reales llegan con
sFlow/NetFlow y los contadores del switch (F-06 §2); el prototipo publica
muestras derivadas de los eventos observados, con esa limitación
declarada en los comentarios.
"""

import os
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

from sdn_common.app import create_app
from sdn_common.bus import consume_events, publish_event
from sdn_common.events import build_event, utc_now, validate_event

SERVICE = "monitor"
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "events"
QUEUE = "monitor"
BINDINGS = ["DeviceConnected", "MitigationApplied"]

locations: dict[str, dict] = {}          # mac → {switch, port}
samples = deque(maxlen=1000)             # MetricSample publicados
mitigations: dict[str, dict] = {}        # incidente → estado de verificación
seen_events = 0                          # contador de la ventana actual


def _bus_url() -> str:
    return os.environ.get("BUS_URL", "")


def _interval() -> int:
    return int(os.environ.get("SAMPLE_INTERVAL_S", "5"))


def _publish(event) -> None:
    # Sin bus no hay Monitor: se falla en voz alta, no se omite en
    # silencio. Las pruebas sustituyen publish_event.
    validate_event(event, SCHEMAS_DIR)
    publish_event(_bus_url(), event)


def handle_event(event: dict) -> bool:
    """Procesa un evento del bus; True si se aceptó."""
    event_type = event["type"]
    payload = event["payload"]
    global seen_events

    if event_type == "DeviceConnected":
        mac = payload["mac"]
        new_location = {"switch": payload["switch"], "port": payload["port"]}
        previous = locations.get(mac)
        if previous is not None and previous != new_location:
            _publish(build_event(
                "MAC_Moved",
                {"mac": mac, "previous_location": previous,
                 "new_location": new_location},
                sender=SERVICE,
                correlation={"device": mac},
            ))
        locations[mac] = new_location
        seen_events += 1
        return True

    if event_type == "MitigationApplied":
        # La verificación compara la muestra actual contra la del momento
        # de la aplicación (prototipo; con los contadores del switch, la
        # comparación es de tasas reales — F-06 §2).
        latest = samples[-1]["pps"] if samples else 0.0
        mitigations[payload["incident"]] = {
            "rules": payload["rules"],
            "applied_at": payload["applied_at"],
            "pps_before": latest,
        }
        return True

    return False


def sample_loop() -> None:
    """Publica un MetricSample por ventana, derivado de lo observado."""
    global seen_events
    window_s = _interval()
    while True:
        time.sleep(window_s)
        pps = seen_events / window_s
        seen_events = 0
        _publish(build_event(
            "MetricSample",
            {
                "destination": "aggregate",
                "window": f"{window_s}s",
                "pps": round(pps, 2),
                "bps": round(pps * 512 * 8, 2),  # paquete medio asumido
                "new_flows": 0,
                "distinct_sources": len(locations),
            },
            sender=SERVICE,
        ))


def verification_loop() -> None:
    """Cierra mitigaciones pendientes con MitigationVerified."""
    while True:
        time.sleep(_interval())
        now_s = utc_now()
        for incident, state in list(mitigations.items()):
            latest = samples[-1]["pps"] if samples else 0.0
            before = state["pps_before"]
            _publish(build_event(
                "MitigationVerified",
                {
                    "incident": incident,
                    "rates_before": {"pps": before, "bps": 0.0},
                    "rates_after": {"pps": latest, "bps": 0.0},
                    "meets_objective": latest < before or before == 0.0,
                },
                sender=SERVICE,
                correlation={"incident": incident},
            ))
            del mitigations[incident]
            _ = now_s


@asynccontextmanager
async def lifespan(_app):
    if _bus_url():
        threading.Thread(
            target=consume_events,
            args=(_bus_url(), QUEUE, BINDINGS, handle_event),
            daemon=True,
        ).start()
        threading.Thread(target=sample_loop, daemon=True).start()
        threading.Thread(target=verification_loop, daemon=True).start()
    yield


app = create_app(SERVICE, lifespan=lifespan)


@app.get("/metrics")
def get_metrics():
    """I7: muestras recientes (solo lectura)."""
    return {"metrics": list(samples)}


@app.get("/baselines")
def get_baselines():
    """I7: línea base observada (solo lectura)."""
    pps_values = [sample["pps"] for sample in samples]
    if not pps_values:
        return {"baselines": {"aggregate": {"mean": 0.0, "sigma": 0.0}}}
    mean = sum(pps_values) / len(pps_values)
    variance = sum((v - mean) ** 2 for v in pps_values) / len(pps_values)
    return {"baselines": {"aggregate": {
        "mean": round(mean, 2), "sigma": round(variance ** 0.5, 2)}}}
