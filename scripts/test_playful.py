"""测试俏皮回复"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from food_recall.workflow import run_workflow_sync

test_input = "我要一份带鸡腿的 700 大卡左右的套餐"
result = run_workflow_sync(test_input)

print("=" * 60)
print(f"输入: {test_input}")
print(f"路由决策: {result.get('route_decision')}")
print()
print("最终响应:")
print(result.get('final_response', '无响应'))