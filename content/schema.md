# post.json スキーマ

```json
{
  "id": "2026-11-16-chatgpt-mail",
  "scheduled_for": "2026-11-16",
  "pillar": "コピペで使えるAIプロンプト",
  "keyword": "ChatGPT メール 時短",
  "slides": [
    {"type": "cover", "title": "メール返信が\n3秒で終わる\nChatGPTの使い方", "subtitle": "コピペOKのプロンプト付き"},
    {"type": "body", "heading": "① 丁寧に断る", "body": "本文…", "code": "（任意）コピペ用プロンプト"},
    {"type": "cta", "title": "保存して\n明日から使おう", "body": "毎日20時に時短ワザを投稿中"}
  ],
  "caption": "1行目に検索キーワードを含める。改行で読みやすく。最後に保存/シェアの一言。",
  "hashtags": ["#ChatGPT活用", "#仕事効率化", "#時短術"],
  "alt_text": "画像の内容説明（検索にも効く）",
  "sources": ["https://… or 自社検証メモ"],
  "is_pr": false,
  "ai_label_required": false,
  "compliance": {"status": "pending | approved | rejected", "notes": ""},
  "status": "draft | ready | published | failed",
  "published": {"media_id": null, "at": null, "permalink": null}
}
```

- スライドは 5〜8 枚（cover 1 + body 3〜6 + cta 1）
- body の本文は 1 スライド 90 文字以内、code は 120 文字以内
- ハッシュタグは 3〜5 個（Instagram の上限変更に対応して少数精鋭）
- `is_pr: true` のときはキャプション冒頭と cover の subtitle に `【PR】` を入れる
