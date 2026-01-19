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

## 🚀 クイックスタート（5分で起動）

### 1. 起動（1コマンド）

```bash
./start.sh
```

これだけで以下が自動実行されます：
- バックエンド起動（Python/Flask）
- フロントエンド起動（React/Vite）
- 接続確認

### 2. ブラウザで開く

http://localhost:5173

### 3. AIをカスタマイズ

開発時は以下のファイルを編集:
```
src/backend/src/agents/_template/agent.py
```

このファイルの `SYSTEM_PROMPT` を編集するとAIの性格が変わります。

> **本番デプロイ時**: 顧客ごとに `templates/_template/` をコピーして使用。
> 詳細は `docs/CUSTOMER_GUIDE.md` を参照。

---

## 📁 ディレクトリ構成

```
📁 GCP/
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
├── 📂 src/                  ← 【ソースコード】
│   ├── 🚪 gateway/          ← Gateway（認証・ルーティング）
│   │   └── src/main.py
│   ├── ⚙️ backend/          ← バックエンド（Python/Flask）
│   │   └── src/
│   │       ├── main.py
│   │       ├── common/      ← 共通モジュール
│   │       └── agents/_template/  ← 🧠 AIエージェント
│   └── 🖥️ frontend/         ← フロントエンド（React）
│       └── src/
│
├── 🛠️ infrastructure/       ← 【デプロイスクリプト】
│   ├── deploy.sh            ← 本番環境にデプロイ
│   ├── deploy-customer.sh   ← 顧客別デプロイ
│   └── firestore.rules      ← Firestoreセキュリティルール
│
└── 📋 templates/            ← 【顧客用テンプレート】
    └── _template/           ← 新規顧客用テンプレート
```

**開発 vs 本番の違い:**
- **開発時**: `src/backend/` と `src/frontend/` を使用（`./start.sh`）
- **本番時**: `templates/_template/` をコピーして顧客別にデプロイ

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
cd src/backend

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

## 📊 プロジェクト情報

| 項目 | 値 |
|------|------|
| 対象ユーザー | データサイエンスチーム、Python開発者 |
| 必要スキル | Python基礎（React/TypeScriptは不要） |
| 推定学習時間 | 1〜2日（基本操作） |
| 本番運用開始 | 1週間〜 |
