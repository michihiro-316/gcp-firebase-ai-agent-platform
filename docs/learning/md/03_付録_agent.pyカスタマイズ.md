# 付録: agent.py カスタマイズガイド

<div class="goal-box">
<div class="box-title">🎯 このページのゴール</div>
<div class="box-content">

agent.py を安全にカスタマイズできるようになる

🔥 ゴール達成後のあなた:
「SYSTEM_PROMPT を変えるだけでAIの性格が変わるんだ！」と理解できる

</div>
</div>

---

## そもそも agent.py って何？

<div class="info-box">
<div class="box-title">🤖 AIの「脳みそ」を設定するファイル</div>
<div class="box-content">

agent.py は、AIチャットボットの**性格・能力・記憶力**を決めるファイルです。

**たとえるなら：**
- SYSTEM_PROMPT = AIの「性格」「話し方」
- MODEL_NAME = AIの「頭の良さ」（賢いモデル or 速いモデル）
- MAX_HISTORY_MESSAGES = AIの「記憶力」（何回前の会話まで覚えているか）

**イメージ:**
```
┌──────────────────────────────────────┐
│  agent.py = AIの設定ファイル          │
├──────────────────────────────────────┤
│                                      │
│  「あなたは親切なアシスタントです」   │  ← 性格
│  gemini-1.5-flash                    │  ← 頭の良さ
│  20件まで覚える                       │  ← 記憶力
│                                      │
└──────────────────────────────────────┘
```

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

<!-- HTML図解: LangGraphの処理フロー -->
<div style="margin: 24px 0;">
<div style="display: flex; align-items: center; justify-content: center; gap: 16px; flex-wrap: wrap;">
  <div style="background: #3b82f6; color: white; padding: 16px 24px; border-radius: 8px; text-align: center; min-width: 100px;">
    <div style="font-size: 1.2em; font-weight: bold;">START</div>
    <div style="font-size: 0.8em; opacity: 0.8;">入口</div>
  </div>
  <div style="font-size: 2em; color: #3b82f6;">→</div>
  <div style="background: #10b981; color: white; padding: 16px 24px; border-radius: 8px; text-align: center; min-width: 100px; position: relative;">
    <div style="font-size: 1.2em; font-weight: bold;">chat</div>
    <div style="font-size: 0.8em; opacity: 0.8;">AI応答</div>
    <div style="position: absolute; top: -30px; left: 50%; transform: translateX(-50%); background: #fbbf24; color: #1e293b; padding: 4px 8px; border-radius: 4px; font-size: 0.7em; white-space: nowrap;">ここが _chat_node()</div>
  </div>
  <div style="font-size: 2em; color: #10b981;">→</div>
  <div style="background: #ef4444; color: white; padding: 16px 24px; border-radius: 8px; text-align: center; min-width: 100px;">
    <div style="font-size: 1.2em; font-weight: bold;">END</div>
    <div style="font-size: 0.8em; opacity: 0.8;">出口</div>
  </div>
</div>
<p style="text-align: center; color: #6b7280; margin-top: 12px; font-size: 0.9em;">ユーザーの質問 → AIが回答 → 終了</p>
</div>

</div>
</div>

---

## これだけは守れ！3つのルール

<div class="warning-box">
<div class="box-title">🚨 絶対に守ること</div>
<div class="box-content">

<!-- HTML図解: 3つのルール -->
<div style="display: grid; gap: 16px; margin: 16px 0;">

<!-- ルール1 -->
<div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 16px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
  <span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">ルール1</span>
  <span style="font-weight: bold; color: #b91c1c;">BaseAgent を継承する</span>
</div>

```python
# ✅ 正しい
class MyAgent(BaseAgent):
    pass

# ❌ ダメ（継承を外すと動かない）
class MyAgent:
    pass
```

<div style="background: white; padding: 12px; border-radius: 4px; margin-top: 8px;">
<strong>なぜ？</strong> BaseAgent に <code>run_sync()</code> メソッドがあり、これがAI呼び出し処理を担当しているため。
</div>
</div>

<!-- ルール2 -->
<div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 16px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
  <span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">ルール2</span>
  <span style="font-weight: bold; color: #b91c1c;">create_graph() は StateGraph を返す</span>
</div>

