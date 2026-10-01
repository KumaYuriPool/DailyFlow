# DailyFlow v0.2 原型验收 Prompt

> 你是一个独立验收 agent。请按下列清单验证 `D:\Life\AgenticApp\DailyFlow\bundle\` 中的 OctoSense 应用是否真实可用。
> 不要信任任何已有截图或文档——必须自己重新启动 + 真实点击 + 真实截图。

## 你的工作环境

- Windows + Git Bash + PowerShell
- OctoSense App Hub 已构建：`D:\Life\AgenticApp\OctoSense-App-Hub\target\release\{hub,card-host}.exe`
- Python 3.13.16：`C:\Users\44231\AppData\Local\Programs\Python\Python313\python.exe`
- 工具 CLI：`D:\Life\AgenticApp\OctoScript-App-Design-Flow\tools\octo`
- 远程桥通过 HTTP 8143（每次启动换一个端口避免冲突）

## 必读文件（按顺序读，不超过 30 分钟）

1. `D:\Life\AgenticApp\agent.md` — 整个工作区的最新状态、DailyFlow 历史、已知限制
2. `D:\Life\AgenticApp\DailyFlow\docs\PRODUCT_PLAN.md` — v0.2 产品方向
3. `D:\Life\AgenticApp\DailyFlow\docs\UI_PROTOTYPE.md` — 详细 UI 原型
4. `D:\Life\AgenticApp\DailyFlow\bundle\main.splash` — 当前 splash 源码（约 23KB）

## 启动命令（PowerShell）

```powershell
$env:PYTHONUTF8 = '1'
$env:OCTO_HUB = 'D:\Life\AgenticApp\OctoSense-App-Hub\target\release\hub.exe'
$env:OCTO_CARD_HOST = 'D:\Life\AgenticApp\OctoSense-App-Hub\target\release\card-host.exe'
cd D:\Life\AgenticApp\OctoScript-App-Design-Flow

# 第 0 步：准入检查
python -X utf8 tools/octo check 'D:\Life\AgenticApp\DailyFlow\bundle'

# 第 1 步：启动（detached，hidden window）
python -X utf8 tools/octo run 'D:\Life\AgenticApp\DailyFlow\bundle' --port 8143 --hidden --detach
sleep 3

# 第 2 步：截图
python -X utf8 tools/octo shot 8143 'D:\Life\AgenticApp\DailyFlow\build\verify-01-startup.png'

# 第 3 步：测试结束必须退出
curl -s -m 2 127.0.0.1:8143/quit
```

## 验收清单（9 项必须全部跑过）

| # | 测试 | 通过标准 | 关键截图 |
|---|------|----------|----------|
| 1 | octo check | 输出 `dailyflow 0.1.0 — PASSED` | — |
| 2 | 启动无 [E] 错误 | `card-host.log` 中 grep `\[E\]` 结果为 0 行 | — |
| 3 | 默认界面 | 显示日历完整月历 1-31（一二三四五六日 + 5 行日期） | `verify-01-startup.png` |
| 4 | 点击日历格子 | 用 `/click?x=&y=` 点击 18 日格后，状态栏显示"选中 2026-10-18" | `verify-02-click18.png` |
| 5 | 月份导航 < | 点击 < 按钮，状态栏从"月 10"变为"月 9" | `verify-03-prev.png` |
| 6 | 切到记账 tab | 点击"记账"按钮，看到记账界面 | `verify-04-expense.png` |
| 7 | 列表显示 | 预填 3 条 ¥32/¥15/¥50 记录全部显示 | `verify-04-expense.png` |
| 8 | 点击删除 | 点击 row1 后状态栏总计 ¥97→¥82，文件实际变为 2 条 | `verify-05-after-delete.png` |
| 9 | 切回日历 | 关闭应用后 `expenses.json` 真的被修改为 2 条 | 文件验证 |

## 测试数据准备

启动前，先写入测试数据：

```bash
mkdir -p "D:/Life/AgenticApp/DailyFlow/.local-state/dailyflow"
cat > "D:/Life/AgenticApp/DailyFlow/.local-state/dailyflow/expenses.json" << 'EOF'
[{"id":1,"amount":32,"note":"午饭","date":"2026-10-15","ts":1},
 {"id":2,"amount":15,"note":"咖啡","date":"2026-10-18","ts":2},
 {"id":3,"amount":50,"note":"晚饭","date":"2026-10-22","ts":3}]
EOF
```

## 关键远程桥路由（用 curl 测试）

| 路由 | 用途 |
|------|------|
| `GET /snap` | 返回 widget tree JSON（id/ty/r/t）—— **必须先看这个再点击** |
| `GET /g?w=&scale=1` 或 `tools/octo shot 8143 <path>` | 截图 |
| `GET /click?x=&y=` 或 `POST /click -d '{"x":N,"y":N}'` | 模拟点击 |
| `GET /k?t=TEXT` | 输入文字（**不是 `/type`**） |
| `GET /quit` | 关闭应用（**测试结束必须调用**） |

获取 widget 坐标脚本：
```bash
curl -s 127.0.0.1:8143/snap | python -c "
import json,sys
d=json.loads(sys.stdin.read())
for w in d['s']:
  if w['ty'] in ('Button','GestureView','TextInput','Label'):
    print(f'{w[\"ty\"]:10} r={w[\"r\"]} t={repr(w.get(\"t\",\"\"))[:30]}')
"
```

## 验证标准

- ✅ PASS：截图 + widget tree + 文件状态三重证据都正确
- ❌ FAIL：实际行为与预期不符，**立即停止后续测试**并报告
- ⚠️ PARTIAL：部分功能工作，记录差异

## 输出报告

完成后写一份 `D:\Life\AgenticApp\DailyFlow\docs\ACCEPTANCE_REPORT.md`：

```markdown
# DailyFlow v0.2 验收报告

日期：YYYY-MM-DD
验收人：[你的名字/agent ID]

## 总结
- 通过：X / 9
- 失败：X
- 部分：X

## 详细结果

### 1. octo check
[结果]

### 2. 启动无错误
[结果 + log 行数]

### 3. 默认界面
[截图路径 + 截图说明]

... (每项类似)

## 发现的问题
1. [问题描述]
2. ...

## 建议
1. [修复建议]
2. ...
```

## 重要原则

1. **每个测试项都重新截图保存**，不要复用之前的截图
2. **不要修改任何源码**，只记录观察结果
3. **每个会话结束必须 `/quit`**，避免端口占用
4. **遇到 [E] 错误立刻报告**，不要继续
5. **状态栏文字是真实数据指针**，观察它就能验证功能是否真工作
6. **`[E]` 错误数 = 0 不代表功能完成**——必须真实点击验证
7. **如果 widget tree 中 Label.text 是空字符串或默认值，说明该 widget 未被刷新**，是 bug

## 已知限制（预期会出现，不是 bug）

1. 月份标题中间空白（on_render 失效）
2. 选中态视觉对比度弱
3. 日历格子下没显示当日金额
4. on_render 在嵌套 SolidView 内不可靠

## 联系方式

发现任何新问题或改进建议，请：
1. 截图保存到 `D:\Life\AgenticApp\DailyFlow\build\verify-*.png`
2. 写进 `ACCEPTANCE_REPORT.md`
3. 在 `agent.md` DailyFlow 章节追加"验收发现"小节
4. 不要自动 commit，先告知用户决策

---

**开始工作吧。祝你验收顺利！**
