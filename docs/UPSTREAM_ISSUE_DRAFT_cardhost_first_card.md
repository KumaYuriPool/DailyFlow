# 上游 Issue 草稿：card-host 首卡 `app_tools.dispatch@1` 时序

**状态：已于 2026-10-12 01:21 发布为 [#215](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/215)（open，发布者 KumaYuriPool，API 读回核对正文 4337 字符一致）。** 目标：[OctoSense-org/OctoSense-App-Hub](https://github.com/OctoSense-org/OctoSense-App-Hub) 的**空白 Issue**（不用 submit-app 上架模板）。语言：英文（上游工作语言；双语规则只约束仓内文档）。后续 PR 引用此 Issue 编号（已回填 PR 草稿）。

---

## Issue 标题

```
card-host refuses a script-tools-v1 bundle when it is the process's first card (app_tools.dispatch@1 registered after admission)
```

## Issue 正文（英文，拟提交）

### Summary

A legitimate third-party bundle declaring `requires: ["script-tools-v1"]` is
refused by `card-host` whenever the bundle is the process's **first** card.
Admission runs `check_manifest` → `check_host_apis(available_versions())`,
but `app_tools.dispatch@1` is only registered by `CardModule::register()` —
which no admission can have reached yet. The full shell pre-registers the same
ABI for exactly this reason; the single-app runner never got the equivalent.

### Environment

- Official `desktop-v0.1.0-rc.2` Windows installer (189,331,055 bytes, SHA256
  `628a68a0d9e5fa615ca01d3a6e3ff2bbd2ccd02cf71ec6acbd9e28a652c58e00`,
  unpacked only, never modified).
- App Hub source at `386359153ed6377b5f047bd9ed2767a6a2ac2bc7`, self-compiled
  `card-host` (cargo/rustc 1.98.1, Windows); labeled self-compiled throughout.
- Third-party app: DailyFlow 0.1.1 bundle (`requires: ["script-tools-v1"]`).

### Minimal reproduction (run by me)

```
card-host --bundle <script-tools-v1 bundle> --app-data <fresh dir> \
          --allow-unsigned --stamp --size 1280x900
```

Actual, both at `38635915` and at the earlier pin `655114c` (two runs each):
the window shows only the refusal card —

```
card-host refused this bundle
app dailyflow needs a host implementing app_tools.dispatch@1
```

Expected: a bundle the runner supports is admitted on its own, as already
happens in the full shell once any built-in card has opened first.

Control on the unmodified official RC2 binary: launching the same app as the
first card never reaches evaluation; launching a built-in card first, then the
app, succeeds (`ready:true`, empty notices). UI loading alone proves nothing
about tool execution; this report covers admission ordering only.

### Source trace

- Admission check runs in `App::mount` before any card module exists:
  [host.rs#L420](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/386359153ed6377b5f047bd9ed2767a6a2ac2bc7/crates/card-host/src/host.rs#L420)
- `app_tools.dispatch@1` is registered only at card-module registration:
  [cardapp.rs#L215](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/386359153ed6377b5f047bd9ed2767a6a2ac2bc7/crates/appstore/src/cardapp.rs#L215)
- `register_policy_runtime_features()` covers `app_policy.device_consent`
  only, so it does not fill the gap:
  [lib.rs#L474](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/386359153ed6377b5f047bd9ed2767a6a2ac2bc7/crates/appstore/src/lib.rs#L474)
- The shell's equivalent pre-registration, with the rationale in its comment:
  [apps.rs#L283](https://github.com/OctoSense-org/OctoSense/blob/9266b0083544d86bd7636543b5ff60c61b26460f/crates/shell/src/apps.rs#L283)

### Proposed fix (patch and tests ready)

`crates/card-host/src/host.rs` gains `register_linked_runtime_abis()`, called
at the top of `run()`, mirroring the shell:

```rust
fn register_linked_runtime_abis() {
    octosense_appstore::register_policy_runtime_features();
    octosense_appstore::host_api::register_runtime_feature("app_tools.dispatch", 1);
}
```

With a regression test: after pre-registration a `script-tools-v1` manifest
passes `check_manifest`, while `backend-api-v1` (known, not implemented by
this host) is still refused — admission is not widened. All run:

- `cargo test --release -p octosense-card-host`: 18/18 + 2/2 pass
- `cargo test --release -p octosense-appstore -p octosense-app-contract`: 114/114 pass
- Process level, hidden window + remote control (`MAKEPAD_HIDE_WINDOWS=1`):
  refused before / admitted after, two runs each way

**Question for maintainers**: fix locally in card-host as above, or factor a
shared helper so the shell and card-host cannot drift again? I will prepare
the PR accordingly.

### Separate small finding (not part of this fix)

The committed `Cargo.lock` at `38635915` lacks Windows-target packages
(`webview2-com`, `windows-implement`, …), so `cargo build --locked` fails on
Windows; regenerating it is additive-only (no version changes, nothing
removed). Happy to send that as its own commit if you want it.

### Evidence

Per-run `result.json` / `snapshot.json` / `runtime.log`, the patch file and
the repro script are available; binaries are not byte-reproducible across
builds, so the evidence is the verdicts plus the source diff. Nothing here
includes private data, credentials or provider profiles.

---

## 发送前核对

- [ ] 用户审核正文
- [ ] 空白 Issue，不用 submit-app.yml 模板
- [ ] 正文含"哪些跑过/哪些只是源码核对"的区分（已含：control 段标注 UI 加载不证明工具执行；Evidence 段说明证据形态）
- [ ] 不含凭据/个人数据/私有路径（已确认）
- [ ] Issue 发出后把编号回填到 [PR 草稿](UPSTREAM_PR_DRAFT_cardhost_first_card.md) 与 execution-state.json
