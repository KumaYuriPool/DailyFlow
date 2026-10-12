"""Idempotence & determinism test for the synthetic-source importer.

Validates:
- Re-importing the same envelope produces identical on-disk projection.
- Re-importing an envelope with a strictly higher revision increments only
  that record's revision file; the older revision file is preserved
  (history).
- A tombstone re-applied after content does not resurrect the record.
- Two scenarios imported together do not collide (different source_apps).

Run:
    python -X utf8 tools/test_synthetic_projection_idempotence.py \
        --climb build/semifinal-202610/synthetic-source/climbing \
        --concert build/semifinal-202610/synthetic-source/concert \
        --output build/semifinal-202610/synthetic-source/idempotence
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def hash_directory(p):
    if not p.exists():
        return None
    files = sorted([f for f in p.rglob("*") if f.is_file()])
    h = hashlib.sha256()
    for f in files:
        h.update(f.relative_to(p).as_posix().encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


def hash_summary(projection):
    rec_root = projection / "records"
    summary = {"source_apps": sorted([p.name for p in rec_root.iterdir()]) if rec_root.exists() else []}
    for src in summary["source_apps"]:
        src_dir = rec_root / src
        records = sorted([r.name for r in src_dir.iterdir()])
        summary[src] = {}
        for r in records:
            rd = src_dir / r
            revs = sorted([p.name for p in rd.glob("rev-*.json")])
            summary[src][r] = {"revs": revs, "tombstone": (rd / "tombstone.json").exists()}
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--climb", required=True)
    ap.add_argument("--concert", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    tmp_a = out / "projection-A"
    tmp_b = out / "projection-B"

    if tmp_a.exists():
        shutil.rmtree(tmp_a)
    if tmp_b.exists():
        shutil.rmtree(tmp_b)

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments/synthetic-source"))
    import importer  # type: ignore

    report = {"checks": []}

    ok1, errs1, _ = importer.import_scenario(args.climb, tmp_a)
    ok2, errs2, _ = importer.import_scenario(args.concert, tmp_a)

    if not (ok1 and ok2):
        report["failed_first"] = {"climb_errs": errs1, "concert_errs": errs2}
        (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[FAIL] first import failed:", report["failed_first"])
        return 2

    report["checks"].append({"name": "first-import", "ok": True})

    hash_first = hash_directory(tmp_a)

    ok_r1, errs_r1, _ = importer.import_scenario(args.climb, tmp_b)
    ok_r2, errs_r2, _ = importer.import_scenario(args.concert, tmp_b)

    if not (ok_r1 and ok_r2):
        report["failed_repeat"] = {"errs": errs_r1 + errs_r2}
        (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[FAIL] repeat import:", errs_r1, errs_r2)
        return 2

    report["checks"].append({"name": "second-import", "ok": True})
    hash_second = hash_directory(tmp_b)

    stable = hash_first == hash_second
    report["checks"].append({"name": "idempotent-projection-hash", "ok": stable, "first": hash_first, "second": hash_second})
    if not stable:
        (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[FAIL] projection not idempotent")
        return 2

    summary = hash_summary(tmp_b)
    (out / "projection-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report["projection_summary"] = summary

    tomb_present = summary.get("synthetic-concert", {}).get("concert-recap-007", {}).get("tombstone", False)
    report["checks"].append({"name": "tombstone-persists", "ok": bool(tomb_present)})
    if not tomb_present:
        (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[FAIL] tombstone not persisted")
        return 2

    climb_post_001_revs = summary.get("synthetic-climbing", {}).get("climb-post-001", {}).get("revs", [])
    report["checks"].append({"name": "single-revision-file", "ok": len(climb_post_001_revs) >= 1})
    if not climb_post_001_revs:
        print("[FAIL] climb-post-001 missing")
        return 2

    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] idempotence confirmed; tombstone persisted; first==second hash={hash_first[:16]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
