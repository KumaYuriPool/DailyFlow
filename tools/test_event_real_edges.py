"""Real Provider ambiguity tests against prior synthetic Provider state."""
import argparse,json,time
from pathlib import Path
from desktop_flow_probe import DesktopProbe,ROOT
from test_real_model_flow import UI
def run(p):
    p.wait_ready();ui=UI(p);ui.click('说一件事');before=ui.state()
    for i,text in enumerate(['洗护费改成100元。','团子有两次洗护，这笔护理用品花了5元，归哪次我还不确定。']):
        ui.fill('chat_input',text);ui.click('发送')
        until=time.monotonic()+60
        while time.monotonic()<until:
            if not any(w.get('t')=='正在处理…' for w in ui.widgets()):break
            time.sleep(.3)
        ui.evidence(f'0{i+1}-ambiguity');ui.find('补充并继续');assert ui.state()==before
        print('Real ambiguity clarified:',text,flush=True)
        ui.click('取消')
    ui.click('说一件事');ui.click('账本日历');ui.evidence('03-desktop-ledger')
    (p.output/'report.json').write_text(json.dumps(dict(passed=True,real_provider=True,requests=2,checks=['multiple correction candidates clarify','uncertain event association clarify','no write on ambiguity']),ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--seed',type=Path,required=True);a=p.parse_args()
    probe=DesktopProbe(ROOT/'bundle',a.output,Path.home()/'.octosense/octos-home/.octos',seed_state=a.seed)
    try:run(probe)
    finally:probe.stop()
