"""Real existing desktop + configured Provider + DailyFlow persistence/UI.

Only sends explicit synthetic test statements. Never reads Provider secrets.
Unlike injected model tests, success here requires a real host/model response.
"""
import argparse
import json
from pathlib import Path
import time
from desktop_flow_probe import DesktopProbe, ROOT


class UI:
    def __init__(self, probe): self.probe = probe

    def widgets(self):
        return [w for w in self.probe.snapshot()['s'] if w.get('ty') in ('Label', 'Button', 'TextInput')]

    def find(self, text=None, ident=None, ty=None):
        matches = [w for w in self.widgets() if (text is None or w.get('t') == text)
                   and (ident is None or w.get('i') == ident) and (ty is None or w.get('ty') == ty)]
        assert matches, f'Widget absent: {text or ident}'
        return matches[0]

    def click(self, text=None, ident=None, ty=None):
        w = self.find(text, ident, ty)
        x, y, width, height = w['r']
        self.probe.request('click', x=x+width/2, y=y+height/2, wait=1)
        time.sleep(.2)

    def fill(self, ident, value):
        self.click(ident=ident, ty='TextInput')
        self.probe.request('k', c='KeyA', ctrl=1, wait=1)
        self.probe.request('k', t=value, wait=1)
        time.sleep(.2)
        assert self.find(ident=ident,ty='TextInput')['t'] == value

    def state(self):
        candidates = []
        for f in (self.probe.apps/self.probe.app_id).rglob('state-*.json'):
            try: candidates.append(json.loads(f.read_text(encoding='utf-8-sig')))
            except (ValueError, OSError): pass
        return max(candidates, key=lambda s:s['revision']) if candidates else {'records': [], 'flows': []}

    def evidence(self, name):
        (self.probe.output/(name+'.json')).write_text(json.dumps({'widgets': self.widgets(), 'state': self.state()}, ensure_ascii=False, indent=2), encoding='utf-8')
        (self.probe.output/(name+'.png')).write_bytes(self.probe.request('g', raw=1))

    def send(self, text, followup=False):
        self.fill('chat_input', text)
        self.click('补充并继续' if followup else '发送并记录')
        deadline = time.monotonic()+60
        while time.monotonic() < deadline:
            if not any(w.get('ty') == 'Button' and w.get('t') == '正在处理…' for w in self.widgets()):
                return
            time.sleep(.5)
        raise TimeoutError('Model UI did not finish')


def run(probe):
    probe.wait_ready()
    ui = UI(probe)
    ui.click('对话')
    ui.send('今天买猫粮花了45元，归到宠物照护')
    ui.evidence('01-real-expense')
    data = ui.state()
    assert len(data['records']) == 1, 'Real model did not save exactly one record; inspect 01-real-expense.json'
    assert data['records'][0]['cents'] == 4500 and len(data['flows']) == 1
    assert data['flows'][0]['name'] == '宠物照护'
    assert data['records'][0]['flow_ids'] == [data['flows'][0]['id']]
    revision = data['revision']
    ui.click('发送并记录')
    assert ui.state()['revision'] == revision, 'Duplicate send changed data'
    ui.click('查看这件事的 Flow')
    ui.evidence('02-real-flow')
    assert any('45.00' in w.get('t','') for w in ui.widgets())
    ui.click('对话')
    ui.send('今天买猫砂花了点钱，也归到宠物照护')
    ui.evidence('03-real-clarification')
    assert len(ui.state()['records']) == 1, 'Ambiguous amount was saved'
    ui.find('补充并继续')
    ui.send('26元', followup=True)
    ui.evidence('04-real-followup')
    data = ui.state()
    assert len(data['records']) == 2 and len(data['flows']) == 1, 'Followup did not reuse Flow'
    assert sorted(r['cents'] for r in data['records']) == [2600,4500]
    assert all(r['flow_ids'] == [data['flows'][0]['id']] for r in data['records'])
    ui.click('查看这件事的 Flow')
    ui.evidence('05-real-flow-complete')
    assert any('71.00' in w.get('t','') for w in ui.widgets())
    result = {'real_provider': True, 'real_model_requests': 3,
              'checks': ['clear statement auto-saved', 'Flow auto-created', 'duplicate send no-op',
                         'ambiguous amount not saved', 'real clarification', 'followup auto-saved',
                         'Flow reused', 'graph shows actual total'], 'records':2, 'flows':1, 'cents':7100}
    (probe.output/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,default=ROOT/'bundle')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--core-dir',type=Path,required=True)
    parser.add_argument('--binary',type=Path)
    args=parser.parse_args()
    probe=DesktopProbe(args.bundle,args.output,args.core_dir,args.binary)
    try: run(probe)
    finally: probe.stop()
