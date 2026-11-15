#!/usr/bin/env python3
"""プロフィールのリンク集ページ（docs/index.html）を作る。GitHub Pages で公開する。

- 公開済みの投稿から「投稿で紹介した研究（出典）」を自動で並べる
- config/links.json の本・サービスを並べ、アフィリエイトIDがあれば自動で付ける
使い方: python3 scripts/build_links.py
"""
import html
import json
import shutil
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND = json.loads((ROOT / "config/brand.json").read_text(encoding="utf-8"))
LINKS = json.loads((ROOT / "config/links.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs"
D = BRAND["design"]
e = html.escape


def book_url(b):
    q = urllib.parse.quote(f"{b['title']} {b['author']}")
    tag = LINKS["affiliate"].get("amazon_tag")
    return f"https://www.amazon.co.jp/s?k={q}" + (f"&tag={urllib.parse.quote(tag)}" if tag else "")


def published_posts():
    posts = []
    for pj in (ROOT / "content/queue").glob("*/post.json"):  # archive は旧ジャンルなので対象外
        p = json.loads(pj.read_text(encoding="utf-8"))
        if p.get("status") == "published":
            posts.append(p)
    return sorted(posts, key=lambda p: p["published"]["at"], reverse=True)[:15]


def source_html(s):
    if s.startswith("http"):
        host = urllib.parse.urlparse(s).netloc
        return f'<li><a href="{e(s)}" target="_blank" rel="noopener">{e(host)}</a></li>'
    return f"<li>{e(s)}</li>"


def build():
    OUT.mkdir(exist_ok=True)
    shutil.copy(ROOT / "assets/profile-icon.png", OUT / "icon.png")
    acc = BRAND["account"]
    name = acc["display_name"].split("｜")[0]

    posts = published_posts()
    if posts:
        items = []
        for p in posts:
            title = p["slides"][0]["title"].replace("\n", "")
            date = p["published"]["at"][:10].replace("-", "/")
            link = p["published"].get("permalink") or "#"
            srcs = "".join(source_html(s) for s in p.get("sources", []))
            items.append(f'<details><summary><span class="date">{date}</span>{e(title)}</summary>'
                         f'<a class="ig" href="{e(link)}" target="_blank" rel="noopener">投稿を見る →</a>'
                         f'<p class="lbl">出典</p><ul>{srcs}</ul></details>')
        posts_html = "".join(items)
    else:
        posts_html = '<p class="empty">最初の投稿は準備中です。公開されるとここに出典がまとまります。</p>'

    books = "".join(
        f'<a class="card" href="{e(book_url(b))}" target="_blank" rel="noopener sponsored">'
        f'<span class="t">{e(b["title"])}</span><span class="a">{e(b["author"])}</span>'
        f'<span class="w">{e(b["why"])}</span><span class="go">Amazonで見る →</span></a>'
        for b in LINKS.get("books", []))
    services = "".join(
        f'<a class="card" href="{e(s["url"])}" target="_blank" rel="noopener sponsored">'
        f'<span class="t">{e(s["name"])}</span><span class="w">{e(s["why"])}</span><span class="go">詳しく見る →</span></a>'
        for s in LINKS.get("services", []))
    services_sec = f'<h2>キャリア・学びのサービス</h2>{services}' if services else ""

    page = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(name)}｜リンク集</title>
<meta name="description" content="{e(LINKS['intro'])}">
<link rel="icon" href="icon.png">
<style>
:root{{--bg:{D['bg']};--text:{D['text']};--acc:{D['accent']};--sub:{D['sub']};--card:#fff;--line:#E7E1D6}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141A2B;--text:#EEF0F5;--sub:#A3A9B8;--card:#1E2638;--line:#2C3550}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;line-height:1.7}}
main{{max-width:560px;margin:0 auto;padding:32px 16px 48px}}
header{{text-align:center}}header img{{width:96px;height:96px;border-radius:50%}}
h1{{font-size:22px;margin:12px 0 4px}}.handle{{color:var(--sub);font-size:14px}}.intro{{font-size:15px;margin:16px 0}}
.pr{{font-size:12px;color:var(--sub);border:1px solid var(--line);border-radius:8px;padding:8px 12px;margin:16px 0}}
h2{{font-size:17px;margin:32px 0 12px;padding-left:10px;border-left:5px solid var(--acc)}}
.card{{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:0 0 12px;color:inherit;text-decoration:none}}
.card .t{{display:block;font-weight:700;font-size:16px}}.card .a{{display:block;color:var(--sub);font-size:13px}}
.card .w{{display:block;font-size:14px;margin-top:6px}}.card .go{{display:block;color:var(--acc);font-weight:700;font-size:14px;margin-top:8px}}
details{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 16px;margin:0 0 10px}}
summary{{cursor:pointer;font-weight:700}}.date{{color:var(--sub);font-weight:400;font-size:13px;margin-right:8px}}
.ig{{color:var(--acc);font-size:14px;font-weight:700;text-decoration:none}}.lbl{{margin:8px 0 0;font-size:13px;color:var(--sub)}}
ul{{margin:4px 0 0;padding-left:20px;font-size:13px;word-break:break-all}}a{{color:var(--acc)}}
.empty{{color:var(--sub);font-size:14px}}footer{{text-align:center;color:var(--sub);font-size:12px;margin-top:40px}}
</style></head><body><main>
<header><img src="icon.png" alt="{e(name)}のアイコン"><h1>{e(name)}</h1>
<div class="handle">{e(acc['handle'])}</div><p class="intro">{e(LINKS['intro'])}</p></header>
<p class="pr">【PR】このページには広告（アフィリエイトリンク）が含まれます。リンク経由で購入・申込があると、運営者に紹介料が入ることがあります。</p>
<h2>もっと知りたい人へ：おすすめの本</h2>{books}
{services_sec}
<h2>投稿で紹介した研究（出典）</h2>{posts_html}
<footer>© {e(name)} ／ <a href="https://www.instagram.com/{e(acc['handle'].lstrip('@'))}/" target="_blank" rel="noopener">Instagram</a></footer>
</main></body></html>
"""
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"docs/index.html を作成（本 {len(LINKS.get('books', []))} / 投稿 {len(posts)}）")


if __name__ == "__main__":
    build()
