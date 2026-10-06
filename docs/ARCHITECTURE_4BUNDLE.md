# DailyFlow 4-Bundle 拆分设计方案

> 历史方案，非当前实现。2026-10-06 当前为一个 `dailyflow` bundle，内部记账、日历和 Flow 是伪 App 模块。当前主体身份与按需查询协议见 [MODULE_QUERY_PROTOCOL.md](MODULE_QUERY_PROTOCOL.md)。下文保留作历史参考，不能据此宣称已接入独立 App 间调用。

**日期**：2026-10-02（更新）
**作者**：DailyFlow 工作区
**版本**：v0.6（已通过 OctoSense Shell 实际验证）

---

## 0. 关键架构调研结论（先读这一节）

**问题**：OctoSense 是否真支持 4 个独立 bundle？

**答案**：✅ 是的——但**有重要限制**。

### 0.1 已验证：用户已安装 OctoSense 桌面 Shell

- 进程：`octosense.exe` (PID 38964) 在 Windows 任务列表中
- 数据目录：`C:\Users\44231\.octosense\`
- 已装系统 App：os.ai-providers / os.mail / os.maps / os.news / os.photos / os.youtube

### 0.2 OctoSense 组件多 App 支持

| OctoSense 组件 | 多 App 支持 | 证据 |
|----------------|-------------|------|
| **App Hub / appstore**（catalog） | ✅ | `octosense-app-hub/crates/appstore/src/lib.rs` `InstalledApp` 列表、`open(app_id)` |
| **OctoSense Shell**（desktop/phone） | ✅ | `Screen::Running(app_id)` 切换；用户可手动启动多个 App |
| **card-host**（独立 host） | ❌ | `card-host --bundle <dir>` 一次只跑一个 bundle |

### 0.3 **关键限制：App-to-App 启动无 host service**

虽然 Shell 支持多 App，**当前 Shell 注册的 host services 只有**：

| Service | 用途 | 来源 |
|---------|------|------|
| `mail` | 邮件账户 | `register_host_services()` |
| `glance` | 卡片显示 | `glance.rs` |
| `news` | 新闻 | `register_news()` |
| `llm` / `model` | AI | `ai-host/src/lib.rs` |

**没有** `shell.run` / `octos.run` / `navigate` / `launch_app` 这种跨 App 启动的服务。

**HOST-SERVICES.md 明确说**：

> `octos`: None in OctoSense. The four `octos.*` capabilities pass the gate, but no OctoSense shell registers a service for them: a call answers `no service answers "octos" on this device"`.

### 0.4 对本工作区的含义

- ✅ 4 个 bundle **可以装到 Shell**——catalog 显示为 4 个独立 App，用户从桌面启动其中一个
- ❌ 4 个 App **互相不能调用**——dailyflow-calendar 不能 `host.request("shell.run", {id: "dailyflow-expense"})`
- ❌ 数据**仍然 sandbox 隔离**——每个 App 自己 fs

### 0.5 结论

| 方案 | 可行性 |
|------|--------|
| 4 个独立 bundle + Shell 安装列表 | ✅ 可行 |
| 4 个独立 bundle + 数据互通 | ❌ 当前不可行 |
| 单 bundle 多 view + Splash `set_visible` 切换 | ✅ 可行（之前 v0.3 试过） |

### 0.6 架构决定

**保留 4 个 bundle 拆分**——它的价值：
1. 每个 App 独立迭代（拆分后我之前 v0.3 那种 widget 爆炸问题被物理隔离）
2. 用户可以选装（不想要经期就不装 dailyflow-period）
3. 未来 OctoSense 加上 `shell.run` host service 时，零成本升级到跨 App 通信

**不逆转**——保留 4 bundle 拆分。

---

## 1. 背景与动机

### 1.1 原方案的问题

DailyFlow v0.1 / v0.2 / v0.3 都是**单 splash** 的设计，把"日历 / 记账 / 日记 / 经期"四个模块塞在一个 `main.splash` 里：

```text
D:\Life\AgenticApp\DailyFlow\bundle\
├── main.splash  ← 单文件，包含全部模块
├── manifest.json
├── assets/icon.svg
├── screenshots/01-main.png
└── listing.json
```

### 1.2 暴露的问题

1. **Splash 脚本体积膨胀**：`main.splash` 从最初的 2KB 增长到 32KB
2. **widget 数量爆炸**：日历 42 个 GestureView + 84 个 SolidView/Label + 5 个记账行 + 设置面板 → 130+ widget
3. **Splash 解析器静默丢弃**：body 内 widget 超过某个阈值后整个 root view 不渲染，**无 `[E]` 错误**
4. **维护性差**：每次新增模块要重新设计整个 splash，导致 v0.3 多次重写
5. **不符合 OctoSense 设计**：OctoSense 原生支持**多 bundle 架构**，每个 bundle 独立 sandbox、独立 manifest、独立发布

### 1.3 用户决策

经用户确认（2026-10-02），最终方案：

