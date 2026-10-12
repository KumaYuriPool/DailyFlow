"""Generate candidate relations between timeline records, based on co-occurrence.

Heuristic:
- Same topic tag
- Date gap <= 7 days
- Different source_apps (so a relation crosses sources)
- One side is post / image, other is event_fact / event_plan / expense
- Record-level body/title includes key terms of the other
"""

import argparse
import datetime as _dt
import json
import re
from pathlib import Path


def _parse_dt(s):
    if not s:
        return None
    if "T" in s:
        try:
            return _dt.datetime.fromisoformat(s)
        except Exception:
            return None
    try:
        return _dt.datetime.fromisoformat(s + "T00:00:00")
    except Exception:
        return None


def body_tokens(text):
    if not text:
        return set()
    return set(re.findall(r"[\w\u4e00-\u9fff]{2,}", text.lower()))


def extract_tokens(rec):
    text = " ".join([
        rec.get("title", "") or "",
        rec.get("body", "") or "",
        " ".join(rec.get("tags", []) or []),
    ])
    return body_tokens(text)


def candidate_pairs(records):
    pairs = []
    by_topic = {}
    for r in records:
        for t in r.get("tags", []):
            by_topic.setdefault(t, []).append(r)
    for topic, rs in by_topic.items():
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                if a.get("source_app") == b.get("source_app"):
                    continue
                da = _parse_dt(a.get("occurred_at", ""))
                db = _parse_dt(b.get("occurred_at", ""))
                if not da or not db:
                    continue
                if da.tzinfo is not None and db.tzinfo is None:
                    db = db.replace(tzinfo=da.tzinfo)
                elif db.tzinfo is not None and da.tzinfo is None:
                    da = da.replace(tzinfo=db.tzinfo)
                if abs((da - db).days) > 7:
                    continue
                ta, tb = extract_tokens(a), extract_tokens(b)
                common = ta & tb
                if len(common) < 1:
                    continue
                pairs.append({
                    "candidate_id": f"rel-{len(pairs) + 1:03d}",
                    "topic": topic,
                    "left": {
                        "source_app": a.get("source_app"),
                        "source_record_id": a.get("source_record_id"),
                        "kind": a.get("kind"),
                        "occurred_at": a.get("occurred_at"),
                        "title": a.get("title"),
                    },
                    "right": {
                        "source_app": b.get("source_app"),
                        "source_record_id": b.get("source_record_id"),
                        "kind": b.get("kind"),
                        "occurred_at": b.get("occurred_at"),
                        "title": b.get("title"),
                    },
                    "common_tokens": sorted(common)[:6],
                    "score_hint": min(1.0, 0.4 + 0.1 * len(common)),
                    "decision": "needs_user",
                })
    return pairs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    timeline = json.loads(Path(args.timeline).read_text(encoding="utf-8"))
    pairs = candidate_pairs(timeline.get("records", []))
    out = {
        "tool": "dailyflow.relation_candidates",
        "contract_version": 1,
        "topic": timeline.get("topic"),
        "candidate_count": len(pairs),
        "pairs": pairs,
        "audit": {"adoption_layer": "v1-import (route=B)"},
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(pairs)} candidate relations -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
