#!/bin/bash
# =============================================================================
# 顧客別デプロイスクリプト（バックエンド + フロントエンド）
# =============================================================================
#
# 【このスクリプトでやること】
#   1. バックエンド（Cloud Functions）を顧客専用としてデプロイ
#   2. 指定した顧客のフロントエンドをビルド
#   3. GCSバケットの顧客ディレクトリにアップロード
#   4. キャッシュ設定の適用
#
# 【使い方】
#   ./deploy-customer.sh <customer_id> [options]
#
#   オプション:
#     --frontend-only    フロントエンドのみデプロイ
#     --backend-only     バックエンドのみデプロイ
#
# 【例】
#   ./deploy-customer.sh customer-a              # 両方デプロイ
#   ./deploy-customer.sh customer-a --frontend-only  # フロントエンドのみ
#   ./deploy-customer.sh customer-a --backend-only   # バックエンドのみ
#
# 【前提条件】
#   - frontend/ ディレクトリにフロントエンドのソースがあること
#   - backend/customer-configs/{customer_id}.env が存在すること
#   - GCSバケットが設定済みであること（setup-gcs-hosting.sh）
#
# 【GCS構造】
#   gs://{project}-frontend/
#     common/                  # 共通ファイル（利用規約など）
#     customers/
#       {customer_id}/         # 顧客ごとのフロントエンド
#         index.html
#         assets/
#         config.json
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
CUSTOMER_ID=""
DEPLOY_FRONTEND=true
DEPLOY_BACKEND=true

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend-only)
            DEPLOY_BACKEND=false
            shift
            ;;
        --backend-only)
            DEPLOY_FRONTEND=false
            shift
            ;;
        -*)
            log_error "不明なオプション: $1"
            exit 1
            ;;
        *)
            if [ -z "$CUSTOMER_ID" ]; then
                CUSTOMER_ID="$1"
            fi
            shift
            ;;
    esac
done

if [ -z "$CUSTOMER_ID" ]; then
    log_error "顧客IDを指定してください"
    echo ""
    echo "使い方: ./deploy-customer.sh <customer_id> [options]"
    echo ""
    echo "オプション:"
    echo "  --frontend-only    フロントエンドのみデプロイ"
    echo "  --backend-only     バックエンドのみデプロイ"
    echo ""
    echo "例:     ./deploy-customer.sh customer-a"
    echo "        ./deploy-customer.sh customer-a --backend-only"
    exit 1
fi

if [ "$PROJECT_ID" = "your-project-id" ]; then
    log_error "PROJECT_ID を設定してください"
    echo "例: export PROJECT_ID=my-actual-project-id"
    exit 1
fi

# バックエンド設定ファイルのパス
BACKEND_CONFIG_DIR="${PROJECT_ROOT}/backend/customer-configs"
BACKEND_CONFIG_FILE="${BACKEND_CONFIG_DIR}/${CUSTOMER_ID}.env"

# -----------------------------------------------------------------------------
# Step 0: バックエンド設定ファイルの確認
# -----------------------------------------------------------------------------
check_backend_config() {
    if [ "$DEPLOY_BACKEND" = false ]; then
        return 0
    fi

    log_step "Step 0: バックエンド設定ファイルの確認"

    # 設定ディレクトリ作成
    mkdir -p "$BACKEND_CONFIG_DIR"

    # 設定ファイルが存在しない場合はテンプレートをコピー
    if [ ! -f "$BACKEND_CONFIG_FILE" ]; then
        TEMPLATE_FILE="${BACKEND_CONFIG_DIR}/template.env"

        if [ -f "$TEMPLATE_FILE" ]; then
            log_warn "バックエンド設定ファイルが見つかりません: $BACKEND_CONFIG_FILE"
            log_info "テンプレートから作成します..."

            cp "$TEMPLATE_FILE" "$BACKEND_CONFIG_FILE"

            # CUSTOMER_ID を自動で置換
            sed -i.bak "s/CUSTOMER_ID=your-customer-id/CUSTOMER_ID=${CUSTOMER_ID}/" "$BACKEND_CONFIG_FILE"
            rm -f "${BACKEND_CONFIG_FILE}.bak"

            log_info "テンプレートを作成しました: $BACKEND_CONFIG_FILE"
            echo ""
            echo "============================================"
            echo "  重要: バックエンド設定ファイルを編集してください"
            echo "============================================"
            echo ""
            echo "  ファイル: $BACKEND_CONFIG_FILE"
            echo ""
            echo "  特に以下の値を確認してください:"
            echo "    - DEFAULT_AGENT: デフォルトで使用するエージェント"
            echo "    - ALLOWED_AGENTS: 使用を許可するエージェント（カンマ区切り）"
            echo ""
            echo "  編集後、このスクリプトを再実行してください。"
            echo ""
            exit 0
        else
            log_error "テンプレートファイルが見つかりません: $TEMPLATE_FILE"
            exit 1
        fi
    fi

    log_info "バックエンド設定ファイルを確認しました: $BACKEND_CONFIG_FILE"

    # 設定内容を読み込んで表示
    log_info "設定内容:"
    grep -E "^(CUSTOMER_ID|DEFAULT_AGENT|ALLOWED_AGENTS)=" "$BACKEND_CONFIG_FILE" | while read line; do
        echo "  $line"
    done
}