> **拆分为 4 个独立 bundle，无入口 App**
> - `dailyflow-calendar` / `dailyflow-expense` / `dailyflow-diary` / `dailyflow-period`

---

## 2. 目标架构

### 2.1 目录结构

```text
D:\Life\AgenticApp\
├── my-notes\bundle\                          # 笔记 Demo（保持不变）
│
└── DailyFlow\apps\                                # 4 个独立 App
    ├── dailyflow-calendar\bundle\
    │   ├── main.splash           # 日历 UI
    │   ├── manifest.json         # id=dailyflow-calendar, capabilities=[storage]
    │   ├── listing.json           # 商店描述
    │   ├── assets/icon.svg        # 日历图标
    │   └── screenshots/01-main.png
    │
    ├── dailyflow-expense\bundle\
    │   ├── main.splash           # 记账 UI
    │   ├── manifest.json         # id=dailyflow-expense, capabilities=[storage]
    │   └── ...（同上）
    │
    ├── dailyflow-diary\bundle\
    │   ├── main.splash           # 日记 UI
    │   ├── manifest.json         # id=dailyflow-diary, capabilities=[storage]
    │   └── ...（同上）
    │
    └── dailyflow-period\bundle\
        ├── main.splash           # 经期 UI
        ├── manifest.json         # id=dailyflow-period, capabilities=[storage]
        └── ...（同上）
```

### 2.2 数据隔离

| App | 沙盒路径 | 文件 |
|-----|----------|------|
| dailyflow-calendar | `~/.local-state/dailyflow-calendar/` | （暂未持久化） |
| dailyflow-expense | `~/.local-state/dailyflow-expense/` | `expenses.json` |
| dailyflow-diary | `~/.local-state/dailyflow-diary/` | `entries.json` |
| dailyflow-period | `~/.local-state/dailyflow-period/` | `cycles.json` |

**关键限制**：每个 App 是**独立 sandbox**，不能直接读取其他 App 的数据。

---

## 3. 各 Bundle 功能范围

### 3.1 dailyflow-calendar（日历 App）

**功能**：
- 显示当前月日历（5×7 网格）
- 点击日期选中
- 月份导航 ‹ ›
- 显示选中日期的合计信息（从本地读取 expenses/entries/cycles）
- iOS 极简风格：白底 + 蓝色选中态 + 周日红色

**v0.5 已实现**（D:\Life\AgenticApp\DailyFlow\bundle\main.splash 验证通过）：
- 5 行 31 天固定布局
- 选中态蓝色背景
- 月份标题用 `on_render` 动态更新
- 0 个 `[E]` 错误

**未实现**：
- 真实数据加载（需要跨 bundle 通信）
- 选中日期数据汇总

### 3.2 dailyflow-expense（记账 App）

**功能**：
- 添加一笔：金额 + 备注 + 日期
- 列表显示所有记录
- 点击列表删除记录
- 显示当日合计 / 总计
- 持久化到 `expenses.json`

**状态**：未拆分。`DailyFlow/bundle/main.splash` 历史版本已实现此功能，需要迁移到独立 bundle。

### 3.3 dailyflow-diary（日记 App）

**功能**：
- 添加日记条目：日期 + 文字
- 列表显示所有条目
- 持久化到 `entries.json`

**状态**：未实现。规划中。

### 3.4 dailyflow-period（经期 App）

**功能**：
- 记录经期开始 / 结束日期
- 显示最近 N 次周期
- 不预测（不排卵、不安全期）

**状态**：未实现。规划中。

---

## 4. 跨 App 数据流（关键约束）

### 4.1 OctoSense 限制

OctoSense **没有跨 bundle 通信机制**：
- 没有共享数据库
- 没有 RPC 调用其他 App
- 每个 App 是独立的 sandbox

### 4.2 应对方案：数据冗余存储

**原则**：每个 App 独立存储自己的数据。日历 App 想要"今日合计"，必须从**自己的本地缓存**读取。

**具体方案**：
1. dailyflow-expense 写入 `expenses.json`
2. dailyflow-calendar 在启动时**只读本地缓存**（如 `dailyflow_calendar_cache.json`）
3. 缓存由 dailyflow-expense 写入，由 dailyflow-calendar 读取

**问题**：这个缓存写入需要 dailyflow-expense "知道" dailyflow-calendar 的位置——做不到（sandbox 隔离）。

### 4.3 实际可行的妥协

由于 OctoSense 没有跨 App 通信，**最现实的方案**：

1. **每个 App 独立运行**——日历 App 不显示其他 App 的数据
2. **数据冗余**——用户手动在每个 App 中录入
3. **未来扩展**：如果 OctoSense 引入"共享存储"capability，可整合

**接受这个限制**——这是 OctoSense 框架的根本约束。

---

## 5. UI 一致性规范

所有 4 个 App 共享：

