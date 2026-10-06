"""Actual UI clicks with injected replies, isolated data; no Provider calls."""
import argparse,json,time
from pathlib import Path
from test_workspace_ui import Probe
from test_real_model_flow import UI
MOCK='''
fn compact_test_model(route,payload,callback){
    let text = payload.input.conversation[payload.input.conversation.len()-1].text
    let reply = {intent: "create" title: "洗护费" amount: "120" subject: "团子" event_title: "洗护"}
    if text == "金额不明确" { reply = {intent: "clarify" question: "实际花了多少元？"} }
    callback({is_ok: true data: {output: reply}})
}
'''
def run(p,wide):
    ui=UI(p)
    def texts():return [w.get('t','') for w in ui.widgets()]
    def shot(n):ui.evidence(n)
    def send(text):
        ui.fill('chat_input',text);ui.click('发送');time.sleep(.3)
    def header():
        nodes=[ui.find(ident='layout_toggle'),next(w for w in ui.widgets() if w.get('t','').startswith('范围 · ')),ui.find('+ 说件新事'),ui.find(ident='workspace_toggle')]
        assert max(w['r'][1] for w in nodes)-min(w['r'][1] for w in nodes)<2,nodes
        assert all(nodes[i]['r'][0]+nodes[i]['r'][2]<=nodes[i+1]['r'][0] for i in range(3)),nodes
        assert nodes[-1]['r'][0]+nodes[-1]['r'][2]<=int(p.size.split('x')[0]),nodes
    assert not any(t.startswith('试试：') for t in texts());header()
    if wide:
        if '并排' in texts():ui.click(ident='layout_toggle')
        ui.find('单列')
    shot('01-header')
    send('给团子洗护花了120元')
    assert texts().count('已保存：洗护费 · ¥120.00')==1,texts()
    assert not any(t.startswith('已保存 · ') for t in texts())
    assert '查看源记录' not in texts() and '回看相关记录' not in texts()
    ui.find('相关操作 ▾');shot('02-saved-collapsed')
    ui.click('相关操作 ▾');ui.find('查看源记录');assert '在日历查看' not in texts();ui.find('回看相关记录');shot('03-expanded')
    ui.click('相关操作 ▴');assert '查看源记录' not in texts()
    ui.click('相关操作 ▾');ui.click('查看源记录');ui.find('洗护费')
    ui.click(ident='workspace_toggle');ui.find('相关操作 ▴')
    # Query collapses prior saved actions and exposes only its own references.
    saved=ui.state();send('团子一共花了多少钱？')
    ui.find('相关操作 ▾');assert '查看源记录' not in texts() and not any(t.startswith('来源 · ') for t in texts())
    ui.click('相关操作 ▾');ui.find('来源 · 洗护费');ui.click('来源 · 洗护费');ui.find('洗护费')
    shot('04-source')
    if wide:
        ui.fill('chat_input','保留草稿');ui.click('放大');ui.click('恢复');assert ui.find(ident='chat_input')['t']=='保留草稿'
    ui.click(ident='workspace_toggle')
    send('金额不明确');assert texts().count('实际花了多少元？')==1,texts();shot('05-single-clarification')
    assert '来源 · 洗护费' not in texts();assert ui.state()==saved
    ui.click('+ 说件新事');assert '相关操作 ▾' not in texts() and '相关操作 ▴' not in texts()
    ui.fill('chat_input','保留的草稿');ui.click(ident='workspace_toggle');ui.click(ident='workspace_toggle');assert ui.find(ident='chat_input')['t']=='保留的草稿';header()
    log=p.output/'runtime.log'
    if not log.exists():log=p.output/'desktop.log'
    assert '[E]' not in log.read_text(encoding='utf8')
    report=dict(passed=True,wide=wide,real_provider=False,checks=['one header row and ordered compact controls','sample button removed','saved reply once','actions collapsed and reversible','source and calendar/Flow entries grouped','query resets disclosure and old receipt','source opens','clarification rendered once','new conversation clears actions','workspace keeps draft','no navigation/query data writes'])
    (p.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--wide',action='store_true');a.add_argument('--binary',type=Path,required=True);args=a.parse_args()
    p=Probe(args.output,size='1280x900' if args.wide else '412x892',binary=args.binary)
    try:
        p.stop();file=p.bundle/'main.splash';s=file.read_text(encoding='utf8').replace('host.request("model.complete",','compact_test_model("model.complete",');s=s.replace('start_timeout(0.08,|| boot())',MOCK+'\nstart_timeout(0.08,|| boot())');file.write_text(s,encoding='utf8');p.start();run(p,args.wide)
    except BaseException:
        try:UI(p).evidence('failure')
        except Exception:pass
        raise
    finally:p.stop()
