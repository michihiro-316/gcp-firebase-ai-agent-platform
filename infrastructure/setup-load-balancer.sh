#!/bin/bash
# =============================================================================
# Cloud Load Balancer + CDN 設定スクリプト
# =============================================================================
#
# 【このスクリプトでやること】
#   1. 外部静的IPアドレスの予約
#   2. SSL証明書の作成（マネージド）
#   3. GCSバケット用バックエンドバケットの作成
#   4. Cloud Functions用サーバーレスNEGの作成
#   5. URLマップの設定（パスベースルーティング）
#   6. HTTPSプロキシとフォワーディングルールの作成
#   7. Cloud CDNの有効化
#
# 【前提条件】
#   - setup-gcs-hosting.sh を実行済み
#   - カスタムドメインのDNS設定が可能であること
#
# 【実行方法】
#   chmod +x setup-load-balancer.sh
#   ./setup-load-balancer.sh
#
# =============================================================================

set -e  # エラー時に停止

# -----------------------------------------------------------------------------
# 設定値（ここを環境に合わせて変更）
# -----------------------------------------------------------------------------

# プロジェクトID（必須）
PROJECT_ID="${PROJECT_ID:-your-project-id}"

# カスタムドメイン（必須: あなたのドメインに変更）
# 例: app.example.com
DOMAIN="${DOMAIN:-app.example.com}"

# リージョン
REGION="asia-northeast1"

# リソース名のプレフィックス
PREFIX="ai-agent"

# バケット名
BUCKET_NAME="${PROJECT_ID}-frontend"

# Cloud Functions名
FUNCTION_NAME="ai-agent-api"

# -----------------------------------------------------------------------------
# 色付きログ出力
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
# 前提条件チェック
# -----------------------------------------------------------------------------
check_prerequisites() {
    log_step "前提条件チェック"

    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI がインストールされていません"
        exit 1
    fi

    if [ "$PROJECT_ID" = "your-project-id" ]; then
        log_error "PROJECT_ID を設定してください"
        echo "例: export PROJECT_ID=my-actual-project-id"
        exit 1
    fi

    if [ "$DOMAIN" = "app.example.com" ]; then
        log_warn "DOMAIN が設定されていません。デモ用に進めます。"
        log_warn "本番環境では必ず実際のドメインを設定してください。"
        echo "例: export DOMAIN=app.yourdomain.com"
    fi

    gcloud config set project "$PROJECT_ID"
    log_info "プロジェクト: $PROJECT_ID"
    log_info "ドメイン: $DOMAIN"

    # 必要なAPIを有効化
    log_info "必要なAPIを有効化中..."
    gcloud services enable compute.googleapis.com --quiet
}

# -----------------------------------------------------------------------------
# Step 1: 静的IPアドレスの予約
# -----------------------------------------------------------------------------
reserve_ip_address() {
    log_step "Step 1: 静的IPアドレスの予約"

    IP_NAME="${PREFIX}-ip"

    if gcloud compute addresses describe "$IP_NAME" --global &> /dev/null; then
        log_warn "IPアドレスは既に存在します: $IP_NAME"
    else
        gcloud compute addresses create "$IP_NAME" \
            --ip-version=IPV4 \
            --global
        log_info "IPアドレスを予約しました: $IP_NAME"
    fi

    # IPアドレスを取得
    IP_ADDRESS=$(gcloud compute addresses describe "$IP_NAME" --global --format="value(address)")
    log_info "IPアドレス: $IP_ADDRESS"

    echo ""
    echo "============================================"
    echo "  重要: DNSレコードを設定してください"
    echo "============================================"
    echo ""
    echo "  ドメイン: $DOMAIN"
    echo "  タイプ:   A"
    echo "  値:       $IP_ADDRESS"
    echo ""
    echo "  DNS設定が完了してから次に進んでください。"
    echo "  (DNS反映には数分〜数時間かかる場合があります)"
    echo ""
}

