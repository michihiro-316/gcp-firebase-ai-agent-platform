# GCP AIエージェント基盤

複数の顧客にAIチャットボットを提供するマルチテナントプラットフォームです。

---

## 🎯 このプロジェクトの特徴

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   🧠 AIエージェント開発に集中できる設計                              │
│                                                                     │
│   ┌─────────────────────┐     ┌─────────────────────┐              │
│   │  ✅ 触る場所        │     │  🔒 触らなくてOK    │              │
│   │  ─────────────     │     │  ──────────────    │              │
│   │  agent.py          │     │  認証・認可         │              │
│   │  (AIの性格・能力)   │     │  フロントエンド     │              │
│   │                    │     │  インフラ           │              │
│   └─────────────────────┘     └─────────────────────┘              │
│                                                                     │
│   データサイエンスチームはAIの「心臓部」に集中！                      │
│   認証やUIは自動で動きます。                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 前提条件

`./start.sh` を実行する前に、以下がインストールされていることを確認してください。

| ツール | バージョン | 確認コマンド | インストール（Mac） |
|--------|-----------|-------------|-------------------|
| Python | 3.11以上 | `python3 --version` | `brew install python` |
| Node.js | 18以上 | `node --version` | `brew install node` |

> **💡 ヒント**: `start.sh` は仮想環境の作成と依存関係のインストールを自動で行います。

### 本番デプロイ時に追加で必要なもの

| ツール | 用途 | インストール |
|--------|------|-------------|
| gcloud CLI | Cloud Functionsデプロイ | `brew install google-cloud-sdk` |
| Firebase CLI | Firebase Hostingデプロイ | `npm install -g firebase-tools` |

初期設定は `docs/SETUP.md` を参照してください。

---

## 🚀 クイックスタート（5分で起動）

### 1. 起動（1コマンド）

```bash
./start.sh
```

これだけで以下が自動実行されます：
- Python仮想環境の作成（なければ自動作成）
- Python依存関係のインストール
- バックエンド起動（Python/Flask）
- フロントエンド起動（React/Vite）
- 接続確認

### 2. ブラウザで開く

http://localhost:5173

### 3. AIをカスタマイズ

以下のファイルを編集:
```
backend/agents/_template/agent.py
```

このファイルの `SYSTEM_PROMPT` を編集するとAIの性格が変わります。

---

## 📁 ディレクトリ構成

```
📁 gcp-firebase-ai-agent-platform/
│
├── 🚀 start.sh              ← 開発環境を1コマンドで起動
│
├── 📖 README.md             ← 今読んでいるファイル
│
├── 📚 docs/                 ← 【ドキュメント】
│   ├── SETUP.md             ← GCP/Firebaseの初期設定
│   ├── CUSTOMER_GUIDE.md    ← 顧客追加の手順
│   └── learning/md/         ← 学習用ドキュメント
│       ├── 01_はじめに読んでください.md  ← ★最初にこれ
│       ├── 02_全体像.md                  ← システム構成図
│       ├── 03_バックエンド解説.md        ← Python/Flask
│       ├── 04_フロントエンド解説.md      ← React/TypeScript
│       ├── 06_コマンド解説.md            ← ★コマンドの意味
│       ├── 07_動かしてみよう.md          ← ハンズオン
│       └── 08_AIカスタマイズ.md          ← ★AI編集ガイド
│
├── ⚙️ backend/              ← 【バックエンド】Cloud Functionsにそのままデプロイ可
│   ├── main.py              ← エントリーポイント
│   ├── requirements.txt     ← Python依存関係
│   ├── agents/_template/    ← 🧠 AIエージェント（ここを編集）
│   └── common/              ← 共通モジュール
│
├── 🚪 gateway/              ← 【Gateway】Cloud Functionsにそのままデプロイ可
│   ├── main.py              ← 認証・ルーティング
│   └── requirements.txt     ← Python依存関係
│
├── 🖥️ frontend/             ← 【フロントエンド】Firebase Hostingにデプロイ
│   ├── src/                 ← Reactソースコード
│   └── package.json         ← npm設定
│
└── 🛠️ infrastructure/       ← 【デプロイスクリプト】
    ├── deploy.sh            ← 本番環境にデプロイ
    ├── deploy-customer.sh   ← 顧客別デプロイ
    └── firestore.rules      ← Firestoreセキュリティルール
```

**デプロイ方法:**
- **コピペ**: 各フォルダ（`backend/`, `gateway/`, `frontend/`）をGCPコンソールから直接アップロード
- **シェルスクリプト**: `./infrastructure/deploy.sh` を実行

