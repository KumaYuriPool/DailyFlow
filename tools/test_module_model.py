"""One actual Provider compound query with isolated synthetic source records."""
import argparse,json,time
from pathlib import Path
from desktop_flow_probe import DesktopProbe,ROOT
from test_real_model_flow import UI
def run(probe):
    probe.wait_ready();ui=UI(probe);before=ui.state()
    ui.fill('chat_input','团子这个月花了多少，下次洗护是什么时候？')
    started=time.monotonic();ui.click('发送')
    end=time.monotonic()+55
    while time.monotonic()<end:
        if not any(w.get('t') in ('正在理解…','正在处理…') for w in ui.widgets()):break
        time.sleep(.4)
    ui.evidence('01-compound')
    texts=[w.get('t','') for w in ui.widgets()]
    assert any('150.00' in t and '2026-12-10' in t for t in texts),texts
    assert ui.state()==before,'Query wrote business data'
    elapsed=round(time.monotonic()-started,3)
    ui.click('相关操作 ▾')
    for _ in range(8):
        if any(w.get('t')=='来源 · 猫粮' for w in ui.widgets()):break
        x,y,width,height=next(w['r'] for w in probe.snapshot()['s'] if w.get('i')=='home_page')
        probe.request('m',k='scroll',x=x+width/2,y=y+height*.7,dy=160,wait=1);time.sleep(.2)
    ui.evidence('01-sources')
    ui.click('来源 · 猫粮');ui.evidence('02-source')
    assert any(w.get('t')=='猫粮' for w in ui.widgets())
    assert ui.state()==before
    usage=json.loads((probe.apps/'.host/model/ledger.json').read_text(encoding='utf8'))['apps']['dailyflow']
    assert usage['calls']==1 and usage['tokens']>0
    report=dict(passed=True,real_provider=True,requests=1,usage=usage,seconds=elapsed,total_minor=15000,next_date='2026-12-10',read_only=True,source_opened=True)
    (probe.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--seed-state',type=Path,required=True);a=p.parse_args()
    probe=DesktopProbe(ROOT/'bundle',a.output,core_dir=Path.home()/'.octosense/octos-home/.octos',seed_state=a.seed_state)
    try:run(probe)
    finally:probe.stop()
