"""Existing desktop + real Provider, synthetic event scenario, fresh data only."""
import argparse,json,time,shutil
from pathlib import Path
from desktop_flow_probe import DesktopProbe,ROOT
from test_real_model_flow import UI

def run(probe):
    probe.wait_ready();ui=UI(probe);ui.evidence('00-calendar')
    ui.click('说一件事')
    def send(text,name,follow=False):
        ui.fill('chat_input',text);ui.click('补充并继续' if follow else '发送')
        end=time.monotonic()+60
        while time.monotonic()<end:
            if not any(w.get('t')=='正在处理…' for w in ui.widgets()):break
            time.sleep(.4)
        ui.evidence(name)
        print(name,json.dumps([w.get('t') for w in ui.widgets() if w.get('ty')=='Label'][-5:],ensure_ascii=False),flush=True)
    send('今天给团子洗护花了120元。','01-fact')
    state=ui.state();assert len(state['records'])==1 and state['records'][0]['cents']==12000,state
    assert len(state['calendar_events'])==1 and len(state['relations'])>=3,state
    fid=state['flows'][0]['id'];eid=state['records'][0]['id']
    send('给团子买护理用品花了35元。','02-associated')
    state=ui.state();assert len(state['records'])==2 and len(state['flows'])==1,state
    assert all(r['flow_ids']==[fid] for r in state['records'])
    send('10月11日15点再带团子去护理。','03-plan')
    state=ui.state();assert sum(r['cents'] for r in state['records'])==15500
    assert any(e['status']=='planned' and e['date']=='2026-10-11' and e['time']=='15:00' for e in state['calendar_events']),state
    assert any(r['type']=='follow_up' for r in state['relations']),state
    send('刚才洗护费不是120，是110。','04-correct')
    state=ui.state();assert len(state['records'])==2 and next(r for r in state['records'] if r['id']==eid)['cents']==11000,state
    revision=state['revision']
    send('这次护理花了多少？','05-query')
    assert ui.state()['revision']==revision
    assert any('145.00' in w.get('t','') for w in ui.widgets())
    send('今天又给团子洗护花了一百多。','06-ambiguous')
    assert ui.state()['revision']==revision;ui.find('补充并继续')
    send('是130元。','07-clarified',True)
    state=ui.state();assert len(state['records'])==3 and sum(r['cents'] for r in state['records'])==27500,state
    ui.click('查看事件');ui.evidence('08-semantic-graph')
    assert any('费用归属' in w.get('t','') for w in ui.widgets())
    (probe.output/'report.json').write_text(json.dumps({'real_provider':True,'requests':7,'passed':True,'same_expense_id':eid,'flow_id':fid,'total_minor':27500},ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--capture-proposal',action='store_true');a=p.parse_args()
    candidate=a.output.with_name(a.output.name+'-candidate');shutil.copytree(ROOT/'bundle',candidate)
    source=(candidate/'main.splash').read_text(encoding='utf8')
    if a.capture_proposal:source=source.replace('let o = r.data.output','let o = r.data.output fs.write("model-proposal.json",o.to_json())')
    (candidate/'main.splash').write_text(source,encoding='utf8')
    probe=DesktopProbe(candidate,a.output,Path.home()/'.octosense/octos-home/.octos')
    try:run(probe)
    finally:probe.stop()
