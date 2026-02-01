# Backend（バックエンド）

AIエージェントのAPIサーバーです。

## フォルダ構成

```
backend/
├── main.py              # エントリーポイント（Cloud Functionsで実行される）
├── requirements.txt     # Pythonの依存関係
├── agents/              # AIエージェント
│   ├── _base/           # 共通の基底クラス
│   └── _template/       # テンプレートエージェント（ここを編集）
└── common/              # 共通モジュール（認証、CORS等）
```

## Cloud Functionsへのデプロイ方法

### 方法1: コピペでデプロイ（初心者向け）

1. このフォルダ（`backend/`）をそのままCloud Functionsにアップロード
2. GCPコンソールで以下を設定：
   - ランタイム: Python 3.11
   - エントリーポイント: `main`
   - トリガー: HTTP

### 方法2: gcloudコマンドでデプロイ

```bash
# このフォルダに移動
cd backend

# デプロイ実行
gcloud functions deploy my-chat-api \
    --gen2 \
    --runtime=python311 \
    --region=asia-northeast1 \
    --source=. \
    --entry-point=main \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars="CUSTOMER_ID=default,GOOGLE_CLOUD_PROJECT=your-project-id" \
    --memory=512MB \
    --timeout=300s
```

### 方法3: シェルスクリプトでデプロイ

```bash
# プロジェクトルートから実行
./infrastructure/deploy.sh
```

## ローカルでの実行方法

```bash
# このフォルダに移動
cd backend

# 仮想環境を作成（初回のみ）
python -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# 実行
python -m functions_framework --target=main --port=8080 --debug
```

## AIエージェントの編集

`agents/_template/agent.py` を編集してAIの動作をカスタマイズできます。

```python
# agents/_template/agent.py

# システムプロンプトを変更
SYSTEM_PROMPT = """
あなたは親切なAIアシスタントです。
"""
```
