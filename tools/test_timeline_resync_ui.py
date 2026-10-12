"""Audit R5/R2 live-UI chain: change a source, run the one-command sync, press
刷新 in the running app, and verify the new state — then user-level exclusion,
refresh, still excluded, repeat refresh idempotent.

Real card-host (655114c+patch), production bundle, no model, no fixtures.
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


def sweep(ui, rounds=14, x=1100):
    """Wide layout: the timeline lives in the right workspace column."""
    out = texts(ui)
    for _ in range(rounds):
        ui.probe.request("m", k="scroll", x=x, y=500, dy=200, wait=1)
        time.sleep(0.12)
        out += texts(ui)
    return out


def sweep_back_top(ui):
    """Scroll the right column back to the top (negative dy)."""
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
            time.sleep(0.5)
            return
        ui.click("时间流")
        time.sleep(0.4)
    raise AssertionError("刷新 button not found")


def exclude_first(ui, needle):
    for w in ui.widgets():
        if w.get("ty") == "Button" and needle in (w.get("t") or ""):
            # the record row's 排除 button is the next Button after the row
            rows = [x for x in ui.widgets() if x.get("ty") == "Button"]
            for i, x in enumerate(rows):
                if needle in (x.get("t") or ""):
                    ex = next((b for b in rows[i:] if (b.get("t") or "") == "排除"), None)
                    if ex:
                        ui.click("排除")
                        return True
            break
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
        print(("PASS " if ok else "FAIL ") + name + (f" :: {detail}"[:120] if not ok else ""))

    try:
        ui = UI(probe)
        time.sleep(0.4)
        app_dir = probe.apps / probe.app_id

        # sync v1 baseline into the app jail.
        # ISOLATION (r5 fix): the sync chain runs in a PRIVATE workdir under
        # this run's output; the canonical build/semifinal-202610/synthetic-source
        # tree is only READ (producer pages as overlay base), never written —
        # a leaked overlay would permanently raise the canonical projection's
        # revision ceiling and drop records from every later sync.
        work = out / "synwork"
        subprocess.run([sys.executable, "-X", "utf8", str(SYNC), "--data-root", str(probe.apps),
                        "--out", str(work)],
                       check=True, capture_output=True)
        open_timeline(ui)
        labels = sweep(ui)
        sweep_back_top(ui)
        ck("baseline-visible", any("主题 · " in t or "条 · 按时间排列" in t for t in labels),
           [t for t in labels if "条" in t][:2])

        # ---- R5: source change (the independent source corrects a record);
        # the overlay lives in the private workdir's climbing envelope dir
        # (the producer step does not delete pre-existing extra pages, so the
        # overlay survives and is imported on the next sync).
        canon_dir = ROOT / "build/semifinal-202610/synthetic-source/climbing"
        env_dir = work / "climbing"
        env_dir.mkdir(parents=True, exist_ok=True)
        overlay_path = env_dir / "page-04-source-change.json"
        overlay = {
            "contract_version": 1, "source_app": "synthetic-climbing",
            "source_module": "post", "fetched_at": "2026-10-11T05:00:00Z",
            "snapshot_revision": 2, "records": [], "tombstones": [],
            "page": 1, "page_size": 50, "has_more": False,
        }
        rec = json.loads((canon_dir / "page-01-posts.json").read_text(encoding="utf-8"))["records"][0]
        import hashlib
        rec["source_revision"] = 3
        rec["content"]["title"] = "B 站的攀岩入门视频（已收藏 · 更新）"
        rec["content_hash"] = hashlib.sha256(json.dumps(
            rec["content"], sort_keys=True, ensure_ascii=False,
            separators=(",", ":")).encode("utf-8")).hexdigest()
        overlay["records"].append(rec)
        overlay_path.write_text(
            json.dumps(overlay, ensure_ascii=False, indent=2), encoding="utf-8")

        # one-command sync (no model), then in-app 刷新
        subprocess.run([sys.executable, "-X", "utf8", str(SYNC), "--data-root", str(probe.apps),
                        "--out", str(work)],
                       check=True, capture_output=True)
        press_refresh(ui)
        time.sleep(0.3)
        labels = sweep(ui)
        sweep_back_top(ui)
        ck("resync-new-rev-visible", any("B 站的攀岩入门视频（已收藏 · 更新）" in t for t in labels),
           [t for t in labels if "更新" in t][:2])
        ck("resync-rev3-line", any("rev3" in t for t in labels),
           [t for t in labels if "rev3" in t][:2])
        # old title gone
        ck("resync-old-title-gone", not any(t.endswith("（已收藏）") and "更新" not in t and "攀岩入门视频" in t for t in labels))

        # repeat refresh is idempotent
        press_refresh(ui)
        labels2 = sweep(ui)
        sweep_back_top(ui)
        ck("repeat-refresh-idempotent", any("B 站的攀岩入门视频（已收藏 · 更新）" in t for t in labels2))

        # ---- R2: user-level exclude survives refresh ----
        # the top record is climb-post-001; its row owns the first 排除 button.
        # After sweep_back_top the viewport is at the top, so the first visible
        # 排除 belongs to climb-post-001 — click by coordinates.
        rows = [w for w in ui.widgets() if w.get("ty") == "Button" and (w.get("t") or "") == "排除"]
        assert rows, "排除 button not visible at top"
        x, y, bw, bh = rows[0]["r"]
        ui.probe.request("click", x=x + bw / 2, y=y + bh / 2, wait=1)
        time.sleep(0.4)
        labels3 = sweep(ui)
        ck("exclude-hides-record", not any("B 站的攀岩入门视频（已收藏 · 更新）" in t for t in labels3),
           [t for t in labels3 if "更新" in t][:2])
        press_refresh(ui)
        labels4 = sweep(ui)
        ck("exclude-survives-refresh", not any("B 站的攀岩入门视频（已收藏 · 更新）" in t for t in labels4))
        press_refresh(ui)
        labels5 = sweep(ui)
        ck("exclude-survives-repeat-refresh", not any("B 站的攀岩入门视频（已收藏 · 更新）" in t for t in labels5))

        # ---- R3: read-only detail ----
        sweep_back_top(ui)  # prior sweeps left the viewport at the bottom
        detail_btn = None
        for _ in range(10):
            # the 详情 button immediately after the target row's title label
            wid = ui.widgets()
            titles = [i for i, w in enumerate(wid) if w.get("ty") == "Label" and "第一次室内抱石体验" in (w.get("t") or "")]
            if titles:
                nxt = next((w for w in wid[titles[0]:] if w.get("ty") == "Button" and (w.get("t") or "") == "详情"), None)
                if nxt:
                    detail_btn = nxt
                    break
            ui.probe.request("m", k="scroll", x=1100, y=500, dy=200, wait=1)
            time.sleep(0.12)
        assert detail_btn, "详情 button not found near target row"
        x, y, bw, bh = detail_btn["r"]
        ui.probe.request("click", x=x + bw / 2, y=y + bh / 2, wait=1)
        time.sleep(0.5)
        labels6 = texts(ui)
        ck("detail-read-only-visible", any("导入记录详情（只读）" in t for t in labels6) and
           any("来源身份：" in t for t in labels6),
           [t for t in labels6 if "详情" in t or "来源身份" in t][:3])
        ck("detail-shows-body", any("配文：" in t for t in labels6))
        # the excluded record's detail stays reachable? No: it is hidden; use
        # the visible first row instead — already covered above.
        # back to list, business state untouched
        ui.click("对话")  # leave the detail view (rail entry is always present)
        time.sleep(0.3)
        st = ui.state()
        ck("no-business-write", len(st.get("records", [])) == 0, st.get("records"))
    finally:
        probe.stop()
        # Private synwork dir is kept as run evidence; the canonical
        # synthetic-source tree was never touched, so nothing to clean.
        canon = ROOT / "build/semifinal-202610/synthetic-source/climbing"
        leaked = [p.name for p in canon.glob("page-0[456]-*.json")]
        if leaked:
            print(f"WARNING: unexpected overlay pages in canonical tree: {leaked}")
    # r5 guard: the canonical synthetic-source tree must be untouched and
    # climb-post-001 must not be tombstoned in the canonical projection.
    canon = ROOT / "build/semifinal-202610/synthetic-source"
    pages = sorted(p.name for p in (canon / "climbing").glob("page-*.json"))
    ck("guard-canonical-envelope-set",
       pages == ["page-01-posts.json", "page-02-events.json", "page-03-expenses.json"],
       pages)
    ck("guard-climb-post-001-alive",
       not (canon / "projection-climbing/records/synthetic-climbing/climb-post-001/tombstone.json").exists())
    fail = not all(c["ok"] for c in checks)
    (out / "report.json").write_text(json.dumps(
        {"checks": checks, "fail": fail,
         "evidence_class": "R5/R2/R3 live-UI chain (sync -> refresh -> exclude persists)"},
        ensure_ascii=False, indent=2), encoding="utf-8")
    passed = sum(1 for c in checks if c["ok"])
    print(f"[{'FAIL' if fail else 'OK'}] {passed}/{len(checks)} resync/exclude chain checks")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
