# App Hub Issue: route-b-2026-10-10 交付材料

**status: Draft, awaiting user review (DF-22 gate)**
**captured:** 2026-10-10T22:30:00+08:00
**route:** B (import + protocol + offline organization + offline render)
**release_label:** route-b-2026-10-10

---

## Background

DailyFlow 0.1.1 candidate 已经通过 RC2 宿主实测(`build/semifinal-202610/official-host/real-agent-r1/*`)。复赛剩余时间(截至 2026-10-13 24:00 Beijing)内,本次采用**路线 B**对"Agent 组织跨来源个人经历"做了完整 end-to-end 离线可复现 evidence。

详细:
- 路线决策: `docs/execution-state.json` `route=B`,依据 `SEMIFINAL_PLAN.md §三条交付路线`
- 与历史 0.1.0 release 关系: DailyFlow bundle 保持 0.1.1 unsigned 不变;本次新增 `route-b-2026-10-10` 是 **离线 evidence 包**,作为 0.1.1 candidate 的复赛支持材料

## 核心交付 (本包内)

- `e2e-report.json` — 16/16 checks pass
- `freshness-report.json` — 5/5 checks pass
- `resilience-report.json` — 6/6 checks pass
- `v1-contract-report.json` — 4/4 fixture pass
- `timelines.html` — 可在浏览器直接打开的两场景时间流(含来源状态、关联 candidate、缺口面板)
- `preview.png` — Pillow PNG 时间流预览(无图片)
- `preview-with-media.png` — 含三张合成图片(攀岩三段)的时间流预览
- `timeline-climbing-applied.json` — 用户 confirm/exclude 后的应用 timeline
- `timeline-concert.json` — 演出 timeline
- `relations-climbing-decided.json` — 用户决策覆盖
- `EXTERNAL_SOURCE_CONTRACT.md` — v1 冻结 wire 契约(身份/修订/墓碑/分页)
- `INTERACTION_MATRIX.md` — UI 状态机与失败可见性合约
- `handoff-df{11,12,15,16,17,20}.md` — 6 个关键步骤交接文档
- `baseline.json` — DF-01 工作区基线(SHA + commit)

## 设计要点

1. **Agent 选源而非手挑**:用户问"我是怎么从刷到攀岩视频到开始持续练习的?",Agent 读 `experiments/synthetic-source/catalog.json` 能力目录,匹配 "攀岩 → bouldering" → 选 `synthetic-climbing` + `synthetic-calendar` + `synthetic-expense`。多源协同,**两场景**共享同一代码路径,不在 prompt/UI 硬编码答案。

2. **可信事件接入**:`v1 contract` 冻结(source_app + record_id + revision + content_hash + tombstone),不信任 payload 自称 app_id。

3. **可核验时间流**:每条记录带 stable source_record_id @ revision,UI 与源 detail 可回查。`timeline_query` 字段对齐 DailyFlow 已有 `08_time_protocol` 表面。

4. **关联候选 confirm/exclude**:8 条候选根据 tag/date proximity 列出,用户决策后只标记本地视图,不写源。`applied timeline` 输出链路证明。

5. **失败可见**:source closed / tombstone / 部分结果 / 零结果 / 强歧义 都在 `INTERACTION_MATRIX.md` 显式可见。

## 与初赛 75 分评语(#113)的关系

#113 评语指出:
> Apache-2.0 LICENSE 已补,dailyflow.* 工具在官方宿主执行验收,src 到 build_event_app.py 模块对应文档,GitHub 发布流程与版本号提高。

本次回应:
- ✅ LICENSE 仍在 bundle/APACHE 全文(`bundle/LICENSE.txt` SHA 一致)
- ✅ dailyflow.* 工具在 RC2 宿主执行验收已记录(DF-01 baseline / 既有 evidence)
- ✅ 模块地图(`docs/MODULE_MAP.md`)已准备
- ✅ GitHub 发布流程准备 (`docs/GITHUB_RELEASE_PREFLIGHT.md`)
- ✅ 版本号澄清:`route-b-2026-10-10` 是本次路线 evidence 的 release label,与 `v0.1.0` 公开 release 共存

## 不在本次提交中

- 不重新发布 bundle(Splash 包仍为 0.1.1)
- 不修改 RC2 host / Hub / Makepad
- 不动 Provider profile 或个人业务数据
- 不提交修复 host issue(DF-18 deferred,no decisive probe finding)
- 不创建独立记账 App(DF-19 deferred 到赛后)

## 路线选择与边界

为什么不走 route=A(真实接入):RC2 `Catalog::owner_of` 固定 `os.<ns>` 解析,任何 store app 互通需绕过该设计或假设上游修复;不在本次比赛时间盒内可达(详见 DF-03)。

为什么不走 route=C(已验证核心):本路线 B 已能 end-to-end 输出 evidence,不退回到单独演示已通过的工具集;路线 C 会削弱本次产品展示(详见 DF-27)。

## 后续

- 12 日 12:00 功能冻结 → 13 日 12:00 提交读回。本材料已存在,无需额外提交源代码改动。
- App Hub 维护者引用时,可直接看 zip 内 20 个文件 + `docs/INTERACTION_MATRIX.md` 即可复现。
- 仍需用户授权发送 / 创建新 GitHub Issue / Release(不在本轮自动执行)。

## 文件清单 / SHA256

详见 `route-b-2026-10-10.zip` 内 `PACKAGE_README.md`,ZIP SHA256 `be1d56ad32b41ae9f363183bfc03df25274049b866c5ad86f5575c53923b980a`（2026-10-12 r5/r6 回归修复后重建，supersedes `2cc1f443…` 与 `ea635a2a…`；包内 `handoff-r5-r6.md` 说明差异）。bundle: main.splash SHA256 `550f18f7e595be1f10979209f04133e81da24f88bfbad708b0b85ab0de294b9f`,manifest bundle_blake3 `3786f45906574d8909af430fccdb6ae807c84d8ad1ee86a6eb79733a9d301347`。
