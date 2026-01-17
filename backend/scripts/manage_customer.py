"""
顧客管理スクリプト

【使い方】
1. 顧客一覧を見る
   python manage_customer.py list

2. 新しい顧客を追加する
   python manage_customer.py add test-corp "株式会社テスト"

3. ユーザーを顧客に紐付ける
   python manage_customer.py add-user test-corp user@example.com

4. 顧客の情報を確認する
   python manage_customer.py show test-corp

5. ユーザーの情報を確認する
   python manage_customer.py show-user user@example.com

【準備】
このスクリプトを実行する前に、以下を確認してください：
- backend/.env に GOOGLE_APPLICATION_CREDENTIALS が設定されている
- service-account.json が存在する
"""
import sys
import os

# 親ディレクトリをパスに追加（srcのモジュールを使うため）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 環境変数を読み込む
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import firebase_admin
from firebase_admin import credentials, firestore, auth


# Firebase初期化
def init_firebase():
    """Firebaseを初期化"""
    try:
        firebase_admin.get_app()
    except ValueError:
        # 認証情報のパスを取得
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # デフォルト認証を使用
            firebase_admin.initialize_app()
    return firestore.client()


# ========== コマンド ==========

def cmd_list(db):
    """顧客一覧を表示"""
    print("\n=== 顧客一覧 ===\n")

    customers = db.collection('customers').stream()
    count = 0

    for doc in customers:
        data = doc.to_dict()
        name = data.get('name', '名前なし')
        print(f"  {doc.id}: {name}")
        count += 1

    if count == 0:
        print("  （顧客がまだ登録されていません）")

    print(f"\n合計: {count}社\n")


def cmd_add(db, customer_id, customer_name):
    """新しい顧客を追加"""
    print(f"\n=== 顧客を追加 ===\n")
    print(f"  顧客ID: {customer_id}")
    print(f"  顧客名: {customer_name}")

    # 既に存在するか確認
    doc_ref = db.collection('customers').document(customer_id)
    if doc_ref.get().exists:
        print(f"\n❌ エラー: 顧客ID '{customer_id}' は既に存在します")
        return

    # 顧客を作成
    doc_ref.set({
        'name': customer_name,
        'created_at': firestore.SERVER_TIMESTAMP,
    })

    print(f"\n✅ 顧客 '{customer_name}' を追加しました！")
    print(f"\n次のステップ:")
    print(f"  ユーザーを追加するには:")
    print(f"  python manage_customer.py add-user {customer_id} user@example.com")


def cmd_add_user(db, customer_id, email):
    """ユーザーを顧客に紐付ける"""
    print(f"\n=== ユーザーを顧客に紐付け ===\n")
    print(f"  顧客ID: {customer_id}")
    print(f"  メール: {email}")

    # 顧客が存在するか確認
    customer_doc = db.collection('customers').document(customer_id).get()
    if not customer_doc.exists:
        print(f"\n❌ エラー: 顧客ID '{customer_id}' が見つかりません")
        print(f"   先に顧客を追加してください:")
        print(f"   python manage_customer.py add {customer_id} \"顧客名\"")
        return

    # Firebase Authでユーザーを検索
    try:
        user = auth.get_user_by_email(email)
        uid = user.uid
        print(f"  ユーザーUID: {uid}")
    except auth.UserNotFoundError:
        print(f"\n❌ エラー: メール '{email}' のユーザーが見つかりません")
        print(f"   ユーザーは先にログインしている必要があります")
        return

    # Custom Claimsを設定
    auth.set_custom_user_claims(uid, {'customer_id': customer_id})

    # Firestoreにも記録（バックアップ用）
    db.collection('users').document(uid).set({
        'email': email,
        'customer_id': customer_id,
        'updated_at': firestore.SERVER_TIMESTAMP,
    }, merge=True)

    customer_name = customer_doc.to_dict().get('name', customer_id)
    print(f"\n✅ ユーザー '{email}' を '{customer_name}' に紐付けました！")
    print()
    print("=" * 50)
    print("⚠️  重要: ユーザーに再ログインをお願いしてください")
    print("=" * 50)
    print()
    print("  Custom Claims（顧客情報）はIDトークンに含まれます。")
    print("  現在のセッションでは古いトークンが使われるため、")
    print("  紐付け完了後は必ず再ログインが必要です。")
    print()
    print("  再ログインしないと「顧客に紐付けされていません」")
    print("  エラーが発生します。")
    print()


