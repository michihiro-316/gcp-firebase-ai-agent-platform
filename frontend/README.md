# Frontend（フロントエンド）

チャットUIを提供するReactアプリケーションです。

## フォルダ構成

```
frontend/
├── src/
│   ├── App.tsx              # メインコンポーネント
│   ├── main.tsx             # エントリーポイント
│   ├── styles.css           # スタイル
│   ├── components/          # UIコンポーネント
│   │   ├── ChatScreen.tsx   # チャット画面
│   │   ├── LoginScreen.tsx  # ログイン画面
│   │   └── SessionTabs.tsx  # セッションタブ
│   ├── hooks/               # カスタムフック
│   │   ├── useAuth.ts       # 認証
│   │   ├── useChat.ts       # チャット
│   │   └── useSessions.ts   # セッション管理
│   └── services/            # API通信
│       ├── api.ts           # バックエンドAPI
│       └── firebase.ts      # Firebase初期化
├── index.html               # HTMLテンプレート
├── package.json             # npm設定
└── vite.config.ts           # Vite設定
```

## Firebase Hostingへのデプロイ方法

### 方法1: Firebaseコンソールからデプロイ

1. `npm run build` でビルド
2. `dist/` フォルダをFirebase Hostingにアップロード

### 方法2: Firebase CLIでデプロイ

```bash
# このフォルダに移動
cd frontend

# 環境変数を設定（.envファイルを作成）
echo "VITE_API_BASE_URL=https://your-backend-url" > .env

# ビルド
npm run build

# デプロイ
firebase deploy --only hosting
```

### 方法3: シェルスクリプトでデプロイ

```bash
# プロジェクトルートから実行
./infrastructure/deploy.sh
```

## ローカルでの実行方法

```bash
# このフォルダに移動
cd frontend

# 依存関係をインストール（初回のみ）
npm install

# 環境変数を設定
cp .env.example .env
# .envファイルを編集してFirebase設定を入力

# 開発サーバーを起動
npm run dev
```

ブラウザで http://localhost:5173 を開きます。

## 環境変数

`.env` ファイルに以下を設定：

```bash
# Firebase設定
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id

# バックエンドAPI URL
VITE_API_BASE_URL=http://localhost:8080
```

## UIのカスタマイズ

`src/styles.css` でデザインを変更できます。カラーパレットはCSS変数で定義されています：

```css
:root {
  --color-primary: #489F9D;      /* メインカラー */
  --color-primary-dark: #285958; /* 濃いメインカラー */
  --color-text: #333333;         /* テキスト色 */
}
```
