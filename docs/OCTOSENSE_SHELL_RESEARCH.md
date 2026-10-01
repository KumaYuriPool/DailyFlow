# OctoSense Shell 架构调研报告

**日期**：2026-10-02
**调研者**：DailyFlow 项目 agent
**目的**：弄清 OctoSense 桌面 Shell 是否支持我们想要的"4 个 dailyflow-* App 联动"

---

## 0. 关键结论

| 能力 | 当前 Shell 支持 | 备注 |
|------|----------------|------|
| **装多个 App** | ✅ | 用户从 Shell catalog 启动 |
| **同时存在多个 App 沙盒** | ✅ | 每个 App 独立 fs |
| **App 启动另一个 App** | ❌ | 没有 `shell.run` / `octos.run` host service |
| **App 读其他 App 数据** | ❌ | sandbox 隔离 |
| **App 之间通信** | ❌ | 仅 Mail/News/Glance/AI 服务 |

**对 DailyFlow 项目的影响**：

1. ✅ 可以装 4 个 dailyflow-* App 到 Shell
2. ❌ App 之间**不能联动**——calendar 启动不了 expense
3. ❌ App 之间**不能共享数据**——calendar 读不到 expense 的账

---

## 1. 调研过程

### 1.1 第一步：找到 OctoSense Shell

```bash
tasklist | grep octosense
# 结果: octosense.exe  PID 38964
```

进程名 `octosense.exe` 正在运行。数据目录：

```
C:\Users\44231\.octosense\
├── apps\
│   ├── .host\news\
│   └── .system\
│       ├── os.ai-providers\
│       ├── os.mail\
│       ├── os.maps\
│       ├── os.news\
│       ├── os.photos\
│       └── os.youtube\
├── logs\
├── secrets\
└── wm\
    └── themes\tokyo-night\
```

**已装系统 App**：mail / maps / news / photos / youtube / ai-providers。
**注意**：**没有** `os.calendar`！

### 1.2 第二步：找 Shell 源码

```
D:/Life/AgenticApp/OctoSense/crates/
├── ai-host\
├── app-contract\
├── app-hub-app\
├── app-policy\
├── appstore\
├── card-studio\
├── shell\         ← 这里
│   ├── src\
│   │   ├── lib.rs
│   │   ├── apps.rs        ← host service 注册
│   │   ├── glance.rs
│   │   └── ...
│   └── ...
```

### 1.3 第三步：搜 host services

```bash
grep "register_host_service" crates/shell/src/apps.rs
```

**结果**：

```rust
fn register_host_services() {
    crate::glance::register();           // ✓ glance 服务
    if demo {
        octosense_mail_service::register_demo()  // ✓ mail 服务
    } else {
        octosense_mail_service::register()       // ✓ mail 服务
    }
    register_news();                     // ✓ news 服务
}
```

加上 `ai-host` 注册的 `llm` / `model`：

**Shell 当前提供的 host services**：
- ✅ `mail`（邮件）
- ✅ `glance`（卡片展示）
- ✅ `news`（新闻）
- ✅ `llm` / `model`（AI）
- ❌ `shell.run` / `octos.run` / `navigate` / `launch_app`（**没有**）

### 1.4 第四步：搜官方文档

`D:/Life/AgenticApp/OctoScript-App-Design-Flow/docs/HOST-SERVICES.md`：

> `octos`: **None in OctoSense.** The four `octos.*` capabilities pass the gate, but no OctoSense shell registers a service for them: a call answers `no service answers "octos" on this device"`.

—— 官方文档明确确认 `octos.*` 没有服务。

### 1.5 第五步：看 Shell 内部启动 API

`crates/shell/src/lib.rs`：

```rust
fn launch_app(&mut self, cx: &mut Cx, app_id: &str) { ... }
fn launch_app_with_args(&mut self, cx: &mut Cx, app_id: &str, extra_args: &[String]) { ... }
```

**Shell 内部有启动 App 的能力**——但**没暴露给 Splash App**。

---

## 2. 结论详述

### 2.1 App 装到 Shell 是可行的

App Hub / appstore 列表支持多 App。Shell `Screen::Running(app_id)` 切换。

### 2.2 App 装到 Shell 后的体验

