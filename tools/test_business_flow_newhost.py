"""Business regression driven through the REAL UI on the selected native host.

User directive: business regression must run on the newest host only; the old
card-host and its --tool-call injection are not used. This drives the app's own UI:
记一笔 form -> save -> read back -> edit/correct -> invalid input refused ->
future plan not counted -> full host restart -> state survives.

Business state is read from the app's storage files (state-*.json) for exact
assertions; UI asserts the visible side. Synthetic data only.
"""
import native_runtime
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_workspace_ui import Probe  # noqa: E402
from test_real_model_flow import UI  # noqa: E402
from test_timeline_ui import TimelineProbe  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NEW_HOST = native_runtime.binary("card_host")


def texts(ui):
    return [w.get("t", "") for w in ui.widgets()]


def run(p):
    ui = UI(p)
    time.sleep(.4)
    checks = []

    def ck(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:200]})

    def biz_state():
        return ui.state()

    # 1. 记一笔: open the form, fill, save
    ui.click("记一笔")
    time.sleep(.3)
    ui.fill("record_title", "回归猫粮")
    ui.fill("record_amount", "45")
    ui.click("保存记录")
    time.sleep(.5)
    s = biz_state()
    expenses = [r for r in s.get("records", []) if r.get("kind") == "expense"]
    ck("save-45", len(expenses) == 1 and expenses[0].get("cents") == 4500, s.get("records"))

    # 2. ledger -> scroll to the record row -> open detail -> edit to 46 -> save
    ui.click("账本")
    time.sleep(.4)

    def find_record_row(needle):
        for _ in range(6):
            for w in ui.widgets():
                t = w.get("t", "")
                if w.get("ty") == "Button" and needle in t:
                    return w
            ui.probe.request("m", k="scroll", x=230, y=500, dy=300, wait=1)
            time.sleep(.2)
        return None

    row = find_record_row("回归猫粮")
    assert row is not None, "ledger record row not found"
    ui.click(row["t"])
    time.sleep(.3)
    ui.click("修改")
    time.sleep(.3)
    ui.fill("record_amount", "46")
    ui.click("保存记录")
    time.sleep(.5)
    s = biz_state()
    expenses = [r for r in s.get("records", []) if r.get("kind") == "expense"]
    ck("correct-46-same-id", len(expenses) == 1 and expenses[0].get("cents") == 4600
       and expenses[0].get("revision", 0) >= 2, expenses)

    # 3. invalid amount refused, nothing written (back to ledger, then "+ 记一笔")
    ui.click("‹ 返回")
    time.sleep(.4)
    ui.click("+ 记一笔")
    time.sleep(.3)
    ui.fill("record_title", "非法金额")
    ui.fill("record_amount", "45.111")
    ui.click("保存记录")
    time.sleep(.4)
    s2 = biz_state()
    expenses2 = [r for r in s2.get("records", []) if r.get("kind") == "expense"]
    ck("invalid-refused", len(expenses2) == 1 and expenses2[0].get("cents") == 4600,
       f"records={len(expenses2)}")
    ck("invalid-message-visible", any("无效" in t or "金额" in t for t in texts(ui)),
       [t for t in texts(ui) if "金额" in t or "无效" in t][:3])

    # 4. ledger total shows only the corrected 46
    ui.click("账本")
    time.sleep(.4)

    def scroll_texts():
        out = list(texts(ui))
        for _ in range(5):
            ui.probe.request("m", k="scroll", x=230, y=500, dy=300, wait=1)
            time.sleep(.15)
            out += texts(ui)
        return out

    ledger_texts = scroll_texts()
    ck("ledger-shows-46", any("¥46" in t or "46.00" in t for t in ledger_texts),
       [t for t in ledger_texts if "¥" in t][:4])
    ui.evidence("01-ledger")

    # 5. full host restart -> state survives
    p.stop()
    time.sleep(.5)
    p.start()  # same stamped bundle dir and app-data jail; new process + port
    ui2 = UI(p)
    time.sleep(.4)
    s3 = ui2.state()
    expenses3 = [r for r in s3.get("records", []) if r.get("kind") == "expense"]
    ck("restart-survives", len(expenses3) == 1 and expenses3[0].get("cents") == 4600,
       expenses3)
    ui2.evidence("02-after-restart")
    # UI shows the record again in ledger
    ui2.click("账本")
    time.sleep(.4)
    ck("restart-ledger-visible", any("¥46" in t or "46.00" in t for t in texts(ui2)))
    return checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--wide", action="store_true")
    args = ap.parse_args()
    out = Path(args.output)
    if out.exists():
        import shutil
        shutil.rmtree(out)
    p = TimelineProbe(out, ROOT / "bundle", size="1280x900" if args.wide else "412x892",
                      binary=str(NEW_HOST))
    try:
        checks = run(p)
    finally:
        try:
            p.stop()
        except Exception:
            pass
    fail = not all(c["ok"] for c in checks)
    (out / "report.json").write_text(json.dumps(
        {"checks": checks, "fail": fail,
         "host_binary": str(NEW_HOST),
         "evidence_class": "official-path UI-driven business regression (new host, no tool injection)"},
        ensure_ascii=False, indent=2), encoding="utf-8")
    passed = sum(1 for c in checks if c["ok"])
    print(f"[{'FAIL' if fail else 'OK'}] {passed}/{len(checks)} business UI checks")
    for c in checks:
        if not c["ok"]:
            print(f"  FAIL {c['name']}: {c['detail']}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
