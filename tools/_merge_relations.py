"""Helper: merge candidate relations with user-decided decisions.

Reads:
- candidates JSON
- decisions JSON

Writes merged JSON with `decision` field per pair.
"""
import argparse
import json
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--decisions", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    rels = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    decided = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    by_id = {p["candidate_id"]: p for p in decided.get("pairs", [])}
    for p in rels["pairs"]:
        cid = p["candidate_id"]
        if cid in by_id:
            p["decision"] = by_id[cid]["decision"]
            if "user_note" in by_id[cid]:
                p["user_note"] = by_id[cid]["user_note"]
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(rels, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] merged -> {args.output}")


if __name__ == "__main__":
    raise SystemExit(main())
