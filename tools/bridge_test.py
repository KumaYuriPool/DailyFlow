"""Development-only bridge driver. Never used by the production application."""
import json, time, urllib.request, urllib.parse, pathlib, sys, os
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'build' / os.environ.get('DAILYFLOW_TEST_DATA','mvp-acceptance')
PORT = 8171
def req(path, **args):
    url = f'http://127.0.0.1:{PORT}/{path}?'+urllib.parse.urlencode(args)
    with urllib.request.urlopen(url, timeout=12) as r: return r.read()
def snap(): return json.loads(req('snap'))['s']
def widgets(): return [w for w in snap() if w['ty'] in ('Label','TextInput','Button')]
def find(text=None, ident=None, ty=None):
    matches = [w for w in widgets() if (text is None or w.get('t') == text) and (ident is None or w['i'] == ident) and (ty is None or w['ty'] == ty)]
    assert matches, f'widget missing: {text or ident}; '+str([(w['i'],w.get('t')) for w in widgets()])
    return matches[0]
def click(text=None, ident=None, ty=None):
    w=find(text,ident,ty); x,y,ww,hh=w['r']
    assert y+hh/2<889, f'widget offscreen: {w}'
    req('click',x=x+ww/2,y=y+hh/2,wait=1); time.sleep(.12)
def fill(ident,text):
    click(ident=ident,ty='TextInput'); req('k',c='KeyA',ctrl=1,wait=1); req('k',t=text,wait=1); time.sleep(.08)
    assert find(ident=ident)['t']==text, (ident,find(ident=ident)['t'],text)
def status(): return find(ident='status')['t']
def state():
    states=[]
    for p in (OUT/'dailyflow').glob('state-*.json'):
        try: states.append(json.loads(p.read_text(encoding='utf-8-sig')))
        except Exception: pass
    return max(states,key=lambda d:d['revision'])
def evidence(name):
    (OUT/(name+'.json')).write_text(json.dumps({'widgets':widgets(),'state':state()},ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/(name+'.png')).write_bytes(req('g',raw=1))
def run_smoke():
    click('Flow'); fill('flow_input','宠物照护'); click('创建 Flow')
    assert state()['flows'][0]['name']=='宠物照护',status()
    fill('flow_input','生活账本'); click('创建 Flow')
    click('记录'); click('+ 记账'); fill('record_title','猫粮'); fill('record_amount','32.50'); click('保存记录')
    assert state()['records'][0]['cents']==3250,status()
    click('+ 宠物照护'); click('+ 生活账本')
    assert len(state()['records'][0]['flow_ids'])==2,status()
    fill('record_amount','45.25'); click('保存记录')
    assert state()['records'][0]['cents']==4525,status()
    evidence('02-expense')
    click('Flow'); click('宠物照护'); assert any('45.25' in w.get('t','') for w in widgets())
    click('生活账本'); assert any('45.25' in w.get('t','') for w in widgets())
    evidence('03-flow')
    click('日历'); assert any('支出 ¥45.25' in w.get('t','') for w in widgets())
    evidence('04-calendar-linked')
    print('SMOKE PASS',status())
if __name__=='__main__': run_smoke()


