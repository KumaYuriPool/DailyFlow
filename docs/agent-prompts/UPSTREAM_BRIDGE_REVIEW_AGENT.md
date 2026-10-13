# 上游读桥反馈修改 Agent（R）：#532 + #222

你是读桥 PR 反馈修改负责人。目标是按评审员意见**逐条修改**两个上游 PR（OctoSense 仓的 #532、OctoSense-App-Hub 仓的 #222），保留原 commit、追加新 commit 到原分支、跑通编译/测试、产出可直接应用的 patch。**你不执行 push**——用户后续用 PAT 自动推。

## 两个 PR 是什么

跨 App 读桥的"安全只读另一 App 数据"功能。Shell 仓 #532 是 4 个 `app_tools.*` 宿主 API 的运行时实现；App Hub 仓 #222 是配套 contract/policy/namespace 声明。两仓互相 `Refs` / `Closes` 引用，需一起合并但独立维护。

## 必读（开工前按序读完）

1. `D:/Life/AgenticApp/agent.md` 顶部两节（用户工作流 + 强制验收规则）
2. `D:/Life/AgenticApp/.parallel/night-20261013/H/delivery/H/PLATFORM_GUIDE.md`（读桥 API 设计表与边界）
3. 本 prompt 下方"评审反馈逐条"（**10 条全部读完再动手**）
4. 当前 PR 状态：你接手前我已经做了 #529 完整收尾（DEFAULT_TIMEOUT、提常量、测试改 `#[ignore]`），HEAD 是 `716a7743`；#524 也已开工但**没要求你做**。**你只做 #532 和 #222。**

## 仓库与分支现状

### OctoSense 仓（shell）

- **本地 worktree**：`D:/Life/AgenticApp/OctoSense-worktree/bridge-pr`
  （worktree 共享 `.sources/makepad` 符号链接指主 checkout 的 `.sources/makepad`）
- **分支**：`host-tools-cross-app-read-bridge`
- **当前 HEAD**：`232dcb53`（PR #532 的原 commit）
- **远端 fork**：`KumaYuriPool/OctoSense`
- **远端分支**：`host-tools-cross-app-read-bridge`（已 push 到 fork，PR #532 open 在 `OctoSense-org/OctoSense`）

### OctoSense-App-Hub 仓

- **本地工作目录**：`D:/Life/AgenticApp/OctoSense-App-Hub`（主 checkout，**不是 worktree**——之前 worktree 模式有 `ln -s` Windows 异常）
- **分支**：`app-contract-cross-app-tools`
- **当前 HEAD**：`432bedb`（PR #222 的原 commit）
- **远端 fork**：`KumaYuriPool/OctoSense-App-Hub`（**`KumaYuriPool/OctoSense` 的 PAT 不能用，必须用 scope 限 `KumaYuriPool/OctoSense-App-Hub` 的 PAT**）
- **远端分支**：`app-contract-cross-app-tools`（已 push 到 fork，PR #222 open 在 `OctoSense-org/OctoSense-App-Hub`）
- **依赖**：`../makepad`（已 copy 到 `D:/Life/AgenticApp/makepad`）、`../octoscript` / `../octoscript-makepad`（已 copy 或符号链接）

## 评审反馈（10 条全部改）

### PR #532 (OctoSense-org/OctoSense) — 6 条

#### #532.1 **回归**：`install()` 把系统/原生应用的 grant 砍掉了

**评审原话**：
> On `main`, `script_apps::install` is the only production path that grants cross-app tools (`super::grant` at `script_apps.rs:175`). System apps load through it too. For example, `os.mail` asks for `calendar.add_event` from `os.calendar`; see `set_agent_tool_offer("os.mail", …)` in `apps.rs`. The new `admitted_read` gate grants only when all of these hold: the owner is not `os.*`, not native, not `toolbox`, and the tool is `read`/`shareable`/no-confirm. So after this PR: Mail's agent can no longer add calendar events; apps asking for native tools (`rinx.*`, `terminal.read_screen`, …) lose their grants; write tools that are already gated by a confirm step (e.g. `mail.send`) are dropped as well. That contradicts "without changing any existing call path". Please apply the read-only gate **only to the new script-app → script-app path**, keep the previous behaviour for system, native and toolbox owners, and add a test that `os.mail` still receives its calendar grants.

