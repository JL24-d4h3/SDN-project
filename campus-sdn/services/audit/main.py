"""Audit: registro de todo lo que ocurre.

Consume todo el catálogo del bus (cola propia con enlace `#`, LLD
02_eventos §4). Un salto en la secuencia de un incidente se registra
como hueco declarado — jamás se oculta (P11). La persistencia llega con
bd_politicas; el prototipo guarda en memoria con tope.
"""

import os
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

from sdn_common.app import create_app
from sdn_common.bus import consume_events
from sdn_common.events import utc_now

SERVICE = "audit"
QUEUE = "audit"
BINDINGS = ["*"]

records = deque(maxlen=10000)
sequences: dict[str, int] = {}


def _bus_url() -> str:
    return os.environ.get("BUS_URL", "")


def handle_event(event: dict) -> bool:
    """Registra el evento; los huecos de secuencia quedan declarados."""
    incident = (event.get("correlation") or {}).get("incident")
    sequence = event.get("sequence")
    if incident and sequence is not None:
        expected = sequences.get(incident, 0) + 1
        if sequence != expected:
            records.append({
                "type": "gap-declared",
                "incident": incident,
                "expected": expected,
                "received": sequence,
                "at": utc_now(),
            })
        sequences[incident] = sequence
    records.append(event)
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


@app.get("/events")
def get_events(since: str = "", actor: str = "", cursor: int = 0,
               limit: int = 100):
    """I7: consulta de eventos (solo lectura; paginación por cursor)."""
    filtered = [record for record in records
                if (not actor or record.get("sender") == actor)
                and (not since or record.get("timestamp", "") >= since)]
    page = filtered[cursor:cursor + limit]
    return {"data": page, "cursor": cursor + len(page),
            "total": len(filtered)}
