# 官方宿主工具接入与验收

更新：2026-10-10。此页区分源码核对、应用桥接测试和官方发行包实测，避免把已有本地补丁宿主当成官方发布证据。比赛截止以[四天计划](SEMIFINAL_PLAN.md)为准。

## 固定版本与接口结论

目标版本为 OctoSense `desktop-v0.1.0-rc.2`，源码 `4ccf8e068399b1da139771a9ed94cef05fa6ae60`，对应 App Hub `95e4831afca7227b640f075b252c04355bb63865`。运行器源码只调用 `app_tool(name, call_id)`，没有对 DailyFlow 原有 `on_agent_tool(token, name, args_json)` 的自动兼容分支；注册模块仅有 `request`、`active`、`complete`、`fail`，没有旧 `resolve`/`reject`。

依据：[固定 App Hub 工具实现](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/95e4831afca7227b640f075b252c04355bb63865/crates/appstore/src/script_tools.rs)、[RC2 ABI 说明](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/docs/adr/0012-app-host-api-discovery.zh-CN.md)、[官方示例](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/tools/fixtures/host-api-lab/bundle/main.splash)。

## 应用侧最小修改

[40_coordinator.splash](../src/40_coordinator.splash)增加 RC2 入口并保留旧入口：

1. 官方回调接收工具名和宿主调用 ID，进入原有短队列。
2. 真正执行前调用 `active(call_id)`，排队期间已取消或过期则不执行业务。
3. 使用 `request(call_id).args` 获取宿主参数；不从模型消息重新生成参数，不读取或伪造调用方身份。
4. 新旧入口复用同一个业务分发和事务实现。参数的 JSON 编解码仅用于兼容既有分发签名。
5. 官方入口使用 `complete` 返回结构化业务结果、`fail` 返回桥接/未知工具失败；业务拒绝仍通过结果中的 `ok:false` 表达。不能把传输成功当业务成功。

此修改不扩大 shareable 权限，不新增跨 App 授权，不改变风险声明、交易语义、持久化或官方确认。正在执行或已完成的同步写入不承诺可被后续取消撤回。清单已声明必需的 `script-tools-v1`；旧VM回归只在显式标注的隔离测试副本中移除此项，不能代表生产包准入。

## 可重复的应用桥接测试

[test_official_tool_bridge.py](../tools/test_official_tool_bridge.py)在新隔离目录从当前 `src` 构建副本，注入 RC2 调用 API，然后由已有隐藏 card-host 的真实 Splash VM 执行业务。默认仅准备，不启动；只有 `--run` 启动隔离宿主，并在结束后退出。无需 Provider。

```powershell
python tools/test_official_tool_bridge.py --output build/semifinal-202610/official-host/bridge-new --run
```

输出目录必须尚不存在。测试涵盖：调用参数进入真实保存事务、独立查询读回、每次调用一次结果、取消后不开始执行、宿主请求缺失、未知工具、重复写入幂等、过期修订拒绝、只读空查询与参数错误。

2026-10-10 运行记录：`build/semifinal-202610/official-host/bridge-r2/report.json` 中 8 个隔离场景、10 项断言通过，8 个测试宿主均退出。首轮 `bridge-r1` 夹具使用旧 VM 不支持的字符串方法而失败，日志保留；改为简单字段匹配后通过，生产桥接未因这一夹具问题改业务逻辑。Python 编译与专属文件 `git diff --check` 通过。

这是**应用桥的真实 VM 测试，但 RC2 宿主 API 被注入**。它不能证明实际官方队列、安装准入、审批界面、应用 peer、真实模型、关闭应用行为或 RC2 Windows 渲染已通过。不得使用其成功结果替代下面的官方验收。

## 官方发行包验收清单

使用合成数据与隔离数据根目录；不修改个人 Provider 配置，不自动批准用户授权。状态随实际证据更新。

