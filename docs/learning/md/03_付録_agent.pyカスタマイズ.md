# 付録: agent.py カスタマイズガイド

<div class="goal-box">
<div class="box-title">🎯 このページのゴール</div>
<div class="box-content">

agent.py を安全にカスタマイズできるようになる

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

### ルール2: create_graph() は StateGraph を返す

```python
def create_graph(self) -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("chat", self._chat_node)
    graph.set_entry_point("chat")
    graph.add_edge("chat", END)
    return graph  # ← StateGraph を返す
```

### ルール3: _chat_node() は {"messages": [...]} を返す

```python
async def _chat_node(self, state: AgentState) -> dict:
    # ... 処理 ...
    response = await self.llm.ainvoke(messages)
    return {"messages": [response]}  # ← この形式で返す
```

</div>
</div>

---

## 自由に変えていいところ

<div class="tip-box">
<div class="box-title">✅ 編集OK</div>
<div class="box-content">

| 項目 | 場所 | 変更するとどうなる |
|------|------|------------------|
| AIの性格 | `SYSTEM_PROMPT` | 話し方・役割が変わる |
| AIモデル | `MODEL_NAME` | 速度・コスト・精度が変わる |
| 記憶力 | `MAX_HISTORY_MESSAGES` | 会話の記憶量が変わる |

### 例: 関西弁のAIにする

```python
SYSTEM_PROMPT = """あなたは関西弁で話すAIアシスタントやで。
ユーザーの質問にフレンドリーに答えてな。
「やで」「やん」「なんでやねん」を使ってな。"""
```

### 例: モデルを変える

```python
# 速い・安い
MODEL_NAME = "gemini-1.5-flash"

# 賢い・高い
MODEL_NAME = "gemini-1.5-pro"
```

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
│  【自由に編集OK】                                        │
│  ┌───────────────────────────────────────────────────┐ │
│  │ SYSTEM_PROMPT = "..."   ← AIの性格               │ │
│  │ MODEL_NAME = "..."      ← 使うモデル             │ │
│  │ MAX_HISTORY_MESSAGES    ← 記憶する会話数         │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  【触らない方がいい】                                    │
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

**Q: 新しい顧客用のエージェントを作りたい**

```bash
cp -r _template acme-corp
```
でコピーして、`acme-corp/agent.py` を編集。

**Q: もっと複雑なことがしたい（ツール使用、条件分岐）**

→ [LangGraph公式ドキュメント](https://langchain-ai.github.io/langgraph/) を参照

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

**→ [バックエンド解説に戻る](03_バックエンド解説.html)**

</div>
</div>
