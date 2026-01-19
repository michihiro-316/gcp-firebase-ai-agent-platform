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
├── gateway/                 # 共通 Gateway（1つ）
├── customers/               # 顧客別コード
│   ├── _template/           # 新規顧客用テンプレート
│   │   ├── frontend/
│   │   └── backend/
│   └── {customer_id}/       # 顧客ごとにコピー
├── backend/                 # 共通バックエンド（開発用）
├── frontend/                # 共通フロントエンド（開発用）
└── learning/                # 学習用ドキュメント
```

---

## 主要ファイル

| ファイル | 役割 |
|----------|------|
| `customers/_template/backend/src/agents/_template/agent.py` | AI エージェントのテンプレート |
| `customers/{customer_id}/backend/src/main.py` | 顧客別 Backend API |
| `customers/{customer_id}/frontend/src/App.tsx` | 顧客別フロントエンド |
| `gateway/src/main.py` | Gateway エントリーポイント（共通） |
| `backend/src/main.py` | 開発用 Backend API |
| `frontend/src/App.tsx` | 開発用フロントエンド |

---

## コーディング規約

- Python: PEP 8 準拠
- 変数名: スネークケース（`agent_class` など）
- コメント: 初心者エンジニアが理解できる日本語で記述
- 不要なコード: 使用していない関数・変数は削除する
