#!/usr/bin/env python3
"""公開キューからカルーセルを Instagram に公開する（Instagram Graph API / 公式）。

必要な環境変数:
  IG_USER_ID       Instagram プロアカウントの ID
  IG_ACCESS_TOKEN  長期アクセストークン（instagram_business_content_publish 権限）
  MEDIA_BASE_URL   画像を公開URLで配信するベース。例:
                   https://raw.githubusercontent.com/<owner>/<repo>/main
任意:
  IG_GRAPH_HOST    省略時はトークンの種類から自動判定
  IG_API_VERSION   既定 v23.0

使い方: python3 scripts/publish_instagram.py [--max 1] [--dry-run]
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "content/queue"
JST = dt.timezone(dt.timedelta(hours=9))

# トークンの種類で接続先を自動判定: "IG" で始まる = Instagramユーザートークン（graph.instagram.com）
#                                  それ以外 = 統合ログイン/システムユーザートークン（graph.facebook.com）
_default_host = "graph.instagram.com" if os.environ.get("IG_ACCESS_TOKEN", "").startswith("IG") else "graph.facebook.com"
HOST = os.environ.get("IG_GRAPH_HOST", _default_host)
VER = os.environ.get("IG_API_VERSION", "v23.0")
BASE = f"https://{HOST}/{VER}"


def api(method, path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{BASE}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: {e.code} {e.read().decode()[:500]}")


def wait_ready(container_id, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        st = api("GET", container_id, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {container_id} status {st}")
        time.sleep(5)
    raise RuntimeError(f"container {container_id} timeout")


def due_posts():
    today = dt.datetime.now(JST).date().isoformat()
    posts = []
    for pj in sorted(QUEUE.glob("*/post.json")):
        p = json.loads(pj.read_text(encoding="utf-8"))
        if (
            p.get("status") == "ready"
            and p.get("compliance", {}).get("status") == "approved"
            and p.get("scheduled_for", "9999") <= today
        ):
            posts.append((pj, p))
    return posts


def build_caption(p):
    tags = " ".join(p.get("hashtags", [])[:5])
    return f"{p['caption']}\n\n{tags}".strip()


def publish(pj: Path, p: dict, dry: bool):
    d = pj.parent
    slides = sorted(d.glob("slide-*.png"))
    if not 2 <= len(slides) <= 10:
        raise RuntimeError(f"{d.name}: スライド数 {len(slides)}（2〜10枚が必要。render_carousel.py を先に実行）")
    rel = d.relative_to(ROOT).as_posix()
    base = os.environ.get("MEDIA_BASE_URL", "https://example.invalid").rstrip("/")
    urls = [f"{base}/{rel}/{s.name}" for s in slides]
    caption = build_caption(p)
    if dry:
        print(f"[dry-run] {d.name}\n  images: {len(urls)} 枚 例 {urls[0]}\n  caption:\n{caption}\n")
        return
    ig = os.environ["IG_USER_ID"]
    children = []
    for u in urls:
        c = api("POST", f"{ig}/media", image_url=u, is_carousel_item="true")
        children.append(c["id"])
    for c in children:
        wait_ready(c)
    carousel = api("POST", f"{ig}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)
    wait_ready(carousel["id"])
    res = api("POST", f"{ig}/media_publish", creation_id=carousel["id"])
    media_id = res["id"]
    link = api("GET", media_id, fields="permalink").get("permalink")
    p["status"] = "published"
    p["published"] = {"media_id": media_id, "at": dt.datetime.now(JST).isoformat(), "permalink": link}
    pj.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"published {d.name} -> {link}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    dry = a.dry_run or not all(os.environ.get(k) for k in ("IG_USER_ID", "IG_ACCESS_TOKEN", "MEDIA_BASE_URL"))
    if dry and not a.dry_run:
        print("認証情報が未設定のため dry-run で実行します")
    posts = due_posts()[: min(a.max, 2)]
    if not posts:
        print("公開対象なし")
        return
    failed = False
    for pj, p in posts:
        try:
            publish(pj, p, dry)
        except Exception as e:  # noqa: BLE001
            failed = True
            print(f"ERROR {pj.parent.name}: {e}", file=sys.stderr)
            p.setdefault("published", {})["error"] = str(e)[:500]
            pj.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
