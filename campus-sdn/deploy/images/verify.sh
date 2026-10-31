#!/usr/bin/env python3
"""Compara el digest local de cada imagen con el fijado en el lock.

Uso: ./verify.sh
Sale con 0 si todo coincide; con 1 si falta una imagen, un digest o la
coincidencia. No descarga nada.
"""

import json
import subprocess
import sys
from pathlib import Path

LOCK = Path(__file__).resolve().parent / "images.lock"


def main():
    lock = json.loads(LOCK.read_text())
    fail = False
    for img in lock["images"]:
        if not img["digest"]:
            print(f"SIN DIGEST {img['name']}: ejecute pull.sh primero")
            fail = True
            continue
        r = subprocess.run(
            ["docker", "image", "inspect", img["ref"],
             "--format", '{{join .RepoDigests ","}}'],
            text=True, capture_output=True)
        if r.returncode != 0:
            print(f"AUSENTE {img['name']}: {r.stderr.strip()}")
            fail = True
            continue
        digests = [d.strip().split("@", 1)[-1]
                   for d in r.stdout.split(",") if d.strip()]
        if img["digest"] in digests:
            print(f"OK {img['name']}")
        else:
            print(f"FALLO {img['name']}: local {digests}, "
                  f"esperado {img['digest']}")
            fail = True
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
