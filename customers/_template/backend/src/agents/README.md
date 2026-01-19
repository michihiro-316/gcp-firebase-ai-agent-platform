# AIエージェント

顧客ごとに異なるAIエージェントを作成・管理します。

---

## ディレクトリ構成

```
agents/
├── _base/           ← 共通基盤（触らない）
│   ├── base_agent.py
│   └── firestore_checkpointer.py
├── _template/       ← コピー元テンプレート
│   ├── agent.py     ← ここを編集
│   └── state.py
└── {customer_id}/   ← 顧客別エージェント
    ├── agent.py
    └── state.py
```

---

## 顧客別エージェントの作り方

### 1. テンプレートをコピー

```bash
cd backend/src/agents
cp -r _template acme-corp
```

### 2. agent.py を編集

```python
# agents/acme-corp/agent.py

class AcmeCorpAgent(BaseAgent):

    # ここを変更するとAIの性格が変わる
    SYSTEM_PROMPT = """あなたはACME社の専門AIです。
製品に関する質問に答えてください。"""
```

### 3. main.py に登録

```python
# main.py

from agents.acme_corp.agent import AcmeCorpAgent

AGENTS = {
    "template": TemplateAgent,
    "acme-corp": AcmeCorpAgent,  # 追加
}
```

### 4. 設定ファイルを作成

```bash
cp customer-configs/template.env customer-configs/acme-corp.env
```

```env
# customer-configs/acme-corp.env
CUSTOMER_ID=acme-corp
DEFAULT_AGENT=acme-corp
```

### 5. デプロイ

```bash
./infrastructure/deploy-customer.sh acme-corp
```

---

## カスタマイズ例

### AIの性格を変える

```python
SYSTEM_PROMPT = """あなたは関西弁で話すAIです。
ユーザーの質問にフレンドリーに答えてください。"""
```

### モデルを変える

```python
MODEL_NAME = "gemini-1.5-pro"  # より高性能なモデル
```

### 会話履歴を増やす

```python
MAX_HISTORY_MESSAGES = 40  # 約20往復分
```

---

## 注意事項

- `_base/` は触らない（共通基盤）
- `_template/` は直接編集しない（コピーして使う）
- 顧客IDとフォルダ名は一致させる
