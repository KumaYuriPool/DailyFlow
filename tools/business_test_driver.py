"""Real card-host development test driver; never imported by the production app.
All state, stamped manifests and logs stay in a freshly created output directory.
"""
from pathlib import Path
import json,subprocess,os,time,socket,urllib.request,shutil,hashlib
from datetime import datetime,timezone,timedelta
ROOT = None
BIN = None
DAY = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
FUTURE_DAY = (datetime.now(timezone(timedelta(hours=8))).date() + timedelta(days=5)).isoformat()

def configure(bundle, output, binary, *, legacy_vm_fixture=False):
    """Copy into fresh output; explicitly labelled legacy fixtures may omit only
    script-tools-v1 in that copy. Default preserves every manifest requirement.
    This fixture mode never proves admission of the production package.
    """
    global ROOT, BIN
    bundle, output, binary = bundle.resolve(), output.resolve(), binary.resolve()
    if not (bundle / 'manifest.json').is_file() or not binary.is_file():
        raise ValueError('Bundle manifest and card-host binary must exist.')
    if output == bundle or output.is_relative_to(bundle):
        raise ValueError('Output must be outside the source bundle.')
    manifest_path = bundle / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    requires = manifest.get('requires', [])
    if legacy_vm_fixture and (not isinstance(requires, list) or any(r != 'script-tools-v1' for r in requires)):
        raise ValueError('Legacy VM fixture may remove only script-tools-v1; unknown requirements are refused.')
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(bundle, output / 'bundle')
    if legacy_vm_fixture:
        production = Path(__file__).resolve().parents[1] / 'bundle'
        digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        original_requires = list(requires)
        manifest.pop('requires', None)
        copied_manifest = output / 'bundle/manifest.json'
        copied_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        metadata = dict(legacy_vm_fixture=True,
                        evidence_kind='isolated legacy VM business/injection fixture; not exact production admission',
                        official_admission_evidence=False, production_bundle=str(production),
                        production_manifest_sha256=digest(production/'manifest.json'),
                        production_main_sha256=digest(production/'main.splash'),
                        input_bundle=str(bundle), input_manifest_sha256=digest(manifest_path),
                        source_main_sha256=digest(bundle/'main.splash'),
                        original_requires=original_requires, fixture_requires=[],
                        removed_requires=[r for r in original_requires if r == 'script-tools-v1'],
                        fixture_manifest_sha256_before_stamp=digest(copied_manifest),
                        note='Only the fresh copy is changed. The driver stamps that fixture, not the production bundle.')
        (output/'fixture-manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2),encoding='utf8')
    ROOT, BIN = output, binary
    return ROOT

def fixture_metadata():
    path = ROOT / 'fixture-manifest.json'
    return json.loads(path.read_text(encoding='utf8')) if path.is_file() else None

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
