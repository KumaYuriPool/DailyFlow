# 上游 PR 草稿：card-host 首卡 `app_tools.dispatch@1` 注册时序

**状态：待用户审核，未对外提交。** 目标仓库：[OctoSense-org/OctoSense-App-Hub](https://github.com/OctoSense-org/OctoSense-App-Hub)。拟分支名：`fix/card-host-first-card-dispatch`。

**上游现状核查（2026-10-12，HEAD `38635915`）：问题仍存在，且已在新 HEAD 完成运行级复现与修复对照。** `crates/card-host/src/host.rs` 的 `App::mount` 在约 420 行执行 `octosense_appstore::host_api::check_manifest(&manifest)`（内部即 `check_host_apis(available_versions())`），而 `app_tools.dispatch@1` 仍只在 `crates/appstore/src/cardapp.rs:215` 的 `CardModule::register()` 里注册——即第一张卡实例化之后。`register_policy_runtime_features()` 现在只注册 `app_policy.device_consent`（`crates/appstore/src/lib.rs:474`），不再覆盖 dispatch。对照：OctoSense Shell 主仓 `crates/shell/src/apps.rs` 的 `register_host_services` 已在准入前显式预注册 `app_tools.dispatch@1` 并注明原因（"App Hub admits bundles before the first CardModule is opened"）。card-host 是单应用运行器，没有"先开内置 Calendar"的绕法，因此第一个第三方 script-tools-v1 卡必现拒绝。

**新 HEAD 运行证据（2026-10-12，详见 `build/upstream-pr/VERIFICATION.md`）：** 未修改构建拒绝（`card-host refused this bundle: app dailyflow needs a host implementing app_tools.dispatch@1`，两轮一致）；打补丁后同输入准入通过、应用到达就绪（两轮一致）。补丁文件 `build/upstream-pr/card-host-first-card-38635915.patch`，复现工具 `tools/repro_cardhost_first_card.py`（可随 PR 提供给 maintainer 复跑）。

---

## PR 标题

```
card-host: register the card runner's tool ABI before first-card admission
```

## PR 正文（英文，拟提交）

### Summary

`card-host` refuses a legitimate third-party `script-tools-v1` bundle when that
bundle is the first card in the process: admission runs
`check_manifest` → `check_host_apis(available_versions())`, but
`app_tools.dispatch@1` is only registered by `CardModule::register()` —
which no admission can have reached yet. The full shell already pre-registers
the same ABI in `register_host_services` for exactly this reason; the
single-app runner never got the equivalent.

### Root cause

- `crates/card-host/src/host.rs` (`App::mount`): `check_manifest` runs before
  any card module exists.
- `crates/appstore/src/cardapp.rs`: `register_runtime_feature("app_tools.dispatch", 1)`
  lives in `CardModule::register()`, i.e. after admission.
- `register_policy_runtime_features()` covers `app_policy.device_consent` only,
  so it does not fill the gap.

Net effect: a fresh `card-host --bundle <script-tools-v1 app>` refuses its own
supported ABI with `app dailyflow needs a host implementing app_tools.dispatch@1`
(reproduced with a third-party app on `655114c`; code path unchanged at
`38635915`).

### Fix

`crates/card-host/src/host.rs` gains a small helper that `run()` calls before
anything else, mirroring the shell:

```rust
/// The ABI the linked card runner implements, registered before admission.
/// Otherwise `app_tools.dispatch@1` appears only when the first CardModule
/// registers — after admission — so a script-tools-v1 bundle that is this
/// process's first card would be refused by its own runner. Mirrors the
/// shell's register_host_services; check_manifest still enforces every
/// requirement.
fn register_linked_runtime_abis() {
    octosense_appstore::register_policy_runtime_features();
    octosense_appstore::host_api::register_runtime_feature("app_tools.dispatch", 1);
}

pub fn run(args: Args) {
    register_linked_runtime_abis();
    let _ = ARGS.set(args);
    app_main();
}
```

plus a regression test (`first_card_admission_finds_the_card_runners_abi`):
after the pre-registration, a `script-tools-v1` manifest passes
`check_manifest`, while `backend-api-v1` — known but not implemented by this
host — is still refused, proving admission is not widened.

No check is relaxed: `check_manifest` runs unchanged, and hosts that do not
link the card runner still cannot advertise the ABI. Not app-specific.

### Test plan

- New regression test in `crates/card-host/src/host.rs` (above);
  `cargo test --release -p octosense-card-host` → 18/18 + 2/2 pass.
- Existing: `cargo test --release -p octosense-appstore -p octosense-app-contract`
  → 114/114 pass at the PR base with the patch applied.
- Process level: `repro_cardhost_first_card.py` launches the built binary with
  a `script-tools-v1` bundle in a fresh data root — refused before the patch,
  admitted after (two runs each).
- Note: at `38635915` the committed `Cargo.lock` is missing Windows-target
  packages (webview2-com, windows-implement, …), so `cargo build --locked`
  fails on Windows before reaching this issue; the lock regenerates cleanly
  with additive-only entries. Worth a separate lockfile refresh commit or a
  mention in this PR.

### Evidence

- **At the PR base (`38635915`, self-compiled, Windows)**: unmodified build
  refuses the bundle as the process's first card — visible refusal card reads
  `card-host refused this bundle / app dailyflow needs a host implementing
  app_tools.dispatch@1` (two runs); with the two-line patch, the same
  production bundle is admitted and reaches readiness (two runs). Repro script
  (`repro_cardhost_first_card.py`, hidden window + remote control), per-run
  `result.json`/`snapshot.json`/`runtime.log` and the patch file available;
  binaries are not byte-reproducible across builds, so the verdicts and the
  source diff are the evidence.
- Reproduction on official `desktop-v0.1.0-rc.2` (installer SHA256
  `628a68a0…`, unpacked only): a third-party `script-tools-v1` app as the
  first card never reaches evaluation; the same binary loads it after any
  built-in card opened first. Same root cause, shell side; full write-up
  available on request.
- Earlier pin `655114c`: same before/after behavior (refusal text → admitted,
  16 UI assertions pass after the fix).

### Notes for reviewers

- Discussion and reproduction report: #215.
- Mirrors `crates/shell/src/apps.rs` (`register_host_services`) in the main
  OctoSense repo; consider whether a shared helper should own this list so the
  two hosts cannot drift again.
- We found this while qualifying our app (DailyFlow) for the semifinal; happy
  to adjust scope or tests to your conventions.

## 提交前自检清单（按上游 AGENTS.md）

技术与证据项（已完成）：

- [x] 在新 HEAD `38635915` 重新编译并复现"修改前失败→修改后成功"（build/upstream-pr/VERIFICATION.md，两轮对照＋重构后复验 admitted）
- [x] 补上回归测试 `first_card_admission_finds_the_card_runners_abi`（含"未实现能力仍拒绝"的反向断言）
- [x] 按 App Hub AGENTS"改动↔验证"对照表执行：`cargo test --release -p octosense-card-host` 覆盖 `--bin card-host`（18/18）与 `--test cli`（2/2）；`-p octosense-appstore -p octosense-app-contract` 114/114；Windows 下 `--locked` 因上游 lock 缺项不可用，已在正文注明而非顺手改 lock
- [x] 未改 pins、未提交重新生成的 Cargo.lock（遵守"文档/fix 不动钉版"规则；lock 缺项仅在正文注明）
- [x] UI 自动化符合规范：`MAKEPAD_HIDE_WINDOWS=1`＋独立 `MAKEPAD_REMOTE` 端口＋独立 app-data，只退出自己启动的实例（tools/repro_cardhost_first_card.py）
- [x] 补丁保持契约兼容与拒绝行为：只预注册 ABI，未把描述性声明变成执行门，未放松 `check_manifest`
- [x] 证据脱敏：不含 `.local-state`、Provider profile、个人数据

对外动作项（待用户审核授权后执行）：

- [x] 先开**空白 Issue**（不用 submit-app 模板）：已发布为 [#215](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/215)（2026-10-12 01:21，API 读回核对一致），含 RC2 复现＋新 HEAD 对照＋修法偏好询问＋Windows lock 缺项
- [ ] 等 maintainer 回应；若倾向共享 helper，按其方向改完再提 PR
- [ ] fork → 分支 `fix/card-host-first-card-dispatch` → 单 PR 单一改动，正文已含 `Discussion: #215`（见 Notes for reviewers）
- [ ] commit 用公开 GitHub noreply 身份；先检查 `git config user.email`
