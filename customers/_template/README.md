# 顧客テンプレート

新しい顧客を追加する際のテンプレートです。

---

## 使い方

```bash
# 1. テンプレートをコピー
cp -r customers/_template customers/acme-corp

# 2. 顧客名でディレクトリを作成済み
cd customers/acme-corp

# 3. バックエンドをカスタマイズ
#    backend/src/agents/_template/agent.py の SYSTEM_PROMPT を編集

# 4. デプロイ
./infrastructure/deploy-customer.sh acme-corp
```

---

## ディレクトリ構成

```
_template/
├── frontend/           # フロントエンド（React）
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── hooks/
│   │   └── renderers/  # 表示カスタマイズ
│   └── package.json
│
├── backend/            # バックエンド（Python/Flask）
│   ├── src/
│   │   ├── main.py
│   │   ├── agents/     # AI エージェント
│   │   └── common/     # 共通モジュール
│   └── requirements.txt
│
└── README.md           # このファイル
```

---

## カスタマイズポイント

| 対象 | ファイル | 説明 |
|------|----------|------|
| AI の応答 | `backend/src/agents/_template/agent.py` | SYSTEM_PROMPT を編集 |
| UI テーマ | `frontend/src/App.tsx` | CSS を編集 |
| チャット表示 | `frontend/src/renderers/` | レンダラーを追加 |