# -----------------------------------------------------------------------------
# Step 1: バックエンドのデプロイ（Cloud Functions）
# -----------------------------------------------------------------------------
deploy_backend() {
    if [ "$DEPLOY_BACKEND" = false ]; then
        return 0
    fi

    log_step "Step 1: バックエンドのデプロイ"

    cd "${PROJECT_ROOT}/backend"

    # 顧客専用の Cloud Functions 名
    CUSTOMER_FUNCTION_NAME="${CUSTOMER_ID}-api"

    # 環境変数を設定ファイルから読み込み
    log_info "環境変数を読み込み中..."

    # .env ファイルをソース（export）
    set -a
    source "$BACKEND_CONFIG_FILE"
    set +a

    # 追加の環境変数を設定
    export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"

    # 環境変数をカンマ区切りの文字列に変換
    ENV_VARS="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
    ENV_VARS="${ENV_VARS},CUSTOMER_ID=${CUSTOMER_ID}"
    ENV_VARS="${ENV_VARS},DEFAULT_AGENT=${DEFAULT_AGENT:-sample}"
    ENV_VARS="${ENV_VARS},ALLOWED_AGENTS=${ALLOWED_AGENTS:-}"
    ENV_VARS="${ENV_VARS},VERTEX_AI_LOCATION=${VERTEX_AI_LOCATION:-asia-northeast1}"

    log_info "Cloud Functions をデプロイ中: ${CUSTOMER_FUNCTION_NAME}"
    log_info "環境変数:"
    log_info "  CUSTOMER_ID=${CUSTOMER_ID}"
    log_info "  DEFAULT_AGENT=${DEFAULT_AGENT:-sample}"
    log_info "  ALLOWED_AGENTS=${ALLOWED_AGENTS:-（制限なし）}"
    # 注: ENV_VARS全体は出力しない（機密情報保護のため）

    # Cloud Functions v2 でデプロイ
    # --allow-unauthenticated について:
    #   GCPレベルでは認証なしでアクセス可能にしています。
    #   これは、Firebase Authentication でアプリケーションレベルの認証を
    #   行っているため、GCP IAM での二重認証は不要という設計です。
    #   全てのAPIリクエストは main.py の authenticate_request() で
    #   Firebase IDトークンを検証しています。
    gcloud functions deploy "$CUSTOMER_FUNCTION_NAME" \
        --gen2 \
        --runtime python311 \
        --region "$REGION" \
        --source . \
        --entry-point main \
        --trigger-http \
        --allow-unauthenticated \
        --set-env-vars "$ENV_VARS" \
        --memory 512MB \
        --timeout 300s \
        --min-instances 0 \
        --max-instances 10

    # デプロイしたFunctionのURLを取得
    CUSTOMER_FUNCTION_URL=$(gcloud functions describe "$CUSTOMER_FUNCTION_NAME" --region="$REGION" --format='value(serviceConfig.uri)')
    log_info "デプロイ完了: ${CUSTOMER_FUNCTION_URL}"

    # URLをエクスポート（フロントエンド設定で使用）
    export CUSTOMER_FUNCTION_URL
}

