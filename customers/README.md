# 顧客ディレクトリ

顧客ごとのフロントエンドとバックエンドを管理します。

---

## 構成

```
customers/
├── _template/          # 新規顧客用テンプレート
│   ├── frontend/
│   └── backend/
│
├── acme-corp/          # 顧客A（例）
│   ├── frontend/
│   └── backend/
│
└── customer-b/         # 顧客B（例）
    ├── frontend/
    └── backend/
```

---

## 新規顧客の追加手順

```bash
# 1. テンプレートをコピー
cp -r customers/_template customers/{customer_id}

# 2. Firestore に顧客を登録
python backend/scripts/manage_customer.py add {customer_id} "顧客名"

# 3. 顧客用にカスタマイズ（AI プロンプトなど）
vim customers/{customer_id}/backend/src/agents/_template/agent.py

# 4. デプロイ
./infrastructure/deploy-customer.sh {customer_id}
```

---

## 注意事項

- `_template/` は直接編集しないでください
- 顧客ディレクトリ名は英数字とハイフンのみ使用可能
- 各顧客は独立した Cloud Run としてデプロイされます
