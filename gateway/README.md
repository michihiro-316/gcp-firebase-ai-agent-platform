# Gateway

マルチテナント環境で認証とルーティングを担う Gateway Cloud Functions です。

---

## 役割

```
ユーザー（ブラウザ）
      │
      │ Firebase Token
      ▼
┌─────────────────┐
│    Gateway      │ ← このコンポーネント
│  1. 認証検証    │
│  2. 顧客ID取得  │
│  3. 転送       │
└────────┬────────┘
         │ 内部ヘッダー + HMAC署名
         ▼
┌─────────────────┐
│ Backend API     │
│ (顧客別)        │
└─────────────────┘
```

---

## ファイル構成

```
gateway/
├── src/
│   ├── main.py            # Gateway本体
│   └── requirements.txt   # Python依存関係
├── .env.example           # 環境変数のサンプル
└── README.md              # このファイル
```

---

## セキュリティ

### HMAC署名による認証

Gateway と Backend 間の通信は HMAC-SHA256 署名で保護されています。

1. Gateway が `X-Gateway-Signature` ヘッダーを生成
2. Backend が署名を検証
3. 署名が一致しない場合はリクエストを拒否

**重要**: `GATEWAY_SECRET` 環境変数を Gateway と Backend で同じ値に設定してください。

---

## ローカル開発

```bash
cd gateway/src

# 依存関係インストール
pip install -r requirements.txt

# 起動
functions-framework --target=main --port=8081

# 別ターミナルでテスト
curl http://localhost:8081/health
```

---

## デプロイ

```bash
./infrastructure/deploy-gateway.sh
```

---

## 詳細ドキュメント

- [10_Gatewayアーキテクチャ.md](../learning/md/10_Gatewayアーキテクチャ.md)
