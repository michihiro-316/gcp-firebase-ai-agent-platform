"""
AIエージェント基底クラス

すべてのAIエージェントはこのクラスを継承して実装します。

【新しいエージェントを作る場合】
1. このクラスを継承
2. create_graph() メソッドを実装してLangGraphを定義
3. get_initial_state() メソッドを実装して初期状態を定義

例:
    class MyAgent(BaseAgent):
        def create_graph(self):
            # LangGraphを作成して返す
            ...

        def get_initial_state(self):
            return {"messages": []}
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator
from langgraph.graph import StateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver


class BaseAgent(ABC):
    """
    AIエージェントの基底クラス

    すべてのエージェントはこのクラスを継承して実装します。
    """

    def __init__(self, checkpointer: BaseCheckpointSaver = None):
        """
        Args:
            checkpointer: 状態を永続化するためのチェックポインター
                          Firestoreを使う場合はFirestoreCheckpointerを渡す
        """
        self.checkpointer = checkpointer
        self._graph = None

    @abstractmethod
    def create_graph(self) -> StateGraph:
        """
        LangGraphのグラフを作成

        このメソッドをオーバーライドしてエージェントのロジックを定義します。

        Returns:
            StateGraph: コンパイル前のグラフ
        """
        pass

    @abstractmethod
    def get_initial_state(self) -> dict:
        """
        エージェントの初期状態を返す

        Returns:
            dict: 初期状態
        """
        pass

    @property
    def graph(self):
        """コンパイル済みグラフを取得（遅延初期化）"""
        if self._graph is None:
            state_graph = self.create_graph()
            self._graph = state_graph.compile(checkpointer=self.checkpointer)
        return self._graph

    async def run(
        self,
        user_input: str,
        thread_id: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        エージェントを実行（ストリーミング）

        Args:
            user_input: ユーザーからの入力メッセージ
            thread_id: 会話スレッドID（会話履歴の管理に使用）
            **kwargs: 追加のパラメータ

        Yields:
            str: エージェントからの応答（トークン単位）
        """
        # 設定を作成
        config = {"configurable": {"thread_id": thread_id}}

        # 入力を準備
        state = self.get_initial_state()
        state["messages"] = [{"role": "user", "content": user_input}]

        # ストリーミング実行
        async for event in self.graph.astream_events(state, config, version="v2"):
            # AIのテキスト出力をストリーミング
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

    async def run_sync(
        self,
        user_input: str,
        thread_id: str,
        **kwargs
    ) -> str:
        """
        エージェントを実行（非ストリーミング）

        Args:
            user_input: ユーザーからの入力メッセージ
            thread_id: 会話スレッドID

        Returns:
            str: エージェントからの応答（全文）
        """
        result = []
        async for chunk in self.run(user_input, thread_id, **kwargs):
            result.append(chunk)
        return "".join(result)
