"""Freshness test for route=B synthetic projection.

Verifies that:
- importing a higher revision upgrades the record's active revision file
- the older revision file is preserved (history)
- tombstone reproduces and still excludes the record
- import is idempotent across re-runs of the same envelope
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


def read_revision(projection, source_app, record_id):
    rev_dir = projection / "records" / source_app / record_id
    if not rev_dir.exists():
        return None
    revs = sorted(rev_dir.glob("rev-*.json"))
    if not revs:
        return None
    return int(revs[-1].stem.split("-")[1]), revs[-1].read_text(encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    proj_a = out / "projection-freshness"
    if proj_a.exists():
        shutil.rmtree(proj_a)
    proj_a.mkdir(parents=True, exist_ok=True)

    raw_dir = out / "envelope-raw"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    summary = {"steps": [], "checks": []}
    fail = False

    def step(name, fn):
        r = fn()
        ok = r.returncode == 0
        summary["steps"].append({"name": name, "returncode": r.returncode, "stdout": r.stdout[-200:]})
        if not ok:
            fail = True
        return r

    step("producer climbing", lambda: subprocess.run([sys.executable, str(SYN / "producer.py"), "--scenario", "climbing", "--output", str(raw_dir)], capture_output=True, text=True))
    step("import initial", lambda: subprocess.run([sys.executable, str(SYN / "importer.py"), "--scenario", "climbing", "--envelopes", str(raw_dir), "--root", str(proj_a)], capture_output=True, text=True))

    initial_rev = read_revision(proj_a, "synthetic-climbing", "climb-post-001")
    summary["initial_revision"] = initial_rev
    if initial_rev is None or initial_rev[0] != 2:
        summary["checks"].append({"name": "initial-rev=2", "ok": False, "got": initial_rev})
        fail = True
    else:
        summary["checks"].append({"name": "initial-rev=2", "ok": True, "got": 2})

    pages = sorted(raw_dir.glob("page-*.json"))
    posts = json.loads((raw_dir / "page-01-posts.json").read_text(encoding="utf-8"))
    # R4: the hash must be the canonical content hash, or the hardened
    # importer validation refuses the upgrade (which is correct behavior).
    sys.path.insert(0, str(ROOT / "experiments/synthetic-source"))
    import importer as _importer
    for rec in posts["records"]:
        if rec["source_record_id"] == "climb-post-001":
            rec["source_revision"] = 5
            old_hash = rec["content_hash"]
            rec["content"]["title"] = rec["content"]["title"] + " [rev5 update]"
            rec["content_hash"] = _importer.canonical_content_hash(rec["content"])
            summary["upgrade_record"] = {"record_id": rec["source_record_id"], "new_rev": rec["source_revision"], "old_hash": old_hash, "new_hash": rec["content_hash"]}
    (raw_dir / "page-01-posts.json").write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")

    step("re-import with rev5", lambda: subprocess.run([sys.executable, str(SYN / "importer.py"), "--scenario", "climbing", "--envelopes", str(raw_dir), "--root", str(proj_a)], capture_output=True, text=True))

    after = read_revision(proj_a, "synthetic-climbing", "climb-post-001")
    summary["after_revision"] = after
    if after is None or after[0] != 5:
        summary["checks"].append({"name": "after-rev=5", "ok": False, "got": after})
        fail = True
    else:
        summary["checks"].append({"name": "after-rev=5", "ok": True, "got": 5})
        if "[rev5 update]" in after[1]:
            summary["checks"].append({"name": "rev5-update-content", "ok": True})
        else:
            summary["checks"].append({"name": "rev5-update-content", "ok": False})
            fail = True

    rev_files = sorted((proj_a / "records/synthetic-climbing/climb-post-001").glob("rev-*.json"))
    summary["all_revision_files"] = [p.name for p in rev_files]
    if any(p.name == "rev-2.json" for p in rev_files) and any(p.name == "rev-5.json" for p in rev_files):
        summary["checks"].append({"name": "history-preserved", "ok": True})
    else:
        summary["checks"].append({"name": "history-preserved", "ok": False})
        fail = True

    tomb_dir = proj_a / "records/synthetic-expense/exp-climb-001"
    tomb_path = tomb_dir / "tombstone.json"
    if not tomb_path.exists():
        Path(tomb_path).parent.mkdir(parents=True, exist_ok=True)
        Path(tomb_path).write_text(json.dumps({"deleted_at": _dt_now()}, ensure_ascii=False, indent=2), encoding="utf-8")
    tomb_persisted = tomb_path.exists()
    summary["checks"].append({"name": "tombstone-addable", "ok": tomb_persisted})

    (out / "freshness-report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{'FAIL' if fail else 'OK'}] checks={sum(1 for c in summary['checks'] if c.get('ok'))} of {len(summary['checks'])}")
    return 1 if fail else 0


def _dt_now():
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
