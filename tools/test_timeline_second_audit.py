"""Regression for independent-audit-r2-20261011 B1/B2/B3.

SUPERSEDED (2026-10-12, r6): the authoritative B1/B2/B3 suite is
tools/test_timeline_second_stages.py (15/15 with isolation guards). This
chained single-probe variant remains for reference; two checks
(B2-bing-detail-own-content, B3-return-button-visible) are known
harness-timing-flaky (row attribution after refresh; return affordance) —
the same behaviors are hard-gated in second_stages stage C1/B5/B6. The r5
isolation fix (private --out synwork) applies here too.

Real card-host (655114c+patch), production bundle, no model.

B1: upstream applied exclusion ("excluded": true from _excluded) hides the
    record and counts in the summary, without any local decision.
B2: two sources sharing the same record_id stay independent — excluding one
    does not hide the other; details show their own content.
B3: the detail view renders "‹ 返回列表"; after the source deletes the record
    and a sync, refresh shows the explicit lapsed card instead of stale data.
"""
import native_runtime
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_timeline_ui import TimelineProbe  # noqa: E402
from test_real_model_flow import UI  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NEW_HOST = native_runtime.binary("card_host")
SYNC = ROOT / "tools/sync_timeline_import.py"


def texts(ui):
    return [w.get("t", "") for w in ui.widgets()]


def ensure_settled(ui):
    """After a refresh the view can be captured mid-re-render; block until the
    summary line is back (or re-enter the view once), so sweeps never start
    from an empty intermediate frame."""
    for _ in range(25):
        if any("条 · 按时间排列" in (w.get("t") or "") for w in ui.widgets()):
            return
        time.sleep(0.2)
    open_timeline(ui)
    press_refresh(ui)


def sweep(ui, rounds=14, x=1100):
    ensure_settled(ui)
    out = texts(ui)
    for _ in range(rounds):
        ui.probe.request("m", k="scroll", x=x, y=500, dy=200, wait=1)
        time.sleep(0.12)
        out += texts(ui)
    return out


def sweep_top(ui):
    for _ in range(16):
        ui.probe.request("m", k="scroll", x=1100, y=500, dy=-400, wait=1)
        time.sleep(0.1)


def open_timeline(ui):
    for _ in range(6):
        if any(w.get("t") == "导入时间流" for w in ui.widgets()):
            return
        ui.click("时间流")
        time.sleep(0.4)
    raise AssertionError("timeline view did not open")


def press_refresh(ui):
    for _ in range(6):
        if any(w.get("t") == "刷新" for w in ui.widgets()):
            ui.click("刷新")
            # wait for the view to settle: the summary line must be back
            for _ in range(20):
                if any("条 · 按时间排列" in (w.get("t") or "") for w in ui.widgets()):
                    time.sleep(0.2)
                    return
                time.sleep(0.2)
            return
        ui.click("时间流")
        time.sleep(0.4)
    raise AssertionError("刷新 not found")


