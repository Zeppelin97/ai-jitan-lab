#!/usr/bin/env python3
"""「もしも〇〇だったら」実験リール #1: 地球を貫通する穴に飛び込んだら？

物理: 一様密度の地球では単振動。片道 T/2 = π√(R/g) ≈ 42.2分、中心で最大速度 √(gR) ≈ 7.9 km/s
実際の密度分布では約38分（Klotz, 2015, Am. J. Phys. 83, 231）。空気抵抗は無視。

使い方: python3 scripts/whatif/gravity_tunnel.py <出力フォルダ> [--preview-only]
"""
import math
import random
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from render_reel import (FPS, RATE, H, W, blend, ease, font, pcm_of, tts_say,  # noqa: E402
                         tts_voicevox, voicevox_alive, wrap)
from render_carousel import FB, FR  # noqa: E402

G, R_EARTH = 9.81, 6.371e6
VMAX = math.sqrt(G * R_EARTH) / 1000          # 7.9 km/s
T_HALF_MIN = math.pi * math.sqrt(R_EARTH / G) / 60  # 42.2 分
SPEAKER, SPEED, CREDIT = 3, 1.15, "VOICEVOX:ずんだもん"
HANDLE = "@matrix.neo1989"

CX, CY, RP = W // 2, 980, 380   # 地球の中心と半径（px）
BG, ACC, WHITE = "#0B1020", "#FF7A45", "#FFFFFF"

# (ナレーション, シーン種別, 落下の進み u の開始, 終了)  u=0:日本, 1:真裏, 2:日本に戻る
SCENES = [
    ("もしも、地球を貫通する穴に飛び込んだら、どうなるのか。実験してみた。", "hook", 0.0, 0.0),
    ("日本から飛び込むと、重力でどんどん加速していく。", "fall", 0.0, 0.42),
    ("地球の中心で、速さは最大の秒速7.9キロ。新幹線のおよそ90倍だ。", "center", 0.42, 0.58),
    ("そして約42分後、地球の真裏に、ぴたりと到着する。", "arrive", 0.58, 1.0),
    ("でも、何かにつかまらないと、また落ちていく。空気がなければ、永遠に往復だ。", "back", 1.0, 2.0),
    ("ちなみに、実際の地球の密度で計算すると、約38分という研究もある。", "note", 2.0, 2.0),
    ("次は何で実験してほしい？コメントで教えてね。", "cta", 2.0, 2.0),
]

random.seed(7)
STARS = [(random.randrange(W), random.randrange(H), random.choice([1, 1, 2])) for _ in range(160)]


def draw_earth(d):
    layers = [(1.00, "#2E6FD8"), (0.985, "#8B5A2B"), (0.94, "#D9692E"), (0.55, "#F2A541"), (0.19, "#FFE08A")]
    for r, c in layers:
        rr = RP * r
        d.ellipse([CX - rr, CY - rr, CX + rr, CY + rr], fill=c)
    d.rectangle([CX - 14, CY - RP - 6, CX + 14, CY + RP + 6], fill="#1A1A1A")  # 穴
    lf = font(FB, 38)
    for txt, y in (("日本", CY - RP - 70), ("日本の真裏（南米沖）", CY + RP + 24)):
        d.text((CX - d.textlength(txt, font=lf) / 2, y), txt, font=lf, fill=WHITE)


def draw_person(d, y):
    c = ACC
    d.ellipse([CX - 16, y - 46, CX + 16, y - 14], fill=c)          # 頭
    d.line([CX, y - 14, CX, y + 22], fill=c, width=8)              # 体
    d.line([CX - 22, y - 4, CX + 22, y - 4], fill=c, width=7)      # 腕
    d.line([CX, y + 22, CX - 16, y + 50], fill=c, width=7)         # 足
    d.line([CX, y + 22, CX + 16, y + 50], fill=c, width=7)


def hud(d, minutes, speed, a=1.0):
    box = blend(BG, "#1C2440", a)
    d.rounded_rectangle([70, 250, W - 70, 470], radius=28, fill=box)
    lf, vf = font(FR, 36), font(FB, 76)
    col_l, col_v = blend(BG, "#AEB6CC", a), blend(BG, WHITE, a)
    d.text((120, 275), "経過時間", font=lf, fill=col_l)
    d.text((120, 330), f"{int(minutes):02d}分{int(minutes % 1 * 60):02d}秒", font=vf, fill=col_v)
    d.text((580, 275), "速さ", font=lf, fill=col_l)
    d.text((580, 330), f"秒速{speed:.1f}km", font=vf, fill=blend(BG, ACC, a))


def subtitle(d, text, a):
    f = font(FB, 50)
    lines = wrap(d, text, f, W - 220)
    y = 1470
    h = len(lines) * 72 + 40
    d.rounded_rectangle([90, y - 20, W - 90, y - 20 + h], radius=24, fill=blend(BG, "#000000", 0.6 * a))
    for i, ln in enumerate(lines):
        d.text((CX - d.textlength(ln, font=f) / 2, y + i * 72), ln, font=f, fill=blend(BG, WHITE, a))


