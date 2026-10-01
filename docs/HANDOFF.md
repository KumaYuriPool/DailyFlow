# DailyFlow 项目 handoff 文档

**日期**：2026-10-02
**版本**：v0.6（含 4-bundle 拆分 + iOS 极简日历 v0.5）
**目的**：让任何接手 agent 能在 30 分钟内理解项目状态并能继续开发

2026-10-02 更名补充：本地项目已统一为 DailyFlow，应用 ID 为 `dailyflow` / `dailyflow-*`，详见 [更名记录](RENAMING.md)。本轮五个 bundle 准入检查通过，但独立日历运行时仍复现既有 UI nil 错误；下方历史“0 错误”不代表当前结果。

---

## 0. 一句话总结

> 当前代码仍为四个独立 Splash bundle，日历为原型，其余三个为占位页。2026-10-02 的新产品讨论将 DailyFlow 延伸为以日历为入口的时间 Flow 系统，建议先在单 App 内验证统一协议；尚未实施合并。请先读 [产品愿景与路线图](PRODUCT_VISION_ROADMAP.md)。

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
