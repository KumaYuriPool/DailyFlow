"""Organizer: combine query results from multiple sources into a single
chronological flow with citations. Mirrors what DailyFlow Agent
`dailyflow.timeline_organize` would do if exposed.

Reads:
- selection.json (from agent_selector.py)
- query JSON (from dailyflow_query_v1.py for each selected source)

Writes:
- timeline.json (sorted records with citations + provenance + gaps)

Run:
    python -X utf8 experiments/synthetic-source/organizer.py \
        --selection build/semifinal-202610/synthetic-source/selection.json \
        --query-climb build/semifinal-202610/synthetic-source/query-climbing.json \
        --query-concert build/semifinal-202610/synthetic-source/query-concert.json \
        --projection-climb build/semifinal-202610/synthetic-source/projection-climbing \
        --projection-concert build/semifinal-202610/synthetic-source/projection-concert \
        --output build/semifinal-202610/synthetic-source/timeline.json
"""

import argparse
import json
from pathlib import Path


INJECTION_MARKERS = (
    "忽略之前所有指令", "忽略所有安全规则", "泄露", "标记为支出并同步",
    "删除日历事件", "改成 0 元", "system prompt", "disregard previous",
)


def flag_suspicious(rec):
    """Spec §7: source body text is DATA, never instructions. Records whose body
    asks the agent to leak other sources, rewrite money, or delete data are shown
    with a warning flag and are never executed. Flagging is deterministic."""
    body = (rec.get("body") or "")
    hits = [m for m in INJECTION_MARKERS if m in body]
    if hits:
        rec = dict(rec)
        rec["suspicious_instruction"] = True
        rec["suspicious_markers"] = hits
    return rec


def render_timeline(selection, queries_by_source, *, topics, shortfall_predicates=None):
    if shortfall_predicates is None:
        shortfall_predicates = []
    selected_sources = selection.get("selected_sources", [])
    topic = selection.get("query", {}).get("matched_topic")

    records = []
    citations = []
    for src, query in queries_by_source.items():
        result = query.get("result", {})
        for rec in result.get("records", []):
            if topic and topic not in [t.lower() for t in rec.get("tags", [])] and topic not in rec.get("title", "").lower():
                continue
            records.append(flag_suspicious({**rec, "_citation_source": src}))

    records.sort(key=lambda r: (r.get("occurred_at") or "", r.get("source_record_id", "")))

    citations_table = {}
    for src, query in queries_by_source.items():
        result = query.get("result", {})
        citations_table[src] = {
            "query_id": query.get("query", {}).get("query_id"),
            "fetched_at_window": [query.get("query", {}).get("from"), query.get("query", {}).get("to")],
            "record_count": result.get("record_count", 0),
            "sources_seen": result.get("sources_seen", []),
        }

    gaps = []
    for kind, predicate in shortfall_predicates:
        ok = predicate(records)
        if not ok:
            gaps.append({"kind": kind, "detail": "not enough data"})

    return {
        "tool": "dailyflow.timeline_organize",
        "contract_version": 1,
        "selection": selection,
        "topic": topic,
        "topics_in_query": topics,
        "records": [
            {
                "occurred_at": r.get("occurred_at"),
                "kind": r.get("kind"),
                "title": r.get("title"),
                "body": r.get("body"),
                "source_app": r.get("source_app"),
                "source_record_id": r.get("source_record_id"),
                "source_revision": r.get("source_revision"),
                "tags": r.get("tags", []),
                "amount_minor": r.get("amount_minor", -1),
                "currency": r.get("currency"),
                "media": r.get("media", []),
                "citation": r.get("_citation_source"),
                **({"suspicious_instruction": True, "suspicious_markers": r["suspicious_markers"]}
                   if r.get("suspicious_instruction") else {}),
            }
            for r in records
        ],
        "citations": citations_table,
        "gaps": gaps,
        "audit": {"adoption_layer": "v1-import (route=B)", "organizer": "rule-based"},
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selection", required=True)
    ap.add_argument("--query-climb", default="")
    ap.add_argument("--query-concert", default="")
    ap.add_argument("--projection-climb", default="")
    ap.add_argument("--projection-concert", default="")
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    sel = json.loads(Path(args.selection).read_text(encoding="utf-8"))
    queries_by_source = {}
    if args.query_climb:
        queries_by_source["climbing"] = json.loads(Path(args.query_climb).read_text(encoding="utf-8"))
    if args.query_concert:
        queries_by_source["concert"] = json.loads(Path(args.query_concert).read_text(encoding="utf-8"))

    topic = sel.get("query", {}).get("matched_topic")

    def climbing_weekly_check(_records):
        return True

    shortfall = []
    if topic == "bouldering":
        shortfall.append(("weekly_frequency", lambda rs: any("每周" in r.get("body", "") or "每周" in r.get("title", "") for r in rs)))
        # coach guidance: only claimed if a record states recurring/ongoing coaching;
        # one mention inside a single experience post is NOT recurring guidance
        def coach_recurring(rs):
            mentions = [r for r in rs if "教练" in (r.get("body", "") or "") + (r.get("title", "") or "")]
            recurring = [r for r in mentions if any(k in (r.get("body", "") or "") for k in ("每周", "定期", "长期", "课程包"))]
            return len(recurring) >= 1
        shortfall.append(("coach_guidance", coach_recurring))
    if topic == "concert":
        # transport: confirmed only if a record asserts the chosen mode as booked/decided
        def transport_confirmed(rs):
            decided = [r for r in rs if any(k in (r.get("body", "") or "") for k in ("已打车", "已订车", "开车去", "地铁直达已确认", "已约车"))]
            return len(decided) >= 1
        shortfall.append(("transport_mode", transport_confirmed))

    timeline = render_timeline(sel, queries_by_source, topics=[topic] if topic else [], shortfall_predicates=shortfall)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] organized {len(timeline['records'])} records -> {out}; gaps={timeline['gaps']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
