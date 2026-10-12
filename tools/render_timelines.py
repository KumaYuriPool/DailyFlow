"""Render timeline.json outputs as a single HTML demo page.

Reads two timeline files (climbing + concert) and renders them following
INTERACTION_MATRIX.md v1 contract.

Run:
    python -X utf8 tools/render_timelines.py \
        --climb build/semifinal-202610/synthetic-source/timeline-climbing.json \
        --concert build/semifinal-202610/synthetic-source/timeline-concert.json \
        --output build/semifinal-202610/steps/DF-13/time-flow-ui/timelines.html
"""

import argparse
import html
import json
from pathlib import Path


def render_record_card(r):
    media = []
    for m in r.get("media", []):
        media.append(
            f'<div class="media-placeholder">📷 {html.escape(m.get("media_id", ""))}'
            f'<span class="media-meta">{html.escape(m.get("mime", ""))} · {m.get("size_bytes", 0)} B</span></div>'
        )
    media_html = "\n".join(media) if media else ""
    tags_html = " ".join(
        f'<span class="tag">{html.escape(t)}</span>' for t in r.get("tags", [])
    )
    citation = r.get("citation", "") or ""
    if citation:
        citation = f'<a class="citation" href="#" data-source="{html.escape(citation)}">{html.escape(citation)}</a>'
    return f"""
<div class="row" data-source-app="{html.escape(r.get('source_app', ''))}" data-record-id="{html.escape(r.get('source_record_id', ''))}">
  <div class="date">{html.escape(r.get('occurred_at', ''))}</div>
  <div class="card">
    <div class="card-head">
      <span class="kind kind-{html.escape(r.get('kind', ''))}">{html.escape(r.get('kind', ''))}</span>
      <span class="topic">{tags_html}</span>
      <span class="src">{html.escape(r.get('source_app', ''))}</span>
    </div>
    <div class="title">{html.escape(r.get('title', ''))}</div>
    <div class="body">{html.escape(r.get('body', ''))}</div>
    <div class="ref">引用: {html.escape(r.get('source_record_id', ''))} rev {r.get('source_revision', '')} {citation} <a class="open-detail" href="#" data-id="{html.escape(r.get('source_record_id', ''))}">[明细]</a></div>
    {media_html}
  </div>
</div>
"""


def render_panel(title, timeline, scenario_id):
    if not timeline or not timeline.get("records"):
        return f"<section class='scenario'><h2>{title}</h2><div class='empty'>无匹配记录</div></section>"

    citation = timeline.get("citations", {})
    src_rows = []
    for src, cit in citation.items():
        src_rows.append(
            f'<li><span class="src-name">{html.escape(src)}</span> · {cit.get("record_count", 0)} 条 · 最后读取 {cit.get("fetched_at_window", ["",""])[0] or "—"}</li>'
        )

    cards = "\n".join(render_record_card(r) for r in timeline["records"])

    gap_html = ""
    if timeline.get("gaps"):
        rows = "".join(f"<li><strong>{html.escape(g.get('kind', ''))}</strong>: {html.escape(g.get('detail', ''))}</li>" for g in timeline["gaps"])
        gap_html = f"<div class='gaps'><h4>尚未覆盖</h4><ul>{rows}</ul></div>"

    return f"""
<section class="scenario" id="scenario-{scenario_id}">
  <h2>{html.escape(title)}</h2>
  <div class="source-status">
    <strong>来源状态</strong>
    <ul>{"".join(src_rows)}</ul>
    <small>adoption_layer: v1-import (route=B)</small>
  </div>
  <div class="timeline">
    {cards}
  </div>
  {gap_html}
</section>
"""


