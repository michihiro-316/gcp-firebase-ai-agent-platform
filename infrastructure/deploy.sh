#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  deploy.sh - 簡易デプロイスクリプト                                           ║
# ╠══════════════════════════════════════════════════════════════════════════════╣
# ║                                                                              ║
# ║  🎯 役割:                                                                    ║
# ║     ローカルのコードをGoogle Cloud Platform（GCP）にデプロイします            ║
# ║                                                                              ║
# ║  📝 使い方:                                                                  ║
# ║     ./deploy.sh                    # デフォルト顧客としてデプロイ            ║
# ║     ./deploy.sh acme-corp          # 顧客別デプロイ                          ║
# ║                                                                              ║
# ║  🔄 処理の流れ:                                                              ║
# ║     1. バックエンド → Cloud Functions にデプロイ                             ║
# ║     2. フロントエンド → ビルド → Firebase Hosting にデプロイ                 ║
# ║     3. Firestore ルール → Firestore にデプロイ                               ║
# ║                                                                              ║
# ║  📚 詳細: learning/md/06_コマンド解説.md                                     ║
# ║                                                                              ║
# ║  ⚠️  本番デプロイ前に必ず SETUP.md の設定を完了してください                   ║
# ║                                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -e  # エラー時に停止

# 色の定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 引数からカスタマーIDを取得（デフォルト: 環境変数またはdefault）
CUSTOMER_ID=${1:-${CUSTOMER_ID:-"default"}}

# プロジェクトルートに移動
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 デプロイを開始します                                    ║${NC}"
echo -e "${BLUE}║     顧客ID: ${CUSTOMER_ID}                                           ${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 事前チェック
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${YELLOW}📋 事前チェック...${NC}"

# gcloud認証チェック
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null 2>&1; then
    echo -e "${RED}❌ gcloud にログインしていません${NC}"
    echo "   実行: gcloud auth login"
    exit 1
fi

# プロジェクトID取得
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ GCPプロジェクトが設定されていません${NC}"
    echo "   実行: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "   ${GREEN}✅ プロジェクト: ${PROJECT_ID}${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 1: バックエンドデプロイ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${YELLOW}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│ Step 1/3: バックエンドをCloud Functionsにデプロイ           │${NC}"
echo -e "${YELLOW}│                                                             │${NC}"
echo -e "${YELLOW}│ 📁 ソース: backend/src/                                     │${NC}"
echo -e "${YELLOW}│ 🎯 デプロイ先: Cloud Functions (Python 3.11)                │${NC}"
echo -e "${YELLOW}│                                                             │${NC}"
echo -e "${YELLOW}│ 💡 これにより以下が作成されます:                             │${NC}"
echo -e "${YELLOW}│    - HTTPエンドポイント（/chat, /health等）                  │${NC}"
echo -e "${YELLOW}│    - Vertex AI (Gemini) との接続                             │${NC}"
echo -e "${YELLOW}└─────────────────────────────────────────────────────────────┘${NC}"

cd "$PROJECT_ROOT/backend"

FUNCTION_NAME="${CUSTOMER_ID}-chat-api"

gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime=python311 \
    --region=asia-northeast1 \
    --source=src \
    --entry-point=main \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars="CUSTOMER_ID=${CUSTOMER_ID},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --memory=512MB \
    --timeout=300s

# デプロイされたURLを取得
BACKEND_URL=$(gcloud functions describe "$FUNCTION_NAME" --region=asia-northeast1 --format="value(serviceConfig.uri)")

echo -e "   ${GREEN}✅ バックエンドデプロイ完了${NC}"
echo -e "   ${GREEN}   URL: ${BACKEND_URL}${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 2: フロントエンドビルド＆デプロイ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${YELLOW}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│ Step 2/3: フロントエンドをFirebase Hostingにデプロイ        │${NC}"
echo -e "${YELLOW}│                                                             │${NC}"
echo -e "${YELLOW}│ 📁 ソース: frontend/src/                                    │${NC}"
echo -e "${YELLOW}│ 🔧 ビルド: npm run build → dist/                            │${NC}"
echo -e "${YELLOW}│ 🎯 デプロイ先: Firebase Hosting                             │${NC}"
echo -e "${YELLOW}│                                                             │${NC}"
echo -e "${YELLOW}│ 💡 これにより以下が作成されます:                             │${NC}"
echo -e "${YELLOW}│    - 静的Webサイト（React）                                  │${NC}"
echo -e "${YELLOW}│    - HTTPS対応のURL                                         │${NC}"
echo -e "${YELLOW}└─────────────────────────────────────────────────────────────┘${NC}"

cd "$PROJECT_ROOT/frontend"

# .envファイルにAPIのURLを設定
echo "VITE_API_URL=${BACKEND_URL}" > .env.production

# ビルド
echo "   📦 フロントエンドをビルド中..."
npm run build

# Firebase Hostingにデプロイ
echo "   🚀 Firebase Hostingにデプロイ中..."
firebase deploy --only hosting

echo -e "   ${GREEN}✅ フロントエンドデプロイ完了${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 3: Firestoreルールデプロイ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${YELLOW}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│ Step 3/3: Firestoreセキュリティルールをデプロイ             │${NC}"
echo -e "${YELLOW}│                                                             │${NC}"
echo -e "${YELLOW}│ 📁 ソース: firestore.rules                                  │${NC}"
echo -e "${YELLOW}│ 🎯 デプロイ先: Firestore                                    │${NC}"
echo -e "${YELLOW}│                                                             │${NC}"
echo -e "${YELLOW}│ 💡 これによりデータベースのアクセス制御が設定されます         │${NC}"
echo -e "${YELLOW}└─────────────────────────────────────────────────────────────┘${NC}"

cd "$PROJECT_ROOT"

firebase deploy --only firestore:rules

echo -e "   ${GREEN}✅ Firestoreルールデプロイ完了${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 完了メッセージ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ デプロイ完了！                                          ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║  📊 デプロイ結果:                                          ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║  バックエンド（Cloud Functions）:                          ║${NC}"
echo -e "${GREEN}║    ${BACKEND_URL}${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║  フロントエンド（Firebase Hosting）:                       ║${NC}"
echo -e "${GREEN}║    https://${PROJECT_ID}.web.app                           ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║  📚 次のステップ:                                          ║${NC}"
echo -e "${GREEN}║    1. 上記URLにアクセスして動作確認                        ║${NC}"
echo -e "${GREEN}║    2. Googleログインでサインイン                           ║${NC}"
echo -e "${GREEN}║    3. チャットを送信してAIの応答を確認                     ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