```python
def create_graph(self) -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("chat", self._chat_node)
    graph.set_entry_point("chat")
    graph.add_edge("chat", END)
    return graph  # ← StateGraph を返す（必須）
```

<div style="background: white; padding: 12px; border-radius: 4px; margin-top: 8px;">
<strong>なぜ？</strong> BaseAgent がこのグラフを使ってAIを実行するため。
</div>
</div>

<!-- ルール3 -->
<div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 16px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
  <span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">ルール3</span>
  <span style="font-weight: bold; color: #b91c1c;">_chat_node() は {"messages": [...]} を返す</span>
</div>

```python
async def _chat_node(self, state: AgentState) -> dict:
    # ... 処理 ...
    response = await self.llm.ainvoke(messages)
    return {"messages": [response]}  # ← この形式で返す（必須）
```

<div style="background: white; padding: 12px; border-radius: 4px; margin-top: 8px;">
<strong>なぜ？</strong> LangGraph が会話履歴を管理するために、この形式を期待しているため。
</div>
</div>

</div>

</div>
</div>

---

## 自由に変えていいところ

<div class="tip-box">
<div class="box-title">✅ 編集OK（初心者向け）</div>
<div class="box-content">

<!-- HTML図解: 編集OKな項目 -->
<div style="display: grid; gap: 20px; margin: 16px 0;">

<!-- SYSTEM_PROMPT -->
<div style="background: #ecfdf5; border: 2px solid #10b981; border-radius: 8px; padding: 16px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
  <span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">1</span>
  <span style="font-weight: bold; color: #065f46;">SYSTEM_PROMPT（AIの性格）</span>
</div>

<p style="margin-bottom: 12px;">AIに「あなたは〇〇です」と役割を伝えます。ここを変えるだけでAIの話し方が変わります。</p>

```python
# 💡 例1: 関西弁のAI
SYSTEM_PROMPT = """あなたは関西弁で話すAIアシスタントやで。
ユーザーの質問にフレンドリーに答えてな。
「やで」「やん」「なんでやねん」を使ってな。"""

# 💡 例2: 厳格なビジネスAI
SYSTEM_PROMPT = """あなたは法務部門のAIアシスタントです。
契約書のレビューを専門とします。
常に敬語を使い、法的リスクを指摘してください。"""

# 💡 例3: 優しい先生AI
SYSTEM_PROMPT = """あなたは小学生に教える優しい先生です。
難しい言葉は使わず、たとえ話を使って説明してください。
「〜だね」「〜かな？」など親しみやすい口調で話してください。"""
```

</div>

<!-- MODEL_NAME -->
<div style="background: #ecfdf5; border: 2px solid #10b981; border-radius: 8px; padding: 16px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
  <span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">2</span>
  <span style="font-weight: bold; color: #065f46;">MODEL_NAME（使用するAIモデル）</span>
</div>

<p style="margin-bottom: 12px;">「頭の良さ」と「速さ」のトレードオフです。</p>

```python
# 速い・安い（日常会話向け）
MODEL_NAME = "gemini-1.5-flash"

# 賢い・高い（複雑な推論向け）
MODEL_NAME = "gemini-1.5-pro"
```

<!-- モデル比較表（HTML） -->
<div style="overflow-x: auto; margin-top: 12px;">
<table style="width: 100%; border-collapse: collapse; background: white;">
<tr style="background: #f0fdf4;">
  <th style="padding: 8px; border: 1px solid #d1fae5; text-align: left;">モデル</th>
  <th style="padding: 8px; border: 1px solid #d1fae5; text-align: center;">速度</th>
  <th style="padding: 8px; border: 1px solid #d1fae5; text-align: center;">コスト</th>
  <th style="padding: 8px; border: 1px solid #d1fae5; text-align: left;">おすすめ用途</th>
</tr>
<tr>
  <td style="padding: 8px; border: 1px solid #d1fae5; font-family: monospace;">gemini-1.5-flash</td>
  <td style="padding: 8px; border: 1px solid #d1fae5; text-align: center;">⚡高速</td>
  <td style="padding: 8px; border: 1px solid #d1fae5; text-align: center;">💰安い</td>
  <td style="padding: 8px; border: 1px solid #d1fae5;">一般的な会話、FAQ</td>
