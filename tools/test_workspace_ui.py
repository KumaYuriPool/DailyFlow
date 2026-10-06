"""Isolated card-host probe and compatibility entry for test_conversation_ui."""
import argparse,json,os,shutil,socket,subprocess,sys,time,urllib.parse,urllib.request
from pathlib import Path
from test_real_model_flow import UI

ROOT=Path(__file__).resolve().parents[1]

class Probe:
    def __init__(self,out,seed=None,size='412x892',binary=None):
        self.size=size
        self.binary=Path(binary or ROOT.parent/'OctoSense-App-Hub/target/release/card-host.exe').resolve()
        self.output=out.resolve();self.output.mkdir(parents=True,exist_ok=False);self.apps=self.output/'apps';self.app_id='dailyflow'
        self.bundle=self.output/'bundle';shutil.copytree(ROOT/'bundle',self.bundle)
        folder=self.apps/self.app_id;folder.mkdir(parents=True)
        if seed:
            for p in Path(seed).rglob('state-*.json'):shutil.copyfile(p,folder/p.name)
        with socket.socket() as s:s.bind(('127.0.0.1',0));self.port=s.getsockname()[1]
        self.log=(self.output/'runtime.log').open('a',encoding='utf8')
        self.child=subprocess.Popen([str(self.binary),'--bundle',str(self.bundle),'--app-data',str(self.apps),'--allow-unsigned','--stamp','--size',self.size],stdout=self.log,stderr=subprocess.STDOUT,env=dict(os.environ,MAKEPAD_HIDE_WINDOWS='1',MAKEPAD_REMOTE=str(self.port)),creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(120):
            try:
                if any(w.get('t')=='本地数据已就绪' for w in self.snapshot().get('s',[])):return
            except (OSError,ValueError):pass
            time.sleep(.2)
        self.stop();raise RuntimeError('UI not ready')
    def request(self,path,**args):
        with urllib.request.urlopen(f'http://127.0.0.1:{self.port}/{path}?'+urllib.parse.urlencode(args),timeout=12) as r:return r.read()
    def snapshot(self):return json.loads(self.request('snap'))
    def start(self):
        with socket.socket() as s:s.bind(('127.0.0.1',0));self.port=s.getsockname()[1]
        self.log=(self.output/'runtime.log').open('a',encoding='utf8')
        self.child=subprocess.Popen([str(self.binary),'--bundle',str(self.bundle),'--app-data',str(self.apps),'--allow-unsigned','--stamp','--size',self.size],stdout=self.log,stderr=subprocess.STDOUT,env=dict(os.environ,MAKEPAD_HIDE_WINDOWS='1',MAKEPAD_REMOTE=str(self.port)),creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(120):
            try:
                if any(w.get('t')=='本地数据已就绪' for w in self.snapshot().get('s',[])):return
            except (OSError,ValueError):pass
            time.sleep(.2)
        self.stop();raise RuntimeError('UI not ready after restart')
    def stop(self):
        try:self.request('quit')
        except OSError:pass
        try:self.child.wait(5)
        except subprocess.TimeoutExpired:self.child.kill();self.child.wait(5)
        self.log.close();(self.output/'cleanup.json').write_text(json.dumps(dict(pid=self.child.pid,stopped=True,port=self.port)),encoding='utf8')

def labels(ui):
    return [w.get('t') for w in ui.widgets()]
def click_text(ui,*candidates):
    for c in candidates:
        if c in labels(ui):
            ui.click(c);return c
    raise AssertionError('No click target: '+str(candidates))

def run(p):
    from test_conversation_ui import run as run_current
    return run_current(p)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--seed',type=Path,required=True);args=a.parse_args()
    p=Probe(args.output,args.seed)
    try:run(p)
    except BaseException:
        try:UI(p).evidence('failure')
        except Exception:pass
        raise
    finally:p.stop()
