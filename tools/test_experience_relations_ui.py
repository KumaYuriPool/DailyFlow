"""Native relation UI regression using recorded official Agent output.

Not a fresh Agent run. Scope transformations and direct projection fault
injections are recorded; original producer/sync evidence is not claimed here.
"""
import native_runtime
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_timeline_ui import TimelineProbe
from test_real_model_flow import UI

ROOT = Path(__file__).resolve().parents[1]
HOST = native_runtime.binary("card_host")


def key(ref):
    return '/'.join((ref['source_app'], ref.get('source_module', 'external'), ref['record_id']))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', required=True)
    ap.add_argument('--recorded-output', type=Path, default=ROOT / 'build/ux-official-r3/apps/dailyflow')
    ap.add_argument('--compact', action='store_true')
    args = ap.parse_args()
    out = Path(args.output).resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    source = args.recorded_output.resolve()
    source_files = {name: source / name for name in ('timeline-imported.json', 'experiences-v1.json')}
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in source_files.items()}
    projection = json.loads(source_files['timeline-imported.json'].read_text(encoding='utf-8'))
    store = json.loads(source_files['experiences-v1.json'].read_text(encoding='utf-8'))
    record_map = {key(r): r for r in projection['records']}
    transformed = copy.deepcopy(store)
    transformed.update(seq=2, items=[], decisions=[], disabled=[], relation_decisions=[])
    mapping = []
    for n, graph in enumerate(transformed['organizations'], 1):
        refs = [e for claim in graph['claims'] for e in claim['evidence']]
        topics = {record_map[key(ref)]['topic'] for ref in refs}
        assert len(topics) == 1
        topic = next(iter(topics))
        identity = 'recorded-experience-' + str(n)
        mapping.append({'from': graph['experience'], 'to': identity, 'topic': topic})
        graph['experience'] = identity
        transformed['items'].append(dict(id=identity, title='验收·攀岩' if topic == 'bouldering' else '验收·演出', topic=topic,
                                         start='', end='', sources=[], question='回顾这段经历'))
    graph = next(g for g in transformed['organizations'] if g['experience'] == next(m['to'] for m in mapping if m['topic'] == 'bouldering'))
    assert graph['claims'] and graph['edges']
    edge = graph['edges'][0]
    initial_ref = graph['claims'][0]['evidence'][0]
    fault_ref = edge['from']
    initial_record = record_map[key(initial_ref)]
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    width, height = (412, 892) if args.compact else (1280, 900)
    probe = TimelineProbe(out, ROOT / 'bundle', f'{width}x{height}', binary=HOST)
    report = dict(evidence_class='native GUI over recorded-real-output fixture; no fresh Agent, no source sync',
                  source_files={n: str(p) for n, p in source_files.items()}, source_sha256=hashes,
                  main_sha256=hashlib.sha256((probe.bundle / 'main.splash').read_bytes()).hexdigest(),
                  fixture_transformation={'temporary_to_saved': mapping, 'new_items': transformed['items'],
                                          'decisions_reset': True, 'claims_and_edges': 'unchanged'},
                  fault_injections=[], checks=[])
    ui = UI(probe)
    def ck(name, passed):
        report['checks'].append({'name': name, 'passed': bool(passed)})
        (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        assert passed, name
        print('PASS', name, flush=True)
    def texts():
        return [w.get('t', '') for w in ui.widgets()]
    def scroll(dy):
        probe.request('m', k='scroll', x=width - 90, y=450, dy=dy, wait=1)
    def top():
        scroll(-6000)
    def click_panel(text):
        for _ in range(20):
            matches = [w for w in ui.widgets() if w.get('ty') == 'Button' and w.get('t') == text
                       and 215 <= w['r'][1] + w['r'][3] / 2 <= height - 150
                       and w['r'][2] > 0]
            if matches:
                w = matches[0]
                x, y, ww, hh = w['r']
                probe.request('click', x=x + ww / 2, y=y + hh / 2, wait=1)
                time.sleep(.2)
                return
            scroll(240)
        raise AssertionError('No visible panel button: ' + text)
    def read_store():
        return json.loads((probe.apps / probe.app_id / 'experiences-v1.json').read_text(encoding='utf-8'))
    def money_text():
        return next(t for t in texts() if '已确认' in t and '/ 待核对' in t)
    def count_text():
        return next(t for t in texts() if '条记录 · 文件导入样本' in t)
    def write_projection(value, action):
        (probe.apps / probe.app_id / 'timeline-imported.json').write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        report['fault_injections'].append(action)
        ui.click('重新读取')
    try:
        probe.stop()
        data = probe.apps / probe.app_id
        (data / 'timeline-imported.json').write_text(json.dumps(projection, ensure_ascii=False), encoding='utf-8')
        (data / 'experiences-v1.json').write_text(json.dumps(transformed, ensure_ascii=False), encoding='utf-8')
        probe.start()
        ui = UI(probe)
        if not args.compact:
            ui.click('布局')
        ui.click('验收·攀岩')
        ui.click('经历概括')
        ck('saved-recorded-overview-loaded', graph['claims'][0]['text'] in texts())
        ui.evidence('01-overview')
        click_panel('查看依据 · ' + initial_ref['quote'])
        ck('citation-opens-own-original-record', initial_record['body'] in texts() and any(key(initial_ref) in t for t in texts()))
        ui.evidence('02-original-evidence')
        ui.click('‹ 返回时间流')
        ui.click('核对关联 · ' + str(len(graph['edges'])))
        top()
        original_money, original_count = money_text(), count_text()
        click_panel('确认相关')
        ck('exact-edge-confirmed-by-click', len(read_store()['relation_decisions']) == 1 and read_store()['relation_decisions'][0]['value'] == 'confirmed')
        ui.evidence('03-confirmed')
        click_panel('不相关')
        ck('edge-rejected-without-membership-change', read_store()['relation_decisions'][0]['value'] == 'rejected'
           and read_store()['decisions'] == [] and money_text() == original_money and count_text() == original_count)
        ui.evidence('04-rejected')
        click_panel('撤销上次关联决定')
        top()
        ck('undo-restores-exact-edge', read_store()['relation_decisions'][0]['value'] == 'confirmed'
           and '已确认相关' in texts() and money_text() == original_money and count_text() == original_count)
        ui.evidence('05-undo')
        # A genuine process restart reads the decision file just written by UI.
        probe.stop(); probe.start(); ui = UI(probe)
        if not args.compact:
            ui.click('布局')
        ui.click('验收·攀岩'); ui.click('核对关联 · ' + str(len(graph['edges'])))
        ck('confirmed-relation-survives-process-restart', '已确认相关' in texts() and read_store()['relation_decisions'][0]['value'] == 'confirmed')
        ui.evidence('06-restarted-confirmation')
        click_panel('起点 · ' + fault_ref['quote'])
        changed = copy.deepcopy(projection)
        changed_record = next(r for r in changed['records'] if key(r) == key(fault_ref))
        changed_record.update(revision=changed_record['revision'] + 100, title='投影更正后的攀岩记录', body='这是隔离投影更正验收原文。')
        write_projection(changed, {'type': 'direct-projection-correction', 'key': key(fault_ref), 'new_revision': changed_record['revision']})
        ck('correction-shows-new-original-hides-old-edge', changed_record['body'] in texts() and edge['title'] not in texts()
           and (args.compact or '依据已变化，需要重新整理' in texts()) and read_store()['relation_decisions'][0]['value'] == 'confirmed')
        ui.evidence('07-corrected-evidence')
        deleted = copy.deepcopy(changed)
        deleted['records'] = [r for r in deleted['records'] if key(r) != key(fault_ref)]
        write_projection(deleted, {'type': 'direct-projection-removal', 'key': key(fault_ref)})
        ck('deletion-hides-open-detail-and-derived-content', any('旧内容已隐藏' in t for t in texts())
           and changed_record['body'] not in texts() and edge['title'] not in texts())
        ui.evidence('08-deleted-evidence')
        ui.click('‹ 返回时间流')
        ck('changed-edge-invalid-in-relations-view', edge['title'] not in texts() and '依据已变化，需要重新整理' in texts())
        ui.click('设置'); ui.click('停止读取 · ' + fault_ref['source_app']); ui.click('回到经历')
        ui.click('核对关联 · ' + str(len(graph['edges'])))
        ck('disabled-source-invalidates-all-dependent-edges', '依据已变化，需要重新整理' in texts()
           and all(e['title'] not in texts() for e in graph['edges'] if fault_ref['source_app'] in (e['from']['source_app'], e['to']['source_app'])))
        ui.evidence('09-source-disabled')
        ui.click('经历概括')
        hidden_claims = [c for c in graph['claims'] if any(r['source_app'] == fault_ref['source_app'] for r in c['evidence'])]
        ck('disabled-source-hides-dependent-overview', all(c['text'] not in texts() for c in hidden_claims))
        ui.evidence('10-overview-after-disable')
        probe.stop(); probe.start(); ui = UI(probe)
        if not args.compact:
            ui.click('布局')
        ui.click('验收·攀岩'); ui.click('核对关联 · ' + str(len(graph['edges'])))
        ck('restart-keeps-disabled-source-and-invalid-edge', fault_ref['source_app'] in read_store()['disabled']
           and edge['title'] not in texts() and '依据已变化，需要重新整理' in texts())
        ui.evidence('11-restarted-invalid')
        ck('no-authoritative-business-writes', ui.state().get('records', []) == [] and read_store()['decisions'] == [])
        ck('recorded-real-output-files-unchanged', all(hashlib.sha256(p.read_bytes()).hexdigest() == hashes[n] for n, p in source_files.items()))
    except BaseException:
        ui.evidence('failure')
        raise
    finally:
        probe.stop()


if __name__ == '__main__':
    main()
