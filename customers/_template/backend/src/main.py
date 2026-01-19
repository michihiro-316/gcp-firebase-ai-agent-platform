"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  main.py - バックエンドのエントリーポイント                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🎯 役割:                                                                    ║
║     フロントエンドからのHTTPリクエストを受け取り、                             ║
║     適切なAIエージェントに処理を振り分ける「司令塔」                           ║
║                                                                              ║
║  📡 エンドポイント:                                                          ║
║     POST /chat      → チャットメッセージを処理（ストリーミング）              ║
║     POST /chat/sync → 同期版チャット（デバッグ用）                           ║
║     GET  /health    → ヘルスチェック（死活監視用）                           ║
║     GET  /agents    → 利用可能なエージェント一覧                             ║
║                                                                              ║
║  🔒 セキュリティ:                                                            ║
║     - Firebase認証トークンの検証                                             ║
║     - Gateway からの内部ヘッダー認証（X-Gateway-Verified + HMAC署名検証）    ║
║     - 顧客IDによるデータ分離（マルチテナント）                                ║
║     - レート制限（DoS対策）                                                  ║
║     - メッセージ長制限（コスト攻撃対策）                                      ║
║                                                                              ║
║  📚 詳細: learning/md/02_バックエンド解説.md                                 ║
║                                                                              ║
║  ⚠️  通常このファイルを編集する必要はありません                               ║
║      AIの動作を変えるには agents/_template/agent.py を編集してください        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

【マルチテナント設計】
顧客ごとにデータを完全分離。customer_idはFirebase Custom Claimsから取得。
Gateway経由の場合は X-Gateway-Verified ヘッダー + HMAC署名で認証済みと判定。

【セキュリティ】
Gateway-Backend 間は共有シークレット（HMAC署名）で保護。
GATEWAY_SECRET 環境変数の設定が必須（Gateway と同じ値を設定）。

