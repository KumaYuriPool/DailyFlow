"""Render timeline JSON to a PNG preview using only Pillow (no browser).

Used as a visual artifact for the demo when no headless browser is
available. Layout mirrors the HTML style but with a simple left-aligned
list. NOT the final UI; shows the time-flow idea.

Run:
    python -X utf8 tools/preview_timeline.py \
        --climb build/semifinal-202610/synthetic-source/timeline-climbing.json \
        --concert build/semifinal-202610/synthetic-source/timeline-concert.json \
        --output build/semifinal-202610/steps/DF-13/time-flow-ui/preview.png
"""

import argparse
import datetime as _dt
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def find_system_font(size):
    candidates = [
        ("C:/Users/44231/AppData/Local/Microsoft/Windows/Fonts/Alibaba-PuHuiTi-Bold.ttf", "Alibaba PuHuiTi Bold"),
        ("C:/Users/44231/AppData/Local/Microsoft/Windows/Fonts/HelloFont WenYi.ttf", "HelloFont WenYi"),
        ("C:/Windows/Fonts/segoeui.ttf", "Segoe UI"),
        ("C:/Windows/Fonts/msyh.ttc", "Microsoft YaHei"),
        ("C:/Windows/Fonts/NotoSansSC-VF.ttf", "Noto Sans SC VF"),
    ]
    for path, _ in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def fit_text(draw, text, max_width, font):
    while text and draw.textlength(text, font=font) > max_width:
        text = text[:-2]
    return text + "…" if text != "" else ""


def draw_panel(draw, x0, y0, w, title, timeline, *, title_font, body_font, small_font, accent):
    box_h = 30 + 22 + 4 + 6
    draw.rectangle([x0, y0, x0 + w, y0 + box_h], outline=(220, 220, 215))
    draw.text((x0 + 14, y0 + 10), title, fill=accent, font=title_font)
    src_y = y0 + box_h - 22
    draw.text((x0 + 14, src_y), "来源状态:", fill=(80, 80, 80), font=small_font)
    citations = timeline.get("citations", {}) if timeline else {}
    cx = x0 + 90
    for src, cit in citations.items():
        s = f"[✓ {src} {cit.get('record_count', 0)}]"
        draw.text((cx, src_y), s, fill=(40, 110, 80), font=small_font)
        cx += int(draw.textlength(s, font=small_font)) + 12
    y = y0 + box_h + 12
    if not timeline or not timeline.get("records"):
        draw.text((x0 + 14, y), "无匹配记录", fill=(140, 140, 140), font=body_font)
        return y + 28
    for rec in timeline["records"]:
        y = draw_record_card(draw, x0 + 6, y, w - 12, rec, body_font, small_font, accent)
        y += 6
    if timeline.get("gaps"):
        gy = y + 4
        draw.rectangle([x0 + 6, gy, x0 + w - 6, gy + 24 + 16 * len(timeline["gaps"])], fill=(255, 247, 214), outline=(240, 215, 112))
        draw.text((x0 + 14, gy + 4), "尚未覆盖:", fill=(138, 109, 0), font=small_font)
        for i, g in enumerate(timeline["gaps"]):
            draw.text((x0 + 90, gy + 4 + i * 16), f"· {g.get('kind', '')}: {g.get('detail', '')}", fill=(110, 80, 0), font=small_font)
        y = gy + 24 + 16 * len(timeline["gaps"])
    return y


def draw_record_card(draw, x, y, w, rec, body_font, small_font, accent):
    date = rec.get("occurred_at", "")[:16]
    title_text = rec.get("title", "")
    body = rec.get("body", "")
    kind = rec.get("kind", "")
    src = rec.get("source_app", "")
    rev = rec.get("source_revision", "")
    rid = rec.get("source_record_id", "")
    h = 64
    draw.rectangle([x, y, x + w, y + h], outline=(225, 225, 220))
    draw.text((x + 10, y + 6), date, fill=(120, 120, 120), font=small_font)
    badge_x = x + 130
    draw.rectangle([badge_x, y + 6, badge_x + 60, y + 22], fill=(217, 231, 223))
    draw.text((badge_x + 4, y + 8), kind, fill=accent, font=small_font)
    draw.text((badge_x + 70, y + 8), src, fill=accent, font=small_font)
    title_str = fit_text(draw, title_text, w - 160, body_font)
    draw.text((x + 10, y + 28), title_str, fill=(20, 20, 20), font=body_font)
    body_str = fit_text(draw, body, w - 24, small_font)
    draw.text((x + 10, y + 46), body_str, fill=(80, 80, 80), font=small_font)
    return y + h


def render(climb_timeline, concert_timeline):
    W = 1280
    padding = 24
    title_h = 50
    panel_gap = 24
    panel_w = W - 2 * padding
    accent = (47, 111, 79)
    title_font = find_system_font(20)
    h2_font = find_system_font(16)
    body_font = find_system_font(13)
    small_font = find_system_font(11)

    climb_panel = climb_timeline or {}
    concert_panel = concert_timeline or {}
    climb_h = 80 + max(len(climb_panel.get("records", [])) * 70 + (24 if climb_panel.get("gaps") else 0), 80)
    concert_h = 80 + max(len(concert_panel.get("records", [])) * 70 + (24 if concert_panel.get("gaps") else 0), 80)
    H = title_h + climb_h + concert_h + 80 + 2 * panel_gap

    img = Image.new("RGB", (W, H), (247, 247, 245))
    draw = ImageDraw.Draw(img)

    draw.text((padding, 14), "DailyFlow · 时间流（route=B 演示）", fill=accent, font=title_font)
    draw.text((padding, 38), "演示：导入合成样本 → 离线组织 → 按时间流出", fill=(120, 120, 120), font=small_font)

    y = title_h
    y = draw_panel(draw, padding, y, panel_w, "兴趣进入生活：从刷到攀岩视频到开始持续练习", climb_panel,
                   title_font=h2_font, body_font=body_font, small_font=small_font, accent=accent)
    y += panel_gap
    draw_panel(draw, padding, y, panel_w, "从官宣到散场：一次演出的等待与结束", concert_panel,
               title_font=h2_font, body_font=body_font, small_font=small_font, accent=accent)

    return img


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--climb", required=True)
    ap.add_argument("--concert", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    climb = json.loads(Path(args.climb).read_text(encoding="utf-8"))
    concert = json.loads(Path(args.concert).read_text(encoding="utf-8"))
    img = render(climb, concert)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG", optimize=True)
    print(f"[OK] preview -> {out} ({img.size[0]}x{img.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
