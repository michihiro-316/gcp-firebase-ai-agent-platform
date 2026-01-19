# AIエージェントパッケージ
#
# 【ディレクトリ構成】
#
#   agents/
#   ├── _base/           ← 共通基盤（触らない）
#   ├── _template/       ← コピー元テンプレート
#   └── {customer_id}/   ← 顧客別エージェント（ここを作成）
#
# 【顧客別エージェントの作り方】
# 1. _template をコピー
#    cp -r _template acme-corp
#
# 2. agent.py の SYSTEM_PROMPT を編集
#
# 3. main.py の AGENTS に登録
#    from agents.acme_corp import AcmeCorpAgent
#    AGENTS = {"acme-corp": AcmeCorpAgent, ...}
#
# 4. customer-configs/acme-corp.env を作成
#    DEFAULT_AGENT=acme-corp
