"""
レート制限モジュール

ユーザーごとに1分間あたりのリクエスト数を制限します。
制限値はFirestoreの設定で変更可能です。

【仕組み】
- Firestoreにユーザーごとのリクエスト履歴を保存
- 過去1分間のリクエスト数をカウント
- 制限を超えた場合はエラーを返す
"""
import logging
from datetime import datetime, timedelta, timezone
from .firebase_init import db
from .auth import get_access_control_settings
from .config import config

logger = logging.getLogger(__name__)


def _filter_recent_timestamps(timestamps: list, one_minute_ago: datetime) -> list:
    """1分以内のタイムスタンプのみをフィルタリング"""
    return [
        ts for ts in timestamps
        if ts.replace(tzinfo=None) > one_minute_ago
    ]


def check_rate_limit(user_id: str) -> bool:
    """
    ユーザーのレート制限をチェック

    Args:
        user_id: ユーザーのUID

    Returns:
        True: リクエスト許可
        False: 制限超過

    副作用:
        リクエストをFirestoreに記録
    """
    # 設定からレート制限値を取得
    settings = get_access_control_settings()
    limit = settings.get("rate_limit_per_minute", config.DEFAULT_RATE_LIMIT)

    # 現在時刻と1分前の時刻
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    one_minute_ago = now - timedelta(minutes=1)

    # ユーザーのリクエスト履歴を取得
    requests_ref = db.collection("rate_limits").document(user_id)

    # トランザクションでチェックと記録を行う
    @db.transaction
    def check_and_record(transaction):
        doc = requests_ref.get(transaction=transaction)

        if doc.exists:
            data = doc.to_dict()
            timestamps = data.get("timestamps", [])
        else:
            timestamps = []

        # 1分以内のリクエストのみをフィルタ
        recent_timestamps = _filter_recent_timestamps(timestamps, one_minute_ago)

        # 制限チェック
        if len(recent_timestamps) >= limit:
            return False

        # 新しいリクエストを記録
        recent_timestamps.append(now)

        transaction.set(requests_ref, {
            "timestamps": recent_timestamps,
            "last_request": now
        })

        return True

    try:
        return check_and_record(db.transaction())
    except Exception as e:
        # エラー時は安全側に倒して許可（サービス継続を優先）
        # ただし、エラー内容はログに記録して後から調査可能にする
        logger.warning(
            f"レート制限チェック中にエラーが発生しました（user_id={user_id}）: {e}",
            exc_info=True  # スタックトレースも記録
        )
        return True
