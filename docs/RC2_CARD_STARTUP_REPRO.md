# RC2 第一个第三方 Card 的 script-tools-v1 准入顺序问题（报告草稿）

状态：2026-10-10 本地复现，尚未向上游提交。标题建议：`RC2: first third-party script-tools-v1 app is gated before Card registers app_tools.dispatch`。

## 环境与范围

- Windows 官方 `desktop-v0.1.0-rc.2` 安装器，189331055 bytes，SHA256 `628a68a0d9e5fa615ca01d3a6e3ff2bbd2ccd02cf71ec6acbd9e28a652c58e00` 与官方清单吻合；7-Zip 隔离解包，未运行安装器。
- 使用发行包原始 `octosense.exe` 及配套 kernel，没有修改运行器、禁用完整性校验或自动批准权限。
- Shell 源码固定 `4ccf8e068399b1da139771a9ed94cef05fa6ae60`，其 App Hub 固定 `95e4831afca7227b640f075b252c04355bb63865`。
- DailyFlow 0.1.1 包含 `tools.json`，manifest 声明 `requires: ["script-tools-v1"]`。测试 catalog 由 App Hub `655114c4943cd2490daaefa2173e7b5aaa20669f` 工具准备和验证；它与 RC2 固定版本不同，不能混称同一构建。
- 两轮 manifest 的 bundle digest 相同：`2df8d5f1e42c1c73824297c76ad55f843211290d618242c45df02910579f024d`，requires 同为 `script-tools-v1`；各轮使用独立临时签名与运行根目录。
- 全新隔离应用目录、本地临时签名 legacy catalog，明确设置 `OCTOSENSE_HUB_CATALOG=legacy`。这是本地开发准入复现，未验证 GitHub v2 发布安装路径。两轮未请求 Provider，测试进程均退出。

## 启动对照

为每轮准备独立但内容相同的合法签名 bundle/catalog，分别设置 `OCTOSENSE_HOME`、`OCTOSENSE_APP_DATA`、`OCTOS_APP_CORE_DIR` 到该轮空白隔离目录，`OCTOSENSE_HUB_ANCHOR` 为该轮临时公开根密钥；保持默认权限检查。临时私钥不属于报告附件。

对照 A，直接启动第三方应用：

```text
octosense.exe --test-action launch-hub:dailyflow
```

实际：DailyFlow 未加载，`ready:false`；日志只有 `wm: --test-action launch hub:dailyflow` 和通知 toast，没有 DailyFlow Card 源码求值。此次未取得 toast 文本，因此不把推断的 gate 错误冒充实测错误原文。

对照 B，同一未经修改的官方程序先打开官方内置 Card 应用：

```text
octosense.exe --test-action launch-calendar --test-action launch-hub:dailyflow
```

实际：`ready:true`、`ui_loaded:true`、`notices:[]`。日志依次记录：

```text
wm: launched calendar as client 1 (in-process, card)
wm: launched hub:dailyflow as client 2 (in-process, card)
```

`requires` 在成功轮保留。Calendar 使用隔离本地状态；此轮没有工具请求或 Agent 同意操作。预期行为：一个合法第三方 script-tools-v1 应用作为本进程第一个 Card 时也应能通过相同准入，而不要求用户先打开别的 Card。

## 源码链路

1. [Shell lib.rs:770](https://github.com/OctoSense-org/OctoSense/blob/4ccf8e068399b1da139771a9ed94cef05fa6ae60/crates/shell/src/lib.rs#L770) 中 `launch_app_with_args` 对非 `os.*` Card 先调用 `catalog::try_may_open_from_environment`，成功后才进入 `launch_module_as`。
2. [catalog.rs:164](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/95e4831afca7227b640f075b252c04355bb63865/crates/app-hub-app/src/catalog.rs#L164) 创建 Store 时读取当前 `host_api::available_versions()`。
3. [manifest.rs:776](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/95e4831afca7227b640f075b252c04355bb63865/crates/app-contract/src/manifest.rs#L776) 的 `check_host_apis` 对 `script-tools-v1` 要求 `app_tools.dispatch` 为版本 1。该 feature 已在 KNOWN_FEATURES 中，不是未知声明。
4. [cardapp.rs:211](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/95e4831afca7227b640f075b252c04355bb63865/crates/appstore/src/cardapp.rs#L211) 在 `CardModule::register` 中注册该能力。
5. [module_host.rs:657](https://github.com/OctoSense-org/OctoSense/blob/4ccf8e068399b1da139771a9ed94cef05fa6ae60/crates/shell/src/module_host.rs#L657) 创建模块实例时才调用 `module.register(vm)`。内置 Calendar 的 `os.calendar` 不经过第三方 catalog gate，因此可以先初始化同一 Card runner，随后第三方 gate 就能看见该能力。

这与启动对照一致：能力注册晚于第一次需要它的设备准入。单纯等待未必有用；是否已有 Card 实例才是本次对照变量。建议上游将实际已链接 Card 运行器的能力注册放到首次设备准入之前，并增加“全新进程第一个第三方 Card”的回归；不得让不具备该 ABI 的宿主虚报能力。

## 证据与未验证项

- 失败：`build/semifinal-202610/official-host/final-newhub-r2/shell-check/{result.json,desktop.log,snapshot.json}`。
- 成功：`build/semifinal-202610/official-host/final-newhub-r3/shell-check/{result.json,desktop.log,snapshot.json}`。
- 各轮 `rc2-stage-evidence.json` 记录对应本地 catalog 公钥、工具源码版本和包路径。

UI 加载和空 notice 不证明 `dailyflow.*` 已经执行。后续独立窗口的 `agent prepared` 同样不证明模型调用或工具完成。真实 Provider、自有工具读写、用户授权、GitHub 发布准入以及其他平台均不纳入本报告的已验证范围。对外提交前只附脱敏证据，不附 `.local-state`、Provider profile、会话或个人数据。
