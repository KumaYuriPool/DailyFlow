# 夜间集成契约 v1.0.0

状态：冻结；本契约定义应用层接口，不是宿主能力声明。基线摘要与角色路径以 `.parallel/night-20261013/dispatch.json` 为准。角色不得修改共同契约；不兼容需求写入自己的 `contract-change.md`，由 I 在阶段 B 处理。

## 1. 身份、存储和证据边界

| 项目 | 冻结值 |
| --- | --- |
| DailyFlow app_id | `dailyflow`（现有身份不变） |
| 独立账本 app_id / 展示名 | `dailyflow-ledger` / DailyFlow Ledger |
| 来源模块 / 工具命名空间 | `expense` / `dailyflowledger` |
| 来源类型 | `independent_app`；未完成真实路由前 connection 为 unavailable/unknown |
| 来源数据文件 | 账本自己的 app-data 下 `ledger-v1.json`，禁止直接读写旧 DailyFlow 账目 |
| DailyFlow 持久数据 | 既有 `experiences-v1.json`；新增 `source-connections-v1.json`、`source-sync-v1.json`、`external-requests-v1.json`（版本均为 1） |
| 模拟社媒 | `synthetic-climbing`、`synthetic-concert`，标为 `synthetic_import` |
| 导入日历、费用 | `synthetic-calendar`、`synthetic-expense`，标为 `synthetic_import`；不伪称真实连接 |

每角色 app-data、home、core、日志、输出目录独立。实际路径见 dispatch。不得复制 Provider、授权、个人数据；默认新 home 无授权，真实权限由人处理。已有 Provider 只能按当前宿主支持的方式原地只读引用，不把配置复制进工作副本或交付包。旧脚本若会复制 core，必须先调整隔离启动方式，不能直接执行。

账本与模拟费用属于不同来源，不默认把同一业务样本同时启用并累计；真实账本演示范围关闭 synthetic-expense，社媒/日历仍如实标为导入。旧工作台不迁移、不充当独立账本。

## 2. 已有格式的选择与纠错

外部 wire 沿用 `docs/EXTERNAL_SOURCE_CONTRACT.md` 的 **contract_version=1、records/tombstones/content** envelope；不是 `experiments/source-bridge/consumer.py` 的 protocol-v2/events 实验外壳。旧同包 `08_time_protocol.splash` v2 不改。S 在适配层完成两者映射。

旧 v1 文档“相同修订 hash 改变可以 upsert”已与修复后的 importer 冲突。本轮明确：**同修订同内容幂等；同修订不同内容/删除冲突拒绝；只有更高修订可更新**。完整身份是三元组 `(source_app, source_module, source_record_id)`，旧 Python importer 只用 app/id 的目录键不能原样复用给多模块。这些是本轮明确的约束补充；旧历史契约文档不覆盖改写。

## 3. 账本拟实现工具（须由 H 验证真实注册和归属）

| 工具 | 输入 | 输出与权限 |
| --- | --- | --- |
| `dailyflowledger.capabilities` | `{contract_version:1}` | 协议、模块、read_events 工具名、分页上限；read |
| `dailyflowledger.read_events` | `{contract_version:1,page:0,page_size:50,snapshot_revision:null}` | 下述完整 envelope；read、private_data=true，跨 App 共享必须经宿主合法授权 |
| `dailyflowledger.save_record` | `{contract_version:1,request_id,record_id?,expected_revision?,content}` | `{record_id,source_revision,snapshot_revision}`；新增或更正，宿主确认；不开放给 DailyFlow 读取适配器 |
| `dailyflowledger.delete_record` | `{contract_version:1,request_id,record_id,expected_revision}` | `{record_id,source_revision,snapshot_revision,deleted_at}`；destructive、宿主确认 |

工具名是本轮应用契约，不保证工具 namespace 能被宿主映射到 app_id；若实际 owner 路由不支持，H 报告 blocker/最小通用修复，不冒用 `os.*`，不静默更名。具体 manifest schema 与 confirm 写法遵照实际 runtime，不新增虚构宿主字段。模型不得重写工具原始 JSON 充当来源传输。

