# チャットレンダラー

顧客ごとにチャットの表示形式をカスタマイズできます。

---

## ディレクトリ構成

```
renderers/
├── README.md           ← このファイル
├── types.ts            ← 型定義
├── index.ts            ← レンダラー選択ロジック
├── default/            ← デフォルト（シンプルなテキスト表示）
│   ├── MessageRenderer.tsx
│   └── index.ts
└── _examples/          ← サンプル実装（直接使用しない）
    ├── README.md
    ├── TableRenderer.tsx
    └── MarkdownRenderer.tsx
```

---

## カスタマイズ手順

### 1. 顧客用ディレクトリを作成

```bash
mkdir src/renderers/acme-corp
```

### 2. サンプルをコピー

```bash
cp src/renderers/_examples/TableRenderer.tsx \
   src/renderers/acme-corp/MessageRenderer.tsx
```

### 3. index.ts に登録

```typescript
// src/renderers/index.ts

import { MessageRenderer as AcmeCorpMessageRenderer } from './acme-corp/MessageRenderer'

const customerRenderers: Record<string, typeof DefaultMessageRenderer> = {
  'acme-corp': AcmeCorpMessageRenderer,
}
```

### 4. 再ビルド＆デプロイ

```bash
./infrastructure/deploy-customer.sh acme-corp --frontend-only
```

---

## 初心者向け情報

**このフォルダは上級者向けです。**

チャットの表示をカスタマイズしたい場合のみ使います。
基本的な機能は `default/` のレンダラーで十分です。

まずは以下を理解してから触ることをおすすめします:
- React コンポーネントの基本
- TypeScript の型定義
- `hooks/useChat.ts` の Message 型

---

## JSON設定でのカスタマイズ

コードを書かずに色やフォントを変更できます。

`frontend/customer-configs/{customer_id}.json`:

```json
{
  "chatRenderer": {
    "styling": {
      "userMessageBg": "#e3f2fd",
      "assistantMessageBg": "#f5f5f5"
    }
  }
}
```

詳細は `types.ts` の `ChatRendererConfig` を参照してください。
