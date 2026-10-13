# 上游贡献准备 Agent（P）：安全跨 App 读桥 PR

你是上游贡献准备负责人。目标：把 DailyFlow 团队实现的**安全跨 App 读桥**（Shell 平台新功能）整理成一个可直接提交的 OctoSense 上游 PR——包括最小 diff 分支、功能介绍（PR 正文）和用户上传步骤。**你不执行网页上传/推送官方仓库**；最终 push 到 Fork 和开 PR 由用户人工完成。

## 背景一句话

OctoSense 官方 Shell 的跨 App 工具授权按工具名第一段解析归属（`Catalog::owner_of`），陌生命名空间落到 `os.<ns>`，导致两个第三方商店 App 无法互相调用工具；且官方没有"应用脚本后台只读另一 App 数据、可感知撤权"的 API。我们实现了 `app_tools.read / cancel / focus / watch_authorization` 四个宿主 API（带准入校验、双方 consent、身份绑定、授权纪元、结构化只读保证），已在本地全栈真实验证。本 PR 把它贡献给官方。

## 必读（开工前按序读完）

1. `D:/Life/AgenticApp/agent.md` 顶部两节（当前状态与阶段 B 最终回归）
2. `D:/Life/AgenticApp/.parallel/night-20261013/H/delivery/H/PLATFORM_GUIDE.md`（API 设计表与边界，PR 正文的素材基础；另有 zh-CN 版）
3. `D:/Life/AgenticApp/.parallel/night-20261013/H/delivery/H/BUG_NOTES.md` 中 OS-H-01 段（了解但不属于本 PR）
4. 读桥源码：`D:/Life/AgenticApp/.parallel/night-20261013/H/runtime-work/candidate/shell/crates/shell/src/host_tools/read_bridge.rs`（约 15KB，内含单元测试）

## 源码位置与已知引用足迹（已预核查）

- **上游主仓库**：`D:/Life/AgenticApp/OctoSense`，HEAD = ffd5e488 = origin/main（无本地运行时提交；开工先 `git status` 记录既有未提交内容，**不得破坏**；建议新建独立 worktree 或干净 clone 做分支）
- **读桥实现树（不是 git 仓库，是导出快照）**：`D:/Life/AgenticApp/.parallel/night-20261013/H/runtime-work/candidate/shell`
  - `crates/shell/src/host_tools/read_bridge.rs` —— 新文件（上游 ffd5e488 无此文件，已核实）
  - `crates/shell/src/host_tools/mod.rs` —— 两处引用：`pub mod read_bridge;`（约 754 行）与 poll 调用 `{ script_apps::poll(); read_bridge::poll(); }`（约 126 行）
  - `crates/shell/src/apps.rs` —— 一处注册：`crate::host_tools::read_bridge::register();`（约 395 行，在 app-hub feature 路径内）
- **H 交付的 base/new 文件对照**：`D:/Life/AgenticApp/.parallel/night-20261013/H/delivery/H/platform/shell/{base,new}/crates/shell/src/host_tools/{installed_owner,mod,relay,script_apps}.rs`

## PR 范围

本贡献横跨**两个官方仓库**，各开一个 PR：

**PR-1（OctoSense 仓库，分支 `host-tools-cross-app-read-bridge`）**：读桥本体 + 使其编译/注册所需的最小修改。已核实的完整文件集（最终构建树 vs 上游 ffd5e488 的真实差异）：
- 新增：`crates/shell/src/host_tools/{read_bridge,activation,input_origin,installed_owner}.rs`
- 修改：`crates/shell/src/host_tools/{mod,relay,script_apps}.rs`、`crates/shell/src/apps.rs`（注册）、`crates/shell/src/approvals/mod.rs`（新增 `consent_epoch()` 访问器）
- 其中 `input_origin.rs`（内核 peer/input occurrence id → 原始系统 turn 的映射）与 `activation.rs`（准入激活队列）是系统入口链的配套，若与读桥耦合则并入本 PR，独立性强也可拆出并在 handoff 说明。
- 用 `cargo check -p octosense-shell --features app-hub` 验证；参照 H 交付 base/new 对照（`platform/shell/`）确认没有多拿 hunk。

**PR-2（OctoSense-App-Hub 仓库，分支 `app-contract-cross-app-tools`）**：Hub 合约与 card-host 侧配套。已核实的文件集（`.sources/app-hub` 树 vs 官方 38635915）：
- `crates/app-contract/src/manifest.rs`：已知 requires 清单加 `cross-app-read-v1`、已知 capabilities 清单加 `app_tools`（注释明确"声明不授予执行"）；**另含一个独立官方缺陷修复：工具命名空间 `short_id(app_id).replace('-', "")` 连字符剥离**（hyphenated app id 的工具归属错位）——若评审认为应拆分，此修复单独成 PR-3。
- `crates/appstore/src/script_tools.rs`：`Invocation` 元数据（origin_turn_id 等系统入口绑定）、`is_running`、扩展 submit 入口。
- `crates/card-host/src/host.rs`：首卡 ABI 预注册（已有 PR 草稿 `DailyFlow/docs/UPSTREAM_PR_DRAFT_cardhost_first_card.md` 与 `build/upstream-pr/` 可直接复用）。
- 验证：`cargo check` + `cargo test -p octosense-app-policy`（或对应 crate 名）里 manifest 校验相关测试。

