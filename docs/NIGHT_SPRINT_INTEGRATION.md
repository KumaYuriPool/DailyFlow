# 2026-10-13 阶段 B 集成记录

当前为进行中；没有最终通过结论。唯一账本仍为 `execution-state.json`。

18:01 后进展：两份新 release exe 均构建成功；`runtime-final-r1.json` 固定四 exe 与完整公开源码清单。18点再次核对29来源，内核/Matrix的新提交仅涉及测试代码，逐段判断见 `upstream-freeze-equivalence.json`；保留真实构建提交，不声称新测试HEAD已编译。前期 `runtime-test-r1.json` 与最终manifest采用相同四exe，最终交付须保存对应哈希比较。

17:59:42 冻结43份应用源码/声明。冻结后原生测试暴露账本规范化/持久校验中旧兼容分支的VM栈错误，以及消费者合流残留的无对应条件else；修复保留所有字段/类型/范围校验。失败 `producer-contract-r1/r2/r4`、`producer-trace-r3`、`producer-storage-r5`、`producer-contract-r6` 与 `consumer-final-r1` 均保留。`producer-contract-r7` 14项通过（timer调用本应用业务，非跨App工具证据）；`consumer-final-r2` 24项、`external-final-r1` 39项通过（明确注入）。`ledger-ui-narrow-final-r1` 的真实录入220→更正200→确认删除→重启6项通过，实际412宽截图已打开查看。宽屏经历测试首轮的来源卡断言受弹层保留的滚动位置影响，正在从顶部重新扫描；不能记为整卡UI通过。

宽屏二轮进一步排除了滚动原因。短探针 `settings-probe-r1` 的实际顶部控件表显示标签回退到了 `dailyflow-ledger` 等内部ID；设置页改用按实际 source_app 映射的显示名称，连接/授权/同步状态仍读实时接口。保留两轮失败与探针，第三轮全流程正在运行。

三份交付位于 `D:/Life/AgenticApp/.parallel/night-20261013/{U,S,H}/delivery/<role>`。共同基线为 `night-20261013-stage-a-v1`，冻结契约 v1.0.0 的字节保持不变。收到交付后未创建或联系其他 Agent。

工作候选：`D:/Life/AgenticApp/DailyFlow/build/overnight-20261013/integration-r1/candidate-r2`。审计、原文件与三方合并输入保存在其父目录；早期失败的 candidate 与测试目录保留。S 的 bundle manifest 存在一次后续 stamp 导致的摘要漂移，已检查最终身份与权限，并重新生成，不能称原摘要一致。

## 合流决定

- 保留 S 最终独立账本的七模块结构、稳定身份 `dailyflow-ledger` 和命名空间 `dailyflowledger`，保留其最终界面和校验；没有迁移旧工作台数据。
- Canonical JSON 与 SHA 源码在生产者和消费者保持同一实现；应用层使用 H 已验证的原生位运算及整数 floor 修复，保留 S 的精确收据字节比较。未增加 hash 宿主 API。
- 来源消费者保留分页、整轮暂存及原子提交；接入 H 的身份绑定、取消和授权变化监听。关闭本机范围会停止进行中的同步；损坏状态停止读取。本机范围不代表宿主授权。
- U 的 65 界面及 66 helper 与 47/48/49/60 统一接线。来源面板调用运行态接口；外部定位关闭遮挡层并在最终经历内容渲染后确认准确 experience_id。
- `66_experience_overlay` 必须在 60 之前；只有 60/65 参与 UI 样式替换。全部 main.splash 由生成器生成。
- 两 App 通过配套 H 平台修复支持的已安装身份与只读工具通信；宿主 API 为 `app_tools.read/cancel/focus/watch_authorization@1`。声明能力不是授权，后台不能批准权限。

## v1 兼容说明与限制

应用 wire 版本仍为 1；省略 experience_id 在验证宿主身份后等同 null。`source_apps=[]` 的规划专用路径目前明确返回 `UNSUPPORTED_PLANNING_ONLY`，不是已完成的无来源规划能力；不会默认读取所有私有来源。外部整理同时只运行一项，其他请求返回 APP_BUSY；持久请求表上限 128。

本次来源读取每页 1 项、最多 100 页，不能宣传支持一次同步 5000 项。超出上限或内容哈希未完成不得提交部分投影。大型单条内容仍须以实际宿主测试结果为准。导入费用样本默认不启用，避免与真实独立账本重复统计；测试若需要这些样本，显式在隔离前置中开启。

## 运行时与证据边界

16:55 再次联网核对 29 个 Git 来源，H 交付后 Shell、kernel、matrix-sdk、storytold-filmcraft 已前进。本次私有更新分别选择 ffd5e488、d7a2e3a0、33ec929c、cee1feb1；完整提交及时间见 integration-r1/upstream-current.json。I 接管已结束的 H 私有增量构建树，保留更新前文件、H 交付与冻结二进制；主 Hub 锁及 Makepad 修复不变。构建成功前，H 已测 exe 仅是开发参照，不能称本次全最新通过。

独立 card-host 的界面测试采用明确记录的 manifest fixture，仅证明实际 Splash 界面。来源注入回放、原生账本业务调用、真实双 App 传输、真实官方系统模型分别记录。最终系统验收须在同一最新组合中验证新 turn、只读工具回执、确定性同步、结构化整理、保存与自动定位，不能用角色旧报告代替。

新验收应用数据放在 candidate-r2/state/apps。H 已由人配置的 home/core 仅原地引用，不复制配置、凭据或授权。真实撤权须由人完成；不得伪写授权文件。最终代码、权限、截图和许可证检查完成后才冻结可审核候选，公开发布/推送/比赛提交仍需具体授权。
