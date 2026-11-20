#!/usr/bin/env python3
"""朝・夜の報告に使う数字をまとめて Markdown で出す（数値の計算だけ。判断は報告担当の Claude が行う）。

使い方: python3 scripts/progress.py
出力:  目標に対する進捗率 / 最新投稿の初速と過去平均の比較 / 次の投稿予定
"""
import csv
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JST = dt.timezone(dt.timedelta(hours=9))


def rows(path):
    p = ROOT / path
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def posts():
    out = []
    for pj in sorted((ROOT / "content/queue").glob("*/post.json")):
        out.append(json.loads(pj.read_text(encoding="utf-8")))
    return out


def latest_insights():
    """投稿ごとの最新行（同じ投稿は何度も取得されるため）。"""
    latest = {}
    for r in rows("data/insights.csv"):
        latest[r["post_id"]] = r
    return latest


def rate(r, key):
    reach = num(r.get("reach"))
    v = num(r.get(key))
    return v / reach if reach and v is not None else None


def pct(v):
    return "—" if v is None else f"{v * 100:.1f}%"


def main():
    g = json.loads((ROOT / "strategy/goals.json").read_text(encoding="utf-8"))
    now = dt.datetime.now(JST)
    start = dt.date.fromisoformat(g["start"])
    end = dt.date.fromisoformat(g["end"])
    time_pct = min(1.0, max(0.0, (now.date() - start).days / max(1, (end - start).days)))

    acc = rows("data/account_daily.csv")
    followers = num(acc[-1]["followers_count"]) if acc else 0
    ps = posts()
    published = sorted((p for p in ps if p.get("status") == "published"),
                       key=lambda p: (p.get("published") or {}).get("at") or "")  # フォルダ名ではなく公開時刻順
    ins = latest_insights()
    recent = [ins[p["id"]] for p in published[-7:] if p["id"] in ins]
    share_rates = [x for x in (rate(r, "shares") for r in recent) if x is not None]
    avg_share = sum(share_rates) / len(share_rates) if share_rates else None

    current = {"followers": followers or 0, "posts": len(published),
               "share_rate": avg_share or 0, "winning_patterns": g.get("winning_patterns_found", 0)}
    print(f"## 目標に対する進捗（{g['phase']}：{g['start']}〜{g['end']}）")
    print("| 目標 | 現在 | 目標値 | 達成率 |")
    print("|---|---|---|---|")
    total = 0.0
    for goal in g["goals"]:
        cur = current[goal["id"]]
        r = min(1.0, cur / goal["target"]) if goal["target"] else 0
        total += r * goal["weight"]
        shown = pct(cur) if goal["unit"] == "率" else f"{cur:g}{goal['unit']}"
        target = pct(goal["target"]) if goal["unit"] == "率" else f"{goal['target']:g}{goal['unit']}"
        if goal["id"] == "share_rate" and avg_share is None:
            shown = "データなし"
        print(f"| {goal['label']} | {shown} | {target} | {r * 100:.0f}% |")
    print(f"\n**総合の達成率: {total * 100:.0f}%**（期間の経過: {time_pct * 100:.0f}%）")
    if len(acc) >= 2:
        prev = num(acc[-2]["followers_count"]) or 0
        print(f"フォロワーの前回比: {followers - prev:+g}人")

    print("\n## 最新投稿の初速")
    if published:
        last = published[-1]
        r = ins.get(last["id"])
        print(f"- 投稿: {last['slides'][0]['title'].replace(chr(10), '')}（{last.get('format', 'carousel')}・"
              f"型 {last.get('experiment', {}).get('variant', '—')}）")
        print(f"- 公開: {last['published'].get('at', '—')} / {last['published'].get('permalink', '—')}")
        if r:
            dur = num(last.get("reel", {}).get("duration_sec"))
            watch = num(r.get("ig_reels_avg_watch_time"))
            keep = (watch / 1000 / dur) if (watch and dur) else None
            print(f"- 取得時刻 {r['fetched_at']}: リーチ {r.get('reach') or '—'} / 再生 {r.get('views') or '—'} / "
                  f"いいね {r.get('likes') or '—'} / シェア {r.get('shares') or '—'} / 保存 {r.get('saved') or '—'} / "
                  f"フォロー {r.get('follows') or '—'}")
            print(f"- シェア率 {pct(rate(r, 'shares'))} / 保存率 {pct(rate(r, 'saved'))} / "
                  f"フォロー率 {pct(rate(r, 'follows'))} / 視聴維持率 {pct(keep)}")
            others = [ins[p["id"]] for p in published[:-1] if p["id"] in ins]
            if others:
                o = [x for x in (rate(x, "shares") for x in others) if x is not None]
                print(f"- 過去{len(others)}本の平均シェア率 {pct(sum(o) / len(o) if o else None)}")
            else:
                print("- 比較できる過去の投稿はまだありません")
        else:
            print("- インサイトはまだ取得されていません（朝 8:15 の自動取得後に反映）")
    else:
        print("- まだ公開された投稿はありません")

    print("\n## 次の投稿予定")
    upcoming = [p for p in ps if p.get("status") in ("ready", "draft")]
    if not upcoming:
        print("- キューが空です（毎日20時の自動実行で補充されます）")
    for p in upcoming[:3]:
        d = Path("content/queue") / p["id"]
        made = (ROOT / d / "reel.mp4").exists() if p.get("format") == "reel" else any((ROOT / d).glob("slide-*.png"))
        print(f"- {p.get('scheduled_for')}：{p['slides'][0]['title'].replace(chr(10), '')}（{p.get('format', 'carousel')}・"
              f"型 {p.get('experiment', {}).get('variant', '—')}・審査 {p.get('compliance', {}).get('status')}・"
              f"{'動画/画像あり' if made else '未作成（20時の実行で作成）'}）")
    print(f"- キューの残り: {len(upcoming)}本")


if __name__ == "__main__":
    main()
