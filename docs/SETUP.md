# GCP AIエージェントプラットフォーム セットアップガイド

## 1. GCPプロジェクト作成

### 1.1 Google Cloud Console でプロジェクト作成
1. https://console.cloud.google.com/ にアクセス
2. 上部の「プロジェクトを選択」→「新しいプロジェクト」
3. プロジェクト名を入力（例: `ai-agent-platform`）
4. 「作成」をクリック

### 1.2 請求先アカウント設定
1. 左メニュー「お支払い」→「リンクされた請求先アカウント」
2. 請求先アカウントを選択または新規作成

### 1.3 必要なAPIを有効化
Cloud Shell または gcloud CLI で以下を実行:

```bash
# プロジェクトIDを設定（あなたのプロジェクトIDに置き換え）
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 必要なAPIを有効化
gcloud services enable \
  cloudfunctions.googleapis.com \
  run.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

---

## 2. Firebase設定

### 2.1 Firebaseプロジェクト追加
1. https://console.firebase.google.com/ にアクセス
2. 「プロジェクトを追加」
3. 「既存のGoogle Cloudプロジェクトに追加」を選択
4. 作成したGCPプロジェクトを選択
5. Googleアナリティクスは任意（不要なら無効化してOK）

### 2.2 Webアプリ登録
1. Firebaseコンソールで「プロジェクトの概要」横の歯車→「プロジェクトの設定」
2. 「マイアプリ」セクションで「</>」（Web）をクリック
3. アプリ名を入力（例: `ai-agent-web`）
4. 「Firebase Hostingも設定」にチェック
5. 「アプリを登録」

表示される設定情報をメモ:
```javascript
const firebaseConfig = {
  apiKey: "xxx",
  authDomain: "xxx.firebaseapp.com",
  projectId: "xxx",
  storageBucket: "xxx.appspot.com",
  messagingSenderId: "xxx",
  appId: "xxx"
};
```

### 2.3 Firebase Authentication設定
1. 左メニュー「Authentication」→「始める」
2. 「Sign-in method」タブ
3. 「Google」を選択して有効化
4. サポートメールを設定
5. 「保存」

### 2.4 Firestore作成
1. 左メニュー「Firestore Database」→「データベースを作成」
2. 「本番環境モード」を選択
3. ロケーション: `asia-northeast1`（東京）
4. 「有効にする」

---

## 3. アクセス制御設定（Firestore）

Firestoreで許可ユーザー/ドメインを管理します。

### 3.1 許可ドメイン設定
Firestoreコンソールで以下のドキュメントを作成:

**コレクション**: `config`
**ドキュメントID**: `access_control`

```json
{
  "allowed_domains": ["example.com", "company.co.jp"],
  "allowed_emails": ["guest@gmail.com", "partner@other.com"],
  "rate_limit_per_minute": 10
}
```

---

## 4. ローカル開発環境セットアップ

### 4.1 必要なツール
- Node.js 18以上
- Python 3.11以上
- Firebase CLI

```bash
# Firebase CLIインストール
npm install -g firebase-tools

# Firebaseにログイン
firebase login

# プロジェクト選択
firebase use your-project-id
```

### 4.2 サービスアカウントキー取得（ローカル開発用）
1. GCPコンソール→「IAMと管理」→「サービスアカウント」
2. デフォルトのサービスアカウントをクリック
3. 「キー」タブ→「鍵を追加」→「新しい鍵を作成」
4. JSON形式でダウンロード
5. `backend/service-account.json` として保存（.gitignoreに追加済み）

### 4.3 環境変数設定

**backend/.env**
```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
ALLOWED_ORIGINS=http://localhost:5173
VERTEX_AI_LOCATION=asia-northeast1
```

**frontend/.env**
```
VITE_FIREBASE_API_KEY=xxx
VITE_FIREBASE_AUTH_DOMAIN=xxx.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=xxx
VITE_API_BASE_URL=http://localhost:8080
```

### 4.4 ローカルサーバー起動

**ターミナル1: バックエンド**
```bash
cd backend
pip install -r requirements.txt
functions-framework --target=main --port=8080
```

**ターミナル2: フロントエンド**
```bash
cd frontend
npm install
npm run dev
```

ブラウザで http://localhost:5173 を開いてください。

---

## 5. デプロイ

### 5.1 バックエンドデプロイ（Cloud Run Functions）
```bash
cd backend

gcloud functions deploy ai-agent-api \
  --gen2 \
  --runtime=python311 \
  --region=asia-northeast1 \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=your-project-id,ALLOWED_ORIGINS=https://your-project-id.web.app,VERTEX_AI_LOCATION=asia-northeast1"
```

### 5.2 フロントエンドデプロイ（Firebase Hosting）
```bash
cd frontend

# ビルド
npm run build

# デプロイ
firebase deploy --only hosting
```

---

## トラブルシューティング

### よくあるエラー

**「CORS エラー」が出る場合**
- backend/.env の `ALLOWED_ORIGINS` を確認
- フロントエンドのURLと一致しているか確認

**「認証エラー」が出る場合**
- Firebase Authentication でGoogleプロバイダが有効か確認
- `config/access_control` ドキュメントにドメイン/メールが登録されているか確認

**「Vertex AI エラー」が出る場合**
- Vertex AI APIが有効化されているか確認
- サービスアカウントに「Vertex AI ユーザー」ロールがあるか確認
