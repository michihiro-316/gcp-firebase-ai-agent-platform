"""
認証・認可モジュール

Firebase Authenticationのトークン検証と
ドメイン/メールアドレスによるアクセス制御を行います。

【マルチテナント】
ユーザーのcustomer_idは以下の順序で決定されます：
1. Custom Claimsに既に設定されている場合はそれを使用
2. 未設定の場合、顧客の allowed_emails にメールアドレスが含まれているか確認
3. 未設定の場合、顧客の allowed_domains にドメインが含まれているか確認
4. 自動マッチした場合、Custom Claimsを自動設定

手動設定: manage_customer.py add-user <customer_id> <email>
ドメイン追加: manage_customer.py add-domain <customer_id> <domain>
メール追加: manage_customer.py add-email <customer_id> <email>
"""
import time
from firebase_admin import auth
from .firebase_init import db

# アクセス制御設定のキャッシュ（60秒間有効）
_cache: dict = {}
_CACHE_TTL_SECONDS = 60


def verify_token(id_token: str, check_revoked: bool = True) -> dict:
    """
    Firebase IDトークンを検証し、ユーザー情報を返す

    Args:
        id_token: フロントエンドから送られたFirebase IDトークン
        check_revoked: トークン失効チェックを行うか（本番環境ではTrue推奨）

    Returns:
        ユーザー情報（uid, email など）

    Raises:
        ValueError: トークンが無効または失効している場合
    """
    try:
        # check_revoked=True: ログアウトや無効化されたトークンを拒否
        return auth.verify_id_token(id_token, check_revoked=check_revoked)
    except auth.RevokedIdTokenError:
        raise ValueError("セッションが無効です。再度ログインしてください。")
    except auth.ExpiredIdTokenError:
        raise ValueError("セッションの有効期限が切れました。再度ログインしてください。")
    except auth.InvalidIdTokenError:
        raise ValueError("認証トークンが無効です。")
    except Exception as e:
        raise ValueError(f"トークンの検証に失敗しました: {str(e)}")


def get_access_control_settings() -> dict:
    """
    Firestoreからアクセス制御設定を取得（60秒キャッシュ）

    Returns:
        {"allowed_domains": [...], "allowed_emails": [...]}
    """
    global _cache
    current_time = time.time()

    # キャッシュが有効ならそれを返す
    if _cache and current_time - _cache.get("timestamp", 0) < _CACHE_TTL_SECONDS:
        return _cache["settings"]

    # Firestoreから取得
    doc = db.collection("config").document("access_control").get()
    settings = doc.to_dict() if doc.exists else {
        "allowed_domains": [],
        "allowed_emails": []
    }

    # キャッシュ更新
    _cache = {"settings": settings, "timestamp": current_time}
    return settings


def is_user_allowed(email: str) -> bool:
    """
    ユーザーのメールアドレスがアクセス許可されているか確認

    チェック順序:
    1. allowed_emails に完全一致
    2. allowed_domains にドメインが一致
    3. 両方空なら全員許可

    Args:
        email: ユーザーのメールアドレス

    Returns:
        True: アクセス許可 / False: アクセス拒否
    """
    settings = get_access_control_settings()
    allowed_domains = settings.get("allowed_domains", [])
    allowed_emails = settings.get("allowed_emails", [])

    # 両方空なら全員許可
    if not allowed_domains and not allowed_emails:
        return True

    # メールアドレス完全一致
    if email in allowed_emails:
        return True

    # ドメイン一致
    if email and "@" in email:
        domain = email.split("@")[1]
        if domain in allowed_domains:
            return True

    return False


def find_customer_by_email(email: str) -> str | None:
    """
    メールアドレスから顧客を検索（allowed_emails）

    Args:
        email: ユーザーのメールアドレス

    Returns:
        customer_id or None
    """
    try:
        # allowed_emails にメールが含まれる顧客を検索
        customers = db.collection("customers").where(
            "allowed_emails", "array_contains", email
        ).limit(1).get()

        for doc in customers:
            return doc.id
        return None
    except Exception:
        return None


def find_customer_by_domain(email: str) -> str | None:
    """
    メールドメインから顧客を検索（allowed_domains）

    Args:
        email: ユーザーのメールアドレス

    Returns:
        customer_id or None
    """
    if not email or "@" not in email:
        return None

    domain = email.split("@")[1]

    try:
        # allowed_domains にドメインが含まれる顧客を検索
        customers = db.collection("customers").where(
            "allowed_domains", "array_contains", domain
        ).limit(1).get()

        for doc in customers:
            return doc.id
        return None
    except Exception:
        return None


def auto_assign_customer(uid: str, email: str) -> str | None:
    """
    メールアドレスから顧客を自動検索し、Custom Claimsを設定

    Args:
        uid: Firebase Auth ユーザーID
        email: ユーザーのメールアドレス

    Returns:
        customer_id or None（マッチしなかった場合）
    """
    # 1. allowed_emails でメール完全一致を検索
    customer_id = find_customer_by_email(email)

    # 2. allowed_domains でドメイン一致を検索
    if not customer_id:
        customer_id = find_customer_by_domain(email)

    if not customer_id:
        return None

    # Custom Claimsを自動設定
    try:
        auth.set_custom_user_claims(uid, {"customer_id": customer_id})

        # Firestoreにも記録（バックアップ・監査用）
        from google.cloud.firestore import SERVER_TIMESTAMP
        db.collection("users").document(uid).set({
            "email": email,
            "customer_id": customer_id,
            "auto_assigned": True,
            "updated_at": SERVER_TIMESTAMP,
        }, merge=True)

        return customer_id
    except Exception:
        return None


def get_user_customer_id(uid: str, email: str = None) -> str:
    """
    ユーザーのcustomer_idを取得（自動振り分け対応）

    取得順序:
    1. Custom Claimsに既に設定されている場合はそれを使用
    2. 未設定の場合、allowed_emails / allowed_domains から自動検索・設定

    Args:
        uid: Firebase Auth ユーザーID
        email: ユーザーのメールアドレス（自動振り分け用）

    Returns:
        customer_id

    Raises:
        ValueError: 顧客に紐付けされていない場合
    """
    try:
        user = auth.get_user(uid)
        claims = user.custom_claims or {}
        customer_id = claims.get("customer_id")

        # 既にCustom Claimsがあればそれを返す
        if customer_id:
            return customer_id

        # 自動振り分けを試行
        if email:
            customer_id = auto_assign_customer(uid, email)
            if customer_id:
                return customer_id

        raise ValueError("顧客に紐付けされていません。管理者に連絡してください。")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"顧客情報の取得に失敗しました: {str(e)}")


def authenticate_request(request) -> dict:
    """
    リクエストを認証し、ユーザー情報を返す

    Returns:
        {"uid": "...", "email": "...", "customer_id": "..."}

    Raises:
        ValueError: 認証失敗時
    """
    # Authorizationヘッダーからトークン取得
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        raise ValueError("認証トークンがありません")

    # Bearer トークン形式の検証
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        raise ValueError("認証ヘッダーの形式が不正です")

    id_token = parts[1]
    if not id_token:
        raise ValueError("認証トークンが空です")

    # トークン検証
    user_info = verify_token(id_token)

    # アクセス制御チェック
    email = user_info.get("email", "")
    if not is_user_allowed(email):
        raise ValueError("このアカウントはアクセスが許可されていません")

    # customer_idを追加（自動振り分け対応）
    user_info["customer_id"] = get_user_customer_id(user_info["uid"], email)

    return user_info
