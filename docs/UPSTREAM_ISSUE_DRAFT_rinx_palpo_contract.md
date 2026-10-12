# 上游 Issue 草稿：Rinx 主线无法在 OctoSense Shell 中构建（palpo 契约特性未合并）

**状态：已提交。** 用户本人于 2026-10-12 19:48（北京时间）通过 App Hub "Report a problem" 表单提交为 [OctoSense-App-Hub #218](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/218)（API 回读核实：state open，labels: bug，标题 `Problem:Rinx main cannot build inside the OctoSense Shell workspace (bundled palpo app needs contract features not on main)`）。表单 Full output 字段中 `<build-dir>`/`<cargo-home>` 占位符被 GitHub 表单 sanitize 掉，仅显示反斜杠路径，不影响阅读，不补编辑。

**上游现状核查（2026-10-12 16:40 北京时间，经代理联网 `git ls-remote`）：** App Hub main 仍为 `386359153ed6377b5f047bd9ed2767a6a2ac2bc7`，Rinx main 仍为 `f42df668b8c547ecd9907f99cdc45f50c77b767d`，冲突在当前最新组合中固有存在。官方 Shell（`f0754134`，按 native-apps.json 锁定的标签版 Rinx）不受影响；仅在按用户要求选用 Rinx 主线时触发。

**本地处置（已验收，见 `../build/latest-runtime-20261012-r1/patches/rinx-f42df668-drop-palpo-catalog.md`）：** 本地副本仅移除 `system-apps.json` 的 palpo 目录条目并以 `[patch]` 重定向 Rinx 来源全部 8 个包；契约保持 App Hub 1.12.0 不变。

---

## Issue 标题

```
Rinx main cannot build inside the OctoSense Shell workspace: bundled im.palpo.operations requires contract features that only exist on feat/palpo-miniapp-contract
```

## Issue 正文（英文，拟提交）

### Summary

When the OctoSense Shell workspace pins Rinx to current main
(`f42df668b8c547ecd9907f99cdc45f50c77b767d`), `cargo build` fails in Rinx's
build script because the bundled mini-app `im.palpo.operations` declares
`requires` features that the App Hub contract on main (1.12.0) does not know.
The features exist only in Rinx's vendored contract copy, which is built from
this repo's unmerged `feat/palpo-miniapp-contract` branch — and a dependency's
own `[patch]` table does not reach a consumer workspace, so the Shell build
links the contract from App Hub main instead.

### Environment

- OctoSense Shell `f07541348ee5364557429d2ff764692835a340ff` (workspace root:
  `octosense-app-contract = "1.12"`, `[patch.crates-io]` → App Hub `38635915`)
- Rinx `f42df668b8c547ecd9907f99cdc45f50c77b767d` (`default-features = false`,
  `features = ["octosense-module"]`)
- Windows 11, rustc 1.98.1 (reproducible on any host OS; the failure is in a
  build script)

### Reproduction

1. In the Shell workspace, point the `rinx` dependency at Rinx main
   `f42df668` (instead of the tag pinned by `native-apps.json`).
2. `cargo build --release -p octosense`

### Actual result

```
error: failed to run custom build command for `rinx v1.3.0 (...Rinx.git?rev=f42df668...)`
  thread 'main' panicked at build.rs:5:49:
  validate Rinx system apps: "app im.palpo.operations needs a newer host:
  palpo-actions-room-v1, palpo-agent-navigation-v1, palpo-account-navigation-v1,
  palpo-project-room-picker-v1"
```

### Root cause

- `apps/palpo/bundle/manifest.json` in Rinx main requires five features:
  `palpo-admin-v1` plus the four above. Rinx validates its bundled catalog at
  build time via `rinx_system_apps::pack()`.
- Rinx carries a vendored `octosense-app-contract` 1.2.0
  (`vendor/octosense-app-contract`, per `RINX-PATCH.md` taken from App Hub
  branch `feat/palpo-miniapp-contract` `9854614` and follow-ups `6180376`,
  `8ff0654`, `a93073d`, `2e2ad26`, `978a28f`) whose `KNOWN_FEATURES` and
  `KNOWN_CAPABILITIES` cover the palpo grammar. Rinx's own workspace `[patch]`
  points to it, so standalone Rinx builds fine.
- `[patch]` tables are not transitive. In the Shell workspace the root
  `[patch.crates-io]` unifies `octosense-app-contract` to App Hub main's
  1.12.0, whose `KNOWN_FEATURES` has only `palpo-admin-v1`. The same delta
  exists in capabilities: 1.12.0 lacks `palpo.accounts.open`,
  `palpo.actions.room.get`, `palpo.actions.room.ensure`, `palpo.agents.control`,
  `palpo.inbox.recover`, `palpo.notifications.get`, `palpo.notifications.set`,
  `palpo.projects.select_room`, `palpo.requests.open`.
- Net effect: Rinx main is currently unbuildable for any downstream workspace
  until the palpo contract additions land on App Hub main (or a crates.io
  contract release).

### Suggested fix

Merge `feat/palpo-miniapp-contract` (or equivalent additive contract release)
into App Hub main so the published contract knows the palpo features and
capabilities, then Rinx can drop its vendored patch — which is exactly what
`vendor/octosense-app-contract/RINX-PATCH.md` already anticipates ("Remove the
root, standalone miniapp-catalog, system-apps and miniapp-package Cargo
patches when the same shared contract is published").

### Workaround we use meanwhile

In our build tree we keep a byte-identical copy of Rinx `f42df668` with a
single edit — `system-apps.json` drops the `{"directory": "palpo"}` entry — and
redirect all eight packages from the Rinx git source to that copy via the
Shell's root `[patch."https://github.com/hagency-org/Rinx.git"]`. The Palpo
operations mini-app is then simply not embedded; the contract stays at App Hub
1.12.0 and everything else is unchanged.

### Notes

- Verified 2026-10-12: App Hub main is still `38635915`, Rinx main still
  `f42df668`; the official Shell release configuration (tagged Rinx per
  `native-apps.json`) is unaffected.

---

## 提交入口与表单字段映射

入口：https://github.com/OctoSense-org/OctoSense-App-Hub/issues/new ，选择 **Report a problem**（App Hub 自身问题表单，可用中文），由用户本人点击 Submit。该表单为分段字段，按字段拆好的粘贴文本在 `../build/issue-form/`：

| 表单字段 | 粘贴文件 |
|---|---|
| Title（表单自带 `Problem: ` 前缀，替换占位即可） | 1-title.txt |
| What happened | 2-what-happened.txt |
| What you expected | 3-expected.txt |
| Steps to reproduce | 4-steps.txt |
| App Hub revision | 5-revision.txt（38635915 全 40 位） |
| Platform | 下拉选 **Windows** |
| Full output | 6-output.txt（本地路径已脱敏为 `<build-dir>`/`<cargo-home>`） |
| Anything else | 7-more.txt |

上方"Issue 标题/正文"两节为单栏版本，保留作归档；分段表单内容以 issue-form/ 为准。
