"""Pruebas de contrato de la política (etapa 0).

La política operativa (valores en inglés) debe validar sin errores y
permanecer estructuralmente sincronizada con su gemelo histórico del
corpus (en español): mismas claves de permisos y condiciones, misma
cantidad de roles, perfiles y obligaciones, y mismos IDs de asignaciones,
reglas y delegaciones. La correspondencia de valores está en
policy/README.md.
"""

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "policy" / "tools" / "validate.py"
OPERATIVE = ROOT / "policy" / "permissions.yaml"
HISTORICAL = ROOT.parent / "implementation" / "policy" / "permisos.yaml"


def load(path):
    return yaml.safe_load(path.read_text())


def test_policy_validates():
    result = subprocess.run(
        [sys.executable, str(VALIDATE)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "errores: 0" in result.stdout


def test_synced_with_corpus():
    operative = load(OPERATIVE)
    historical = load(HISTORICAL)

    # Bloques cuyas claves no cambiaron: deben ser idénticas.
    for block in ["permissions", "conditions"]:
        assert set(operative[block]) == set(historical[block]), block

    # Bloques cuyas claves se tradujeron: misma cantidad.
    for block in ["roles", "profiles", "obligations", "profile_aliases"]:
        assert len(operative[block]) == len(historical[block]), block

    # Bloques por ID: mismos identificadores en ambas copias.
    for block in ["assignments", "rules", "delegations"]:
        ids_operative = {item["id"] for item in operative[block]}
        ids_historical = {item["id"] for item in historical[block]}
        assert ids_operative == ids_historical, block