**绝不包含**：DailyFlow/DailyFlowLedger 任何业务代码；OS-H-01（lib.rs）与 OS-H-06（contained.rs）——用户已提交官方等合并；Cargo.toml/Cargo.lock/native-apps.json 的本地依赖重定向（Rinx/palpo 已有 App-Hub #218）；Makepad/D3D11 修复；matrix/filmcraft 本地叠加；kernel (octos) 侧 overlay（另行专项审计）。

## PR 正文（功能介绍）必须覆盖

英文为主（上游文档为英文），结构建议：

1. **Problem**：第三方↔第三方工具归属解析失效（`owner_of` 的 `os.<ns>` 兜底）；无只读跨 App 读取面；无撤权/纪元语义。附最小复现描述（可参考 BUG_NOTES 的写法，但不要引用 DailyFlow 私有路径）。
2. **Proposal**：四个 `app_tools.*` API 的表格（输入/结果/边界——直接改写 PLATFORM_GUIDE 的表，去掉 DailyFlow 语境）；安全模型：双方 admitted + 双方 consent + `agent.tools` asks 声明匹配（owner 侧 risk=read + shareable）+ Authority 快照（账号/consent epoch/manifests）+ `READ_ONLY_REQUIRED` 结构化拒绝写 + 授予纪元失配即 REVOKED + 分页跨纪元检测。
3. **Boundaries**（诚实披露）：Windows-only v1（`with_platforms(&["windows"])`）；16 并发 read/watch 上限；45 秒服务期限、20 秒下游工具期限；focus 只激活调用方自身且需当前人工 consent；watch 为至多 30 秒租约、由 poll 复查。
4. **Testing**：`read_bridge.rs` 内单元测试（准入/身份/错误路径）+ 本地全栈真实证据摘要（两个独立 App 的真实读/写拒绝/错主拒绝/撤权隐藏/更正同步，注明"在本地修补运行时上验证，哈希与日志可提供"）。
5. **Out of scope**：OS-H-01/06 另行 PR；非 Windows 平台注册后续。

## 执行步骤

1. 记录基线：上游 repo 状态、read_bridge.rs 与相关文件 SHA256。
2. 在干净 worktree/clone 上从官方 main 建分支（建议名 `host-tools-cross-app-read-bridge`）。
3. 提取最小 diff（按"PR 范围"）；`cargo check -p octosense-shell --features app-hub` 通过；再跑 `cargo test -p octosense-shell --lib --features app-hub`（至少 read_bridge 相关测试；全量失败要逐项判断是否与本改动相关，不相关的不阻塞并在交接中注明）。
4. 写 PR 标题 + 正文（`pr-title.txt`、`pr-body.md`）。
5. 写用户上传步骤（`upload-steps.md`）：Fork 官方仓库（账号 KumaYuriPool，官方仓库 pull:true/push:false **禁止直推/强推官方 main**）→ push 分支到 Fork → 网页开 PR（base=官方 main，compare=Fork 分支）→ 粘贴正文。若用 gh CLI 辅助，只对 Fork 操作。
6. 全部产出写入 `D:/Life/AgenticApp/DailyFlow/build/upstream-bridge-pr-r1/`，含 `handoff.md`（做了什么/没做什么/下一步）与 `summary.json`（文件清单+哈希+验证命令与退出码）。

## 硬约束

- 不推送、不打 tag、不开 Issue/PR、不发布——一切外发由用户执行。
- 不修改 `OctoSense-App-Hub` 的 Cargo.lock、Makepad 的 `d3d11.rs` 修复、任何 DailyFlow 生产源码/bundle/账本数据、`.parallel` 下各角色交付（只读引用）。
- 不 reset/清理任何运行时或构建缓存；不长时间占用构建资源（如需 release 级构建先在 handoff 里说明理由）。
- 网络如需 git 操作：先试直连；失败再显式 `export HTTPS_PROXY=http://127.0.0.1:7890`（该代理时活时死，两种都试过再下结论）。
- 遇到与本 prompt 冲突的既有文档，以本 prompt 为准并在 handoff 里记录冲突点。
- 预算：约 2-3 小时。cargo 全量测试若超时，跑定向测试并如实记录未跑项。

完成后输出：分支名、commit 哈希、验证结果、`upload-steps.md` 路径，以及任何未决问题（尤其 owner_for 依赖判断的结论）。