- 用户桌面（Shell Home）显示 4 个 dailyflow-* App 图标
- 点击任一图标 → 启动该 App
- 切换 App → 关闭当前，启动另一个（Shell 内置 launch_app）
- 数据**每个 App 独立**——一个 App 看不到另一个的数据

### 2.3 我们的开发环境

我们用 `card-host` 独立启动 bundle（不是真正的 Shell）。但 `card-host --bundle` 一次只跑一个 bundle——所以**开发时无法验证多 App 联动**。

### 2.4 未来可能

如果 OctoSense 加上 `octos.run` 服务（Rust 几行代码），Splash App 可以 `host.request("octos.run", {app: "id"})`。但**目前没有**。

---

## 3. 我们的架构决定

### 3.1 选项对比

| 选项 | 数据共享 | 装到 Shell | 工作量 | 状态 |
|------|----------|-----------|--------|------|
| A. 4 个独立 bundle | ❌ | ✅ | 中 | 当前实施 |
| B. 1 bundle + 5 splash 文件 | ❌（不支持 include） | ✅ | — | 不可行 |
| C. 1 bundle + 1 splash 多 view | ✅ | ✅ | 中 | **推荐** |
| D. 改 Shell 内置 Calendar（Rust） | — | — | 极大 | 备选 |

### 3.2 推荐：C 方案

**理由**：
- 1 个 bundle → 1 个沙盒 → fs 共享
- 1 个 main.splash → Splash 框架原生支持
- 入口 splash 含日历（默认）+ 底部 4 tab 切换到记账/日记/经期
- 单 bundle 单 splash，工作量可控（widget 数量 ≤ 80）

### 3.3 Splash 多 splash 文件支持性

**测试结果**：Splash **不支持** `import` / `require` / `include`：
- 只有 `main.splash` 一个入口文件
- `fs.read` 能读其他 splash 文件内容，但**不能执行**它们
- 没有 `eval(string)` API

所以 B 方案不可行。

### 3.4 单一 splash 多 view 的可行性

**测试结果**（v0.5 已验证）：
- 1 个 main.splash 80 widget 工作
- 多个 View 用 `set_visible(true/false)` 切换工作
- 共享 fs（如 expenses.json）

**结论**：C 方案完全可行。

---

## 4. 实际产出

### 4.1 现有 4 bundle 拆分

```
D:\Life\AgenticApp\DailyFlow\apps\
├── dailyflow-calendar\bundle\    ✅ octo check PASSED
├── dailyflow-expense\bundle\     ✅ octo check PASSED + 占位 splash
├── dailyflow-diary\bundle\       ✅ octo check PASSED + 占位 splash
└── dailyflow-period\bundle\      ✅ octo check PASSED + 占位 splash
```

### 4.2 每日操作要点

每个 bundle 独立可启动 + 验证。完整开发流程见 `ACCEPTANCE_PROMPT.md`。

---

## 5. 未来方向

| 时机 | 行动 |
|------|------|
| OctoSense 加 `octos.run` host service | 4 bundle 升级：calendar 加 `host.request("octos.run", {app: "dailyflow-expense"})` |
| OctoSense 加共享存储 capability | 4 bundle 共享一个 db 文件 |
| OctoSense 加日历 Rust App API | 我们的 dailyflow-calendar 改用之 |
| 我们决定改用 Rust | 学 Rust + Makepad widget 重写 |

---

## 6. 给接手 Agent 的提醒

- 不要假设 App 能调起另一个 App——**当前不支持**
- 不要假设 App 能读其他 App 的数据——**当前不支持**
- OctoSense Shell 已装 = 仅意味着"能装多个 dailyflow-* App"，**不意味着能联动**
- 如果用户提"App 之间通信"，**先看 HOST-SERVICES.md 看是否真有 service**

---

## 7. 相关文件

- `D:/Life/AgenticApp/OctoScript-App-Design-Flow/docs/HOST-SERVICES.md` — 服务列表
- `D:/Life/AgenticApp/OctoSense/crates/shell/src/apps.rs` — Shell 服务注册
- `D:/Life/AgenticApp/OctoSense/crates/shell/src/lib.rs` — `launch_app` 内部 API
- `D:/Life/AgenticApp/OctoSense/crates/appstore/src/lib.rs` — App 列表管理
- `D:/Life/AgenticApp/makepad/apps/calendar/` — Rust Calendar App（仅供参考）
