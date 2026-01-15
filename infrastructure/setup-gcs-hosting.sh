#!/bin/bash
# =============================================================================
# GCS 静的サイトホスティング 初期設定スクリプト
# =============================================================================
#
# 【このスクリプトでやること】
#   1. フロントエンド用GCSバケットの作成
#   2. 公開アクセス設定
#   3. 静的サイトホスティング設定
#
# 【実行方法】
#   chmod +x setup-gcs-hosting.sh
#   ./setup-gcs-hosting.sh
#
# =============================================================================

set -e  # エラー時に停止

# -----------------------------------------------------------------------------
# 設定値（ここを環境に合わせて変更）
# -----------------------------------------------------------------------------

# プロジェクトID（必須: あなたのGCPプロジェクトIDに変更）
PROJECT_ID="${PROJECT_ID:-your-project-id}"

# バケット名（プロジェクトID + サフィックス）
BUCKET_NAME="${PROJECT_ID}-frontend"

# リージョン（東京固定）
LOCATION="asia-northeast1"

# -----------------------------------------------------------------------------
# 色付きログ出力
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# -----------------------------------------------------------------------------
# 前提条件チェック
# -----------------------------------------------------------------------------
check_prerequisites() {
    log_info "前提条件をチェック中..."

    # gcloud CLIが使えるか
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI がインストールされていません"
        echo "インストール方法: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    # プロジェクトが設定されているか
    if [ "$PROJECT_ID" = "your-project-id" ]; then
        log_error "PROJECT_ID を設定してください"
        echo "例: export PROJECT_ID=my-actual-project-id"
        exit 1
    fi

    # 認証されているか
    if ! gcloud auth print-identity-token &> /dev/null; then
        log_warn "gcloud にログインしていません。ログインを開始します..."
        gcloud auth login
    fi

    # プロジェクトを設定
    gcloud config set project "$PROJECT_ID"
    log_info "プロジェクト: $PROJECT_ID"
}

# -----------------------------------------------------------------------------
# GCSバケット作成
# -----------------------------------------------------------------------------
create_bucket() {
    log_info "GCSバケットを作成中: gs://${BUCKET_NAME}/"

    # バケットが既に存在するかチェック
    if gsutil ls -b "gs://${BUCKET_NAME}" &> /dev/null; then
        log_warn "バケットは既に存在します: gs://${BUCKET_NAME}/"
        return 0
    fi

    # バケット作成
    gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$LOCATION" "gs://${BUCKET_NAME}/"

    log_info "バケット作成完了"
}

# -----------------------------------------------------------------------------
# 公開アクセス設定
# -----------------------------------------------------------------------------
configure_public_access() {
    log_info "公開アクセスを設定中..."

    # 均一なバケットレベルアクセスを有効化
    gsutil uniformbucketlevelaccess set on "gs://${BUCKET_NAME}/"

    # allUsersに読み取り権限を付与
    gsutil iam ch allUsers:objectViewer "gs://${BUCKET_NAME}"

    log_info "公開アクセス設定完了"
}

# -----------------------------------------------------------------------------
# 静的サイト設定
# -----------------------------------------------------------------------------
configure_static_hosting() {
    log_info "静的サイトホスティングを設定中..."

    # メインページとエラーページの設定
    # 注意: 顧客ごとにindex.htmlがあるため、ここでは設定しない
    # Load Balancerのルーティングで制御する

    # CORS設定（APIと連携するため必要）
    cat > /tmp/cors-config.json << 'EOF'
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type", "Cache-Control"],
    "maxAgeSeconds": 3600
  }
]
EOF

    gsutil cors set /tmp/cors-config.json "gs://${BUCKET_NAME}"
    rm /tmp/cors-config.json

    # キャッシュ制御のデフォルト設定
    # HTMLは短めのキャッシュ、アセットは長めのキャッシュ
    log_info "キャッシュ設定は各ファイルアップロード時に設定します"

    log_info "静的サイトホスティング設定完了"
}

