# DailyFlow 技术栈详解

2026-10-02 用户明确的硬约束：DailyFlow 只使用 OctoScript/Splash 脚本实现，不扩展或修改 Shell、host service、运行时的 Rust 层。可以使用宿主已公开且获授权的 API；缺失能力列为平台依赖，不能通过原生扩展补齐。统一时间协议保留在应用层。已有 Windows 渲染补丁继续保留，不属于新增产品功能的实施路径。

**日期**：2026-10-02
**目的**：让任何接手 DailyFlow 项目的 agent/开发者理解我们用什么技术写

---

## 0. 核心结论

DailyFlow 项目的 App **全部用 Splash 编写**（`.splash` 文件）。**不涉及 Rust 编程**。

只有 OctoSense Shell **本身** 是 Rust + Makepad widget 系统写的。DailyFlow 项目**不修改 Shell 内部代码**。

---

## 1. 两层技术栈

| | Splash（我们用） | Rust + Makepad widget（Shell 用） |
|--|-----------------|-------------------------------|
| **使用者** | 第三方 App 开发者（您、我） | OctoSense 核心团队 |
| **代码位置** | `D:/Life/AgenticApp/DailyFlow/bundle/main.splash` | `D:/Life/AgenticApp/OctoSense/`, `D:/Life/AgenticApp/makepad/` |
| **执行方式** | Splash VM 解释执行 | 编译为机器码 |
| **编译需要** | ❌ 无需 | ✅ `cargo build --release` |
| **改完生效** | 重启 App（秒级） | 重新编译 Shell（分钟级） |
| **学习成本** | 低（DSL） | 高（Rust + widget 系统） |
| **能力上限** | 用现有 widget 组合 | 完全自由（含 shader、自定义 widget） |

---

## 2. Splash 是什么

**全称**：Makepad Splash Script

**类比**：
- iOS 开发者写 Swift → 编译成 iOS App
- Android 开发者写 Kotlin → 编译成 Android App
- **Splash 开发者写 Splash → 被 Shell 解释执行**

### 2.1 Splash 代码长什么样

```splash
// 一个简单 Splash app
let expenses = []

fn load(){
    if fs.exists("expenses.json") {
        let v = fs.read("expenses.json").parse_json()
        if v != nil { expenses = v }
    }
}

fn add(amount){
    expenses.push({amount: amount, date: time_now()})
    fs.write("expenses.json", expenses.to_json())
}

start_timeout(0.05, || load())

SolidView{width: Fill height: Fill
    ButtonFlat{text: "添加 10 元" on_click: || add(10)
        draw_bg +: {color: #x007aff}}
}
```

### 2.2 关键特征

- **声明式 UI**：用 `{Widget{...}}` 嵌套定义 UI 树
- **闭包作为事件处理**：`on_click: || add(10)`
- **自动 fs 沙盒**：`fs.read/write` 在 App 自己的目录
- **即时生效**：改完重启 App 即可

### 2.3 限制

| 限制 | 值/说明 |
|------|---------|
| 入口文件 | 只有 `main.splash` 一个 |
| 文件包含 | 全部 UI + 逻辑 + 数据 |
| 不能 import/require | 每个 App 是独立 Splash VM 实例 |
| 自定义 widget | ❌ 不支持（只能用现有的） |
| Shader 自绘 | ❌ 不支持 |
| 编译 | ❌ 无（解释执行） |
| 性能 | 解释执行，widget 多了会卡 |

---

## 3. Rust + Makepad widget 是什么

这是 OctoSense Shell 本身用的技术栈。DailyFlow 开发者**不需要碰**，但理解它能帮您理解 Shell 的能力上限。

### 3.1 在哪里

- **OctoSense Shell 仓库**：`D:/Life/AgenticApp/OctoSense/crates/`
  - `shell/src/lib.rs`（Shell 主逻辑）
  - `shell/src/apps.rs`（内置 App 注册）
  - `shell/src/glance.rs`（glance 卡片服务）
