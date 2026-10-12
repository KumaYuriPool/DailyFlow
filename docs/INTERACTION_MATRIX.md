# Visible Interaction Spec & State Matrix

2026-10-11：新版经历界面及Agent接入目标见[经历界面与 Agent 交互设计](UX_AGENT_INTERACTION_DESIGN.md)。本页保留旧route=B实验规格；旧frozen状态不表示第二版HTML界面、官方Agent回流或新增任务流程已实现。

**status: frozen for v1 (route=B shipping)**
**frozen_at: 2026-10-10T22:30:00+08:00**
**owner: main-agent**
**supersedes: n/a; first issue of this document**
**applies_to: DailyFlow route=B demo UI; offline / runtime agnostic**

## Purpose

This document fixes the **visible** interaction set for the route=B demo, so reviewers can replay every transition without inspecting code. It is intentionally minimal and aligned with `docs/PRODUCT_SPEC.md` §3 + §7.

The implementation in this round is offline-rendered Markdown, not the live Splash UI. The state semantics, panel names and rules are identical; only the rendering substrate differs.

## States

| State | Display | Allowed Transitions |
|---|---|---|
| `idle` | greeting + chevron/placeholder | enter `typing` (user taps composer) |
| `typing` | composer focused; dropdown hidden | enter `submitting` (user taps send) |
| `submitting` | composer disabled; spinner near composer | enter `clarifying`, `loading`, `error` |
| `clarifying` | clarification panel visible (multi-choice chips) | enter `submitting` (user picks) / `idle` (user dismisses) |
| `loading` | "正在读取授权来源" + small per-source indicators | enter `loaded`, `partial`, `error` |
| `loaded` | timeline panel + source status bar (all green) | enter `selecting-source` / `correcting` / `refresh` |
| `partial` | timeline panel + source status bar (some red) | enter `selecting-source` / `refresh` |
| `error` | failure card with reason; "再试" / "换路径" buttons | enter `submitting` (retry) / `idle` |
| `selecting-source` | per-source row taps toggle included/excluded | enter `loaded` / `partial` |
| `correcting` | detail view in "candidate relation" mode | enter `loaded` |
| `refresh` | in-flight spinner per selected source | enter `loaded` / `partial` / `error` |

## Panel contract

### Source status bar

Always visible when state ∈ {loaded, partial, refreshing, correcting}.

```
来源状态  [✓ synthetic-climbing  3] [✓ synthetic-calendar  1] [✓ synthetic-expense  2] [+]
                最后读取 14:30                最后读取 14:30                最后读取 14:30
```

- tick + count: source enabled, N records returned
- ✗ / 红色: source failed or excluded
- last-read timestamp: from envelope `fetched_at`
- "+": add another synthetic-source (admin only)

### Timeline panel

```
时间流
─────────────────────────────────────────────────────────────────────────────
2026-09-12  社媒｜攀岩｜[synthetic-climbing]       标题: B 站的攀岩入门视频（已收藏）
              配文: 周末已入馆体验，准备约下一次。
              引用: climb-post-001 rev 2     [明细]
─────────────────────────────────────────────────────────────────────────────
2026-09-13  体验｜抱石｜[synthetic-calendar]      标题: 抱石体验课
              时间: 15:00–17:00
              引用: evt-climb-001 rev 1       [明细] [关联: 已发生]
─────────────────────────────────────────────────────────────────────────────
```

Each card shows: date / kind / topic / source-app / title / body excerpt / stable record id + revision / [detail] / [source detail].

### Gap panel

Visible when `timeline.gaps` is non-empty.

```
尚未覆盖
- 每周练习频率：没有数据；需要用户提供或保留未知
```

UI does not invent: when user supply is missing, panel says "数据中没有，下次回答时补充即可".

### Detail panel

```
来源明细
  source_app      synthetic-climbing
  source_module   post
  record_id       climb-post-001
  revision        2
  occurred_at     2026-09-12
  title           B 站的攀岩入门视频（已收藏）
  body            周末已入馆体验，准备约下一次。
  tags            bouldering, first-visit
  media           climb-thumb-001 (image/png, 81920 bytes, syn-licensed)
```

No "edit source value" affordance; users can only **associate** (claim relation) or **exclude** (drop from current query view). Source writes remain read-only.

### Candidate relation panel (correcting state)

```
关联候选
- evt-climb-001 (体验课 2026-09-13) ⓘ来自 synthetic-calendar
  ✓ 体验与 climb-post-002 同一活动
  ✗ 不关联
```

User taps confirm/exclude. Affirmations don't alter source records; exclusions only hide from current query view.

## Failure mode visibility

| Failure | Display |
|---|---|
| source closed | row "✗ 不可访问" + reason "对方应用未启动或已下架" |
| tombstone appears | row removed from timeline; if previously shown, hide with note "该来源已删除" |
| picture unavailable | placeholder with media_id; body still visible |
| partial result | row count says "已读 X/Y"; missing items collapsed under "未读" |
| empty result | empty timeline; bottom panel says "无匹配记录" (NO 假 zero-result) |
| ambiguous match (>=2 strong candidates) | clarification chips appear |

## Cancellation

- `submitting` → `idle` is allowed (cancel mid-request)
- After cancel, late results from the model do NOT overwrite the new request (0.5.6 contract holds)
- Composer must remain responsive within 200 ms after cancel acknowledgement

## Refresh

- `refresh` triggers re-fetch by snapshot_revision; old records kept until new fetch returns
- New envelope must satisfy DF-05 contract and DF-09 idempotence
- Errors return to `partial` (with the source marked ✗) not `idle`

## What this matrix does NOT cover

- Cross-source link click-and-jump: deferred (route=B has no live cross-app)
- Multi-currency aggregation: not implemented in v1
- Authoring from detail panel: out of v1 scope
- Inline picture preview if image is local-resource-allowed: implementation deferred until DF-14

## Companion JSON contract

For automated rendering, the timeline payload conforms to the form produced by `experiments/synthetic-source/organizer.py`:

```
{
  "tool": "dailyflow.timeline_organize",
  "contract_version": 1,
  "selection": {...},
  "topic": "...",
  "records": [...],
  "citations": {...},
  "gaps": [...],
  "audit": {...}
}
```

Renderers MUST NOT add fields; they MUST NOT silently drop `gaps`; they MUST display `citations` keys per row.
