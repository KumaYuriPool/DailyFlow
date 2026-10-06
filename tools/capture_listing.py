"""Capture actual UI with fresh synthetic records, never personal app data."""
import json
from pathlib import Path
import business_test_driver as driver
from test_workspace_ui import Probe
from test_real_model_flow import UI

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/submission-review-0.6.4'
BINARY = ROOT.parent/'build/native-update-20261006/OctoSense/target/release/card-host.exe'


def main():
    # Before new captures exist, the baseline listing still names valid images.
    driver.configure(OUT/'baseline/bundle', OUT/'fixture2', BINARY)
    state = OUT/'fixture2/state'
    result = driver.run('seed', [
        {'name':'dailyflow.apply','args':dict(request_id='listing-care',kind='expense',title='团子洗护费',date=driver.DAY,amount='120',subject='团子',event_title='团子洗护',plan_title='再次护理',plan_date=driver.FUTURE_DAY,plan_time='15:00',evidence='合成演示：明确记录本次洗护和下次安排')},
        {'name':'dailyflow.apply','args':dict(request_id='listing-lunch',kind='expense',title='午餐',date=driver.DAY,amount='35')}
    ], state)
    assert all(r['ok'] and r['data']['ok'] for r in result.values()),result
    # Probe stamps its own copy; temporarily point missing new image at a real prior PNG.
    placeholder = ROOT/'bundle/screenshots/03-recall.png'
    if not placeholder.exists():
        placeholder.write_bytes((OUT/'baseline/bundle/screenshots/03-event-flow.png').read_bytes())
    p=Probe(OUT/'screenshots',state,size='1280x900',binary=BINARY)
    try:
        ui=UI(p);ui.click(ident='layout_toggle')
        before=ui.state()
        ui.click('日历');ui.evidence('01-calendar')
        ui.click('账本');ui.find('全部支出 ¥155.00');ui.evidence('02-ledger')
        ui.click('查找');ui.fill('recall_input','团子洗护');ui.click('搜索')
        ui.find('找到 3 条 · 按时间排列');ui.evidence('03-recall')
        ui.click('帮助');ui.click('DailyFlow 想帮你做什么',ty='Button');ui.evidence('04-help')
        assert ui.state()==before
        (OUT/'screenshots/report.json').write_text(json.dumps(dict(passed=True,synthetic_data=True,real_provider=False,business_unchanged=True),indent=2),encoding='utf8')
    finally:p.stop()
    for name in ['01-calendar','02-ledger','03-recall']:
        (ROOT/'bundle/screenshots'/f'{name}.png').write_bytes((OUT/'screenshots'/f'{name}.png').read_bytes())


if __name__=='__main__':main()
