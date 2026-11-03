"""Las imágenes instalan todo lo que el código del servicio importa.

Un import perezoso dentro de una función pasa las pruebas locales (el
venv de la laptop tiene de todo) y revienta en el contenedor si el
Dockerfile no lo instala: le pasó al IAM con httpx. Esta prueba exige
que cada import de terceros del servicio esté cubierto por la línea de
pip de su Dockerfile o por las dependencias de sdn-common.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

MODULE_TO_PIP = {
    "fastapi": "fastapi",
    "httpx": "httpx",
    "pika": "pika",
    "yaml": "pyyaml",
    "pyotp": "pyotp",
    "bcrypt": "bcrypt",
    "pyrad": "pyrad",
    "jsonschema": "jsonschema",
    "uuid6": "uuid6",
}


def _imports(source: str) -> set[str]:
    found = set()
    for line in source.splitlines():
        match = re.match(r"\s*(?:import|from)\s+([a-zA-Z0-9_]+)", line)
        if match:
            found.add(match.group(1))
    return found


def _common_deps() -> set[str]:
    pyproject = (ROOT / "services/common/pyproject.toml").read_text()
    block = re.search(r"dependencies\s*=\s*\[(.*?)\]", pyproject, re.S)
    return set(re.findall(r'"([a-z0-9_-]+)"', block.group(1)))


def test_each_service_image_covers_its_imports():
    common = _common_deps()
    assert "httpx" in common
    for main in sorted((ROOT / "services").glob("*/main.py")):
        service = main.parent
        if not (service / "Dockerfile").exists():
            continue
        dockerfile = (service / "Dockerfile").read_text()
        pip_line = next(line for line in dockerfile.splitlines()
                        if line.startswith("RUN pip install"))
        covered = set(re.findall(r'"([a-z0-9_-]+)"', pip_line))
        covered |= {token for token in pip_line.split()
                    if re.fullmatch(r"[a-z0-9_.-]+", token)}
        required = {MODULE_TO_PIP[m] for m in _imports(main.read_text())
                    if m in MODULE_TO_PIP}
        missing = {pkg for pkg in required
                   if pkg not in covered and pkg not in common}
        assert not missing, f"{service.name} importa {missing} sin instalarlos"
