"""
メインエントリーポイント（Cloud Run Functions）

【マルチテナント】
顧客ごとにデータを分離。customer_idはCustom Claimsから取得。

【新しいエージェントを追加する場合】
AGENTS辞書にクラスを追加するだけでOK。
"""
import asyncio
import re
import uuid
import logging
from flask import Flask, request, Response
import functions_framework

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 共通モジュール
from common.config import config
from common.cors import setup_cors
from common.auth import authenticate_request
from common.rate_limiter import check_rate_limit, get_remaining_requests
from common.errors import error_response, success_response
from common.firebase_init import db

# エージェント
from agents.sample_agent import SampleAgent
from agents.firestore_checkpointer import FirestoreCheckpointer


# ===== 設定 =====

# 利用可能なエージェント一覧
# 新しいエージェントを追加する場合はここに追記
AGENTS = {
    "sample": SampleAgent,
    # "rag_agent": RagAgent,  # 例: RAGエージェントを追加
}

# デフォルトで使用するエージェント
DEFAULT_AGENT = "sample"

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
        AgentClass = AGENTS[agent_name]
        _agent_cache[cache_key] = AgentClass(
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


def prepare_chat_request():
    """
    チャットリクエストの共通前処理

    Returns:
        tuple: (agent, message, thread_id, user_id, customer_id)
    """
    # 認証チェック
    try:
        user_info = authenticate_request(request)
    except ValueError as e:
        raise ChatRequestError(str(e), 401)

    user_id = user_info["uid"]
    customer_id = user_info["customer_id"]

    # レート制限チェック
    if not check_rate_limit(user_id):
        remaining = get_remaining_requests(user_id)
        raise ChatRequestError(
            f"リクエスト制限を超えました。(残り: {remaining}回/分)",
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
    def generate():
        async def async_generate():
            try:
                async for chunk in agent.run(message, thread_id):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                # エラー詳細はログに記録し、クライアントには汎用メッセージを返す
                logger.exception(f"ストリーミング中にエラーが発生: user_id={user_id}, thread_id={thread_id}")
                yield "data: [ERROR] エラーが発生しました。しばらく待ってから再度お試しください。\n\n"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = async_generate()
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
    # 認証チェック
    try:
        authenticate_request(request)
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
