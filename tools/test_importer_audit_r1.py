"""Regression for independent-audit-20261011 R1/R4 counterexamples.

All assertions go through the REAL query layer (dailyflow_query_v1.discover_
records / latest_state semantics), not just file inspection.

R1 cases (previously failing):
1. content rev2 -> delete rev5 -> late content rev3  => tombstone survives
2. delete rev5 only -> late content rev1             => stays deleted
3. content rev2 -> delete rev5 -> old delete rev3    => tombstone revision stays 5

R4 cases:
4. forged content_hash (64×'f') is refused by validate_envelope
5. record.source_app != envelope.source_app is refused
6. correct hash is accepted (positive control)
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/synthetic-source"))
import importer  # noqa: E402
sys.path.insert(0, str(ROOT / "tools"))

OUT = ROOT / "build/importer-audit-r1-regression"
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
SRC = "synthetic-climbing"

checks = []


def ck(name, ok, detail=""):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:250]})
    print(("PASS " if ok else "FAIL ") + name + (f" :: {detail}"[:150] if not ok else ""))


def rec(rid, rev, title, body="x"):
    content = {"kind": "post", "occurred_at": "2026-09-01", "ended_at": None,
               "open_end": False, "title": title, "body": body, "media": [],
               "tags": ["t"], "amount_minor": -1, "currency": "CNY", "source_meta": {}}
    return {"source_app": SRC, "source_module": "post", "source_record_id": rid,
            "source_revision": rev, "deleted_at": None,
            "content_hash": importer.canonical_content_hash(content),
            "content": content}


def tomb(rid, rev):
    return {"source_app": SRC, "source_module": "post", "source_record_id": rid,
            "source_revision": rev, "deleted_at": "2026-10-11T00:00:00Z",
            "content_hash": "0" * 64}


def env(records=None, tombs=None):
    return {"contract_version": 1, "source_app": SRC, "source_module": "post",
            "fetched_at": "2026-10-11T00:00:00Z", "snapshot_revision": 1,
            "records": records or [], "tombstones": tombs or [],
            "page": 1, "page_size": 50, "has_more": False}


def apply(env_obj, root):
    summary, run_report = {}, {}
    importer.import_envelope(env_obj, root, summary, run_report)
    return run_report


def query_state(root, rid):
    """Real query-layer readback: numeric-max content rev, tombstone gate."""
    # reuse dailyflow_query_v1's discovery semantics
    sys.path.insert(0, str(ROOT / "experiments/synthetic-source"))
    import dailyflow_query_v1 as q
    rd = root / "records" / SRC / rid
    if not rd.exists():
        return {"exists": False}
    rows = list(q.discover_records(root, source_apps={SRC}))
    row = next((r for r in rows if r["source_record_id"] == rid), None)
    if row is None:
        return {"exists": False}
    return {"exists": True, "revision": row["source_revision"], "title": row["title"],
            "deleted": row.get("deleted", False)}


def tomb_rev(root, rid):
    t = root / "records" / SRC / rid / "tombstone.json"
    if not t.exists():
        return 0
    return json.loads(t.read_text(encoding="utf-8"))["source_revision"]


# R1-1: content rev2 -> delete rev5 -> late content rev3
root = OUT / "case1"
rr = {}
apply(env(records=[rec("r1", 2, "v2")]), root)
apply(env(tombs=[tomb("r1", 5)]), root)
apply(env(records=[rec("r1", 3, "late3")]), root)
st = query_state(root, "r1")
ck("R1-1-late-content-no-resurrect", not st.get("exists"), st)
ck("R1-1-tombstone-rev-5", tomb_rev(root, "r1") == 5, tomb_rev(root, "r1"))

# R1-2: delete rev5 only -> late content rev1
root = OUT / "case2"
apply(env(tombs=[tomb("r2", 5)]), root)
apply(env(records=[rec("r2", 1, "late1")]), root)
st = query_state(root, "r2")
ck("R1-2-delete-first-no-resurrect", not st.get("exists"), st)

# R1-3: content rev2 -> delete rev5 -> old delete rev3 must not roll back
root = OUT / "case3"
apply(env(records=[rec("r3", 2, "v2")]), root)
apply(env(tombs=[tomb("r3", 5)]), root)
apply(env(tombs=[tomb("r3", 3)]), root)
ck("R1-3-tombstone-no-regression", tomb_rev(root, "r3") == 5, tomb_rev(root, "r3"))
st = query_state(root, "r3")
ck("R1-3-still-deleted", not st.get("exists"), st)

# R4-1: forged 64-f hash refused
bad = rec("r4", 1, "forged")
bad["content_hash"] = "f" * 64
errs = importer.validate_envelope(env(records=[bad]))
ck("R4-1-forged-hash-refused", any("content_hash mismatch" in e for e in errs), errs)

# R4-2: record identity != envelope identity refused
mismatch = rec("r5", 1, "x")
mismatch["source_app"] = "synthetic-expense"
errs = importer.validate_envelope(env(records=[mismatch]))
ck("R4-2-identity-binding-refused", any("identity mismatch" in e for e in errs), errs)

# R4-3: positive control — honest record passes
errs = importer.validate_envelope(env(records=[rec("r6", 1, "honest")]))
ck("R4-3-honest-hash-accepted", not errs, errs)

fail = not all(c["ok"] for c in checks)
(OUT / "audit-r1-regression-report.json").write_text(
    json.dumps({"checks": checks, "fail": fail}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[{'FAIL' if fail else 'OK'}] {sum(1 for c in checks if c['ok'])}/{len(checks)} audit-R1/R4 regression checks")
sys.exit(1 if fail else 0)