| 层次 | 具体步骤与通过条件 | 状态 |
| --- | --- | --- |
| 版本与来源 | 官方发行物 SHA256 对照发布清单；记录实际 exe、版本、启动参数和应用包摘要 | 官方 Windows 安装器摘要通过；见下方记录 |
| 启动与准入 | 目标 bundle 被官方运行器接受，完整应用打开，控件可见可操作，无 ABI/语法错误 | 补 requires 后，先启动官方 Calendar 再启动 DailyFlow：ready:true、notices:[]、UI 加载；仅本地 legacy catalog。工具执行、交互与正式发布准入仍待验证 |
| 自有只读工具 | 对真实宿主工具队列调用 `dailyflow.capabilities`、`dailyflow.query`，结果符合 schema | 实际官方peer审计两项allowed/ok；返回正文与数量仍待核对 |
| 官方 Agent 委派 | 系统助手发现应用，按实际返回的标识委派给已获用户允许的应用 Agent | 待验证 |
| 拒绝授权 | 用户拒绝写入批准后不改变源记录/修订；不能由自动点击替代用户批准 | 本次通过：01:21:25审计denied/not_called，未见重试，隔离业务文件与前态一致 |
| 批准、执行、读回 | 用户批准合成账目写入后查询到真实 ID、金额和来源，未来计划不计入已发生费用 | 批准写入及query读回通过，落盘r2/12000分/1条expense；未来计划排除尚待该场景验证 |
| 更正与重查 | 同源更正 120→100，旧修订拒绝，查询与 UI 一致；重启后仍一致 | 更正与工具读回通过：r2/100元/revision3/expense数1；整宿主重启后精确ID/expense查询通过；旧修订拒绝与UI仍待该官方场景验证 |
| 关闭/取消 | 关闭应用可见 `app_not_running`，取消/超时诚实返回；不宣称冷启动或自动回滚 | 待验证 |
| 缺失状态 | 无数据、无模型配置/服务失败时不伪造结果，不声称已完成任务 | 待验证 |
| 发布物一致 | 从确切新标签导出的正式 bundle 重复必要验收，材料注明平台与边界 | 待验证 |

直接注入队列或 card-host CLI 只能计自有工具层；官方 Agent 委派必须有真实 peer/模型链证据。包检查不等于 UI 验收，更不等于发布与提交完成。

集成负责人记录：Windows 官方 installer 大小 `189331055` bytes，SHA256 `628a68a0d9e5fa615ca01d3a6e3ff2bbd2ccd02cf71ec6acbd9e28a652c58e00` 与发布清单吻合。使用 7-Zip 21.07 在工作区隔离解包 580 个文件，未执行安装器，所以不计安装器验收。官方 Shell 已可启动并查看桌面截图；DailyFlow 的首轮旧摘要准入失败，修正隔离测试摘要后成功加载。`launch-r1/r2/r3` 已退出，未调用 Provider。旧运行时业务 15 次调用、Agent 43 项及短超时回归通过，见 `build/semifinal-202610/regression/business` 与 `agent`；这些不属于 RC2 实测。

后续官方 RC2 记录：`build/semifinal-202610/official-host/portable-stage-r3/shell-check/result.json` 与 `portable-candidate-r1/shell-check/result.json` 曾记录 `ready:true`、`local_legacy_catalog:true`、`provider:false`、`stopped:true`。这只证明两个包加载出 `chat_input`，原探针漏判了 `App tools unavailable: Script tool apps must declare requires: ["script-tools-v1"]`。因此撤回“工具就绪”的任何推断；未请求 Provider、未批准应用 Agent，工具调用和完整 UI 任务仍未通过。新探针须把此类 notice 作为失败。

## 与独立来源的边界

应用自身工具执行与第三方 App 互通分别验证。RC2 的第三方 owner 解析限制仍按[更新核对](OCTOSENSE_RC2_REVIEW.md)处理；本桥接不负责跨 App 路由，也不会把工具结果自动写入事件投影。不能通过冒用 `os.*` 身份、扩大私有工具共享或开发者模式绕过权限来宣称互通。

## RC2 隔离启动与测试入口核对

以下为固定 RC2 源码核对，尚非成功运行记录。

