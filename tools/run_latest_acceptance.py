"""Run the full local acceptance matrix against ONE explicit hashed runtime.

Provider/official phases run separately after offline/native gates, because
they need an existing human-authorized host home. No consent is created here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runtime-manifest', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--phase', choices=['native', 'official', 'model', 'relations'], default='native')
    ap.add_argument('--core-dir')
    ap.add_argument('--consent-home')
    ap.add_argument('--recorded-output')
    ap.add_argument('--offline-report', help='Already completed fresh offline report; avoids duplicate execution')
    args = ap.parse_args()
    manifest = Path(args.runtime_manifest).resolve()
    os.environ['DAILYFLOW_RUNTIME_MANIFEST'] = str(manifest)
    import native_runtime
    out = Path(args.output).resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists(), 'Use a fresh DailyFlow/build output'
    out.mkdir(parents=True)
    native_runtime.record_runtime(out)
    baseline = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [ROOT/'bundle/main.splash', ROOT/'bundle/manifest.json']}
    (out/'bundle-before.json').write_text(json.dumps(baseline, indent=2))
    if args.phase == 'native':
        legacy_args = []
        if args.offline_report:
            prior = Path(args.offline_report).resolve()
            assert prior.is_relative_to(ROOT/'build')
            rows=json.loads(prior.read_text())
            assert len(rows)==8 and all(x['passed'] for x in rows)
            prior_baseline=json.loads((prior.parent/'baseline.json').read_text())
            assert all(prior_baseline.get(p)==v for p,v in baseline.items()), 'Offline evidence has different app bytes'
            (out/'offline-evidence.json').write_text(json.dumps({'report':str(prior),'sha256':hashlib.sha256(prior.read_bytes()).hexdigest()},indent=2))
            legacy_args=['--ui-only']
        tests = [('legacy', 'run_ux_regression.py', legacy_args),
                 ('experience-contracts', 'test_experience_contracts.py', []),
                 ('peer-contracts', 'test_experience_peer_contracts.py', []),
                 ('reasoning', 'test_experience_reasoning.py', []),
                 ('experience-wide', 'test_experience_ui.py', ['--wide']),
                 ('experience-compact', 'test_experience_ui.py', []),
                 ('expenses', 'test_experience_expenses.py', [])]
    elif args.phase in ('official', 'model'):
        assert args.core_dir, '--core-dir is required'
        extra = ['--core-dir', args.core_dir]
        if args.phase == 'official':
            assert args.consent_home, 'An existing human-approved --consent-home is required'
            extra += ['--consent-home', args.consent_home]
        tests = [(args.phase, 'test_experience_'+args.phase+'.py', extra)]
    else:
        assert args.recorded_output, 'Use output from this runtime\'s actual official run'
        extra = ['--recorded-output', str(Path(args.recorded_output).resolve())]
        tests = [('relations-wide', 'test_experience_relations_ui.py', extra),
                 ('relations-compact', 'test_experience_relations_ui.py', extra+['--compact'])]
    reports=[]
    for name, script, extra in tests:
        command=[sys.executable,'-X','utf8',str(ROOT/'tools'/script),'--output',str(out/name),*extra]
        start=time.monotonic()
        with (out/(name+'.log')).open('wb') as log:
            # Disable proxies ONLY for the UI client's loopback urllib requests.
            bootstrap=('import runpy,sys,urllib.request; '
                       'urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({}))); '
                       f'sys.path.insert(0,{str(ROOT/"tools")!r}); sys.argv={command[3:]!r}; '
                       f'runpy.run_path({str(ROOT/"tools"/script)!r},run_name="__main__")')
            result=subprocess.run([sys.executable,'-X','utf8','-c',bootstrap],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        reports.append({'suite':name,'exit_code':result.returncode,'passed':result.returncode==0,
                        'seconds':round(time.monotonic()-start,1),'log':name+'.log'})
        (out/'report.json').write_text(json.dumps(reports,indent=2))
        print(name, 'PASS' if result.returncode==0 else 'FAIL', flush=True)
    after={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in baseline}
    unchanged=baseline==after
    (out/'bundle-preservation.json').write_text(json.dumps({'unchanged':unchanged,'before':baseline,'after':after},indent=2))
    return 0 if unchanged and all(x['passed'] for x in reports) else 1


if __name__=='__main__':
    sys.exit(main())
