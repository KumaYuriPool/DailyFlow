import bridge_test as b
import hashlib
b.PORT=8172
b.OUT=b.ROOT/'build'/'mvp-legacy'
path=b.OUT/'dailyflow/expenses.json'
before=hashlib.sha256(path.read_bytes()).hexdigest()
b.click('设置'); b.click('导入旧 expenses.json（去重）')
assert len(b.state()['records'])==3,b.status()
assert sum(r['cents'] for r in b.state()['records'])==9700
b.click('导入旧 expenses.json（去重）'); assert len(b.state()['records'])==3
assert hashlib.sha256(path.read_bytes()).hexdigest()==before
b.evidence('25-legacy-idempotent')
# Create, rename, hide and remove membership through real controls.
b.click('Flow'); b.fill('flow_input','旧账本回看'); b.click('创建 Flow')
b.fill('flow_input','历史账目'); b.click('重命名'); assert b.state()['flows'][0]['name']=='历史账目'
b.click('显示 / 隐藏'); assert b.state()['flows'][0]['hidden']
b.click('记录'); row=next(w['t'] for w in b.widgets() if w['ty']=='Button' and '午饭' in w.get('t','')); b.click(row)
b.click('+ 历史账目'); assert len(b.state()['records'][0]['flow_ids'])==1
b.click('✓ 历史账目'); assert len(b.state()['records'][0]['flow_ids'])==0
b.fill('record_amount','33.10'); b.click('保存记录')
# Legacy future records can be viewed, but correcting requires actual occurrence dates.
if '未来计划' in b.status():
    from datetime import datetime,timezone,timedelta
    b.fill('record_date',datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')); b.click('保存记录')
assert b.state()['records'][0]['cents']==3310
b.click('删除源记录'); b.click('删除源记录'); assert len(b.state()['records'])==2
b.evidence('26-source-expense-deleted')
assert hashlib.sha256(path.read_bytes()).hexdigest()==before
try: b.req('quit')
except OSError: pass
print('LEGACY PASS: original unchanged, import dedup, flow rename/hide/membership, source edit/delete')
