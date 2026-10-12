# 2026-10-12 全最新运行时回归

状态：**本轮验收完成（2026-10-12 傍晚）**。新版 Shell 完整构建成功（shell-build-r7，exit0），no-consent、official、model、relations 四阶段全部通过；证据与保留的失败轮次见下。仍不构成公开安装可用声明：两项官方发布门槛未通过（见"未通过的官方构建门槛"），且 Shell 依赖含本地补丁（rinx 目录移除 palpo 条目，见"本地补丁"）。

## 最终结果（2026-10-12 傍晚，shell-build-r7）

- Shell 构建：`cargo build --release -p octosense`，r7 轮 28m34s 完成（前段 r5 -j1 编 151 包，用户释放内存后 r6/r7 提速 -j2）。exe 527,915,008 字节，SHA256 `9e239ef354257c7b09ab88a18ce4ec7cb00ee80160a25bf1ef86f7206b7bb812`。r6 失败（rinx 构建脚本拒绝 palpo 应用）与 r5 主动中止均保留记录。
- 全组件清单 `../../build/latest-runtime-20261012-r1/runtime-all.json`：hub `fa3e50f2…`、card-host `62304027…`（首卡补丁）、shell `9e239ef3…`、kernel `561831b6…`（octos 2.0.3-rc.13 c2e1c575）。各源码树 HEAD 与本地差异补丁存 `provenance/all/`。
- `../build/latest-20261012-no-consent-r1/report.json`：全新 home 未授权 5/5（明确拒绝文案、零工具、零回执、零业务写入、未产生授权）。未自动批准。
- `../build/latest-20261012-official-r1/`：真实官方 Agent 两故事四轮全过（4 个不同 turn_id、读取工具审计、实际取消无迟到落盘、源业务零写入，73.4s）。
- `../build/latest-20261012-model-r5/`：真实 model.complete 备用路径两故事全过（207.6s）。r1–r4 失败轮次保留：r1/r4 演出故事自由文本未过引用核验、r2/r3 攀岩故事整理超时——应用按设计拒绝并保留原始记录，属既有模型输出波动类别，非运行时回归（同测试历史轮次亦需多次尝试）。
- `../build/latest-20261012-relations-r1/`：以本轮 official 真实回传输出回放关联 UI，宽屏 13.7s、窄屏 11.3s 全过。
- 三阶段 cleanup 均确认：测试宿主已退出、原 Provider 配置未变、既有人类授权未变。生产 bundle 字节未变（main.splash `d497f4ef…`）。
- 本轮截图已查看：official 两故事结果、model-r5 演出结果、relations 宽屏概览。
- 启动入口 `run-dailyflow-latest.cmd` 已更新为本组合。

## 本地补丁（本轮新增，须随报告披露）

`../../build/latest-runtime-20261012-r1/patches/rinx-f42df668-drop-palpo-catalog.md`：Rinx 主线 f42df668 内置应用 im.palpo.operations 的清单要求 4 个 palpo-* 宿主特性，这些特性只存在于 App Hub 未合并分支 feat/palpo-miniapp-contract；2026-10-12 16:40 联网复核 App Hub main 仍为 38635915、Rinx main 仍为 f42df668，冲突为当前上游最新组合固有。本地副本仅移除 system-apps.json 的 palpo 目录条目（Palpo 操作小程序不嵌入本构建；article-editor 保留），Shell Cargo.toml 以 [patch] 把 Rinx 来源全部 8 个包重定向到该副本，契约保持 App Hub 1.12.0 不变。待上游合并后应回退本补丁。

## 过程记录（2026-10-12 上午，停止前）

## 版本与证据

北京时间 2026-10-12 10:11:46 联网核对主线；23 个直接 Git 来源记录在 `../../build/latest-runtime-20261012-r1/upstream.json`。长时间构建使用这个固定快照。

| 组件 | 提交 |
|---|---|
| Shell | f07541348ee5364557429d2ff764692835a340ff |
| App Hub/card-host | 386359153ed6377b5f047bd9ed2767a6a2ac2bc7 |
| Makepad | 10f1102f65cf5d6f26511e61d9686e8391b1fcb2 |
| OctoScript | b57c726dacfa416d2b95578784a0ee0d82ba2e35 |
| OctoScript-Makepad | 6cf2d90aa33ff4ae603f49c7557f3ecf986207f0 |
| App Flow | 15b1da01a769a770aaf12bd3012d17c6ff267b6c |
| Octos 内核 | c2e1c575f589d22e2c5cf53ff11e570b794d951e |

原工作区已拉取更新，既有暂存改动及 Windows 渲染修复保留。隔离构建目录为 `../../build/latest-runtime-20261012-r1/`。官方 Shell 锁定的若干依赖落后于各仓库主线；本轮按用户要求调整到主线，保留官方 Makepad overlay，不能称未经修改的官方发行包。已合入 Makepad 的 launch-input-hardening 不重复应用。历史 nix OHOS vendored 引用仅为兼容源码位置，不是实际运行的旧内核。

测试运行必须显式指定 `DAILYFLOW_RUNTIME_MANIFEST`。`runtime-hub.json` 仅含已构建的 Hub/card-host；其余组件缺失时拒绝启动，不回退旧二进制。报告记录实际路径、SHA256、来源及补丁。

生产应用保持不变：main.splash SHA256 `d497f4efe2759540a8b256f82ce625b255b47215809ea173a9a2f3170e767859`，bundle BLAKE3 `79f5eed0c4f5eb9363df375767d46e85ceba3b2a1cbee995620fb7edbbd42a48`。

## 已完成

所有下述 DailyFlow 证据均在 `../build/`；没有复用历史成功报告。

