# 阶段 B 后 U 补丁集成（2026-10-14）

本次将 U 的 `post-b-20261014` 交付增量合入阶段 B 候选，生成 `build/overnight-20261013/integration-r1/candidate-r3`。原 `candidate-r2` 的源码、bundle 和历史测试证据保留。主仓库 `src/` 与 `bundle/` 尚未整体提升为阶段 B 版本；本报告不把新候选误称为主源码已升级。

启动入口：`D:/Life/AgenticApp/DailyFlow/run-dailyflow-candidate.cmd`。原集成启动脚本 `integration-r1/run_candidate.py` 默认也使用 r3。它继续原地使用 r2 的 review 数据目录和 H 已有人配置的 home/core，只安装公共 bundle，不复制业务数据、Provider 或授权文件。通过 `--candidate candidate-r2` 可选择原候选代码；这不是数据回滚。

## 修改与身份

- `47_experience.splash`：已保存问题与下一次输入草稿分离；打开经历清空输入框，保存空草稿保留历史问题；没有可读来源时打开设置并保留草稿。
- `65_experience_ui.splash`、`66_experience_overlay.splash`：显示独立账本连接核验与同步入口；区分范围关闭、拒绝/撤权、同步失败、无记录及未导入样本。继续隐藏未经当次授权核验的缓存。
- `bundle/AGENT.md`：要求 Agent 根据普通问题自行构造协议参数，不让用户填写 source_app、request_id、JSON null 或预期金额。
- 新增 `tools/test_post_b_ui.py`，沿用 U 的交付实现。

54 个交付文件 SHA256 全匹配；4 个原文件与阶段 B 前哈希一致，无三方冲突。应用两份 patch 后逐文件验证输出，再从源码重新生成 bundle；未复制 U 的生成包。

`main.splash` SHA256：`f28a17209a4251bf7b7a7bfa4b865dc03ac2183a49bc930fe53cfdda78166a36`。

bundle BLAKE3：`21f04a78f50a0e3278c6aaf6230d62e3c15157c2a5053d49d0460965ff81a0d0`。

运行时继续采用阶段 B `runtime-final-r1.json`，四个 exe 已重新核验摘要，manifest SHA256：`aa65a223cc5b177c660bf5c53eaeac2353ce0a6e6cc46f58f1e8735479b23fb7`。本轮是固定运行时上的补丁回归，没有联网升级或声称 14 日全最新运行时验收。

## 验证证据

证据根：`build/overnight-20261013/integration-r1/post-b-u-20261014/`。运行时测试原始输出在 `candidate-r3/DailyFlow/build/post-b-*`，由资源守卫以 I 角色串行执行，使用独立合成数据。

- `merge-audit.json`：交付/前后文件/运行时/保护文件摘要及公共文件复制清单。
- `test-results.json`：每轮实际命令、退出码、时间与预算覆盖；保留失败轮次。
- `hub-check-local.log`：显式 `--allow-unsigned` 的本地准入检查。初次不带此标志按签名策略拒绝，原日志保留；本地通过不等于正式签名或发布。
- `install-report.json`：安装结果、已安装 main 摘要，以及已有 review 业务文件安装前后哈希比较。
- `final-audit.json`：最终数量、候选摘要、原候选/保护文件不变与宿主清理核对。

本轮 4 张 `post-b-ui-r1` 截图已由 I 实际逐张打开查看：1280/412 下旧请求不占输入框，同步入口和设置关闭按钮可见，导入样本状态解释明确；未见新增遮挡或内容越界。窄屏侧栏原有省略显示与 Esc 不关闭弹层仍保留。

外部状态机首轮 `post-b-external-r1` 在默认预算下出现 `script time budget exceeded`，不是通过。沿用阶段 B 插桩验收方式，仅为外部状态机重跑设置 `MAKEPAD_SPLASH_BUDGET_MS=4000`；其余 UI/旧工作台和启动入口不设置该覆盖，生产 bundle 未改预算。

既有 H 测试驱动的 `production_main_sha256` 对 `read_text()` 后的 LF 规范化文本计算，因此与 Windows CRLF 文件字节摘要不同；原报告未改写。`final-audit.json` 同时保存两者并验证对应关系，候选身份以文件字节 SHA256 为准。

本轮自己的测试串行执行。测试结束时守卫曾观察到另一个任务短暂启动的两个 Cargo 进程并保留租约；其记录为 `retained-lease-after-tests.json`。随后只读确认这些进程已自行退出，按守卫接口释放 I 的保留租约后才安装。未终止其他任务，不能声称整个测试时段全机绝无外部编译。

## 验收边界

本轮 GUI 使用 card-host 的 UI manifest fixture；外部状态机使用注入宿主绑定与模型返回。它们不证明真实系统 Assistant、真实授权或跨 App 全链路。阶段 B 的真实冷/热 E2E 证据仅对应原 r2 `46a7c6d3…`，不能直接转记为 r3 新通过。

官方 Assistant 清空实际上下文仍未由本补丁修复；普通自然语言请求的真实模型 E2E 仍待单独验证。U 的诊断在 `.parallel/night-20261013/U/delivery/U/post-b-20261014/ASSISTANT_CLEAR_DIAGNOSIS.md`。本轮不修改平台运行时、不自动授权、不发布、不创建或联系 Agent。

最终结果：UI 22/22、外部注入 39/39、宽屏集成 41/41、旧工作台 8/8，共 110 项通过；已安装 r3，已有业务文件哈希一致，测试宿主退出、租约释放。
