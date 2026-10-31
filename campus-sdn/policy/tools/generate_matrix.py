#!/usr/bin/env python3
"""Genera y verifica la matriz Rol x Permiso desde policy/permissions.yaml.

Uso:
    python3 generate_matrix.py                 # valida y muestra la matriz
    python3 generate_matrix.py --format md     # tabla Markdown
    python3 generate_matrix.py --format tex    # cuerpo LaTeX
    python3 generate_matrix.py --check         # compara con el corpus

La fuente de verdad es permissions.yaml. La matriz de los documentos del
corpus es una vista generada; --check falla si ambas divergen.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]          # raíz del repositorio
POLICY = BASE / "policy" / "permissions.yaml"
CORPUS = BASE.parent                                 # raíz del corpus
MATRIX_DOC = CORPUS / "implementation" / "02_matriz_rol_permiso.md"
TEX_DOC = CORPUS / "plan" / "propuestas" / "Arquitectura_SDN_Consolidada.tex"

ROLES = [
    ("academic", "Académico"),
    ("it_specialist", "Esp. TI"),
    ("network_admin", "Admin. Red"),
    ("super_admin", "Superadmin"),
]


def load_policy() -> dict:
    with POLICY.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate(policy: dict) -> list[str]:
    """Devuelve una lista de errores; vacía si la política es consistente."""
    errors: list[str] = []
    roles = policy.get("roles", {})
    permissions = policy.get("permissions", {})
    conditions = policy.get("conditions", {})
    assignments = policy.get("assignments", [])

    if set(roles) != {key for key, _ in ROLES}:
        errors.append(f"roles inesperados: {sorted(roles)}")

    seen: set[str] = set()
    pairs: dict[tuple[str, str], int] = {}
    for item in assignments:
        aid = item.get("id", "?")
        if aid in seen:
            errors.append(f"asignación duplicada: {aid}")
        seen.add(aid)

        role = item.get("role")
        permission = item.get("permission")
        if role not in roles:
            errors.append(f"{aid}: rol inexistente {role!r}")
        if permission not in permissions:
            errors.append(f"{aid}: permiso inexistente {permission!r}")

        for condition in item.get("conditions", []):
            if condition not in conditions:
                errors.append(f"{aid}: condición inexistente {condition!r}")

        key = (role, permission)
        pairs[key] = pairs.get(key, 0) + 1

    duplicates = [f"{role}/{permission}" for (role, permission), n in pairs.items() if n > 1]
    if duplicates:
        errors.append(f"asignaciones repetidas rol/permiso: {sorted(duplicates)}")

    for pid, spec in permissions.items():
        if spec.get("plane") not in {"pre_session", "network", "services"}:
            errors.append(f"{pid}: plano inválido {spec.get('plane')!r}")

    return errors


def cell_for(policy: dict, role: str, permission: str) -> str:
    spec = policy["permissions"][permission]
    plane = spec.get("plane")
    if plane == "pre_session":
        return "PRE"
    if plane == "network":
        # La etiqueta RED la fija el corpus (red de datos); se conserva
        # para que --check siga comparando contra la matriz del documento.
        return "RED"

    matches = [
        item
        for item in policy["assignments"]
        if item["role"] == role and item["permission"] == permission
    ]
    if not matches:
        return "—"
    item = matches[0]
    if item.get("effect", "permit") == "deny":
        return "—"
    conditions = item.get("conditions", [])
    return "+".join(conditions) if conditions else "P"


def rows(policy: dict) -> list[tuple[str, str, list[str]]]:
    result = []
    for pid, spec in policy["permissions"].items():
        cells = [cell_for(policy, role, pid) for role, _ in ROLES]
        result.append((pid, spec["name"], cells))
    return result


def format_md(policy: dict) -> str:
    header = "| ID | Permiso | " + " | ".join(label for _, label in ROLES) + " |"
    sep = "|---|---|---|---|---|---|"
    lines = [header, sep]
    for pid, name, cells in rows(policy):
        lines.append(f"| {pid} | {name} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def format_tex(policy: dict) -> str:
    lines = []
    for pid, name, cells in rows(policy):
        rendered = [
            r"\texttt{" + cell + "}" if cell not in {"—"} else "---"
            for cell in cells
        ]
        lines.append(f"{pid} {name} & " + " & ".join(rendered) + r"\\")
    return "\n".join(lines)


def parse_doc_matrix(path: Path) -> dict[str, list[str]]:
    """Extrae las filas de la matriz del documento Markdown."""
    found: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| P"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) != 6:
            continue
        found[parts[0]] = parts[2:]
    return found


def parse_tex_matrix(path: Path) -> list[str]:
    """Extrae el cuerpo de la matriz LaTeX (filas entre midrule y bottomrule)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.startswith(r"\begin{longtable}{p{0.30\linewidth}")
        ),
        None,
    )
    if start is None:
        return []

    body: list[str] = []
    inside = False
    for line in lines[start:]:
        stripped = line.strip()
        if stripped == r"\midrule":
            inside = True
            continue
        if stripped == r"\bottomrule":
            break
        if inside and stripped:
            body.append(stripped)
    return body