def render_page(climb_timeline, concert_timeline):
    climb_panel = render_panel(
        "兴趣进入生活：从刷到攀岩视频到开始持续练习",
        climb_timeline,
        "climbing",
    )
    concert_panel = render_panel(
        "从官宣到散场：一次演出的等待与结束",
        concert_timeline,
        "concert",
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>DailyFlow 时间流（route=B 演示）</title>
<style>
  :root {{
    --bg: #f7f7f5;
    --card: #ffffff;
    --ink: #1d1d1b;
    --ink-soft: #5c5c57;
    --accent: #2f6f4f;
    --border: #e3e3df;
    --tag: #d9e7df;
    --gap: #fff7d6;
    --gap-ink: #8a6d00;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px; background: var(--bg); color: var(--ink); font: 14px/1.5 "PingFang SC", "Noto Sans CJK SC", system-ui, sans-serif; }}
  h1 {{ margin: 0 0 12px; font-size: 22px; }}
  h2 {{ margin: 24px 0 12px; font-size: 17px; color: var(--accent); }}
  h4 {{ margin: 0 0 6px; font-size: 13px; color: var(--gap-ink); }}
  .meta {{ color: var(--ink-soft); font-size: 12px; margin-bottom: 16px; }}
  .scenario {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 18px 22px; margin-bottom: 24px; }}
  .source-status {{ background: #fafaf7; border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; margin-bottom: 18px; font-size: 13px; }}
  .source-status ul {{ list-style: none; padding: 0; margin: 6px 0; }}
  .source-status li {{ padding: 2px 0; color: var(--ink-soft); }}
  .source-status .src-name {{ color: var(--ink); font-weight: 600; }}
  .timeline .row {{ display: flex; gap: 14px; padding: 10px 0; border-bottom: 1px dashed var(--border); }}
  .timeline .row:last-child {{ border-bottom: 0; }}
  .timeline .date {{ width: 130px; flex-shrink: 0; color: var(--ink-soft); padding-top: 4px; font-variant-numeric: tabular-nums; }}
  .timeline .card {{ flex: 1; }}
  .timeline .card-head {{ display: flex; gap: 8px; align-items: center; font-size: 12px; color: var(--ink-soft); margin-bottom: 2px; }}
  .timeline .kind {{ background: #dde6dd; color: var(--accent); padding: 1px 6px; border-radius: 3px; font-weight: 600; }}
  .timeline .kind-expense {{ background: #fce4dc; color: #a63716; }}
  .timeline .kind-event_fact, .timeline .kind-event_plan {{ background: #dde0ef; color: #2e3e8e; }}
  .timeline .kind-image {{ background: #efe1de; color: #6d402b; }}
  .timeline .topic {{ display: inline-flex; gap: 4px; }}
  .timeline .tag {{ background: var(--tag); color: var(--accent); padding: 1px 6px; border-radius: 3px; font-size: 11px; }}
  .timeline .src {{ font-weight: 600; color: var(--accent); }}
  .timeline .title {{ font-size: 15px; font-weight: 600; margin: 1px 0 3px; }}
  .timeline .body {{ color: var(--ink-soft); }}
  .timeline .ref {{ font-size: 11px; color: var(--ink-soft); margin-top: 3px; }}
  .timeline .citation {{ color: var(--accent); text-decoration: underline; }}
  .timeline .open-detail {{ color: var(--accent); margin-left: 4px; }}
  .timeline .media-placeholder {{ margin-top: 6px; padding: 8px 10px; background: #f0eee7; border: 1px solid var(--border); border-radius: 4px; color: var(--ink-soft); font-size: 12px; display: flex; gap: 10px; align-items: center; }}
  .timeline .media-placeholder .media-meta {{ color: #999; }}
  .gaps {{ background: var(--gap); border: 1px solid #f0d770; border-radius: 6px; padding: 8px 14px; margin-top: 18px; font-size: 13px; }}
  .gaps ul {{ padding-left: 18px; margin: 4px 0; }}
  .empty {{ color: var(--ink-soft); padding: 18px; text-align: center; background: #fafaf7; border-radius: 6px; }}
  footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border); color: var(--ink-soft); font-size: 12px; }}
  footer code {{ background: #efefe9; padding: 1px 4px; border-radius: 2px; }}
</style>
</head>
<body>
  <h1>DailyFlow · 时间流</h1>
  <div class="meta">
    演示：route=B（导入合成样本，离线组织）。点击问题 → 看到两组并排时间流。
    数据来源：v1 contract，adoption_layer 标记为 offline import。
  </div>
  {climb_panel}
  {concert_panel}
  <footer>
    本页由 <code>tools/render_timelines.py</code> 渲染自 organizer 输出。规格见
    <code>docs/INTERACTION_MATRIX.md</code>。
  </footer>
</body>
</html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--climb", required=True)
    ap.add_argument("--concert", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    climb = json.loads(Path(args.climb).read_text(encoding="utf-8"))
    concert = json.loads(Path(args.concert).read_text(encoding="utf-8"))

    html_doc = render_page(climb, concert)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_doc, encoding="utf-8")
    print(f"[OK] rendered {len(climb.get('records', []))} climb + {len(concert.get('records', []))} concert records -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
