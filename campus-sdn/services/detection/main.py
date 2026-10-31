"""Detection: anomalías sobre la línea base (F-06 §2).

Consume `MetricSample` y mantiene una línea base por destino (media y
sigma, Welford). Si la desviación supera el umbral, publica
`AnomalyDetected`. La línea base solo se actualiza con muestras normales,
para que una ráfaga no envenene la referencia. El umbral se ajusta por
entorno; el valor fino sale de la medición (P33).
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from sdn_common.app import create_app
from sdn_common.bus import consume_events, publish_event
from sdn_common.events import build_event, validate_event

SERVICE = "detection"
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "events"
QUEUE = "detection"
BINDINGS = ["MetricSample"]

baseline: dict[str, dict] = {}  # destino → {n, mean, m2, sigma}


def _bus_url() -> str:
    return os.environ.get("BUS_URL", "")


def _threshold() -> float:
    return float(os.environ.get("DETECTION_SIGMA", "5"))


def _publish(event) -> None:
    # Sin bus no hay Detección: se falla en voz alta, no se omite en
    # silencio. Las pruebas sustituyen publish_event.
    validate_event(event, SCHEMAS_DIR)
    publish_event(_bus_url(), event)


def _update_baseline(destination: str, pps: float) -> None:
    stats = baseline.setdefault(destination, {"n": 0, "mean": 0.0,
                                             "m2": 0.0, "sigma": 0.0})
    stats["n"] += 1
    delta = pps - stats["mean"]
    stats["mean"] += delta / stats["n"]
    stats["m2"] += delta * (pps - stats["mean"])
    if stats["n"] > 1:
        stats["sigma"] = (stats["m2"] / (stats["n"] - 1)) ** 0.5


def handle_event(event: dict) -> bool:
    """Evalúa una muestra contra su línea base; True si se aceptó."""
    if event["type"] != "MetricSample":
        return False
    payload = event["payload"]
    destination = payload["destination"]
    stats = baseline.get(destination)

    if stats and stats["n"] > 2:
        mean = stats["mean"]
        sigma = stats["sigma"]
        if sigma > 0:
            deviation = (payload["pps"] - mean) / sigma
            anomalous = deviation >= _threshold()
        else:
            # Línea base constante (sigma 0): se compara la diferencia
            # absoluta contra un múltiplo de la media.
            deviation = payload["pps"] - mean
            anomalous = mean > 0 and deviation >= _threshold() * mean
        if anomalous:
            _publish(build_event(
                "AnomalyDetected",
                {
                    "type": "flood",
                    "target": {"ip": destination, "service": ""},
                    "origins": [],
                    "rates": {"pps": payload["pps"], "bps": payload["bps"]},
                    "baseline": {"mean": round(mean, 2),
                                 "sigma": round(sigma, 2)},
                    "deviation": round(deviation, 2),
                    "proposed_severity": "high",
                },
                sender=SERVICE,
            ))
            return True  # no se actualiza la base con la anomalía

    _update_baseline(destination, payload["pps"])
    return True


@asynccontextmanager
async def lifespan(_app):
    if _bus_url():
        import threading

        threading.Thread(
            target=consume_events,
            args=(_bus_url(), QUEUE, BINDINGS, handle_event),
            daemon=True,
        ).start()
    yield


app = create_app(SERVICE, lifespan=lifespan)
