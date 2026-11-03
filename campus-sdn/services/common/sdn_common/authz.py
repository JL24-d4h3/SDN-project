"""Autorización por la política (policy/permissions.yaml).

Cada servicio declara qué permiso exige su endpoint; la dependencia
valida la sesión contra el IAM (SSO) y evalúa la asignación rol→permiso
de la política con la condición C9 (el tipo de recurso está en los
recursos de la asignación). Las demás condiciones (C1–C11) las evaluará
el motor de política cuando se integre; aquí se aplica la forma cerrada.
Sin IAM_URL configurado, modo prototipo sin sesión. El YAML se relee en
cada decisión: es la fuente de verdad (etapa 0).
"""

import os
from pathlib import Path

import httpx
import yaml
from fastapi import Header, HTTPException

def _policy_path() -> Path:
    """La política se lee del árbol fuente, de `/app/policy` (imagen) o
    del directorio actual. En la imagen el paquete vive en
    `site-packages`, así que la ruta relativa al archivo no basta."""
    configured = os.environ.get("POLICY_PATH", "")
    if configured:
        return Path(configured)
    candidates = [
        Path(__file__).resolve().parents[3] / "policy" / "permissions.yaml",
        Path("/app/policy/permissions.yaml"),
        Path.cwd() / "policy" / "permissions.yaml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


POLICY_PATH = _policy_path()


def _allowed(role: str, permission: str, resource_type: str) -> bool:
    """La asignación rol→permiso cubre el tipo de recurso (C9)."""
    policy = yaml.safe_load(POLICY_PATH.read_text())
    for assignment in policy.get("assignments", []):
        if assignment["role"] != role:
            continue
        if assignment["permission"] != permission:
            continue
        resources = assignment["resources"]
        return resource_type in resources or "*" in resources
    return False


def require_permission(permission: str, resource_type: str):
    """Dependencia de FastAPI: sesión válida (SSO) + permiso sobre el
    tipo de recurso. 401 sin sesión, 403 con sesión sin permiso."""
    def dependency(session: str = Header(default="", alias="X-Session")):
        iam_url = os.environ.get("IAM_URL", "")
        if not iam_url:
            return None  # modo prototipo sin SSO
        if not session:
            raise HTTPException(status_code=401, detail="session required")
        try:
            response = httpx.get(f"{iam_url}/sessions/{session}", timeout=5)
        except httpx.HTTPError:
            raise HTTPException(status_code=503,
                                detail="identity unavailable")
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="session expired")
        role = response.json().get("profile_or_role")
        if not _allowed(role, permission, resource_type):
            raise HTTPException(status_code=403, detail="insufficient role")
        return session

    return dependency
