#!/usr/bin/env bash
# Carga los bundles en el demonio Docker local y verifica la suma.
# Uso: ./load.sh [nombre nombre...]   (sin argumentos, carga todos)
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLES="$DIR/bundles"

if [ ! -d "$BUNDLES" ]; then
  echo "no existe $BUNDLES; copie los bundles a la VM antes de cargar" >&2
  exit 1
fi

if [ "$#" -gt 0 ]; then
  TARS=()
  for n in "$@"; do TARS+=("$BUNDLES/$n.tar"); done
else
  mapfile -t TARS < <(find "$BUNDLES" -maxdepth 1 -name '*.tar' | sort)
fi

[ "${#TARS[@]}" -gt 0 ] || { echo "no hay bundles en $BUNDLES" >&2; exit 1; }

for tar in "${TARS[@]}"; do
  [ -f "$tar" ] || { echo "no existe $tar" >&2; exit 1; }
  if [ -f "$tar.sha256" ]; then
    (cd "$BUNDLES" && sha256sum -c --quiet "$(basename "$tar").sha256")
  fi
  docker load -i "$tar"
done

echo "carga completa"
