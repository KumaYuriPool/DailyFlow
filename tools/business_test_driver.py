"""Real card-host development test driver; never imported by the production app.
All state, stamped manifests and logs stay in a freshly created output directory.
"""
from pathlib import Path
import json,subprocess,os,time,socket,urllib.request,shutil
from datetime import datetime,timezone,timedelta
ROOT = None
BIN = None
DAY = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
FUTURE_DAY = (datetime.now(timezone(timedelta(hours=8))).date() + timedelta(days=5)).isoformat()

def configure(bundle, output, binary):
    """Create a new isolated output and copy the bundle before stamping it."""
    global ROOT, BIN
    bundle, output, binary = bundle.resolve(), output.resolve(), binary.resolve()
    if not (bundle / 'manifest.json').is_file() or not binary.is_file():
        raise ValueError('Bundle manifest and card-host binary must exist.')
    if output == bundle or output.is_relative_to(bundle):
        raise ValueError('Output must be outside the source bundle.')
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(bundle, output / 'bundle')
    ROOT, BIN = output, binary
    return ROOT

def save(rid='req1',**kw):
 a=dict(request_id=rid,record_id='',expected_revision=0,kind='expense',title='猫粮',date=DAY,amount='45',time='',end_date='',source='',flow_names=['宠物照护'],user_tags=['猫'])
 a.update(kw);return dict(name='dailyflow.save_record',args=a)
def query(**kw):return dict(name='dailyflow.query',args=kw)
def run(name,calls,state=None):
 out=ROOT/name;out.mkdir(exist_ok=True)
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 cmd=[str(BIN),'--bundle',str(ROOT/'bundle'),'--app-data',str(state or out/'state'),'--allow-unsigned','--stamp']
 for c in calls:cmd+=['--tool-call',json.dumps(c,ensure_ascii=False)]
 log=out/'runtime.log'
 with log.open('w',encoding='utf8') as stream:
  p=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,MAKEPAD_HIDE_WINDOWS='1',MAKEPAD_REMOTE=str(port)),creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
  try:
   end=time.monotonic()+80;results={}
   while time.monotonic()<end:
    txt=log.read_text(encoding='utf8',errors='replace')
    if 'card-host: refused:' in txt:raise AssertionError(txt[-10000:])
    for line in txt.splitlines():
     if 'card-host: tool-result ' in line:
      r=json.loads(line.split('card-host: tool-result ',1)[1]);results[r['index']]=r
    if len(results)==len(calls):break
    if p.poll()!=None:raise AssertionError(txt[-10000:])
    time.sleep(.15)
   assert len(results)==len(calls),txt[-15000:]
   try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/snap',timeout=5) as response:snap=json.load(response)
    (out/'snapshot.json').write_text(json.dumps(snap,ensure_ascii=False),encoding='utf8')
   except OSError:pass
   (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
   return results
  finally:
   try:urllib.request.urlopen(f'http://127.0.0.1:{port}/quit',timeout=3).close()
   except (OSError,TimeoutError):pass
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
   (out/'cleanup.json').write_text(json.dumps(dict(pid=p.pid,port=port,stopped=p.poll()!=None)))
def latest(state):
 items=[json.loads(p.read_text(encoding='utf8')) for p in Path(state).glob('dailyflow/state-*.json') if p.is_file()]
 return max(items,key=lambda x:x['revision'])