def check(policy: dict) -> int:
    if not MATRIX_DOC.exists():
        print(f"ERROR: no existe {MATRIX_DOC}", file=sys.stderr)
        return 1

    documented = parse_doc_matrix(MATRIX_DOC)
    generated = {pid: cells for pid, _, cells in rows(policy)}

    errors = 0
    for pid, cells in generated.items():
        if pid not in documented:
            print(f"FALTA en el documento: {pid}", file=sys.stderr)
            errors += 1
            continue
        if documented[pid] != cells:
            print(
                f"DIVERGE {pid}: documento={documented[pid]} yaml={cells}",
                file=sys.stderr,
            )
            errors += 1

    for pid in documented:
        if pid not in generated:
            print(f"SOBRA en el documento: {pid}", file=sys.stderr)
            errors += 1

    if not TEX_DOC.exists():
        print(f"ERROR: no existe {TEX_DOC}", file=sys.stderr)
        return 1

    tex_rows = parse_tex_matrix(TEX_DOC)
    generated_tex = format_tex(policy).splitlines()

    def tex_cells(rows):
        # Compara el identificador y las celdas, no el nombre: el corpus
        # muestra los nombres en español y el repositorio en inglés.
        result = {}
        for row in rows:
            pid, rest = row.split(" ", 1)
            _, cells = rest.split(" & ", 1)
            result[pid] = cells
        return result

    documented_tex = tex_cells(tex_rows)
    generated_cells = tex_cells(generated_tex)
    if documented_tex != generated_cells:
        errors += 1
        print("DIVERGE la matriz LaTeX del documento consolidado", file=sys.stderr)
        for pid in sorted(set(documented_tex) | set(generated_cells)):
            if documented_tex.get(pid) != generated_cells.get(pid):
                print(f"  yaml={generated_cells.get(pid)!r}", file=sys.stderr)
                print(f"  tex ={documented_tex.get(pid)!r}", file=sys.stderr)
                break
        if len(tex_rows) != len(generated_tex):
            print(
                f"  filas: yaml={len(generated_tex)} tex={len(tex_rows)}",
                file=sys.stderr,
            )

    if errors:
        return 1
    print(
        f"OK: {len(generated)} permisos coinciden con "
        f"{MATRIX_DOC.name} y la matriz LaTeX"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["md", "tex"], default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    policy = load_policy()
    errors = validate(policy)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.check:
        return check(policy)

    if args.format == "md":
        print(format_md(policy))
    elif args.format == "tex":
        print(format_tex(policy))
    else:
        print(
            f"OK: {len(policy['roles'])} roles, "
            f"{len(policy['permissions'])} permisos, "
            f"{len(policy['assignments'])} asignaciones, "
            f"{len(policy['conditions'])} condiciones"
        )
        print(format_md(policy))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
