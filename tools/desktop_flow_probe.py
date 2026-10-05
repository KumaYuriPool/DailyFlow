"""Development-only isolated desktop harness. No publication or production data.

Requires cryptography. It creates a disposable, locally trusted catalog, with
ephemeral signing keys kept only in memory. The real host reads its existing
provider profile; no key or profile is copied into the app or evidence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import re
import uuid
from datetime import datetime, timezone, timedelta
import time
import urllib.parse
import urllib.request

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def manifest_defaults(m):
    m = json.loads(json.dumps(m))
    m.setdefault("network", {"hosts": []})
    m.setdefault("storage", {})
    m["storage"].setdefault("max_bytes", None)
    m.setdefault("compute", {})
    m["compute"].setdefault("instruction_budget", None)
    m["compute"].setdefault("memory_bytes", None)
    m["integrity"].setdefault("signature", None)
    m.setdefault("agent", None)
    if m["agent"] is not None:
        m["agent"].setdefault("tools", [])
        m["agent"].setdefault("max_iterations", None)
        m["agent"].setdefault("token_budget", None)
        if m["agent"].get("model") is not None:
            m["agent"]["model"].setdefault("needs", [])
            m["agent"]["model"].setdefault("tier", "standard")
            m["agent"]["model"].setdefault("local_only", False)
    return m


def stage_local_catalog(bundle, apps):
    """Stage signed local code/catalog only; private signing keys stay in memory.

    The caller must hold its data-root lock. Existing application state is preserved.
    """
    apps = Path(apps).resolve()
    apps.mkdir(parents=True, exist_ok=True)
    stamp_date = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    staging = apps / (".dailyflow-stage-" + uuid.uuid4().hex)
    staging.mkdir()
    try:
        m = json.loads((Path(bundle) / "manifest.json").read_text(encoding="utf-8-sig"))
        app_id = m["id"]
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", app_id):
            raise ValueError("Invalid local app ID")
        app_dir = apps / app_id
        app_dir.mkdir(parents=True, exist_ok=True)
        if app_dir.resolve() != apps / app_id:
            raise ValueError("App directory may not redirect outside the launcher data root")
        staged_bundle = staging / "bundle"
        shutil.copytree(bundle, staged_bundle)
        hub = WORKSPACE / "OctoSense-App-Hub/target/release/hub.exe"
        subprocess.run([str(hub), "stamp", str(staged_bundle)], check=True, capture_output=True)
        subprocess.run([str(hub), "check", str(staged_bundle), "--allow-unsigned"], check=True, capture_output=True)
        m = manifest_defaults(json.loads((staged_bundle / "manifest.json").read_text(encoding="utf-8")))
        # The desktop also requires a publisher signature on the manifest.
        # These disposable keys are not a publisher identity or store release.
        publisher = Ed25519PrivateKey.generate()
        publisher_pub = publisher.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
        m["integrity"]["signature"] = None
        m["integrity"]["signature"] = {"key_id": "local-test-only", "value": publisher.sign(canonical(m)).hex()}
        (staged_bundle / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
        entry = {"manifest": m, "listing": None, "artifact": "local-test-only",
                 "publisher": "local-test-only", "publisher_key": publisher_pub,
                 "source": {"repository": "", "commit": ""},
                 "status": {"state": "offered"}, "admitted": stamp_date}
        catalog = {"schema": 1, "sequence": 1, "published": stamp_date, "entries": [entry],
                   "signature": None, "key": None}
        anchor, working = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
        anchor_pub = anchor.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
        working_pub = working.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        catalog["signature"] = working.sign(canonical(catalog)).hex()
        catalog["key"] = {"public": working_pub.hex(), "anchor_certificate": anchor.sign(working_pub).hex()}
        catalog_path = staging / "catalog.json"
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
        subprocess.run([str(hub), "verify", str(catalog_path), "--anchor", anchor_pub], check=True, capture_output=True)
        # Replace only the staged application code, never its state or account directories.
        destination = app_dir / "bundle"
        if destination.exists():
            if destination.resolve() != app_dir / "bundle":
                raise ValueError("Bundle directory may not redirect outside the app directory")
            destination.rename(staging / "previous-bundle")
        try:
            staged_bundle.rename(destination)
        except BaseException:
            if (staging / "previous-bundle").exists():
                (staging / "previous-bundle").rename(destination)
            raise
        os.replace(catalog_path, apps / "catalog.json")
        return app_id, destination, anchor_pub
    finally:
        # This exact directory was created above, and contains only staged code.
        if staging.resolve().parent != apps or not staging.name.startswith(".dailyflow-stage-"):
            raise RuntimeError("Refusing to clean an unexpected staging path")
        shutil.rmtree(staging)


class DesktopProbe:
    def __init__(self, bundle, output, core_dir=None, binary=None, seed_state=None):
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=False)
        self.apps = self.output / "apps"
        self.app_id, self.bundle, anchor_pub = stage_local_catalog(bundle, self.apps)
        if seed_state is not None:
            # Explicit synthetic state only, supplied by the event acceptance harness.
            for source in Path(seed_state).glob('state-*.json'):
                shutil.copyfile(source, self.apps / self.app_id / source.name)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]
        env = dict(os.environ, MAKEPAD_HIDE_WINDOWS="1", MAKEPAD_REMOTE=str(self.port),
                   OCTOSENSE_HOME=str(self.output / "home"), OCTOSENSE_APP_DATA=str(self.apps),
                   OCTOSENSE_HUB_ANCHOR=anchor_pub, OCTOSENSE_HUB=str(self.apps))
        # The model service needs no agent kernel. Do not launch one against
        # the person's profile directory during this direct-model probe.
        env.pop("OCTOS_APP_CORE_BIN", None)
        env.pop("MAKEPAD_WM_TEST_APP", None)
        self.profile = None
        self.profile_hash = None
        if core_dir:
            env["OCTOS_APP_CORE_DIR"] = str(Path(core_dir).resolve())
            self.profile = Path(core_dir) / "profiles/_main.json"
            self.profile_hash = hashlib.sha256(self.profile.read_bytes()).hexdigest()
        else:
            env["OCTOS_APP_CORE_DIR"] = str(self.output / "core")
        exe = Path(binary or WORKSPACE / "OctoSense/target/release/octosense.exe").resolve()
        self.log = (self.output / "desktop.log").open("w", encoding="utf-8")
        self.child = subprocess.Popen([str(exe), "--test-action", "launch-hub:" + self.app_id],
                                      cwd=WORKSPACE / "OctoSense", env=env,
                                      stdout=self.log, stderr=subprocess.STDOUT,
                                      creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        (self.output / "process.json").write_text(json.dumps({"pid": self.child.pid, "port": self.port}), encoding="utf-8")

    def request(self, path, **args):
        url = f"http://127.0.0.1:{self.port}/{path}?" + urllib.parse.urlencode(args)
        with urllib.request.urlopen(url, timeout=15) as response:
            return response.read()

    def snapshot(self):
        return json.loads(self.request("snap"))

    def wait_ready(self):
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if self.child.poll() is not None:
                raise RuntimeError(f"desktop exited {self.child.returncode}; see desktop.log")
            try:
                snap = self.snapshot()
                if any(w.get("i") == "date_jump" for w in snap.get("s", [])) and any(w.get("i") == "status" and w.get("t") != "读取中" for w in snap.get("s", [])):
                    return snap
            except (OSError, TimeoutError, ValueError):
                pass
            time.sleep(.3)
        raise TimeoutError("DailyFlow did not appear; see desktop.log")

    def stop(self):
        try:
            self.request("quit")
        except (OSError, TimeoutError):
            pass
        try:
            self.child.wait(timeout=8)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.wait(timeout=8)
        self.log.close()
        preserved = self.profile is None or hashlib.sha256(self.profile.read_bytes()).hexdigest() == self.profile_hash
        (self.output / "cleanup.json").write_text(json.dumps({"stopped": self.child.poll() is not None,
                                                              "provider_profile_unchanged": preserved}), encoding="utf-8")
        assert preserved, "Provider profile changed during the probe"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT / "bundle")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--core-dir", type=Path)
    parser.add_argument("--binary", type=Path)
    args = parser.parse_args()
    probe = DesktopProbe(args.bundle, args.output, args.core_dir, args.binary)
    try:
        snap = probe.wait_ready()
        (probe.output / "snapshot.json").write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"ready": True, "port": probe.port, "output": str(probe.output)}))
    finally:
        probe.stop()
