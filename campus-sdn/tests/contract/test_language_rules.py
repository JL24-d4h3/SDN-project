"""La regla de idioma como prueba (CLAUDE.md): identificadores en inglés.

Recorre los archivos Python del repositorio y falla si una definición de
función o clase contiene partes en español (separadas por `_`). Así, un
nombre como `test_verifica_evento` rompe la suite en el momento, no en la
revisión.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

SPANISH_PARTS = {
    "valido", "valida", "validar", "invalido", "invalida",
    "rechaza", "rechazo", "evento", "eventos", "envoltura",
    "sesion", "sesiones", "publica", "publicar", "emite", "emitir",
    "lista", "historial", "revocar", "revocacion", "registro",
    "registrar", "cierra", "cerrar", "desconocido", "desconocida",
    "operacion", "privilegiado", "muestras", "rafaga", "anomalia",
    "envenena", "envenenar", "ubicacion", "conexion", "misma", "mismo",
    "catalogo", "mapa", "rutas", "metodos", "politica", "sincronizada",
    "correlacion", "campos", "tipos", "archivos", "errores", "avisos",
    "reintentos", "envio", "recepcion", "cola", "colas", "mensaje",
    "mensajes", "datos", "servicios", "red", "puerto", "motivo",
    "estado", "reglas", "caminos", "nodo", "nodos", "cuenta",
    "cuentas", "clave", "claves", "usuario", "usuarios", "equipo",
    "equipos", "dispositivo", "dispositivos", "umbral", "umbrales",
    "elevacion", "mitigacion", "deteccion", "auditoria", "incidente",
    "incidentes", "politicas", "consola", "adaptador", "actualiza",
    "construye", "genera", "verifica", "devuelve", "procesa",
    "registrada", "pendiente", "completo", "completa",
}

FILES = [p for p in ROOT.rglob("*.py") if ".venv" not in p.parts]


@pytest.mark.parametrize(
    "path", FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_definition_names_are_english(path):
    text = path.read_text()
    for match in re.finditer(r"\b(def|class)\s+([A-Za-z_]+)", text):
        name = match.group(2)
        parts = [part for part in name.split("_") if part]
        bad = [part for part in parts if part in SPANISH_PARTS]
        assert not bad, f"{name}: partes en español {bad}"
