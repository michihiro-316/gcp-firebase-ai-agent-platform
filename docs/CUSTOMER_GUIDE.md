# 顧客追加ガイド

新しい顧客を追加する手順です。

---

## 手順

### 1. バックエンド設定ファイルを作成

顧客ごとに異なるAIエージェントを使用するため、まずバックエンド設定ファイルを作成します。

```bash
# テンプレートをコピー
cp src/backend/customer-configs/template.env src/backend/customer-configs/<顧客ID>.env

# 例
cp src/backend/customer-configs/template.env src/backend/customer-configs/acme-corp.env
```

設定ファイルを編集して、使用するエージェントを指定します：

```env
# src/backend/customer-configs/acme-corp.env
CUSTOMER_ID=acme-corp
DEFAULT_AGENT=acme-corp       # この顧客専用エージェントを指定
```

### 1.5. 顧客専用エージェントを作成（オプション）

AIの応答をカスタマイズする場合は、顧客専用エージェントを作成します。

```bash
# テンプレートをコピー
cd src/backend/src/agents
cp -r _template acme-corp

# agent.py の SYSTEM_PROMPT を編集
vim acme-corp/agent.py
```

```python
# src/backend/src/agents/acme-corp/agent.py
class AcmeCorpAgent(BaseAgent):
    SYSTEM_PROMPT = """あなたはACME社の専門AIアシスタントです。
ACME社の製品・サービスに関する質問に答えてください。"""
```

main.py に登録:
```python
from agents.acme_corp.agent import AcmeCorpAgent

AGENTS = {
    "template": TemplateAgent,
    "acme-corp": AcmeCorpAgent,  # 追加
}
```

**重要:**
- カスタマイズしない場合は `DEFAULT_AGENT=template` のままでOK
- 詳細は `learning/md/08_AIカスタマイズ.md` を参照（docs/learning/md/）

### 2. 顧客をFirestoreに登録

```bash
cd src/backend
python scripts/manage_customer.py add <顧客ID> "<顧客名>"

# 例
python scripts/manage_customer.py add acme-corp "株式会社ACME"
```

### 3. バックエンド＆フロントエンドをデプロイ

```bash
# 環境変数を設定
export PROJECT_ID=your-gcp-project-id

# 両方デプロイ（推奨）
./infrastructure/deploy-customer.sh acme-corp

# バックエンドのみ
./infrastructure/deploy-customer.sh acme-corp --backend-only

# フロントエンドのみ
./infrastructure/deploy-customer.sh acme-corp --frontend-only
```

初回実行時は設定ファイルのテンプレートが作成されます。編集後に再実行してください。

### 4. ユーザーを顧客に紐付け

#### 方法A: メールドメインで自動振り分け（推奨）

メールドメイン（メールアドレスの@以降）を登録すると、該当するメールドメインのユーザーを全員自動で振り分けできます。

```bash
# メールドメインを登録（例: @acme.co.jp のユーザーを全員自動振り分け）
python scripts/manage_customer.py add-domain acme-corp acme.co.jp

# 複数のメールドメインを登録する場合
python scripts/manage_customer.py add-domain acme-corp group.acme.co.jp
```

#### 方法B: 個別メール登録（業務委託者など）

会社のメールドメインを持たない外部の人を個別に登録します。

```bash
# 個別のメールアドレスを登録
python scripts/manage_customer.py add-email acme-corp tanaka@gmail.com
```

#### 方法C: 手動紐付け（特殊ケース）

自動振り分けを使わない場合のみ。ユーザーが先にGoogleログインしている必要があります。

```bash
python scripts/manage_customer.py add-user <顧客ID> <メールアドレス>

# 例
python scripts/manage_customer.py add-user acme-corp yamada@acme.co.jp
```

**どの方法を使う？**

| 場面 | 推奨コマンド | 理由 |
|------|-------------|------|
| 社内ユーザー（@company.co.jp） | `add-domain` | 社員全員を一括登録 |
| 業務委託者（Gmail等） | `add-email` | 個別登録で柔軟対応 |
| 特殊ケース | `add-user` | 手動で明示的に設定 |

### 5. 確認

```bash
# 顧客一覧
python scripts/manage_customer.py list

# 顧客詳細
python scripts/manage_customer.py show acme-corp

# ユーザー詳細
python scripts/manage_customer.py show-user yamada@acme.co.jp
```

---

## アーキテクチャ

顧客ごとに独立したバックエンド（Cloud Functions）をデプロイすることで、
顧客別に異なるAIエージェントを適用できます。

