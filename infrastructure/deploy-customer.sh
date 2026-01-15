#!/bin/bash
# =============================================================================
# 顧客別フロントエンドデプロイスクリプト
# =============================================================================
#
# 【このスクリプトでやること】
#   1. 指定した顧客のフロントエンドをビルド
#   2. GCSバケットの顧客ディレクトリにアップロード
#   3. キャッシュ設定の適用
#
# 【使い方】
#   ./deploy-customer.sh <customer_id>
#
# 【例】
#   ./deploy-customer.sh customer-a
#   ./deploy-customer.sh customer-b
#
# 【前提条件】
#   - frontend/ ディレクトリにフロントエンドのソースがあること
#   - GCSバケットが設定済みであること（setup-gcs-hosting.sh）
#
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# 設定値
# -----------------------------------------------------------------------------

# プロジェクトID
PROJECT_ID="${PROJECT_ID:-your-project-id}"

# バケット名
BUCKET_NAME="${PROJECT_ID}-frontend"

# リージョン
REGION="asia-northeast1"

# Cloud Functions名
FUNCTION_NAME="ai-agent-api"

# スクリプトのディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
# 引数チェック
# -----------------------------------------------------------------------------
CUSTOMER_ID="$1"

if [ -z "$CUSTOMER_ID" ]; then
    log_error "顧客IDを指定してください"
    echo ""
    echo "使い方: ./deploy-customer.sh <customer_id>"
    echo "例:     ./deploy-customer.sh customer-a"
    exit 1
fi

if [ "$PROJECT_ID" = "your-project-id" ]; then
    log_error "PROJECT_ID を設定してください"
    echo "例: export PROJECT_ID=my-actual-project-id"
    exit 1
fi

# -----------------------------------------------------------------------------
# Step 1: 顧客設定ファイルの確認/作成
# -----------------------------------------------------------------------------
create_customer_config() {
    log_step "Step 1: 顧客設定ファイルの準備"

    CONFIG_DIR="${PROJECT_ROOT}/frontend/customer-configs"
    CONFIG_FILE="${CONFIG_DIR}/${CUSTOMER_ID}.json"

    # 設定ディレクトリ作成
    mkdir -p "$CONFIG_DIR"

    # 設定ファイルが存在しない場合はテンプレートを作成
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warn "設定ファイルが見つかりません: $CONFIG_FILE"
        log_info "テンプレートを作成します..."

        # Cloud FunctionsのURLを取得
        FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" --region="$REGION" --format='value(serviceConfig.uri)' 2>/dev/null || echo "")

        if [ -z "$FUNCTION_URL" ]; then
            FUNCTION_URL="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"
            log_warn "Cloud FunctionsのURLを自動取得できませんでした。デフォルトURLを使用します。"
        fi

        # Firebase設定を取得（できれば）
        FIREBASE_API_KEY="${FIREBASE_API_KEY:-YOUR_API_KEY}"
        FIREBASE_AUTH_DOMAIN="${PROJECT_ID}.firebaseapp.com"

        cat > "$CONFIG_FILE" << EOF
{
  "customer_id": "${CUSTOMER_ID}",
  "customer_name": "${CUSTOMER_ID} 様",
  "theme": {
    "primary_color": "#1976d2",
    "secondary_color": "#dc004e"
  },
  "firebase": {
    "apiKey": "${FIREBASE_API_KEY}",
    "authDomain": "${FIREBASE_AUTH_DOMAIN}",
    "projectId": "${PROJECT_ID}"
  },
  "api": {
    "base_url": "${FUNCTION_URL}"
  }
}
EOF

        log_info "テンプレートを作成しました: $CONFIG_FILE"
        echo ""
        echo "============================================"
        echo "  重要: 設定ファイルを編集してください"
        echo "============================================"
        echo ""
        echo "  ファイル: $CONFIG_FILE"
        echo ""
        echo "  特に以下の値を確認してください:"
        echo "    - customer_name: 顧客の表示名"
        echo "    - theme.primary_color: テーマカラー"
        echo "    - firebase.apiKey: Firebase APIキー"
        echo ""
        echo "  編集後、このスクリプトを再実行してください。"
        echo ""
        exit 0
    fi

    log_info "設定ファイルを確認しました: $CONFIG_FILE"
}

# -----------------------------------------------------------------------------
# Step 2: フロントエンドのビルド
# -----------------------------------------------------------------------------
build_frontend() {
    log_step "Step 2: フロントエンドのビルド"

    cd "${PROJECT_ROOT}/frontend"

    # 顧客設定を public ディレクトリにコピー
    CONFIG_FILE="${PROJECT_ROOT}/frontend/customer-configs/${CUSTOMER_ID}.json"
    mkdir -p public
    cp "$CONFIG_FILE" "public/config.json"
    log_info "設定ファイルをコピーしました"

    # 依存関係インストール
    if [ ! -d "node_modules" ]; then
        log_info "依存関係をインストール中..."
        npm install
    fi

    # ビルド（baseパスを顧客ディレクトリに設定）
    log_info "ビルド中..."

    # vite.config.ts に base パスを設定するために環境変数を使用
    VITE_BASE_PATH="/${CUSTOMER_ID}/" npm run build

    log_info "ビルド完了"
}

