# 当前交接：0.6.4 产品定位与新路线规划

当前产品方向、价值、概念、成熟度判断和阶段建议见 [PRODUCT_ROADMAP](PRODUCT_ROADMAP.md)。旧愿景继续保留。内置说明新增定位与概念，Flow节解释通用时间协议、源事实和按需回顾，共9节；只改文案与规划，未接通新的对话查找或外部App。宽窄帮助UI验收、gate和保护核对见build/product-roadmap-r1及根agent.md。本次未改业务/原生/个人数据，未提交发布。

## 0.6.3 内置使用说明

左下「帮助」或全部搜索「使用说明」，离线七节指南，src/user_guide.json构建嵌入并生成USER_GUIDE.md；新增55_help，15个编译模块。宽窄屏真实点击、返回/草稿保留和unsigned gate通过，见 build/help-guide-r1。上游README及App Hub提交流程、当前商店材料差距和验证边界见 [APP_HUB_SUBMISSION](APP_HUB_SUBMISSION.md)。未改业务协议或个人数据，未改原生/Provider/启动器，未提交发布。

## 0.6.2 无命名 Flow 的源关联修复

允许独立expense_for/follow_up/fulfills，普通日历同日事项＋明确费用显示一项；对话移除日历快捷动作，详情保留定位。新增39_relation_repair，当前14模块，启动时严格凭据验证并备份后补回旧无Flow复合关联。个人状态本轮未直接改写，需正常重开加载。见 [SOURCE_RELATIONS_FIX](SOURCE_RELATIONS_FIX.md) 及根agent.md最新节。

## 0.6.1 按需查找与时间线（历史）

已移除常驻Flow栏，新增查找工作区和只读dailyflow.recall，按名字/关键词与明确关联生成临时时间线。当前13模块，详情见 [FLOW_RECALL](FLOW_RECALL.md)。不是任意自然语言检索，无新增Provider调用；原型中的聊天查找勿当成已实现能力。

## 0.6.0 通用时间协议与经期来源（历史）

2026-10-06 最新实现见 [TIME_EVENT_PROTOCOL](TIME_EVENT_PROTOCOL.md) 及项目AGENTS/根agent.md顶部。当前单包12模块，记账、日历、经期通过注册式时间协议协作；普通日历自动消费经期日期区间。协议29调用/模块39调用/原业务15调用/Agent43注入断言和一次真实Provider经期查询均有隔离证据。旧0.4–0.5交接保留历史。

用户已确认Flow后台组织、按需回顾是后续界面方向；本轮没有移除现有Flow栏。经期成为第三伪App是新明确授权，覆盖旧删减范围。独立App通信、多时区、预测、发布均未交付。

## 2026-10-04 历史交接：对话工作区设计与 0.4.0 实际版本

最新产品方向见 [对话工作区设计](CONVERSATION_WORKSPACE_DESIGN.md)：双左栏 App/Flow、中间对话、右侧可搜索应用工作区；日历独立于 App，普通/账本视图收进可搜索的视图下拉；日格日期居中、选中为圆形。本次只更新设计预览和文档，当前 0.4.0 应用尚未实现这套界面。不要把未来多 App 导航设计理解为现在拆 App 或恢复旧四 bundle。

## 2026-10-04 最近一次实现交付：0.4.0 事件 Flow

本轮按 P1–P4 完成单 App 事件 Flow 本地实现与 Windows 验收，未提交发布。先读 [新验收](EVENT_FLOW_ACCEPTANCE.md)、[新协议](EVENT_FLOW_PROTOCOL.md) 和项目 AGENTS。src 模块构建为单 Splash；旧 apps 已归档，历史数据保留。下文是先前阶段记录，冲突时以本节与新报告为准。

# DailyFlow 项目 handoff 文档

## 最新接手入口 · 2026-10-03 产品收敛

先读 [PET_CARE_FLOW_REPLAN](PET_CARE_FLOW_REPLAN.md)。用户本轮只要求规划与交接，明确选择暂时一个App、内部严格分开记账与日历；宠物护理是事件Flow，不是新App。新目标包含普通/账本日历切换、事件与费用关系可视化、Agent自动组织与更正、真正经模块协议同步。其余产品能力删除、不占位，但保留历史数据。