# -----------------------------------------------------------------------------
# Step 2: SSL証明書の作成
# -----------------------------------------------------------------------------
create_ssl_certificate() {
    log_step "Step 2: SSL証明書の作成（Google マネージド）"

    CERT_NAME="${PREFIX}-cert"

    if gcloud compute ssl-certificates describe "$CERT_NAME" --global &> /dev/null; then
        log_warn "SSL証明書は既に存在します: $CERT_NAME"
    else
        gcloud compute ssl-certificates create "$CERT_NAME" \
            --domains="$DOMAIN" \
            --global
        log_info "SSL証明書を作成しました: $CERT_NAME"
        log_warn "証明書のプロビジョニングには最大60分かかる場合があります"
    fi
}

# -----------------------------------------------------------------------------
# Step 3: バックエンドバケットの作成（GCS用）
# -----------------------------------------------------------------------------
create_backend_bucket() {
    log_step "Step 3: バックエンドバケットの作成（GCS用）"

    BACKEND_BUCKET_NAME="${PREFIX}-backend-bucket"

    if gcloud compute backend-buckets describe "$BACKEND_BUCKET_NAME" &> /dev/null; then
        log_warn "バックエンドバケットは既に存在します: $BACKEND_BUCKET_NAME"
    else
        gcloud compute backend-buckets create "$BACKEND_BUCKET_NAME" \
            --gcs-bucket-name="$BUCKET_NAME" \
            --enable-cdn \
            --cache-mode=CACHE_ALL_STATIC \
            --default-ttl=3600 \
            --max-ttl=86400
        log_info "バックエンドバケットを作成しました: $BACKEND_BUCKET_NAME"
    fi
}

# -----------------------------------------------------------------------------
# Step 4: サーバーレスNEGの作成（Cloud Functions用）
# -----------------------------------------------------------------------------
create_serverless_neg() {
    log_step "Step 4: サーバーレスNEGの作成（Cloud Functions用）"

    NEG_NAME="${PREFIX}-neg"

    if gcloud compute network-endpoint-groups describe "$NEG_NAME" --region="$REGION" &> /dev/null; then
        log_warn "サーバーレスNEGは既に存在します: $NEG_NAME"
    else
        gcloud compute network-endpoint-groups create "$NEG_NAME" \
            --region="$REGION" \
            --network-endpoint-type=serverless \
            --cloud-function-name="$FUNCTION_NAME"
        log_info "サーバーレスNEGを作成しました: $NEG_NAME"
    fi
}

# -----------------------------------------------------------------------------
# Step 5: バックエンドサービスの作成（Cloud Functions用）
# -----------------------------------------------------------------------------
create_backend_service() {
    log_step "Step 5: バックエンドサービスの作成（Cloud Functions用）"

    BACKEND_SERVICE_NAME="${PREFIX}-backend-service"
    NEG_NAME="${PREFIX}-neg"

    if gcloud compute backend-services describe "$BACKEND_SERVICE_NAME" --global &> /dev/null; then
        log_warn "バックエンドサービスは既に存在します: $BACKEND_SERVICE_NAME"
    else
        # バックエンドサービス作成
        gcloud compute backend-services create "$BACKEND_SERVICE_NAME" \
            --global \
            --load-balancing-scheme=EXTERNAL_MANAGED \
            --protocol=HTTPS

        # NEGをバックエンドとして追加
        gcloud compute backend-services add-backend "$BACKEND_SERVICE_NAME" \
            --global \
            --network-endpoint-group="$NEG_NAME" \
            --network-endpoint-group-region="$REGION"

        log_info "バックエンドサービスを作成しました: $BACKEND_SERVICE_NAME"
    fi
}

