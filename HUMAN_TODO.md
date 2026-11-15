# 人間にしかできない作業（AI社員はここに書いて待つ）

## 初期設定（1回だけ・合計30〜60分）
- [x] 1. Instagram アカウント作成・プロアカウント化（@matrix.neo1989）
- [x] 2. プロフィール: 名前・自己紹介を設定済み
- [ ] 2b. プロフィール写真に assets/profile-icon.png を設定（Instagramアプリかブラウザで手動アップロード）
- [ ] 2c. リンク集（lit.link 等）を作ったら、自己紹介にリンクを追加
- [x] 3. Meta アプリ作成（jitan-lab-publisher）・権限追加・ビジネスポートフォリオ（Ai時短ラボ）作成・統合ログイン設定
- [x] 4. テスター承認・Instagram アカウント接続済み（IG_USER_ID = 17841458023368315）
- [ ] 4b. 開発者画面の「トークンを生成」を押し、表示されたトークンを安全な場所に保存（チャットには貼らない）
- [ ] 5. GitHub に **公開(Public)リポジトリ** を作り、このフォルダを push（画像URLの配信に raw.githubusercontent.com を使うため）
- [ ] 6. リポジトリの Settings → Secrets and variables → Actions に登録
      - `ANTHROPIC_API_KEY`（console.anthropic.com で発行）
      - `IG_USER_ID` = 17841458023368315 / `IG_ACCESS_TOKEN`（手順4b）
      - `GH_PAT`（トークンが `IG` で始まる場合のみ: 自動延長用。対象リポジトリの Secrets: Read and write 権限の fine-grained PAT）
- [ ] 7. Actions タブ → daily-run → Run workflow で初回実行し、投稿されたことを確認
- [ ] 8. プロフィールリンク: lit.link 等にアフィリエイトリンク集を作り、URL を config/brand.json の monetization.link_in_bio に記入

## 継続（週5分）
- [ ] 毎週月曜: strategy/weekly-report.md と このファイルを確認
- [ ] PR案件のDMが来たら受けるか判断（受けたら is_pr=true で依頼）
- [ ] 収益化機能の招待・条件達成の通知が来たら申請（本人確認・口座登録）
