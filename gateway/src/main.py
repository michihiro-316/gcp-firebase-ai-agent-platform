"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  Gateway Cloud Functions                                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  役割:                                                                       ║
║     すべてのリクエストの入口として、認証と振り分けを行う                        ║
║                                                                              ║
║  やること（3つだけ）:                                                         ║
║     1. Firebase トークンを検証                                               ║
║     2. customer_id から転送先 URL を取得                                     ║
║     3. リクエストをそのまま転送（プロキシ）                                    ║
║                                                                              ║
║  やらないこと（重要）:                                                        ║
║     - AI 処理                                                                ║
║     - ビジネスロジック                                                       ║
║     - UI ロジック                                                            ║
║                                                                              ║
║  詳細: learning/md/10_Gatewayアーキテクチャ.md                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

【設計思想】
- Gateway は「認証して転送するだけ」のシンプルな存在
- 複雑なロジックは入れない
- Company Cloud Functions に処理を委譲する

【セキュリティ】
- Gateway-Backend 間は共有シークレット（HMAC署名）で保護
- GATEWAY_SECRET 環境変数の設定が必須
"""
import os
import time
import hmac
import hashlib
import logging
from flask import Flask, request, Response
import requests
import functions_framework
import firebase_admin
from firebase_admin import auth, firestore

# ===== ロギング設定 =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== 設定 =====
# Gateway-Backend 間の認証用シークレット（必須）
GATEWAY_SECRET = os.environ.get("GATEWAY_SECRET", "")
if not GATEWAY_SECRET:
    logger.warning("GATEWAY_SECRET が未設定です。本番環境では必ず設定してください。")

# キャッシュ TTL（秒）: 顧客設定の変更を反映するまでの時間
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))  # デフォルト5分

# ===== Firebase 初期化 =====
firebase_admin.initialize_app()
db = firestore.client()

# ===== Flask アプリケーション =====
app = Flask(__name__)


# ===== ヘルパー関数 =====

def create_gateway_signature(user_id: str, customer_id: str) -> str:
    """
    Gateway-Backend 間の認証用署名を生成

    Args:
        user_id: ユーザーID
        customer_id: 顧客ID

    Returns:
        HMAC-SHA256 署名（16進数文字列）

    【なぜ必要か】
    Backend が直接インターネットからアクセス可能な場合、
    攻撃者が X-Gateway-Verified ヘッダーを偽装できてしまう。
    この署名により、正規の Gateway からのリクエストのみを受け付ける。
    """
    if not GATEWAY_SECRET:
        return ""

    message = f"{user_id}:{customer_id}".encode()
    return hmac.new(
        GATEWAY_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()


def error_response(message: str, status_code: int, detail: str = None):
    """
    統一されたエラーレスポンス

    Args:
        message: エラーメッセージ
        status_code: HTTPステータスコード
        detail: 詳細メッセージ（オプション）
    """
    body = {"error": message}
    if detail:
        body["message"] = detail
    return body, status_code, {"Access-Control-Allow-Origin": "*"}


# ===== 認証 =====

def verify_request():
    """
    Firebase トークンを検証して uid, customer_id を返す

    Returns:
        tuple: (uid, customer_id) または (None, None)

    処理の流れ:
    1. Authorization ヘッダーからトークンを取得
       例: "Bearer abc123xyz..." → "abc123xyz..."
    2. Firebase Admin SDK でトークンを検証
    3. Custom Claims から customer_id を取得
    """
    # Authorization ヘッダーからトークンを取得
    auth_header = request.headers.get("Authorization", "")
    # "Bearer " で始まるかチェック（OAuth 2.0 の形式）
    if not auth_header.startswith("Bearer "):
        return None, None

    # "Bearer " (7文字) を除去してトークン本体を取得
    # 例: "Bearer abc123" → "abc123"
    token = auth_header[7:]
    if not token:
        return None, None

    try:
        # トークン検証（失効チェック付き）
        decoded = auth.verify_id_token(token, check_revoked=True)
        uid = decoded["uid"]

        # Custom Claims から customer_id を取得
        user = auth.get_user(uid)
        customer_id = (user.custom_claims or {}).get("customer_id")

        if not customer_id:
            logger.warning(f"customer_id が未設定: uid={uid}")
            return uid, None

        return uid, customer_id

    except auth.RevokedIdTokenError:
        logger.warning("トークンが失効しています")
        return None, None
    except auth.ExpiredIdTokenError:
        logger.warning("トークンの有効期限が切れています")
        return None, None
    except auth.InvalidIdTokenError:
        logger.warning("無効なトークンです")
        return None, None
    except Exception as e:
        # スタックトレースも記録（デバッグ用）
        logger.exception(f"認証エラー: {e}")
        return None, None


# ===== 転送先 URL の取得 =====

# TTL付きキャッシュ: {customer_id: (url, timestamp)}
_url_cache: dict[str, tuple[str, float]] = {}


def get_company_url(customer_id: str) -> str | None:
    """
    Firestore から顧客の Cloud Functions URL を取得（TTL付きキャッシュ）

    Args:
        customer_id: 顧客ID

    Returns:
        Cloud Functions の URL または None

    Firestore 構造:
        customers/{customer_id}
        ├── cloud_functions_url: "https://xxx.cloudfunctions.net/..."
        └── enabled: true

    【キャッシュについて】
    - 毎回 Firestore を読むと遅いのでキャッシュを使用
    - ただし顧客設定の変更を反映するため、TTL（有効期限）を設定
    - デフォルト5分でキャッシュが切れて再取得される
    """
    now = time.time()

    # キャッシュを確認（TTL内なら使用）
    if customer_id in _url_cache:
        cached_url, cached_time = _url_cache[customer_id]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_url
        # TTL切れ: キャッシュを削除して再取得
        del _url_cache[customer_id]

    try:
        doc = db.collection("customers").document(customer_id).get()
        if not doc.exists:
            logger.warning(f"顧客が見つかりません: {customer_id}")
            return None

        data = doc.to_dict()

        # 有効かどうか確認
        if not data.get("enabled", True):
            logger.warning(f"顧客が無効化されています: {customer_id}")
            return None

        url = data.get("cloud_functions_url")
        if url:
            # キャッシュに保存（タイムスタンプ付き）
            _url_cache[customer_id] = (url, now)
            return url

        logger.warning(f"cloud_functions_url が未設定: {customer_id}")
        return None

    except Exception as e:
        logger.exception(f"Firestore エラー: {e}")
        return None


# ===== エンドポイント =====

@app.route("/health", methods=["GET"])
def health():
    """
    ヘルスチェック（認証不要）

    Load Balancer や監視ツールからの死活監視用
    """
    return {"status": "healthy", "service": "gateway"}


# ルートパス「/」と、それ以下の全てのパス「/xxx/yyy」の両方をこの関数で処理
# defaults={"path": ""} により、「/」にアクセスした場合は path="" となる
@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def proxy(path):
    """
    リクエストを顧客の Cloud Functions に転送

    処理の流れ:
    1. CORS プリフライトを処理
    2. Firebase トークンを検証
    3. customer_id から転送先 URL を取得
    4. リクエストをそのまま転送（ストリーミング対応）
    """
    # ----- CORS プリフライト -----
    # ブラウザが実際のリクエスト前に送る「確認リクエスト」
    if request.method == "OPTIONS":
        return "", 204, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Max-Age": "3600",
        }

    # ----- 1. 認証 -----
    uid, customer_id = verify_request()
    if not uid:
        return error_response(
            "認証が必要です",
            401,
            "有効な Firebase トークンを Authorization ヘッダーに設定してください"
        )

    if not customer_id:
        return error_response(
            "顧客に紐付けされていません",
            403,
            "管理者に連絡してください"
        )

    # ----- 2. 転送先 URL を取得 -----
    company_url = get_company_url(customer_id)
    if not company_url:
        return error_response(
            "顧客の設定が見つかりません",
            404,
            "管理者に連絡してください"
        )

    # ----- 3. リクエストを転送 -----
    target_url = f"{company_url}/{path}" if path else company_url

    logger.info(f"転送: {request.method} /{path} -> {target_url} (customer={customer_id})")

    # Gateway-Backend 間の認証用署名を生成
    signature = create_gateway_signature(uid, customer_id)

    try:
        # リクエストを転送
        # stream=True: レスポンスを一度に全部メモリに読み込まず、少しずつ受信
        # 大きなレスポンスや、AI のストリーミング応答に対応するため必須
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={
                # Gateway が検証済みであることを示すヘッダー
                "X-Gateway-Verified": "true",
                "X-User-Id": uid,
                "X-Customer-Id": customer_id,
                # 署名（Backend 側で検証）
                "X-Gateway-Signature": signature,
                # 元のリクエストのヘッダー
                "Content-Type": request.content_type or "application/json",
            },
            data=request.get_data(),
            stream=True,
            timeout=300,  # 5分（AI 応答に時間がかかる場合がある）
        )

        # レスポンスをそのまま返す（ストリーミング）
        def generate():
            """
            ジェネレータ関数: return の代わりに yield を使うことで、
            データを少しずつ返すことができる。
            これにより、大きなデータも少ないメモリで処理できる。
            """
            try:
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk  # 1024バイトずつクライアントに送信
            except GeneratorExit:
                # クライアントが途中で切断した場合
                pass
            finally:
                resp.close()  # 接続を確実にクローズ

        # レスポンスヘッダーを透過
        response_headers = {
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
        }

        # X-Thread-Id などの重要なヘッダーを透過
        for header in ["X-Thread-Id"]:
            if header in resp.headers:
                response_headers[header] = resp.headers[header]

        return Response(
            generate(),
            status=resp.status_code,
            content_type=resp.headers.get("Content-Type", "application/json"),
            headers=response_headers,
        )

    except requests.Timeout:
        logger.error(f"タイムアウト: {target_url}")
        return error_response(
            "リクエストがタイムアウトしました",
            504,
            "しばらく待ってから再度お試しください"
        )

    except requests.RequestException as e:
        logger.exception(f"転送エラー: {e}")
        return error_response(
            "サーバーへの接続に失敗しました",
            502,
            "しばらく待ってから再度お試しください"
        )


# ===== Cloud Functions エントリーポイント =====

@functions_framework.http
def main(req):
    """
    Cloud Functions のエントリーポイント

    gcloud functions deploy で指定する --entry-point はこの関数
    """
    with app.request_context(req.environ):
        return app.full_dispatch_request()
