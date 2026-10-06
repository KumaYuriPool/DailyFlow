"""One real Provider query of synthetic period records; no real health data."""
import argparse,json,time
from pathlib import Path
from desktop_flow_probe import DesktopProbe,ROOT
from test_real_model_flow import UI
def run(p):
 p.wait_ready();ui=UI(p);before=ui.state()
 ui.fill('chat_input','查一下我2026年9月28日至9月30日的经期记录。')
 ui.click('发送');deadline=time.monotonic()+60
 while time.monotonic()<deadline:
  if not any(w.get('t') in ('正在理解…','正在处理…') for w in ui.widgets()):break
  time.sleep(.4)
 ui.evidence('01-answer');texts=[w.get('t','') for w in ui.widgets()]
 assert any('1次经期记录' in t and '2026-09-28' in t and '2026-09-30' in t for t in texts),texts
 assert ui.state()==before
 ui.click('相关操作 ▾')
 for _ in range(8):
  if any(w.get('t')=='来源 · 经期' for w in ui.widgets()):break
  box=next(w['r'] for w in p.snapshot()['s'] if w.get('i')=='home_page');x,y,w,h=box;p.request('m',k='scroll',x=x+w/2,y=y+h*.7,dy=160,wait=1);time.sleep(.2)
 ui.click('来源 · 经期');ui.find('结束：2026-09-30');ui.evidence('02-source')
 assert ui.state()==before
 usage=json.loads((p.apps/'.host/model/ledger.json').read_text(encoding='utf8'))['apps']['dailyflow']
 assert usage['calls']==1 and usage['tokens']>0
 report=dict(passed=True,real_provider=True,requests=1,usage=usage,read_only=True,source_opened=True)
 (p.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--seed-state',type=Path,required=True);args=a.parse_args();p=DesktopProbe(ROOT/'bundle',args.output,core_dir=Path.home()/'.octosense/octos-home/.octos',seed_state=args.seed_state)
 try:run(p)
 finally:p.stop()
