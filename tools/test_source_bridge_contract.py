"""Offline conformance examples, not official-host or production integration tests."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/source-bridge"
spec = importlib.util.spec_from_file_location("bridge_consumer", EXPERIMENT / "consumer.py")
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)
CAPTURE = EXPERIMENT / "fixtures/historical-splash-all.json"
CAPTURE_SHA256 = "19be7f78c5b64a954ca442ec29557f597a6e463f1d01e8f68863ef9e707ca595"
ORIGINAL = json.loads(CAPTURE.read_text(encoding="utf-8"))["0"]["data"]["events"]
SOURCE = "dev.dailyflow.probeledger"


def event(revision=1, amount=12000, source=SOURCE, record="probe-1"):
    result = deepcopy(next(e for e in ORIGINAL if e["source_module"] == "expense"))
    result.update(source_app=source, source_record_id=record, source_revision=revision,
                  event_id=f"{source}/expense/{record}", change_id=f"{source}/expense/{record}/{revision}",
                  summary="合成洗护记录", amount_minor=amount, updated_at=1791283900 + revision)
    result["entry"].update(record_id=record, source_revision=revision)
    return result


def tombstone(revision=3):
    e = event(revision)
    return {k: e[k] for k in ("protocol_version", "source_app", "source_module", "source_record_id", "source_revision", "event_id", "change_id")} | {"operation": "delete", "deleted_at": 1791284000.25}


def page(*events, source=SOURCE, complete=True, offset=0, snapshot=1):
    return dict(status="ok", source_app=source, events=list(events), complete=complete,
                offset=offset, snapshot_revision=snapshot)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.p = consumer.Projection({SOURCE: ["expense"]})

    def assertRefusedUnchanged(self, payload, source=SOURCE):
        before = deepcopy((self.p.items, self.p.status, self.p.snapshots))
        with self.assertRaises(consumer.ContractError):
            self.p.apply_page(source, payload)
        self.assertEqual(before, (self.p.items, self.p.status, self.p.snapshots))

    def test_historical_three_source_splash_capture(self):
        self.assertEqual(hashlib.sha256(CAPTURE.read_bytes()).hexdigest(), CAPTURE_SHA256)
        p = consumer.Projection({"dailyflow": ["expense", "calendar", "period"]})
        p.apply_page("dailyflow", page(*ORIGINAL, source="dailyflow"))
        self.assertEqual(len(p.visible()), 3)
        self.assertEqual(sum(e["amount_minor"] for e in p.visible()), 3500)
        self.assertEqual(next(e for e in p.visible() if e["status"] == "planned")["occurred_at"], "")

    def test_duplicate_read_preserves_one_bill(self):
        self.p.apply_page(SOURCE, page(event()))
        self.assertEqual(self.p.apply_page(SOURCE, page(event()))["ignored"], 1)
        self.assertEqual([e["amount_minor"] for e in self.p.visible()], [12000])

    def test_correction_keeps_identity_and_updates_amount(self):
        self.p.apply_page(SOURCE, page(event()))
        self.p.apply_page(SOURCE, page(event(2, 10000), snapshot=2))
        self.assertEqual([(e["source_record_id"], e["amount_minor"]) for e in self.p.visible()], [("probe-1", 10000)])

    def test_old_record_cannot_overwrite_new_revision(self):
        self.p.apply_page(SOURCE, page(event(2, 10000)))
        self.p.apply_page(SOURCE, page(event()))
        self.assertEqual(self.p.visible()[0]["amount_minor"], 10000)

    def test_tombstone_blocks_late_resurrection(self):
        self.p.apply_page(SOURCE, page(event(), tombstone()))
        self.p.apply_page(SOURCE, page(event(2, 10000)))
        self.assertEqual(self.p.visible(), [])
        self.assertEqual(next(iter(self.p.items.values()))["source_revision"], 3)

    def test_partial_page_does_not_delete_absent_records(self):
        self.p.apply_page(SOURCE, page(event(record="a"), event(record="b")))
        self.p.apply_page(SOURCE, page(event(2, 10000, record="a"), complete=False, snapshot=2))
        self.assertEqual({e["source_record_id"] for e in self.p.visible()}, {"a", "b"})
        self.assertEqual(self.p.status[SOURCE], "partial")

    def test_empty_complete_snapshot_never_infers_deletion(self):
        self.p.apply_page(SOURCE, page(event()))
        self.p.apply_page(SOURCE, page(snapshot=2))
        self.assertEqual(len(self.p.visible()), 1)

    def test_source_failure_is_not_empty_success(self):
        self.p.apply_page(SOURCE, page(event()))
        self.p.apply_page(SOURCE, {"status": "unavailable"})
        self.assertEqual(self.p.visible(), [])
        self.assertEqual(len(self.p.items), 1)
        self.assertEqual(self.p.status[SOURCE], "unavailable")

    def test_denial_hides_cached_content(self):
        self.p.apply_page(SOURCE, page(event()))
        self.p.apply_page(SOURCE, {"status": "denied"})
        self.assertEqual(self.p.visible(), [])
        self.assertEqual(self.p.status[SOURCE], "denied")

    def test_identical_record_ids_across_sources_remain_distinct(self):
        p = consumer.Projection({SOURCE: ["expense"], "other": ["expense"]})
        p.apply_page(SOURCE, page(event()))
        p.apply_page("other", page(event(source="other"), source="other"))
        self.assertEqual(len(p.visible()), 2)

    def test_spoofed_or_unregistered_sources_are_rejected(self):
        self.assertRefusedUnchanged(page(event(source="other")))
        self.assertRefusedUnchanged(page(event()), source="other")
        e = event(); e["source_module"] = "private"
        self.assertRefusedUnchanged(page(e))

    def test_conflicting_same_revision_is_rejected(self):
        self.p.apply_page(SOURCE, page(event()))
        self.assertRefusedUnchanged(page(event(amount=999)))

    def test_invalid_page_is_atomic(self):
        e = event(record="b"); e["amount_minor"] = 1.2
        self.assertRefusedUnchanged(page(event(), e))

    def test_bad_identity_revision_and_date_are_rejected(self):
        for field, value in (("event_id", "wrong"), ("source_revision", True), ("date", "2026-02-30"),
                             ("created_at", float("nan")), ("occurred_at", "2026-10-02T00:00:00+08:00")):
            with self.subTest(field=field):
                e = event(); e[field] = value
                self.assertRefusedUnchanged(page(e))

    def test_continuation_requires_same_snapshot_and_offset(self):
        self.p.apply_page(SOURCE, page(event(record="a"), complete=False, snapshot=7))
        self.assertRefusedUnchanged(page(event(record="b"), offset=1, snapshot=8))
        self.assertRefusedUnchanged(page(event(record="b"), offset=2, snapshot=7))
        self.p.apply_page(SOURCE, page(event(record="b"), offset=1, snapshot=7))
        self.assertEqual(len(self.p.visible()), 2)
        self.assertEqual(self.p.status[SOURCE], "ok")

    def test_missing_or_empty_partial_page_is_rejected(self):
        self.assertRefusedUnchanged(page(event(), offset=1))
        self.assertRefusedUnchanged(page(complete=False))

    def test_input_mutation_cannot_change_cached_record(self):
        e = event(); self.p.apply_page(SOURCE, page(e)); e["amount_minor"] = 1
        visible = self.p.visible(); visible[0]["amount_minor"] = 2
        self.assertEqual(self.p.visible()[0]["amount_minor"], 12000)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "tests.log").open("w", encoding="utf-8") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests))
    projection = consumer.Projection({SOURCE: ["expense"]})
    trace = []
    for name, incoming in (("initial", event()), ("duplicate", event()), ("corrected", event(2, 10000)),
                           ("late_old", event()), ("deleted", tombstone()), ("late_after_delete", event(2, 10000))):
        outcome = projection.apply_page(SOURCE, page(incoming))
        visible = projection.visible()
        trace.append(dict(step=name, incoming=incoming, outcome=outcome, visible=visible,
                          visible_count=len(visible), amount_minor=sum(e["amount_minor"] for e in visible)))
    (args.output / "synthetic-change-trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
    report = dict(passed=result.wasSuccessful(), tests=result.testsRun,
                  evidence_kind="offline Python independent consumer and historical Splash export replay",
                  official_host_tested=False, production_bridge_implemented=False,
                  failures=[(str(test), error) for test, error in result.failures + result.errors],
                  inputs={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (Path(__file__), EXPERIMENT / "consumer.py", CAPTURE)})
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if result.wasSuccessful() else 1)
