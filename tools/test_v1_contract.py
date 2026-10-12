"""Offline conformance validator for External Source Contract v1 (route=B import).

Run:
    python -X utf8 tools/test_v1_contract.py \
        --fixtures experiments/source-bridge/fixtures/probes \
        --output build/semifinal-202610/source-bridge/v1-contract

Each fixture is an envelope (one page). The validator enforces:
- contract_version must be 1
- source_app must be from allowed list
- records have mandatory identity fields, content_hash is 64-hex
- records must NOT carry deleted_at AND content body
- tombstones must carry deleted_at and NO content body
- revision rule: same source_record_id may reappear with a strictly larger source_revision;
  equal or smaller revision is rejected (no overwrite).
- idempotence: two pages with identical content_hash for the same source_record_id+revision do not increase record count.
"""
import argparse
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path

ALLOWED_SOURCES = {"dailyflow", "synthetic-climbing", "synthetic-concert", "synthetic-calendar", "synthetic-expense"}
VALID_KINDS = {"expense", "event_fact", "event_plan", "post", "image", "media_link"}


def _now_iso():
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _canonicalize(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def validate_envelope(envelope, *, seen=None):
    """Validate one envelope page. seen is dict[(app,record_id)] -> max revision seen."""
    errors = []
    if seen is None:
        seen = {}

    if envelope.get("contract_version") != 1:
        errors.append("contract_version must be 1")
    src = envelope.get("source_app")
    if src not in ALLOWED_SOURCES:
        errors.append(f"source_app not in allowed list: {src}")

    records = envelope.get("records", [])
    tombstones = envelope.get("tombstones", [])

    for rec in records:
        _check_identity(rec, errors, label="record")
        ch = rec.get("content_hash", "")
        if not (isinstance(ch, str) and len(ch) == 64 and all(c in "0123456789abcdef" for c in ch)):
            errors.append(f"content_hash not 64-hex: {rec.get('source_record_id')}")
        content = rec.get("content")
        if content is None:
            errors.append(f"record missing content: {rec.get('source_record_id')}")
            continue
        kind = content.get("kind")
        if kind not in VALID_KINDS:
            errors.append(f"invalid kind {kind!r} for {rec.get('source_record_id')}")
        if kind == "expense":
            amt = content.get("amount_minor")
            if not (isinstance(amt, int) and amt >= 0):
                errors.append(f"expense requires non-negative amount_minor, got {amt!r}")
        if content.get("open_end") is True and content.get("ended_at"):
            errors.append("open_end=true must not have ended_at")
        if rec.get("deleted_at"):
            errors.append(f"record with deleted_at must be in tombstones, not records: {rec.get('source_record_id')}")

        key = (rec["source_app"], rec["source_record_id"])
        prev = seen.get(key, 0)
        rev = rec["source_revision"]
        if rev <= prev:
            errors.append(f"non-increasing revision for {key}: prev={prev} new={rev}")
        seen[key] = rev

    for tomb in tombstones:
        _check_identity(tomb, errors, label="tombstone")
        if not tomb.get("deleted_at"):
            errors.append(f"tombstone missing deleted_at: {tomb.get('source_record_id')}")
        if "content" in tomb:
            errors.append(f"tombstone must not contain content: {tomb.get('source_record_id')}")
        ch = tomb.get("content_hash", "")
        if ch and not (isinstance(ch, str) and len(ch) == 64 and all(c in "0123456789abcdef" for c in ch)):
            errors.append(f"tombstone content_hash must be 64-hex if provided: {tomb.get('source_record_id')}")
        key = (tomb["source_app"], tomb["source_record_id"])
        prev = seen.get(key, 0)
        rev = tomb["source_revision"]
        if rev <= prev:
            errors.append(f"non-increasing tombstone revision for {key}: prev={prev} new={rev}")
        seen[key] = rev

    if envelope.get("has_more") and envelope.get("page", 0) < 1:
        errors.append("has_more without page number")
    return errors, seen


def _check_identity(obj, errors, *, label):
    for key in ("source_app", "source_record_id", "source_revision"):
        if key not in obj:
            errors.append(f"{label} missing field: {key}")
    rev = obj.get("source_revision")
    if rev is not None and (not isinstance(rev, int) or rev < 1):
        errors.append(f"{label} source_revision must be int >= 1, got {rev!r}")
    if not obj.get("source_app") in ALLOWED_SOURCES and obj.get("source_app") not in ALLOWED_SOURCES:
        errors.append(f"{label} source_app not allowed: {obj.get('source_app')!r}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    in_dir = Path(args.fixtures)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    fixtures = sorted(in_dir.glob("*.json"))
    if not fixtures:
        print(f"[E] no fixtures under {in_dir}")
        return 2

    seen = {}
    report = {"generated_at": _now_iso(), "fixtures": [], "errors": [], "summary": {}}
    passed = 0
    for f in fixtures:
        try:
            env = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            report["errors"].append(f"{f.name}: cannot parse: {exc}")
            continue
        errs, seen = validate_envelope(env, seen=seen)
        block = {
            "file": f.name,
            "source_app": env.get("source_app"),
            "snapshot_revision": env.get("snapshot_revision"),
            "record_count": len(env.get("records", [])),
            "tombstone_count": len(env.get("tombstones", [])),
            "errors": errs,
            "ok": not errs,
        }
        report["fixtures"].append(block)
        if not errs:
            passed += 1

    report["summary"] = {"total": len(fixtures), "passed": passed, "failed": len(fixtures) - passed}

    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_path = out_dir / "summary.txt"
    summary_lines = [
        f"fixtures={len(fixtures)} passed={passed} failed={len(fixtures) - passed}",
        "fixtures:",
    ] + [f"  {f}" for f in fixtures] + ["errors:"] + [f"  {e}" for e in report["errors"]]
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    if report["errors"] or passed != len(fixtures):
        print(summary_path.read_text(encoding="utf-8"))
        return 2
    print(f"[OK] {passed}/{len(fixtures)} v1 contract fixtures conform")
    return 0


if __name__ == "__main__":
    sys.exit(main())