# -----------------------------------------------------------------------------
# Step 3: GCSへのアップロード
# -----------------------------------------------------------------------------
upload_to_gcs() {
    log_step "Step 3: GCSへのアップロード"

    DIST_DIR="${PROJECT_ROOT}/frontend/dist"
    GCS_PATH="gs://${BUCKET_NAME}/${CUSTOMER_ID}/"

    if [ ! -d "$DIST_DIR" ]; then
        log_error "ビルド成果物が見つかりません: $DIST_DIR"
        exit 1
    fi

    # 既存ファイルを削除（オプション）
    log_info "既存ファイルを削除中..."
    gsutil -m rm -r "${GCS_PATH}**" 2>/dev/null || true

    # アップロード
    log_info "アップロード中..."
    gsutil -m cp -r "${DIST_DIR}/"* "$GCS_PATH"

    # 顧客設定もアップロード
    CONFIG_FILE="${PROJECT_ROOT}/frontend/customer-configs/${CUSTOMER_ID}.json"
    gsutil cp "$CONFIG_FILE" "${GCS_PATH}config.json"

    log_info "アップロード完了"
}

# -----------------------------------------------------------------------------
# Step 4: キャッシュ設定
# -----------------------------------------------------------------------------
configure_cache() {
    log_step "Step 4: キャッシュ設定"

    GCS_PATH="gs://${BUCKET_NAME}/${CUSTOMER_ID}/"

    # HTMLファイル: 短いキャッシュ（5分）
    log_info "HTMLファイルのキャッシュ設定..."
    gsutil -m setmeta -h "Cache-Control:public, max-age=300" \
        "${GCS_PATH}index.html" 2>/dev/null || true

    # JSファイル: 長いキャッシュ（1週間）- ハッシュ付きなので安全
    log_info "JSファイルのキャッシュ設定..."
    gsutil -m setmeta -h "Cache-Control:public, max-age=604800, immutable" \
        "${GCS_PATH}assets/*.js" 2>/dev/null || true

    # CSSファイル: 長いキャッシュ（1週間）
    log_info "CSSファイルのキャッシュ設定..."
    gsutil -m setmeta -h "Cache-Control:public, max-age=604800, immutable" \
        "${GCS_PATH}assets/*.css" 2>/dev/null || true

    # 設定ファイル: 短いキャッシュ（1分）
    log_info "設定ファイルのキャッシュ設定..."
    gsutil -m setmeta -h "Cache-Control:public, max-age=60" \
        "${GCS_PATH}config.json" 2>/dev/null || true

    log_info "キャッシュ設定完了"
}

# -----------------------------------------------------------------------------
# 結果表示
# -----------------------------------------------------------------------------
show_result() {
    # Load BalancerのドメインまたはGCS直接URLを表示
    DOMAIN="${DOMAIN:-app.example.com}"

    echo ""
    echo "============================================================================="
    echo "  デプロイ完了: ${CUSTOMER_ID}"
    echo "============================================================================="
    echo ""
    echo "  【アップロード先】"
    echo "    gs://${BUCKET_NAME}/${CUSTOMER_ID}/"
    echo ""
    echo "  【アクセスURL】"
    if [ "$DOMAIN" != "app.example.com" ]; then
        echo "    本番: https://${DOMAIN}/${CUSTOMER_ID}/"
    fi
    echo "    GCS直接: https://storage.googleapis.com/${BUCKET_NAME}/${CUSTOMER_ID}/index.html"
    echo ""
    echo "  【設定ファイル】"
    echo "    ${PROJECT_ROOT}/frontend/customer-configs/${CUSTOMER_ID}.json"
    echo ""
    echo "============================================================================="
}

# -----------------------------------------------------------------------------
# メイン処理
# -----------------------------------------------------------------------------
main() {
    echo ""
    echo "============================================================================="
    echo "  顧客別フロントエンドデプロイ"
    echo "============================================================================="
    echo ""
    echo "  顧客ID:     ${CUSTOMER_ID}"
    echo "  プロジェクト: ${PROJECT_ID}"
    echo "  バケット:    gs://${BUCKET_NAME}/"
    echo ""

    gcloud config set project "$PROJECT_ID"

    create_customer_config
    build_frontend
    upload_to_gcs
    configure_cache
    show_result
}

# 実行
main "$@"
