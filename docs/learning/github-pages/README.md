# GitHub Pages 学習ドキュメント

このフォルダには GitHub Actions によって自動生成されたHTMLファイルが配置されます。

## デザイン

Qiita風のモダンなデザインを採用しています：

- サイドバーナビゲーション
- シンタックスハイライト（Monokai風）
- レスポンシブ対応（モバイル対応）
- カード型のインデックスページ

## 仕組み

```
learning/md/*.md  ──(GitHub Actions)──>  learning/github-pages/*.html
                          │
                          ↓
                   GitHub Pages で公開
```

## ローカルでプレビュー

```bash
# 依存関係をインストール
pip install markdown pygments

# ビルド
cd learning/github-pages
python build.py

# ブラウザで確認
open index.html
```

## GitHub Pages の設定方法

1. GitHubリポジトリ → Settings → Pages
2. Source を「GitHub Actions」に変更
3. `learning/md/` にMarkdownを追加してプッシュ
4. 自動でHTMLが生成・公開される

公開URL: `https://<username>.github.io/<repo-name>/`

## ファイル構成

```
learning/github-pages/
├── assets/
│   └── style.css      # Qiita風スタイル
├── build.py           # ビルドスクリプト
├── index.html         # トップページ（自動生成）
├── *.html             # 各ドキュメント（自動生成）
└── README.md          # このファイル
```

## カスタマイズ

### スタイルを変更する

`assets/style.css` を編集してください。CSS変数でカラーを管理しています：

```css
:root {
  --primary-color: #55c500;     /* メインカラー（Qiita緑） */
  --text-color: #333;           /* テキスト色 */
  --bg-color: #f6f6f6;          /* 背景色 */
  --code-bg: #364549;           /* コードブロック背景 */
}
```

### ページ構成を変更する

`build.py` の `get_page_config()` 関数でページのアイコンや説明を設定できます。
