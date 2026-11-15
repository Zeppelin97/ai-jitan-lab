#!/usr/bin/env python3
"""公開済み投稿のインサイトを取得して data/insights.csv に追記する。

環境変数は publish_instagram.py と同じ（IG_ACCESS_TOKEN など）。
指標名は Meta 側で変わることがあるため IG_METRICS で上書き可能。
"""
import csv
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_instagram import JST, QUEUE, ROOT, api  # noqa: E402

METRICS = os.environ.get("IG_METRICS", "reach,views,saved,shares,likes,comments,follows").split(",")
CSV = ROOT / "data/insights.csv"
COLS = ["post_id", "pillar", "keyword", "media_id", "fetched_at"] + [
    "reach", "views", "saved", "shares", "likes", "comments", "follows"]


def fetch(media_id):
    out = {}
    for m in METRICS:  # 1指標ずつ取って、非対応の指標があっても他は取得する
        try:
            r = api("GET", f"{media_id}/insights", metric=m)
            out[m] = r["data"][0]["values"][0]["value"]
        except Exception as e:  # noqa: BLE001
            out[m] = ""
            print(f"  {m}: skip ({str(e)[:80]})", file=sys.stderr)
    return out


def main():
    if not os.environ.get("IG_ACCESS_TOKEN"):
        print("IG_ACCESS_TOKEN 未設定のためスキップ")
        return
    now = dt.datetime.now(JST).isoformat(timespec="minutes")
    rows = []
    for pj in sorted(QUEUE.glob("*/post.json")):
        p = json.loads(pj.read_text(encoding="utf-8"))
        mid = (p.get("published") or {}).get("media_id")
        if p.get("status") != "published" or not mid:
            continue
        vals = fetch(mid)
        rows.append({"post_id": p["id"], "pillar": p.get("pillar", ""), "keyword": p.get("keyword", ""),
                     "media_id": mid, "fetched_at": now, **{k: vals.get(k, "") for k in COLS[5:]}})
    with CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writerows(rows)
    print(f"{len(rows)} posts appended to {CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
