"""
顧客管理スクリプト

このスクリプトは、顧客（会社）とユーザーの管理を行います。
詳しい説明は learning/md/05_顧客管理の仕組み.md を参照してください。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【クイックスタート】新しい顧客を追加する場合

  ステップ1: 顧客を作成
    python manage_customer.py add acme-corp "株式会社ACME"

  ステップ2: メールドメイン（@以降）を登録（社員全員が自動振り分け）
    python manage_customer.py add-domain acme-corp acme.co.jp

  ステップ3: 確認
    python manage_customer.py show acme-corp

  → これで @acme.co.jp のユーザーは全員自動で振り分けられます！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【全コマンド一覧】

  基本操作:
    list                              顧客一覧を表示
    add <顧客ID> <顧客名>             顧客を作成
    show <顧客ID>                     顧客の詳細を表示
    show-user <メール>                ユーザーの詳細を表示

  自動振り分け設定（推奨）:
    add-domain <顧客ID> <メールドメイン>    メールドメイン（@以降）を追加（社員全員自動振り分け）
    add-email <顧客ID> <メール>             メールを追加（業務委託者など個別）
    remove-domain <顧客ID> <メールドメイン> メールドメインを削除
    remove-email <顧客ID> <メール>          メールを削除

  手動紐付け（自動振り分けを使わない場合のみ）:
    add-user <顧客ID> <メール>        ユーザーを手動で紐付け

【使用例】

  # 顧客を作成
  python manage_customer.py add acme-corp "株式会社ACME"

  # 社員のメールドメインを登録（これで@acme.co.jpの社員400人も自動対応）
  python manage_customer.py add-domain acme-corp acme.co.jp

  # 業務委託者を個別追加（Gmailなど外部メール）
  python manage_customer.py add-email acme-corp tanaka@gmail.com

  # 設定を確認
  python manage_customer.py show acme-corp

【準備】
  - backend/.env に GOOGLE_APPLICATION_CREDENTIALS を設定
  - service-account.json が存在すること
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import firebase_admin
from firebase_admin import credentials, firestore, auth


# ========== ヘルパー関数 ==========

def init_firebase():
    """Firebaseを初期化してFirestoreクライアントを返す"""
    try:
        firebase_admin.get_app()
    except ValueError:
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if cred_path and os.path.exists(cred_path):
            firebase_admin.initialize_app(credentials.Certificate(cred_path))
        else:
            firebase_admin.initialize_app()
    return firestore.client()


def get_customer(db, customer_id):
    """
    顧客を取得する

    Returns:
        (doc_ref, data): 顧客が存在する場合
        (None, None): 顧客が存在しない場合
    """
    doc_ref = db.collection('customers').document(customer_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc_ref, doc.to_dict()
    return None, None


def require_customer(db, customer_id):
    """
    顧客を取得し、存在しない場合はエラーメッセージを表示する

    Returns:
        (doc_ref, data): 顧客が存在する場合
        (None, None): 顧客が存在しない場合（エラーメッセージ表示済み）
    """
    doc_ref, data = get_customer(db, customer_id)
    if not doc_ref:
        print(f"\n❌ エラー: 顧客ID '{customer_id}' が見つかりません")
        print(f"   先に顧客を作成してください:")
        print(f"   python manage_customer.py add {customer_id} \"顧客名\"")
        print()
    return doc_ref, data


def check_conflict(db, field, value, current_customer_id=None):
    """
    他の顧客で同じ値が使われていないかチェックする

    Args:
        db: Firestoreクライアント
        field: チェックするフィールド名（'allowed_domains' または 'allowed_emails'）
        value: チェックする値
        current_customer_id: 現在の顧客ID（自分自身を除外するため）

    Returns:
        str: 競合する顧客ID（競合がある場合）
        None: 競合がない場合
    """
    docs = db.collection('customers').where(field, 'array_contains', value).limit(1).get()
    for doc in docs:
        if doc.id != current_customer_id:
            return doc.id
    return None


# ========== コマンド: 基本操作 ==========

def cmd_list(db):
    """顧客一覧を表示"""
    print("\n=== 顧客一覧 ===\n")
    customers = list(db.collection('customers').stream())

    if not customers:
        print("  （まだ顧客が登録されていません）")
        print()
        print("  顧客を追加するには:")
        print("  python manage_customer.py add 顧客ID \"顧客名\"")
    else:
        for doc in customers:
            data = doc.to_dict()
            name = data.get('name', '名前なし')
            domains = data.get('allowed_domains', [])
            domain_str = f" (@{domains[0]})" if domains else ""
            print(f"  {doc.id}: {name}{domain_str}")

    print(f"\n合計: {len(customers)}社\n")


def cmd_add(db, customer_id, name):
    """顧客を作成"""
    print(f"\n=== 顧客を作成 ===\n")

    # 既に存在するかチェック
    _, existing = get_customer(db, customer_id)
    if existing:
        print(f"❌ エラー: 顧客ID '{customer_id}' は既に存在します")
        print(f"   詳細を見るには: python manage_customer.py show {customer_id}")
        print()
        return

    # 作成
    db.collection('customers').document(customer_id).set({
        'name': name,
        'created_at': firestore.SERVER_TIMESTAMP,
    })

    print(f"✅ 顧客 '{name}' ({customer_id}) を作成しました")
    print()
    print(f"次のステップ:")
    print(f"  python manage_customer.py add-domain {customer_id} example.com")
    print()


def cmd_show(db, customer_id):
    """顧客の詳細を表示"""
    doc_ref, data = require_customer(db, customer_id)
    if not doc_ref:
        return

    name = data.get('name', customer_id)
    print(f"\n=== {name} ===\n")
    print(f"  顧客ID: {customer_id}")
    print(f"  作成日: {data.get('created_at', '不明')}")

    # 自動振り分け設定
    print(f"\n  --- 自動振り分け設定 ---")
    domains = data.get('allowed_domains', [])
    emails = data.get('allowed_emails', [])

    if domains:
        print(f"  許可メールドメイン:")
        for domain in domains:
            print(f"    @{domain}")
    else:
        print(f"  許可メールドメイン: （未設定）")

    if emails:
        print(f"  許可メール（個別）:")
        for email in emails:
            print(f"    {email}")
    elif not domains:
        print(f"  許可メール: （未設定）")

    # 所属ユーザー
    print(f"\n  --- 所属ユーザー ---")
    users = list(db.collection('users').where('customer_id', '==', customer_id).stream())

    if not users:
        print("    （まだ誰もログインしていません）")
    else:
        for user_doc in users[:20]:  # 最大20人まで表示
            user_data = user_doc.to_dict()
            auto = "（自動）" if user_data.get('auto_assigned') else ""
            print(f"    {user_data.get('email', user_doc.id)} {auto}")
        if len(users) > 20:
            print(f"    ... 他 {len(users) - 20}人")

    print(f"\n  ユーザー数: {len(users)}人\n")


def cmd_show_user(db, email):
    """ユーザーの詳細を表示"""
    print(f"\n=== ユーザー詳細: {email} ===\n")

    try:
        user = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        print(f"❌ エラー: メール '{email}' のユーザーが見つかりません")
        print(f"   ユーザーは先にログインしている必要があります")
        print()
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
        if user_data.get('auto_assigned'):
            print(f"  振り分け方法: 自動")
        else:
            print(f"  振り分け方法: 手動")
    print()


# ========== コマンド: 自動振り分け設定 ==========

def cmd_add_domain(db, customer_id, domain):
    """
    顧客に【メールドメイン】を追加（自動振り分け用）

    メールドメイン（メールアドレスの@以降の部分）を登録することで、
    該当するメールドメインを持つユーザーは初回ログイン時に
    自動でこの顧客に振り分けられます。

    Args:
        domain: メールドメイン（例: acme.co.jp）
                ※ @は不要です
    """
    print(f"\n=== メールドメインを追加 ===\n")

    # メールドメイン形式のチェック
    domain = domain.lower().strip()
    if not domain or '.' not in domain or '@' in domain:
        print(f"❌ エラー: 無効なメールドメイン形式です")
        print(f"   正しい例: example.com, acme.co.jp")
        print(f"   ❌ 間違った例: @example.com, https://example.com")
        print()
        return

    # 顧客の存在確認
    doc_ref, data = require_customer(db, customer_id)
    if not doc_ref:
        return

    # 競合チェック
    conflict = check_conflict(db, 'allowed_domains', domain, customer_id)
    if conflict:
        print(f"❌ エラー: メールドメイン '{domain}' は既に顧客 '{conflict}' で使用されています")
        print(f"   1つのメールドメインは1つの顧客にのみ設定できます")
        print()
        return

    # 追加
    doc_ref.update({'allowed_domains': firestore.ArrayUnion([domain])})

    customer_name = data.get('name', customer_id)
    print(f"✅ メールドメイン '@{domain}' を '{customer_name}' に追加しました")
    print()
    print(f"→ @{domain} のユーザーはログイン時に自動で振り分けられます")
    print()


def cmd_add_email(db, customer_id, email):
    """
    顧客にメールアドレスを追加（業務委託者など個別追加用）

    会社のドメインを持たない外部の人（フリーランス等）を
    個別に登録する場合に使用します。
    """
    print(f"\n=== メールアドレスを追加 ===\n")

    # メール形式のチェック
    email = email.lower().strip()
    if not email or '@' not in email or '.' not in email:
        print(f"❌ エラー: 無効なメール形式です")
        print()
        return

    # 顧客の存在確認
    doc_ref, data = require_customer(db, customer_id)
    if not doc_ref:
        return

    # 競合チェック
    conflict = check_conflict(db, 'allowed_emails', email, customer_id)
    if conflict:
        print(f"❌ エラー: メール '{email}' は既に顧客 '{conflict}' で登録されています")
        print()
        return

    # 追加
    doc_ref.update({'allowed_emails': firestore.ArrayUnion([email])})

    customer_name = data.get('name', customer_id)
    print(f"✅ メール '{email}' を '{customer_name}' に追加しました")
    print()
    print(f"→ {email} はログイン時に自動で振り分けられます")
    print()


def cmd_remove_domain(db, customer_id, domain):
    """顧客からメールドメインを削除"""
    print(f"\n=== メールドメインを削除 ===\n")

    doc_ref, _ = require_customer(db, customer_id)
    if not doc_ref:
        return

    domain = domain.lower().strip()
    doc_ref.update({'allowed_domains': firestore.ArrayRemove([domain])})

    print(f"✅ メールドメイン '@{domain}' を削除しました")
    print()
    print("  ⚠️ 注意: 既に振り分け済みのユーザーには影響しません")
    print("     既存ユーザーの紐付けを変更するには別途対応が必要です")
    print()


def cmd_remove_email(db, customer_id, email):
    """顧客からメールアドレスを削除"""
    print(f"\n=== メールアドレスを削除 ===\n")

    doc_ref, _ = require_customer(db, customer_id)
    if not doc_ref:
        return

    email = email.lower().strip()
    doc_ref.update({'allowed_emails': firestore.ArrayRemove([email])})

    print(f"✅ メール '{email}' を削除しました")
    print()
    print("  ⚠️ 注意: 既に振り分け済みのユーザーには影響しません")
    print()


# ========== コマンド: 手動紐付け ==========

def cmd_add_user(db, customer_id, email):
    """
    ユーザーを顧客に手動で紐付ける

    自動振り分けを使わない場合や、特殊なケースで使用します。
    通常は add-domain や add-email を使った自動振り分けを推奨します。
    """
    print(f"\n=== ユーザーを手動で紐付け ===\n")

    doc_ref, data = require_customer(db, customer_id)
    if not doc_ref:
        return

    # Firebase Authでユーザーを検索
    try:
        user = auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        print(f"❌ エラー: メール '{email}' のユーザーが見つかりません")
        print(f"   ユーザーは先にログインしている必要があります")
        print()
        return

    # Custom Claimsを設定
    auth.set_custom_user_claims(user.uid, {'customer_id': customer_id})

    # Firestoreにも記録
    db.collection('users').document(user.uid).set({
        'email': email,
        'customer_id': customer_id,
        'updated_at': firestore.SERVER_TIMESTAMP,
    }, merge=True)

    customer_name = data.get('name', customer_id)
    print(f"✅ ユーザー '{email}' を '{customer_name}' に紐付けました")
    print()
    print("⚠️ 重要: ユーザーに再ログインを依頼してください")
    print("   （新しいトークンを取得するため）")
    print()


# ========== メイン ==========

# コマンド定義: (引数の数, 関数)
COMMANDS = {
    'list': (0, cmd_list),
    'add': (2, cmd_add),
    'show': (1, cmd_show),
    'show-user': (1, cmd_show_user),
    'add-domain': (2, cmd_add_domain),
    'add-email': (2, cmd_add_email),
    'remove-domain': (2, cmd_remove_domain),
    'remove-email': (2, cmd_remove_email),
    'add-user': (2, cmd_add_user),
}


def main():
    # 引数なし、またはヘルプ要求
    if len(sys.argv) < 2 or sys.argv[1] in ['help', '-h', '--help']:
        print(__doc__)
        return

    cmd = sys.argv[1]

    # 不明なコマンド
    if cmd not in COMMANDS:
        print(f"\n❌ 不明なコマンド: {cmd}")
        print(__doc__)
        return

    # 引数の数をチェック
    arg_count, func = COMMANDS[cmd]
    if len(sys.argv) < 2 + arg_count:
        print(f"\n❌ 引数が足りません")
        print()
        if cmd == 'add':
            print(f"  使い方: python manage_customer.py add 顧客ID \"顧客名\"")
            print(f"  例:     python manage_customer.py add acme-corp \"株式会社ACME\"")
        elif cmd == 'show':
            print(f"  使い方: python manage_customer.py show 顧客ID")
            print(f"  例:     python manage_customer.py show acme-corp")
        elif cmd == 'show-user':
            print(f"  使い方: python manage_customer.py show-user メール")
            print(f"  例:     python manage_customer.py show-user yamada@acme.co.jp")
        elif cmd == 'add-domain':
            print(f"  使い方: python manage_customer.py add-domain 顧客ID メールドメイン")
            print(f"  例:     python manage_customer.py add-domain acme-corp acme.co.jp")
            print(f"  ※ メールドメイン = メールアドレスの@以降（例: acme.co.jp）")
        elif cmd == 'add-email':
            print(f"  使い方: python manage_customer.py add-email 顧客ID メール")
            print(f"  例:     python manage_customer.py add-email acme-corp tanaka@gmail.com")
        elif cmd == 'remove-domain':
            print(f"  使い方: python manage_customer.py remove-domain 顧客ID メールドメイン")
        elif cmd == 'remove-email':
            print(f"  使い方: python manage_customer.py remove-email 顧客ID メール")
        elif cmd == 'add-user':
            print(f"  使い方: python manage_customer.py add-user 顧客ID メール")
            print(f"  例:     python manage_customer.py add-user acme-corp yamada@acme.co.jp")
        print()
        return

    # Firebase初期化とコマンド実行
    db = init_firebase()
    args = sys.argv[2:2 + arg_count]
    func(db, *args)


if __name__ == '__main__':
    main()