| 元素 | 规范 |
|------|------|
| 主色 | `#x007aff` (iOS 蓝) |
| 选中态背景 | `#xe5f1ff` |
| 主文字 | `#x1c1c1e` |
| 副文字 | `#x8e8e93` |
| 背景 | `#xf5f5f7` |
| 卡片背景 | `#xffffff` |
| 错误 / 周日红 | `#xff3b30` |
| 圆角 | `border_radius: 8.0` 或 `10.0` |
| 按钮样式 | `ButtonFlat{text:... draw_bg +:{border_radius: X color:...} draw_text +:{color:...}}` |

字体：使用 `theme.font_bold{font_size: N}` 处理粗体，标准大小 14/17/22/28（Apple HIG）。

---

## 6. 拆分步骤

### 步骤 1：建目录骨架

```powershell
mkdir D:\Life\AgenticApp\DailyFlow\apps\dailyflow-calendar\bundle
mkdir D:\Life\AgenticApp\DailyFlow\apps\dailyflow-calendar\bundle\assets
mkdir D:\Life\AgenticApp\DailyFlow\apps\dailyflow-calendar\bundle\screenshots

# 同理 dailyflow-expense / dailyflow-diary / dailyflow-period
```

### 步骤 2：dailyflow-calendar manifest/listing/icon

`manifest.json`:
```json
{
  "capabilities": ["storage"],
  "id": "dailyflow-calendar",
  "integrity": {
    "bundle_blake3": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "name": "DailyFlow 日历",
  "schema": 1,
  "version": "0.1.0"
}
```

`listing.json`: 模板（参考 my-notes）
`icon.svg`: 日历图标（参考 D:\Life\AgenticApp\DailyFlow\bundle\assets\icon.svg）

### 步骤 3：复制 v0.4 main.splash 到 dailyflow-calendar/bundle

### 步骤 4：octo check 验证

```powershell
$env:PYTHONUTF8 = '1'
$env:OCTO_HUB = 'D:\Life\AgenticApp\OctoSense-App-Hub\target\release\hub.exe'
$env:OCTO_CARD_HOST = 'D:\Life\AgenticApp\OctoSense-App-Hub\target\release\card-host.exe'
cd D:\Life\AgenticApp\OctoScript-App-Design-Flow

python -X utf8 tools/octo check 'D:\Life\AgenticApp\DailyFlow\apps\dailyflow-calendar\bundle'
# 期望：dailyflow-calendar 0.1.0 — PASSED
```

### 步骤 5：实际启动 + 截图

```powershell
python -X utf8 tools/octo run 'D:\Life\AgenticApp\DailyFlow\apps\dailyflow-calendar\bundle' --port 8143 --hidden --detach
sleep 3
python -X utf8 tools/octo shot 8143 'D:\Life\AgenticApp\DailyFlow\apps\dailyflow-calendar\build\01-launch.png'
curl -s -m 2 127.0.0.1:8143/quit
```

### 步骤 6：拆分其他 3 个 App

按同样流程复制 dailyflow-expense / dailyflow-diary / dailyflow-period 的 splash 与配置。

---

## 7. 开发路线图

| 阶段 | 任务 | 状态 |
|------|------|------|
| **0** | dailyflow-calendar v0.5 — 纯日历，已完成 | ✅ |
| 1 | dailyflow-calendar v0.6 — 添加点击月份导航响应 | 待办 |
| 2 | dailyflow-calendar v0.7 — 添加状态栏动态更新（当前选中日期） | 待办 |
| 3 | dailyflow-expense v0.5 — 复制 v0.2 记账功能 | 待办 |
| 4 | dailyflow-diary v0.5 — 全新实现日记 App | 待办 |
| 5 | dailyflow-period v0.5 — 全新实现经期 App | 待办 |
| 6 | 集成测试 — 4 个 App 同时可安装运行 | 待办 |

---

## 8. 风险与回退方案

| 风险 | 应对 |
|------|------|
| `dailyflow-calendar 0.1.0` ID 被占用 | 改名 `dailyflow-cal-1` 等 |
| Sandbox 隔离导致无法跨 App 同步 | 接受，每个 App 独立数据 |
| Splash 解析器再次丢 widget | 退回到 v0.4 baseline (日历 42 cell 已验证) |
| 用户不接受多 App 安装成本 | 提供"DailyFlow Suite"超级 bundle 把 4 个合并 |

---

## 9. 验收标准

每个 bundle 必须：

- ✅ `octo check` 输出 `XXX 0.1.0 — PASSED`
- ✅ 启动 0 个 `[E]` 错误
- ✅ 默认界面渲染完整（截图验证）
- ✅ 至少 1 个交互功能工作（点击/输入/导航）
- ✅ 数据持久化（重启后状态保留）

---

## 10. 文档同步

每完成一个 bundle，需要更新：

- `D:\Life\AgenticApp\agent.md` — 工作区状态
- `D:\Life\AgenticApp\DailyFlow\apps\<app>\README.md` — 单 App 文档
- `D:\Life\AgenticApp\DailyFlow\docs\PRODUCT_PLAN.md` — 标注 bundle 拆分决策

---

**完成时间**：待 4 个 App 全部通过 `octo check` + 实际启动验证。
**当前进度**：仅 dailyflow-calendar v0.4 stable 通过验证。其他 3 个待开发。
