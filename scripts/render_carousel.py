#!/usr/bin/env python3
"""post.json からカルーセル画像 (1080x1350 PNG) を生成する。

使い方: python3 scripts/render_carousel.py content/queue/<id> [<id> ...]
"""
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BRAND = json.loads((ROOT / "config/brand.json").read_text(encoding="utf-8"))
D = BRAND["design"]
W, H = D["size"]
M = 96  # 左右マージン

BOLD_CANDIDATES = [
    os.environ.get("FONT_BOLD", ""),
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
]
REG_CANDIDATES = [
    os.environ.get("FONT_REGULAR", ""),
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]


def find_font(cands):
    for c in cands:
        if c and Path(c).exists():
            return c
    sys.exit("日本語フォントが見つかりません。FONT_BOLD / FONT_REGULAR を設定してください")


FB, FR = find_font(BOLD_CANDIDATES), find_font(REG_CANDIDATES)


def font(path, size):
    return ImageFont.truetype(path, size)


# 行頭に来てはいけない文字（簡易禁則）
NO_START = set("、。，．・：；？！ー）」』】〕〉》’”ぁぃぅぇぉっゃゅょァィゥェォッャュョ")


def wrap(draw, text, fnt, max_w):
    """日本語向けに文字単位で折り返す。明示的な \\n は尊重。"""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if draw.textlength(cur + ch, font=fnt) <= max_w or not cur:
                cur += ch
            elif ch in NO_START:
                cur += ch  # ぶら下げ
            else:
                lines.append(cur)
                cur = ch
        lines.append(cur)
    return lines


def draw_lines(draw, lines, fnt, x, y, fill, spacing=1.45, center=False):
    lh = int(fnt.size * spacing)
    for ln in lines:
        if center:
            tw = draw.textlength(ln, font=fnt)
            draw.text(((W - tw) / 2, y), ln, font=fnt, fill=fill)
        else:
            draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def footer(draw, idx, total, dark=False, color=None):
    f = font(FR, 30)
    color = color or ("#AAAAAA" if dark else D["sub"])
    draw.text((M, H - 90), BRAND["account"]["handle"], font=f, fill=color)
    page = f"{idx}/{total}"
    draw.text((W - M - draw.textlength(page, font=f), H - 90), page, font=f, fill=color)