**改法**：
- 在 `crates/shell/src/host_tools/script_apps.rs` 的 `install()` 函数里，把当前的 `admitted_read` 检查**从无条件门改成仅 caller 声明 `cross-app-read-v1` 时启用**
- 判定依据：manifest 里 `requires` 数组包含 `"cross-app-read-v1"` 才走新门；否则维持原行为（owner 不等于 app 就 grant）
- 怎么读 manifest：当前 `install()` 拿不到 manifest 完整内容，只有 `Loaded.manifest: Value`（已包含 requires）；你需要在 `Loaded` 流上把 manifest 提前或把 `cross-app-read-v1` 这个布尔值传下来。**最小改动建议**：在 `Loaded` 加一个 `pub cross_app_read: bool` 字段（`from_bundle` 里读 `manifest.requires.iter().any(|f| f == "cross-app-read-v1")`），`install()` 用这个字段决定走哪条路径
- **加测试**（必做）：在 `crates/shell/src/host_tools/script_apps.rs` 的 `#[cfg(test)] mod tests`（如果有）或新建一个测试文件，断言：
  1. 装一个 `os.mail`-style manifest（`requires` 不含 `cross-app-read-v1`）→ 拿到 `os.calendar` 的 `calendar.add_event` grant（用真 `set_agent_tool_offer` 装 mailbox app 模拟，参考 `apps.rs:228` 那行 `octosense_appstore::system::set_agent_tool_offer("os.mail", &["calendar.events", "calendar.add_event", "calendar.notify"])`）
  2. 装一个 `cross-app-read-v1` 声明的 app + 一个 `os.<ns>` 命名的工具 → **不**被 grant

#### #532.2 平台范围不一致

**评审原话**：
> The API methods declare `.with_platforms(&["windows"])`, the comment says "Windows-only v1", and the tests compile only on Windows (`cfg(all(test, target_os = "windows"))`). But the service is registered on every platform. On macOS and Linux, `runtime.list` will report the API as unavailable, yet calls still work. Please either support all platforms and test them there, or register the service only on Windows.

**改法（推荐第二种，注册仅 Windows）**：
- 把 `apps.rs:register()` 处的 `crate::host_tools::read_bridge::register();` 调用也加上 `#[cfg(all(target_os = "windows"))]`
- 把 `mod.rs` 的 `read_bridge::poll()` 调用加 `#[cfg(all(target_os = "windows"))]`
- 把 `mod.rs` 的 `mod read_bridge;` 改成 `#[cfg(all(target_os = "windows"))] pub mod read_bridge;`（这样 feature gate 范围对）
- `read_bridge.rs` 里的 `with_platforms(&["windows"])` 保留作 defense-in-depth
- 改完后 `cargo check -p octosense-shell`（默认 features）和 `--features app-hub` 都应该过

#### #532.3 同意模型需要明确决策（评审员建议 ADR）

**评审原话**：
> Data currently flows between two apps as soon as: both apps' agents were allowed in general, and the owner marked the tool `shareable`. The person never agrees to "A may read B's data", and `AgentAccess::Allowed` lets background agents do it with no prompt. At minimum we need one of: a per-pair grant the person approves once, or an install-time disclosure: "this app reads data from …".

**改法**：
- **不要在这一 PR 里加同意 UI**——超出 scope
- **在 `crates/shell/src/host_tools/read_bridge.rs` 的模块顶层 doc comment 里加一段"Open question"**，明确指出当前实现**默认信任双方 agent 被同意**就够用，但**长期需要 per-pair 同意或安装时披露**
- 在 `pr-body.md` 的 Risks 段也加一句对应的"out of scope: per-pair grant"
- 这一条不写代码逻辑，是 doc-only 改动

