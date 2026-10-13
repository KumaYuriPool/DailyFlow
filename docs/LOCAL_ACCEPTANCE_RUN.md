# 本地验收步骤（评审前必读，2 分钟跑完）

目标：在**本机**复现真实系统 Assistant → 跨 App 读取独立账本 → 自动整理并定位经历的完整链路。无需重装 Shell、无需 App Hub、无需联网。所有证据落在 `D:/Life/AgenticApp/DailyFlow/build/overnight-20261013/integration-r1/`。

## 一、准备（约 30 秒）

打开 PowerShell 或 Git Bash，先关掉大内存程序（Unity / Chrome 等），剩下至少 **2 GB 空闲内存**。然后：

```bash
cd D:/Life/AgenticApp/DailyFlow/build/overnight-20261013/integration-r1
```

确认今天搭建的本地运行时四组件（已就位，无需重建）：
- `runtime-final-r1.json` 中锁定的 Shell `0476df1f3aadf33f28104e69f99240f1693bac7b751f0b25b19b878da3ac6de0`、kernel `4e72bc7d…`、card-host `0e92683e…`、hub `6eaeb666…`
- 候选包：`candidate-r2/DailyFlow/bundle/main.splash` SHA256 `46a7c6d38d3e1da0f03b31032d153df83774eb17653cff74655670adda09f7d3`

## 二、起服务（同一窗口，分步执行）

### 第 1 步：拉起候选的可见窗口

```bash
python -X utf8 run_candidate.py --app dailyflow
```

会弹出 DailyFlow 窗口；同时拉起独立账本进程（同进程内 Card 模式）。**保持窗口打开**。可用 PowerShell 工具查看进程是否真的跑起来（`tasklist | findstr octosense`），但一般肉眼可见即可。

### 第 2 步：手动在独立账本里加一条今天的新记录

切换到 DailyFlow Ledger 窗口：
1. 点"+ 记一笔"
2. 标题填：`2026-10-13 攀岩馆课时费`
3. 金额填：`150`
4. 日期默认今天即可
5. 保存

这条记录是"演示钩子"——让后面系统助手整理时能拉到一条旧经历里没有的新数据，效果最好。

### 第 3 步：切回 DailyFlow 窗口

**在系统 Assistant 弹层里**操作（顶部"Ask DailyFlow"或顶部"对话"入口均可，看你的窗口语言）：

先发一句 `/new`（或点击 **New conversation** 按钮），清空历史会话，确保是新会话。

然后**逐字**发送下面这条提示词（直接复制粘贴）：

```
帮我整理一下我的攀岩经历：读取独立账本里的所有攀岩相关记录，保存成一段新经历，并自动打开、定位到该经历。如果工具或授权不可用，请明确说明，不能虚构成功。
```

按 **Send**。

### 第 4 步：看结果（约 1 分钟内完成）

不要切走、不要关窗口。完整流程会按下面顺序发生：

1. 系统助手调用 `agents.list` 找到 DailyFlow（peer 列表已 ready）—— 助手面板显示 `agents_list · done`
2. 系统助手通过 `peer_send_input` 把请求委派给 DailyFlow —— `peer_send_input · done`
3. DailyFlow 弹出"整理过程"面板（左侧），显示：委派到达 → 读取独立账本（projection 拉到 2-3 条记录）→ 模型整理（生成带原文引用的概括+候选关联）→ 提交校验
4. **经历自动打开**并定位到新经历，时间流里显示刚才加的 150 元记录和之前的旧记录

如果停在某一步超过 90 秒没动，截图发我，我看是哪段超时（多半是模型慢）。

## 三、检查证据（可选，1 分钟）

直接看 `D:/Life/AgenticApp/DailyFlow/build/overnight-20261013/integration-r1/candidate-r2/DailyFlow/build/` 下最新一次 `live-cold-final-rX` 目录：

- `screen-*.png`：每 15 秒一张窗口截图，最后一张应当显示"已打开本地经历"+ 时间流 + 整理过程面板
- `durable-result.json`：模型最终落盘的请求结构（request_id、sources、topic、organization）
- `e2e-checks.json`：本轮所有 19 项端到端检查的布尔结果，应全部 `passed: true`
- `native-tool-audit.json`：宿主实际审计的 7 条工具调用记录（含两次 `dailyflow.experience_context` + 两次 `dailyflow.experience_result` + 一次 `experience_request_status`）

## 四、完整复现的真实证据清单（不靠窗口观察也能确认）

| 场景 | 目录 | 关键结果 |
| --- | --- | --- |
| 跨 App 真实拉取（2 次） | `candidate-r2/DailyFlow/build/bridge-final-r1/` 和 `bridge-final-r2/` | `native-sync.json` 显示 2-3 条记录 |
| 真实更正（220→200，同 ID） | `bridge-final-r2/` 和 `bridge-final-r3/` | `exp-1` rev2, 20000 分 |
| 真实删除不复活 | `bridge-final-r4/` | 仅 `exp-1` 和 `exp-3` |
| 真实撤权（卸载来源 App） | `bridge-final-r5/` | `records: []`, `authorization: revoked` |
| 系统 Assistant 冷启动 | `live-cold-final-r2/` | e2e-checks 19/19 通过 |
| 系统 Assistant 热窗口 | `live-warm-final-r2/` | e2e-checks 19/19 通过 |
| 视觉截图 12 张 | `ui-wide-final-r4/`、`ledger-ui-narrow-final-r1/`、`workbench-final-r1/` | 物理捕获有效 |
| 旧工作台真实点击 | `workbench-final-r1/` | summary.json 8/8 |

## 五、常见问题

**Q：窗口黑屏、卡住、显存占满？**
A：内存不够。先关掉其他程序再试；或用 `run_candidate.py --app dailyflow-ledger` 单独验独立账本 App。

**Q：模型说"我无法读取您的独立账本"？**
A：先回到第 2 步确认你确实在独立账本 App 里加了一条新记录；同时 `tasklist | findstr octosense` 确认两个 App 都在跑。

**Q：日志里有 `script time budget exceeded`？**
A：低内存 + I/O 竞争时偶发，应用层有重试（P1 修复 `nf_external_recover`），最终仍会完成；如果真没完成，截图发我。

**Q：想重新跑一次端到端？**
A：关掉所有窗口，重新从第 1 步开始。共享账本数据保留，不需要重新"加新记录"（但建议每次都加一条不同金额的，让演示有差异）。

## 六、确认验收通过的标准

✅ 窗口里看到经历自动打开并定位，整理过程面板有完整事件流
✅ `live-cold-final-rX/e2e-checks.json` 中 `passed: true`（all checks）
✅ `native-tool-audit.json` 至少 6 条 `outcome: "ok"`
✅ 截图最后一张显示"已打开本地经历"或类似确认文本

**全过即视为本地验收通过，可以按你准备好的 PR 流程去上游提了**。
