# 顧客追加ガイド

新しい顧客を追加する手順です。

---

## 手順

### 1. 顧客を登録

```bash
cd backend
python scripts/manage_customer.py add <顧客ID> "<顧客名>"

# 例
python scripts/manage_customer.py add acme-corp "株式会社ACME"
```

### 2. ユーザーを顧客に紐付け

ユーザーが先にGoogleログインしている必要があります。

```bash
python scripts/manage_customer.py add-user <顧客ID> <メールアドレス>

# 例
python scripts/manage_customer.py add-user acme-corp yamada@acme.co.jp
```

### 3. 確認

```bash
# 顧客一覧
python scripts/manage_customer.py list

# 顧客詳細
python scripts/manage_customer.py show acme-corp

# ユーザー詳細
python scripts/manage_customer.py show-user yamada@acme.co.jp
```

---

## 注意事項

- ユーザーは紐付け後、**再ログイン**が必要です
- 顧客IDは英数字とハイフンのみ使用してください
- 1ユーザーは1顧客にのみ所属できます

---

## Firestoreのデータ構造

```
customers/
  {customer_id}/
    name: "株式会社ACME"
    created_at: ...
    checkpoints/
      {thread_id}/
        checkpoints/
          {checkpoint_id}: {...}

users/
  {uid}/
    email: "yamada@acme.co.jp"
    customer_id: "acme-corp"
```

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| ユーザーが見つからない | 未ログイン | ユーザーに先にログインしてもらう |
| 古い顧客データが見える | 再ログインしていない | ユーザーに再ログインしてもらう |
| 権限エラー | Custom Claims未反映 | 最大1分待って再試行 |
