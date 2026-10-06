"""Actual calendar/detail clicks after repairing a synthetic pre-fix compound."""
import argparse,json,time
from pathlib import Path
from test_workspace_ui import Probe
from test_real_model_flow import UI

def visible_click(p,ui,text):
 for _ in range(15):
  targets=[w for w in ui.widgets() if w.get('t')==text and w.get('ty')=='Button' and 120<w['r'][1]<int(p.size.split('x')[1])-65]
  if targets:
   x,y,w,h=targets[0]['r'];p.request('click',x=x+w/2,y=y+h/2,wait=1);time.sleep(.2);return
  p.request('m',k='scroll',x=int(p.size.split('x')[0])-95,y=520,dy=220,wait=1);time.sleep(.15)
 raise AssertionError('Unreachable '+text)

def run(p,wide):
 ui=UI(p)
 if wide:ui.click(ident='layout_toggle')
 repaired=ui.state();assert len(repaired['relations'])==1 and not repaired['flows']
 assert list((p.apps/'dailyflow').glob('pre-source-relations-v1-*.json'))
 ui.click('日历');visible_click(p,ui,'已发生 · 做SPA · ¥350.00');ui.find('做SPA');ui.find('费用 · SPA花费 ¥350.00');ui.evidence('01-event-detail')
 ui.click('费用 · SPA花费 ¥350.00');ui.find('¥350.00');ui.find('相关事项 · 做SPA');ui.find('定位到日历');ui.evidence('02-expense-detail')
 ui.click('修改');ui.fill('record_amount','320');ui.click('保存记录');ui.find('¥320.00')
 ui.click('日历')
 # Scroll until the combined row is visible, then capture before opening it.
 for _ in range(12):
  candidates=[w for w in ui.widgets() if w.get('t')=='已发生 · 做SPA · ¥320.00' and 120<w['r'][1]<int(p.size.split('x')[1])-65]
  if candidates:break
  p.request('m',k='scroll',x=int(p.size.split('x')[0])-95,y=520,dy=220,wait=1);time.sleep(.15)
 else:raise AssertionError('Combined calendar item absent')
 assert not any(w.get('t')=='SPA花费  ¥320.00' for w in ui.widgets());ui.evidence('03-single-calendar-item')
 ui.click('账本');ui.find('全部支出 ¥320.00');assert sum(r['cents'] for r in ui.state()['records'])==32000
 before=ui.state();p.stop();p.start();assert ui.state()==before
 assert '[E]' not in (p.output/'runtime.log').read_text(encoding='utf8')
 report=dict(passed=True,wide=wide,real_provider=False,checks=['backup and repair on boot','one ordinary calendar item with amount','source-to-expense navigation','date locator remains in detail','same-ID correction reflects combined calendar','ledger counted once','restart idempotent'])
 (p.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--seed',type=Path,required=True);a.add_argument('--binary',type=Path,required=True);a.add_argument('--wide',action='store_true');args=a.parse_args();p=Probe(args.output,args.seed,size='1280x900' if args.wide else '412x892',binary=args.binary)
 try:run(p,args.wide)
 except BaseException:
  try:UI(p).evidence('failure')
  except Exception:pass
  raise
 finally:p.stop()