```
                    Cloud Load Balancer
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    /customer-a/*     /customer-b/*     /customer-c/*
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Cloud Functions │ │ Cloud Functions │ │ Cloud Functions │
│ customer-a-api  │ │ customer-b-api  │ │ customer-c-api  │
│ (SampleAgent)   │ │  (RAGAgent)     │ │ (CustomAgent)   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │    Firestore    │
                    │  (customer_id   │
                    │   でデータ分離)  │
                    └─────────────────┘
```

---

## GCS（フロントエンド）構造

```
gs://{project}-frontend/
  common/                      # 共通ファイル（利用規約など）
  customers/
    {customer_id}/             # 顧客ごとのフロントエンド
      index.html
      assets/
      config.json              # 顧客設定（レンダラー設定含む）
```

---

## カスタムレンダラー（チャット表示のカスタマイズ）

顧客ごとにチャットの表示形式をカスタマイズできます。

### 設定ファイルでのカスタマイズ

`src/frontend/customer-configs/{customer_id}.json` の `chatRenderer` セクションを編集：

```json
{
  "chatRenderer": {
    "output": {
      "enableTables": true,      // テーブル表示
      "enableCharts": false,     // グラフ表示
      "enableCodeHighlight": true,
      "enableMarkdown": true,
      "maxWidth": "800px"
    },
    "styling": {
      "userMessageBg": "#e3f2fd",
      "assistantMessageBg": "#f5f5f5",
      "fontFamily": "system-ui, sans-serif"
    }
  }
}
```

### コードでのカスタマイズ（TypeScript/Reactの知識が必要）

顧客専用のレンダラーコンポーネントを作成できます：

**手順1.** サンプルをコピーして顧客フォルダを作成

```bash
mkdir src/frontend/src/renderers/acme-corp
cp src/frontend/src/renderers/_examples/TableRenderer.tsx \
   src/frontend/src/renderers/acme-corp/MessageRenderer.tsx
```

**手順2.** `src/frontend/src/renderers/index.ts` に登録

```typescript
// ファイル冒頭のインポートに追加
import { MessageRenderer as AcmeCorpMessageRenderer } from './acme-corp/MessageRenderer'

// customerRenderers に追加
const customerRenderers: Record<string, typeof DefaultMessageRenderer> = {
  'acme-corp': AcmeCorpMessageRenderer,
}
```

**手順3.** 再ビルド＆デプロイ

```bash
./infrastructure/deploy-customer.sh acme-corp --frontend-only
```

サンプルは `src/frontend/src/renderers/_examples/` を参照してください：
- `MarkdownRenderer.tsx` - Markdown対応（セキュリティ上の注意あり）
- `TableRenderer.tsx` - テーブル形式データ対応

---

## カスタマイズの役割分担

| カスタマイズ内容 | 言語 | ファイル |
|-----------------|------|----------|
| AIの応答内容・性格 | **Python** | `src/backend/src/agents/{customer_id}/agent.py` |
| 使用エージェントの指定 | 設定ファイル | `src/backend/customer-configs/*.env` |
| チャットの色・フォント | **JSON** | `src/frontend/customer-configs/*.json` |
| チャット表示の高度なカスタマイズ | TypeScript | `src/frontend/src/renderers/{customer_id}/` |

**推奨**: Python開発者の方は、まずバックエンド（Python）のカスタマイズから始めてください。
フロントエンドの高度なカスタマイズ（TypeScript）は必要に応じて後から対応できます。

---

## 注意事項

- ユーザーは紐付け後、**再ログイン**が必要です
- 顧客IDは英数字とハイフンのみ使用してください
- 1ユーザーは1顧客にのみ所属できます
- バックエンド設定ファイル（`.env`）を変更した場合は再デプロイが必要です
- フロントエンド設定（`config.json`）を変更した場合も再デプロイが必要です

---

## Firestoreのデータ構造

```
customers/
  {customer_id}/
    name: "株式会社ACME"
    created_at: ...
    checkpoints/
      {thread_id}/
        checkpoints/
          {checkpoint_id}: {...}

users/
  {uid}/
    email: "yamada@acme.co.jp"
    customer_id: "acme-corp"
```

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| ユーザーが見つからない | 未ログイン | ユーザーに先にログインしてもらう |
| 古い顧客データが見える | 再ログインしていない | ユーザーに再ログインしてもらう |
| 権限エラー | Custom Claims未反映 | 最大1分待って再試行 |
