#!/usr/bin/env python3
"""post.json の reel 台本から、縦長リール動画 (1080x1920, 30fps) を作る。

- ナレーション: VOICEVOX エンジン（VOICEVOX_URL、既定 http://localhost:50021）
               無ければ macOS の say、それも無ければ無音（プレビュー用）
- 動画: Pillow でフレームを描き、ffmpeg で H.264/AAC の mp4 にする
- ffmpeg が無い環境では、確認用の静止画（reel-preview.png）だけ作る

使い方: python3 scripts/render_reel.py content/queue/<id> [--preview-only]
出力:   reel.mp4 / reel-cover.png / reel-preview.png
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import wave
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_carousel import BRAND, FB, FR, NO_START, font  # noqa: E402

D = BRAND["design"]
W, H = 1080, 1920
FPS = 30
M = 90
SAFE_TOP, SAFE_BOTTOM = 260, 1500  # リールのUI（上部タブ・下部キャプション）を避ける範囲
RATE = 24000
VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://localhost:50021")


# ---------- 音声 ----------
def tts_voicevox(text, speaker, speed):
    q = urllib.parse.urlencode({"text": text, "speaker": speaker})
    with urllib.request.urlopen(urllib.request.Request(f"{VOICEVOX_URL}/audio_query?{q}", method="POST"), timeout=60) as r:
        query = json.loads(r.read())
    query.update({"speedScale": speed, "outputSamplingRate": RATE, "outputStereo": False,
                  "prePhonemeLength": 0.05, "postPhonemeLength": 0.1})
    req = urllib.request.Request(f"{VOICEVOX_URL}/synthesis?speaker={speaker}", data=json.dumps(query).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def tts_say(text):
    if not shutil.which("say"):
        return None
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "a.wav"
        subprocess.run(["say", "-v", "Kyoko", "-r", "230", "--file-format=WAVE",
                        f"--data-format=LEI16@{RATE}", "-o", str(out), text], check=True)
        return out.read_bytes()


def voicevox_alive():
    try:
        urllib.request.urlopen(f"{VOICEVOX_URL}/version", timeout=3)
        return True
    except Exception:  # noqa: BLE001
        return False


def pcm_of(wav_bytes):
    with wave.open(io.BytesIO(wav_bytes)) as w:
        assert w.getframerate() == RATE and w.getnchannels() == 1 and w.getsampwidth() == 2, "音声形式が想定外"
        return w.readframes(w.getnframes())


def synthesize(scenes, reel):
    """各シーンの音声(PCM)と長さ(秒)を返す。"""
    engine = "voicevox" if voicevox_alive() else ("say" if shutil.which("say") else "silent")
    speaker, speed = reel.get("speaker", BRAND.get("reel", {}).get("speaker", 2)), reel.get("speed", 1.15)
    out = []
    for s in scenes:
        text = s.get("say") or s["text"].replace("\n", "")
        if engine == "voicevox":
            pcm = pcm_of(tts_voicevox(text, speaker, speed))
        elif engine == "say":
            pcm = pcm_of(tts_say(text))
        else:
            pcm = b"\x00\x00" * int(RATE * max(1.2, len(text) * 0.11))
        dur = len(pcm) / 2 / RATE
        out.append((pcm, dur))
    print(f"  音声エンジン: {engine}")
    return out, engine


# ---------- 描画 ----------
def wrap(d, text, f, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if d.textlength(cur + ch, font=f) <= max_w or not cur or ch in NO_START:
                cur += ch
            else:
                lines.append(cur)
                cur = ch
        lines.append(cur)
    return lines


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def blend(c1, c2, a):
    c1 = tuple(int(c1[i:i + 2], 16) for i in (1, 3, 5))
    c2 = tuple(int(c2[i:i + 2], 16) for i in (1, 3, 5))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))


def centered_block(d, lines, f, y, fill_fn, spacing=1.35):
    lh = int(f.size * spacing)
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f)
        d.text(((W - tw) / 2, y + i * lh), ln, font=f, fill=fill_fn(i))
    return y + len(lines) * lh


def chrome(d, t_total, total, note=None, dark=False):
    """上部の進捗バー・下部のハンドル/出典。"""
    d.rectangle([0, 0, W, 14], fill=blend(D["sub"], D["bg"], 0.6) if not dark else (60, 70, 95))
    d.rectangle([0, 0, int(W * t_total / total), 14], fill=D["accent"])
    f = font(FR, 34)
    col = "#C9CCD6" if dark else D["sub"]
    hd = BRAND["account"]["handle"]
    d.text(((W - d.textlength(hd, font=f)) / 2, SAFE_BOTTOM + 40), hd, font=f, fill=col)
    if note:
        nf = font(FR, 30)
        tx = "出典: " + note
        d.text(((W - d.textlength(tx, font=nf)) / 2, SAFE_BOTTOM - 10), tx, font=nf, fill=col)


def frame(s, t, dur, t_total, total):
    kind = s.get("kind", "text")
    dark = kind == "hook"
    bg = D["cover_bg"] if dark else (D["accent"] if kind == "cta" else D["bg"])
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    a_in = ease(t / 0.35)  # 入りのフェード

    if kind == "hook":
        f = font(FB, 118)
        lines = wrap(d, s["text"], f, W - 2 * M)
        # 1行ずつ素早く出す
        per = 0.18
        y0 = 620 - len(lines) * 70
        centered_block(d, lines, f, y0, lambda i: blend(D["cover_bg"], D["cover_text"], ease((t - i * per) / 0.25)))
        if s.get("chip"):
            cf = font(FB, 52)
            tw = d.textlength(s["chip"], font=cf)
            y = y0 + len(lines) * int(118 * 1.35) + 60
            a = ease((t - 0.6) / 0.3)
            d.rounded_rectangle([(W - tw) / 2 - 40, y, (W + tw) / 2 + 40, y + 96], radius=48,
                                fill=blend(D["cover_bg"], D["accent"], a))
            d.text(((W - tw) / 2, y + 18), s["chip"], font=cf, fill=blend(D["cover_bg"], "#FFFFFF", a))
    elif kind == "data":
        if s.get("heading"):
            hf = font(FB, 56)
            centered_block(d, wrap(d, s["heading"], hf, W - 2 * M), hf, 420,
                           lambda i: blend(D["bg"], D["sub"], a_in))
        bf = font(FB, 300)
        to = s.get("count_to")
        if to is not None:
            v = to * ease(t / 0.9)
            big = f"{int(round(v))}{s.get('suffix', '')}"
        else:
            big = s["big"]
        tw = d.textlength(big, font=bf)
        d.text(((W - tw) / 2, 620), big, font=bf, fill=blend(D["bg"], D["accent"], a_in))
        lf = font(FB, 60)
        centered_block(d, wrap(d, s["text"], lf, W - 2 * M), lf, 1030,
                       lambda i: blend(D["bg"], D["text"], ease((t - 0.7 - i * 0.15) / 0.3)))
    elif kind == "cta":
        f = font(FB, 104)
        lines = wrap(d, s["text"], f, W - 2 * M)
        y = centered_block(d, lines, f, 640, lambda i: blend(D["accent"], "#FFFFFF", a_in))
        if s.get("sub"):
            sf = font(FR, 48)
            centered_block(d, wrap(d, s["sub"], sf, W - 2 * M), sf, y + 70,
                           lambda i: blend(D["accent"], "#FFFFFF", ease((t - 0.4) / 0.3)), 1.5)
    else:  # text
        hf, bf = font(FB, 66), font(FB, 80)
        hl = wrap(d, s["heading"], hf, W - 2 * M - 40) if s.get("heading") else []
        lines = wrap(d, s["text"], bf, W - 2 * M)
        HL, BL = 90, 124
        block = len(hl) * HL + (70 if hl else 0) + len(lines) * BL
        y = SAFE_TOP + (SAFE_BOTTOM - 60 - SAFE_TOP - block) // 2  # 縦方向センタリング
        if hl:
            d.rectangle([M, y + 12, M + 16, y + 78], fill=D["accent"])
            for i, ln in enumerate(hl):
                d.text((M + 44, y + i * HL), ln, font=hf, fill=blend(D["bg"], D["accent"], a_in))
            y += len(hl) * HL + 70
        # ナレーションの進み具合に合わせて行を出す
        reveal = (t / max(0.5, dur * 0.85)) * len(lines)
        for i, ln in enumerate(lines):
            a = ease(reveal - i + 0.6)
            d.text((M, y + i * BL), ln, font=bf, fill=blend(D["bg"], D["text"], a))

    chrome(d, t_total, total, s.get("note"), dark=dark or kind == "cta")
    return img


# ---------- 合成 ----------
def render(post_dir: Path, preview_only=False):
    post = json.loads((post_dir / "post.json").read_text(encoding="utf-8"))
    reel = post.get("reel")
    if not reel:
        sys.exit(f"{post_dir.name}: post.json に reel がありません")
    scenes = reel["scenes"]
    audio, engine = synthesize(scenes, reel)
    pad = 0.35
    durs = [max(1.4, a[1] + pad) for a in audio]
    total = sum(durs)

    # 確認用: 各シーンの中ほどのフレームを並べた画像
    thumbs, t0 = [], 0.0
    for s, dur in zip(scenes, durs):
        thumbs.append(frame(s, dur * 0.8, dur, t0 + dur * 0.8, total).resize((270, 480)))
        t0 += dur
    sheet = Image.new("RGB", (len(thumbs) * 280, 480), "white")
    for i, th in enumerate(thumbs):
        sheet.paste(th, (i * 280, 0))
    sheet.save(post_dir / "reel-preview.png")
    frame(scenes[0], durs[0], durs[0], 0.01, total).save(post_dir / "reel-cover.png")

    if preview_only or not shutil.which("ffmpeg"):
        print(f"{post_dir.name}: プレビューのみ作成（{total:.1f}秒の予定）")
        return

    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "voice.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            for (pcm, adur), dur in zip(audio, durs):
                w.writeframes(pcm + b"\x00\x00" * int(RATE * (dur - adur)))
        out = post_dir / "reel.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", str(wav),
               "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        t_total = 0.0
        for s, dur in zip(scenes, durs):
            n = int(round(dur * FPS))
            for k in range(n):
                t = k / FPS
                p.stdin.write(frame(s, t, dur, t_total + t, total).tobytes())
            t_total += dur
        p.stdin.close()
        if p.wait() != 0:
            sys.exit("ffmpeg でエラー")
    post.setdefault("reel", {})["engine"] = engine
    post["reel"]["duration_sec"] = round(total, 1)
    (post_dir / "post.json").write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{post_dir.name}: reel.mp4 {total:.1f}秒 / {out.stat().st_size // 1024}KB")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    for a in args:
        render(Path(a), preview_only="--preview-only" in sys.argv)
