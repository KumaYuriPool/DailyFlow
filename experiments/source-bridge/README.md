# 独立来源接入实验（未接入生产）

本目录用于两件彼此独立的事：准备 RC2 跨第三方 App 授权的最小候选包；用独立 Python 消费者验证事件交换的正确性。所有记录均为合成资料，不含个人数据或 Provider 配置。

**不能把本目录的测试通过称为 DailyFlow 已支持跨 App。** 当前生产协议仍限定 `source_app == "dailyflow"`；Python 消费者不在生产构建里，两个包尚未在官方宿主运行、准入或安装。它们不是可发布成品。

## 文件与证据

| 文件 | 用途 |
| --- | --- |
| `consumer.py` | 独立 v2 消费者，显式绑定来源，原子校验一页、修订合并、明确墓碑删除 |
| `fixtures/historical-splash-all.json` | 从 2026-10-06 实际 Splash 合成测试保存的原始三来源输出；本轮仅离线回放 |
| `fixtures/upstream-owner-excerpts.json` | 官方 RC2 固定提交的 owner/grant 源码摘录及链接；不是实际失败日志 |
| `ledger/bundle/` | 使用 RC2 `app_tool/request/complete/fail` 的来源候选包，公开一条合成记录 |
| `reader/bundle/` | 请求 `probeledger.events` 的调用方候选包；没有投影导入器 |
| `../../tools/test_source_bridge_contract.py` | 独立消费者契约测试入口 |
| `../../docs/SOURCE_BRIDGE_PROBE.md` | 验证结论、平台限制、后续官方宿主步骤 |

历史输入来自 `build/time-protocol-r1/contracts-final2/all/results.json`，本目录副本 SHA256 为 `19be7f78c5b64a954ca442ec29557f597a6e463f1d01e8f68863ef9e707ca595`。原有历史验收使用当时的本地 card-host；不构成当前 RC2 发行版证据。测试用外部 `dev.dailyflow.probeledger` 身份的数据由测试显式构造，不假称来源 App 真正返回。

## 离线复现

在 DailyFlow 根目录运行，输出目录必须不存在：

```powershell
python -X utf8 tools/test_source_bridge_contract.py --output build/semifinal-202610/source-bridge/contracts-local-1
```

无需网络、UI、模型、宿主或第三方 Python 包。读取固定合成夹具，输出 tests.log 与 report.json。报告记录输入哈希、测试数量和严格的证据类型。

## 消费者契约

`Projection(bindings)` 的绑定由可信调用方提供，不能从来源内容或模型推断。`apply_page(bound_source, page)` 只接受该绑定的来源及模块。事件字段沿用 DailyFlow v2，外部来源身份和下列分页外壳为**实验扩展**，并非官方标准或生产 API。

```json
{
  "status": "ok",
  "source_app": "dev.dailyflow.probeledger",
  "snapshot_revision": 1,
  "offset": 0,
  "complete": true,
  "events": []
}
```

- 稳定身份为来源 App＋模块＋源 ID，不使用标题、日期或数组序号判断同一条。
- 同一身份只接受更高修订；相同修订相同内容忽略，相同修订内容冲突拒绝整页。新旧日期不改变身份。
- 删除只接受更高修订的明确墓碑。完整/空快照也不推断删除，要求来源提供墓碑；这是一项保守限制，不是完整同步算法。
- 续页须与已读取页的快照和偏移一致。部分结果标为 partial；任何缺失、错误或分页遗漏均不转换为删除。
- unavailable/denied 隐藏缓存内容并保留状态，缓存内部保留以便本次实验检查。实际授权、撤权时缓存清除、迟到响应作废和持久化恢复不由本程序实现。
- 事件完整保留来源引用、事实/计划、时间精度；日精度不补零点，金额必须是整数最小货币单位。Unix 时间戳允许有限小数，与现有 Splash 输出一致。
- 来源不可伪造、数据不可变校验不等同密码学真实性；生产还需要可信传输和宿主授权。此实验不接收模型改写过的源数据。

## 两个候选包的边界

`ledger` 的合成阶段由 UI 按钮依次从修订 1 的 CNY120，到修订 2 的 CNY100，再到修订 3 墓碑。重启回到修订 1；**不用于生产、重启持久化或复活安全验收**。读取工具无写权限、无网络、无真实账本。shareable 仅用于公开合成夹具，不能作为开放 DailyFlow 私有回顾的先例。

`reader` 仅验证宿主是否向其 Agent 提供正确来源的工具。它没有脚本直连、读其他 App 存储或模型结果导入能力。首个真实返回值也只证明传输一步，尚不证明数据进入 DailyFlow。

manifest 未伪造 integrity、签名或来源证明。需要由主 Agent 依据目标官方宿主当前支持的合法准入方式进行预检，使用隔离副本准备发布元数据；不能通过 `--allow-unsigned`、开发者模式、冒用 `os.*` 或手写授权状态宣称正式互通。
