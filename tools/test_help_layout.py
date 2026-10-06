"""Help occupies the whole right workspace after visiting other mounted pages."""
import argparse
import json
import time
from pathlib import Path
from test_real_model_flow import UI


def run(p, wide):
    ui = UI(p)
    if wide and any(w.get('t') == '并排' for w in ui.widgets()):
        ui.click(ident='layout_toggle')
    initial = ui.state()
    ui.fill('chat_input', '帮助切换保留草稿')
    for index, entry in enumerate(['账本', '日历', '数据', '账本']):
        ui.click(entry)
        old_title = '支出账本' if entry == '账本' else '本地数据' if entry == '数据' else '今天'
        ui.find(old_title)
        ui.click('帮助')
        ui.find('慢慢来，先记一件事。')
        assert old_title not in [w.get('t') for w in ui.widgets()], 'Previous page leaked into help'
        snapshot = p.snapshot()['s']
        help_box = next(w['r'] for w in snapshot if w.get('i') == 'help_page')
        work_box = next(w['r'] for w in snapshot if w.get('i') == 'workspace_column')
        hx, hy, hw, hh = help_box
        wx, wy, ww, wh = work_box
        assert hh > wh*.70 and hy < wy+120, (help_box, work_box)
        assert hw > ww*.90 and hy+hh >= wy+wh-24, (help_box, work_box)
        if index == 0:
            ui.evidence('01-help-full-workspace')
        ui.click('‹ 返回刚才的页面')
        ui.find(old_title)
        assert '慢慢来，先记一件事。' not in [w.get('t') for w in ui.widgets()]
    # Queue a fast page/help transition, then ensure the settled layout stays exclusive.
    for text in ['账本', '帮助', '日历', '帮助']:
        x,y,w,h=ui.find(text,ty='Button')['r']
        p.request('click',x=x+w/2,y=y+h/2,wait=0)
        time.sleep(.08)
    time.sleep(.5)
    assert '支出账本' not in [w.get('t') for w in ui.widgets()]
    assert '以这一天补记' not in [w.get('t') for w in ui.widgets()]
    ui.click('对话')
    assert ui.find(ident='chat_input')['t'] == '帮助切换保留草稿'
    assert ui.state() == initial
    report = dict(passed=True,wide=wide,real_provider=False,checks=['ledger/calendar/data to help exclusive', 'help full workspace geometry', 'back restores source page', 'rapid transitions', 'chat draft preserved', 'no business writes'])
    (p.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--output',type=Path,required=True)
    a.add_argument('--desktop',action='store_true')
    a.add_argument('--wide',action='store_true')
    args=a.parse_args()
    if args.desktop:
        from desktop_flow_probe import DesktopProbe
        p=DesktopProbe(Path('bundle'),args.output)
        p.wait_ready()
    else:
        from test_workspace_ui import Probe
        p=Probe(args.output,size='1280x900' if args.wide else '412x892',binary=Path('../build/native-update-20261006/OctoSense/target/release/card-host.exe'))
    try:
        run(p,args.wide or args.desktop)
    except BaseException:
        try: UI(p).evidence('failure')
        except Exception: pass
        raise
    finally:
        p.stop()
