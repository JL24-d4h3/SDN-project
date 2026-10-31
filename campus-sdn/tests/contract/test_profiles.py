"""profiles.yaml es una vista derivada de permissions.yaml (plan 09 §6)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    return yaml.safe_load((ROOT / "policy" / name).read_text())


def test_profiles_match_policy():
    policy = load("permissions.yaml")
    profiles = load("profiles.yaml")
    assert set(profiles["profiles"]) == set(policy["profiles"])
    assert set(profiles["profile_aliases"]) == set(policy["profile_aliases"])
    assert profiles["version"] == policy["version"]