def render_cover(s, idx, total):
    img = Image.new("RGB", (W, H), D["cover_bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([M, 310, M + 120, 324], fill=D["accent"])
    title_f = font(FB, 100)
    y = draw_lines(d, wrap(d, s["title"], title_f, W - 2 * M), title_f, M, 380, D["cover_text"], 1.35)
    if s.get("subtitle"):
        sub_f = font(FB, 40)
        y += 40
        tw = d.textlength(s["subtitle"], font=sub_f)
        d.rounded_rectangle([M, y, M + tw + 56, y + 80], radius=40, fill=D["accent"])
        d.text((M + 28, y + 16), s["subtitle"], font=sub_f, fill="#FFFFFF")
    hint_f = font(FR, 32)
    d.text((W - M - d.textlength("スワイプ →", font=hint_f), H - 170), "スワイプ →", font=hint_f, fill="#BBBBBB")
    footer(d, idx, total, dark=True)
    return img


def render_body(s, idx, total):
    img = Image.new("RGB", (W, H), D["bg"])
    d = ImageDraw.Draw(img)
    head_f, body_f, code_f = font(FB, 68), font(FR, 48), font(FR, 40)
    head = wrap(d, s["heading"], head_f, W - 2 * M - 40)
    body = wrap(d, s.get("body", ""), body_f, W - 2 * M)
    code = wrap(d, s["code"], code_f, W - 2 * M - 80) if s.get("code") else []
    box_h = int(len(code) * code_f.size * 1.5) + 110 if code else 0
    total_h = (len(head) * int(head_f.size * 1.3) + 56 + len(body) * int(body_f.size * 1.6)
               + (48 + box_h if code else 0))
    y = max(150, (H - 120 - total_h) // 2)  # 縦方向センタリング（フッター分を除く）
    # 出典（H-150）に重なる場合だけ、上余白を詰めて本文を少しずつ小さくする
    limit = H - 170
    while y + total_h > limit and body_f.size > 40:
        body_f = font(FR, body_f.size - 2)
        body = wrap(d, s.get("body", ""), body_f, W - 2 * M)
        total_h = (len(head) * int(head_f.size * 1.3) + 56 + len(body) * int(body_f.size * 1.6)
                   + (48 + box_h if code else 0))
        y = max(110, (H - 120 - total_h) // 2)
    d.rectangle([M, y + 10, M + 14, y + 76], fill=D["accent"])
    y = draw_lines(d, head, head_f, M + 40, y, D["text"], 1.3) + 56
    y = draw_lines(d, body, body_f, M, y, D["text"], 1.6)
    if code:
        y += 48
        d.rounded_rectangle([M, y, W - M, y + box_h], radius=24, fill="#FFFFFF", outline="#E2DED6", width=3)
        d.text((M + 40, y + 26), "コピペOK", font=font(FB, 30), fill=D["accent"])
        draw_lines(d, code, code_f, M + 40, y + 80, D["text"], 1.5)
    draw_note(d, s)
    footer(d, idx, total)
    return img


def draw_note(d, s):
    """出典などの小さな注記を、フッターの上に表示する。"""
    if s.get("note"):
        f = font(FR, 28)
        d.text((M, H - 150), "出典: " + s["note"], font=f, fill=D["sub"])


def render_data(s, idx, total):
    """実験結果の数字を大きく見せるスライド。"""
    img = Image.new("RGB", (W, H), D["bg"])
    d = ImageDraw.Draw(img)
    if s.get("heading"):
        hf = font(FB, 48)
        draw_lines(d, wrap(d, s["heading"], hf, W - 2 * M), hf, M, 200, D["sub"], 1.3, center=True)
    big_f = font(FB, 260)
    tw = d.textlength(s["big"], font=big_f)
    if tw > W - 2 * M:  # 左右の余白を割る長さの場合だけ縮める
        big_f = font(FB, int(260 * (W - 2 * M) / tw))
        tw = d.textlength(s["big"], font=big_f)
    d.text(((W - tw) / 2, 380 + (260 - big_f.size) // 2), s["big"], font=big_f, fill=D["accent"])
    lf = font(FB, 52)
    draw_lines(d, wrap(d, s.get("label", ""), lf, W - 2 * M), lf, M, 760, D["text"], 1.45, center=True)
    draw_note(d, s)
    footer(d, idx, total)
    return img


def render_cta(s, idx, total):
    img = Image.new("RGB", (W, H), D["accent"])
    d = ImageDraw.Draw(img)
    title_f = font(FB, 88)
    lines = wrap(d, s["title"], title_f, W - 2 * M)
    y = draw_lines(d, lines, title_f, M, 430, "#FFFFFF", 1.35, center=True)
    if s.get("body"):
        body_f = font(FR, 40)
        y += 50
        draw_lines(d, wrap(d, s["body"], body_f, W - 2 * M), body_f, M, y, "#FFFFFF", 1.5, center=True)
    icon_f = font(FB, 36)
    label = "保存 ・ シェア ・ フォロー"
    tw = d.textlength(label, font=icon_f)
    d.rounded_rectangle([(W - tw) / 2 - 40, H - 330, (W + tw) / 2 + 40, H - 240], radius=45, fill="#FFFFFF")
    d.text(((W - tw) / 2, H - 310), label, font=icon_f, fill=D["accent"])
    footer(d, idx, total, color="#FFFFFF")
    return img


RENDER = {"cover": render_cover, "body": render_body, "data": render_data, "cta": render_cta}


def render(post_dir: Path):
    post = json.loads((post_dir / "post.json").read_text(encoding="utf-8"))
    for old in post_dir.glob("slide-*.png"):
        old.unlink()
    slides = post["slides"]
    out = []
    for i, s in enumerate(slides, 1):
        img = RENDER[s["type"]](s, i, len(slides))
        p = post_dir / f"slide-{i:02d}.png"
        img.save(p, optimize=True)
        out.append(p.name)
    print(f"{post_dir.name}: {len(out)} slides")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        render(Path(arg))
