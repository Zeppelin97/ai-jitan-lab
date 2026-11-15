---
description: 毎日の運用（ネタ補充→審査→画像化→公開）を CEO として実行する
---
あなたは CEO です。CLAUDE.md の鉄則に従い、以下を順に実行してください。

1. `content/queue/` を確認し、status が draft/ready で未公開の投稿数を数える
2. `config/brand.json` の schedule.queue_buffer に満たない分だけ、次の流れで補充する
   （scheduled_for は最後の予定日の翌日から1日ずつ。pillar は playbook の配分に従う）
   - researcher にテーマ1件を依頼
   - writer に post.json 作成を依頼
   - compliance に審査を依頼（rejected なら別テーマで作り直し。最大2回）
   - designer に画像化と目視チェックを依頼
3. publisher に公開を依頼
4. 最後に今日やったこと（作成・審査結果・公開結果）を `strategy/daily-log.md` の先頭に3〜5行で追記
