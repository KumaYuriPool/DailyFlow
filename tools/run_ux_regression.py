"""Fresh, retained evidence for the UX migration; never reuse old test outputs."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    ap.add_argument('--ui-only', action='store_true')
    ap.add_argument('--offline-only', action='store_true')
    args = ap.parse_args()
    if args.ui_only and args.offline_only:
        ap.error('--ui-only and --offline-only are mutually exclusive')
    out = Path(args.output).resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists(), 'Use a fresh build directory'
    out.mkdir(parents=True)
    tests = [] if args.ui_only else [
        ('contract', 'test_v1_contract.py', ['--fixtures', str(ROOT/'experiments/source-bridge/fixtures/probes')]),
        ('adversarial', 'test_importer_adversarial.py', []),
        ('audit', 'test_importer_audit_r1.py', []),
        ('expectations', 'test_scenario_expectations.py', []),
        ('decisions', 'test_decision_persistence.py', []),
        ('e2e', 'test_route_b_end_to_end.py', []),
        ('freshness', 'test_route_b_freshness.py', []),
        ('resilience', 'test_route_b_resilience.py', []),
    ]
    tests += [] if args.offline_only else [('ui-compact','test_timeline_ui.py', []), ('ui-wide','test_timeline_ui.py',['--wide']),
              ('business','test_business_flow_newhost.py', []), ('resync','test_timeline_resync_ui.py',[]),
              ('second-stages','test_timeline_second_stages.py',[])]
    baseline = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in list((ROOT/'src').glob('*.splash')) + [ROOT/'bundle/main.splash', ROOT/'bundle/manifest.json']}
    (out/'baseline.json').write_text(json.dumps(baseline, indent=2))
    reports = []
    for name, script, extra in tests:
        path = ROOT/'tools'/script
        source = path.read_text(encoding='utf-8')
        # Preserve old tools and their evidence; redirect their historical fixed
        # scratch paths only in this executable copy. __file__ stays authoritative.
        source = source.replace('OUT = ROOT / "build/importer-adversarial-r1"', f'OUT = Path({str(out/name)!r})')
        source = source.replace('OUT = ROOT / "build/importer-audit-r1-regression"', f'OUT = Path({str(out/name)!r})')
        source = source.replace('out = ROOT / f"build/second-stages-{tag}"', f'out = Path({str(out/name)!r}) / tag')
        copy = out/(name+'-executed.py')
        copy.write_text(source, encoding='utf-8')
        argv = [str(path), *extra]
        if name not in ('adversarial','audit'):
            argv += ['--output', str(out/name)]
        code = ('import sys,urllib.request; from pathlib import Path; '
                'urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({}))); '
                f'sys.path.insert(0,{str(ROOT/"tools")!r}); sys.argv={argv!r}; '
                f'exec(compile(Path({str(copy)!r}).read_text(encoding="utf-8"),{str(path)!r},"exec"),'
                f'{{"__name__":"__main__","__file__":{str(path)!r}}})')
        try:
            r = subprocess.run([sys.executable, '-X','utf8','-c',code], cwd=ROOT, capture_output=True, timeout=240)
            log = r.stdout.decode('utf-8',errors='replace')+r.stderr.decode('utf-8',errors='replace')
            rc = r.returncode
        except subprocess.TimeoutExpired as e:
            log, rc = str(e), -1
        (out/(name+'.log')).write_text(log, encoding='utf-8')
        reports.append({'suite':name,'exit_code':rc,'passed':rc==0,'log':name+'.log'})
        (out/'report.json').write_text(json.dumps(reports,indent=2))
        print(name, 'PASS' if rc==0 else 'FAIL', flush=True)
    return 0 if all(r['passed'] for r in reports) else 1

if __name__ == '__main__':
    sys.exit(main())
