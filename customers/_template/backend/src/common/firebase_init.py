"""
Firebase初期化モジュール

アプリケーション起動時に一度だけ初期化されます。
"""
import firebase_admin
from firebase_admin import firestore

# Firebase初期化（一度だけ実行）
# 公式APIを使用して初期化済みかどうかをチェック
# （firebase_admin._appsはプライベートAPIのため使用を避ける）
try:
    firebase_admin.get_app()
except ValueError:
    # アプリが初期化されていない場合のみ初期化
    # GCP環境ではデフォルトの認証情報を使用
    # ローカルではGOOGLE_APPLICATION_CREDENTIALS環境変数を使用
    firebase_admin.initialize_app()

# Firestoreクライアント（アプリ全体で共有）
db = firestore.client()