def cmd_show(db, customer_id):
    """顧客の詳細を表示"""
    print(f"\n=== 顧客詳細: {customer_id} ===\n")

    # 顧客情報
    doc = db.collection('customers').document(customer_id).get()
    if not doc.exists:
        print(f"❌ 顧客ID '{customer_id}' が見つかりません")
        return

    data = doc.to_dict()
    print(f"  顧客名: {data.get('name', '名前なし')}")
    print(f"  作成日: {data.get('created_at', '不明')}")

    # この顧客のユーザー一覧
    print(f"\n  --- 所属ユーザー ---")
    users = db.collection('users').where('customer_id', '==', customer_id).stream()
    user_count = 0
    for user_doc in users:
        user_data = user_doc.to_dict()
        print(f"    {user_data.get('email', user_doc.id)}")
        user_count += 1

    if user_count == 0:
        print("    （ユーザーなし）")
    print(f"\n  ユーザー数: {user_count}人\n")


def cmd_show_user(db, email):
    """ユーザーの詳細を表示"""
    print(f"\n=== ユーザー詳細: {email} ===\n")

    try:
        user = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        print(f"❌ メール '{email}' のユーザーが見つかりません")
        return

    print(f"  UID: {user.uid}")
    print(f"  メール: {user.email}")
    print(f"  表示名: {user.display_name or '未設定'}")

    # Custom Claims
    claims = user.custom_claims or {}
    customer_id = claims.get('customer_id', '未設定')
    print(f"  顧客ID: {customer_id}")

    # Firestoreの情報
    user_doc = db.collection('users').document(user.uid).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        print(f"  Firestore顧客ID: {user_data.get('customer_id', '未設定')}")
    print()


def print_help():
    """ヘルプを表示"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                    顧客管理スクリプト                        ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  【顧客の操作】                                             ║
║                                                            ║
║    一覧表示:                                                ║
║      python manage_customer.py list                        ║
║                                                            ║
║    追加:                                                    ║
║      python manage_customer.py add 顧客ID "顧客名"          ║
║      例: python manage_customer.py add test-corp "テスト社" ║
║                                                            ║
║    詳細表示:                                                ║
║      python manage_customer.py show 顧客ID                  ║
║                                                            ║
║  【ユーザーの操作】                                          ║
║                                                            ║
║    顧客に紐付け:                                            ║
║      python manage_customer.py add-user 顧客ID メール       ║
║      例: python manage_customer.py add-user test-corp \\    ║
║          yamada@example.com                                ║
║                                                            ║
║    詳細表示:                                                ║
║      python manage_customer.py show-user メール             ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")


# ========== メイン ==========

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    # ヘルプ
    if command in ['help', '-h', '--help']:
        print_help()
        return

    # Firebase初期化
    db = init_firebase()

    # コマンド実行
    if command == 'list':
        cmd_list(db)

    elif command == 'add':
        if len(sys.argv) < 4:
            print("❌ 使い方: python manage_customer.py add 顧客ID \"顧客名\"")
            return
        cmd_add(db, sys.argv[2], sys.argv[3])

    elif command == 'add-user':
        if len(sys.argv) < 4:
            print("❌ 使い方: python manage_customer.py add-user 顧客ID メール")
            return
        cmd_add_user(db, sys.argv[2], sys.argv[3])

    elif command == 'show':
        if len(sys.argv) < 3:
            print("❌ 使い方: python manage_customer.py show 顧客ID")
            return
        cmd_show(db, sys.argv[2])

    elif command == 'show-user':
        if len(sys.argv) < 3:
            print("❌ 使い方: python manage_customer.py show-user メール")
            return
        cmd_show_user(db, sys.argv[2])

    else:
        print(f"❌ 不明なコマンド: {command}")
        print_help()


if __name__ == '__main__':
    main()
