# Gateway アーキテクチャ解説

## 概要

本プラットフォームは「Gateway + Company Cloud Functions」構成を採用しています。

```
   ユーザー（ブラウザ）
        │
        │ HTTPS + Firebase Token
        ▼
┌─────────────────────────────────────────┐
│     Gateway Cloud Functions（1つ）       │
│                                         │
│  やること（3つだけ）:                     │
│  1. Firebase 認証チェック                │
│  2. customer_id から URL を取得          │
│  3. そのまま転送（プロキシ）              │
│                                         │
└────────────────┬────────────────────────┘
                 │
                 │ そのまま転送
                 ▼
┌─────────────────────────────────────────┐
│   Company Cloud Functions（会社ごと）    │
│                                         │
│  バックエンド API + AI Agent             │
│  → 既存の backend/src/main.py           │
│                                         │
└─────────────────────────────────────────┘
```

---

## なぜこの設計か

### 既存の問題点

- Cloud Functions は各社ごとにデプロイ → OK、そのまま維持
- でもフロントエンドは GCS で共有 → そのまま維持（今回は変更しない）
- 認証が各 Cloud Functions で分散 → Gateway で一元化

### この設計の良い点

- **Gateway は「認証して転送するだけ」** → シンプル
- **既存の Cloud Functions を変更しない** → 移行リスク最小
- **既存コードをほぼそのまま使える** → 学習コスト低い
- **Docker 不使用** → 既存のデプロイ方式を維持

### 受託・長期運用に向いている理由

- 顧客ごとにコードをフォークできる
- 1社だけ特殊なカスタマイズも可能
- 他社への影響ゼロ
- 新人エンジニアでも理解しやすい

---

## Gateway の責務

Gateway は以下の3つだけを行います:

### 1. Firebase 認証チェック

```python
def verify_request():
    """Firebase トークンを検証して uid, customer_id を返す"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = auth.verify_id_token(token, check_revoked=True)
    uid = decoded["uid"]

    # Custom Claims から customer_id を取得
    user = auth.get_user(uid)
    customer_id = (user.custom_claims or {}).get("customer_id")

    return uid, customer_id
```

### 2. customer_id から URL を取得

```python
def get_company_url(customer_id: str) -> str:
    """Firestore から転送先 URL を取得"""
    doc = db.collection("customers").document(customer_id).get()
    if doc.exists:
        return doc.to_dict().get("cloud_functions_url")
    return None
```

### 3. リクエストをそのまま転送

```python
# リクエストを転送（ストリーミング対応）
resp = requests.request(
    method=request.method,
    url=target_url,
    headers={
        "X-Gateway-Verified": "true",
        "X-User-Id": uid,
        "X-Customer-Id": customer_id,
    },
    data=request.get_data(),
    stream=True,  # SSE 対応
    timeout=300,
)
```

---

## Gateway がやらないこと（重要）

- AI 処理
- ビジネスロジック
- UI ロジック
- データベース操作（顧客 URL 取得以外）

これらはすべて Company Cloud Functions で行います。

---

## Company Cloud Functions の変更点

Gateway 経由のリクエストを受け付けるため、以下の認証関数が追加されています:

```python
def authenticate_request_with_gateway(request) -> dict:
    """Gateway 経由のリクエストを認証"""

    # Gateway 経由かどうかを確認
    gateway_verified = request.headers.get("X-Gateway-Verified")

    if gateway_verified == "true":
        # Gateway が認証済みなので、内部ヘッダーを信頼
        user_id = request.headers.get("X-User-Id")
        customer_id = request.headers.get("X-Customer-Id")
        return {
            "uid": user_id,
            "customer_id": customer_id,
        }

    # Gateway 経由でない場合は従来の認証
    return authenticate_request(request)
```

---

## Firestore スキーマ

Gateway が顧客の Cloud Functions URL を取得するため、以下のフィールドが必要です:

