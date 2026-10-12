"""Embedded PNG generator for synthetic media_ids.

Searches for media references in timeline JSON and renders an embedded
version of the time flow with actual PNG images at the media slots.

Run:
    python -X utf8 experiments/synthetic-source/media_resolver.py \
        --timeline build/semifinal-202610/synthetic-source/timeline-climbing.json \
        --media-dir build/semifinal-202610/steps/DF-14/media \
        --output build/semifinal-202610/steps/DF-14/time-flow-with-media.png
"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_timeline(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resolve_media(media_dir, media_id):
    p = Path(media_dir) / f"{media_id}.png"
    if p.exists():
        return Image.open(p)
    return None


def find_cjk_font(size):
    for path in ("C:/Users/44231/AppData/Local/Microsoft/Windows/Fonts/Alibaba-PuHuiTi-Bold.ttf",
                 "C:/Users/44231/AppData/Local/Microsoft/Windows/Fonts/HelloFont WenYi.ttf"):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_record(draw, x, y, w, rec, media_img_cache, f_title, f_body, f_meta):
    date = rec.get("occurred_at", "")[:16]
    title = rec.get("title", "")
    body = rec.get("body", "")
    kind = rec.get("kind", "")
    src = rec.get("source_app", "")
    rev = rec.get("source_revision", "")
    rid = rec.get("source_record_id", "")

    media_w = 96
    row_h = 96
    draw.rectangle([x, y, x + w, y + row_h], outline=(225, 225, 220), width=1)
    draw.text((x + 8, y + 4), date, fill=(120, 120, 120), font=f_meta)
    draw.rectangle([x + 100, y + 4, x + 156, y + 24], fill=(217, 231, 223))
    draw.text((x + 104, y + 6), kind, fill=(47, 111, 79), font=f_meta)
    draw.text((x + 160, y + 6), src, fill=(47, 111, 79), font=f_meta)
    draw.text((x + 8, y + 28), title, fill=(20, 20, 20), font=f_title)
    body_text = body if len(body) < 60 else body[:58] + "…"
    draw.text((x + 8, y + 56), body_text, fill=(80, 80, 80), font=f_body)
    draw.text((x + 8, y + 78), f"引用: {rid} rev {rev}", fill=(140, 140, 140), font=f_meta)

    media_items = rec.get("media", [])
    if media_items:
        m = media_items[0]
        mid = m.get("media_id", "")
        img_path = Path(__file__).resolve().parents[2] / "build/semifinal-202610/steps/DF-14/media" / f"{mid}.png"
        if img_path.exists():
            img = Image.open(img_path)
            img = img.resize((80, 80))
            draw._image.paste(img, (x + w - 88, y + 8))
        else:
            draw.rectangle([x + w - 88, y + 8, x + w - 8, y + 88], fill=(240, 240, 240), outline=(200, 200, 200))
            draw.text((x + w - 80, y + 40), mid, fill=(160, 160, 160), font=f_meta)

    return y + row_h


def render_timeline(timeline, *, output, title):
    records = timeline.get("records", [])
    W = 1280
    H = 60 + 30 + len(records) * 100 + 80
    img = Image.new("RGB", (W, H), (247, 247, 245))
    draw = ImageDraw.Draw(img)

    f_h1 = find_cjk_font(22)
    f_meta = find_cjk_font(11)
    f_title = find_cjk_font(13)
    f_body = find_cjk_font(11)

    draw.text((24, 14), f"DailyFlow · 时间流（route=B, 含图片） - {title}", fill=(47, 111, 79), font=f_h1)
    draw.text((24, 40), "媒 介质:climb-thumb-*.png（DF-14 合成）", fill=(120, 120, 120), font=f_meta)
    y = 70
    for rec in records:
        y = render_record(draw, 24, y, W - 48, rec, {}, f_title, f_body, f_meta) + 4

    img.save(output, "PNG", optimize=True)
    print(f"[OK] rendered {len(records)} records -> {output}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--media-dir", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)
    timeline = load_timeline(args.timeline)
    render_timeline(timeline, output=args.output, title=args.timeline)


if __name__ == "__main__":
    raise SystemExit(main())