# -----------------------------------------------------------------------------
# Step 6: URLマップの作成
# -----------------------------------------------------------------------------
create_url_map() {
    log_step "Step 6: URLマップの作成（パスベースルーティング）"

    URL_MAP_NAME="${PREFIX}-url-map"
    BACKEND_BUCKET_NAME="${PREFIX}-backend-bucket"
    BACKEND_SERVICE_NAME="${PREFIX}-backend-service"

    if gcloud compute url-maps describe "$URL_MAP_NAME" &> /dev/null; then
        log_warn "URLマップは既に存在します: $URL_MAP_NAME"
        log_info "URLマップを更新します..."

        # 既存のURLマップを削除して再作成
        # 注意: 本番環境では慎重に行うこと
    else
        # URLマップの設定をYAMLファイルに書き出し
        cat > /tmp/url-map.yaml << EOF
name: ${URL_MAP_NAME}
defaultService: https://www.googleapis.com/compute/v1/projects/${PROJECT_ID}/global/backendBuckets/${BACKEND_BUCKET_NAME}
hostRules:
- hosts:
  - "${DOMAIN}"
  - "*"
  pathMatcher: path-matcher
pathMatchers:
- name: path-matcher
  defaultService: https://www.googleapis.com/compute/v1/projects/${PROJECT_ID}/global/backendBuckets/${BACKEND_BUCKET_NAME}
  routeRules:
  # /api/* は Cloud Functions へ
  - priority: 1
    matchRules:
    - prefixMatch: /api/
    service: https://www.googleapis.com/compute/v1/projects/${PROJECT_ID}/global/backendServices/${BACKEND_SERVICE_NAME}
    routeAction:
      urlRewrite:
        pathPrefixRewrite: /
  # /health は Cloud Functions へ
  - priority: 2
    matchRules:
    - prefixMatch: /health
    service: https://www.googleapis.com/compute/v1/projects/${PROJECT_ID}/global/backendServices/${BACKEND_SERVICE_NAME}
  # それ以外は GCS へ（デフォルト）
EOF

        gcloud compute url-maps import "$URL_MAP_NAME" \
            --source=/tmp/url-map.yaml \
            --global \
            --quiet

        rm /tmp/url-map.yaml
        log_info "URLマップを作成しました: $URL_MAP_NAME"
    fi

    echo ""
    echo "  ルーティング設定:"
    echo "    /api/*     → Cloud Functions (${FUNCTION_NAME})"
    echo "    /health    → Cloud Functions (${FUNCTION_NAME})"
    echo "    /*         → GCS Bucket (gs://${BUCKET_NAME}/)"
    echo ""
}

# -----------------------------------------------------------------------------
# Step 7: HTTPSプロキシの作成
# -----------------------------------------------------------------------------
create_https_proxy() {
    log_step "Step 7: HTTPSプロキシの作成"

    PROXY_NAME="${PREFIX}-https-proxy"
    URL_MAP_NAME="${PREFIX}-url-map"
    CERT_NAME="${PREFIX}-cert"

    if gcloud compute target-https-proxies describe "$PROXY_NAME" &> /dev/null; then
        log_warn "HTTPSプロキシは既に存在します: $PROXY_NAME"
    else
        gcloud compute target-https-proxies create "$PROXY_NAME" \
            --url-map="$URL_MAP_NAME" \
            --ssl-certificates="$CERT_NAME" \
            --global
        log_info "HTTPSプロキシを作成しました: $PROXY_NAME"
    fi
}

# -----------------------------------------------------------------------------
# Step 8: フォワーディングルールの作成
# -----------------------------------------------------------------------------
create_forwarding_rule() {
    log_step "Step 8: フォワーディングルールの作成"

    RULE_NAME="${PREFIX}-https-rule"
    PROXY_NAME="${PREFIX}-https-proxy"
    IP_NAME="${PREFIX}-ip"

    if gcloud compute forwarding-rules describe "$RULE_NAME" --global &> /dev/null; then
        log_warn "フォワーディングルールは既に存在します: $RULE_NAME"
    else
        gcloud compute forwarding-rules create "$RULE_NAME" \
            --load-balancing-scheme=EXTERNAL_MANAGED \
            --network-tier=PREMIUM \
            --address="$IP_NAME" \
            --target-https-proxy="$PROXY_NAME" \
            --global \
            --ports=443
        log_info "フォワーディングルールを作成しました: $RULE_NAME"
    fi
}

