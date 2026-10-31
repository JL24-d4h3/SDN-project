"""Sensor adapter: traduce el espejo a `MetricSample` (la materia prima).

Lee el EVE JSON de Suricata (la NIC del espejo, H0) y agrega por ventana
y por destino: paquetes, bytes, flujos nuevos y fuentes distintas. Así la
Detección recibe tasas reales del plano de datos en lugar de las muestras
sintéticas del prototipo (F-06 §2). Sin el archivo del espejo, el
servicio espera y no publica nada.
"""

import json
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from sdn_common.app import create_app
from sdn_common.bus import publish_event
from sdn_common.events import build_event, validate_event

SERVICE = "sensor_adapter"
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "events"

windows: dict[str, dict] = {}  # destino → acumulados de la ventana


def _bus_url() -> str:
    return os.environ.get("BUS_URL", "")


def _eve_log() -> str:
    return os.environ.get("EVE_LOG", "/var/log/suricata/eve.json")


def _window_s() -> int:
    return int(os.environ.get("SENSOR_WINDOW_S", "10"))


def _publish(event) -> None:
    validate_event(event, SCHEMAS_DIR)
    publish_event(_bus_url(), event)


def handle_line(line: str) -> None:
    """Acumula una línea EVE de tipo flow en la ventana de su destino."""
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return
    if record.get("event_type") != "flow":
        return
    destination = record.get("dest_ip")
    if not destination:
        return
    window = windows.setdefault(destination, {
        "pkts": 0, "bytes": 0, "flows": set(), "sources": set(),
    })
    window["pkts"] += int(record.get("flow", {}).get("pkts_toserver", 0)) + \
        int(record.get("flow", {}).get("pkts_toclient", 0))
    window["bytes"] += int(record.get("flow", {}).get("bytes_toserver", 0)) + \
        int(record.get("flow", {}).get("bytes_toclient", 0))
    window["flows"].add(record.get("flow_id", ""))
    source = record.get("src_ip")
    if source:
        window["sources"].add(source)


def flush() -> None:
    """Publica un MetricSample por destino y reinicia las ventanas."""
    window_s = _window_s()
    for destination, window in list(windows.items()):
        _publish(build_event(
            "MetricSample",
            {
                "destination": destination,
                "window": f"{window_s}s",
                "pps": round(window["pkts"] / window_s, 2),
                "bps": round(window["bytes"] * 8 / window_s, 2),
                "new_flows": len(window["flows"]),
                "distinct_sources": len(window["sources"]),
            },
            sender=SERVICE,
        ))
    windows.clear()


def tail_loop() -> None:
    """Sigue el EVE log y descarga ventanas completas."""
    window_s = _window_s()
    last_flush = time.monotonic()
    while True:
        path = Path(_eve_log())
        if not path.exists():
            time.sleep(2)
            continue
        with path.open() as handle:
            handle.seek(0, 2)  # solo lo nuevo
            while True:
                line = handle.readline()
                if line:
                    handle_line(line)
                else:
                    time.sleep(0.5)
                if time.monotonic() - last_flush >= window_s:
                    flush()
                    last_flush = time.monotonic()


@asynccontextmanager
async def lifespan(_app):
    if _bus_url():
        threading.Thread(target=tail_loop, daemon=True).start()
    yield


app = create_app(SERVICE, lifespan=lifespan)
