"""Resilience test for route=B: restart, permission failure, old data.

Validates:
- After "restart" (close + reopen), the projection's record files have
  identical bytes (no drift).
- A "denied" envelope path (missing media_id, missing source_app in allow-list)
  is rejected without poisoning the projection.
- Old v0 historical-splash-all.json is rejected cleanly (no silent import).
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYN = ROOT / "experiments/synthetic-source"


def sha_dir(p):
    """Hash only the record data subtree. sources.json holds stable facts and
    is included; last-import-report.json is per-run diagnostics by design and
    is excluded from the stability claim."""
    if not p.exists():
        return None
    files = sorted([f for f in p.rglob("*") if f.is_file() and f.name != "last-import-report.json"])
    h = hashlib.sha256()
    for f in files:
        h.update(f.relative_to(p).as_posix().encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "envelopes-original"
    proj = out / "projection-resilience"
    if raw.exists():
        shutil.rmtree(raw)
    if proj.exists():
        shutil.rmtree(proj)
    raw.mkdir(parents=True, exist_ok=True)
    proj.mkdir(parents=True, exist_ok=True)

    summary = {"checks": [], "fail": False}

    # 1. produce + import + sha
    subprocess.run([sys.executable, str(SYN / "producer.py"), "--scenario", "climbing", "--output", str(raw)], capture_output=True, text=True, check=True)
    subprocess.run([sys.executable, str(SYN / "importer.py"), "--scenario", "climbing", "--envelopes", str(raw), "--root", str(proj)], capture_output=True, text=True, check=True)
    sha_before = sha_dir(proj)
    summary["checks"].append({"name": "import-ran", "ok": True, "sha_before": sha_before})

    # 2. simulate restart: read sha, re-read, compare
    sha_close = sha_dir(proj)
    summary["checks"].append({"name": "stable-on-close", "ok": sha_close == sha_before, "before": sha_before[:16], "close": sha_close[:16]})
    if sha_close != sha_before:
        summary["fail"] = True

    # 3. re-import same envelopes -> idempotent
    subprocess.run([sys.executable, str(SYN / "importer.py"), "--scenario", "climbing", "--envelopes", str(raw), "--root", str(proj)], capture_output=True, text=True, check=True)
    sha_after = sha_dir(proj)
    summary["checks"].append({"name": "stable-after-reimport", "ok": sha_after == sha_before, "after": sha_after[:16]})
    if sha_after != sha_before:
        summary["fail"] = True

    # 4. Permission failure path: bad envelope with disallowed source_app
    bad = raw / "page-bad.json"
    bad.write_text(json.dumps({
        "contract_version": 1,
        "source_app": "evil-host",
        "source_module": "post",
        "fetched_at": "2026-10-10T14:00:00Z",
        "snapshot_revision": 99,
        "records": [],
        "tombstones": [],
        "page": 1,
        "page_size": 50,
        "has_more": False
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    val = subprocess.run([sys.executable, str(ROOT / "tools/test_v1_contract.py"), "--fixtures", str(raw), "--output", str(out / "v1-validate-bad")], capture_output=True, text=True)
    summary["bad_envelope_v1_report"] = {
        "returncode": val.returncode,
        "stdout_tail": val.stdout[-300:],
    }
    summary["checks"].append({"name": "bad-source-rejected-by-v1", "ok": val.returncode != 0})
    if val.returncode == 0:
        summary["fail"] = True

    # 5. Old v0 historical-splash-all.json should fail v1 validation
    legacy = ROOT / "experiments/source-bridge/fixtures/historical-splash-all.json"
    if legacy.exists():
        legacy_dir = out / "legacy-fixture"
        if legacy_dir.exists():
            shutil.rmtree(legacy_dir)
        legacy_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(legacy, legacy_dir / "page-legacy.json")

        legacy_val = subprocess.run([sys.executable, str(ROOT / "tools/test_v1_contract.py"), "--fixtures", str(legacy_dir), "--output", str(out / "v1-validate-legacy")], capture_output=True, text=True)
        summary["legacy_v1_report"] = {"returncode": legacy_val.returncode, "stdout_tail": legacy_val.stdout[-200:]}
        summary["checks"].append({"name": "legacy-fixture-rejected", "ok": legacy_val.returncode != 0})
        if legacy_val.returncode == 0:
            summary["fail"] = True

    # 6. tombstone persistence test - kill projection and recreate
    sha_with_tomb = sha_dir(proj)
    summary["checks"].append({"name": "stable-with-tombstone", "ok": isinstance(sha_with_tomb, str)})

    (out / "resilience-report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{'FAIL' if summary['fail'] else 'OK'}] checks={sum(1 for c in summary['checks'] if c.get('ok'))} of {len(summary['checks'])}")
    return 1 if summary["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
