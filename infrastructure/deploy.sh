#!/bin/bash
#
# デプロイスクリプト
#
# 使い方:
#   ./infrastructure/deploy.sh [PROJECT_ID]
#
# 例:
#   ./infrastructure/deploy.sh my-ai-agent-project

set -e

# プロジェクトID
PROJECT_ID=${1:-$GOOGLE_CLOUD_PROJECT}

if [ -z "$PROJECT_ID" ]; then
  echo "エラー: プロジェクトIDを指定してください"
  echo "使い方: ./infrastructure/deploy.sh [PROJECT_ID]"
  exit 1
fi

echo "=== プロジェクト: $PROJECT_ID ==="

# プロジェクトを設定
gcloud config set project $PROJECT_ID

# ===== バックエンドデプロイ =====
echo ""
echo "=== バックエンドをデプロイ中... ==="
cd backend

# 本番用の許可オリジンを設定
ALLOWED_ORIGINS="https://${PROJECT_ID}.web.app,https://${PROJECT_ID}.firebaseapp.com"

gcloud functions deploy ai-agent-api \
  --gen2 \
  --runtime=python311 \
  --region=asia-northeast1 \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=300s \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},ALLOWED_ORIGINS=${ALLOWED_ORIGINS},VERTEX_AI_LOCATION=asia-northeast1"

# Cloud FunctionsのURLを取得
FUNCTION_URL=$(gcloud functions describe ai-agent-api --region=asia-northeast1 --format='value(serviceConfig.uri)')
echo "バックエンドURL: $FUNCTION_URL"

cd ..

# ===== フロントエンドデプロイ =====
echo ""
echo "=== フロントエンドをデプロイ中... ==="
cd frontend

# .envファイルを更新（本番URL）
cat > .env << EOF
VITE_FIREBASE_API_KEY=$(firebase apps:sdkconfig WEB --project $PROJECT_ID | grep apiKey | cut -d'"' -f2)
VITE_FIREBASE_AUTH_DOMAIN=${PROJECT_ID}.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=${PROJECT_ID}
VITE_API_BASE_URL=${FUNCTION_URL}
EOF

# ビルド
npm install
npm run build

# デプロイ
firebase deploy --only hosting --project $PROJECT_ID

cd ..

# ===== Firestoreルールデプロイ =====
echo ""
echo "=== Firestoreルールをデプロイ中... ==="
firebase deploy --only firestore:rules --project $PROJECT_ID

echo ""
echo "=== デプロイ完了 ==="
echo "フロントエンドURL: https://${PROJECT_ID}.web.app"
echo "バックエンドURL: ${FUNCTION_URL}"
