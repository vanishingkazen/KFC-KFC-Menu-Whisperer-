"""LangGraph State 定义"""

from typing import TypedDict, List, Optional
from .models import (
    Combo,
    Demand,
    ComboValidation,
    CalorieRange,
)


class AgentState(TypedDict):
    """
    贯穿整个工作流的全局状态

    各阶段数据交换格式：
    """
    # ===== 原始输入 =====
    user_input: str

    # ===== 阶段一：粗排召回 =====
    target_calorie: Optional[int]          # 目标热量
    calorie_range: Optional[CalorieRange]  # 热量范围
    candidates: Optional[List[Combo]]      # SQL 召回的候选套餐 (≤60)

    # ===== 阶段二：精排核验 =====
    demands: Optional[List[Demand]]        # 软需求列表
    validation_results: Optional[List[ComboValidation]]  # 核验结果

    # ===== 阶段三：决策生成 =====
    route_decision: Optional[str]          # "perfect_match" | "fallback" | "no_match"
    perfect_matches: Optional[List[ComboValidation]]     # 满分套餐
    partial_matches: Optional[List[ComboValidation]]     # 部分匹配
    final_response: Optional[str]          # 最终响应


# ============== 各节点 Input/Output 定义 ==============
# Node              | Input (from State)           | Output (to State)
# ------------------+-------------------------------+---------------------------
# extract_calorie   | user_input                   | target_calorie
# calculate_range   | target_calorie               | calorie_range
# sql_recall        | calorie_range                | candidates
# extract_demands   | user_input                   | demands
# validate_batch    | candidates + demands         | validation_results
# route_decision    | validation_results           | route_decision + matches
# generate_response | route_decision + matches     | final_response