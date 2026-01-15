"""
サンプルエージェント

シンプルなQ&Aチャットボットの実装です。
LangGraphとVertex AI (Gemini)を使用しています。

【カスタマイズ方法】
1. system_prompt を変更してAIの性格を調整
2. model_name を変更してモデルを切り替え
3. create_graph() を変更して複雑なワークフローを追加
4. MAX_HISTORY_MESSAGES を変更して会話履歴の保持数を調整
"""
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import StateGraph, END

from ..base_agent import BaseAgent
from .state import AgentState


class SampleAgent(BaseAgent):
    """
    サンプルQ&Aエージェント

    シンプルな会話を行うエージェントです。
    ユーザーの質問に対してGeminiが回答します。

    会話履歴は直近20件まで記憶します。
    """

    # システムプロンプト（AIの性格・役割を定義）
    SYSTEM_PROMPT = """あなたは親切で丁寧なAIアシスタントです。
ユーザーの質問に対して、わかりやすく簡潔に回答してください。
日本語で回答してください。
過去の会話の文脈を踏まえて回答してください。"""

    # 使用するモデル
    MODEL_NAME = "gemini-1.5-flash"

    # 会話履歴の最大保持数（ユーザー+アシスタントのメッセージペアで約10往復分）
    MAX_HISTORY_MESSAGES = 20

    def __init__(self, checkpointer=None, project_id: str = None, location: str = "asia-northeast1"):
        """
        Args:
            checkpointer: 状態永続化用のチェックポインター
            project_id: GCPプロジェクトID
            location: Vertex AIのリージョン
        """
        super().__init__(checkpointer)
        self.project_id = project_id
        self.location = location

        # LLMを初期化
        self.llm = ChatVertexAI(
            model=self.MODEL_NAME,
            project=project_id,
            location=location,
            temperature=0.7,
            max_tokens=2048,
            streaming=True,
        )

    def create_graph(self) -> StateGraph:
        """
        LangGraphのグラフを作成

        このサンプルでは単純な1ノードのグラフです：
        [START] -> [chat] -> [END]

        より複雑なエージェントでは、条件分岐や複数ノードを追加できます。
        """
        # グラフを作成
        graph = StateGraph(AgentState)

        # ノードを追加
        graph.add_node("chat", self._chat_node)

        # エッジを追加（フローを定義）
        graph.set_entry_point("chat")
        graph.add_edge("chat", END)

        return graph

    def get_initial_state(self) -> dict:
        """初期状態を返す"""
        return {"messages": []}

    def _trim_messages(self, messages: list) -> list:
        """
        メッセージ履歴を直近N件に制限する

        古いメッセージを削除し、トークン数を節約します。
        会話の流れを保つため、直近のメッセージを優先します。

        Args:
            messages: 全メッセージリスト

        Returns:
            直近MAX_HISTORY_MESSAGES件のメッセージ
        """
        if len(messages) <= self.MAX_HISTORY_MESSAGES:
            return messages

        # 直近N件のメッセージのみを保持
        return messages[-self.MAX_HISTORY_MESSAGES:]

    async def _chat_node(self, state: AgentState) -> dict:
        """
        チャットノード

        ユーザーのメッセージを受け取り、LLMで応答を生成します。
        会話履歴は直近20件まで使用します。
        """
        messages = state["messages"]

        # 会話履歴を直近N件に制限
        trimmed_messages = self._trim_messages(messages)

        # システムプロンプトを先頭に追加
        full_messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *trimmed_messages
        ]

        # LLMで応答を生成
        response = await self.llm.ainvoke(full_messages)

        return {"messages": [response]}
