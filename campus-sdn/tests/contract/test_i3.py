"""Pruebas de contrato de la API del portal (I3).

La forma del contrato: las tres rutas del LLD 01_apis.md §5, con sus
métodos y sus respuestas de error estructuradas.
"""

from pathlib import Path

import yaml

API = Path(__file__).resolve().parents[2] / "contracts" / "api"


def load():
    return yaml.safe_load((API / "i3-portal.openapi.yaml").read_text())


def test_portal_routes():
    doc = load()
    assert set(doc["paths"]) == {"/login", "/logout", "/guest-register",
                                 "/elevation"}


def test_methods_per_route():
    paths = load()["paths"]
    assert {"get", "post"} <= set(paths["/login"])
    assert "post" in paths["/logout"]
    assert "post" in paths["/guest-register"]
    assert {"get", "post"} <= set(paths["/elevation"])


def test_structured_error():
    errors = load()["components"]["schemas"]["Error"]
    assert set(errors["required"]) == {"code", "message"}


def test_operations_in_english():
    doc = load()
    operations = {
        op["operationId"]
        for path in doc["paths"].values()
        for op in path.values()
        if isinstance(op, dict) and "operationId" in op
    }
    assert operations == {
        "getLoginSelector", "submitLogin", "submitLogout",
        "submitGuestRegistration", "getElevationScopes",
        "submitElevationRequest",
    }


def test_guest_population_in_selector():
    doc = load()
    login_get = doc["paths"]["/login"]["get"]["responses"]["200"]["content"]
    enum = login_get["application/json"]["schema"]["properties"][
        "populations"]["items"]["enum"]
    assert enum == ["university", "operations", "guest"]
