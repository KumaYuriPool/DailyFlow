"""Read the bundled guide through real controls, with isolated data and no model."""
import argparse
import json
import time
from pathlib import Path
from test_workspace_ui import Probe
from test_real_model_flow import UI


def click_topic(p, ui, title):
    height = int(p.size.split('x')[1])
    for _ in range(10):
        buttons = [w for w in ui.widgets() if w.get('t') == title and w.get('ty') == 'Button']
        if not buttons:
            p.request('m', k='scroll', x=int(p.size.split('x')[0])-85, y=550, dy=180, wait=1)
            continue
        button = buttons[0]
        x, y, width, h = button['r']
        if 200 < y and y+h < height-20:
            ui.click(title, ty='Button')
            return
        p.request('m', k='scroll', x=int(p.size.split('x')[0])-85, y=550, dy=180 if y>200 else -180, wait=1)
    raise AssertionError('Guide topic unreachable: '+title)


def run(p, wide):
    ui = UI(p)
    if wide:
        ui.click(ident='layout_toggle')
    before = ui.state()
    ui.fill('chat_input', '还没发出的午餐记录')
    ui.click('帮助')
    ui.find('慢慢来，先记一件事。')
    ui.evidence('01-directory')
    topics = json.loads((Path(__file__).resolve().parents[1]/'src/user_guide.json').read_text(encoding='utf8'))
    for index, section in enumerate(topics):
        click_topic(p, ui, section['title'])
        for _ in range(5):
            p.request('m', k='scroll', x=int(p.size.split('x')[0])-85, y=300, dy=-300, wait=1)
        seen = {w.get('t') for w in ui.widgets()}
        ui.evidence(f'02-topic-{index}')
        # Check scrolling exposes the last paragraph and the directory remains reachable.
        for _ in range(6):
            p.request('m', k='scroll', x=int(p.size.split('x')[0])-85, y=550, dy=250, wait=1)
            time.sleep(.06)
            seen.update(w.get('t') for w in ui.widgets())
        assert all(paragraph in seen for paragraph in section['paragraphs']), 'Unreadable guide paragraph'
        last = ui.find(section['paragraphs'][-1])
        assert last['r'][1] < int(p.size.split('x')[1])-20
        ui.evidence(f'03-topic-bottom-{index}')
        for _ in range(8):
            p.request('m', k='scroll', x=int(p.size.split('x')[0])-85, y=300, dy=-300, wait=1)
        ui.click('‹ 说明目录')
    ui.click('‹ 返回刚才的页面')
    assert ui.find(ident='chat_input')['t'] == '还没发出的午餐记录'
    ui.click('记一笔')
    ui.fill('record_title', '尚未保存的手工记录')
    ui.fill('record_amount', '18')
    ui.click('帮助')
    ui.click('‹ 返回刚才的页面')
    assert ui.find(ident='record_title')['t'] == '尚未保存的手工记录'
    assert ui.find(ident='record_amount')['t'] == '18'
    ui.click('全部')
    ui.fill('picker_search', '使用说明')
    ui.click('使用说明', ty='Button')
    ui.find('慢慢来，先记一件事。')
    ui.click('‹ 返回刚才的页面')
    assert ui.find(ident='record_title')['t'] == '尚未保存的手工记录'
    assert ui.state() == before, 'Guide must not write business data'
    assert '[E]' not in (p.output/'runtime.log').read_text(encoding='utf8')
    report = dict(passed=True, wide=wide, topics=len(topics), real_provider=False, checks=['offline guide and every topic', 'scrollable content and directory', 'chat draft preserved', 'manual edit draft preserved', 'searchable entry and route return', 'no business writes'])
    (p.output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--output', type=Path, required=True)
    a.add_argument('--binary', type=Path, required=True)
    a.add_argument('--wide', action='store_true')
    args = a.parse_args()
    p = Probe(args.output, size='1280x900' if args.wide else '412x892', binary=args.binary)
    try:
        run(p, args.wide)
    except BaseException:
        try: UI(p).evidence('failure')
        except Exception: pass
        raise
    finally:
        p.stop()
