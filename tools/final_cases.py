from acceptance_cases import *
def start_timer_case():
    due=datetime.now(TZ).replace(second=0,microsecond=0)+timedelta(minutes=1)
    if (due-datetime.now(TZ)).total_seconds()<15: due+=timedelta(minutes=1)
    add('任务','运行中定时提醒测试',date=due.strftime('%Y-%m-%d'),at=due.strftime('%H:%M'))
    r=next(r for r in state()['records'] if r['title']=='运行中定时提醒测试')
    assert r['reminded_due']==0
    (OUT/'timer-due.json').write_text(json.dumps({'id':r['id'],'due_at':r['due_at']}))
    click('提醒'); evidence('27-before-timer')
    print('TIMER SCHEDULED',due.isoformat())
def verify_timer_case():
    item=json.loads((OUT/'timer-due.json').read_text())
    assert time.time()>item['due_at']+20
    r=next(r for r in state()['records'] if r['id']==item['id'])
    assert r['reminded_due']==r['due_at']
    assert len([a for a in state()['alerts'] if a['record_id']==item['id']])==1
    # Do not click the manual check button: this verifies the interval callback.
    assert any('运行中定时提醒测试' in w.get('t','') for w in widgets())
    evidence('28-foreground-timer')
    click('打开'); click('完成')
    # Period source CRUD and privacy, news correction/delete.
    click('记录'); click(record_row('经期','经期开始')); fill('record_title','实际周期记录'); click('保存记录')
    click('设置'); click('敏感记录：显示（点击切换）'); click('记录')
    assert not any('实际周期记录' in w.get('t','') for w in widgets())
    click('设置'); click('敏感记录：隐藏（点击切换）'); click('记录'); click(record_row('经期','实际周期记录'))
    click('删除源记录'); click('删除源记录'); assert count('period')==0
    click(record_row('新闻','测试进展二')); fill('record_title','测试进展二（更正）'); click('保存记录')
    click('Flow'); click('新闻观察（测试材料）'); assert any('测试进展二（更正）' in w.get('t','') for w in widgets())
    click(record_row('新闻','测试进展二（更正）')); click('删除源记录'); click('删除源记录'); assert count('news')==1
    evidence('29-module-delete-sync')
    click('设置'); click('导出备份')
    exported=json.loads((OUT/'dailyflow/events-export.json').read_text())
    assert len(exported)==len(state()['records'])
    for e in exported:
        r=next(r for r in state()['records'] if r['id']==e['source_record_id'])
        assert e['source_revision']==r['revision'] and e['entry']['record_id']==r['id']
        assert e['precision']==('minute' if r['kind']=='task' else 'day')
    evidence('30-final-export')
    (OUT/'final-cases-result.txt').write_text('PASS: actual interval due, period privacy and CRUD, news correction/delete, protocol projection consistency\n')
    print('FINAL CASES PASS')
if __name__=='__main__':
    if len(sys.argv)>1: verify_timer_case()
    else: start_timer_case()
