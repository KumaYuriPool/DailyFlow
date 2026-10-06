"""Real hidden UI checks, synthetic state only; no Provider requests or native edits."""
import argparse
import json
import time
from pathlib import Path

import native_runtime
from test_workspace_ui import Probe
from test_real_model_flow import UI

ROOT = Path(__file__).resolve().parents[1]


def rectangle(probe, ident):
    return next(w['r'] for w in probe.snapshot()['s'] if w.get('i') == ident)


def seek(ui, text):
    for _ in range(12):
        x, y, width, height = rectangle(ui.probe, 'workspace_column')
        targets = [w for w in ui.widgets() if w.get('ty') == 'Button' and w.get('t') == text]
        ty, th = (targets[0]['r'][1], targets[0]['r'][3]) if targets else (y+height, 0)
        if targets and y + 65 <= ty and ty + th < y + height:
            ui.click(text, ty='Button')
            return
        ui.probe.request('m', k='scroll', x=x+width/2, y=y+height*.65,
                         dy=180 if ty+th >= y+height else -180, wait=1)
        time.sleep(.15)
    raise AssertionError('Unreachable workspace button: '+text)


def resize_desktop(probe, delta):
    # Resize only this harness's owned app frame; geometry comes from its snapshot.
    card = next(w for w in probe.snapshot()['s'] if w.get('ty') == 'Splash' and w.get('i') == 'card')
    x, y, width, height = card['r']
    right, mid = x+width+1, y+height/2
    for kind, px in [('move', right), ('down', right), ('move', right+delta), ('up', right+delta)]:
        probe.request('m', k=kind, x=px, y=mid, wait=1)
    time.sleep(.3)


def run(probe, desktop=False):
    ui = UI(probe)
    initial = ui.state()
    if not desktop:
        ui.click('并排查看')
    else:
        ui.find('单列查看')  # Real on_app_resize, no script injection.
    ui.fill('chat_input', '尚未发送的四列草稿')
    ui.click('日历')
    ui.click('团子 · 洗护', ty='Button')
    ui.fill('date_jump', '2026-10-04')
    ui.click('定位')
    ui.click('普通日历 ▾')
    ui.click('账本日历 · 来源：记账')
    ui.find('此事件')
    ui.find('¥275')
    before = rectangle(probe, 'workspace_column')
    chat = rectangle(probe, 'chat_column')
    assert ui.find('DF')['r'][0] < ui.find('Flow')['r'][0] < chat[0] < before[0]
    # Short desktop tiles clip later rows; the tall standalone run verifies all 35 cells.
    days = [w for w in ui.widgets() if w.get('ty') == 'Button' and w.get('t', '').isdigit()
            and before[0] <= w['r'][0] < before[0]+before[2]]
    assert len(days) >= 21 if desktop else len(days) == 35
    # Every day stays within the workspace's horizontal bounds, including its scrollbar gutter.
    assert all(before[0] <= w['r'][0] and w['r'][0]+w['r'][2] <= before[0]+before[2]-12 for w in days)
    ui.evidence('01-four-columns')
    ui.click('放大')
    expanded = rectangle(probe, 'workspace_column')
    assert expanded[2] > before[2]+250
    assert not any(w.get('i') == 'chat_input' for w in ui.widgets())
    ui.evidence('02-expanded')
    ui.click('恢复')
    assert rectangle(probe, 'workspace_column') == before
    assert rectangle(probe, 'chat_column') == chat
    assert ui.find(ident='chat_input')['t'] == '尚未发送的四列草稿'
    ui.click('收起')
    ui.click('打开工作区')
    assert ui.find(ident='date_jump')['t'] == '2026-10-04'
    ui.find('账本日历 ▾')
    ui.find('此事件')
    ui.click('›')
    assert ui.find(ident='date_jump')['t'] == '2026-11-04'
    ui.click('账本日历 ▾')
    ui.fill('picker_search', '日历')
    ui.click('放大')
    ui.click('恢复')
    assert ui.find(ident='picker_search')['t'] == '日历'
    ui.click('普通日历 · 来源：日历')
    assert ui.find(ident='date_jump')['t'] == '2026-11-04'
    ui.click('记一笔')
    fields = {'record_title': '暂不保存的编辑', 'record_date': '2026-10-03', 'record_amount': '987.65'}
    for ident, value in fields.items():
        ui.fill(ident, value)
    ui.click('放大')
    ui.click('收起')
    ui.click('打开工作区')
    ui.click('恢复')
    for ident, value in fields.items():
        assert ui.find(ident=ident)['t'] == value
    ui.evidence('03-edit-draft-retained')
    ui.click('‹ 返回')
    assert ui.find(ident='date_jump')['t'] == '2026-11-04'
    ui.click('‹')
    seek(ui, '以这一天补记')
    assert ui.find(ident='chat_input')['t'] == '尚未发送的四列草稿'
    assert any(w.get('t') == '补记 · 2026-10-04 · 团子 · 洗护' for w in ui.widgets())
    if desktop:
        resize_desktop(probe, -230)
        ui.find('回到对话')
        assert not any(w.get('t') == 'Flow' or w.get('i') == 'chat_input' for w in ui.widgets())
        ui.evidence('04-auto-compact')
        resize_desktop(probe, 230)
        ui.find('放大')
        assert ui.find(ident='chat_input')['t'] == '尚未发送的四列草稿'
        ui.evidence('05-auto-wide')
    else:
        ui.click('单列查看')
        ui.find('回到对话')
        ui.click('回到对话')
        assert ui.find(ident='chat_input')['t'] == '尚未发送的四列草稿'
        ui.click('并排查看')
        ui.click('打开工作区')
        ui.find('放大')
    assert ui.state() == initial, 'Layout, search, browsing and uncommitted drafts must not write business data'
    ui.click('账本', ty='Button')
    seek(ui, '2026-10-04  洗护费  ¥110.00')
    ui.click('修改')
    ui.fill('record_amount', '111')
    ui.click('保存记录')
    changed = ui.state()
    assert len(changed['records']) == len(initial['records'])
    assert next(r for r in changed['records'] if r['id'] == 'r2')['cents'] == 11100
    ui.find('支出 ¥276.00')  # The persistent Flow rail must refresh from the saved source.
    ui.evidence('06-saved-source-and-flow')
    log = probe.output/('desktop.log' if desktop else 'runtime.log')
    assert '[E]' not in log.read_text(encoding='utf8')
    report = dict(passed=True, desktop=desktop, real_provider=False, visible_calendar_cells=len(days),
                  original_workspace=before, expanded_workspace=expanded,
                  checks=['four columns', 'expand/restore exact geometry', 'chat and edit draft retention',
                          'close/reopen retains route and state', 'search retained during expand/restore',
                          'month/date/scope/view retention', 'explicit backfill keeps wide workspace open',
                          'real Shell resize hook' if desktop else 'standalone layout switch',
                          'no business write from navigation or drafts', 'same-ID save refreshes Flow sidebar'])
    (probe.output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=Path, required=True)
    parser.add_argument('--desktop', action='store_true')
    args = parser.parse_args()
    if args.desktop:
        from desktop_flow_probe import DesktopProbe
        probe = DesktopProbe(ROOT/'bundle', args.output, seed_state=args.seed)
    else:
        probe = Probe(args.output, args.seed, size='1280x900', binary=native_runtime.binary('card_host'))
    try:
        if args.desktop:
            probe.wait_ready()
        run(probe, args.desktop)
    except BaseException:
        UI(probe).evidence('failure')
        raise
    finally:
        probe.stop()