</tr>
<tr style="background: #f9fafb;">
  <td style="padding: 8px; border: 1px solid #d1fae5; font-family: monospace;">gemini-1.5-pro</td>
  <td style="padding: 8px; border: 1px solid #d1fae5; text-align: center;">🐢普通</td>
  <td style="padding: 8px; border: 1px solid #d1fae5; text-align: center;">💰💰高い</td>
  <td style="padding: 8px; border: 1px solid #d1fae5;">複雑な推論、分析</td>
</tr>
<tr>
  <td style="padding: 8px; border: 1px solid #d1fae5; font-family: monospace;">gemini-2.0-flash</td>
  <td style="padding: 8px; border: 1px solid #d1fae5; text-align: center;">⚡最速</td>
  <td style="padding: 8px; border: 1px solid #d1fae5; text-align: center;">💰安い</td>
  <td style="padding: 8px; border: 1px solid #d1fae5;">最新機能が必要時</td>
</tr>
</table>
</div>

</div>

<!-- MAX_HISTORY_MESSAGES -->
<div style="background: #ecfdf5; border: 2px solid #10b981; border-radius: 8px; padding: 16px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
  <span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">3</span>
  <span style="font-weight: bold; color: #065f46;">MAX_HISTORY_MESSAGES（会話の記憶量）</span>
</div>

<p style="margin-bottom: 12px;">AIが「何回前の会話まで覚えているか」を設定します。</p>

```python
# 少なめ（コスト重視）
MAX_HISTORY_MESSAGES = 10  # 約5往復分

# 普通（バランス型）← おすすめ
MAX_HISTORY_MESSAGES = 20  # 約10往復分

# 多め（記憶力重視）
MAX_HISTORY_MESSAGES = 40  # 約20往復分
```

<div style="background: #fffbeb; border: 1px solid #f59e0b; padding: 12px; border-radius: 4px; margin-top: 8px;">
⚠️ <strong>注意:</strong> 多いほど「賢く」なりますが、コストも増えます
</div>

</div>

</div>

</div>
</div>

---

## 全体の構造（図解）

<div class="info-box">
<div class="box-title">🏗️ agent.py の構造</div>
<div class="box-content">

<!-- HTML図解: ファイル構造 -->
<div style="background: #1e293b; border-radius: 8px; padding: 20px; color: #e2e8f0; font-family: monospace;">

<div style="color: #94a3b8; margin-bottom: 16px;">agent.py</div>

<!-- 編集OKゾーン -->
<div style="background: rgba(34, 197, 94, 0.2); border: 2px solid #22c55e; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
<div style="color: #22c55e; font-weight: bold; margin-bottom: 8px;">🟢 自由に編集OK</div>
<div style="color: #e2e8f0;">
<div>SYSTEM_PROMPT = "..."  <span style="color: #94a3b8;">← AIの性格</span></div>
<div>MODEL_NAME = "..."     <span style="color: #94a3b8;">← 使うモデル</span></div>
<div>MAX_HISTORY_MESSAGES   <span style="color: #94a3b8;">← 記憶する会話数</span></div>
</div>
</div>

<!-- 触らないゾーン -->
<div style="background: rgba(239, 68, 68, 0.2); border: 2px solid #ef4444; border-radius: 8px; padding: 16px;">
<div style="color: #ef4444; font-weight: bold; margin-bottom: 8px;">🔴 触らない方がいい</div>
<div style="color: #e2e8f0;">
<div>class XxxAgent(BaseAgent):  <span style="color: #94a3b8;">← 継承は外さない</span></div>
<div style="margin-top: 8px;">def create_graph(self):</div>
<div style="padding-left: 20px;">return StateGraph(...)  <span style="color: #94a3b8;">← StateGraph を返す</span></div>
<div style="margin-top: 8px;">async def _chat_node(self, state):</div>
<div style="padding-left: 20px;">return {"messages": [...]}  <span style="color: #94a3b8;">← この形式で返す</span></div>
</div>
</div>

</div>

</div>
</div>

---

## よくある質問

<div class="info-box">
<div class="box-title">❓ FAQ</div>
<div class="box-content">