---

## 📚 学習ガイド

### あなたは誰ですか？

| あなた | 読むべきドキュメント |
|--------|----------------------|
| **データサイエンティスト** | `08_AIカスタマイズ.md` → `agent.py` を編集 |
| **新人エンジニア** | `01_はじめに〜.md` → `07_動かしてみよう.md` |
| **PM** | `01_全体像.md` → `CUSTOMER_GUIDE.md` |
| **フルスタック** | `02_バックエンド解説.md` → `03_フロントエンド解説.md` |
| **インフラ担当** | `docs/learning/md/10_Gatewayアーキテクチャ.md` → マルチテナント構成 |

### 推奨学習順序

```
1️⃣  ./start.sh で起動        ← まず動かす（5分）
2️⃣  ブラウザでチャット       ← 動作確認（5分）
3️⃣  agent.py を編集          ← AIをカスタマイズ（30分）
4️⃣  06_コマンド解説.md       ← 仕組みを理解（1時間）
5️⃣  01_全体像.md             ← 全体を俯瞰（1時間）
```

---

## 🛠️ 主要コマンド

### 開発

| コマンド | 説明 |
|----------|------|
| `./start.sh` | 開発環境を起動 |
| `Ctrl+C` | 停止 |

### デプロイ

| コマンド | 説明 |
|----------|------|
| `./infrastructure/deploy.sh` | 本番環境にデプロイ |
| `./infrastructure/deploy-customer.sh acme-corp` | 顧客別デプロイ |

### 顧客管理

```bash
cd backend

# 顧客追加
python scripts/manage_customer.py add acme-corp "株式会社ACME"

# メールドメイン登録（社員全員が自動振り分け）
python scripts/manage_customer.py add-domain acme-corp acme.co.jp
```

詳細は `docs/CUSTOMER_GUIDE.md` を参照。

---

## 🏗️ 使用技術

| 領域 | 技術 | 説明 |
|------|------|------|
| **AI** | LangGraph + Vertex AI | AIエージェントの心臓部 |
| バックエンド | Python + Flask | API処理 |
| フロントエンド | React + TypeScript | UI |
| 認証 | Firebase Auth | Googleログイン |
| データベース | Firestore | 会話履歴など |
| ホスティング | Cloud Functions + Firebase Hosting | デプロイ先 |

**LangGraph** は2025年最も成長しているAIエージェントフレームワークです。
- 月間9,000万ダウンロード
- Uber, LinkedIn, JPMorgan等が本番採用
- AIエンジニアの必須スキル

---

## 🔒 セキュリティ

- Firebase Authentication（Google OAuth）
- 顧客ごとのデータ完全分離（マルチテナント）
- レート制限（DoS対策）
- メッセージ長制限（コスト攻撃対策）
- Custom Claimsによるアクセス制御

---

## ❓ 困ったら

| 状況 | 対処 |
|------|------|
| コマンドの意味がわからない | `docs/learning/md/06_コマンド解説.md` |
| AIの応答を変えたい | `docs/learning/md/08_AIカスタマイズ.md` |
| 全体像を理解したい | `docs/learning/md/02_全体像.md` |
| エラーが出た | `docs/SETUP.md` のトラブルシューティング |
| 顧客を追加したい | `docs/CUSTOMER_GUIDE.md` |

---

## 📖 用語集（最初に覚える5つ）

| 用語 | 一言で言うと | イメージ |
|------|-------------|---------|
| **Cloud Functions** | サーバーなしでPythonを動かす場所 | レンタルキッチン（使った分だけ支払い） |
| **Gateway** | 玄関番（認証・振り分け担当） | マンションの受付 |
| **Backend** | AIが住んでいる場所 | 料理人がいる厨房 |
| **LangGraph** | AIに「記憶」と「思考の流れ」を持たせるツール | 料理人のレシピノート |
| **Firestore** | データを保存する場所（会話履歴など） | 冷蔵庫 |

> **💡 なぜ Gateway と Backend が分かれているの？**
>
> 複数の会社（顧客）に対応するため。Gateway が「どの会社のユーザーか」を判定し、
> その会社専用の Backend に転送します。これにより顧客ごとにAIをカスタマイズできます。

---

## 📊 プロジェクト情報

| 項目 | 値 |
|------|------|
| 対象ユーザー | データサイエンスチーム、Python開発者 |
| 必要スキル | Python基礎（React/TypeScriptは不要） |
| 推定学習時間 | 1〜2日（基本操作） |
| 本番運用開始 | 1週間〜 |
