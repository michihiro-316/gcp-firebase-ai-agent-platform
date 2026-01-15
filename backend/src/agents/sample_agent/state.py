"""
エージェントの状態定義

LangGraphで管理する状態の型を定義します。
"""
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    エージェントの状態

    Attributes:
        messages: 会話履歴。add_messagesアノテーションにより
                  新しいメッセージが自動的に追加される
    """
    messages: Annotated[list, add_messages]
