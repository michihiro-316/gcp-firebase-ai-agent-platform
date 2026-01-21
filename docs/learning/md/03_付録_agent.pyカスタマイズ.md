# 付録: agent.py カスタマイズガイド

<div class="goal-box">
<div class="box-title">🎯 このページのゴール</div>
<div class="box-content">

agent.py を安全にカスタマイズできるようになる！

🔥 ゴール達成後のあなた:
「ここは触っていい、ここは触っちゃダメ」が判断できる

</div>
</div>

---

## これだけは守れ！ルール表

<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 12px; padding: 24px; margin: 20px 0;">

<div style="display: grid; gap: 16px;">

<!-- 安全ゾーン -->
<div style="background: rgba(34, 197, 94, 0.15); border: 2px solid #22c55e; border-radius: 8px; padding: 16px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
<span style="font-size: 24px;">🟢</span>
<span style="color: #22c55e; font-weight: bold; font-size: 18px;">安全に編集OK</span>
<span style="color: #94a3b8; font-size: 14px;">← 初心者はここだけ触ろう！</span>
</div>
<table style="width: 100%; border-collapse: collapse;">
<tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
<td style="padding: 8px; color: #22c55e; font-family: monospace;">SYSTEM_PROMPT</td>
<td style="padding: 8px; color: #e2e8f0;">AIの性格・役割を変更</td>
<td style="padding: 8px; color: #94a3b8;">例: 「関西弁で話して」「敬語で」</td>
</tr>
<tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
<td style="padding: 8px; color: #22c55e; font-family: monospace;">MODEL_NAME</td>
<td style="padding: 8px; color: #e2e8f0;">使用するAIモデルを変更</td>
<td style="padding: 8px; color: #94a3b8;">gemini-1.5-flash / pro / 2.0</td>
</tr>
<tr>
<td style="padding: 8px; color: #22c55e; font-family: monospace;">MAX_HISTORY_MESSAGES</td>
<td style="padding: 8px; color: #e2e8f0;">会話履歴の保持数</td>
<td style="padding: 8px; color: #94a3b8;">多い=記憶力UP、コストUP</td>
</tr>
</table>
</div>

<!-- 注意ゾーン -->
<div style="background: rgba(234, 179, 8, 0.15); border: 2px solid #eab308; border-radius: 8px; padding: 16px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
<span style="font-size: 24px;">🟡</span>
<span style="color: #eab308; font-weight: bold; font-size: 18px;">理解してから編集</span>
<span style="color: #94a3b8; font-size: 14px;">← 中級者向け</span>
</div>
<table style="width: 100%; border-collapse: collapse;">
<tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
<td style="padding: 8px; color: #eab308; font-family: monospace;">__init__()</td>
<td style="padding: 8px; color: #e2e8f0;">初期化処理の追加</td>
<td style="padding: 8px; color: #94a3b8;">外部API接続など</td>
</tr>
<tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
<td style="padding: 8px; color: #eab308; font-family: monospace;">_chat_node()</td>
<td style="padding: 8px; color: #e2e8f0;">チャット処理のカスタマイズ</td>
<td style="padding: 8px; color: #94a3b8;">前処理・後処理の追加</td>
</tr>
<tr>
<td style="padding: 8px; color: #eab308; font-family: monospace;">temperature</td>
<td style="padding: 8px; color: #e2e8f0;">AIの創造性調整（0~1）</td>
<td style="padding: 8px; color: #94a3b8;">0=確実、1=創造的</td>
</tr>
</table>
</div>

<!-- 危険ゾーン -->
<div style="background: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444; border-radius: 8px; padding: 16px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
<span style="font-size: 24px;">🔴</span>
<span style="color: #ef4444; font-weight: bold; font-size: 18px;">変更時は慎重に</span>
<span style="color: #94a3b8; font-size: 14px;">← 上級者向け、壊れる可能性あり</span>
</div>
<table style="width: 100%; border-collapse: collapse;">
<tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
<td style="padding: 8px; color: #ef4444; font-family: monospace;">create_graph()</td>
<td style="padding: 8px; color: #e2e8f0;">処理フローの変更</td>
<td style="padding: 8px; color: #94a3b8;">LangGraph理解必須</td>
</tr>
<tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
<td style="padding: 8px; color: #ef4444; font-family: monospace;">BaseAgent継承</td>
<td style="padding: 8px; color: #e2e8f0;">基底クラスからの継承</td>
<td style="padding: 8px; color: #94a3b8;">絶対に外さない！</td>
</tr>
<tr>
<td style="padding: 8px; color: #ef4444; font-family: monospace;">get_initial_state()</td>
<td style="padding: 8px; color: #e2e8f0;">初期状態の定義</td>
<td style="padding: 8px; color: #94a3b8;">messagesキー必須</td>
</tr>
</table>
</div>

</div>
</div>

---

## ペルソナ別アドバイス

<details style="margin: 16px 0; background: #1e293b; border-radius: 8px; padding: 4px;">
<summary style="cursor: pointer; padding: 16px; font-weight: bold; color: #38bdf8; font-size: 18px;">
👶 初学者向け（Python 2ヶ月程度）
</summary>
<div style="padding: 0 16px 16px 16px; color: #e2e8f0;">

### やっていいこと ✅
1. **SYSTEM_PROMPT を書き換える**
   - 「あなたは〇〇です」で始める
   - 具体的な指示を書く
   - 日本語でOK

2. **MODEL_NAME を変更する**
   - `gemini-1.5-flash` → 速い、安い
   - `gemini-1.5-pro` → 賢い、高い

3. **MAX_HISTORY_MESSAGES を調整する**
   - 10〜30 が目安
   - 大きすぎるとコスト増