| 配置或入口 | 实际含义与限制 |
| --- | --- |
| `OCTOS_APP_CORE_DIR` | 指定隔离的 Octos core 根目录，内含 `profiles/_main.json` 等状态；默认才是 Shell 数据目录下 `octos-home/.octos`。不能只隔离应用数据而继续复用个人 core 做批准/peer 试验 |
| `OCTOS_APP_CORE_BIN` | 显式指定内核可执行文件，优先于随包内核；显式路径不会经过随包 receipt 的版本检查。默认优先使用同一发行包里的内核与 receipt |
| 随包内核 | Shell 旁 `octos-kernel.exe` 加 `octos-kernel.json`；默认校验 pinned revision 与 SHA256。解包目录已有该 receipt，不应生成假的 receipt 或启用 ANY_REVISION 绕过 |
| 子进程参数 | Shell 以 `serve --stdio --data-dir <core>` 启动内核，给子进程设置 `OCTOS_HOME=<core>`；`<core>/config.json` 存在时再指定配置 |
| `--test-action system-chat` | 打开真实系统助手 UI |
| `--test-action system-chat-send:<text>` | 向真实系统助手发送输入，可能请求真实 Provider；不是离线测试 |
| `--test-action ask:dailyflow` | 打开真实 DailyFlow 应用 Agent 面板，经正常 `agents::ask` 请求首用同意；不会自动允许 |
| `--test-action ask-send:<text>` | 向当前应用 Agent 面板发送输入；须先建立正确应用面板并准备好 Provider/peer |
| `approval-sheet` / `approval-consent` 等 | 仅用于显示示例审批，不能当 DailyFlow 真正工具调用或批准证据 |

内核依据：[launch.rs](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/kernel/src/launch.rs)、[dirs.rs](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/kernel/src/dirs.rs)。助手入口依据：[系统助手](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/shell/src/system_chat/mod.rs)、[应用助手](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/shell/src/app_chat/mod.rs)。所有正向授权与危险动作批准仍由用户操作，不使用合成批准代替。

### 旧启动器的两项兼容风险

1. `tools/launch_desktop_flow.py` 强制要求已有 `profiles/_main.json`，并从子进程环境主动删除 `OCTOS_APP_CORE_BIN`。它不适合直接验证“无 Provider”的首次启动，也不能指望外部设置的 BIN 被保留。当前可使用完整官方发行包的默认内核发现，无需更改个人配置。
2. `stage_local_catalog` 使用临时开发签名产生旧 `catalog.json`；RC2 默认选择 GitHub v2，读取 `catalog-v2.json`，不会因发现旧缓存自动降级。只有在全新隔离根目录明确设置 `OCTOSENSE_HUB_CATALOG=legacy`，才适合继续这条本地开发验收；根目录已有 v2 缓存时拒绝降级，不应删除正式缓存来强行降级。`.bundles/<id>/bundle` 仍是官方优先目录，新增 manifest 可选字段为空时保留旧签名字节规则，但旧 hub stamp/check/verify 不能替代新宿主的实际准入。

第二项直接解释了“旧本地 catalog 已验证，RC2 却只显示桌面而不打开应用”的一个源码可见原因，最终以运行日志和可见错误为准。[官方目录选择](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/95e4831afca7227b640f075b252c04355bb63865/crates/appstore/src/source.rs)。这一 legacy 开发准入不等于 GitHub 发布认证通过。

### 已独立重算确认的 Windows 摘要差异

补充 `legacy` 后仍未加载，继续对 `visible-r1` 留存包只读核验。其 manifest 与 catalog 中的 manifest 完全一致，发布者签名和 catalog 工作密钥签名均通过 Ed25519 独立验证；当前文件的 compute/network/storage/model 默认值与 RC2 序列化对应。该轮未读进程内临时 anchor，未把这项验证误称完整信任链。

发现旧活跃 hub 的 `digest_dir` 使用 Windows `relative.to_string_lossy()`（子目录反斜杠），RC2 使用 portable `/`，路径排序仍为 Path 组件序。独立 Rust 小工具对同一留存包的 8 个文件重算：

- 旧 Windows 算法：`1bf14a6bcc1ecc9492bf0d69703d9c4a958754bdf17074a4734a1e3ebb288baf`，与旧 stage 的 manifest 精确一致。
- RC2 算法：`6013f592c06371d239d7820ae1ecb2512c4a4caa9b43b5cb2fa3b33b4d406fee`，不一致。

