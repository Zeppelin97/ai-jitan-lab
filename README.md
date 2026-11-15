# 株式会社オートグラム — ほぼ無人の Instagram 運用会社

Claude Code の役割別エージェント（社員）と GitHub Actions（勤務時間）を組み合わせて、
**ネタ出し → 原稿 → 審査 → デザイン → 投稿 → 分析 → 改善** を自動で回す仕組みです。

## 収益の仕組み（前提）
Instagram には YouTube のような「誰でももらえる広告収益の分配」はほぼありません。
ボーナスや広告分配は招待制で、再生数の条件も高めです。なので最短ルートは次の順です。

| 段階 | 収益源 | 目安 | この仕組みでの対応 |
|---|---|---|---|
| 0日目〜 | アフィリエイト（プロフィールリンク経由） | フォロワー数不問 | link_in_bio、PR投稿の【PR】表記を自動化 |
| 5千〜1万人 | 企業PR・ブランドコラボ | エンゲージメント次第 | 分析部が到達を検知し HUMAN_TODO に追加 |
| 条件達成後 | サブスク・ボーナス・広告分配など公式機能 | 招待・条件次第 | 同上（申請は本人のみ可能） |

## 組織と流れ
```
[毎日20時 GitHub Actions]
 CEO(/daily-run) ─▶ リサーチ部 ─▶ 編集部 ─▶ 審査部 ─▶ デザイン部 ─▶ 配信部 ─▶ Instagram
[毎週月曜]
 分析部(インサイト取得) ─▶ CEO(/weekly-review) ─▶ playbook 更新 ─▶ 翌週の配分に反映
```
- 社員: `.claude/agents/*.md`、業務手順: `.claude/commands/*.md`、社則: `CLAUDE.md`
- 画像生成: `scripts/render_carousel.py`（テンプレート方式なので AI ラベル不要・毎回品質が安定）
- 投稿: `scripts/publish_instagram.py`（Meta 公式 Graph API。非公式ボットは凍結リスクがあるので不使用）
- 分析: `scripts/fetch_insights.py` → `data/insights.csv`
- トークン: 統合ログインのシステムユーザートークン（無期限）を使うので更新作業なし

## 人間の作業
`HUMAN_TODO.md` を参照。初期設定 30〜60 分、その後は週 5 分程度。

## 手元で試す
```bash
pip install -r requirements.txt
python3 scripts/render_carousel.py content/queue/*/
python3 scripts/publish_instagram.py --dry-run
```
Claude Code で `/daily-run` を実行すれば手元でも会社が1日分働きます。

## 月額コストの目安
- GitHub Actions: 公開リポジトリなら無料
- Claude API: 1日1投稿で数百〜千円台/月程度（モデルと試行回数による）

## 拡張（GitHub / プラグイン）
- 予約投稿を GUI で管理したい → Posty プラグイン（Claude Code の `/mcp` で認証すると使える）
- リール動画化 → `social-media-skills:reels-script` + Remotion（github.com/remotion-dev/remotion）でテンプレ動画を自動生成
- 同じ原稿を Threads にも流用 → `social-media-skills:cross-platform-repurposing`
