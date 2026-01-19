"""
CORS（Cross-Origin Resource Sharing）設定モジュール

フロントエンドからのリクエストを許可するための設定を行います。
許可するオリジンは環境変数 ALLOWED_ORIGINS で設定します。
"""
from flask import Flask
from flask_cors import CORS
from .config import config


def setup_cors(app: Flask) -> None:
    """
    FlaskアプリにCORS設定を適用

    Args:
        app: Flaskアプリケーションインスタンス
    """
    CORS(
        app,
        origins=config.ALLOWED_ORIGINS,
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "OPTIONS"]
    )