【エージェント追加方法】
1. agents/ に新しいディレクトリを作成（_templateをコピー）
2. 下記のAGENTS辞書にクラスを追加
"""
import os
import hmac
import hashlib
import asyncio
import re
import uuid
import logging
from flask import Flask, request, Response
import functions_framework

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== Gateway-Backend 間認証 =====
# Gateway と同じシークレットを設定（必須）
GATEWAY_SECRET = os.environ.get("GATEWAY_SECRET", "")
if not GATEWAY_SECRET:
    logger.warning("GATEWAY_SECRET が未設定です。本番環境では必ず設定してください。")

# 共通モジュール
from common.config import config
from common.cors import setup_cors
from common.auth import authenticate_request
from common.rate_limiter import check_rate_limit
from common.errors import error_response, success_response
from common.firebase_init import db

# エージェント
from agents._base.firestore_checkpointer import FirestoreCheckpointer
from agents._template import TemplateAgent


# ===== 設定 =====

# 利用可能なエージェント一覧
# 顧客別エージェントを追加する場合はここに追記
# 例: from agents.acme_corp.agent import AcmeCorpAgent
AGENTS = {
    "template": TemplateAgent,
    # "acme-corp": AcmeCorpAgent,  # 顧客別エージェントの例
}

# この顧客で使用するエージェント（環境変数 DEFAULT_AGENT で指定）
DEFAULT_AGENT = config.DEFAULT_AGENT or "template"

# 起動時に設定をログ出力
if config.CUSTOMER_ID:
    logger.info(f"顧客別バックエンド起動: customer_id={config.CUSTOMER_ID}, agent={DEFAULT_AGENT}")
else:
    logger.info(f"共通バックエンド起動: agent={DEFAULT_AGENT}")

# セキュリティ設定
MAX_MESSAGE_LENGTH = 10000  # メッセージの最大文字数（DoS/コスト攻撃対策）
THREAD_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')  # thread_idの許可パターン


# ===== アプリケーション初期化 =====

app = Flask(__name__)
setup_cors(app)

# エージェントキャッシュ: {(agent_name, customer_id): agent_instance}
_agent_cache = {}


# ===== ヘルパー関数 =====

def get_agent(agent_name: str, customer_id: str):
    """エージェントを取得（顧客別にキャッシュ）"""
    cache_key = (agent_name, customer_id)
    if cache_key not in _agent_cache:
        checkpointer = FirestoreCheckpointer(db, customer_id)
        agent_class = AGENTS[agent_name]
        _agent_cache[cache_key] = agent_class(
            checkpointer=checkpointer,
            project_id=config.PROJECT_ID,
            location=config.VERTEX_AI_LOCATION
        )
    return _agent_cache[cache_key]


class ChatRequestError(Exception):
    """チャットリクエストのエラー"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def verify_gateway_signature(user_id: str, customer_id: str, signature: str) -> bool:
    """
    Gateway からの署名を検証

    【なぜ必要か】
    X-Gateway-Verified ヘッダーだけでは、攻撃者が直接 Backend にアクセスして
    ヘッダーを偽装できてしまう。この署名検証により、正規の Gateway からの
    リクエストのみを受け付ける。

    Args:
        user_id: ユーザーID
        customer_id: 顧客ID
        signature: Gateway が生成した HMAC-SHA256 署名

    Returns:
        署名が正しければ True、そうでなければ False
    """
    if not GATEWAY_SECRET:
        # シークレットが未設定の場合は警告を出して許可（開発環境用）
        logger.warning("GATEWAY_SECRET が未設定のため、署名検証をスキップします")
        return True

    if not signature:
        return False

    # Gateway と同じ方法で署名を生成
    message = f"{user_id}:{customer_id}".encode()
    expected_signature = hmac.new(
        GATEWAY_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()

    # タイミング攻撃を防ぐため、hmac.compare_digest を使用
    return hmac.compare_digest(signature, expected_signature)


def authenticate_request_with_gateway(request) -> dict:
    """
    Gateway 経由のリクエストを認証

    Gateway が認証済みの場合（X-Gateway-Verified ヘッダーがある場合）、
    HMAC 署名を検証した上で X-User-Id と X-Customer-Id ヘッダーを信頼する。

    Gateway 経由でない場合は、従来の Firebase トークン認証を行う。

    Returns:
        {"uid": "...", "email": "...", "customer_id": "..."}

    Raises:
        ValueError: 認証失敗時
    """
    # Gateway 経由かどうかを確認
    gateway_verified = request.headers.get("X-Gateway-Verified")

    if gateway_verified == "true":
        # Gateway からの内部ヘッダーを取得
        user_id = request.headers.get("X-User-Id")
        customer_id = request.headers.get("X-Customer-Id")
        signature = request.headers.get("X-Gateway-Signature", "")

        if not user_id or not customer_id:
            raise ValueError("Gateway からの内部ヘッダーが不足しています")

        # 署名を検証（偽装防止）
        if not verify_gateway_signature(user_id, customer_id, signature):
            logger.warning(f"Gateway 署名検証失敗: user_id={user_id}, customer_id={customer_id}")
            raise ValueError("Gateway の署名が無効です")

        logger.info(f"Gateway 経由の認証成功: user_id={user_id}, customer_id={customer_id}")
        return {
            "uid": user_id,
            "email": None,  # Gateway 経由の場合は不明
            "customer_id": customer_id,
        }

    # Gateway 経由でない場合は従来の認証
    return authenticate_request(request)


def prepare_chat_request():
    """
    チャットリクエストの共通前処理

    Returns:
        tuple: (agent, message, thread_id, user_id, customer_id)
    """
    # 認証チェック（Gateway 経由の場合は内部ヘッダーを使用）
    try:
        user_info = authenticate_request_with_gateway(request)
    except ValueError as e:
        raise ChatRequestError(str(e), 401)

    user_id = user_info["uid"]
    customer_id = user_info["customer_id"]

    # 顧客ID検証（顧客別デプロイの場合）
    # 環境変数で CUSTOMER_ID が設定されている場合、
    # ユーザーの所属顧客と一致することを確認
    if config.CUSTOMER_ID and config.CUSTOMER_ID != customer_id:
        raise ChatRequestError(
            "このAPIエンドポイントへのアクセス権限がありません",
            403
        )

    # レート制限チェック
    if not check_rate_limit(user_id):
        raise ChatRequestError(
            "リクエスト制限を超えました。1分後に再度お試しください。",
            429
        )

    # リクエストボディを取得
    data = request.get_json()
    if not data:
        raise ChatRequestError("リクエストボディが必要です")

    message = data.get("message", "").strip()
    if not message:
        raise ChatRequestError("メッセージを入力してください")

    # メッセージ長制限（DoS/コスト攻撃対策）
    if len(message) > MAX_MESSAGE_LENGTH:
        raise ChatRequestError(
            f"メッセージが長すぎます。{MAX_MESSAGE_LENGTH}文字以内で入力してください。"
        )

    # スレッドID生成・検証
    thread_id = data.get("thread_id")
    if thread_id:
        # 既存のthread_idはフォーマット検証
        if not THREAD_ID_PATTERN.match(thread_id):
            raise ChatRequestError(
                "thread_idの形式が不正です。英数字、ハイフン、アンダースコアのみ使用可能です。"
            )
    else:
        # 新規生成
        thread_id = f"{user_id}_{uuid.uuid4().hex[:12]}"
    agent_name = data.get("agent", DEFAULT_AGENT)

    if agent_name not in AGENTS:
        raise ChatRequestError(f"エージェント '{agent_name}' は存在しません")

    # 顧客別エージェントを取得
    agent = get_agent(agent_name, customer_id)

    return agent, message, thread_id, user_id, customer_id


# ===== APIエンドポイント =====

@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェック（認証不要）"""
    return success_response({"status": "healthy"})


@app.route("/chat", methods=["POST"])
def chat():
    """チャットAPI（ストリーミング）"""
    try:
        agent, message, thread_id, user_id, customer_id = prepare_chat_request()
    except ChatRequestError as e:
        return error_response(e.message, e.status_code)

    # ストリーミングレスポンス
    # 【なぜこの構造が必要か】
    # Flask は同期フレームワークだが、AI エージェントは非同期（async）で動作する。
    # そのため、同期の generate() の中で非同期の async_generate() を呼び出す
    # 「ブリッジ」パターンを使用している。
    def generate():
        async def async_generate():
            """非同期ジェネレータ：AI からの応答を少しずつ yield"""
            try:
                async for chunk in agent.run(message, thread_id):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                # エラー詳細はログに記録し、クライアントには汎用メッセージを返す
                logger.exception(f"ストリーミング中にエラーが発生: user_id={user_id}, thread_id={thread_id}")
                yield "data: [ERROR] エラーが発生しました。しばらく待ってから再度お試しください。\n\n"

        # 【asyncio イベントループの仕組み】
        # Cloud Functions は各リクエストで独立したスレッドで実行されるため、
        # リクエストごとに新しいイベントループを作成する必要がある。
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = async_generate()
            # 【__anext__() について】
            # async for を使えないため（同期ジェネレータ内のため）、
            # 手動で次の値を取得。StopAsyncIteration で終了を検知。
            while True:
                try:
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Thread-Id": thread_id,
        }
    )


@app.route("/chat/sync", methods=["POST"])
def chat_sync():
    """同期チャットAPI（デバッグ用）"""
    try:
        agent, message, thread_id, user_id, customer_id = prepare_chat_request()
    except ChatRequestError as e:
        return error_response(e.message, e.status_code)

    # 同期実行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        response_text = loop.run_until_complete(agent.run_sync(message, thread_id))
    finally:
        loop.close()

    return success_response({
        "response": response_text,
        "thread_id": thread_id
    })


@app.route("/agents", methods=["GET"])
def list_agents():
    """利用可能なエージェント一覧"""
    # 認証チェック（Gateway 経由の場合は内部ヘッダーを使用）
    try:
        authenticate_request_with_gateway(request)
    except ValueError as e:
        return error_response(str(e), 401)

    return success_response({
        "agents": list(AGENTS.keys()),
        "default": DEFAULT_AGENT
    })


# Cloud Functions エントリーポイント
@functions_framework.http
def main(req):
    """Cloud Functions のエントリーポイント"""
    with app.request_context(req.environ):
        return app.full_dispatch_request()
