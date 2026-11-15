#!/usr/bin/env python3
"""アカウント全体の数値（フォロワー数・投稿数）を data/account_daily.csv に追記する。"""
import csv
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_instagram import JST, ROOT, api  # noqa: E402

CSV = ROOT / "data/account_daily.csv"
COLS = ["fetched_at", "followers_count", "follows_count", "media_count"]


def main():
    if not os.environ.get("IG_ACCESS_TOKEN"):
        print("IG_ACCESS_TOKEN 未設定のためスキップ")
        return
    r = api("GET", os.environ["IG_USER_ID"], fields="followers_count,follows_count,media_count")
    new = not CSV.exists()
    with CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if new:
            w.writeheader()
        w.writerow({"fetched_at": dt.datetime.now(JST).isoformat(timespec="minutes"),
                    **{k: r.get(k, "") for k in COLS[1:]}})
    print(f"フォロワー {r.get('followers_count')} / 投稿 {r.get('media_count')}")


if __name__ == "__main__":
    main()
