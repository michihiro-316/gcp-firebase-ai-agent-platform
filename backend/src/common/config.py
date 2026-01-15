"""
設定管理モジュール

環境変数から設定を読み込みます。
新しいAIエージェントを追加する際も、このファイルの変更は基本的に不要です。
"""
import os
from dotenv import load_dotenv

# .envファイルを読み込み（ローカル開発用）
load_dotenv()


class Config:
    """アプリケーション設定"""

    # GCPプロジェクト設定
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "asia-northeast1")

    # CORS設定（カンマ区切りで複数指定可能）
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

    # レート制限のデフォルト値（Firestoreの設定で上書き可能）
    DEFAULT_RATE_LIMIT = 10  # 1分あたりの最大リクエスト数


# シングルトンとして利用
config = Config()
