"""
エラーハンドリングモジュール

APIで使用するエラーレスポンスを定義します。
"""
from flask import jsonify


def error_response(message: str, status_code: int = 400):
    """
    エラーレスポンスを生成

    Args:
        message: エラーメッセージ
        status_code: HTTPステータスコード

    Returns:
        (レスポンス, ステータスコード) のタプル
    """
    return jsonify({
        "success": False,
        "error": message
    }), status_code


def success_response(data: dict):
    """
    成功レスポンスを生成

    Args:
        data: レスポンスデータ

    Returns:
        JSONレスポンス
    """
    return jsonify({
        "success": True,
        **data
    })
