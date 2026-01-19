# サンプルレンダラー

**このディレクトリのファイルは参考実装です。直接使用しないでください。**

---

## 使い方

1. 使いたいファイルを `renderers/{customer_id}/` にコピー
2. `renderers/index.ts` に登録
3. 必要に応じてカスタマイズ

```bash
# 例: acme-corp 用にテーブルレンダラーを使う
mkdir ../acme-corp
cp TableRenderer.tsx ../acme-corp/MessageRenderer.tsx
```

---

## 含まれるサンプル

| ファイル | 説明 | 注意点 |
|----------|------|--------|
| `TableRenderer.tsx` | JSON形式のテーブルデータを表として表示 | 安全 |
| `MarkdownRenderer.tsx` | マークダウン記法を解釈して表示 | XSSリスクあり |

---

## MarkdownRenderer の警告

`MarkdownRenderer.tsx` は `dangerouslySetInnerHTML` を使用しています。

**本番環境では以下の対応が必要です:**

```bash
npm install react-markdown
```

```tsx
// 推奨: react-markdown を使用
import ReactMarkdown from 'react-markdown'

<ReactMarkdown>{content}</ReactMarkdown>
```

詳細はファイル内のコメントを参照してください。