### やってはいけないこと ❌
- `class TemplateAgent(BaseAgent):` の `BaseAgent` を消す
- `create_graph()` の中身を消す
- `from` や `import` の行を消す

### 困ったら
1. `git checkout agent.py` で元に戻せる
2. テンプレートからコピーし直す

</div>
</details>

<details style="margin: 16px 0; background: #1e293b; border-radius: 8px; padding: 4px;">
<summary style="cursor: pointer; padding: 16px; font-weight: bold; color: #a78bfa; font-size: 18px;">
🔧 ベテラン向け（設計の意図を知りたい）
</summary>
<div style="padding: 0 16px 16px 16px; color: #e2e8f0;">

### なぜこの設計？

**Q: なぜ BaseAgent を継承？**
> - `run()` メソッドのストリーミング処理を共通化
> - checkpointer の初期化を一元管理
> - 新しいエージェント追加時の実装量を最小化

**Q: なぜ LangGraph？**
> - 会話履歴の永続化が組み込み
> - 複雑なワークフロー（ツール使用、条件分岐）への拡張が容易
> - 状態管理が明示的

**Q: なぜ Gemini？**
> - Google Cloud との統合が容易（Vertex AI）
> - 日本語性能が良い
> - Cloud Run との相性が良い（認証連携）

### 拡張ポイント
- **ツール追加**: `_chat_node` でツールバインディング
- **条件分岐**: `create_graph()` でノード追加
- **RAG統合**: `_chat_node` の前処理で検索

</div>
</details>

<details style="margin: 16px 0; background: #1e293b; border-radius: 8px; padding: 4px;">
<summary style="cursor: pointer; padding: 16px; font-weight: bold; color: #f472b6; font-size: 18px;">
📊 PM向け（コスト・性能トレードオフ）
</summary>
<div style="padding: 0 16px 16px 16px; color: #e2e8f0;">

### モデル選択の判断基準

| 項目 | gemini-1.5-flash | gemini-1.5-pro |
|------|------------------|----------------|
| 速度 | ⚡ 高速 | 🐢 やや遅い |
| コスト | 💰 安い | 💰💰💰 高い |
| 品質 | ◯ 十分 | ◎ 高品質 |
| 用途 | 一般的なQ&A | 複雑な推論、専門知識 |

### コスト最適化のポイント

1. **MAX_HISTORY_MESSAGES を減らす**
   - 20 → 10 でコスト約半減
   - ただし文脈理解は低下

2. **SYSTEM_PROMPT を短くする**
   - 長いプロンプト = 毎回のコスト増
   - 必要最小限に

3. **温度(temperature)を下げる**
   - 0.7 → 0.3
   - 短い回答になりやすい = コスト減

### ROI試算の目安
- 1リクエストあたり: 約 0.1〜1円（モデル・履歴量による）
- 月間1万リクエスト: 約 1,000〜10,000円

</div>
</details>

<details style="margin: 16px 0; background: #1e293b; border-radius: 8px; padding: 4px;">
<summary style="cursor: pointer; padding: 16px; font-weight: bold; color: #4ade80; font-size: 18px;">
📚 学生向け（学習の優先順位）
</summary>
<div style="padding: 0 16px 16px 16px; color: #e2e8f0;">

### 学習ロードマップ

```
Step 1: SYSTEM_PROMPT を変えて遊ぶ（1日）
   ↓
Step 2: Pythonのクラス継承を学ぶ（1週間）
   ↓
Step 3: async/await を理解する（1週間）
   ↓
Step 4: LangChain の基本を学ぶ（2週間）
   ↓
Step 5: LangGraph でワークフロー作成（2週間）
```

### おすすめ学習リソース

1. **Python 基礎**
   - クラス、継承、デコレーター

2. **非同期処理**
   - async/await、ジェネレーター

3. **LangChain / LangGraph**
   - 公式チュートリアル
   - https://langchain-ai.github.io/langgraph/

### 実験してみよう

1. SYSTEM_PROMPT を変えてみる
   - 「猫語で話す」「俳句で返答する」

2. temperature を 0 と 1 で比べる
   - 同じ質問を何度もして違いを見る

3. MAX_HISTORY_MESSAGES を 2 にしてみる
   - AIがすぐ忘れることを体験

</div>
</details>

---

## よくある失敗パターン

<div class="warning-box">
<div class="box-title">⚠️ これやると壊れます！</div>
<div class="box-content">

### 1. BaseAgent 継承を外す
```python
# ❌ ダメ
class TemplateAgent:  # BaseAgent がない！

# ✅ 正しい
class TemplateAgent(BaseAgent):
```

### 2. create_graph() を消す
```python
# ❌ ダメ - 必須メソッドを削除
# def create_graph(self): を削除してしまう

# ✅ 正しい - 中身を変えるのはOK
def create_graph(self) -> StateGraph:
    graph = StateGraph(AgentState)
    # ここは変えてもOK
    return graph
```

### 3. import を消す
```python
# ❌ ダメ
# from .._base.base_agent import BaseAgent  ← これを消す

# ✅ 正しい - 必要な import は残す
from .._base.base_agent import BaseAgent
```

</div>
</div>

---

## まとめ

<div class="summary-box">
<div class="box-title">📝 カスタマイズの鉄則</div>
<div class="box-content">

1. **まずは SYSTEM_PROMPT だけ触る** → 十分なカスタマイズが可能
2. **壊したら git checkout** → 元に戻せる
3. **大きな変更の前にコピー** → templates/_template/ からコピー

**→ 迷ったら [03_バックエンド解説.md](03_バックエンド解説.md) に戻ろう！**

</div>
</div>
