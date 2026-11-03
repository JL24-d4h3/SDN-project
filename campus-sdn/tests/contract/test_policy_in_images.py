"""La política de permisos viaja dentro de las imágenes que la evalúan.

`sdn_common.authz` lee `policy/permissions.yaml` en cada decisión. Un
servicio que la usa y una imagen que no la copia fallan en el contenedor
aunque las pruebas locales pasen: esta prueba lo impide.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_services_using_authz_copy_policy_into_image():
    consumers = [path.parent for path in (ROOT / "services").glob("*/main.py")
                 if "sdn_common.authz" in path.read_text()]
    assert consumers
    for service in consumers:
        dockerfile = (service / "Dockerfile").read_text()
        assert "COPY policy /app/policy" in dockerfile, service.name


def test_policy_path_honors_environment(monkeypatch, tmp_path):
    from sdn_common import authz

    target = tmp_path / "permissions.yaml"
    target.write_text("assignments: []\n")
    monkeypatch.setenv("POLICY_PATH", str(target))
    assert authz._policy_path() == target
