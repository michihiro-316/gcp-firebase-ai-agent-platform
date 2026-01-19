#!/bin/bash
# =============================================================================
# Gateway Cloud Functions デプロイスクリプト
# =============================================================================
#
# 【このスクリプトでやること】
#   Gateway Cloud Functions をデプロイする
#
# 【使い方】
#   ./deploy-gateway.sh
#
# 【前提条件】
#   - gcloud CLI がインストールされていること
#   - PROJECT_ID 環境変数が設定されていること
#   - Firebase プロジェクトが設定済みであること
#
# 【Gateway の役割】
#   - Firebase 認証の検証
#   - customer_id に基づく振り分け
#   - リクエストの転送（プロキシ）
#
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# 設定値
# -----------------------------------------------------------------------------

# プロジェクトID（環境変数から取得）
PROJECT_ID="${PROJECT_ID:-}"
if [ -z "$PROJECT_ID" ]; then
    echo "エラー: PROJECT_ID を設定してください"
    echo "例: export PROJECT_ID=your-project-id"
    exit 1
fi

# リージョン
REGION="asia-northeast1"

# 関数名
FUNCTION_NAME="gateway"

# スクリプトのディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATEWAY_DIR="${SCRIPT_DIR}/../gateway/src"

# -----------------------------------------------------------------------------
# 色付きログ
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# -----------------------------------------------------------------------------
# メイン処理
# -----------------------------------------------------------------------------

echo ""
echo "============================================================================="
echo "  Gateway Cloud Functions デプロイ"
echo "============================================================================="
echo ""
echo "  プロジェクト:   ${PROJECT_ID}"
echo "  リージョン:     ${REGION}"
echo "  関数名:         ${FUNCTION_NAME}"
echo "  ソース:         ${GATEWAY_DIR}"
echo ""

# プロジェクトを設定
gcloud config set project "$PROJECT_ID"

# ソースディレクトリの確認
if [ ! -d "$GATEWAY_DIR" ]; then
    log_error "ソースディレクトリが見つかりません: $GATEWAY_DIR"
    exit 1
fi

if [ ! -f "$GATEWAY_DIR/main.py" ]; then
    log_error "main.py が見つかりません: $GATEWAY_DIR/main.py"
    exit 1
fi

log_step "Step 1: Gateway Cloud Functions をデプロイ"

log_info "デプロイ中..."

# Cloud Functions Gen2 でデプロイ
# --allow-unauthenticated について:
#   GCP IAM レベルでは認証なしでアクセス可能にしています。
#   これは、Firebase Authentication でアプリケーションレベルの認証を
#   行っているため、GCP IAM での二重認証は不要という設計です。
#   全てのAPIリクエストは main.py の verify_request() で
#   Firebase IDトークンを検証しています。
gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime python311 \
    --region "$REGION" \
    --source "$GATEWAY_DIR" \
    --entry-point main \
    --trigger-http \
    --allow-unauthenticated \
    --memory 512MB \
    --timeout 300s \
    --min-instances 0 \
    --max-instances 10

log_step "Step 2: デプロイ結果の確認"

# デプロイした URL を取得
GATEWAY_URL=$(gcloud functions describe "$FUNCTION_NAME" \
    --region="$REGION" \
    --format='value(serviceConfig.uri)')

# ヘルスチェック
log_info "ヘルスチェック中..."
HEALTH_RESPONSE=$(curl -s "${GATEWAY_URL}/health" || echo "failed")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    log_info "ヘルスチェック成功"
else
    log_warn "ヘルスチェックに失敗しました（デプロイ直後は正常です）"
fi

echo ""
echo "============================================================================="
echo "  Gateway デプロイ完了"
echo "============================================================================="
echo ""
echo "  URL: ${GATEWAY_URL}"
echo ""
echo "  【次のステップ】"
echo "  1. フロントエンドの VITE_API_BASE_URL を Gateway URL に変更"
echo "  2. Firestore の customers コレクションに cloud_functions_url を設定"
echo ""
echo "  【テスト方法】"
echo "  curl ${GATEWAY_URL}/health"
echo ""
echo "============================================================================="