当前代码仍0.3.0；下方交付是事实基线，不是新目标已经完成。新Agent在收到执行指令后按新计划推进，旧多模块开发范围与旧四bundle入口不再执行。

**日期**：2026-10-02
**版本**：v0.6（含 4-bundle 拆分 + iOS 极简日历 v0.5）
**目的**：让任何接手 agent 能在 30 分钟内理解项目状态并能继续开发

## 2026-10-03 单 App 0.3.0 最新交付（优先于下方历史）

已完成共享业务入口、`dailyflow.query/save_record`应用工具、明确自动记录/含糊追问、自动建立或复用Flow，以及可点击的时间图。完整桌面实测3次真实Provider请求：猫粮45元→创建宠物照护；重复发送不新增；猫砂追问补充26元→复用Flow，最终2条记录合计71元。见 [0.3.0验收报告](AGENT_FLOW_ACCEPTANCE.md)。此前0.2.0的“模型不可用”仅对应独立card-host。

启动：`run-dailyflow-ai.cmd`使用完整桌面和既有Provider，数据`.local-state/desktop/`；旧`run-dailyflow.cmd`仍是无模型card-host，数据`.local-state/dailyflow/`。两套数据不自动迁移。当前旧Shell不含新脚本工具桥接且未配置测试kernel，**应用内真实model.complete成功不等于Shell Agent工具全链路成功**。

业务32次真实工具调用、对话12项注入集成断言+1次重启、真实Provider3次请求分层记录；最终证据位于`build/agent-flow-r1/`，不要混用早期失败探针。`tools/test_business_flow.py`提供新隔离目录复测。`ok`是Splash关键字，使用`result["ok"]`。

收据上限128，满额后仅阻止新自动写入，手工仍可继续；草稿/追问不跨重启；恢复旧备份回退收据，恢复后不能盲目重投之后的未知旧请求。依然单实例双槽，不承诺跨设备同步或断电零丢失。发布、其他平台、关闭后唤醒、AppCard/glance、连续7天试用未完成。本轮产品开发仅改Splash应用和相关测试/文档，未改Shell/Rust/Provider配置或真实用户数据。

## 2026-10-02 单 App 0.2.0 最新实现（优先于下方历史）

`bundle/main.splash` 已成为统一入口；运行 `run-dailyflow.cmd`。当前可手工管理真实月历、Flow、记账/经期/任务/新闻，使用预算提醒、任务运行时检查与重开补偿、双槽持久化及备份恢复。真实点击、控件树、文件与截图证据见 [MVP 验收报告](MVP_ACCEPTANCE_REPORT.md)；操作见 [USER_GUIDE](USER_GUIDE.md)，数据字段和一致性边界见 [DATA_PROTOCOL](DATA_PROTOCOL.md)。

真实 `model.complete` 已获权限但返回 `no service answers "model" on this device`；输入保留，手工卡片可用。AI 自动记录、歧义追问与模型更正闭环未完成。AppCard/glance、关闭后后台唤醒和 7 天真实试用不在已通过项内。没有修改 Rust 或发布、提交、推送。

备份在 `build/mvp-baseline-20261002/`，主要回归证据在 `build/mvp-final/`，故障注入在 `build/mvp-failure/`，旧账本导入验证在 `build/mvp-legacy/`。真实 `.local-state/dailyflow/expenses.json` 不变，导入需在设置显式点击。

新发现：动态循环构造 42 格月历可行，旧“约 80 个控件上限”不是当前依据；不要使用未验证的三元表达式。存储错误会抛出 VM 错误，必须用 `try/catch` 捕获；损坏 JSON 可能返回缺字段对象，结构验证也需要捕获。所有 UI 引用在初始化后执行；定时规则在成功加载后才允许写入。正常业务运行未复现旧独立日历的 `ui target nil`。

