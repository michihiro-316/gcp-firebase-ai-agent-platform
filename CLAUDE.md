# Claude Code 用プロジェクト設定

このファイルは Claude Code がプロジェクトを理解するための設定です。

---

## 用語定義

| 用語 | 意味 |
|------|------|
| Cloud Run | Cloud Run Functions（旧 Cloud Functions Gen2）と同義。このプロジェクトでは Docker を使用しない Cloud Run Functions を採用。 |
| Gateway | 認証とルーティングを担う Cloud Run Functions。顧客の Backend に転送する。 |
| Backend | 顧客ごとにデプロイされる Cloud Run Functions。AI エージェントを実行する。 |
| 顧客 | このプラットフォームを利用する企業。customer_id で識別。 |

---

## プロジェクト概要

- **目的**: 複数の顧客に AI チャットボットを提供するマルチテナントプラットフォーム
- **対象ユーザー**: Python 経験 2 ヶ月程度の初心者エンジニア
- **設計方針**: シンプル最優先、Docker 不使用

---

## ディレクトリ構成

```
gcp-firebase-ai-agent-platform/
├── backend/                 # バックエンド（Cloud Functionsにそのままデプロイ可）
│   ├── main.py              # エントリーポイント
│   ├── requirements.txt     # Python依存関係
│   ├── agents/              # AIエージェント
│   └── common/              # 共通モジュール
├── gateway/                 # 共通 Gateway（Cloud Functionsにそのままデプロイ可）
│   ├── main.py              # エントリーポイント
│   └── requirements.txt     # Python依存関係
├── frontend/                # フロントエンド（Firebase Hostingにデプロイ）
│   ├── src/                 # Reactソースコード
│   └── package.json         # npm設定
├── docs/                    # ドキュメント
│   ├── SETUP.md
│   ├── CUSTOMER_GUIDE.md
│   └── learning/            # 学習用ドキュメント
├── infrastructure/          # デプロイスクリプト
│   ├── deploy.sh
│   ├── deploy-customer.sh
│   └── firestore.rules
└── start.sh                 # 開発環境起動スクリプト
```

---

## 主要ファイル

| ファイル | 役割 |
|----------|------|
| `backend/agents/_template/agent.py` | AI エージェントのテンプレート（ここを編集） |
| `backend/main.py` | Backend API エントリーポイント |
| `gateway/main.py` | Gateway エントリーポイント |
| `frontend/src/App.tsx` | フロントエンド |

---

## デプロイ方法

### コピペでデプロイ（初心者向け）
各フォルダ（`backend/`, `gateway/`, `frontend/`）は自己完結しているため、
GCPコンソールからそのままCloud Functionsにアップロード可能。

### シェルスクリプトでデプロイ
```bash
./infrastructure/deploy.sh
```

詳細は各フォルダの README.md を参照。

---

## コーディング規約

- Python: PEP 8 準拠
- 変数名: スネークケース（`agent_class` など）
- コメント: 初心者エンジニアが理解できる日本語で記述
- 不要なコード: 使用していない関数・変数は削除する

---

## 未対応タスク (TODO)

### Firestore TTL 設定（優先度: 中）

**背景**:
- フロントエンドの localStorage は MAX_SESSIONS=10 で古いセッションを自動削除
- しかし Firestore の checkpoints データは削除されず蓄積し続ける
- 結果: localStorage から消えた threadId のデータが「死んだデータ」として残り、コストがかかる

**対応方法**:

1. **バックエンド変更** (`backend/agents/_base/firestore_checkpointer.py`)
   ```python
   from datetime import datetime, timedelta

   # ドキュメント保存時に expireAt フィールドを追加
   doc_data = {
       # 既存のデータ...
       "expireAt": datetime.now() + timedelta(days=30)  # 30日後に自動削除
   }
   ```

2. **GCP Console 設定**
   - Firestore → TTL policies → Create policy
   - Collection: `customers/{customer_id}/checkpoints`
   - Field: `expireAt`

**参考**: この設計は 2026-01-26 の会話で決定（セッション管理とデータ永続化の議論）

---

### useChat.ts コードスタイル統一（優先度: 低）

**背景**:
- `frontend/src/hooks/useChat.ts` で配列操作のスタイルが混在している
- 64行目・75行目: spread演算子 `[...array, item]`
- 102行目: `concat()` メソッド

**対応方法**:
- どちらかに統一する（機能的には同じ）
- 推奨: spread演算子に統一（モダンな書き方）

```typescript
// 現状（102行目）
const finalMessages = updatedMessagesWithUser.concat({
  ...assistantMessage,
  content: currentContent,
})

// 統一後
const finalMessages = [...updatedMessagesWithUser, {
  ...assistantMessage,
  content: currentContent,
}]
```

**参考**: 2026-01-26 の会話で発見

---

### useSessions.ts 不要な return 削除（優先度: 低）

**背景**:
- `frontend/src/hooks/useSessions.ts` の `createSession` 関数で `return newSession.id` がある
- しかし、この返り値はどこでも使われていない
- 関数名 `createSession` と返り値 `id` の不一致で混乱を招く

**対応方法**:
- `return newSession.id` を削除する

```typescript
// 現状
const createSession = useCallback(() => {
  const newSession = createNewSession()
  setSessions(prev => { ... })
  setActiveSessionId(newSession.id)
  return newSession.id  // ← 不要
}, [])

// 修正後
const createSession = useCallback(() => {
  const newSession = createNewSession()
  setSessions(prev => { ... })
  setActiveSessionId(newSession.id)
  // return を削除
}, [])
```

**参考**: 2026-01-28 の会話で発見
