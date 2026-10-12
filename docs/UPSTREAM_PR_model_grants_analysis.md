# 上游分析：模型服务清单路径修复——已被上游取代，不建议提 PR

**状态：待用户审核；结论是不提交。** 目标仓库：[OctoSense-org/OctoSense](https://github.com/OctoSense-org/OctoSense)。

## 我们的本地修复（2026-10-06，仅自编译留存）

当时官方 RC2（Shell 源码 `4ccf8e0`）下 DailyFlow 模型调用被拒：`capability: This app was not granted the model capability.` 根因是 App Hub 已把安装位置迁到 `<apps>/.bundles/<id>/bundle/manifest.json`，而 `apps/ai-providers/host-service/src/complete/mod.rs::manifest_grants` 仍只查旧路径 `<apps>/<id>/bundle/manifest.json` 和 `.system`。本地补丁改为优先读当前安装的 `.bundles` 清单、拒绝旧副本提权，配 19 项集成测试与真实 Provider 记账/更正/查询证据（`build/model-permission-fix-20261006/`）。该补丁只服务于我们本机固定的 RC2 工具链，从未提交。

## 上游新 HEAD（`9266b008`）核查结论

**该缺陷已不存在，且机制整体重写，我们的补丁没有可移植对象：**

1. `complete/mod.rs` 里 `manifest_grants` 已消失；授权改为注入式回调 `Grants = Fn(&str app_id, &Path host_dir) -> bool`，默认拒绝（`apps/ai-providers/host-service/src/complete/mod.rs:396-437`）。
2. Shell 在 `crates/shell/src/apps.rs:228` 装配该回调：`set_model_grants(|app, host_dir| script_apps::admitted_host(app, host_dir).is_ok())`。
3. `admitted_host` → `admitted_bundle` → `host_tools/admission.rs::installed_bundle`：通过**带锚点验证的 App Hub Store**（`accept_catalog` → `may_run` → `install_dir`）解析当前安装位置，不再有任何硬编码路径查找；同时校验 host_dir 归属与 manifest id 一致性。

这比我们补丁的语义更强（验签目录＋身份绑定，而非仅换路径），上游还加了注释明确"manifest declaration alone is never proof of identity"。

## 建议动作

- **不提 PR、不开 Issue**：main 已修，重复报告只会增加 maintainer 噪音。
- 本地 `octosense-model-fix.exe` 继续作为 RC2 固定工具链的过渡运行时；一旦官方发布基于新 main 的 RC3/正式版，应重测模型链并退役该补丁。
- 若未来官方从旧基线切 RC3 而不含此重构，再考虑把复现（`capability: not granted`＋路径分析）作为 Issue 提交；目前没有迹象需要。
- 在 DF-22 发布材料的"宿主要求"里注明：DailyFlow 0.1.1 的模型能力在 RC2 上依赖上述本地补丁或等效修复，新版 main 不受影响——避免评审在旧 RC2 上复现失败。

## 核查记录

- `git rev-parse HEAD` = `9266b0083544d86bd7636543b5ff60c61b26460f`（2026-10-11 用户更新后）
- 关键文件：`apps/ai-providers/host-service/src/complete/mod.rs`、`crates/ai-host/src/lib.rs:373-437`、`crates/shell/src/apps.rs:222-235`、`crates/shell/src/host_tools/script_apps.rs:225-246`、`crates/shell/src/host_tools/admission.rs:26-50`
- 性质：静态源码核查；未在新 HEAD 编译运行模型链（如需可另安排真实 Provider 复测）
