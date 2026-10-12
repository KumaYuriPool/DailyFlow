# OctoSense RC2 更新核对（2026-10-09）

本报告检查官方Release和固定标签源码，未下载执行Windows安装器、未升级本地运行时、未进行DailyFlow实机验收。结论用于压缩迭代排期，源码可达不能代替运行通过。

## 版本与比较基线

- 最新桌面预发布版：[desktop-v0.1.0-rc.2](https://github.com/OctoSense-org/OctoSense/releases/tag/desktop-v0.1.0-rc.2)，GitHub published_at 为2026-10-09T12:46:59Z，即北京时间10月9日20:46:59；SDK 1.10.0。
- RC2标签指向 4ccf8e068399b1da139771a9ed94cef05fa6ae60。本地现用补丁运行时基础为 d9d3b8be67614d894ccc685bebb3234a8e467193；官方比较显示标签领先249个提交，不能把它当成小补丁升级，也不涵盖本地自定义修改。
- 查询时main为d2194bdfd350ebbcd6f70a3dc4496f351bf27244，比RC2源码标签晚；main与实际发行包不混用。上一个桌面版为[RC1](https://github.com/OctoSense-org/OctoSense/releases/tag/desktop-v0.1.0-rc.1)。
- 本地 native-runtime-active.json 仍指向 build/native-update-20261006/OctoSense 中的 octosense-model-fix.exe；本轮未修改选择器及运行时。

## 与 DailyFlow 相关的变化

| 更新 | 已核实信息 | 对本轮的影响 |
| --- | --- | --- |
| 应用自身工具执行 | RC1发布说明已列出；RC2中tools.json声明的应用工具路由到已准入完整应用的活动UI isolate；关闭应用可见失败 | 官方宿主工具验收更有条件开展。分别验证应用打开/关闭、授权拒绝/批准、执行后源数据读回 |
| GitHub发布 | RC1已加入GitHub认证发布支持及来源证明校验 | 跟进官方publish-github流程，实际包检查/安装与本地check分开 |
| 可发现宿主API | RC2 SDK1.10.0提供files、location、需审核的Mail/Calendar、有限前台audio等API及支持信息 | 查询目标平台真实可用性；DailyFlow暂不新增这些业务或权限 |
| 模型权限 | RC2实际Shell使用基于已准入bundle的model权限回调，核对调用者根目录 | 不能依据默认旧路径检查就判定仍有旧故障；先实测，避免直接移植本地补丁 |
| 视频/引擎 | 本地视频控件、macOS/Linux捆绑Wasm运行时、系统助手Rust引擎工具/skills | 对本轮核心闭环优先级低；不将系统引擎能力宣传为所有第三方应用任意可用 |

依据：[RC2发布说明](https://github.com/OctoSense-org/OctoSense/releases/tag/desktop-v0.1.0-rc.2)、[RC1发布说明](https://github.com/OctoSense-org/OctoSense/releases/tag/desktop-v0.1.0-rc.1)、[固定版本工具执行代码](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/shell/src/host_tools/script_apps.rs)、[宿主API设计说明](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/docs/adr/0012-app-host-api-discovery.zh-CN.md)。设计说明包含历史阶段状态，实际发行情况以RC2说明和目标平台实测为准。

## 模型权限检查的准确结论

默认complete实现仍能看到旧目录的manifest检查，但仅观察该文件不足以判断Shell真实行为：

1. [ai-host注册模型服务](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/ai-host/src/lib.rs)向complete注入MODEL_GRANTS回调，未注册时拒绝。
2. [Shell注册服务](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/shell/src/apps.rs#L226)通过admitted_bundle取得当前准入应用，校验root/.host与调用者host_dir一致，再检查bundle.families是否包含model。
3. 因此RC2走准入权限机制，不宜直接照搬旧版“.bundles路径修复”。该结论证明源码路径存在，尚未证明DailyFlow在Windows发行包上的Provider调用、授权或工具执行成功。

manifest agent.tools与应用自身tools.json是不同来源；不能仅因agent.tools为空就判断自有dailyflow.*未注册。系统Agent能否直接访问、是否需要委派应用Agent，以目标版本实际发现与授权结果为准；不得为演示直接把私有工具改为共享。

## Windows 与发布说明中的限制

RC2提供Windows x64安装器，发布说明称三平台包完整性/隐私检查通过，源码CI通过49步，macOS打包验收与Linux启动验收通过。但Windows安装器未由发布者执行，且未嵌入代码签名证书，需要WebView2。不能据此声称Windows安装和DailyFlow视觉验收已通过。

Google/GitHub OAuth客户注册不随包提供，相关登录需要发行方配置；它与AI Provider的模型配置并非同一件事，不能据此认定AI Provider不可用。连接服务的各平台写入支持也不能直接类推为DailyFlow自己的存储工具不可用。网络视频重定向/播放列表允许列表仍有限制，不涉及本轮必要能力。

## 执行建议

### 第三方App之间工具授权的目标解析限制

进一步检查RC2的[relay.rs](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/shell/src/host_tools/relay.rs)中Catalog::owner_of与script_apps.rs的owner_for/install：跨App工具按首段命名空间查toolbox/workflow、内置native app，否则映射为os.<namespace>。查询时main也相同。自有工具却按真实安装app id登记，因此不能推断自建dev.example.ledger的ledger.events仅声明shareable并被DailyFlow请求，就能正确授权到该第三方来源。须用两个最小安装包在普通权限模式验证；这是源码可见的接入限制/待复现点，尚不是实机失败报告。不能冒用系统App身份或以开发者模式通过代替发布验证。

官方Agent工具返回与DailyFlow事件投影更新也是两步；需要设计并核验结构化数据传递，不能把模型重新生成的账目当权威源同步。此发现收紧此前关于跨App机制可用的宽泛描述，暂不授权修改宿主或拆分应用。

### 补充核对：官方Agent入口与工具ABI

RC2的[agents.rs](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/crates/shell/src/agents.rs)实现系统Agent发现应用、首用授权和peer委派；应使用发现返回的peer_slug。DailyFlow现有manifest中的agent.tools为空，不代表所属tools.json工具未注册；它与跨应用工具授权是不同配置来源。回顾和时间线仍为shareable:false，不为演示直接扩大权限。

当前DailyFlow/src/40_coordinator.splash:154使用on_agent_tool(token,name,args_json)及resolve/reject；RC2 ADR0012与[官方示例](https://github.com/OctoSense-org/OctoSense/blob/desktop-v0.1.0-rc.2/tools/fixtures/host-api-lab/bundle/main.splash)使用app_tool(name,call_id)及request/complete/fail。已确认接口形式不同，未验证旧ABI兼容性；正式接入前须核实或适配，不能只凭已有tools.json断言可用。目标是复用业务执行层，仅对接官方调用桥。RC2脚本工具依赖已打开的完整应用，关闭返回app_not_running，不能宣称支持自动后台启动。

10月10日先用独立环境评估固定RC2，最多约3小时定位宿主阻塞；通过才锁为验收目标。不覆盖现有运行时，不清理dirty checkout，不改makepad/platform/src/os/windows/d3d11.rs，不重置OctoSense-App-Hub/Cargo.lock。不预先承诺更新解决了所有旧故障。

若受平台问题阻塞，记录最小复现并取消可选recall开发，将时间留给稳定交付；备用官方版本必须实际验证且满足赛事要求。本轮只调查与更新计划，实际安装、模型调用和发布仍未执行。
