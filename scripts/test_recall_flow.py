"""完整检索流程测试脚本"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from food_recall.workflow import run_workflow_sync


def print_combo_details(combos, title="套餐详情"):
    """打印套餐详情"""
    if not combos:
        print(f"  无")
        return
    for i, combo in enumerate(combos, 1):
        print(f"  {i}. {combo.combo_name}")
        print(f"     匹配分数: {combo.score}/{combo.total_demands}")
        required = max(2, int(combo.total_demands * 0.5), 1)
        print(f"     进入fallback所需阈值: max(1, {combo.total_demands}*0.5, 2) = {required}")
        for vr in combo.results:
            status = "✅" if vr.match else "❌"
            print(f"     {status} {vr.demand}: {vr.reason}")
        if combo.unmet_reasons:
            print(f"     未满足原因: {', '.join(combo.unmet_reasons)}")
        print()


def test_recall_flow():
    print("=" * 70)
    print("【场景1】完美匹配 (perfect_match)")
    print("=" * 70)
    test_input = "我要一份带圣代的套餐，不要油炸物，要高蛋白"
    result = run_workflow_sync(test_input)

    print(f"输入: {test_input}")
    print(f"提取的需求: {[d.content for d in result.get('demands', [])]}")
    print(f"路由决策: {result.get('route_decision')}")
    print(f"完美匹配数: {len(result.get('perfect_matches', []))}")
    print(f"部分匹配数: {len(result.get('partial_matches', []))}")

    if result.get('perfect_matches'):
        print("\n完美匹配的套餐:")
        print_combo_details(result.get('perfect_matches'))

    print(f"\n最终响应:\n{result.get('final_response', '无响应')[:500]}")
    print()


    print("=" * 70)
    print("【场景2】fallback 测试 - 5条需求，满足2条 (2/5=40% < 50%阈值)")
    print("=" * 70)
    test_input = "我要一份带圣代的套餐，不要油炸物，要高蛋白，要低脂，要海鲜"
    result = run_workflow_sync(test_input)

    print(f"输入: {test_input}")
    print(f"提取的需求: {[d.content for d in result.get('demands', [])]}")
    print(f"路由决策: {result.get('route_decision')}")
    print(f"完美匹配数: {len(result.get('perfect_matches', []))}")
    print(f"部分匹配数: {len(result.get('partial_matches', []))}")
    print(f"无匹配数: {len(result.get('validation_results', [])) - len(result.get('perfect_matches', [])) - len(result.get('partial_matches', []))}")

    if result.get('partial_matches'):
        print("\n部分匹配的套餐:")
        print_combo_details(result.get('partial_matches')[:3])

    print(f"\n最终响应:\n{result.get('final_response', '无响应')[:500]}")
    print()


    print("=" * 70)
    print("【场景3】fallback 测试 - 3条需求，满足2条 (2/3=67% > 50%阈值)")
    print("=" * 70)
    test_input = "我要一份带圣代的套餐，不要油炸物，要高蛋白"
    result = run_workflow_sync(test_input)

    print(f"输入: {test_input}")
    print(f"提取的需求: {[d.content for d in result.get('demands', [])]}")
    print(f"路由决策: {result.get('route_decision')}")

    if result.get('partial_matches'):
        print("\n部分匹配的套餐:")
        print_combo_details(result.get('partial_matches')[:3])

    print(f"\n最终响应:\n{result.get('final_response', '无响应')[:500]}")


if __name__ == "__main__":
    test_recall_flow()