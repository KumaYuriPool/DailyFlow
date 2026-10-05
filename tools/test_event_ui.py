"""Real 412x892 card-host click/screenshot/restart QA using synthetic Provider state."""
import argparse,json,os,shutil,socket,subprocess,time,urllib.parse,urllib.request
from pathlib import Path
from test_real_model_flow import UI
ROOT=Path(__file__).resolve().parents[1]
class CardProbe:
    def __init__(self,out,seed=None):
        self.output=out.resolve();self.output.mkdir(parents=True,exist_ok=False);self.apps=self.output/'apps';self.app_id='dailyflow'
        self.bundle=self.output/'bundle';shutil.copytree(ROOT/'bundle',self.bundle)
        folder=self.apps/self.app_id;folder.mkdir(parents=True)
        if seed:
            for p in Path(seed).rglob('state-*.json'):shutil.copyfile(p,folder/p.name)
        self.start()
    def start(self):
        with socket.socket() as s:s.bind(('127.0.0.1',0));self.port=s.getsockname()[1]
        self.log=(self.output/'runtime.log').open('a',encoding='utf8')
        self.child=subprocess.Popen([str(ROOT.parent/'OctoSense-App-Hub/target/release/card-host.exe'),'--bundle',str(self.bundle),'--app-data',str(self.apps),'--allow-unsigned','--stamp'],stdout=self.log,stderr=subprocess.STDOUT,env=dict(os.environ,MAKEPAD_HIDE_WINDOWS='1',MAKEPAD_REMOTE=str(self.port)),creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(80):
            try:
                if any(w.get('i')=='date_jump' for w in self.snapshot()['s']):return
            except (OSError,ValueError):pass
            time.sleep(.2)
        self.stop();raise RuntimeError('UI not ready')
    def request(self,path,**args):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.port}/{path}?'+urllib.parse.urlencode(args),timeout=12) as r:return r.read()
    def snapshot(self):return json.loads(self.request('snap'))
    def stop(self):
        try:self.request('quit')
        except OSError:pass
        try:self.child.wait(5)
        except subprocess.TimeoutExpired:self.child.kill();self.child.wait(5)
        self.log.close();(self.output/'cleanup.json').write_text(json.dumps(dict(pid=self.child.pid,stopped=True,port=self.port)),encoding='utf8')
class ScrollUI(UI):
    def scroll(self,dy):self.probe.request('m',k='scroll',x=210,y=410,dy=dy,wait=1);time.sleep(.3)
    def seek(self,text):
        for _ in range(12):
            found=[w for w in self.widgets() if w.get('t')==text and w.get('ty')=='Button' and 65<w['r'][1]<800]
            if found:return found[0]
            self.scroll(320)
        raise AssertionError('Cannot reach '+text)
    def click_seek(self,text):self.seek(text);self.click(text)
    def evidence(self,name):
        super().evidence(name)
        for w in self.widgets():
            x,y,width,height=w['r']
            if w.get('ty') in ('Button','TextInput') and 0<y<885:
                assert x>=-1 and x+width<=413,(name,'horizontal overflow',w)

def run(p):
    ui=ScrollUI(p);ui.evidence('01-ordinary')
    ui.click('账本日历');ui.evidence('02-ledger-calendar')
    assert any('275.00' in w.get('t','') for w in ui.widgets())
    ui.click('普通日历');ui.click_seek('已发生 · 洗护');ui.evidence('03-graph')
    assert any(w.get('t')=='记账 · 洗护费 ¥110.00' for w in ui.widgets()),'Graph order/attachments incorrect'
    ui.click('记账 · 洗护费 ¥110.00');ui.evidence('04-read-detail')
    assert not any(w.get('i')=='record_amount' for w in ui.widgets())
    ui.click('修改');ui.fill('record_amount','111');ui.fill('record_date','2026-10-03');ui.click('保存记录')
    assert len(ui.state()['records'])==3 and sum(r['cents'] for r in ui.state()['records'])==27600
    ui.click('‹ 返回');ui.evidence('05-graph-corrected')
    ui.scroll(220);plan=ui.seek('3 · 护理');original_y=plan['r'][1];ui.click('3 · 护理');ui.click('‹ 返回');assert abs(ui.find('3 · 护理')['r'][1]-original_y)<3;ui.evidence('05b-scroll-return');ui.scroll(-2000)
    ui.click_seek('记账 · 洗护费 ¥111.00');ui.click('定位到日历')
    ui.click('账本日历');ui.evidence('06-moved-date')
    assert ui.find(ident='date_jump')['t']=='2026-10-03'
    assert any(w.get('t') in ('¥111.00','¥111') for w in ui.widgets())
    ui.click('普通日历');assert ui.find(ident='date_jump')['t']=='2026-10-03'
    ui.click('全部');ui.evidence('07-scope-preserved')
    ui.click('账本日历');ui.find('此事件');assert ui.find(ident='date_jump')['t']=='2026-10-03'
    ui.click('›');assert ui.find(ident='date_jump')['t']=='2026-11-03';ui.click('普通日历');ui.find('此事件');assert ui.find(ident='date_jump')['t']=='2026-11-03';ui.click('‹');assert ui.find(ident='date_jump')['t']=='2026-10-03'
    # Reload actual persisted sources/projections, then navigate through ledger source.
    p.stop();p.start();ui=ScrollUI(p);ui.evidence('08-restarted')
    assert sum(r['cents'] for r in ui.state()['records'])==27600
    ui.click('账本');ui.click_seek('2026-10-03  洗护费  ¥111.00');ui.click('删除源记录');ui.click('删除源记录')
    assert len(ui.state()['records'])==2 and len(ui.state()['calendar_events'])==3
    ui.click('日历');ui.click_seek('已发生 · 洗护');ui.click_seek('删除事件关系（保留源记录）');ui.click('删除事件关系（保留源记录）')
    assert len(ui.state()['records'])==2 and len(ui.state()['calendar_events'])==3 and not ui.state()['relations']
    ui.evidence('09-unlinked-sources')
    forbidden=['经期','新闻','预算','任务','提醒','日记','即将推出']
    assert not any(word in w.get('t','') for word in forbidden for w in ui.widgets())
    (p.output/'report.json').write_text(json.dumps(dict(passed=True,window='412x892',checks=['ordinary/ledger','semantic graph source click','read/edit separation','same-ID manual correction','date movement','mode/month/day/scope preserved','restart projection rebuild','expense deletion preserves facts','Flow deletion preserves sources','no horizontal button overflow','removed product entrances','graph scroll position restored']),ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--seed',type=Path,required=True);args=a.parse_args();p=CardProbe(args.output,args.seed)
    try:run(p)
    except BaseException:
        UI(p).evidence("failure")
        raise
    finally:p.stop()