最新开发授权：用户已明确要求新 Agent 开发并跑通单 App 时间 Flow 验证版。接手应先读 [IMPLEMENTATION_HANDOFF](IMPLEMENTATION_HANDOFF.md)，以 `bundle/` 为统一实现入口；保留四个原型 App。旧“只规划”或“不逆转四 bundle”表述不再限制本次获授权开发。只允许 OctoScript/Splash 和现有宿主 API，不扩展 Rust。

2026-10-02 更名补充：本地项目已统一为 DailyFlow，应用 ID 为 `dailyflow` / `dailyflow-*`，详见 [更名记录](RENAMING.md)。本轮五个 bundle 准入检查通过，但独立日历运行时仍复现既有 UI nil 错误；下方历史“0 错误”不代表当前结果。

---

## 0. 一句话总结

> 当前使用 `bundle/` 单 App，四 bundle 保留作历史参考。请先读本页顶部最新实现与验收报告；下面 v0.6 等章节是历史，不代表当前功能与测试结果。

能力说明更新：较新的本地 OctoSense 源码已有应用工具授权转发和交互 glance 卡片，不能再笼统说“完全没有跨 App 通信”。DailyFlow 的工具接入、记录级跳转和后台提醒仍需分别验证；源码能力不等于已安装 Windows 程序已可用。下文与旧调研保留历史信息，有冲突时参考新产品文档及工作区 `agent.md` 的最新补充。

---

## 1. 必读文档（按顺序，30 分钟内完成）

| # | 文档 | 时间 | 内容 |
|---|------|------|------|
| 0 | `PRODUCT_VISION_ROADMAP.md` | 15 分钟 | 新产品方向、协议、卡片与提醒、路线图及未来展望 |
| 1 | `HANDOFF.md`（本文） | 5 分钟 | 总入口、状态、命令速查 |
| 2 | `PRODUCT_PLAN.md` | 5 分钟 | 产品方向、用户场景 |
| 3 | `TECH_STACK.md` | 5 分钟 | Splash vs Rust+Makepad 对比 |
| 4 | `SPLASH_LIMITS.md` | 5 分钟 | 8 个常见坑 + 调试流程 |
| 5 | `OCTOSENSE_SHELL_RESEARCH.md` | 5 分钟 | Shell 能力 + 限制 |
| 6 | `ITERATION_LOG.md` | 5 分钟 | v0.1 → v0.5 真实迭代历史 |
| 7 | `ARCHITECTURE_4BUNDLE.md` | 3 分钟 | 4 bundle 设计原因 |
| 8 | `UI_PROTOTYPE.md` | 5 分钟 | UI 设计原型 |
| 9 | `ACCEPTANCE_PROMPT.md` | 5 分钟 | 验收测试清单 |

---

## 2. 项目目录结构

```
D:\Life\AgenticApp\
├── my-notes\                       # 笔记 Demo（独立）
│   └── bundle\
├── DailyFlow\                      # 统一项目目录，包含原 Git 历史
│   ├── apps\
│   │   ├── dailyflow-calendar\bundle\  # 静态日历原型
│   │   ├── dailyflow-expense\bundle\   # 占位 splash
│   │   ├── dailyflow-diary\bundle\     # 占位 splash
│   │   └── dailyflow-period\bundle\    # 占位 splash
│   ├── docs\                        # 设计文档
│   │   ├── HANDOFF.md                # ← 你在这里
│   │   ├── PRODUCT_PLAN.md
│   │   ├── TECH_STACK.md
│   │   ├── SPLASH_LIMITS.md
│   │   ├── OCTOSENSE_SHELL_RESEARCH.md
│   │   ├── ITERATION_LOG.md
│   │   ├── ARCHITECTURE_4BUNDLE.md
│   │   ├── UI_PROTOTYPE.md
│   │   └── ACCEPTANCE_PROMPT.md
│   ├── bundle\                      # 旧 bundle（保留作参考）
│   └── build\                      # 截图及 main.splash.v0.3-broken.bak 历史备份
├── OctoScript-App-Design-Flow\      # OctoSense 工具 + 文档
│   ├── tools\octo
│   └── docs\
├── OctoSense-App-Hub\              # App Hub Rust 源码（不修改）
├── OctoSense\                       # Shell Rust 源码（不修改）
└── makepad\                         # Makepad Rust 源码（不修改）
```