这证明旧 stamp 的包不能通过 RC2 摘要校验，不只是默认字段猜测。[固定 RC2 算法](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/95e4831afca7227b640f075b252c04355bb63865/crates/app-contract/src/bundle.rs)。辅助代码和证据位于 `build/semifinal-202610/official-host/digest-probe`、`stage_rc2_legacy.py` 与 `portable-stage-r3/rc2-stage-evidence.json`。重签仅发生在新的隔离副本，发布者/目录/anchor 私钥只在内存，三层签名读回验证通过；官方 RC2 仍执行正常 gate，不修改官方二进制、不禁用完整性检查。

当前 0.1.1 候选另有 `LICENSE.txt` 被旧 hub 资源 URL 扫描拒绝的问题，不能据此断言新宿主必然拒绝。实验 helper 的 `--skip-legacy-check` 仅省略过时开发 CLI 检查，让未修改的 RC2 正常准入决定是否可运行；`portable-candidate-r1/rc2-stage-evidence.json` 明记 `legacy_cli_check:false`，不算正式新 hub gate 通过。以上 staged 包均不是公共发布物。

### 必需声明与 RC2 首个 Card 注册顺序

拥有 `tools.json` 的应用必须保留 `requires: ["script-tools-v1"]`；不能删声明只为让 UI 打开。补声明后新 hub 检查与签名验证通过，但 `final-newhub-r2/shell-check/result.json` 记录 `ready:false`，日志没有 DailyFlow 源码求值。固定 RC2 manifest 已认识此 feature，且序列化非空 requires；进一步源码揭示一个先后顺序问题：

1. Shell `launch_app_with_args` 对第三方应用先调用 `catalog::try_may_open_from_environment`；Backend 使用此刻 `host_api::available_versions()` 执行 gate。
2. `script-tools-v1` 在 `check_host_apis` 要求 `app_tools.dispatch@1` 已注册。
3. 该 ABI 由 `CardModule::register` 注册，而模块的 register 只在后续 `launch_module_as` 创建实例时调用；首个第三方 Card 因而可能在自己的运行器初始化之前被拒绝。

验证方案是在全新隔离环境先正常打开官方内置 Calendar（`--test-action launch-calendar`），再 `--test-action launch-hub:dailyflow`。内置 `os.calendar` 使用同一 Card runner，跳过第三方 catalog gate并正常注册 ABI；Calendar 的只读 `calendar.view` 使用隔离状态。这个步骤不改二进制、声明、权限或完整性校验。仅延迟第三方启动不保证解决，因为注册依赖实际创建 Card。

2026-10-10 实测确认：`final-newhub-r3/shell-check/result.json` 为 `ready:true`、`ui_loaded:true`、`notices:[]`、`provider:false`、`stopped:true`；日志先出现 `launched calendar as client 1 (in-process, card)`，再出现 `launched hub:dailyflow as client 2 (in-process, card)`。对应直接启动对照 `final-newhub-r2` 为 `ready:false`。官方 exe 未修改，requires 保留，本地 catalog 签名及完整性检查照常执行。此结果证明首次 Card 初始化顺序影响当前路径，不证明真实工具已执行。详见[上游报告草稿](RC2_CARD_STARTUP_REPRO.md)，尚未对外提交。

依据：[Shell 启动 gate](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/shell/src/lib.rs)、[模块实例注册](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/shell/src/module_host.rs)、[Card ABI 注册](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/95e4831afca7227b640f075b252c04355bb63865/crates/appstore/src/cardapp.rs)、[设备兼容检查](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/95e4831afca7227b640f075b252c04355bb63865/crates/app-contract/src/manifest.rs)。

### 独立 core 的 Provider 最小要求

