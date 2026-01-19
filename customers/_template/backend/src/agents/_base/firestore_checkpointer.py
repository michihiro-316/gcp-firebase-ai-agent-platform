"""
Firestore Checkpointer

LangGraphの状態をFirestoreに保存します。
顧客ごとにデータを分離（マルチテナント対応）。

【データ構造】
customers/{customer_id}/checkpoints/{thread_id}/checkpoints/{checkpoint_id}
"""
import json
from typing import Any, Optional
from datetime import datetime, timezone
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from google.cloud import firestore


class FirestoreCheckpointer(BaseCheckpointSaver):
    """LangGraphの状態をFirestoreに保存（マルチテナント対応）"""

    def __init__(self, db: firestore.Client, customer_id: str = "default"):
        super().__init__()
        self.db = db
        self.customer_id = customer_id

    def _get_checkpoint_ref(self, thread_id: str):
        """顧客別のチェックポイントコレクション参照を取得"""
        return (
            self.db.collection("customers")
            .document(self.customer_id)
            .collection("checkpoints")
            .document(thread_id)
            .collection("checkpoints")
        )

    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """最新のチェックポイントを取得"""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")

        ref = self._get_checkpoint_ref(thread_id)

        if checkpoint_id:
            # 特定のチェックポイントを取得
            doc = ref.document(checkpoint_id).get()
            if not doc.exists:
                return None
            data = doc.to_dict()
        else:
            # 最新のチェックポイントを取得
            docs = ref.order_by("created_at", direction=firestore.Query.DESCENDING).limit(1).stream()
            docs_list = list(docs)
            if not docs_list:
                return None
            data = docs_list[0].to_dict()
            checkpoint_id = docs_list[0].id

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id,
                }
            },
            checkpoint=self._deserialize(data["checkpoint"]),
            metadata=data.get("metadata", {}),
            parent_config=data.get("parent_config"),
        )

    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> dict:
        """チェックポイントを保存"""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]

        ref = self._get_checkpoint_ref(thread_id)

        doc_data = {
            "checkpoint": self._serialize(checkpoint),
            "metadata": metadata,
            "parent_config": config.get("configurable", {}).get("checkpoint_id"),
            "created_at": datetime.now(timezone.utc),
        }

        ref.document(checkpoint_id).set(doc_data)

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }

    def list(self, config: dict, *, filter: Optional[dict] = None, before: Optional[dict] = None, limit: Optional[int] = None):
        """
        チェックポイント一覧を取得

        Args:
            config: 設定辞書（thread_idを含む）
            filter: フィルタ条件（現在未実装 - BaseCheckpointSaverインターフェース準拠のため定義）
            before: このチェックポイントより前のものを取得（現在未実装 - 同上）
            limit: 取得件数の上限

        Note:
            filter, before引数はLangGraphのBaseCheckpointSaverインターフェースで
            定義されているため引数として受け取りますが、現在の実装では使用していません。
            将来的に必要に応じて実装を追加してください。
        """
        # TODO: filter引数による条件フィルタリングの実装
        # TODO: before引数によるページネーションの実装
        _ = filter  # 未使用引数を明示（linter警告回避）
        _ = before  # 未使用引数を明示（linter警告回避）

        thread_id = config["configurable"]["thread_id"]
        ref = self._get_checkpoint_ref(thread_id)

        query = ref.order_by("created_at", direction=firestore.Query.DESCENDING)

        if limit:
            query = query.limit(limit)

        for doc in query.stream():
            data = doc.to_dict()
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_id": doc.id,
                    }
                },
                checkpoint=self._deserialize(data["checkpoint"]),
                metadata=data.get("metadata", {}),
                parent_config=data.get("parent_config"),
            )

    def _serialize(self, obj: Any) -> str:
        """オブジェクトをJSON文字列に変換"""
        return json.dumps(obj, default=str)

    def _deserialize(self, data: str) -> Any:
        """JSON文字列をオブジェクトに変換"""
        return json.loads(data)
