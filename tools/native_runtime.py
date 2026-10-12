"""Resolve the tested local native release, with the original paths as fallback."""
import hashlib
import json
import os
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
ACTIVE = WORKSPACE / "native-runtime-active.json"
LEGACY = {
    "shell": "OctoSense/target/release/octosense.exe",
    "hub": "OctoSense-App-Hub/target/release/hub.exe",
    "card_host": "OctoSense-App-Hub/target/release/card-host.exe",
    "kernel": "OctoSense/target/release/octos-kernel.exe",
}


def active_release():
    configured = os.environ.get("DAILYFLOW_RUNTIME_MANIFEST")
    manifest = Path(configured).resolve() if configured else ACTIVE
    if configured and not manifest.is_file():
        raise RuntimeError(f"Explicit runtime manifest is missing: {manifest}")
    if not manifest.exists():
        return None
    release = json.loads(manifest.read_text(encoding="utf-8"))
    if release.get("schema") != 1:
        raise RuntimeError("Unsupported native-runtime-active.json schema")
    return release


def binary(name):
    release = active_release()
    path = (WORKSPACE / (release["binaries"][name] if release else LEGACY[name])).resolve()
    if not path.is_file():
        raise RuntimeError(f"Native binary is missing: {path}")
    if os.environ.get("DAILYFLOW_RUNTIME_MANIFEST"):
        expected = (release.get("sha256") or {}).get(name)
        if not expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Explicit runtime binary hash mismatch: {name}: {path}")
    return path


def isolated_bundle():
    release = active_release()
    return bool(release and release.get("bundle_layout") == "isolated")


def verify_selection(name, selected):
    """An explicit acceptance manifest forbids silent per-test fallbacks."""
    selected = Path(selected).resolve()
    if os.environ.get("DAILYFLOW_RUNTIME_MANIFEST") and selected != binary(name):
        raise RuntimeError(f"Test tried to bypass the selected runtime: {name}: {selected}")
    return selected


def record_runtime(output):
    if os.environ.get("DAILYFLOW_RUNTIME_MANIFEST"):
        release = active_release()
        # A card-host-only phase may start before Shell/kernel finish building.
        # Requesting an absent component still fails in binary(); never fallback.
        for name in release["binaries"]:
            binary(name)
        Path(output, "runtime-provenance.json").write_text(
            json.dumps(release, ensure_ascii=False, indent=2), encoding="utf-8")
