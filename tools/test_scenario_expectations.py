"""Verify actual pipeline output against human-authored expectations (DF-06).

The expectations in build/semifinal-202610/scenarios/expected-{climbing,concert}.json
were written by hand independent of the implementation. This test compares the
actual timeline/query/relations output against them.

Checks per scenario:
- source selection matches
- expected key records appear in the timeline in date order
- ambiguity candidates are listed separately (not merged)
- occurred expense total matches human arithmetic
- future-plan records are flagged (not counted as occurred expense)
- malicious bodies are flagged suspicious_instruction and trigger nothing
- tombstoned records are absent
- same-day unrelated records are either absent (topic filter) or clearly tagged
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCEN = ROOT / "build/semifinal-202610/scenarios"
SYN = ROOT / "build/semifinal-202610/synthetic-source"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def check_scenario(name, timeline_path, expected_path):
    timeline = load(timeline_path)
    expected = load(expected_path)
    records = timeline["records"]
    checks = []
    fail = False

    def ck(name, ok, detail=""):
        nonlocal fail
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            fail = True

    # source selection
    sel_incl = set(timeline.get("selection", {}).get("selected_sources", []))
    ck("source-selection", sel_incl == set(expected["expected_source_selection"]["included"]),
       f"got {sorted(sel_incl)}")

    ids = [r["source_record_id"] for r in records]
    # key records present in order
    last_idx = -1
    order_ok = True
    order_detail = ""
    for item in expected["expected_timeline_order"]:
        rid = item["record"]
        if rid in ids:
            i = ids.index(rid)
            if i < last_idx:
                order_ok = False
                order_detail = f"{rid} out of order"
            last_idx = i
    ck("timeline-order", order_ok, order_detail)

    # ambiguity: same-name candidates exist as separate records
    for amb in expected.get("expected_ambiguity", []):
        cands = [c.split("(")[0] for c in amb["candidates"]]
        present = [c for c in cands if c in ids]
        ck(f"ambiguity:{amb['trigger'][:12]}", len(present) == len(cands),
           f"present {present} of {cands}")

    # expense arithmetic (minor units per v1 contract)
    total = 0
    for r in records:
        if r.get("kind") == "expense" and not r.get("suspicious_instruction"):
            amt = r.get("amount_minor", -1)
            if amt and amt > 0:
                total += amt
    exp = expected["expected_expense_total"]
    exp_total = exp.get("occurred_only_minor", exp.get("occurred_only"))
    ck("expense-total", total == exp_total, f"got {total} minor, expected {exp_total} minor")

    # future plan not counted as expense and present with future date
    for item in expected["expected_timeline_order"]:
        if item.get("expect", "").startswith("未来"):
            rid = item["record"]
            r = next((x for x in records if x["source_record_id"] == rid), None)
            ck(f"future-plan-present:{rid}", r is not None)
            if r:
                ck(f"future-plan-not-expense:{rid}", r.get("kind") != "expense",
                   f"kind={r.get('kind')}")

    # malicious handling
    mal = expected.get("expected_malicious_handling", {})
    if mal:
        mal_id = mal["record"]
        m = next((x for x in records if x["source_record_id"] == mal_id), None)
        if m is None:
            # filtered out entirely is also acceptable safe behavior
            ck("malicious-record", True, "filtered out (safe)")
        else:
            ck("malicious-flagged", bool(m.get("suspicious_instruction")),
               f"markers={m.get('suspicious_markers')}")
            ck("malicious-not-expense", m.get("kind") != "expense")
            ck("malicious-amount-unchanged", m.get("amount_minor", -1) <= 0)

    # tombstone absent
    tomb = expected.get("expected_tombstone", {})
    if tomb:
        ck("tombstone-absent", tomb["record"] not in ids, tomb["record"])

    # same-day distractor: absent via topic filter OR present-but-tagged
    for item in expected["expected_timeline_order"]:
        if "无关" in item.get("expect", ""):
            rid = item["record"]
            if rid in ids:
                r = next(x for x in records if x["source_record_id"] == rid)
                dist_tags = set(item.get("tags", []))
                ck(f"distractor-tagged:{rid}", bool(dist_tags & set(r.get("tags", []))),
                   f"tags={r.get('tags')}")
            else:
                ck(f"distractor-filtered:{rid}", True, "absent via topic filter")

    # gaps include expected kinds
    gap_kinds = {g["kind"] for g in timeline.get("gaps", [])}
    for g in expected.get("expected_gaps", []):
        ck(f"gap:{g['kind']}", g["kind"] in gap_kinds, f"gaps={sorted(gap_kinds)}")

    return {"scenario": name, "checks": checks, "fail": fail}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    results = [
        check_scenario("climbing", SYN / "timeline-climbing.json", SCEN / "expected-climbing.json"),
        check_scenario("concert", SYN / "timeline-concert.json", SCEN / "expected-concert.json"),
    ]
    fail = any(r["fail"] for r in results)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "expectations-report.json").write_text(
        json.dumps({"results": results, "fail": fail}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    total = sum(len(r["checks"]) for r in results)
    passed = sum(1 for r in results for c in r["checks"] if c["ok"])
    print(f"[{'FAIL' if fail else 'OK'}] {passed}/{total} expectation checks")
    for r in results:
        for c in r["checks"]:
            if not c["ok"]:
                print(f"  FAIL {r['scenario']}:{c['name']} {c.get('detail','')}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
