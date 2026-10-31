#!/usr/bin/env python3
"""Deriva policy/profiles.yaml desde policy/permissions.yaml.

Los perfiles viven en el bloque `profiles` de la política; este archivo
es la vista que los servicios consumen por separado (plan 09 §6). Se
regenera con cada cambio de la política: la prueba de contrato
test_profiles.py verifica que no diverjan.
"""

import sys
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]
POLICY = BASE / "policy" / "permissions.yaml"
PROFILES = BASE / "policy" / "profiles.yaml"


def main() -> int:
    doc = yaml.safe_load(POLICY.read_text())
    profiles = doc.get("profiles", {})
    aliases = doc.get("profile_aliases", {})
    PROFILES.write_text(yaml.safe_dump(
        {"version": doc.get("version"), "profiles": profiles,
         "profile_aliases": aliases},
        sort_keys=False, allow_unicode=True))
    print(f"{PROFILES.name}: {len(profiles)} perfiles, "
          f"versión {doc.get('version')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