# -----------------------------------------------------------------------------
# サンプル顧客ディレクトリ作成
# -----------------------------------------------------------------------------
create_sample_directories() {
    log_info "サンプル顧客ディレクトリを作成中..."

    # customer-a のサンプル
    mkdir -p /tmp/sample-frontend/customer-a
    cat > /tmp/sample-frontend/customer-a/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Customer A - AI Agent</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; }
        h1 { color: #1976d2; }
    </style>
</head>
<body>
    <h1>Customer A</h1>
    <p>このページは customer-a 用のフロントエンドです。</p>
    <p>実際の運用時は、ビルドしたReact/Vueアプリをここに配置します。</p>
</body>
</html>
EOF

    cat > /tmp/sample-frontend/customer-a/config.json << EOF
{
  "customer_id": "customer-a",
  "customer_name": "株式会社A",
  "theme": {
    "primary_color": "#1976d2"
  },
  "api": {
    "base_url": "https://${LOCATION}-${PROJECT_ID}.cloudfunctions.net/ai-agent-api"
  }
}
EOF

    # customer-b のサンプル
    mkdir -p /tmp/sample-frontend/customer-b
    cat > /tmp/sample-frontend/customer-b/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Customer B - AI Agent</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; }
        h1 { color: #4caf50; }
    </style>
</head>
<body>
    <h1>Customer B</h1>
    <p>このページは customer-b 用のフロントエンドです。</p>
    <p>実際の運用時は、ビルドしたReact/Vueアプリをここに配置します。</p>
</body>
</html>
EOF

    cat > /tmp/sample-frontend/customer-b/config.json << EOF
{
  "customer_id": "customer-b",
  "customer_name": "株式会社B",
  "theme": {
    "primary_color": "#4caf50"
  },
  "api": {
    "base_url": "https://${LOCATION}-${PROJECT_ID}.cloudfunctions.net/ai-agent-api"
  }
}
EOF

    # GCSにアップロード
    gsutil -m cp -r /tmp/sample-frontend/* "gs://${BUCKET_NAME}/"

    # HTMLファイルのキャッシュ制御（短め: 5分）
    gsutil -m setmeta -h "Cache-Control:public, max-age=300" "gs://${BUCKET_NAME}/**/index.html"

    # 設定ファイルのキャッシュ制御（短め: 1分）
    gsutil -m setmeta -h "Cache-Control:public, max-age=60" "gs://${BUCKET_NAME}/**/config.json"

    rm -rf /tmp/sample-frontend

    log_info "サンプル顧客ディレクトリ作成完了"
}

# -----------------------------------------------------------------------------
# 結果表示
# -----------------------------------------------------------------------------
show_result() {
    echo ""
    echo "============================================================================="
    echo "  GCS 静的サイトホスティング 設定完了"
    echo "============================================================================="
    echo ""
    echo "  バケット名: gs://${BUCKET_NAME}/"
    echo "  リージョン: ${LOCATION}"
    echo ""
    echo "  サンプル顧客:"
    echo "    - customer-a/"
    echo "    - customer-b/"
    echo ""
    echo "  【次のステップ】"
    echo "  1. Load Balancer を設定: ./setup-load-balancer.sh"
    echo "  2. フロントエンドをビルド・アップロード"
    echo ""
    echo "  【直接アクセス確認（LB設定前）】"
    echo "    https://storage.googleapis.com/${BUCKET_NAME}/customer-a/index.html"
    echo "    https://storage.googleapis.com/${BUCKET_NAME}/customer-b/index.html"
    echo ""
    echo "============================================================================="
}

# -----------------------------------------------------------------------------
# メイン処理
# -----------------------------------------------------------------------------
main() {
    echo ""
    echo "============================================================================="
    echo "  GCS 静的サイトホスティング 初期設定"
    echo "============================================================================="
    echo ""

    check_prerequisites
    create_bucket
    configure_public_access
    configure_static_hosting
    create_sample_directories
    show_result
}

# 実行
main "$@"