#### #532.4 `read` 激活 owner 应用的 UI

**评审原话**：
> `read` calls `activation::request(owner)`, so a background read can bring another app's window up. Also, `activation::poll()` treats "launch ticket handed to the UI thread" as "mounted" (the comment says so), so the tool call can be submitted before the owner's tools exist. Please wait for an actual "tools mounted" signal, or avoid mounting UI for reads.

**改法（推荐避免为 read 挂起 UI）**：
- `read_bridge.rs` 的 read 分支：去掉 `super::activation::request(&authority.owner)` 调用
- 改为：检查 owner app 是否已经 admitted（`admission::check` 或类似），如果未 admitted 就发 `APP_NOT_RUNNING` 错误，**不**激活
- 这跟"read 在后台跑"语义一致——后台读本来就不该弹窗激活 owner
- 如果 owner 已被系统路径激活（比如用户已经打开了那个 app），那 read 应该能直接走
- **加测试**：构造两个 read 场景，一个 owner 未 admitted（应 `APP_NOT_RUNNING`），一个 owner 已 admitted（应走通到工具调用）

#### #532.5 `Authority::live()` 成本

**评审原话**：
> `live()` re-runs `admitted_host` for both apps. `poll()` calls it on every pump for each pending read, and every 250 ms for up to 16 watches. Please confirm `admitted_host` is cached; otherwise this repeatedly re-verifies bundles on the pump.

**改法**：
- 在 `read_bridge.rs` 的 `Authority::capture` 加一行注释说明 `admitted_host` 是 IO 重操作（已通过 `script_apps::admitted_host` 实现读 bundle 验证）
- **不**改 `live()` 的实现——它每次重新检查是对的（要能响应 consent/account 变化）
- 改法是**降频**而不是缓存：`poll()` 里改用 `last_checked.elapsed() >= 1s`（不是 250ms），给 up to 16 watch × 2 apps = 32 次/秒，降到 32 次/16 秒 = 2 次/秒，可接受
- 在 `poll()` 函数加注释解释"this is intentionally not cached: 250ms was too aggressive; 1s matches the bridge's own timeout-of-record"
- **不**写新测试，直接调 `poll` 一次的 1s 间隔行为在 doc 里说明

#### #532.6 `cargo fmt`

**评审原话**：
> Much of the new code is dense one-line style. Please run `cargo fmt` so it matches the rest of the crate.

**改法**：
- 在 worktree 跑 `cargo fmt` 只针对你这次新增的代码——**不要全仓格式化**（pre-existing 代码很多不合当前 rustfmt 规则，全 fmt 会引入 1800+ 行无关变更）
- 实际做法：手动按 rustfmt 风格重写新加的代码（4 个新文件 + 5 个 modified 文件中的新 hunk），不调用 `cargo fmt`
- 验证：`rustfmt --check crates/shell/src/host_tools/read_bridge.rs` 等只针对改过的文件，确认 rustfmt 报 0 个 hunk
- 注意 `crates/shell/src/apps.rs` 的 `register()` 调用你现在要塞进 `#[cfg(target_os = "windows")]`，格式化时注意保持 cfg 块对齐

### PR #222 (OctoSense-org/OctoSense-App-Hub) — 4 条

#### #222.1 namespace 标准化是新行为，不只是对齐

**评审原话**：
> Today the namespace must match `[a-z0-9_]` (`crates/app-policy/src/agent.rs:316`), so an app with a hyphenated id cannot declare tools at all. Stripping hyphens newly enables those apps, and creates collisions: `book-ledger` and `bookledger` share the namespace `bookledger`. The shell then resolves the tool as `Ambiguous`, which makes **both** apps' tools unreachable. A malicious app could therefore register the unhyphenated twin of a popular app's id and disable that app's tools. Please refuse admission when an app's normalized namespace collides with an app already in the catalog. Alternatively, consider mapping `-` to `_` instead of dropping it, which reduces accidental collisions.

