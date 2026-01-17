# 開発用ツール

ローカル開発・検証用のツール集です。
**本番環境では使用しないでください。**

---

## モックAPIサーバー

GCP/Firebase接続なしでフロントエンドの動作確認ができます。

### 起動方法

```bash
cd backend/dev
pip install flask flask-cors  # 初回のみ
python mock_server.py
```

### 本番との違い

| 項目 | 本番 | モック |
|------|------|--------|
| 認証 | Firebase Auth必須 | なし（誰でもアクセス可） |
| AI | Vertex AI (Gemini) | 固定レスポンス or エコー |
| DB | Firestore | なし（履歴保存なし） |
| 課金 | あり | なし |

### フロントエンドとの接続

1. `frontend/.env` を編集:

```env
VITE_API_URL=http://localhost:8080
VITE_DEBUG_MODE=true
```

2. フロントエンド起動:

```bash
cd frontend
npm run dev
```

3. ブラウザで http://localhost:5173 を開く
   - 認証スキップでチャット画面が表示されます

### エージェント種類

| エージェント | 動作 | 用途 |
|-------------|------|------|
| `sample` | 固定レスポンスを返す | 基本動作確認 |
| `echo` | 入力をそのまま返す | 入出力確認 |
| `slow` | 遅延付きで返す | ストリーミング表示確認 |

### APIエンドポイント

```
GET  /health      # ヘルスチェック
POST /chat        # チャット（ストリーミング）
POST /chat/sync   # チャット（同期）
GET  /agents      # エージェント一覧
```

### テスト例

```bash
# ヘルスチェック
curl http://localhost:8080/health

# チャット（同期）
curl -X POST http://localhost:8080/chat/sync \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは"}'

# エコーエージェント
curl -X POST http://localhost:8080/chat/sync \
  -H "Content-Type: application/json" \
  -d '{"message": "テスト", "agent": "echo"}'
```

---

## 使用シーン

### 1. フロントエンドのUI修正

```
モックサーバー起動 → フロント起動 → 画面確認 → 修正 → 確認
```

GCP課金なし、即座に確認可能。

### 2. チャットレンダラーの開発

```
1. モックサーバー起動
2. mock_server.py の MOCK_RESPONSES を編集
3. 表形式データなど特殊なレスポンスをテスト
```

### 3. ストリーミング表示の確認

```bash
curl -N http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "agent": "slow"}'
```

---

## 注意事項

- このディレクトリのコードは**本番に一切影響しません**
- 認証がないため、インターネット公開しないでください
- 会話履歴は保存されません（サーバー再起動でリセット）