---

## 3. 立即可用的命令

### 3.1 环境准备

```powershell
$env:PYTHONUTF8 = '1'
$env:OCTO_HUB = 'D:\Life\AgenticApp\OctoSense-App-Hub\target\release\hub.exe'
$env:OCTO_CARD_HOST = 'D:\Life\AgenticApp\OctoSense-App-Hub\target\release\card-host.exe'
cd D:\Life\AgenticApp\OctoScript-App-Design-Flow
```

### 3.2 检查 bundle

```powershell
python -X utf8 tools/octo check 'D:\Life\AgenticApp\DailyFlow\apps\dailyflow-calendar\bundle'
# 期望：dailyflow-calendar 0.1.0 — PASSED
```

### 3.3 启动 + 截图 + 退出

```powershell
python -X utf8 tools/octo run 'D:\Life\AgenticApp\DailyFlow\apps\dailyflow-calendar\bundle' --port 8143 --hidden --detach
sleep 3
python -X utf8 tools/octo shot 8143 'D:\Life\AgenticApp\DailyFlow\apps\dailyflow-calendar\build\test.png'
curl -s -m 2 127.0.0.1:8143/quit
```

### 3.4 模拟点击 + 输入

```powershell
curl -s -X POST 127.0.0.1:8143/click -H "Content-Type: application/json" -d '{"x": 100, "y": 200}'
curl -s "127.0.0.1:8143/k?t=hello"
```

### 3.5 查看 widget tree

```powershell
curl -s 127.0.0.1:8143/snap | python -c "
import json,sys
d=json.loads(sys.stdin.read())
for w in d['s']:
    if w['ty'] in ('SolidView','Label','GestureView','Button','TextInput'):
        print(f'{w[\"ty\"]:12} i={w.get(\"i\",\"-\"):8}  r={w[\"r\"]}  t={repr(w.get(\"t\",\"\"))[:30]}')
"
```

---

## 4. 当前 v0.5 dailyflow-calendar 验证清单

| # | 验证项 | 命令 | 期望 |
|---|--------|------|------|
| 1 | octo check | 见 3.2 | dailyflow-calendar 0.1.0 — PASSED |
| 2 | 启动 | 见 3.3 | 0 个 [E] 错误 |
| 3 | 默认显示 | 截图 | 31 天完整显示 + 15 日选中（浅蓝）+ "选中 2026-10-15" |
| 4 | 点击 18 | `POST /click {x:206, y:265}` | 状态栏更新到"选中 2026-10-18" |
| 5 | 月份标题 | 截图 | "2026 年 10 月"（中间可能空白，但文本应可见） |

---

## 5. 已验证与未验证清单

### 5.1 已验证 ✅

- [x] Splash 脚本能编译通过 gate
- [x] 启动 0 个 [E] 错误
- [x] 日历完整月历显示（1-31）
- [x] 点击日期切换 selected_day
- [x] 状态栏动态更新（用 ui.<id>.set_text）
- [x] 4 个 bundle 全部 octo check PASSED
- [x] 4 个 bundle 全部可独立启动
- [x] 9 项验收测试（v0.2 历史版本已通过）

### 5.2 未验证 ⏸

- [ ] 月份切换实际工作（按钮 on_click 触发，但日历格子 hardcoded "1".."31"，不会变）
- [ ] 跨 bundle 数据共享（OctoSense Shell 当前不支持）
- [ ] OctoSense Shell 内 dailyflow-calendar 与 dailyflow-expense 联动
- [ ] 移动端布局（首版仅承诺 Windows）
- [ ] AI 对话解析（OctoSense model.complete 尚未实测）

### 5.3 已知 bug（v0.5）

| Bug | 原因 | 临时方案 |
|-----|------|----------|
| 月份标题中间空白 | on_render 在该上下文失效 | 静态文字显示月份 |
| 选中态对比度弱 | blue_light 与白色背景对比不够 | v0.7 优化边框 |
| 第二行 25/27 数字换行 | 窄列宽 + SolidView 默认 Down flow | v0.7 用 on_render |