账本写入 request_id 长度 1–128，同一 request_id 和规范化输入相同，返回已落盘结果；不同输入返回 REQUEST_CONFLICT。更正、删除须 expected_revision 精确相等，否则 REVISION_CONFLICT。新增生成稳定不含路径分隔符的 record_id；更正不换 ID；删除为更高修订墓碑，ID 永不复用，本轮不支持恢复删除。幂等收据与业务记录一次候选提交，重启仍有效；容量不足明确拒绝，不悄悄逐出收据后重放。

## 4. Envelope 与分页

正常工具应用结果统一为 `{ok:true,data:<payload>,error:null}`；失败为 `{ok:false,data:null,error:{code,message,retryable,request_id,source_app}}`。Splash 的 ok 字段使用 `"ok"` / `["ok"]`。宿主外壳仍按实际 `is_ok/data/output` 解码，不能把宿主外壳当业务 envelope。

```json
{
  "contract_version": 1,
  "source_app": "dailyflow-ledger",
  "source_module": "expense",
  "fetched_at": "2026-10-13T00:00:00Z",
  "snapshot_revision": 1,
  "page": 0,
  "page_size": 50,
  "has_more": false,
  "records": [],
  "tombstones": []
}
```

records 项为 `{source_app,source_module,source_record_id,source_revision,content_hash,content}`。content 字段沿用旧 v1：kind/occurred_at/ended_at?/open_end/title/body/media/tags/amount_minor/currency/source_meta。账本 kind 固定 expense；金额整数 0..9007199254740991 最小单位，禁止浮点和 bool；币种为非空三位大写 ISO 代码（本轮录入可仅支持 CNY，遇不支持币种明确拒绝）；不同币种不合计。title 1..80，body 0..4000；media=[]；日期为合法 YYYY-MM-DD 或带 +08:00 的 RFC3339，日精度不补零点。

content_hash 为小写 SHA256，算法沿用 importer.canonical_content_hash：UTF-8、JSON key 递归排序、ensure_ascii=false、紧凑分隔符，无 NaN/Infinity；本轮 content 仅整数字段，无浮点。S 必须实现并验证真实运行层同算法，做不到要提出兼容变更，不能填伪 hash。身份、修订及 tombstone 不计入 content hash，但分别严格校验；可信身份来自宿主绑定，不能相信 payload 自报。

tombstones 项为 `{source_app,source_module,source_record_id,source_revision,deleted_at}`，deleted_at 为 UTC RFC3339；无 content/body/amount，不要求 content_hash。revision 正整数；相同修订墓碑完全相同才幂等，不同 deleted_at 为冲突。

分页冻结如下：

- page 从 0 起，page_size 1..50，默认 50。对当前每条记录的最新状态（含墓碑）按完整身份字典序排列后切页，页内再分 records/tombstones；两数组总数不超过 page_size。
- 首次 page=0、snapshot_revision=null；返回非零快照版本。续页必须携同一 snapshot_revision 和 page_size；账本任一有效写入递增快照，旧续页返回 SNAPSHOT_CHANGED，消费端重新 page=0。
- `has_more=true` 必须有记录且存在下一页；最后空库可 page=0 两空数组 has_more=false。超范围页返回 INVALID_PAGE。消费者最多 100 页/5000 项，超限返回 TRUNCATED 并不宣称全量成功。
- 每次拉取完整快照，包括墓碑；没有隐含 since 游标，也不能以缺席推断删除。持久化 checkpoint 只在整轮所有页验证通过后提交（snapshot_revision、页数、fetched_at）。失败丢弃暂存，保留上次合法投影及同步时间。
- 持久化接收候选必须原子/可回滚，沿用 write_checked 等存储保护；不能先更新游标再更新投影。合并键包含模块；旧修订忽略；同修订冲突拒绝整个同步事务。删除、更正使对应详情/费用确认/关联引用失效，排除决定仍按完整身份保留。

## 5. S → U/H 的应用内接口

下列是 **拟实现 Splash 函数**，S 独占定义，I 接线；不得直接将名字当宿主服务调用。

