# DailyFlow v0.2.0 提交审阅答案

适用版本：v0.2.0（候选 release）
提交日期：2026-10-13
完整提交流程见 [SUBMISSION_v0.2.0.md](https://github.com/KumaYuriPool/DailyFlow/blob/v0.2.0/docs/SUBMISSION_v0.2.0.md)

## 1. 提交状态

- Release status: **pending**（等待跨 App 读桥上游 PR 合并后正式发布）
- App id: `dailyflow`（主应用）/ `dailyflow-ledger`（伴生独立记账 App）
- Version: `0.2.0`

## 2. 仓库与版本

- 仓库 URL: https://github.com/KumaYuriPool/DailyFlow
- Tag: `v0.2.0`（已推）
- Full commit SHA: `12015a86e4d546ce2d50ebda3d1f2c2cde328a1a`
- Bundle path: `bundle/`
- GitHub workflow run URL: 见 `.github/workflows/publish-app.yml`，**待 push tag 触发后填入**
- Release and pack URL: **pending**（跨 App 读桥未合并前，官方 App Hub 的 pack workflow 会被 requires 拒绝）
- Release pack SHA256: **pending**

## 3. Bundle 完整性

- Bundle BLAKE3 digest: `530ca299764d16c0ada99b0f84e38a6b2805051b4d55a1ce519ead2e29a7c43d`
- hub stamp digest: `530ca299764d16c0ada99b0f84e38a6b2805051b4d55a1ce519ead2e29a7c43d`

## 4. Gate 与 publisher 验证输出

完整 GATE 输出见 [review/GATE.txt](GATE.txt)。

`hub check bundle` 结果（节选）：
```
dailyflow 0.1.1 — PASSED
  [warning] publisher-signature: unsigned: accountability rests on the hub alone
  [warning] tools: dailyflow.save_record is destructive: every call waits for the host's approval
  [warning] tools: dailyflow.apply is destructive: every call waits for the host's approval
  declarations: capabilities {"app_tools", "model", "octos.turn.interrupt", "octos.turn.start", "storage"}, hosts {}, storage 16777216 bytes, agent workspace-write
```

App Hub revision：当前使用 `H/runtime-work/candidate/shell/.sources/app-hub` 树（HEAD = 386359153ed6377b5f047bd9ed2767a6a2ac2bc7）。

## 5. 平台与运行时

- 平台：Windows
- 运行时：OctoSense Shell（`0476df1f3aadf33f28104e69f99240f1693bac7b751f0b25b19b878da3ac6de0`，源码 ffd5e488）+ Kernel（`4e72bc7d…`，源码 d7a2e3a0）+ Hub/Card-host 同步。完整运行时清单见 [runtime-final-r1.json](../build/overnight-20261013/integration-r1/runtime-final-r1.json)
- 实际验收运行在**本地修补运行时**上；非官方发行组合。详见下文第 8 条。

## 6. 隐私与支持

- 隐私 URL: https://github.com/KumaYuriPool/DailyFlow/blob/v0.2.0/PRIVACY.md
- 支持方式: https://github.com/KumaYuriPool/DailyFlow/blob/v0.2.0/SUPPORT.md

## 7. 截图

7 张 1280x900 与 412x892 截图已在 `bundle/screenshots/` 目录，由 `bundle/listing.json` 引用。

## 8. What is not verified（如实披露）

跨 App 数据读取依赖我们为 OctoSense 平台新增的 `app_tools` 安全读桥（only-read 保障、双方授权校验、身份绑定、授权纪元、撤权感知）。本组合 manifest 声明 `requires: cross-app-read-v1`——**此字符串尚未在官方 App Hub 合约的已知清单中**。原因：读桥实现（`crates/shell/src/host_tools/read_bridge.rs`）是我们为 OctoSense 平台的新增文件，**上游 main 尚未包含**（已核实 git cat-file：ffd5e488 主线无此文件）。本 PR 材料已完整就绪（commit 232dcb53，8 文件 +364/-11，3 次 cargo check + 测试通过，PR agent 交付 `build/upstream-bridge-pr-r1/`），由维护者评审合并后官方宿主才能识别 `cross-app-read-v1`，本组合才能完成 App Hub 发行流程的 pack workflow。

官方发行门槛（native-apps 标签规则、setup 固定 pin）未通过。本组合**不是官方发行包**；本仓库 v0.2.0 标签的 release 是**集成候选**而非商店发行版。

## 9. Confirmations

- [x] 提交材料不含密钥、API token 或未经遮盖的私人截图
- [x] tag `v0.2.0` 一旦发布不可移动、删除或重建（当前状态：本仓库主分支标签已推）
- [x] 仓库根目录有 `.gitattributes`（`bundle/** -text`）防止 checkout/checkin 转换破坏 bundle 字节
- [x] 提交的所有"待补充 / pending"字段都标了真实状态，未伪造 pass