# -----------------------------------------------------------------------------
# Step 2: 顧客フロントエンド設定ファイルの確認/作成
# -----------------------------------------------------------------------------
create_customer_config() {
    if [ "$DEPLOY_FRONTEND" = false ]; then
        return 0
    fi

    log_step "Step 2: フロントエンド設定ファイルの準備"

    CONFIG_DIR="${PROJECT_ROOT}/frontend/customer-configs"
    CONFIG_FILE="${CONFIG_DIR}/${CUSTOMER_ID}.json"

    # 設定ディレクトリ作成
    mkdir -p "$CONFIG_DIR"

    # 顧客専用の Cloud Functions 名
    CUSTOMER_FUNCTION_NAME="${CUSTOMER_ID}-api"

    # 設定ファイルが存在しない場合はテンプレートを作成
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warn "設定ファイルが見つかりません: $CONFIG_FILE"
        log_info "テンプレートを作成します..."

        # Cloud FunctionsのURLを取得
        FUNCTION_URL=$(gcloud functions describe "$CUSTOMER_FUNCTION_NAME" --region="$REGION" --format='value(serviceConfig.uri)' 2>/dev/null || echo "")

        if [ -z "$FUNCTION_URL" ]; then
            # バックエンドデプロイで取得したURLを使用
            FUNCTION_URL="${CUSTOMER_FUNCTION_URL:-https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${CUSTOMER_FUNCTION_NAME}}"
            log_warn "Cloud FunctionsのURLを自動取得できませんでした。推測URLを使用します。"
        fi

        # Firebase設定を取得（できれば）
        FIREBASE_API_KEY="${FIREBASE_API_KEY:-YOUR_API_KEY}"
        FIREBASE_AUTH_DOMAIN="${PROJECT_ID}.firebaseapp.com"

        cat > "$CONFIG_FILE" << EOF
{
  "customerId": "${CUSTOMER_ID}",
  "customerName": "${CUSTOMER_ID} 様",
  "theme": {
    "primaryColor": "#1976d2",
    "secondaryColor": "#dc004e"
  },
  "firebase": {
    "apiKey": "${FIREBASE_API_KEY}",
    "authDomain": "${FIREBASE_AUTH_DOMAIN}",
    "projectId": "${PROJECT_ID}"
  },
  "api": {
    "baseUrl": "${FUNCTION_URL}"
  },
  "chatRenderer": {
    "output": {
      "enableTables": true,
      "enableCharts": false,
      "enableCodeHighlight": true,
      "enableMarkdown": true,
      "maxWidth": "800px"
    },
    "styling": {
      "userMessageBg": "#e3f2fd",
      "assistantMessageBg": "#f5f5f5",
      "fontFamily": "system-ui, sans-serif"
    }
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
# Step 3: フロントエンドのビルド
# -----------------------------------------------------------------------------
build_frontend() {
    if [ "$DEPLOY_FRONTEND" = false ]; then
        return 0
    fi

    log_step "Step 3: フロントエンドのビルド"

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
    VITE_BASE_PATH="/customers/${CUSTOMER_ID}/" npm run build

    log_info "ビルド完了"
}

# -----------------------------------------------------------------------------
# Step 4: GCSへのアップロード
# -----------------------------------------------------------------------------
upload_to_gcs() {
    if [ "$DEPLOY_FRONTEND" = false ]; then
        return 0
    fi

    log_step "Step 4: GCSへのアップロード"

    DIST_DIR="${PROJECT_ROOT}/frontend/dist"
    GCS_PATH="gs://${BUCKET_NAME}/customers/${CUSTOMER_ID}/"

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
# Step 5: キャッシュ設定
# -----------------------------------------------------------------------------
configure_cache() {
    if [ "$DEPLOY_FRONTEND" = false ]; then
        return 0
    fi

    log_step "Step 5: キャッシュ設定"

    GCS_PATH="gs://${BUCKET_NAME}/customers/${CUSTOMER_ID}/"

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
    CUSTOMER_FUNCTION_NAME="${CUSTOMER_ID}-api"

    echo ""
    echo "============================================================================="
    echo "  デプロイ完了: ${CUSTOMER_ID}"
    echo "============================================================================="
    echo ""

    if [ "$DEPLOY_BACKEND" = true ]; then
        echo "  【バックエンド（Cloud Functions）】"
        echo "    関数名: ${CUSTOMER_FUNCTION_NAME}"
        if [ -n "$CUSTOMER_FUNCTION_URL" ]; then
            echo "    URL: ${CUSTOMER_FUNCTION_URL}"
        fi
        echo "    設定: ${BACKEND_CONFIG_FILE}"
        echo ""
    fi

    if [ "$DEPLOY_FRONTEND" = true ]; then
        echo "  【フロントエンド（GCS）】"
        echo "    アップロード先: gs://${BUCKET_NAME}/customers/${CUSTOMER_ID}/"
        if [ "$DOMAIN" != "app.example.com" ]; then
            echo "    本番URL: https://${DOMAIN}/customers/${CUSTOMER_ID}/"
        fi
        echo "    GCS直接: https://storage.googleapis.com/${BUCKET_NAME}/customers/${CUSTOMER_ID}/index.html"
        echo "    設定: ${PROJECT_ROOT}/frontend/customer-configs/${CUSTOMER_ID}.json"
        echo ""
    fi

    echo "============================================================================="
}

# -----------------------------------------------------------------------------
# メイン処理
# -----------------------------------------------------------------------------
main() {
    echo ""
    echo "============================================================================="
    echo "  顧客別デプロイ（バックエンド + フロントエンド）"
    echo "============================================================================="
    echo ""
    echo "  顧客ID:       ${CUSTOMER_ID}"
    echo "  プロジェクト:   ${PROJECT_ID}"
    echo "  リージョン:     ${REGION}"
    echo ""
    echo "  デプロイ対象:"
    [ "$DEPLOY_BACKEND" = true ] && echo "    - バックエンド（Cloud Functions）"
    [ "$DEPLOY_FRONTEND" = true ] && echo "    - フロントエンド（GCS: gs://${BUCKET_NAME}/customers/）"
    echo ""

    gcloud config set project "$PROJECT_ID"

    # Step 0: バックエンド設定確認
    check_backend_config

    # Step 1: バックエンドデプロイ
    deploy_backend

    # Step 2: フロントエンド設定確認/作成
    create_customer_config

    # Step 3: フロントエンドビルド
    build_frontend

    # Step 4: GCSアップロード
    upload_to_gcs

    # Step 5: キャッシュ設定
    configure_cache

    # 結果表示
    show_result
}

# 実行
main
