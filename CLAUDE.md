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
├── src/                     # ソースコード
│   ├── gateway/             # 共通 Gateway（1つ）
│   ├── backend/             # バックエンド（開発用）
│   └── frontend/            # フロントエンド（開発用）
├── docs/                    # ドキュメント
│   ├── SETUP.md
│   ├── CUSTOMER_GUIDE.md
│   └── learning/            # 学習用ドキュメント
├── infrastructure/          # デプロイスクリプト
│   ├── deploy.sh
│   ├── deploy-customer.sh
│   └── firestore.rules
└── templates/               # 顧客用テンプレート
    └── _template/
```

---

## 主要ファイル

| ファイル | 役割 |
|----------|------|
| `templates/_template/backend/src/agents/_template/agent.py` | AI エージェントのテンプレート |
| `src/gateway/src/main.py` | Gateway エントリーポイント（共通） |
| `src/backend/src/main.py` | 開発用 Backend API |
| `src/frontend/src/App.tsx` | 開発用フロントエンド |

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

1. **バックエンド変更** (`src/backend/src/agents/_base/firestore_checkpointer.py`)
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