RC2 不要求另建 `<core>/config.json`：桌面启动只在该文件存在时传 `--config`，缺失则使用内核默认值。实际模型设置由 `<core>/profiles/_main.json` 提供。固定内核 `b0759a57719fd35b3a2da1c5d969bc67538ed516` 的 ProfileStore 直接读取该文件，`config_from_profile` 使用 `config.llm.primary` 的 `family_id`、`model_id`、可选 `route`（`base_url`、`api_key_env`、`api_type`）以及 `config.env_vars`；fallbacks 同样从该 profile 读取。仅看到 profile 顶层键不能证明内部 Provider 完整、凭据有效或网络可达。[内核 profile 实现](https://github.com/octos-org/octos/blob/b0759a57719fd35b3a2da1c5d969bc67538ed516/crates/octos-cli/src/profiles.rs)。

正常路径是在独立窗口的 AI providers 中由用户配置；Windows 默认密钥保存在 profile，`OCTOSENSE_LLM_VAULT=file` 明确选择该模式。使用既有设置时须按已获授权范围操作，仅向指定隔离 core 提供必要配置；不要读取或输出凭据值，不把 profile、env_vars、QR 或密钥复制进应用包/公开证据，也不复制旧 peer/session/consent。若密钥是 vault 引用而不是原值，仅复制 profile 不保证能解析，不能把“有键名”当“可用”。

固定 RC2 的 `vault::platform` 在 Windows 走 `InProfile`，没有另外必须迁移的 Provider vault 文件。最小隔离副本只需 profile 必需顶层元数据、`config.llm` 和 `config.env_vars`，移除旧 `tool_policy`，由新 Shell 写入其策略；前提是 env 值形态不是空值、`***` 掩码或 `keychain:` 引用。检查可以只记录布尔结论，不输出名称或值。独立副本应置于 ignored 的本地状态目录，不能放进可提交证据。[固定 vault 实现](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/apps/ai-providers/host-service/src/vault.rs)。

启动参数可以依次给 `--test-action launch-hub:dailyflow --test-action ask:dailyflow`：Shell 循环按参数顺序执行；`ask` 从当前 catalog 同步查找已安装应用，不必等 Splash 首帧，正常进入首用 `NeedsConsent`。这一步只请求同意，不批准。先不拼接 `ask-send`，避免在尚未授权或连接完成时发送；用户同意后再进行实际输入和工具验收。

源码进一步确认：`ask-send:<text>` **不缓冲**。`app_chat::send` 在 `s.context` 为空时显示 `Not connected yet.` 后直接返回；`ask` 的 `connect` 则在新线程建立 conversation，之后才赋值 context、加载历史。沿用已同意的同一隔离目录重启也仍要重新建立 context，因此把 `ask` 与 `ask-send` 连续写在启动参数中存在竞争，不能作为可靠验收。`OCTOSENSE_TEST_ASK_DELAY` 只延迟 `ask-appcard` 对另一个原生 `appcard` 模块的调用，并不延迟本应用的 Ask 面板；RC2 的通用 `/event` 路径也没有转发 `ask-send`。只有真实 context 准备好后的发送才走 `ContextOp::TurnFrom` 与真实模型链。[发送与连接实现](https://github.com/OctoSense-org/OctoSense/blob/4ccf8e068399b1da139771a9ed94cef05fa6ae60/crates/shell/src/app_chat/mod.rs#L359)。本结论为只读源码核查，未重新启动或发送测试提示。

Shell 每次启动内核会向其 core profile 写入自己的 `config.tool_policy`，保留其他键；已有其他所有者的 policy 则拒绝覆盖。这正是不能让新验收内核直接共用个人 core 的原因。保持 `OCTOSENSE_CONTAINED_APPS` 未设置（默认首用同意），不设为 `1`；应用 Agent 许可和危险动作批准由用户手工完成。[宿主 policy 写入](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/kernel/src/system_tools.rs)、[官方独立配置说明](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/docs/ai-services.md#desktop-with-a-throwaway-kernel-and-profile)。本次研究没有读取个人 Provider 值，也没有启动模型或变更配置。

### 当前人工只读验收窗口

集成负责人已准备 `.local-state/semifinal-rc2-agent-r2` 的官方可见窗口，使用补全 requires 的候选，并先正常初始化 Calendar。日志记录 `dailyflow's agent is prepared (its peer is listed for the system agent)`；这只证明应用 Agent peer 准备，不等于已请求真实 Provider 或已执行工具。该目录含隔离运行状态，不能打包上传或纳入公开证据。

由用户在 Ask DailyFlow 面板手工发送：

> 请只做只读验证：实际调用 dailyflow.capabilities，然后调用 dailyflow.query，参数为 {"limit":5}。分别展示工具返回结果；没有记录就明确说没有记录。如果工具或模型不可用，请如实报告错误。不要创建、更正或删除任何记录。

验收必须看到真实工具调用名、调用完成结果，以及与隔离数据一致的查询结果；单独的自然语言回答、peer prepared 日志或 UI 就绪均不算通过。若出现同意界面，由用户自行判断并操作；自动化不批准、不代发提示。用户发送后再核验有限日志并对证据脱敏，不收集 Provider profile。此步骤通过后，写入、拒绝、更正、取消与重启读回仍单独待测。

### 不要把通用 remote 入口当任意工具执行器

Shell 的 `/event?data=system-call:<tool> <json>` 仅接收中转目录中声明为 `read` 的工具。`agents.ask` 为 `act`，不会从这里执行；`agents.list` 由系统助手会话单独注册（owner=`agents`），该入口的 namespace 查找却会导向 `os.agents`，也不等价于真正系统会话调用。`dailyflow.*` 同样不能依靠此入口绕过第三方 owner 解析问题。

因此应通过系统助手真实会话完成 `agents.list`→`agents.ask`→实际返回的 peer slug→`peer_send_input`；或先用 `ask:dailyflow` 验证应用 Agent 自有工具。手动发送提示或直接测试动作只能分别证明输入/执行层，不可冒充模型自主选择工具的证据。[只读测试入口源码](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/shell/src/host_tools/mod.rs)、[系统会话注册](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/shell/src/system_chat/session.rs)。

## 2026-10-10 真实官方应用Agent只读调用

用户在顶部Ask DailyFlow手工发送提示并确认收到结果。北京时间01:16:17，官方peer审计记录query和capabilities均allowed/ok，耗时195/202ms，返回85/549bytes。脱敏证据为本地`build/semifinal-202610/official-host/real-agent-r1/read-tool-audit.json`。审计不含结果正文，不能代替schema/数量核验；这是应用Agent自有工具调用，不等于系统助手发现和委派。拒绝/批准写入、重启及关闭验收仍待完成。

拒绝写入实测证据：`build/semifinal-202610/official-host/real-agent-r1/denied-write.json`。用户亲自拒绝，审计与文件前后态独立核对；不代表批准写入已通过。

批准写入证据：`build/semifinal-202610/official-host/real-agent-r1/approved-write.json`。官方save_record approved/ok后query allowed/ok，用户读回与独立读取合成状态一致。1条expense外有1条关联已发生事件，不能混淆源记录数量与时间线节点数量。

官方同源更正证据：`build/semifinal-202610/official-host/real-agent-r1/corrected-write.json`。记录revision 2→3、120→100元且expense计数仍1，关联事件和关系未变；全局state revision=2与记录revision=3分别核对，不混用。

重启验收暂未通过：用户收到r2空结果，但重启前后业务文件哈希未变且state-b仍含r2/100元/revision3。审计只有参数长度，无参数正文；正在核对严格ID查询与expense全量查询，未确认是参数筛选还是运行时加载问题。见本地`build/semifinal-202610/official-host/real-agent-r1/restart-query-mismatch.json`。

2026-10-10 19:34更新：用户提供严格参数与原始返回，两次查询均读到r2/100元/revision3/total1；官方审计两次allowed/ok，业务文件哈希未变。整宿主重启精确读回通过，见`build/semifinal-202610/official-host/real-agent-r1/restart-readback.json`。此前空结果的具体根因仍未确认，失败证据保留。

系统委派首轮未通过：系统助手见peer done后引用旧黑板，未给出新query结果。内核固定b0759a5工具说明确写running only，但实际执行交host callback；RC2 Shell又引导ready应用peer用peer_send_input。保留为待复现的契约/引导疑点，不声称运行时缺陷已确认。见本地`build/semifinal-202610/official-host/real-agent-r1/system-delegation-pending.json`。
