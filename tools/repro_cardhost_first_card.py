"""Reproduce the card-host first-card `app_tools.dispatch@1` admission ordering.

Launches the given card-host binary with the production DailyFlow bundle in a
fresh, isolated app-data root (hidden window, remote control port), then polls
the live UI for either:
  - refusal: any widget text containing `app_tools.dispatch` (the admission
    gate ran before the card runner registered its tool ABI), or
  - admission: the app's own readiness text.

Usage:
  python -X utf8 tools/repro_cardhost_first_card.py --binary <card-host.exe> --output <dir>

Writes result.json (verdict, binary sha256), snapshot.json and runtime.log.
"""
import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

REFUSAL_TITLE = "card-host refused this bundle"
REFUSAL_REASON = "needs a host implementing"
READY = "本地数据已就绪"


def remote_snapshot(port):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/snap", timeout=12) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    binary = Path(args.binary).resolve()
    out = Path(args.output).resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists(), 'Use a fresh build output'
    out.mkdir(parents=True)
    bundle = out / "bundle"
    shutil.copytree(ROOT / "bundle", bundle)
    apps = out / "apps"
    apps.mkdir()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    log = (out / "runtime.log").open("w", encoding="utf8")
    child = subprocess.Popen(
        [str(binary), "--bundle", str(bundle), "--app-data", str(apps),
         "--allow-unsigned", "--stamp", "--size", "1280x900"],
        stdout=log, stderr=subprocess.STDOUT,
        env=dict(os.environ, MAKEPAD_HIDE_WINDOWS="1", MAKEPAD_REMOTE=str(port)),
        creationflags=subprocess.CREATE_NO_WINDOW)

    verdict, detail, snap = "timeout", "", {}
    deadline = time.time() + args.timeout
    try:
        while time.time() < deadline:
            if child.poll() is not None:
                verdict, detail = "exited", f"process exited code={child.returncode}"
                break
            try:
                snap = remote_snapshot(port)
                texts = [w.get("t", "") for w in snap.get("s", [])
                         if isinstance(w, dict) and w.get('ty') in ('Label', 'Button', 'TextInput')]
                joined = "\n".join(texts)
                if REFUSAL_TITLE in texts:
                    verdict = "refused"
                    reason = next((t for t in texts if REFUSAL_REASON in t), "")
                    tail = next((texts[i + 1] for i, t in enumerate(texts)
                                 if REFUSAL_REASON in t and i + 1 < len(texts)), "")
                    detail = f"{reason} {tail}".strip()
                    break
                if READY in texts:
                    verdict = "admitted"
                    detail = "app reached readiness"
                    break
            except (OSError, ValueError):
                pass
            time.sleep(0.3)
    finally:
        child.terminate()
        try:
            child.wait(10)
        except subprocess.TimeoutExpired:
            child.kill()
        log.close()

    (out / "snapshot.json").write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    result = {
        "binary": str(binary),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "verdict": verdict,
        "detail": detail,
    }
    (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if verdict == "admitted" else 1)


if __name__ == "__main__":
    main()