# -----------------------------------------------------------------------------
# Step 9: HTTP→HTTPSリダイレクト（オプション）
# -----------------------------------------------------------------------------
create_http_redirect() {
    log_step "Step 9: HTTP→HTTPSリダイレクト設定"

    HTTP_PROXY_NAME="${PREFIX}-http-proxy"
    HTTP_RULE_NAME="${PREFIX}-http-rule"
    REDIRECT_URL_MAP_NAME="${PREFIX}-redirect-url-map"
    IP_NAME="${PREFIX}-ip"

    # リダイレクト用URLマップ
    if ! gcloud compute url-maps describe "$REDIRECT_URL_MAP_NAME" &> /dev/null; then
        cat > /tmp/redirect-url-map.yaml << EOF
name: ${REDIRECT_URL_MAP_NAME}
defaultUrlRedirect:
  httpsRedirect: true
  redirectResponseCode: MOVED_PERMANENTLY_DEFAULT
EOF
        gcloud compute url-maps import "$REDIRECT_URL_MAP_NAME" \
            --source=/tmp/redirect-url-map.yaml \
            --global \
            --quiet
        rm /tmp/redirect-url-map.yaml
        log_info "リダイレクト用URLマップを作成しました"
    fi

    # HTTPプロキシ
    if ! gcloud compute target-http-proxies describe "$HTTP_PROXY_NAME" &> /dev/null; then
        gcloud compute target-http-proxies create "$HTTP_PROXY_NAME" \
            --url-map="$REDIRECT_URL_MAP_NAME" \
            --global
        log_info "HTTPプロキシを作成しました"
    fi

    # HTTPフォワーディングルール
    if ! gcloud compute forwarding-rules describe "$HTTP_RULE_NAME" --global &> /dev/null; then
        gcloud compute forwarding-rules create "$HTTP_RULE_NAME" \
            --load-balancing-scheme=EXTERNAL_MANAGED \
            --network-tier=PREMIUM \
            --address="$IP_NAME" \
            --target-http-proxy="$HTTP_PROXY_NAME" \
            --global \
            --ports=80
        log_info "HTTPフォワーディングルールを作成しました"
    fi

    log_info "HTTP→HTTPSリダイレクト設定完了"
}

# -----------------------------------------------------------------------------
# 結果表示
# -----------------------------------------------------------------------------
show_result() {
    IP_ADDRESS=$(gcloud compute addresses describe "${PREFIX}-ip" --global --format="value(address)")

    echo ""
    echo "============================================================================="
    echo "  Load Balancer + CDN 設定完了"
    echo "============================================================================="
    echo ""
    echo "  【作成されたリソース】"
    echo "    - 静的IPアドレス:     ${PREFIX}-ip ($IP_ADDRESS)"
    echo "    - SSL証明書:          ${PREFIX}-cert"
    echo "    - バックエンドバケット: ${PREFIX}-backend-bucket"
    echo "    - バックエンドサービス: ${PREFIX}-backend-service"
    echo "    - URLマップ:          ${PREFIX}-url-map"
    echo "    - HTTPSプロキシ:      ${PREFIX}-https-proxy"
    echo "    - フォワーディングルール: ${PREFIX}-https-rule"
    echo ""
    echo "  【URL構成】"
    echo "    https://${DOMAIN}/customer-a/  → 顧客Aのフロントエンド"
    echo "    https://${DOMAIN}/customer-b/  → 顧客Bのフロントエンド"
    echo "    https://${DOMAIN}/api/chat     → AIエージェントAPI"
    echo "    https://${DOMAIN}/api/health   → ヘルスチェック"
    echo ""
    echo "  【重要: DNS設定を確認】"
    echo "    ドメイン: ${DOMAIN}"
    echo "    タイプ:   A"
    echo "    値:       ${IP_ADDRESS}"
    echo ""
    echo "  【SSL証明書のステータス確認】"
    echo "    gcloud compute ssl-certificates describe ${PREFIX}-cert --global"
    echo ""
    echo "    注意: 証明書のプロビジョニングには最大60分かかります。"
    echo "         DNSが正しく設定されていないと証明書は発行されません。"
    echo ""
    echo "============================================================================="
}

# -----------------------------------------------------------------------------
# メイン処理
# -----------------------------------------------------------------------------
main() {
    echo ""
    echo "============================================================================="
    echo "  Cloud Load Balancer + CDN 設定"
    echo "============================================================================="
    echo ""

    check_prerequisites
    reserve_ip_address
    create_ssl_certificate
    create_backend_bucket
    create_serverless_neg
    create_backend_service
    create_url_map
    create_https_proxy
    create_forwarding_rule
    create_http_redirect
    show_result
}

# 実行
main "$@"