- `latest-20261012-offline-r1/report.json`：8 套离线数据回归通过。
- `latest-20261012-unpatched-admission-r2/result.json`：最新未修改 card-host 实际拒绝应用，原因 `app_tools.dispatch@1`。
- `latest-20261012-patched-admission-r2/result.json`：应用既有首卡 ABI 注册补丁后实际就绪。补丁与未修改二进制均保留；18 个 card-host 单元测试通过。
- `latest-20261012-native-r1/report.json`：旧 5 套 GUI、经历契约 20、peer 契约 46、推理契约 32、宽屏 15、窄屏 15、费用 10 项全部通过。契约用注入输出，不作为真实 Agent/Provider 证据。
- 已查看新版实际宽窄界面和来源详情截图；窄屏长标题仍会截断，不宣称视觉完美。13 份 cleanup 回执确认本轮界面宿主已退出；生产 bundle 未变。
- `../../build/latest-runtime-20261012-r1/runtime-selection-checks/report.json`：显式路径及摘要保护 4 项通过。
- 最新内核 release 构建 exit0（64m49s）。实际版本 `octos 2.0.3-rc.13 (c2e1c575)`，SHA256 `561831b6d7659e144e6776389a49a9ddb40c27f7a360ba99b7e7151a6124636e`，证据 `../../build/latest-runtime-20261012-r1/kernel-version.json`。保留上游编译警告。

准入探针 r2 只匹配实际 Label/Button/TextInput 中的精确就绪或拒绝文案；早期探针可能匹配脚本文本，保留作为调试记录，不作为最终准入证据。

## 未通过的官方构建门槛

1. `native-apps-check.log`：最新 Rinx 主线 f42df668 未满足官方仅允许标签版本的规则。未改检查器强行通过。
2. `setup-latest-check.log`：官方 setup 的固定依赖检查要求旧 pin，遇到保留的新版 Makepad overlay 暂存改动拒绝继续。未清理或重置修复来迎合检查。

功能测试与这两项发布门槛分别记录。即使后续真实 Agent 成功，仍不能声称这一主线组合通过官方发布流程。

## 待完成

全部于 2026-10-12 傍晚完成（证据见"最终结果"）：

- ~~新 Shell release 编译、全组件摘要清单。~~ → shell-build-r7 exit0，`runtime-all.json`。
- ~~新宿主真实官方 Agent 两故事四轮：读取工具、结构化回传、终态回执、取消及零业务写入。~~ → latest-20261012-official-r1。
- ~~新宿主真实 model.complete 备用路径。~~ → latest-20261012-model-r5（r1–r4 失败保留）。
- ~~从本轮真实回传结果运行关联 UI 宽窄屏回归。~~ → latest-20261012-relations-r1。
- ~~新隔离 home 未授权时明确拒绝且不执行工具；不自动点击授权。~~ → latest-20261012-no-consent-r1。
- ~~更新最终结论和启动入口。~~ → 本文件与 run-dailyflow-latest.cmd 已更新。

本轮不提交、推送、发布标签、App Hub 入库或比赛提交；不把本地 catalog 加载称为公共安装链完成。

## 接续执行

先检查 `../../build/latest-runtime-20261012-r1/shell-build-r4-process.json` 的 exit_code，以及实际 Shell 文件是否存在。仍在运行时等待，不启动另一份 Cargo；若构建失败，先定位日志，不借旧二进制继续。内核已构建，无需重建。

在 `D:\Life\AgenticApp` 的 PowerShell 中，新 Shell 构建成功后执行：

```powershell
$taskPython = 'C:/Users/44231/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$taskRuntime = 'D:/Life/AgenticApp/build/latest-runtime-20261012-r1'
& $taskPython -X utf8 "$taskRuntime/make_manifest.py" --phase all
$env:DAILYFLOW_RUNTIME_MANIFEST = "$taskRuntime/runtime-all.json"
$taskCore = 'D:/Life/AgenticApp/DailyFlow/.local-state/semifinal-rc2-agent-r2/core'
$taskConsent = 'D:/Life/AgenticApp/DailyFlow/.local-state/semifinal-rc2-agent-r2/home'
& $taskPython -X utf8 DailyFlow/tools/test_experience_no_consent.py --core-dir $taskCore --output DailyFlow/build/latest-20261012-no-consent-r1
& $taskPython -X utf8 DailyFlow/tools/run_latest_acceptance.py --runtime-manifest $env:DAILYFLOW_RUNTIME_MANIFEST --phase official --core-dir $taskCore --consent-home $taskConsent --output DailyFlow/build/latest-20261012-official-r1
& $taskPython -X utf8 DailyFlow/tools/run_latest_acceptance.py --runtime-manifest $env:DAILYFLOW_RUNTIME_MANIFEST --phase model --core-dir $taskCore --output DailyFlow/build/latest-20261012-model-r1
& $taskPython -X utf8 DailyFlow/tools/run_latest_acceptance.py --runtime-manifest $env:DAILYFLOW_RUNTIME_MANIFEST --phase relations --recorded-output DailyFlow/build/latest-20261012-official-r1/official/apps/dailyflow --output DailyFlow/build/latest-20261012-relations-r1
```

这是待执行命令清单，不是通过证据。每条完成后先检查退出码及报告；关联回放依赖本轮 official 成功。已有输出目录必须保留，重试用新编号。`semifinal-rc2-agent-r2` 这里只提供既有 Provider 配置与原地的人类授权，实际执行内核必须来自新 manifest，绝非 RC2 exe。禁止自动授权，禁止在报告中输出 Provider 机密。

最后检查真实工具审计、四个不同 turn_id、取消后无迟到落盘、源业务零写入、cleanup 的原 Provider/授权未变和进程退出；查看本轮截图，再更新报告与启动入口。官方发布检查的两项失败须继续独立披露。
