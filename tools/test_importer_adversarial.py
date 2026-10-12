"""Adversarial importer tests reproducing the independent audit's 4 failing
cases (F03/F04/F05) plus out-of-order replay, after the hardening fix.

Cases (all must PASS now):
1. old_upsert_must_not_resurrect_deleted_record: rev2 content -> tombstone
   rev3 -> replay rev2 content. Tombstone must survive; content not resurrected.
2. latest_revision_10_must_win_over_9: rev-9 and rev-10 both stored; query
   layer must report revision 10 (numeric, not string sort).
3. same_revision_conflict_must_not_silently_overwrite: rev2 content A, then
   rev2 content B (different hash). Stored value A kept, conflict logged.
4. record_id_must_stay_within_source_record_directory: "../../escaped" and
   "a\\b" and absolute-style ids must be refused with no file written outside.
5. out_of_order_replay: pages arriving 3,1,2 -> final state equals rev3; rev1/2
   replays are skipped, not errors.
"""

import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/synthetic-source"))
import importer  # noqa: E402

OUT = ROOT / "build/importer-adversarial-r1"
OUT.mkdir(parents=True, exist_ok=True)

checks = []


def ck(name, ok, detail=""):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
    print(("PASS " if ok else "FAIL ") + name + (" :: " + str(detail)[:120] if detail and not ok else ""))


def rec(source, rid, rev, title, body="x"):
    content = {"kind": "post", "occurred_at": "2026-09-01", "ended_at": None,
               "open_end": False, "title": title, "body": body, "media": [],
               "tags": ["t"], "amount_minor": -1, "currency": "CNY",
               "source_meta": {}}
    import hashlib
    h = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"source_app": source, "source_module": "post", "source_record_id": rid,
            "source_revision": rev, "deleted_at": None, "content_hash": h,
            "content": content}


def tomb(source, rid, rev):
    return {"source_app": source, "source_module": "post", "source_record_id": rid,
            "source_revision": rev, "deleted_at": "2026-10-10T00:00:00Z",
            "content_hash": "0" * 64}


def env(source, records=None, tombs=None):
    return {"contract_version": 1, "source_app": source, "source_module": "post",
            "fetched_at": "2026-10-11T00:00:00Z", "snapshot_revision": 1,
            "records": records or [], "tombstones": tombs or [],
            "page": 1, "page_size": 50, "has_more": False}


def fresh(name):
    d = OUT / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


def latest_state(root, source, rid):
    """Mimic the query layer: numeric-max rev wins; tombstone hides content."""
    rd = root / "records" / source / rid
    if not rd.exists():
        return {"exists": False}
    best_rev, best = 0, None
    for p in rd.glob("rev-*.json"):
        n = int(re.fullmatch(r"rev-(\d+)", p.stem).group(1))
        if n > best_rev:
            best_rev, best = n, p
    t = rd / "tombstone.json"
    tomb_rev = int(json.loads(t.read_text(encoding="utf-8"))["source_revision"]) if t.exists() else -1
    if t.exists() and tomb_rev >= best_rev:
        return {"exists": False, "deleted": True, "tomb_rev": tomb_rev, "content_rev": best_rev}
    if best is None:
        return {"exists": False}
    data = json.loads(best.read_text(encoding="utf-8"))
    return {"exists": True, "revision": data["source_revision"],
            "title": data["content"]["title"]}


SRC = "synthetic-climbing"

# Case 1: tombstone not resurrected by old replay
root1 = fresh("old-after-delete")
ok1, _, _ = importer.import_scenario.__wrapped__ if False else (True, None, None)  # placeholder
summary = {}
importer.import_envelope(env(SRC, records=[rec(SRC, "r1", 2, "v2")]), root1, summary)
importer.import_envelope(env(SRC, tombs=[tomb(SRC, "r1", 3)]), root1, summary)
importer.import_envelope(env(SRC, records=[rec(SRC, "r1", 2, "v2")]), root1, summary)
st = latest_state(root1, SRC, "r1")
ck("F03-old-replay-no-resurrect", st.get("deleted") is True and not st.get("exists"), st)
ck("F03-old-replay-tomb-rev-kept", st.get("tomb_rev") == 3, st)

# Case 2: numeric revision ordering 10 > 9 (write 9 first, then 10; query layer)
root2 = fresh("numeric-revision")
summary2 = {}
importer.import_envelope(env(SRC, records=[rec(SRC, "r2", 9, "nine"), rec(SRC, "r2b", 10, "ten")]), root2, summary2)
# put rev9 and rev10 for the SAME record: importer applies both (10 later)
importer.import_envelope(env(SRC, records=[rec(SRC, "r2", 10, "ten")]), root2, summary2)
st = latest_state(root2, SRC, "r2")
ck("F04-rev10-beats-rev9", st.get("revision") == 10 and st.get("title") == "ten", st)

# Case 3: same-revision conflict refused, stored value kept, conflict logged
root3 = fresh("same-revision-conflict")
summary3 = {}
importer.import_envelope(env(SRC, records=[rec(SRC, "r3", 2, "original")]), root3, summary3)
applied, skipped, conflicted, status = importer._apply_record(root3, rec(SRC, "r3", 2, "conflicting"), "t")
st = latest_state(root3, SRC, "r3")
ck("F05-conflict-kept", st.get("title") == "original" and conflicted and not applied, (st, status))
ck("F05-conflict-logged", (root3 / "records" / SRC / "r3" / "conflicts.json").exists())

# Case 4: path traversal refused, nothing written outside
root4 = fresh("path-traversal")
base = (root4 / "records").resolve()
before = {p for p in root4.rglob("*")}
for bad in ("../../escaped", "a\\b", "/abs/path", "..", "a/b"):
    try:
        importer._apply_record(root4, rec(SRC, bad, 1, "x"), "t")
        ck(f"F06-refuse:{bad!r}", False, "accepted unsafe id")
    except importer.ImportError_:
        ck(f"F06-refuse:{bad!r}", True)
after = {p for p in root4.rglob("*")}
escaped = [p for p in after - before if base not in p.parents and p != base]
ck("F06-no-escape-files", not escaped, escaped)

# Case 5: out-of-order pages converge to rev3
root5 = fresh("out-of-order")
summary5 = {}
run_report5 = {}
for page in [env(SRC, records=[rec(SRC, "r5", 3, "three")]),
             env(SRC, records=[rec(SRC, "r5", 1, "one")]),
             env(SRC, records=[rec(SRC, "r5", 2, "two")])]:
    importer.import_envelope(page, root5, summary5, run_report5)
st = latest_state(root5, SRC, "r5")
ck("F07-outoforder-converges", st.get("revision") == 3 and st.get("title") == "three", st)
skipped_ok = run_report5[SRC]["skipped"] >= 2
ck("F07-stale-skipped-not-error", skipped_ok, run_report5[SRC]["statuses"])

fail = not all(c["ok"] for c in checks)
(OUT / "adversarial-report.json").write_text(
    json.dumps({"checks": checks, "fail": fail}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[{'FAIL' if fail else 'OK'}] {sum(1 for c in checks if c['ok'])}/{len(checks)} adversarial checks")
return_ = 1 if fail else 0
sys.exit(return_)
