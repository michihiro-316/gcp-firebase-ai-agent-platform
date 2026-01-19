"""
モックAPIサーバー（ローカル開発・検証用）

【用途】
- フロントエンドの動作確認
- AIエージェントのレスポンス形式の確認
- 認証なしでの動作テスト
- GCP/Firebase接続なしでの開発

【起動方法】
cd backend/dev
python mock_server.py

【本番との違い】
- 認証: スキップ（誰でもアクセス可能）
- AI: 固定レスポンス or エコー（Vertex AI不要）
- DB: なし（会話履歴は保存されない）
- 課金: なし

【注意】
このサーバーは開発専用です。本番環境では使用しないでください。
"""
import time
import uuid
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ===== 設定 =====

# モックユーザー情報
MOCK_USER = {
    "uid": "mock-user-001",
    "email": "dev@example.com",
    "customer_id": "dev-customer"
}

# モックエージェント一覧
MOCK_AGENTS = ["sample", "echo", "slow"]

# エコーモード: Trueならユーザーの入力をそのまま返す
ECHO_MODE = False

# 固定レスポンス（ECHO_MODE=Falseの場合）
MOCK_RESPONSES = [
    "こんにちは！モックサーバーからの返答です。",
    "これはテスト用のレスポンスです。本番ではAIが応答します。",
    "フロントエンドの動作確認ができましたか？",
]


# ===== ヘルパー =====

def get_mock_response(message: str, agent: str) -> str:
    """モックレスポンスを生成"""
    if ECHO_MODE or agent == "echo":
        return f"[エコー] あなたのメッセージ: {message}"

    # 固定レスポンスをローテーション
    idx = hash(message) % len(MOCK_RESPONSES)
    return MOCK_RESPONSES[idx]


def stream_response(text: str, delay: float = 0.05):
    """ストリーミング形式でレスポンスを返す"""
    for char in text:
        yield f"data: {char}\n\n"
        time.sleep(delay)
    yield "data: [DONE]\n\n"


# ===== APIエンドポイント =====

@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        "success": True,
        "data": {
            "status": "healthy",
            "mode": "mock",
            "message": "これはモックサーバーです"
        }
    })


@app.route("/chat", methods=["POST"])
def chat():
    """チャットAPI（ストリーミング）"""
    data = request.get_json() or {}
    message = data.get("message", "")
    agent = data.get("agent", "sample")
    thread_id = data.get("thread_id") or f"{MOCK_USER['uid']}_{uuid.uuid4().hex[:12]}"

    if not message:
        return jsonify({"success": False, "error": "メッセージを入力してください"}), 400

    # slowエージェントは遅延を大きく
    delay = 0.1 if agent == "slow" else 0.03

    response_text = get_mock_response(message, agent)

    return Response(
        stream_response(response_text, delay),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Thread-Id": thread_id,
        }
    )


@app.route("/chat/sync", methods=["POST"])
def chat_sync():
    """同期チャットAPI"""
    data = request.get_json() or {}
    message = data.get("message", "")
    agent = data.get("agent", "sample")
    thread_id = data.get("thread_id") or f"{MOCK_USER['uid']}_{uuid.uuid4().hex[:12]}"

    if not message:
        return jsonify({"success": False, "error": "メッセージを入力してください"}), 400

    response_text = get_mock_response(message, agent)

    return jsonify({
        "success": True,
        "data": {
            "response": response_text,
            "thread_id": thread_id
        }
    })


@app.route("/agents", methods=["GET"])
def list_agents():
    """利用可能なエージェント一覧"""
    return jsonify({
        "success": True,
        "data": {
            "agents": MOCK_AGENTS,
            "default": "sample"
        }
    })


# ===== メイン =====

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  モックAPIサーバー起動中（開発専用）")
    print("=" * 60)
    print()
    print("  URL: http://localhost:8080")
    print()
    print("  エンドポイント:")
    print("    GET  /health     - ヘルスチェック")
    print("    POST /chat       - チャット（ストリーミング）")
    print("    POST /chat/sync  - チャット（同期）")
    print("    GET  /agents     - エージェント一覧")
    print()
    print("  エージェント:")
    print("    sample - 固定レスポンスを返す")
    print("    echo   - 入力をそのまま返す")
    print("    slow   - 遅延付きで返す（ストリーミング確認用）")
    print()
    print("  フロントエンドの設定:")
    print("    frontend/.env で VITE_API_URL=http://localhost:8080")
    print()
    print("  Ctrl+C で終了")
    print("=" * 60)
    print()

    app.run(host="0.0.0.0", port=8080, debug=True)