def big_card(d, top, big, bottom, a, bg=None):
    if bg:
        d.rounded_rectangle([90, 560, W - 90, 1240], radius=40, fill=blend(BG, bg, a))
    tf, bf, sf = font(FB, 56), font(FB, 200), font(FB, 52)
    for txt, f, y, col in ((top, tf, 640, "#FFFFFF"), (big, bf, 760, ACC if not bg else "#FFFFFF"),
                           (bottom, sf, 1040, "#FFFFFF")):
        for i, ln in enumerate(txt.split("\n")):
            d.text((CX - d.textlength(ln, font=f) / 2, y + i * 70), ln, font=f, fill=blend(BG, col, a))


def frame(i, t, dur, narration):
    _, kind, u0, u1 = SCENES[i]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for x, y, s in STARS:
        d.ellipse([x, y, x + s, y + s], fill="#5A6380")
    draw_earth(d)
    p = min(1.0, t / max(0.1, dur - 0.3))
    u = u0 + (u1 - u0) * (ease(p) if kind == "arrive" else p)
    theta = math.pi * u
    y = CY - RP * math.cos(theta)
    if kind in ("fall", "center", "arrive", "back"):  # 速いほど長く見える残像
        for k in range(1, 9):
            yk = CY - RP * math.cos(math.pi * (u - k * 0.012 * (1 if u1 >= u0 else -1)))
            r = 10 - k
            d.ellipse([CX - r, yk - 30 - r, CX + r, yk - 30 + r], fill=blend(BG, ACC, 0.55 - k * 0.06))
    draw_person(d, y)
    if kind != "hook":
        hud(d, T_HALF_MIN * u, VMAX * abs(math.sin(theta)))
    a_in = ease(t / 0.3)
    if kind == "hook":
        f = font(FB, 92)
        for k, ln in enumerate(["もしも地球を貫通する", "穴に飛び込んだら？"]):
            d.text((CX - d.textlength(ln, font=f) / 2, 280 + k * 120), ln, font=f,
                   fill=blend(BG, WHITE if k == 0 else ACC, ease((t - k * 0.25) / 0.3)))
    elif kind == "note":
        big_card(d, "実際の地球の密度で計算すると", "約38分", "Klotz (2015) Am. J. Phys.\n※空気抵抗・熱は無視", a_in, bg="#1C2440")
    elif kind == "cta":
        big_card(d, "次は何で実験する？", "コメント", "で教えてね", a_in, bg=ACC)
    # 上部の進捗バーとハンドル
    hf = font(FR, 32)
    d.text((CX - d.textlength(HANDLE, font=hf) / 2, 1820), HANDLE, font=hf, fill="#7C86A2")
    subtitle(d, narration, a_in)
    return img


def main(out_dir: Path, preview_only=False):
    out_dir.mkdir(parents=True, exist_ok=True)
    engine = "voicevox" if voicevox_alive() else ("say" if shutil.which("say") else "silent")
    audio = []
    for text, *_ in SCENES:
        if engine == "voicevox":
            pcm = pcm_of(tts_voicevox(text, SPEAKER, SPEED))
        elif engine == "say":
            pcm = pcm_of(tts_say(text))
        else:
            pcm = b"\x00\x00" * int(RATE * len(text) * 0.11)
        audio.append(pcm)
    durs = [max(1.5, len(p) / 2 / RATE + 0.35) for p in audio]
    total = sum(durs)
    print(f"音声: {engine} / 合計 {total:.1f}秒")

    thumbs = [frame(i, durs[i] * 0.7, durs[i], SCENES[i][0]).resize((270, 480)) for i in range(len(SCENES))]
    sheet = Image.new("RGB", (len(thumbs) * 280, 480), "white")
    for k, th in enumerate(thumbs):
        sheet.paste(th, (k * 280, 0))
    sheet.save(out_dir / "reel-preview.png")
    frame(0, 1.0, durs[0], SCENES[0][0]).save(out_dir / "reel-cover.png")
    if preview_only or not shutil.which("ffmpeg"):
        return

    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "v.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            for pcm, dur in zip(audio, durs):
                w.writeframes(pcm + b"\x00\x00" * int(RATE * dur - len(pcm) / 2))
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "21",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest",
               "-movflags", "+faststart", str(out_dir / "reel.mp4")]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i, dur in enumerate(durs):
            for k in range(int(round(dur * FPS))):
                proc.stdin.write(frame(i, k / FPS, dur, SCENES[i][0]).tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            sys.exit("ffmpeg でエラー")
    (out_dir / "credit.txt").write_text(CREDIT + "\n", encoding="utf-8")
    print(f"reel.mp4 {total:.1f}秒")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(Path(args[0] if args else "content/experiments/2026-11-gravity-tunnel"), "--preview-only" in sys.argv)
