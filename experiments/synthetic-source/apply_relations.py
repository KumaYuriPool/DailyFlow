"""Apply user decisions (confirm/exclude) to a candidate list and update timeline.

Reads:
- timeline JSON
- relations JSON (with decision filled)
- optional --decision-root: persistent decision store; stored decisions
  override the relations file (refresh keeps user choices, DF-15)

Writes:
- timeline-applied JSON with applied_relations and source-affinity tags
- when --record is given, the decision of every explicit pair is also
  persisted to the store for future refreshes
"""

import argparse
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_store  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--relations", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--decision-root", default="")
    ap.add_argument("--record", action="store_true",
                    help="persist decisions from the relations file into the store")
    args = ap.parse_args(argv)

    timeline = json.loads(Path(args.timeline).read_text(encoding="utf-8"))
    relations = json.loads(Path(args.relations).read_text(encoding="utf-8"))
    topic = relations.get("topic") or timeline.get("topic") or ""

    store = None
    if args.decision_root:
        store = decision_store.load_store(args.decision_root)
        relations = decision_store.apply_stored_to_candidates(relations, store, topic)
        if args.record:
            for pair in relations.get("pairs", []):
                dec = pair.get("decision", "needs_user")
                if dec != "needs_user":
                    decision_store.record_decision(
                        args.decision_root, topic,
                        pair["left"]["source_record_id"],
                        pair["right"]["source_record_id"],
                        dec, pair.get("user_note", ""))

    confirmed = []
    excluded = []
    pending = []
    for pair in relations.get("pairs", []):
        dec = pair.get("decision") or pair.get("user", {}).get("decision", "needs_user")
        if dec == "confirm":
            confirmed.append(pair)
        elif dec == "exclude":
            excluded.append(pair)
        else:
            pending.append(pair)

    index = {}
    for rec in timeline.get("records", []):
        rid = rec.get("source_record_id")
        if rid:
            index[(rec.get("source_app"), rid)] = rec

    confirmed_keys = set()
    for pair in confirmed:
        for side in ("left", "right"):
            confirmed_keys.add((pair[side]["source_app"], pair[side]["source_record_id"]))

    for pair in confirmed:
        for side in ("left", "right"):
            r = index.get((pair[side]["source_app"], pair[side]["source_record_id"]))
            if r is None:
                continue
            tags = r.setdefault("tags", [])
            partner = pair["left"] if side == "right" else pair["right"]
            tag = f"linked:{partner['source_record_id']}"
            if tag not in tags:
                tags.append(tag)

    excluded_set = set()
    for pair in excluded:
        for side in ("left", "right"):
            excluded_set.add((pair[side]["source_app"], pair[side]["source_record_id"]))

    excluded_set -= confirmed_keys

    out = {
        "tool": "dailyflow.timeline_organize",
        "contract_version": 1,
        "topic": timeline.get("topic"),
        "applied_relations": {
            "confirmed": [
                {"left": p["left"]["source_record_id"], "right": p["right"]["source_record_id"], "topic": p["topic"]}
                for p in confirmed
            ],
            "excluded": [
                {"left": p["left"]["source_record_id"], "right": p["right"]["source_record_id"], "topic": p["topic"]}
                for p in excluded
            ],
            "pending": [
                {"left": p["left"]["source_record_id"], "right": p["right"]["source_record_id"], "topic": p["topic"]}
                for p in pending
            ],
        },
        "records": [
            {**r, "_excluded": ((r.get("source_app"), r.get("source_record_id")) in excluded_set)}
            for r in timeline.get("records", [])
        ],
        "audit": {
            "confirmed_count": len(confirmed),
            "excluded_count": len(excluded),
            "pending_count": len(pending),
            "adoption_layer": "v1-import (route=B)",
        },
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] applied: confirmed={len(confirmed)} excluded={len(excluded)} pending={len(pending)} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