<details style="margin-bottom: 12px; background: #f9fafb; border-radius: 8px;">
<summary style="cursor: pointer; padding: 12px; font-weight: bold;">Q: 壊してしまったら？</summary>
<div style="padding: 0 12px 12px 12px;">

```bash
git checkout agent.py
```
で元に戻せます。心配せずに試してみてください！

</div>
</details>

<details style="margin-bottom: 12px; background: #f9fafb; border-radius: 8px;">
<summary style="cursor: pointer; padding: 12px; font-weight: bold;">Q: 新しい顧客用のエージェントを作りたい</summary>
<div style="padding: 0 12px 12px 12px;">

```bash
cp -r _template acme-corp
```
でコピーして、`acme-corp/agent.py` を編集します。

</div>
</details>

<details style="margin-bottom: 12px; background: #f9fafb; border-radius: 8px;">
<summary style="cursor: pointer; padding: 12px; font-weight: bold;">Q: temperature って何？</summary>
<div style="padding: 0 12px 12px 12px;">

AIの「創造性」を調整するパラメータです（`__init__` 内にあります）。

| 値 | 特徴 | 用途 |
|----|------|------|
| 0.0 | 毎回同じ回答 | FAQ、定型文 |
| 0.7 | バランス型（デフォルト） | 一般会話 |
| 1.0 | 創造的・多様 | ブレスト、物語生成 |

</div>
</details>

<details style="margin-bottom: 12px; background: #f9fafb; border-radius: 8px;">
<summary style="cursor: pointer; padding: 12px; font-weight: bold;">Q: もっと複雑なことがしたい（ツール使用、条件分岐）</summary>
<div style="padding: 0 12px 12px 12px;">

以下のリソースを参照してください：

- <a href="https://langchain-ai.github.io/langgraph/" target="_blank">LangGraph公式ドキュメント</a>
- <a href="https://michihiro-316.github.io/langchain-langgraph-docs/langgraph/" target="_blank">LangGraph学習ガイド（日本語）</a>

</div>
</details>

</div>
</div>

---

## まとめ

<div class="summary-box">
<div class="box-title">📝 覚えること</div>
<div class="box-content">

<!-- まとめ表（HTML） -->
<div style="overflow-x: auto; margin: 16px 0;">
<table style="width: 100%; border-collapse: collapse;">
<tr style="background: #f0fdf4;">
  <th style="padding: 12px; border: 1px solid #d1fae5; text-align: left;">やること</th>
  <th style="padding: 12px; border: 1px solid #d1fae5; text-align: left;">やり方</th>
</tr>
<tr>
  <td style="padding: 12px; border: 1px solid #e5e7eb;">AIの性格を変える</td>
  <td style="padding: 12px; border: 1px solid #e5e7eb;"><code>SYSTEM_PROMPT</code> を編集</td>
</tr>
<tr style="background: #f9fafb;">
  <td style="padding: 12px; border: 1px solid #e5e7eb;">モデルを変える</td>
  <td style="padding: 12px; border: 1px solid #e5e7eb;"><code>MODEL_NAME</code> を編集</td>
</tr>
<tr>
  <td style="padding: 12px; border: 1px solid #e5e7eb;">記憶力を変える</td>
  <td style="padding: 12px; border: 1px solid #e5e7eb;"><code>MAX_HISTORY_MESSAGES</code> を編集</td>
</tr>
<tr style="background: #f9fafb;">
  <td style="padding: 12px; border: 1px solid #e5e7eb;">壊したら</td>
  <td style="padding: 12px; border: 1px solid #e5e7eb;"><code>git checkout agent.py</code></td>
</tr>
</table>
</div>

<!-- 3つのルール（HTML） -->
<div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 16px; margin-top: 16px;">
<div style="font-weight: bold; color: #b91c1c; margin-bottom: 8px;">🚨 3つの絶対ルール:</div>
<ol style="margin: 0; padding-left: 20px; color: #1e293b;">
<li><code>BaseAgent</code> を継承する</li>
<li><code>create_graph()</code> は <code>StateGraph</code> を返す</li>
<li><code>_chat_node()</code> は <code>{"messages": [...]}</code> を返す</li>
</ol>
</div>

<p style="margin-top: 20px;"><strong>→ <a href="03_バックエンド解説.html">バックエンド解説に戻る</a></strong></p>

</div>
</div>
