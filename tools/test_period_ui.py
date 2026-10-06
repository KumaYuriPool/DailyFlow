"""Real clicks for manual period source CRUD and generic calendar projection."""
import argparse,json,time
from pathlib import Path
from test_workspace_ui import Probe
from test_real_model_flow import UI
def run(p,wide):
 ui=UI(p)
 if wide:ui.click(ident='layout_toggle')
 def app():
  ui.click('全部');ui.fill('picker_search','经期');ui.click('经期记录')
 def click_visible(text):
  for _ in range(14):
   widgets=[w for w in ui.widgets() if w.get('t')==text and w.get('ty')=='Button' and 120<w['r'][1]<int(p.size.split('x')[1])-55]
   if widgets:
    x,y,w,h=widgets[0]['r'];p.request('click',x=x+w/2,y=y+h/2,wait=1);time.sleep(.2);return
   p.request('m',k='scroll',x=int(p.size.split('x')[0])-95,y=480,dy=230,wait=1);time.sleep(.2)
  raise AssertionError('Unreachable '+text)
 app();ui.click('+ 记一次经期');ui.fill('record_date','2026-09-29');ui.fill('record_end','2026-10-03');ui.evidence('01-edit')
 ui.click('保存记录');ui.find('2026-09-29 至 2026-10-03');first=ui.state();assert len(first['period_entries'])==1 and not first['flows']
 pid=first['period_entries'][0]['id'];ui.click('2026-09-29 至 2026-10-03');ui.find('结束：2026-10-03');ui.evidence('02-detail')
 ui.click('修改');ui.fill('record_end','2026-10-02');ui.click('保存记录');ui.find('结束：2026-10-02');assert ui.state()['period_entries'][0]['id']==pid
 ui.click('日历');ui.fill('date_jump','2026-10-01');ui.click('定位');click_visible('已发生 · 经期');ui.find('结束：2026-10-02');ui.evidence('03-calendar-source')
 before=ui.state();p.stop();p.start();app();ui.find('2026-09-29 至 2026-10-02');assert ui.state()==before
 ui.click('2026-09-29 至 2026-10-02');click_visible('删除源记录');click_visible('删除源记录');assert not ui.state()['period_entries'];ui.evidence('04-deleted')
 assert '[E]' not in (p.output/'runtime.log').read_text(encoding='utf8')
 report=dict(passed=True,wide=wide,real_provider=False,checks=['search/open third App','manual date interval save','read before edit','same-ID correction','calendar interval opens source','restart','two-step delete','no automatic Flow'])
 (p.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--binary',type=Path,required=True);a.add_argument('--wide',action='store_true');args=a.parse_args();p=Probe(args.output,size='1280x900' if args.wide else '412x892',binary=args.binary)
 try:run(p,args.wide)
 except BaseException:
  try:UI(p).evidence('failure')
  except Exception:pass
  raise
 finally:p.stop()
