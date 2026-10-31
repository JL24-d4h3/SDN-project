#!/usr/bin/env python3
"""Descarga las imágenes del lock y fija el digest cuando falta.

Uso: ./pull.sh
Ejecutar en la máquina con internet. Si el digest ya está fijado, descarga
por digest; si no, descarga por referencia y lo fija en images.lock.
"""

import json
import subprocess
import sys
from pathlib import Path

LOCK = Path(__file__).resolve().parent / "images.lock"


def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)


def main():
    lock = json.loads(LOCK.read_text())
    for img in lock["images"]:
        if img["digest"]:
            ref = f'{img["ref"].split("@", 1)[0]}@{img["digest"]}'
        else:
            ref = img["ref"]
        r = run(["docker", "pull", ref])
        if r.returncode != 0:
            print(f"FALLO {img['name']}: {r.stderr.strip()}")
            sys.exit(1)
        r = run(["docker", "image", "inspect", img["ref"],
                 "--format", "{{index .RepoDigests 0}}"])
        if r.returncode != 0 or not r.stdout.strip():
            print(f"FALLO digest de {img['name']}: {r.stderr.strip()}")
            sys.exit(1)
        digest = r.stdout.strip().split("@", 1)[-1]
        if not img["digest"]:
            img["digest"] = digest
            LOCK.write_text(json.dumps(lock, indent=2, ensure_ascii=False)
                            + "\n")
            print(f"fijado digest {img['name']} = {digest}")
        elif digest != img["digest"]:
            print(f"FALLO {img['name']}: el digest descargado no coincide "
                  f"con el fijado")
            sys.exit(1)
        else:
            print(f"OK {img['name']} {digest[:19]}…")
    print("todas las imágenes listas y verificadas")


if __name__ == "__main__":
    main()
