# 付録: agent.py カスタマイズガイド

<div class="goal-box">
<div class="box-title">🎯 このページのゴール</div>
<div class="box-content">

agent.py を安全にカスタマイズできるようになる

</div>
</div>

---

## LangGraph とは？（たとえ話で理解）

<div class="info-box">
<div class="box-title">🏢 会社の業務フローで考えよう</div>
<div class="box-content">

LangGraph は「AIの思考の流れ」を定義するフレームワークです。

**会社で書類を回すイメージ：**

| LangGraph用語 | 会社でいうと | 役割 |
|---------------|-------------|------|
| **State** | 回覧ファイル | 社員間で共有する情報（会話履歴など） |
| **Node** | 社員 | 自分の担当処理をする（AIに質問など） |
| **Edge** | 業務フロー | 誰から誰へ処理を回すか |

```
┌─────────┐      ┌─────────┐      ┌─────────┐
│  START  │ ──→ │  chat   │ ──→ │   END   │
│ (入口)  │      │ (AI応答)│      │ (出口)  │
└─────────┘      └─────────┘      └─────────┘
                      ↑
              ここが _chat_node()
```

</div>
</div>

---

## これだけは守れ！3つのルール

<div class="warning-box">
<div class="box-title">🚨 絶対に守ること</div>
<div class="box-content">

### ルール1: BaseAgent を継承する

```python
# ✅ 正しい
class MyAgent(BaseAgent):
    pass

# ❌ ダメ（継承を外すと動かない）
class MyAgent:
    pass
```

**なぜ？** BaseAgent に `run()` メソッドがあり、これがストリーミング処理を担当しているため。

---

### ルール2: create_graph() は StateGraph を返す

```python
def create_graph(self) -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("chat", self._chat_node)
    graph.set_entry_point("chat")
    graph.add_edge("chat", END)
    return graph  # ← StateGraph を返す（必須）
```

**なぜ？** BaseAgent がこのグラフを使ってAIを実行するため。

---

### ルール3: _chat_node() は {"messages": [...]} を返す

```python
async def _chat_node(self, state: AgentState) -> dict:
    # ... 処理 ...
    response = await self.llm.ainvoke(messages)
    return {"messages": [response]}  # ← この形式で返す（必須）
```

**なぜ？** LangGraph が会話履歴を管理するために、この形式を期待しているため。

</div>
</div>

---

## 自由に変えていいところ

<div class="tip-box">
<div class="box-title">✅ 編集OK（初心者向け）</div>
<div class="box-content">

### 1. SYSTEM_PROMPT（AIの性格）

```python
# 💡 例1: 関西弁のAI
SYSTEM_PROMPT = """あなたは関西弁で話すAIアシスタントやで。
ユーザーの質問にフレンドリーに答えてな。
「やで」「やん」「なんでやねん」を使ってな。"""

# 💡 例2: 厳格なビジネスAI
SYSTEM_PROMPT = """あなたは法務部門のAIアシスタントです。
契約書のレビューを専門とします。
常に敬語を使い、法的リスクを指摘してください。"""
```

---

### 2. MODEL_NAME（使用するAIモデル）

```python
# 速い・安い（日常会話向け）
MODEL_NAME = "gemini-1.5-flash"

# 賢い・高い（複雑な推論向け）
MODEL_NAME = "gemini-1.5-pro"

# 最新機能（新機能を試したいとき）
MODEL_NAME = "gemini-2.0-flash"
```

| モデル | 速度 | コスト | おすすめ用途 |
|--------|------|--------|-------------|
| gemini-1.5-flash | ⚡高速 | 💰安い | 一般的な会話 |
| gemini-1.5-pro | 🐢普通 | 💰💰高い | 複雑な推論 |
| gemini-2.0-flash | ⚡最速 | 💰安い | 最新機能が必要時 |

---

### 3. MAX_HISTORY_MESSAGES（会話の記憶量）

```python
# 少なめ（コスト重視）
MAX_HISTORY_MESSAGES = 10  # 約5往復分

# 普通（バランス型）
MAX_HISTORY_MESSAGES = 20  # 約10往復分

# 多め（記憶力重視）
MAX_HISTORY_MESSAGES = 40  # 約20往復分
```

⚠️ 多いほどコストが増えます

</div>
</div>

---

## 全体の構造（図解）

<div class="info-box">
<div class="box-title">🏗️ agent.py の構造</div>
<div class="box-content">

```
┌─────────────────────────────────────────────────────────┐
│  agent.py                                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🟢【自由に編集OK】                                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │ SYSTEM_PROMPT = "..."   ← AIの性格               │ │
│  │ MODEL_NAME = "..."      ← 使うモデル             │ │
│  │ MAX_HISTORY_MESSAGES    ← 記憶する会話数         │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  🔴【触らない方がいい】                                  │
│  ┌───────────────────────────────────────────────────┐ │
│  │ class XxxAgent(BaseAgent):  ← 継承は外さない     │ │
│  │                                                   │ │
│  │ def create_graph(self):                          │ │
│  │     return StateGraph(...)  ← StateGraph を返す  │ │
│  │                                                   │ │
│  │ async def _chat_node(self, state):               │ │
│  │     return {"messages": [...]}  ← この形式で返す │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

</div>
</div>

---

## よくある質問

<div class="info-box">
<div class="box-title">❓ FAQ</div>
<div class="box-content">

**Q: 壊してしまったら？**

```bash
git checkout agent.py
```
で元に戻せます。

---

**Q: 新しい顧客用のエージェントを作りたい**

```bash
cp -r _template acme-corp
```
でコピーして、`acme-corp/agent.py` を編集。

---

**Q: temperature って何？**

AIの「創造性」を調整するパラメータです。

| 値 | 特徴 | 用途 |
|----|------|------|
| 0.0 | 毎回同じ回答 | FAQ、定型文 |
| 0.7 | バランス型（デフォルト） | 一般会話 |
| 1.0 | 創造的・多様 | ブレスト、物語生成 |

---

**Q: もっと複雑なことがしたい（ツール使用、条件分岐）**

→ [LangGraph公式ドキュメント](https://langchain-ai.github.io/langgraph/) を参照

→ [LangGraph学習ガイド](https://michihiro-316.github.io/langchain-langgraph-docs/langgraph/)（日本語）

</div>
</div>

---

## まとめ

<div class="summary-box">
<div class="box-title">📝 覚えること</div>
<div class="box-content">

| やること | やり方 |
|----------|--------|
| AIの性格を変える | `SYSTEM_PROMPT` を編集 |
| モデルを変える | `MODEL_NAME` を編集 |
| 記憶力を変える | `MAX_HISTORY_MESSAGES` を編集 |
| 壊したら | `git checkout agent.py` |

**3つの絶対ルール:**
1. `BaseAgent` を継承する
2. `create_graph()` は `StateGraph` を返す
3. `_chat_node()` は `{"messages": [...]}` を返す

**→ <a href="03_バックエンド解説.html">バックエンド解説に戻る</a>**

</div>
</div>
