# post.json スキーマ

```json
{
  "id": "2026-11-16-chatgpt-mail",
  "scheduled_for": "2026-11-16",
  "format": "reel | carousel",
  "pillar": "コピペで使えるAIプロンプト",
  "keyword": "ChatGPT メール 時短",
  "slides": [
    {"type": "cover", "title": "メール返信が\n3秒で終わる\nChatGPTの使い方", "subtitle": "コピペOKのプロンプト付き"},
    {"type": "body", "heading": "① 丁寧に断る", "body": "本文…", "code": "（任意）コピペ用の文", "note": "（任意）出典の短縮表記"},
    {"type": "data", "big": "49%", "label": "8人で引くと、1人あたりの力は\n単独のときの約半分", "note": "Ringelmann（Moede, 1927の報告）"},
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

## リール台本（format: "reel"）
```json
"reel": {"scenes": [
  {"kind": "hook", "text": "なぜ会議では\n誰も発言\nしないのか？", "chip": "社会的手抜き", "say": "なぜ会議では、誰も発言しないのか？"},
  {"kind": "data", "heading": "8人で綱を引くと…", "count_to": 49, "suffix": "%", "text": "1人あたりの力は\n単独のときの約半分", "note": "Ringelmann（Moede, 1927）", "say": "…"},
  {"kind": "text", "heading": "対処法", "text": "…", "say": "…"},
  {"kind": "cta", "text": "会議の進行役に\n送ってあげて", "sub": "…", "say": "…"}
]}
```
- 生成物: reel.mp4（1080×1920）、reel-cover.png、reel-preview.png
- VOICEVOX で作った音声は、公開時にキャプション末尾へクレジット（config/brand.json の reel.credit）が自動で入る
