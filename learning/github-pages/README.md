# GitHub Pages 出力フォルダ

このフォルダには GitHub Actions によって自動生成されたHTMLファイルが配置されます。

## 仕組み

```
learning/md/*.md  ──(GitHub Actions)──>  learning/github-pages/*.html
                          │
                          ↓
                   GitHub Pages で公開
```

## 手動でHTMLを確認したい場合

ローカルでビルドする場合:

```bash
pip install markdown pygments
python learning/github-pages/build_local.py
```

## GitHub Pagesの設定方法

1. GitHubリポジトリ → Settings → Pages
2. Source を「GitHub Actions」に変更
3. learning/md/ にMarkdownを追加してプッシュ
4. 自動でHTMLが生成・公開される

公開URL: `https://<username>.github.io/<repo-name>/`