```
customers/{customer_id}
├── name: "ACME Corporation"
├── allowed_emails: ["user@acme.co.jp", ...]
├── allowed_domains: ["acme.co.jp"]
├── cloud_functions_url: "https://xxx.cloudfunctions.net/{customer_id}-api"  ← 追加
├── enabled: true  ← 追加
└── created_at: timestamp
```

---

## デプロイ方法

### Gateway のデプロイ

```bash
export PROJECT_ID=your-project-id
./infrastructure/deploy-gateway.sh
```

### Company Cloud Functions のデプロイ

```bash
export PROJECT_ID=your-project-id
./infrastructure/deploy-customer.sh customer-a
```

---

## 移行の流れ

### Phase 1: Gateway の追加（既存を壊さない）

1. `gateway/src/main.py` を作成（済み）
2. Gateway Cloud Functions をデプロイ
3. 動作確認（既存の構成と並行稼働）

### Phase 2: フロントエンドの接続先変更

1. フロントエンドの `VITE_API_BASE_URL` を Gateway に変更
2. 動作確認

### Phase 3: 既存 Cloud Functions の調整（オプション）

1. Gateway からの内部ヘッダー対応を追加（済み）
2. 直接アクセスを段階的に制限（必要に応じて）

**重要**: Phase 1 だけで動作するので、段階的に進められます。

---

## ディレクトリ構造

```
gcp-firebase-ai-agent-platform/
│
├── gateway/                          # Gateway Cloud Functions
│   └── src/
│       ├── main.py                   # Gateway 本体（約100行）
│       └── requirements.txt          # 依存関係
│
├── backend/                          # Company Cloud Functions（既存）
│   └── src/
│       ├── main.py                   # バックエンド本体
│       ├── agents/                   # AI エージェント
│       └── common/                   # 共通モジュール
│
├── frontend/                         # フロントエンド（既存）
│
└── infrastructure/
    ├── deploy-gateway.sh             # Gateway デプロイ
    └── deploy-customer.sh            # Company デプロイ（既存）
```

---

## セキュリティ

### 認証フロー

1. フロントエンドが Firebase Token を取得
2. Gateway が Token を検証し、customer_id を取得
3. Gateway が内部ヘッダー（`X-Gateway-Verified`, `X-User-Id`, `X-Customer-Id`）を付与
4. Company Cloud Functions が内部ヘッダーを信頼

### Backend への直接アクセス防止（Cloud Run IAM）

**重要**: Backend への直接アクセスを防ぐため、Cloud Run IAM で Gateway のみアクセス可能に設定することを推奨します。

```bash
# Backend を非公開に設定
gcloud run services update backend \
  --no-allow-unauthenticated \
  --region=asia-northeast1

# Gateway のサービスアカウントに Backend へのアクセス権を付与
gcloud run services add-iam-policy-binding backend \
  --member="serviceAccount:gateway@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=asia-northeast1
```

これにより、インターネットから直接 Backend にアクセスできなくなり、`X-Gateway-Verified` ヘッダーの偽装を防止できます。

### 直接アクセスの場合

Gateway を経由しない場合でも、Company Cloud Functions は従来通り Firebase Token を検証します。

```python
if gateway_verified == "true":
    # Gateway 経由 → 内部ヘッダーを信頼
    return {"uid": user_id, "customer_id": customer_id}
else:
    # 従来の認証
    return authenticate_request(request)
```

---

## トラブルシューティング

### Gateway のヘルスチェック

```bash
curl https://gateway-xxx.cloudfunctions.net/health
# → {"status": "healthy", "service": "gateway"}
```

### 認証エラー

- `401`: Firebase Token が無効
- `403`: customer_id が未設定
- `404`: customers コレクションに cloud_functions_url が未設定

### SSE が途切れる

Gateway のタイムアウトは 300 秒に設定されています。それ以上かかる場合は調整が必要です。