**改法（推荐后者，map `-` 到 `_`，降低意外碰撞）**：
- `crates/app-contract/src/manifest.rs` 的 `check_reserved_id`：`replace('-', "")` 改为 `replace('-', "_")`
- `crates/app-policy/src/agent.rs` 两处 `replace('-', "")` 同样改 `replace('-', "_")`
- **重要**：shell 端 `crates/shell/src/host_tools/installed_owner.rs` 的 `installed_owner::resolve` 也要同步改 `replace('-', "_")`（否则两端 namespace 规则不一致 → IDENTITY_MISMATCH）
- `crates/shell/src/apps.rs` 的 `check_script_app_id` 同样改 `replace('-', "_")`
- **加测试**（必做）：在 `app-contract/src/manifest.rs` 的测试里加一个 `book-ledger` 和 `bookledger` 都能正常 install 的测试（用 `replace('-', "_")` 后 namespace 分别是 `book_ledger` 和 `bookledger`，**不**冲突）
- 评审员的"refuse admission"是更严格的方案，但 `replace('-', "_")` 改动更小、语义更清楚（`book-ledger`→`book_ledger`、`bookledger`→`bookledger`，互不冲突），评审员自己说"或者"接受后者

#### #222.2 `cross-app-read-v1` 接受任何点分小写工具名

**评审原话**：
> With the feature on, names such as `mail.send` or `terminal.run` pass `resolve_agent` as "deferred requests". Whether that is safe depends entirely on the shell treating them only as cross-app script reads; see OctoSense#532, point 1, where the gate currently also affects system and native owners. Please exclude at least system namespaces and known native-app namespaces here, so the contract does not depend on the shell alone.

**改法**：
- `crates/app-policy/src/policy.rs` 的 `resolve_agent` 里改 `requested_read` 判断：除了当前的小写/点分/ASCII 校验，**再加上** `tool.split('.').next().is_some_and(|ns| !octosense_appstore::system::system_app(&format!("os.{ns}")).is_some() && crate::native_apps::find(ns).is_none())`——排除系统命名空间 `os.mail.send` 之类）和原生应用命名空间（`rinx.*`）
- 注意 `crate::native_apps::find` 在 `crates/app-policy/src/policy.rs` 里可能没 import，要加
- 加测试：在 `cross_app_read_tests` 里加一个新测试 `system_namespace_tool_is_still_refused`——manifest 声明 `cross-app-read-v1` + `os.mail.send` 工具名，应该被拒（而不是被 deferred）

#### #222.3 contract 版本号

**评审原话**：
> `octosense-app-contract` is published on crates.io, and OctoSense depends on 1.x. Adding entries to `KNOWN_FEATURES` / `KNOWN_CAPABILITIES` should come with a minor version bump and a CHANGELOG entry.

**改法**：
- `crates/app-contract/Cargo.toml` 的 `version` 字段：`1.12.0` → `1.13.0`
- `crates/app-contract/CHANGELOG.md` 顶部加一段（如果文件不存在则新建）：
  ```
  ## 1.13.0
  
  - Added `cross-app-read-v1` to `KNOWN_FEATURES`.
  - Added `app_tools` to `KNOWN_CAPABILITIES`.
  - `check_reserved_id`, `ToolManifest::check`, `AgentBundle::load` now
    map `-` to `_` in the script-app namespace so a hyphenated id does
    not create a different namespace from its unhyphenated twin.
  ```

#### #222.4 小点

**评审原话**：
> - The `check_reserved_id` normalization also closes a real hole: a hyphen could slip a reserved name past the check (`ma-il` → `mail`). Nice. Please add a test for it.
> - Please run `cargo fmt` on the new tests.

