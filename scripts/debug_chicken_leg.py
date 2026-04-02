"""深入调试鸡腿套餐问题"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from food_recall.workflow import run_workflow_sync
from food_recall.nodes.validation import validate_single_combo
from food_recall.models import Combo, ComboItem

test_input = "我要一份带鸡腿的 700 大卡左右的套餐"

result = run_workflow_sync(test_input)

print("=" * 60)
print(f"输入: {test_input}")
print()

print("【召回阶段】")
print(f"热量范围: {result.get('calorie_range')}")
print(f"召回候选: {[c.combo_name for c in result.get('candidates', [])]}")
print()

print("【需求提取】")
demands = result.get('demands', [])
for d in demands:
    print(f"  demand_id={d.demand_id}, content={d.content}")
print()

print("【核验结果】")
validation_results = result.get('validation_results', [])
for vr in validation_results:
    print(f"  {vr.combo_name}: score={vr.score}/{vr.total_demands}")
    for r in vr.results:
        status = "✅" if r.match else "❌"
        print(f"    {status} demand_id={r.demand_id}: {r.demand}")
        print(f"       reason: {r.reason}")
print()

print("【路由决策】")
print(f"route_decision: {result.get('route_decision')}")
print(f"完美匹配: {[pm.combo_name for pm in result.get('perfect_matches', [])]}")
print(f"部分匹配: {[pm.combo_name for pm in result.get('partial_matches', [])]}")
print()

print("【直接测试核验函数】")
from food_recall.models import Demand
test_demand = Demand(demand_id=0, content="套餐包含鸡腿")

combo = Combo(
    combo_id=102,
    combo_name="烤鸡腿套餐",
    items=[ComboItem(name="烤鸡腿"), ComboItem(name="蔬菜沙拉"), ComboItem(name="冰淇淋")],
    tags=["高蛋白", "非油炸"],
    calories=720,
    sales_volume=980
)

vr = validate_single_combo(combo, [test_demand])
print(f"套餐: {combo.combo_name}")
print(f"单品: {[i.name for i in combo.items]}")
print(f"需求: {test_demand.content}")
print(f"核验结果: score={vr.score}/{vr.total_demands}")
for r in vr.results:
    print(f"  match={r.match}, demand={r.demand}, reason={r.reason}")