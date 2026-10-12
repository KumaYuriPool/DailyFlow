# DailyFlow GitHub 发布预检

核对日期：2026-10-10。截止为北京时间2026-10-13 24:00；内部目标13日12:00提交并读回。当前只准备可审阅的本地工作流和发布步骤，未创建提交、标签、Release或比赛提交。

## 已准备与待解决事项

| 项目 | 当前结果 |
| --- | --- |
| 仓库布局 | 根目录bundle/，单个dailyflow应用，符合发布流程布局 |
| 当前源码版本 | 主Agent已准备manifest候选0.1.1；新标签尚未创建，不移动v0.1.0 |
| 许可证 | 根LICENSE为Apache-2.0标准全文，SHA256为cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30；本地旧v0.1.0标签不含LICENSE |
| 发布工作流 | 已由固定官方CLI生成 [.github/workflows/publish-app.yml](../.github/workflows/publish-app.yml)，尚未推送或运行 |
| 工具链 | 官方App Flow 049bc6b4010aa3660bab4ad632857d6ed4612151；其模板固定Hub 655114c4943cd2490daaefa2173e7b5aaa20669f |
| 新版本地Hub | 已从固定Hub与其三项依赖的git archive在独立目录以--locked编译成功，耗时1分53秒；已运行help，候选bundle门禁由主Agent统一执行 |
| 换行 | .gitattributes已有bundle/** -text，保留；从最终提交导出后仍须复验 |
| 材料版本 | 主Agent已将PRIVACY.md更新为0.1.1候选版；listing及最终新标签公开链接仍须发布前逐项核对 |
| 远端核对 | 本轮git ls-remote因本机127.0.0.1:7890代理不可达失败；连接器tags及Actions权限端点未提供结果，不能称远端权限或新标签已确认 |
| 运行与发布 | 官方宿主、新包证明校验、安装、截图、实际发布均需最终版本证据；本页不是通过记录 |

## 官方命令与实际安装方式

原Design Flow仓库已改名为 [OctoSense-App-Flow](https://github.com/OctoSense-org/OctoSense-App-Flow)。本机旧OctoScript-App-Design-Flow检出e085172不含publish-github；不要对旧CLI杜撰参数或为此重置原生运行时。

已把固定版本的tools/octo、发布模板和publisher-toolchain.json只读下载到build/semifinal-202610/release-preflight/app-flow/，核对代码后执行：

```powershell
python -X utf8 build/semifinal-202610/release-preflight/app-flow/tools/octo publish-github --help
python -X utf8 build/semifinal-202610/release-preflight/app-flow/tools/octo publish-github .
```

实际结果为installed: .github/workflows/publish-app.yml，退出码0。该命令仅安装本地工作流；既不发布，也不运行门禁/构建/视觉验收。此快照仅包含生成工作流所需文件，不是可用于完整doctor/setup的工具仓库。不要用--replace覆盖未经审查的其他工作流。

新版本地Hub位于build/semifinal-202610/release-preflight/hub-build/app-hub/target/release/hub.exe，SHA256为79478aedba6c9e2105e17c89db2bbc296c66ba0c2652a215ab0c8afccb7f904b。本机构建使用Rust1.98.1，官方workflow使用1.97.1；源码pin及锁定依赖相同，不宣称二进制逐字复现官方CI。隔离源和Cargo.lock未改，原仓库未重置。首次offline因缺sigstore缓存失败，随后通过既有代理下载依赖成功，日志均保留在hub-build目录。

## 工作流做什么

新v*标签推送触发两项作业：prepare以contents:read检出准确应用SHA及固定Hub工具链；publish取得contents:write、id-token:write、attestations:write，只用于创建证明和Release。顶层permissions为空，各checkout禁用persist-credentials；Action引用使用完整提交SHA，不使用自设publisher私钥或仓库签名secret。

流水线顺序是publisher-prepare → actions/attest → publisher-attach → publisher-verify → publisher-pack。产物是：

- app.bundle.pack.json：带GitHub证明的封装应用。
- octosense-app-manifest.json：用于证明的规范化清单。
- release-receipt.json：仓库、版本、标签、提交、run及pack_sha256。

工作流执行时不运行应用仓库的build_event_app.py，直接读取已提交的bundle。因此必须先在本地完成从src生成、测试、截图、stamp和源码导出核对，再审查并提交。不能提交旧bundle后期待CI自动构建。

当前工作流来源：[官方CLI](https://github.com/OctoSense-org/OctoSense-App-Flow/blob/049bc6b4010aa3660bab4ad632857d6ed4612151/tools/octo)、[模板](https://github.com/OctoSense-org/OctoSense-App-Flow/blob/049bc6b4010aa3660bab4ad632857d6ed4612151/tools/publish-app.template.yml)、[工具链固定版本](https://github.com/OctoSense-org/OctoSense-App-Flow/blob/049bc6b4010aa3660bab4ad632857d6ed4612151/tools/publisher-toolchain.json)。

## LICENSE如何随目标版本交付

根LICENSE会进入新提交和GitHub源码归档，但工作流只打包bundle/，不会自动把根LICENSE加入app.bundle.pack.json。主Agent已在候选0.1.1中加入同字节bundle/LICENSE.txt；两份SHA256均为上表所列标准全文摘要，未修改正文中的HTTP链接。不要使用bundle/LICENSE：官方门禁拒绝无扩展名文件。

旧本地hub实际拒绝LICENSE.txt中的Apache HTTP网址，不能把这次check记为通过。进一步逐行核对：RC2固定Hub95e4831afca7227b640f075b252c04355bb63865和发布workflow固定Hub655114c4943cd2490daaefa2173e7b5aaa20669f的gate.rs均在external_references第429–434行明确跳过普通文档链接；TXT属于允许扩展名。is_agent_file只把tools.json、skills/及manifest指定instructions视为Agent文件；当前instructions为AGENT.md，根LICENSE.txt不属于该范围。因此两目标版本源码支持原文LICENSE.txt，旧本地拒绝属于工具版本差异；仍须用准确目标Hub执行实际门禁，不把源码判断当实际通过。

依据：[RC2门禁](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/95e4831afca7227b640f075b252c04355bb63865/crates/app-hub/src/gate.rs#L429)、[发布工具链门禁](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/655114c4943cd2490daaefa2173e7b5aaa20669f/crates/app-hub/src/gate.rs#L429)、[Agent文件识别](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/655114c4943cd2490daaefa2173e7b5aaa20669f/crates/app-policy/src/agent.rs)。不得改写许可证、编码其网址、添加网络权限或伪装文件类型来通过旧扫描。

最终检查根LICENSE与bundle/LICENSE.txt哈希一致，并在新标签源码与解包后的准确发布物中分别核对。listing的Apache-2.0声明不能代替许可证文件。[官方包内容限制](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/18cd41d91b326db199fbed4129484a9ba1a8c63d/docs/PUBLISHING.md)。

## 从准备到提交的操作顺序

1. 主Agent确定新版本，统一manifest、listing发行说明、隐私版本及新标签链接；保留准确能力边界。
2. 用目标工具链构建与验证editable source。所有生成产物、许可证和截图固定后stamp/check，并scan形成8题材料；check不等于UI或官方Agent通过。
3. 完成工作流与对外正文审查。在已获得用户具体发布授权后，提交准确文件并创建推送新的v<manifest.version>标签；不复用旧标签。
4. 确认工作流成功，记录run URL、准确SHA、Release URL及三项发布附件。仓库Actions策略、公开属性及OIDC/attestation许可实际由CI验证，不在本地伪称已通过。
5. 从公开Release下载app.bundle.pack.json和release-receipt.json，在新目录解包并核对摘要、publisher proof、门禁及来源版本。已由编译出的固定Hub help确认语法：hub publisher-unpack <app.bundle.pack.json> --out <new staging directory>，再hub publisher-verify <bundle>；两者可选--catalog <authenticated catalog>。本轮未运行解包/证明验证，因为尚无新Release。
6. 用支持publisher-github-v1的准确宿主验收sealed发布物。禁止给该包重新stamp、删除证明或改字节；card-host无证明校验器，不能用它运行sealed包后宣称发行版兼容。
7. 把最终链接、截图、权限、扫描答复和真实验收记录填入 [提交草稿](SEMIFINAL_SUBMISSION_DRAFT.md)。按主办方有效入口提交并读回，记录回执时间。App Hub #113为已有参赛记录，是否补充该Issue或使用另一个赛务入口，须按有效通知处理，不自动新建重复Issue。

源码包通过、GitHub Release成功、App Hub管理员批准、目录入库及比赛提交成功是五个不同状态。没有相应记录就保留未验证。

## 发布前必须齐备的记录

- 新版本、tag、完整SHA、bundle摘要、准确宿主版本与Windows依赖。
- 官方Agent读/批准/拒绝/更正后读回/重启证据，与应用内模型记录分列。
- 根LICENSE、新版本隐私文档、模块映射、截图与实际能力一致。
- 新包下载摘要、证明验证与安装结果；旧版本与失败日志保留。
- 无个人账本、经期记录、Provider配置、token、整个build目录或历史本地数据进入提交。
- 发布者审核的具体正文和最终提交回执。

依据：[官方发布流程](https://github.com/OctoSense-org/OctoSense-App-Flow/blob/049bc6b4010aa3660bab4ad632857d6ed4612151/docs/PUBLISHING.md)、[Hub提交规范](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/18cd41d91b326db199fbed4129484a9ba1a8c63d/docs/SUBMITTING.md)。官方文档的历史RC1/旧样例证据不等于本项目在RC2 Windows验收。