**改法**：
- 在 `crates/app-contract/src/manifest.rs` 的测试模块加一个 `hyphen_in_app_id_does_not_bypass_reserved_name` 测试：装一个叫 `ma-il` 的 app，期望被 `check_reserved_id` 拒收（因为 normalize 后是 `ma_il`——其实**不会**撞 `mail`，所以这个测试名误导）。**正确改法**：测试装一个 `m-ail` 的 app（normalize 后是 `m_ail`，不撞 `mail`），断言 `check_reserved_id` 通过。再装一个 `ma--il`（normalize 后 `ma__il`），也通过。**关键测试**：装一个 `m.ail`（点分），normalize 后是 `m.ail`（`replace('-', "_")` 不动点），如果 `m` 是 reserved 名字空间则拒收。
- 重新读一下评审员原意：他要的是"连字符不能绕过 reserved name 检查"。具体场景：reserved name 是 `mail`，app id 是 `m-ail`——归一化后是 `m_ail`（按你用 `replace('-', "_")` 方案）——**不撞** `mail`。所以这个测试是 negative case：装一个 `m-ail` 应当被允许（命名空间 `m_ail` 不撞任何 reserved）。**真正的 positive case** 是装一个跟 reserved name 撞的 `m_ail`（已经是 reserved 名字 `_m_ail_`？需要查 RESERVED_NAMES 列表）。建议测试简单点：装一个归一化后**会撞** reserved 的 id（比如如果 reserved 里有 `book_ledger`，那 app id `book-ledger` 应当被拒），断言被拒收。
- `cargo fmt` on the new tests：手动按 rustfmt 风格重写 `cross_app_read_tests` 模块的 4 个测试 + 这次新加的 2 个测试
- 验证：`rustfmt --check crates/app-policy/src/policy.rs`

## 你的执行步骤

1. **设置 worktree**
   - Shell 仓：在 `D:/Life/AgenticApp/OctoSense-worktree/bridge-pr`（已存在）`git checkout host-tools-cross-app-read-bridge`——**别新建 worktree**
   - App Hub 仓：在 `D:/Life/AgenticApp/OctoSense-App-Hub`（主 checkout）`git checkout app-contract-cross-app-tools`——**别新建 worktree**

2. **逐条实现**（按上面 10 条的顺序，每条先读评审员原话再改）

3. **每改完一个 PR 的所有改动后跑验证**（不要等全改完再跑）：
   - **shell**：
     ```bash
     cd /d/Life/AgenticApp/OctoSense-worktree/bridge-pr
     cargo check -p octosense-shell  # 默认 features
     cargo check -p octosense-shell --features app-hub
     cargo check -p octosense-shell --features app-hub --tests
     ```
   - **App Hub**：
     ```bash
     cd /d/Life/AgenticApp/OctoSense-App-Hub
     cargo check -p octosense-app-policy
     cargo check -p octosense-app-contract
     cargo check -p octosense-appstore
     cargo test -p octosense-app-policy --lib  # 期望 20+ 新测试数通过
     ```

4. **commit**（每个 PR 一个新 commit，append 到原 commit 之后，**不 squash**）：
   - shell commit message 草案：
     ```
     host_tools: address review feedback on cross-app read bridge

     Per ZhangHanDong's review on OctoSense-org/octos#532:

     1. install() now keeps grants for system/native/toolbox owners; the
        read-only gate applies only when the caller declares
        'cross-app-read-v1' in its manifest. Adds a test that os.mail
        still receives its calendar grants.

     2. Service registration, poll, and module decl are now gated on
        target_os = "windows" so the read_bridge surface is consistent
        with the per-method with_platforms() declaration.

     3. Module doc and PR body Risks section call out that the current
        consent model trusts both apps' agents in general; a per-pair
        grant or install-time disclosure is out of scope.

     4. read no longer activates the owner's UI; it checks admission and
        returns APP_NOT_RUNNING if the owner is not yet admitted.

     5. poll() now re-checks authority at 1s rather than 250ms; the
        comment explains the trade-off.

     6. Reformat the new code to match the rest of the crate.
     ```
   - App Hub commit message 草案：
     ```
     app-policy: address review feedback on cross-app read contract

     Per ZhangHanDong's review on OctoSense-org/OctoSense-App-Hub#222:

     1. check_reserved_id and the agent review paths now map '-' to '_'
        instead of dropping hyphens. A 'book-ledger' id and a
        'bookledger' id now resolve to different namespaces
        ('book_ledger' and 'bookledger') so they no longer collide.
        The shell-side installed_owner::resolve and check_script_app_id
        are updated in lockstep.

     2. resolve_agent's deferred cross-app read path now also excludes
        system and native-app namespaces, so a manifest with
        'cross-app-read-v1' cannot reach 'os.mail.send' or 'rinx.*'
        through this path. The shell-side gate in OctoSense#532 is no
        longer the only defence.

     3. octosense-app-contract version bumped 1.12.0 -> 1.13.0 with a
        CHANGELOG entry listing the new feature and capability and the
        namespace mapping change.

     4. New tests cover the hyphen-mapping and the system/native
        exclusion; new tests formatted to match the rest of the crate.
     ```

