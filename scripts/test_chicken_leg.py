"""测试鸡腿套餐问题"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from food_recall.workflow import run_workflow_sync

test_input = "我要一份带鸡腿的 700 大卡左右的套餐"
result = run_workflow_sync(test_input)

print("=" * 50)
print(f"输入: {test_input}")
print(f"目标热量: {result.get('target_calorie')}")
print(f"热量范围: {result.get('calorie_range')}")
print(f"提取的需求: {[d.content for d in result.get('demands', [])]}")
print(f"召回候选数: {len(result.get('candidates', []))}")
print(f"候选套餐: {[c.combo_name for c in result.get('candidates', [])]}")
print(f"路由决策: {result.get('route_decision')}")
print(f"完美匹配: {len(result.get('perfect_matches', []))}")
print(f"部分匹配: {len(result.get('partial_matches', []))}")

if result.get('partial_matches'):
    print("\n部分匹配详情:")
    for combo in result.get('partial_matches', [])[:3]:
        print(f"  {combo.combo_name}: {combo.score}/{combo.total_demands}")
        for vr in combo.results:
            status = "✅" if vr.match else "❌"
            print(f"    {status} {vr.demand}: {vr.reason}")

print()
print("最终响应:")
print(result.get('final_response', '无响应'))