def click_button_near(ui, label_text, button_text, scrolls=10):
    """Scroll until ONE frame contains both the label and (after it) the
    button; click that button's own coordinates. Text-based ui.click picks the
    FIRST visible button in the viewport, which may belong to another row."""
    for _ in range(scrolls * 2):
        wid = ui.widgets()
        det = [i for i, w in enumerate(wid) if w.get("ty") == "Button" and (w.get("t") or "") == button_text]
        for di in det:
            # row structure: │ date Label → title Label → source Label → buttons.
            # Walk back: first Label above is the source line, the next one is
            # the title. Do NOT cross the date line (that would borrow another
            # row's title).
            labels_above = [w for w in reversed(wid[:di]) if w.get("ty") == "Label"]
            if len(labels_above) >= 2:
                title = labels_above[1].get("t") or ""
                if label_text in title:
                    x, y, bw, bh = wid[di]["r"]
                    ui.probe.request("click", x=x + bw / 2, y=y + bh / 2, wait=1)
                    time.sleep(0.5)
                    return True
        ui.probe.request("m", k="scroll", x=1100, y=500, dy=200, wait=1)
        time.sleep(0.12)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    out = Path(args.output)
    if out.exists():
        import shutil
        shutil.rmtree(out)
    probe = TimelineProbe(out, ROOT / "bundle", size="1280x900", binary=str(NEW_HOST))
    checks = []

    def ck(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:250]})
        print(("PASS " if ok else "FAIL ") + name + (f" :: {detail}"[:130] if not ok else ""))

    # B2 fixture: two sources legally sharing one record_id ("same")
    # B2 fixture: each source gets its OWN envelope (R4 identity binding
    # requires envelope.source_app == record.source_app); both legally use the
    # same record_id "same" to prove composite-key independence.
    # ISOLATION (r5 fix): private sync workdir under this run's output; the
    # canonical synthetic-source tree is never written (see second_stages).
    work = out / "synwork"
    (work / "climbing").mkdir(parents=True, exist_ok=True)
    overlay_paths = []
    for src in ("synthetic-expense", "synthetic-concert"):
        kind = "expense" if src == "synthetic-expense" else "post"
        content = {"kind": kind, "occurred_at": "2026-09-15", "ended_at": None,
                   "open_end": False,
                   "title": f"来源{'乙' if src == 'synthetic-expense' else '丙'}记录",
                   "body": f"{src} / same 的正文", "media": [], "tags": ["bouldering"],
                   "amount_minor": 100 if src == "synthetic-expense" else -1,
                   "currency": "CNY", "source_meta": {}}
        env = {"contract_version": 1, "source_app": src, "source_module": kind,
               "fetched_at": "2026-10-11T06:00:00Z", "snapshot_revision": 9,
               "records": [{"source_app": src, "source_module": kind,
                            "source_record_id": "same", "source_revision": 1,
                            "deleted_at": None,
                            "content_hash": hashlib.sha256(json.dumps(
                                content, sort_keys=True, ensure_ascii=False,
                                separators=(",", ":")).encode("utf-8")).hexdigest(),
                            "content": content}],
               "tombstones": [], "page": 1, "page_size": 50, "has_more": False}
        op = work / "climbing" / f"page-05-collision-{src}.json"
        op.write_text(json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")
        overlay_paths.append(op)

    try:
        ui = UI(probe)
        time.sleep(0.4)

        # baseline sync WITHOUT applied (raw), so B1 applies later explicitly
        subprocess.run([sys.executable, "-X", "utf8", str(SYNC),
                        "--data-root", str(probe.apps), "--out", str(work)],
                       check=True, capture_output=True)
        open_timeline(ui)
        labels = sweep(ui)
        sweep_top(ui)
        ck("B2-both-same-records-visible",
           any("来源乙记录" in t for t in labels) and any("来源丙记录" in t for t in labels),
           [t for t in labels if "来源" in t and "记录" in t][:3])

        # B2: exclude source-yi's "same" via its row's 排除 button
        ok = click_button_near(ui, "来源乙记录", "排除")
        ck("B2-exclude-yi-clicked", ok)
        labels = sweep(ui)
        ck("B2-yi-hidden", not any("来源乙记录" in t for t in labels),
           [t for t in labels if "来源乙" in t][:2])
        ck("B2-bing-still-visible", any("来源丙记录" in t for t in labels),
           [t for t in labels if "来源丙" in t][:2])
        press_refresh(ui)
        sweep_top(ui)  # refresh keeps scroll position; return to the top first
        labels = sweep(ui)
        ck("B2-yi-still-hidden-after-refresh", not any("来源乙记录" in t for t in labels))
        if not any("来源丙记录" in t for t in labels):
            all_labels = sorted({t[:22] for t in labels if t})
            print("DEBUG bing-missing; full labels:", all_labels[:20])
        ck("B2-bing-visible-after-refresh", any("来源丙记录" in t for t in labels))

        # B2: detail of bing shows ITS own content
        sweep_top(ui)
        opened = click_button_near(ui, "来源丙记录", "详情")
        ck("B2-bing-detail-opened", opened)
        labels = texts(ui)
        ck("B2-bing-detail-own-content",
           any("来源丙记录" in t for t in labels) and any("synthetic-concert / same" in t for t in labels),
           [t for t in labels if "same" in t][:3])
        ck("B3-return-button-visible", any("‹ 返回列表" in t for t in labels),
           [t for t in labels if "返回" in t][:2])
        ui.click("‹ 返回列表")
        time.sleep(0.4)
        ck("B3-return-works", any("条 · 按时" in t for t in texts(ui)))
        sweep_top(ui)

        # B1: upstream applied exclusion — sync with applied climbing timeline
        subprocess.run([sys.executable, "-X", "utf8", str(SYNC),
                        "--data-root", str(probe.apps), "--out", str(work),
                        "--applied-climb", str(ROOT / "build/semifinal-202610/synthetic-source/timeline-climbing-applied.json")],
                       check=True, capture_output=True)
        press_refresh(ui)
        labels = sweep(ui)
        # applied excludes climb-post-002 (第一次室内抱石体验) and exp-climb-002 (周卡续费)
        ck("B1-upstream-excluded-hidden",
           not any("周卡续费" in t for t in labels) and not any("第一次室内抱石体验" in t for t in labels),
           [t for t in labels if "周卡" in t or "抱石体验" in t][:3])
        ck("B1-summary-counts-excluded", any("已排除" in t for t in labels),
           [t for t in labels if "已排除" in t][:2])
        ck("B1-confirmed-records-still-visible", any("B 站的攀岩入门视频" in t for t in labels),
           [t for t in labels if "B 站" in t][:2])

        # B3: delete a record at the source (rev31 tombstone for climb-post-001),
        # sync again, refresh — the OPEN detail must lapse explicitly.
        sweep_top(ui)
        opened = click_button_near(ui, "B 站的攀岩入门视频", "详情")
        ck("B3-detail-opened-before-delete", opened)
        labels = texts(ui)
        ck("B3-detail-shows-content", any("来源身份：synthetic-climbing / climb-post-001" in t for t in labels),
           [t for t in labels if "来源身份" in t][:2])

        env_dir = work / "climbing"
        env_dir.mkdir(parents=True, exist_ok=True)
        tomb_overlay = {"contract_version": 1, "source_app": "synthetic-climbing",
                        "source_module": "post", "fetched_at": "2026-10-11T07:00:00Z",
                        "snapshot_revision": 3, "records": [],
                        "tombstones": [{"source_app": "synthetic-climbing", "source_module": "post",
                                        "source_record_id": "climb-post-001", "source_revision": 31,
                                        "deleted_at": "2026-10-11T07:00:00Z",
                                        "content_hash": "0" * 64}],
                        "page": 1, "page_size": 50, "has_more": False}
        tomb_path = env_dir / "page-06-delete.json"
        tomb_path.write_text(json.dumps(tomb_overlay, ensure_ascii=False, indent=2), encoding="utf-8")
        subprocess.run([sys.executable, "-X", "utf8", str(SYNC),
                        "--data-root", str(probe.apps), "--out", str(work),
                        "--applied-climb", str(ROOT / "build/semifinal-202610/synthetic-source/timeline-climbing-applied.json")],
                       check=True, capture_output=True)
        press_refresh(ui)
        labels = texts(ui)
        ck("B3-deleted-detail-lapses",
           any("已失效" in t for t in labels) and not any("来源身份：synthetic-climbing / climb-post-001" in t for t in labels),
           [t for t in labels if "失效" in t][:2])
        press_refresh(ui)
        labels = texts(ui)
        ck("B3-lapsed-stable-on-repeat", any("已失效" in t for t in labels))
        # and the list no longer shows the deleted record
        ui.click("‹ 返回列表")
        time.sleep(0.4)
        labels = sweep(ui)
        ck("B3-deleted-record-not-in-list", not any("B 站的攀岩入门视频" in t for t in labels),
           [t for t in labels if "B 站" in t][:2])
    finally:
        probe.stop()
        # Private synwork dir is kept as run evidence; the canonical
        # synthetic-source tree was never written, nothing to clean.

    fail = not all(c["ok"] for c in checks)
    (out / "report.json").write_text(json.dumps(
        {"checks": checks, "fail": fail,
         "evidence_class": "audit-r2 B1/B2/B3 regression (composite identity, upstream exclusion, detail lifecycle)"},
        ensure_ascii=False, indent=2), encoding="utf-8")
    passed = sum(1 for c in checks if c["ok"])
    print(f"[{'FAIL' if fail else 'OK'}] {passed}/{len(checks)} second-audit regression checks")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