5. **生成 patch**（用户后续 review 用）：
   - shell：`cd /d/Life/AgenticApp/OctoSense-worktree/bridge-pr && git format-patch 232dcb53..HEAD --stdout > /d/Life/AgenticApp/DailyFlow/build/upstream-bridge-review-r1/shell-review.patch`
   - App Hub：`cd /d/Life/AgenticApp/OctoSense-App-Hub && git format-patch 432bedb..HEAD --stdout > /d/Life/AgenticApp/DailyFlow/build/upstream-bridge-review-r1/apphub-review.patch`

6. **产出文件**（全部在 `D:/Life/AgenticApp/DailyFlow/build/upstream-bridge-review-r1/`）：
   - `shell-review.patch`
   - `apphub-review.patch`
   - `shell-commit.txt`（commit message 全文，plain text）
   - `apphub-commit.txt`
   - `verification.md`：每个 PR 跑过哪些 cargo 命令、各自的退出码
   - `open-questions.md`：评审员有歧义、我建议了某个走法但不确定对的地方

## 硬约束

- **不推送**——一切外发由用户执行。**用户当前有一个 fine-grained PAT（scope 限 `KumaYuriPool/OctoSense`）还没撤销**，你想再 push 一次也行，但**不要试图 push 第二次**（PAT 暴露一次即可，不要增加攻击面）
- **不修改 `Cargo.lock`**——prompt 原始要求。如果 cargo 自动更新了它，commit 前 `git checkout HEAD -- Cargo.lock`
- **不新建 worktree**——worktree 已存在（shell）和主 checkout（App Hub）已切到目标分支
- **不重置或清理运行时/构建缓存**
- **不修改 DailyFlow / 任何产品代码 / bundle / ledger**——只动上游仓
- **不 commit `D:/Life/AgenticApp/OctoSense/.sources/` 下的任何东西**——`.sources` 是 git 忽略的依赖目录
- 保留原 commit (`232dcb53` / `432bedb`)**不** amend；review 反馈以新 commit 追加
- 试 push 走 `GIT_TERMINAL_PROMPT=0`，直连 22s 超时用 `HTTPS_PROXY=http://127.0.0.1:7890`（但**这次不需要 push**）

## 预算与时间

- 约 2-3 小时全做完
- 10 条改动里 #532.1（install 回归）和 #222.1（namespace collision）是最难的，先做这两个、跑测试确认能编译，再做其它
- 如果某条改动跑编译 1 分钟还没过，先 `cargo check` 一次确认是源码问题还是依赖问题
- 跑全套测试超过 5 分钟还没完，**记录已通过的子集**而不是等到全跑完

## 输出给用户的清单（必做）

1. 上面 6 个产出文件全部在 `D:/Life/AgenticApp/DailyFlow/build/upstream-bridge-review-r1/`
2. 每个 PR 的 commit SHA 短码（7 位）
3. 每个 PR 的 commit message 全文（用户 review 用）
4. 一句话总结每个 PR 现在的状态
5. **任何没解决的歧义**——比如评审员说"refuse admission or map to _"你选了后者但不确定对，写在 `open-questions.md`
6. 验证命令实际跑过的退出码（不是"应该通过"）

完事写一个简短的 handoff（≤ 80 行），贴在 chat 里。
