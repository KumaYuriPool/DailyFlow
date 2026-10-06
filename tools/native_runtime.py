"""Resolve the tested local native release, with the original paths as fallback."""
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
ACTIVE = WORKSPACE / "native-runtime-active.json"
LEGACY = {
    "shell": "OctoSense/target/release/octosense.exe",
    "hub": "OctoSense-App-Hub/target/release/hub.exe",
    "card_host": "OctoSense-App-Hub/target/release/card-host.exe",
}


def active_release():
    if not ACTIVE.exists():
        return None
    release = json.loads(ACTIVE.read_text(encoding="utf-8"))
    if release.get("schema") != 1:
        raise RuntimeError("Unsupported native-runtime-active.json schema")
    return release


def binary(name):
    release = active_release()
    path = (WORKSPACE / (release["binaries"][name] if release else LEGACY[name])).resolve()
    if not path.is_file():
        raise RuntimeError(f"Native binary is missing: {path}")
    return path


def isolated_bundle():
    release = active_release()
    return bool(release and release.get("bundle_layout") == "isolated")