---

## 6. 下一步建议（按优先级）

### 6.1 短期（1-2 小时）

**选项 A**：继续完善 dailyflow-calendar（v0.7）
- 解决月份标题中间空白
- 优化选中态视觉
- 测试月份切换（虽然 hardcoded）

**选项 B**：把 4 bundle 合并为 1 bundle + 1 splash 多 view
- 解决数据共享问题
- 解决 App 联动问题（共享 fs）
- 工作量：~2 小时

### 6.2 中期（1-2 天）

实现 dailyflow-expense 的完整功能（手动 CRUD + 列表 + 持久化）。

### 6.3 长期

- 等 OctoSense Shell 加 `octos.run` host service → App-to-App 启动
- 等 OctoSense Shell 加共享存储 capability → App-to-App 数据共享

---

## 7. 用户决策日志

| 日期 | 决策 | 来源 |
|------|------|------|
| 2026-10-02 | 全面更名为 DailyFlow，目录与应用 ID 同步迁移 | 用户 |
| 2026-10-01 | 首批功能 = 记账 + 日记 + 经期 | 用户 |
| 2026-10-01 | "明确内容自动记，含糊再问" | 用户 |
| 2026-10-01 | UI 风格 = iOS 极简 | 用户 |
| 2026-10-02 | 拆分 4 bundle（无入口） | 用户 |
| 2026-10-02 | 接受 OctoSense Shell 当前限制（无跨 App 启动） | 调研结论 |

---

## 8. 常用文件路径速查

| 用途 | 路径 |
|------|------|
| DailyFlow 项目根 | `D:/Life/AgenticApp/DailyFlow/` |
| 4 bundle | `D:/Life/AgenticApp/DailyFlow/apps/{dailyflow-calendar,dailyflow-expense,dailyflow-diary,dailyflow-period}/bundle/` |
| 当前最完整 splash | `D:/Life/AgenticApp/DailyFlow/apps/dailyflow-calendar/bundle/main.splash` |
| 文档目录 | `D:/Life/AgenticApp/DailyFlow/docs/` |
| 截图证据 | `D:/Life/AgenticApp/DailyFlow/build/iter-*.png` |
| Splash 工具 CLI | `D:/Life/AgenticApp/OctoScript-App-Design-Flow/tools/octo` |
| Splash 官方 API 文档 | `D:/Life/AgenticApp/OctoScript-App-Design-Flow/docs/SCRIPT-API.md` |
| my-notes 参考模板 | `D:/Life/AgenticApp/my-notes/bundle/main.splash` |
| OctoSense Shell 源码 | `D:/Life/AgenticApp/OctoSense/crates/shell/` |
| Makepad 内置 Calendar | `D:/Life/AgenticApp/makepad/apps/calendar/` |

---

## 9. 接手 Agent 第一步行动清单

```markdown
- [ ] 读 `HANDOFF.md`（本文档）
- [ ] 读 `TECH_STACK.md` 理解技术栈
- [ ] 读 `SPLASH_LIMITS.md` 避免常见坑
- [ ] 读 `OCTOSENSE_SHELL_RESEARCH.md` 理解限制
- [ ] 跑 `python -X utf8 tools/octo check DailyFlow\apps\dailyflow-calendar\bundle` 验证环境
- [ ] 跑 `tools/octo run DailyFlow\apps\dailyflow-calendar\bundle --port 8143 --hidden --detach` 启动
- [ ] 截图 + 看 widget tree + 实际点击验证
- [ ] 在 `DailyFlow\apps\dailyflow-calendar\bundle\main.splash` 继续开发
```

---

## 10. 给 Agent 的话

- 我们已经踩过所有常见坑（见 SPLASH_LIMITS.md）
- 4 bundle 拆分是当前最佳实践
- 数据隔离是已知限制，不强求
- 用户重视实际效果，不要过度承诺
- 每个改动都要验证（截图 + widget tree + 真实点击）
