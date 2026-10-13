# 阶段 A 基线核对（NF-00）

核对已完成；这不是最新运行时 E2E 通过报告。北京时间 2026-10-12T23:41:43.868546+08:00，24 个直接/工具仓库和 5 个传递 Git 来源均联网读回。初次沙箱代理失败日志保留，随后只读网络请求成功。

| 仓库 | 当前/锁定 | 本次上游 | 结论 |
| --- | --- | --- | --- |
| OctoSense-org/OctoSense-App-Hub | `386359153ed6` | `386359153ed6` | 相同 |
| OctoSense-org/OctoSense.git | `f07541348ee5` | `37eb1e23a54c` | 已变化 |
| OctoSense-org/Octoscript-Makepad.git | `6cf2d90aa33f` | `6cf2d90aa33f` | 相同 |
| OctoSense-org/Octoscript.git | `b57c726dacfa` | `b57c726dacfa` | 相同 |
| OctoSense-org/makepad.git | `10f1102f65cf` | `10f1102f65cf` | 相同 |
| Project-Robius-China/makepad-diagram-kit.git | `0536492116e5` | `0536492116e5` | 相同 |
| Project-Robius-China/streaming-markdown-kit.git | `68b8cdf91ea7` | `68b8cdf91ea7` | 相同 |
| hagency-org/Rinx.git | `f42df668b8c5` | `f42df668b8c5` | 相同 |
| octos-org/octos.git | `c2e1c575f589` | `69202ad72b3b` | 已变化 |
| octos-org/octoscode-app.git | `d47fade94498` | `d47fade94498` | 相同 |
| project-robius/robius | `aea7a4fc3d50` | `aea7a4fc3d50` | 相同 |
| ymote/cadcraft.git | `59631c8d4f9f` | `59631c8d4f9f` | 相同 |
| ymote/deckcraft.git | `d0e57d7e25f9` | `d0e57d7e25f9` | 相同 |
| ymote/designcraft.git | `14e677b24216` | `14e677b24216` | 相同 |
| ymote/effectcraft.git | `d60cb71e297a` | `d60cb71e297a` | 相同 |
| ymote/filmcraft.git | `523185244336` | `523185244336` | 相同 |
| ymote/gridcraft.git | `c6b6f4177cbf` | `c6b6f4177cbf` | 相同 |
| ymote/lightcraft.git | `2472021091a2` | `2472021091a2` | 相同 |
| ymote/pdfcraft.git | `51f09eea27c5` | `51f09eea27c5` | 相同 |
| ymote/photocraft.git | `eec4af65513b` | `eec4af65513b` | 相同 |
| ymote/soundcraft.git | `c51e5d5ec52f` | `c51e5d5ec52f` | 相同 |
| ymote/vectorcraft.git | `2cd3a1ca8fbc` | `2cd3a1ca8fbc` | 相同 |
| ymote/wordcraft.git | `7584b9b2930f` | `7584b9b2930f` | 相同 |
| OctoSense-org/OctoScript-App-Design-Flow.git | `15b1da01a769` | `d0344682df7c` | 已变化 |
| ZhangHanDong/rusty-mermaid.git（传递，HEAD） | `68a429b0472d` | `68a429b0472d` | 相同 |
| matrix-org/matrix-rust-sdk（传递，HEAD） | `6892cb217ae4` | `f6224e177f7e` | 落后 |
| matrix-org/vodozemac（传递，HEAD） | `cfc4eeebdf09` | `70ad23e8cbb1` | 落后 |
| project-robius/ruma.git（传递，refs/heads/tsp） | `7a912c857987` | `b9e54dccfd2d` | 落后 |
| storytold/filmcraft（传递，HEAD） | `2c5ba7a72619` | `0879bd7a7e89` | 落后 |

## 增量构建决定

必须更新、评估并增量构建后再作全最新声明。本阶段不启动冷构建，也不替换当前已验收 exe。H 获唯一运行时准备权：先读本报告及 baseline 中的 compare JSON，隔离导出实际源码与完整补丁，迁移到新提交，利用现有缓存单线构建并产生新的私有 manifest。不得直接修改/覆盖共享运行时或冻结 manifest；在 H 交付中给升级清单与新哈希，I 阶段 B 选择并复验。

- Shell f0754134 → 37eb1e23：仅 ADR 文档变化（真实 compare）；源码版本仍需更新并记录，不能把旧 exe 的 revision 改写成新构建。
- 内核 c2e1c575 → 69202ad7：agent convergence/compaction、context journal、session actor 等实际代码改变，必须新编译与回归；Shell 对 octos 的实际依赖一并检查，不能只换旁边 kernel.exe。
- App Flow 15b1da01 → d0344682：tools/octo 与文档/AGENTS 更新；隔离更新时先读新 AGENTS。不要运行 setup 去重置 dirty tree。
- matrix-rust-sdk、vodozemac、project-robius/ruma 的 tsp 分支、storytold/filmcraft 的锁定版本落后（见矩阵），H 必须评估全最新兼容性并记录；不能沿用“全部最新”旧标题。rusty-mermaid 未变。OHOS nix 的历史 vendor 路径是兼容制品，不是运行内核。
- 现有四二进制实际 SHA256 均匹配旧 manifest；七个核心源码树 HEAD、git diff 与已记录补丁均匹配。新增构建若失败应保留可诊断错误，标记新运行时受阻；U/S 可用冻结旧组合进行明确标记的局部开发，最终最新验收不通过。

## 保护与非发布边界

Hub Cargo.lock、生产 main/manifest 与本次开工摘要一致。主 Makepad HEAD=10f1102f 当前工作树 clean；d3d11.rs 的 redraw_all 位于1042行，本次文件哈希 bf53a160… 与上午升级前记录不同，不应错误还原上午旧文件。当前实现及全部历史补丁保持不动。

保留 card-host 首卡 ABI 修复、Shell 官方 overlay、本地依赖重定向、Rinx 移除 palpo catalog 补丁和回退说明。旧 native-apps tag-only 与 setup 固定 pin 两项官方门槛仍未通过；此为本地组合，不是官方发行包。

个人数据仅在主证据目录记录摘要，未复制内容到快照；1637个可读文件已摘要，latest-desktop/.launcher.lock 无法读取，记录为未触碰，不声称已做内容哈希。Provider/授权未复制、不打印、不修改。实际进程见 process-inventory.json；历史 process.json 不能当存活证据。

## 下一步

用户分别启动 U/S/H 的 START.md。H 先作运行时升级评估与 NF-03/04 风险探针，U/S 先实现离线部分。任何旧运行时探针必须写 runtime_latest=false，不能直接满足“当次最新”的最终门槛。新上游再漂移时提交 H/runtime-update.json，由 I 合流处理。
