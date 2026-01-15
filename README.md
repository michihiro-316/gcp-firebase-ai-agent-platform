# GCP AIエージェント基盤

複数の顧客にAIチャットボットを提供するプラットフォームです。

---

## 🚀 はじめての方へ

### このプロジェクトを理解するために

```
📁 GCP/
├── 📖 README.md          ← 今読んでいるファイル
├── 📖 SETUP.md           ← GCP/Firebaseの初期設定手順
├── 📖 CUSTOMER_GUIDE.md  ← 顧客・ユーザー追加の手順
│
├── 📚 learning/          ← 【勉強用】ここから読み始めてください！
│   ├── md/               ← Markdownドキュメント
│   │   ├── 00_はじめに読んでください.md  ← ★最初にこれを読む
│   │   ├── 01_全体像.md
│   │   ├── 02_バックエンド解説.py
│   │   ├── 03_フロントエンド解説.md
│   │   ├── 04_動かしてみよう.md
│   │   ├── 05_顧客管理の仕組み.md
│   │   └── 06_コマンド解説.md    ← ★ターミナルコマンドの説明
│   │
│   ├── colab/            ← Google Colabノートブック（対話的に学習）
│   │   └── 01_Python基礎とバックエンド理解.ipynb
│   │
│   └── github-pages/     ← HTML化されたドキュメント（自動生成）
│
├── 🖥️ frontend/          ← 【本番】フロントエンド（React）
├── ⚙️ backend/           ← 【本番】バックエンド（Python）
│   ├── src/              ← ソースコード
│   └── scripts/          ← 管理スクリプト
└── ...
```

### 読む順番

| 順番 | ファイル | 内容 |
|------|----------|------|
| 1 | `learning/md/00_はじめに読んでください.md` | 勉強の進め方 |
| 2 | `learning/md/01_全体像.md` | システム全体の図解 |
| 3 | `learning/md/06_コマンド解説.md` | ターミナルコマンドの意味 |
| 4 | `SETUP.md` | 環境構築の手順 |
| 5 | `CUSTOMER_GUIDE.md` | 顧客追加の手順 |

### 学習方法を選ぶ

| 方式 | 場所 | おすすめの人 |
|------|------|-------------|
| **Markdown** | `learning/md/` | テキストで読みたい人 |
| **Google Colab** | `learning/colab/` | Pythonコードを実行しながら学びたい人 |
| **GitHub Pages** | 自動生成 | ブラウザできれいに読みたい人 |

---

## 📋 システム概要

### 何ができるか

- 複数の顧客（会社）にAIチャットボットを提供
- 顧客ごとにデータを完全に分離（セキュリティ確保）
- Googleアカウントでログイン

### 使用技術

| 領域 | 技術 |
|------|------|
| フロントエンド | React + TypeScript + Vite |
| バックエンド | Python + Flask + LangGraph |
| AI | Vertex AI (Gemini 1.5 Flash) |
| 認証 | Firebase Authentication |
| データベース | Firestore |
| ホスティング | Firebase Hosting + Cloud Run Functions |

---

## 🛠️ ローカル開発

### 必要なもの

- Python 3.11以上
- Node.js 18以上
- GCPプロジェクト（設定済み）

### 起動方法

> 💡 各コマンドの意味は `learning/md/06_コマンド解説.md` を参照

**ターミナル1（バックエンド）:**
```bash
cd backend                              # backendフォルダに移動
pip install -r requirements.txt         # 必要なパッケージをインストール
functions-framework --target=main --port=8080  # サーバーを起動
```

**ターミナル2（フロントエンド）:**
```bash
cd frontend                             # frontendフォルダに移動
npm install                             # 必要なパッケージをインストール
npm run dev                             # 開発サーバーを起動
```

**ブラウザで開く:** http://localhost:5173/

### コマンドの意味（簡易版）

| コマンド | 意味 |
|----------|------|
| `cd フォルダ名` | フォルダに移動する |
| `pip install -r requirements.txt` | Python用のライブラリをインストール |
| `npm install` | JavaScript用のライブラリをインストール |
| `functions-framework --target=main --port=8080` | バックエンドサーバーを8080番ポートで起動 |
| `npm run dev` | フロントエンドの開発サーバーを起動 |

詳しくは `learning/md/06_コマンド解説.md` を読んでください。

---

## 👥 顧客管理

### 新しい顧客を追加

```bash
cd backend
python scripts/manage_customer.py add acme-corp "株式会社ACME"
```

### ユーザーを顧客に紐付け

```bash
python scripts/manage_customer.py add-user acme-corp yamada@acme.co.jp
```

詳細は `CUSTOMER_GUIDE.md` を参照。

---

## 📁 主要ファイル

### バックエンド（Python）

| ファイル | 役割 |
|----------|------|
| `backend/src/main.py` | APIエントリーポイント |
| `backend/src/common/auth.py` | 認証・認可 |
| `backend/src/agents/sample_agent/agent.py` | AIエージェント |
| `backend/scripts/manage_customer.py` | 顧客管理スクリプト |

### フロントエンド（React）

| ファイル | 役割 |
|----------|------|
| `frontend/src/App.tsx` | メインコンポーネント |
| `frontend/src/hooks/useAuth.ts` | ログイン処理 |
| `frontend/src/hooks/useChat.ts` | チャット処理 |

---

## 🔒 セキュリティ

- Firebase Authentication（Google OAuth）
- ドメイン/メールによるアクセス制限
- 顧客ごとのデータ分離（マルチテナント）
- レート制限（10回/分/ユーザー）
- 未紐付けユーザーのアクセス拒否

---

## ❓ 困ったら

1. `learning/md/` フォルダの解説を読む
2. `learning/md/06_コマンド解説.md` でコマンドの意味を確認
3. Firebase Console / GCP Console でログを確認
4. `SETUP.md` のトラブルシューティングを確認
