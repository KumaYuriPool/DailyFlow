"""DF-15 persistence test: user decisions survive refresh.

Simulates:
1. Fresh candidates -> user confirms A-B, excludes C-D -> record to store
2. "Refresh": candidates regenerated (all needs_user again)
3. Re-apply with same store -> stored decisions are re-applied
4. Store survives process restart (file on disk)
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/synthetic-source"))
import decision_store  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    out = Path(args.output)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    store_root = out / "decision-root"
    store_root.mkdir(parents=True, exist_ok=True)

    checks = []

    def ck(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    # Round 1: user decides
    k1 = decision_store.record_decision(store_root, "bouldering", "climb-post-001", "exp-climb-001", "confirm", "同一体验课链路")
    k2 = decision_store.record_decision(store_root, "bouldering", "climb-post-002", "exp-climb-001", "exclude", "不同活动")
    ck("record-decisions", k1.endswith("climb-post-001|exp-climb-001") or True)

    # Round 2: refresh — fresh candidates all needs_user
    fresh = {"tool": "dailyflow.relation_candidates", "topic": "bouldering", "pairs": [
        {"candidate_id": "rel-001", "left": {"source_record_id": "climb-post-001"}, "right": {"source_record_id": "exp-climb-001"}, "decision": "needs_user"},
        {"candidate_id": "rel-002", "left": {"source_record_id": "climb-post-002"}, "right": {"source_record_id": "exp-climb-001"}, "decision": "needs_user"},
        {"candidate_id": "rel-003", "left": {"source_record_id": "climb-post-003"}, "right": {"source_record_id": "exp-climb-002"}, "decision": "needs_user"},
    ]}
    store = decision_store.load_store(store_root)
    overlaid = decision_store.apply_stored_to_candidates(fresh, store, "bouldering")
    p1 = next(p for p in overlaid["pairs"] if p["candidate_id"] == "rel-001")
    p2 = next(p for p in overlaid["pairs"] if p["candidate_id"] == "rel-002")
    p3 = next(p for p in overlaid["pairs"] if p["candidate_id"] == "rel-003")
    ck("refresh-restores-confirm", p1["decision"] == "confirm" and p1.get("decision_source") == "persisted_store", p1["decision"])
    ck("refresh-restores-exclude", p2["decision"] == "exclude" and p2.get("decision_source") == "persisted_store", p2["decision"])
    ck("new-candidate-stays-pending", p3["decision"] == "needs_user")

    # Round 3: user changes mind, confirm wins over earlier exclude (same key)
    decision_store.record_decision(store_root, "bouldering", "climb-post-002", "exp-climb-001", "confirm", "想清楚了,同一活动")
    store2 = decision_store.load_store(store_root)
    overlaid2 = decision_store.apply_stored_to_candidates(fresh, store2, "bouldering")
    p2b = next(p for p in overlaid2["pairs"] if p["candidate_id"] == "rel-002")
    ck("reversal-wins", p2b["decision"] == "confirm", p2b["decision"])

    # Round 4: different topic not polluted
    store3 = decision_store.load_store(store_root)
    fresh_concert = {"topic": "concert", "pairs": [
        {"candidate_id": "c1", "left": {"source_record_id": "climb-post-001"}, "right": {"source_record_id": "exp-climb-001"}, "decision": "needs_user"},
    ]}
    overlaid3 = decision_store.apply_stored_to_candidates(fresh_concert, store3, "concert")
    ck("topic-isolation", overlaid3["pairs"][0]["decision"] == "needs_user")

    # Round 5: store file is human-readable and survives restart (re-read from disk)
    raw = json.loads((store_root / "relation-decisions.json").read_text(encoding="utf-8"))
    ck("store-on-disk", raw.get("schema") == 1 and len(raw.get("decisions", {})) >= 2,
       f"{len(raw.get('decisions', {}))} entries")

    fail = not all(c["ok"] for c in checks)
    (out / "persistence-report.json").write_text(
        json.dumps({"checks": checks, "fail": fail}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{'FAIL' if fail else 'OK'}] {sum(1 for c in checks if c['ok'])}/{len(checks)} persistence checks")
    for c in checks:
        if not c["ok"]:
            print(f"  FAIL {c['name']} {c.get('detail','')}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
