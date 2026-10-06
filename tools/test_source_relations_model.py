"""One real Provider SPA compound save in the full host, isolated synthetic data."""
import argparse,json,time
from pathlib import Path
from desktop_flow_probe import DesktopProbe,ROOT
from test_real_model_flow import UI

def run(p):
 p.wait_ready();ui=UI(p);ui.fill('chat_input','今天去做SPA花了350元。');ui.click('发送')
 deadline=time.monotonic()+60
 while time.monotonic()<deadline:
  if ui.state().get('records'):break
  time.sleep(.4)
 ui.evidence('01-real-save');state=ui.state()
 assert len(state['records'])==1 and state['records'][0]['cents']==35000
 assert len(state['calendar_events'])==1 and not state['flows']
 expense=state['records'][0];event=state['calendar_events'][0]
 assert any(r['type']=='expense_for' and r['flow_id']=='' and r['from_node']==event['id'] and r['to_node']==expense['id'] for r in state['relations'])
 ui.click('相关操作 ▾');ui.find('查看源记录');assert not any(w.get('t')=='在日历查看' for w in ui.widgets());ui.evidence('02-actions')
 ui.click('查看源记录');ui.find('定位到日历');ui.click('日历')
 label='已发生 · '+event['title']+' · ¥350.00'
 for _ in range(12):
  box=next(w['r'] for w in p.snapshot()['s'] if w.get('i')=='calendar_page');x,y,w,h=box
  visible=[item for item in ui.widgets() if item.get('t')==label and y<=item['r'][1] and item['r'][1]+item['r'][3]<=y+h]
  if visible:break
  p.request('m',k='scroll',x=x+w*.8,y=y+h*.7,dy=180,wait=1);time.sleep(.2)
 else:raise AssertionError('Combined calendar row not visible')
 assert not any(item.get('t')==expense['title']+'  ¥350.00' for item in ui.widgets())
 ui.evidence('03-one-calendar-item');assert ui.state()==state
 usage=json.loads((p.apps/'.host/model/ledger.json').read_text(encoding='utf8'))['apps']['dailyflow'];assert usage['calls']==1 and usage['tokens']>0
 report=dict(passed=True,real_provider=True,requests=1,usage=usage,checks=['ungrouped SPA compound saved and linked','no calendar action in reply','locator remains in details','one ordinary calendar row / one expense','navigation read-only'])
 (p.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);args=a.parse_args();p=DesktopProbe(ROOT/'bundle',args.output,core_dir=Path.home()/'.octosense/octos-home/.octos')
 try:run(p)
 except BaseException:
  try:UI(p).evidence('failure')
  except Exception:pass
  raise
 finally:p.stop()
