#!/usr/bin/env python3
"""Empaqueta las imágenes del lock en bundles/ con su suma de comprobación.

Uso: ./save.sh
Ejecutar después de pull.sh y verify.sh, en la máquina con internet. Deja
en bundles/ un .tar y un .tar.sha256 por imagen; los bundles no se
versionan y se copian al slice para cargarlos con load.sh.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOCK = BASE / "images.lock"
BUNDLES = BASE / "bundles"


def main():
    BUNDLES.mkdir(exist_ok=True)
    lock = json.loads(LOCK.read_text())
    for img in lock["images"]:
        tar = BUNDLES / f'{img["name"]}.tar'
        r = subprocess.run(["docker", "save", img["ref"], "-o", str(tar)],
                           text=True, capture_output=True)
        if r.returncode != 0:
            print(f"FALLO {img['name']}: {r.stderr.strip()}")
            sys.exit(1)
        digest = hashlib.sha256(tar.read_bytes()).hexdigest()
        (BUNDLES / f'{img["name"]}.tar.sha256').write_text(
            f"{digest}  {tar.name}\n")
        size = tar.stat().st_size / 1024 / 1024
        print(f"OK {img['name']}: {size:.0f} MB")
    print(f"bundles listos en {BUNDLES}")


if __name__ == "__main__":
    main()
