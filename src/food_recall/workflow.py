"""LangGraph 工作流定义"""

import os
import time
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

from .llm import init_llm, is_llm_initialized
from .config import init_from_env
from .state import AgentState
from .nodes import (
    extract_calorie,
    calculate_range,
    sql_recall,
    extract_demands,
    validate_batch,
    route_decision,
    generate_response,
)
from .nodes.timing import with_timing, with_timing_sync
from .logging_config import setup_logging, get_logger

setup_logging("food_recall")
logger = get_logger("food_recall")


def init_services():
    """初始化服务和配置"""
    config = init_from_env()
    if not is_llm_initialized():
        init_llm(
            provider=config.llm.provider,
            model=config.llm.model,
            base_url=config.llm.base_url,
            api_key=config.llm.api_key,
            temperature=config.llm.temperature,
        )


def create_workflow():
    """
    创建餐品推荐工作流

    流程：
    1. extract_calorie     - 提取热量约束
    2. calculate_range     - 计算弹性边界
    3. sql_recall          - SQL 召回候选套餐
    4. extract_demands     - 提取软需求
    5. validate_batch      - 并发核验所有候选
    6. route_decision      - 决策路由
    7. generate_response   - 生成最终响应
    """
    workflow = StateGraph(AgentState)

    timed_extract_calorie = with_timing_sync(extract_calorie)
    timed_calculate_range = with_timing_sync(calculate_range)
    timed_sql_recall = with_timing_sync(sql_recall)
    timed_extract_demands = with_timing_sync(extract_demands)
    timed_validate_batch = with_timing(validate_batch)
    timed_route_decision = with_timing_sync(route_decision)
    timed_generate_response = with_timing_sync(generate_response)

    # ===== 阶段一：粗排召回 =====
    workflow.add_node("extract_calorie", timed_extract_calorie)
    workflow.add_node("calculate_range", timed_calculate_range)
    workflow.add_node("sql_recall", timed_sql_recall)

    # ===== 阶段二：精排核验 =====
    workflow.add_node("extract_demands", timed_extract_demands)
    workflow.add_node("validate_batch", timed_validate_batch)

    # ===== 阶段三：决策生成 =====
    workflow.add_node("route_decision", timed_route_decision)
    workflow.add_node("generate_response", timed_generate_response)

    # ===== 设置入口点 =====
    workflow.set_entry_point("extract_calorie")

    # ===== 构建边（Edges）=====
    # 阶段一：热量提取 -> 边界计算 -> SQL 召回
    workflow.add_edge("extract_calorie", "calculate_range")
    workflow.add_edge("calculate_range", "sql_recall")

    # 阶段二：SQL 召回 -> 需求提取 -> 批量核验
    workflow.add_edge("sql_recall", "extract_demands")
    workflow.add_edge("extract_demands", "validate_batch")

    # 阶段三：批量核验 -> 路由决策 -> 生成响应 -> 结束
    workflow.add_edge("validate_batch", "route_decision")
    workflow.add_edge("route_decision", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow


def compile_workflow():
    """编译工作流为可执行图"""
    workflow = create_workflow()
    return workflow.compile()


# 全局编译后的工作流
_workflow = None


def get_workflow():
    """获取编译后的工作流（单例）"""
    global _workflow
    if _workflow is None:
        _workflow = compile_workflow()
    return _workflow


async def run_workflow(user_input: str) -> dict:
    """
    运行工作流

    Args:
        user_input: 用户输入

    Returns:
        最终状态，包含 final_response
    """
    workflow = get_workflow()

    initial_state: AgentState = {
        "user_input": user_input,
        "target_calorie": None,
        "calorie_range": None,
        "candidates": None,
        "demands": None,
        "validation_results": None,
        "route_decision": None,
        "perfect_matches": None,
        "partial_matches": None,
        "final_response": None,
        "timing": {},
    }

    total_start = time.time()
    result = await workflow.ainvoke(initial_state)
    total_elapsed = time.time() - total_start

    timing = result.get("timing", {})

    logger.info("=" * 50)
    logger.info("【耗时汇总】")
    logger.info("=" * 50)
    accounted_total = 0.0
    for node_name, elapsed in timing.items():
        logger.info(f"  {node_name}: {elapsed:.3f}s")
        accounted_total += elapsed
    logger.info("-" * 50)
    logger.info(f"  总耗时: {total_elapsed:.3f}s (内部计时: {accounted_total:.3f}s)")
    logger.info("=" * 50)

    return result


def run_workflow_sync(user_input: str) -> dict:
    """同步版本的工作流运行"""
    init_services()
    import asyncio
    return asyncio.run(run_workflow(user_input))


if __name__ == "__main__":
    # 测试运行
    test_input = "我想吃一份700大卡左右的减脂餐，我刚刚运动过，套餐带一个圣代，不要油炸物"
    result = run_workflow_sync(test_input)
    print(result.get("final_response", "无响应"))