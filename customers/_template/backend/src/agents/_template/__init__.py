# エージェントテンプレート
#
# 【顧客別エージェントの作り方】
# 1. このフォルダをコピー: cp -r _template {customer_id}
# 2. agent.py の SYSTEM_PROMPT を編集
# 3. main.py に登録
#
# 詳細は agents/README.md を参照
from .agent import TemplateAgent

__all__ = ["TemplateAgent"]