- **Makepad 内置 App**：`D:/Life/AgenticApp/makepad/apps/`
  - `apps/calendar/`（日历 Rust App）
  - `apps/calendar/src/month.rs`（自绘日历 widget）
  - `apps/photos/`, `apps/news/` 等

### 3.2 能力上限

- 自定义 widget（如 `CalendarMonthCanvas`）
- GPU shader 自绘（如 `sdf_box` 圆角矩形）
- 集成到 Shell in-process（不是独立进程）

### 3.3 改它需要什么

- Rust 编程能力（中级+）
- Makepad widget 系统理解（深）
- 重新编译 Shell（`cargo build --release`，约 10 分钟）

**结论**：除非您要做 Makepad 核心贡献，否则**不要碰 Rust 代码**。

---

## 4. OctoSense 框架的完整能力图

```
┌────────────────────────────────────────────────────┐
│              OctoSense Shell (Rust)                 │
│  ┌─────────────────────────────────────────────┐ │
│  │  Window Manager (WM)                        │ │
│  │  ┌──────────────┐  ┌──────────────┐        │ │
│  │  │ Mail         │  │ Photos       │ ...    │ │
│  │  │ (Rust+Mkpad) │  │ (Rust+Mkpad) │        │ │
│  │  └──────────────┘  └──────────────┘        │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │  Card Runner (跑 Splash App)                │ │
│  │  ┌──────────────┐  ┌──────────────┐        │ │
│  │  │ DailyFlow (Splash)│  │ my-notes    │ ...    │ │
│  │  │ -sandbox A   │  │ -sandbox B  │        │ │
│  │  └──────────────┘  └──────────────┘        │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │  Host Services (App 可调的 API)             │ │
│  │  ✓ mail     ✓ news     ✓ llm               │ │
│  │  ✓ model    ✓ glance                       │ │
│  │  ✗ shell.run   ✗ octos.run   ✗ navigate  │ │
│  └─────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

---

## 5. 我们项目的实际技术栈

```
┌────────────────────────────────────────────────────┐
│           DailyFlow App Bundle                         │
│  ┌────────────────────────────────────────────┐   │
│  │  main.splash (Splash DSL)                  │   │
│  │  - UI 树（SolidView/View/Label/Button 等） │   │
│  │  - 业务逻辑（fn 闭包）                      │   │
│  │  - 数据持久化（fs.write JSON）               │   │
│  └────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────┐   │
│  │  manifest.json (JSON)                      │   │
│  │  listing.json (JSON)                       │   │
│  │  assets/icon.svg (SVG)                     │   │
│  │  screenshots/01-main.png (PNG)             │   │
│  └────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

**不需要**：Rust 编译器、cargl、nodejs（仅 dev 时用 `tools/octo` 命令）

**需要**：理解 Splash 语法、能用 `/click`, `/k?t=` 远程桥测试

---

## 6. 调试与测试工具（不需要 Rust）

| 工具 | 用途 |
|------|------|
| `python -X utf8 tools/octo check` | 验证 bundle 通过门控 |
| `python -X utf8 tools/octo run --port 8143` | 启动 card-host |
| `curl 127.0.0.1:8143/snap` | 看 widget tree |
| `curl -X POST 127.0.0.1:8143/click` | 模拟点击 |
| `curl 127.0.0.1:8143/k?t=...` | 输入文本 |
| `python -X utf8 tools/octo shot` | 截图 |
| `cat .local-state/card-host.log \| grep "\[E\]"` | 看错误 |

---

## 7. 给接手 Agent 的一句话总结

> DailyFlow 项目的所有功能都在 `.splash` 文件里写。Rust 代码**只在 OctoSense Shell 仓库里**，不要去改。如果遇到 Splash 写不出的功能（如自定义 widget），不要尝试用 Rust——那是不同的工作量级。
