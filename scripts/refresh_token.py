#!/usr/bin/env python3
"""Instagram の長期トークン（60日有効）を延長し、新トークンを標準出力に出す。
GitHub Actions から `gh secret set IG_ACCESS_TOKEN` に渡して自動更新する。"""
import json
import os
import urllib.parse
import urllib.request

q = urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": os.environ["IG_ACCESS_TOKEN"]})
with urllib.request.urlopen(f"https://graph.instagram.com/refresh_access_token?{q}", timeout=30) as r:
    print(json.loads(r.read())["access_token"])
