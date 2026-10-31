#!/usr/bin/env python3
"""Valida policy/permissions.yaml contra su contrato y su integridad referencial.

Uso: ./validate.py [ruta-del-yaml]
El contrato estructural es contracts/policy/permissions.schema.json; si la
librería jsonschema está instalada se usa, y si no, se ejecuta la
verificación estructural propia. La integridad referencial entre bloques
(roles, permisos, condiciones, obligaciones y tipos de recurso) se
verifica siempre.

Sale con 0 si no hay errores; los avisos no fallan la validación.
"""

import json
import sys
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2]
SCHEMA = BASE / "contracts" / "policy" / "permissions.schema.json"
YAML_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "policy" / "permissions.yaml"

errors = []
warnings = []


def error(msg):
    errors.append(msg)


def warning(msg):
    warnings.append(msg)


def validate_structure(doc):
    required = [
        "version", "name", "defaults", "roles", "profiles",
        "profile_aliases", "resources", "conditions", "security_states",
        "permissions", "assignments", "rules", "delegations",
        "obligations", "priorities",
    ]
    for key in required:
        if key not in doc:
            error(f"falta la clave de primer nivel '{key}'")

    for key, value in doc.get("roles", {}).items():
        for field in ["name", "level", "population", "identity_source",
                      "mfa_required", "privileged_session"]:
            if field not in value:
                error(f"rol {key}: falta '{field}'")

    for key, value in doc.get("profiles", {}).items():
        for field in ["name", "type", "priority"]:
            if field not in value:
                error(f"perfil {key}: falta '{field}'")
        if value.get("type") not in ("fixed", "derived", "parameterized"):
            error(f"perfil {key}: tipo '{value.get('type')}' no reconocido")

    for key, value in doc.get("conditions", {}).items():
        if "on_failure" not in value:
            error(f"condición {key}: falta 'on_failure'")
        elif value["on_failure"] not in ("deny", "step_up"):
            error(f"condición {key}: on_failure '{value['on_failure']}' no reconocido")

    for key, value in doc.get("permissions", {}).items():
        for field in ["name", "plane", "verb", "resource_types",
                      "description"]:
            if field not in value:
                error(f"permiso {key}: falta '{field}'")
        if value.get("plane") not in ("pre_session", "network", "services"):
            error(f"permiso {key}: plano '{value.get('plane')}' no reconocido")

    for assignment in doc.get("assignments", []):
        for field in ["id", "role", "permission", "effect", "resources",
                      "conditions", "obligations"]:
            if field not in assignment:
                error(f"asignación {assignment.get('id', '?')}: falta '{field}'")

    for key, value in doc.get("obligations", {}).items():
        if "description" not in value:
            error(f"obligación {key}: falta 'description'")


def validate_references(doc):
    roles = set(doc.get("roles", {}))
    permissions = set(doc.get("permissions", {}))
    conditions = set(doc.get("conditions", {}))
    obligations = set(doc.get("obligations", {}))
    profiles = set(doc.get("profiles", {}))
    resource_types = set(doc.get("resources", {}).get("types", []))

    for key, value in doc.get("profiles", {}).items():
        if "from_role" in value and value["from_role"] not in roles:
            error(f"perfil {key}: from_role '{value['from_role']}' no existe")
        for perm in value.get("requires", []):
            if perm not in permissions:
                error(f"perfil {key}: requires '{perm}' no es un permiso")

    for alias, target in doc.get("profile_aliases", {}).items():
        if target not in profiles:
            error(f"alias {alias}: destino '{target}' no es un perfil")

    for key, value in doc.get("permissions", {}).items():
        for res_type in value.get("resource_types", []):
            if res_type not in resource_types:
                error(f"permiso {key}: tipo de recurso '{res_type}' fuera del catálogo")

    for assignment in doc.get("assignments", []):
        aid = assignment.get("id", "?")
        if assignment.get("role") not in roles:
            error(f"asignación {aid}: rol '{assignment.get('role')}' no existe")
        if assignment.get("permission") not in permissions:
            error(f"asignación {aid}: permiso '{assignment.get('permission')}' no existe")
        for cond in assignment.get("conditions", []):
            if cond not in conditions:
                error(f"asignación {aid}: condición '{cond}' no existe")
        for obligation in assignment.get("obligations", []):
            if obligation not in obligations:
                error(f"asignación {aid}: obligación '{obligation}' no existe")
        for res in assignment.get("resources", []):
            if res != "*" and res not in resource_types:
                error(f"asignación {aid}: recurso '{res}' fuera del catálogo")

    for rule in doc.get("rules", []):
        rid = rule.get("id", "?")
        for perm in rule.get("permissions", []):
            if perm != "*" and perm not in permissions:
                error(f"regla {rid}: permiso '{perm}' no existe")

    for delegation in doc.get("delegations", []):
        did = delegation.get("id", "?")
        if delegation.get("from") not in roles:
            error(f"delegación {did}: origen '{delegation.get('from')}' no existe")
        if delegation.get("to") not in roles:
            error(f"delegación {did}: destino '{delegation.get('to')}' no existe")
        for perm in delegation.get("permissions", []):
            if perm not in permissions:
                error(f"delegación {did}: permiso '{perm}' no existe")
        for obligation in delegation.get("obligations", []):
            if obligation not in obligations:
                error(f"delegación {did}: obligación '{obligation}' no existe")
        for res_type in delegation.get("resource_scope", []):
            if res_type not in resource_types:
                error(f"delegación {did}: recurso '{res_type}' fuera del catálogo")

    for constraint in doc.get("security_states", {}).get("hard_constraints", []):
        cid = constraint.get("id", "?")
        ref = constraint.get("requires")
        if ref and ref not in permissions and ref not in conditions:
            error(f"{cid}: 'requires' '{ref}' no existe en permisos ni "
                  f"condiciones")


def validate_with_jsonschema(doc):
    try:
        import jsonschema
    except ImportError:
        return "sin-jsonschema"
    schema = json.loads(SCHEMA.read_text())
    schema_errors = list(jsonschema.Draft7Validator(schema).iter_errors(doc))
    for schema_error in schema_errors:
        error(f"esquema: {'/'.join(str(part) for part in schema_error.path)}: "
              f"{schema_error.message}")
    return "ok"


def main():
    doc = yaml.safe_load(YAML_PATH.read_text())
    if not isinstance(doc, dict):
        print(f"ERROR: {YAML_PATH} no contiene un documento YAML válido")
        sys.exit(1)
    validate_structure(doc)
    status = validate_with_jsonschema(doc)
    if status == "sin-jsonschema":
        warning("jsonschema no instalada; se usó la verificación estructural "
                "propia")
    validate_references(doc)

    for w in warnings:
        print(f"aviso: {w}")
    for e in errors:
        print(f"error: {e}")
    print(f"avisos: {len(warnings)}; errores: {len(errors)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
