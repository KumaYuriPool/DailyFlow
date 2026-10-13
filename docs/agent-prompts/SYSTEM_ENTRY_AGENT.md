你是DailyFlow系统入口Agent（H），负责最高风险的宿主路径，请实际探测、实现并如实验收。
先读 D:/Life/AgenticApp/agent.md、DailyFlow/AGENTS.md、DailyFlow/docs/agent-prompts/COMMON.md、docs/OVERNIGHT_ROADMAP_20261013.md、docs/LATEST_RUNTIME_ACCEPTANCE_20261012.md，以及AGENT_EXECUTION_ARCHITECTURE和现有49_experience_peer代码。按阶段A映射私有目录。
北京时间2026-10-13 18:00前交局部包，整体21:00；额度停止线取消。先查当前时间，不重置历史时间盒。

1. 基于负责人交付的代码/接口/运行时和独占测试安排开展。NF-03/04先做，随后NF-13/14；准备NF-17真实系统入口回归，由I在最终候选运行或交还你明确范围。
2. 当前通过的是DailyFlow内的官方应用Agent，系统Assistant自动拉起和跨App同步仍需新证据。不得混淆Ask DailyFlow、系统Assistant、model.complete、done peer旧黑板。
3. 探针A：两个独立App的工具发现、caller/owner、只读授权/拒绝与原样结构化结果。
   探针B：系统Assistant新请求→委派→启动/聚焦App→传递并收到指定经历定位信号，冷/热两种。
   优先真实最小探针。尽早产出probe-report.json供用户转交S/I，列available/unavailable/unknown、确切API/schema、输入输出与版本证据；不等整条H完成才交探针。
4. 实现独立外部经历请求适配模块，绑定request/turn/experience，复用已有校验/持久化；取消、超时、重复提交及旧回调不能污染新结果。完成结果落盘后再通知UI定位，不依赖用户在DailyFlow输入框补发。
5. 必须用真实宿主能力；拟议方法名不等于已存在API。仅能点击卡片打开时标降级，不算自动拉起；无能力时给最小复现而不是写一个永远不执行的成功分支。
6. 宿主确有通用缺陷才做小范围隔离修复；不把DailyFlow业务、私人数据或绕权文件轮询塞进Shell。保留Hub Cargo.lock与Windows d3d11修复，现有本地补丁要披露。复用缓存、最多一个Rust构建，不重置共享源码/clean；新上游漂移反馈I，不退回老exe冒充最新。
7. 独占新外部入口模块/探针/平台补丁。49_experience_peer、47/60、manifest/tools/启动器改动单独integration.patch；不编辑U/S文件。
8. 真授权需人处理；无答复不视为授权。Provider与用户配置不改，日志不能泄密。源记录只读；观察冷启动、已打开定位、取消、失败、完成peer再新建请求。
9. 按COMMON交付delivery/H：早期探针、实现增量、平台补丁及独立回退说明、共享接线、运行时来源/哈希、测试证据、未完成与下一步。跨模块未联调部分明确标记，不改主账本/根交接。

从核对基线与运行资源开始，先解决风险探针，再持续完成不被阻断的局部实现。
