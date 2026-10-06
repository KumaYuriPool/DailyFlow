"""Real UI search/details/edit/return, synthetic state, no model invocation."""
import argparse,json,time
from pathlib import Path
from test_workspace_ui import Probe
from test_real_model_flow import UI

def run(p,wide):
 ui=UI(p)
 if wide:ui.click(ident='layout_toggle')
 ui.evidence('01-home')
 assert not any(w.get('t') in ('Flow','支出 ¥120.00') for w in ui.widgets())
 ui.fill('chat_input','还没说完的草稿')
 before=ui.state();ui.click('查找');ui.fill('recall_input','团子洗护');ui.click('搜索')
 ui.find('找到 3 条 · 按时间排列');ui.find('计划 · 再次护理');ui.evidence('02-timeline')
 assert ui.state()==before
 ui.click('为什么找到这些 ▾');ui.find('日历 · 与「团子洗护」有已确认关联');ui.click('为什么找到这些 ▾')
 ui.fill('recall_input','团');ui.click('搜索');ui.click('回看 团子 · 3 条 · 2026-10-04 起');ui.find('找到 3 条 · 按时间排列')
 assert ui.state()==before
 ui.click('团子洗护费  ¥120.00');ui.find('团子洗护费');ui.evidence('03-source')
 assert not any(w.get('t','').startswith('移出 ') for w in ui.widgets())
 ui.click('修改');ui.fill('record_amount','110');ui.click('保存记录');ui.find('¥110.00')
 ui.click('‹ 返回');ui.find('团子洗护费  ¥110.00');ui.evidence('04-refreshed')
 assert len(ui.state()['flows'])==1 and len(ui.state()['records'])==1
 ui.fill('recall_input','不存在');ui.click('搜索');ui.find('找到 0 条 · 按时间排列')
 ui.fill('recall_input','   ');ui.click('搜索');ui.find('输入名字或关键词，回看相关记录。')
 ui.click('对话');assert ui.find(ident='chat_input')['t']=='还没说完的草稿'
 assert any(w.get('t')=='范围 · 全部事件 ▾' for w in ui.widgets()),'Search changed input context'
 snapshot=ui.state();p.stop();p.start()
 if wide:ui.click(ident='layout_toggle')
 ui.click('查找');ui.fill('recall_input','团子洗护');ui.click('搜索');ui.find('团子洗护费  ¥110.00');assert ui.state()==snapshot
 assert '[E]' not in (p.output/'runtime.log').read_text(encoding='utf8')
 report=dict(passed=True,wide=wide,real_provider=False,checks=['no permanent Flow rail','keyword timeline with plan','source details','membership collapsed','same-ID correction refresh after back','empty search','draft/scope unchanged','restart read-only'])
 (p.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--seed',type=Path,required=True);a.add_argument('--binary',type=Path,required=True);a.add_argument('--wide',action='store_true');args=a.parse_args();p=Probe(args.output,args.seed,size='1280x900' if args.wide else '412x892',binary=args.binary)
 try:run(p,args.wide)
 except BaseException:
  try:UI(p).evidence('failure')
  except Exception:pass
  raise
 finally:p.stop()
