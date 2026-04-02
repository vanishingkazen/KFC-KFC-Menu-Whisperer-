"""工作流测试"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from food_recall.workflow import run_workflow_sync


def test_basic_workflow():
    """测试基本工作流"""
    test_input = "我想吃一份700大卡左右的减脂餐，我刚刚运动过，套餐带一个圣代，不要油炸物"

    result = run_workflow_sync(test_input)

    # 验证返回结果
    assert "final_response" in result
    assert result["final_response"] is not None
    assert len(result["final_response"]) > 0

    print(f"\n{'='*50}")
    print(f"输入: {test_input}")
    print(f"{'='*50}")
    print(f"输出:\n{result['final_response']}")
    print(f"{'='*50}")


def test_no_calorie_constraint():
    """测试无热量约束"""
    test_input = "我要一个带圣代的套餐，不要油炸物"

    result = run_workflow_sync(test_input)

    assert "final_response" in result
    print(f"\n{'='*50}")
    print(f"输入: {test_input}")
    print(f"{'='*50}")
    print(f"输出:\n{result['final_response']}")
    print(f"{'='*50}")


if __name__ == "__main__":
    test_basic_workflow()
    test_no_calorie_constraint()