| 函数 | 约定 |
| --- | --- |
| `nf_source_states()` | 返回下述来源状态数组的只读副本，不启动工具调用 |
| `nf_source_set_scope(source_app,enabled)` | 本地选择是否进入展示/模型范围，返回结果外壳；不是宿主授权 |
| `nf_source_sync(source_app,request_id)` | 启动确定性只读同步；立即返回 request_id/state，完成由状态查询读回；同 ID 不并发重入 |
| `nf_source_cancel(request_id)` | 失效 generation，丢弃暂存；宿主取消能力由适配层验证 |
| `nf_source_records(source_app)` | 只返回有效授权、启用范围的已提交生产投影，不泄露不可用缓存 |
| `nf_source_accept_page(binding,request_id,generation,reply)` | H 适配层将原样结构化结果及可信绑定交给 S；不向模型公开成任意导入工具 |

binding 至少含 owner_app/caller_app/tool_name/auth_epoch，值来自经过 H 证实的宿主上下文，不能从模型或来源内容拼造。H 暴露应用内 `nf_transport_read(source_app,tool_name,args,request_id,generation)` 和 `nf_transport_cancel(request_id)` 适配边界；真实支持前返回 TRANSPORT_UNAVAILABLE。S 可以注入显式 fixture 验证自身，但不把 fixture adapter 带入默认生产路径。宿主 API/schema 由 H 的 probe-report 给出。

来源状态项固定：`{contract_version:1,source_app,source_module,label,kind,connection,authorization,scope_enabled,scope,last_sync_at,snapshot_revision,sync_state,request_id,error}`。

- kind：independent_app / synthetic_import / file_import / local_legacy；connection：unknown / unavailable / available / imported；authorization：not_applicable / unknown / denied / granted / revoked。
- scope：`{modules:["expense"],date_from:null,date_to:null}`；v1 真实账本同步为完整 expense 快照，日期筛选只影响展示，不裁掉墓碑。last_sync_at 未成功为 null；sync_state：idle / reading / validating / succeeded / failed / cancelled。
- 本地 scope_enabled 不修改 authorization。重启授权先 unknown 并隐藏缓存，须当前可信授权证据重建；明确拒绝/撤权立即取消在途任务、auth_epoch 递增、清除详情和模型缓存，拒收迟到结果。
- 失败可保留上次合法内部数据但必须显示 stale/error；授权 unknown/denied/revoked/unavailable 时不展示缓存正文/金额、不送模型；未成功不得变 last_sync_at。不要因失败将所有源标为 deleted。
- 导入来源可显示 imported/not_applicable，不宣称 granted；界面可以独立显示范围与宿主权限。连接按钮不得自动批准。

错误 code：INVALID_ARGUMENT、INVALID_PAGE、SCHEMA_MISMATCH、IDENTITY_MISMATCH、HASH_MISMATCH、REVISION_CONFLICT、REQUEST_CONFLICT、SNAPSHOT_CHANGED、TRUNCATED、NO_CONSENT、REVOKED、TRANSPORT_UNAVAILABLE、APP_NOT_RUNNING、TIMEOUT、CANCELLED、STORAGE_ERROR、NOT_FOUND、UNSUPPORTED。message 不含秘密或整条私人记录；拒绝/取消不自动重试，SNAPSHOT_CHANGED 最多自动重启一次，其他失败由用户显式重试。

## 6. H → 经历持久化和 UI 定位

保留现有 `dailyflow.experience_context` / `dailyflow.experience_result` 的结构化校验语义（47/48/49）。新增应用工具拟议名 `dailyflow.experience_request`、`dailyflow.experience_request_status`、`dailyflow.experience_request_cancel`，由 H 提供 schema/风险声明，I 接 tools/manifest。它们不等于现有系统 Assistant 自动可调用。

外部请求 v1：`{contract_version:1,request_id,question,source_apps,experience_id:null}`。request_id 1..128，question 1..2000，source_apps 为已注册身份数组；null 创建独立持久经历，已有 ID 必须存在。调用方身份和 origin_turn_id 由真实宿主上下文绑定，不接受请求正文自报。source_apps 为空只做规划，不能默认读取全部私有来源；规划选源仍受授权和本地范围限制。

H 提供应用内 `nf_external_submit(binding,args)`、`nf_external_status(request_id)`、`nf_external_cancel(request_id)`、`nf_external_pending_open()`、`nf_external_ack_open(request_id,experience_id,generation)`；返回统一结果外壳。status data 固定 `{request_id,experience_id,origin_turn_id,worker_turn_ids,generation,state,error}`。

