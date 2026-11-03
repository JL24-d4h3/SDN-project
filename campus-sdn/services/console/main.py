"""Console: alertas en vivo y agregación de las I7.

Consume las alertas del bus (`AnomalyDetected`, `IncidentOpened`,
`DeviceRegistered`, `DeviceRevoked`) y las sirve a la interfaz del
operador. La sesión del operador es el SSO (F-03 §4): con IAM_URL
configurado, cada petición valida su sesión contra el IAM; sin él, el
prototipo opera sin SSO (limitación declarada).
"""

import os
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends
from fastapi.responses import HTMLResponse

from sdn_common.app import create_app
from sdn_common.authz import require_permission
from sdn_common.bus import consume_events

SERVICE = "console"
QUEUE = "console"
BINDINGS = ["AnomalyDetected", "IncidentOpened", "DeviceRegistered",
            "DeviceRevoked"]

alerts = deque(maxlen=200)

UI_HTML = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Consola — campus-sdn</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:system-ui;max-width:34rem;margin:2rem auto;padding:0 1rem;
     background:#f4f4f5;color:#18181b}
h1{font-size:1.3rem}
.card{background:#fff;padding:1.2rem;border-radius:8px;margin-bottom:1rem}
label{display:block;margin:.6rem 0 .2rem;font-size:.9rem}
input{width:100%;padding:.5rem;box-sizing:border-box}
button{margin-top:.8rem;padding:.55rem 1.1rem;cursor:pointer}
#result{white-space:pre-wrap;background:#18181b;color:#d4d4d8;
        padding:.8rem;border-radius:8px;font-size:.85rem;min-height:2rem}
.ok{color:#4ade80}.ko{color:#f87171}
</style>
</head>
<body>
<h1>Consola del operador</h1>
<div class="card">
<label>Token de sesión (del login en el portal)</label>
<input id="session" placeholder="pega aquí el identificador de la sesión">
<button id="go">Consultar alertas</button>
<p id="status"></p>
</div>
<pre id="result"></pre>
<script>
const result = document.getElementById('result');
const status = document.getElementById('status');
document.getElementById('go').onclick = async () => {
  const session = document.getElementById('session').value;
  const response = await fetch('/alerts', {
    headers: {'X-Session': session},
  });
  status.textContent = 'HTTP ' + response.status +
    (response.status === 200 ? ' — autorizado (rol con P09)'
     : response.status === 403 ? ' — denegado: el rol no tiene P09'
     : response.status === 401 ? ' — sin sesión válida'
     : '');
  status.className = response.status === 200 ? 'ok' : 'ko';
  result.textContent = JSON.stringify(await response.json(), null, 2);
};
</script>
</body>
</html>"""


def _bus_url() -> str:
    return os.environ.get("BUS_URL", "")


def handle_event(event: dict) -> bool:
    if event["type"] in BINDINGS:
        alerts.appendleft(event)
        return True
    return False


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


@app.get("/", response_class=HTMLResponse)
def ui():
    """La página de la consola: consulta /alerts con el token de sesión."""
    return UI_HTML


@app.get("/alerts")
def get_alerts(_=Depends(require_permission("P09", "alert"))):
    """Alertas en vivo para la interfaz del operador (P09: TI, Admin, SA)."""
    return {"alerts": list(alerts)}