状态：accepted → reading → organizing → persisting → completed；终态 failed/cancelled/timed_out。每个 request_id 绑定规范化请求 fingerprint、完整调用方身份及独立 generation；同身份同输入重放返回原状态，异输入/异调用方同 ID 拒绝。不同请求可串行排队，不得覆盖已有经历或取消另一请求；取消/超时终态不接受后续结果。

先将 request→experience 映射和待处理记录写入 `external-requests-v1.json`，新经历 ID 沿用 experiences-v1 的 seq/experience-N 分配，不另建会撞号的计数器。实际结果只经现有上下文、quote/revision、结构化提交、turn 终态全部校验后保存；源变化/撤权须再次校验。结果落盘成功才 completed；写入失败 STORAGE_ERROR，不向 UI 发成功定位。

跨文件写入不能假定原子：请求日志记录 persisting 及目标 ID；经历使用现有持久化层成功后再记录 completed 和 pending_open。重启根据经历记录与日志恢复；不明状态不得重跑产生第二经历。正在运行的旧 turn 不自动当成新请求，无法恢复应明确失败并拒绝迟到结果。

pending_open v1 为 `{request_id,experience_id,generation,created_at}`，存于外部请求日志。U/I 消费前核对 completed、ID 存在、generation 当前，再调用现有 `ex_select`；成功显示后 ack，避免每次重绘抢回旧经历。删除/未知 ID 显示 NOT_FOUND，不打开第一条代替。

应用内 pending_open 只是定位信号。**冷启动、启动/聚焦窗口、系统 Assistant 新问题委派、可信传输回调、宿主撤权通知目前均为 unknown**；H 需真实探针确认 API、参数、身份与授权。只写日志/返回链接/用户手点卡片不算自动打开；严禁全局文件轮询绕过宿主。H 的探针结论必须分开报告 delegation、activation、selection、transport。

## 7. 文件边界与构建顺序

| Owner | 独占修改范围 |
| --- | --- |
| U | `DailyFlow/src/65_experience_ui.splash`，新增 `66_experience_overlay.splash`、`experiments/experience-modal/`、`tools/night_u_*` |
| S | `DailyFlowLedger/**`；新增 `DailyFlow/src/45_source_connection.splash`、`45_source_sync.splash`、`tools/night_s_*`、`experiments/night-source/` |
| H | 新增 `DailyFlow/src/49_external_entry.splash`、`tools/night_h_*`、`experiments/night-host/`、私有 `runtime-work/` 及平台补丁 |
| I | 主目录全部接线；47/48/49_experience_peer/46/60、tools/build_event_app.py、tools/native_runtime.py、旧测试适配、bundle manifest/tools、catalog、启动器、唯一账本 |

S 两模块在 46/47 前，H 模块在 49_experience_peer 后，U 新模块的 UI/helper 类型须明确告诉 I 以避免构建器替换范围错误。函数 forward reference 依现有 Splash 行为，角色必须在私有生成包验证。所有未列出的既有文件默认共享，角色必要修改放 integration.patch；不能悄悄扩大独占范围。

角色可生成私有 bundle 但不能手改 main.splash，也不能用私有整包覆盖主包。生成产物列入测试候选哈希，不作为覆盖式源码增量。最终业务通过与真实 E2E 只以 I 合并后的候选为准。

## 8. 交付与验收

遵照 COMMON：HANDOFF.md、manifest.json、changes.patch 或逐文件 base/new、integration.patch、tests.json、TASK_RESULTS.json、contract-change.md、进程清单。manifest 必须包含 baseline_id、contract_version、contract_sha256、前后文件 SHA256、实际运行时 manifest 摘要；无改动的部分写明 none。

H 首先交 `delivery/H/probe-report.json`，每项带 available/unavailable/unknown、确切宿主 API/schema、runtime sha、原始证据路径及静态/真实分类。S 可只读一次该文件；不存在则完成离线层并交付待联调，不能循环等文件。

共同反例：22000→20000 同 ID 更正、重复页/重复请求、删除→重启、同 ID 跨来源/跨模块、坏 hash、同修订冲突、快照变动、空页/截断、存储失败回滚、拒绝/撤权及迟到结果、旧工作台不变。最终系统 Assistant 两场景冷/热自动定位和 1280/412 视觉检查保留给阶段 B。任何静态或注入通过不能替代真实跨 App 及系统入口验收。
