"""阶段二：精排核验层节点"""

import json
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..models import (
    Demand,
    Combo,
    ComboValidation,
    ValidationResult,
)
from ..prompts import get_prompt
from ..config import get_config
from ..llm import get_llm


def extract_demands(state: dict) -> dict:
    """
    Step 2.1: 提取软需求

    Input:  state["user_input"]
    Output: state["demands"]

    约束：显式忽略热量（已在阶段一处理），仅保留语义需求
    """
    user_input = state["user_input"]

    llm_client = get_llm()
    if llm_client is None:
        demands = _rule_based_demand_extraction(user_input)
        return {"demands": demands}

    prompt = get_prompt("extract_demands", user_input=user_input)
    response = llm_client.invoke(prompt)
    result = json.loads(response) if isinstance(response, str) else json.loads(response.content)
    demand_list = result.get("demand_list", [])
    demands = [Demand(demand_id=i, content=d) for i, d in enumerate(demand_list)]

    return {"demands": demands}


def _rule_based_demand_extraction(user_input: str) -> List[Demand]:
    """基于规则的简单需求提取（用于测试）"""
    demands = []

    # 检测是否需要圣代
    if "圣代" in user_input:
        demands.append(Demand(demand_id=len(demands), content="必须包含圣代"))

    # 检测是否不要油炸
    if "油炸" in user_input or "不要油炸" in user_input or "不含油炸" in user_input:
        demands.append(Demand(demand_id=len(demands), content="不能含有油炸类食物"))

    # 检测是否要减脂
    if "减脂" in user_input or "健身" in user_input or "运动" in user_input:
        demands.append(Demand(demand_id=len(demands), content="适合减脂"))

    # 检测是否要高蛋白
    if "高蛋白" in user_input:
        demands.append(Demand(demand_id=len(demands), content="高蛋白"))

    return demands


def validate_batch(state: dict) -> dict:
    """
    Step 2.2 - 2.4: 并发核验 + 汇总

    Input:  state["candidates"] + state["demands"]
    Output: state["validation_results"]

    机制：启动异步并发（协程/线程池），为每个候选套餐发起独立的核验任务
    """
    candidates = state.get("candidates", [])
    demands = state.get("demands", [])

    if not candidates or not demands:
        return {"validation_results": []}

    config = get_config()
    max_concurrency = config.validation.max_concurrency
    timeout_ms = config.validation.timeout_ms

    validation_results: List[ComboValidation] = []

    # 并发执行核验
    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        future_to_combo = {
            executor.submit(validate_single_combo, combo, demands): combo
            for combo in candidates
        }

        for future in as_completed(future_to_combo, timeout=timeout_ms/1000):
            try:
                result = future.result()
                validation_results.append(result)
            except Exception as e:
                # 单个套餐核验失败，记录日志但继续
                combo = future_to_combo[future]
                validation_results.append(ComboValidation(
                    combo_id=combo.combo_id,
                    combo_name=combo.combo_name,
                    score=0,
                    total_demands=len(demands),
                    results=[],
                    unmet_reasons=[f"核验失败: {str(e)}"]
                ))

    # 按分数排序
    validation_results.sort(key=lambda x: x.score, reverse=True)

    return {"validation_results": validation_results}


def validate_single_combo(combo: Combo, demands: List[Demand]) -> ComboValidation:
    """
    Step 2.3: 单个套餐的核验

    对每条需求进行布尔匹配，逐条判断是否满足

    Args:
        combo: 套餐信息
        demands: 需求列表

    Returns:
        套餐核验结果
    """
    results: List[ValidationResult] = []
    unmet_reasons: List[str] = []

    llm_client = get_llm()

    for demand in demands:
        if llm_client is not None:
            prompt = get_prompt(
                "validate_single",
                single_demand=demand.content,
                combo_name=combo.combo_name,
                items=",".join([item.name for item in combo.items]),
                tags=",".join(combo.tags)
            )
            response = llm_client.invoke(prompt)
            result = json.loads(response) if isinstance(response, str) else json.loads(response.content)
            match_result = {
                "match": bool(result.get("match", 0)),
                "reason": result.get("reason", "")
            }
        else:
            match_result = _rule_based_match(demand.content, combo)

        results.append(ValidationResult(
            demand_id=demand.demand_id,
            demand=demand.content,
            match=match_result["match"],
            reason=match_result["reason"]
        ))

        if not match_result["match"]:
            unmet_reasons.append(f"未满足: {demand.content}")

    score = sum(1 for r in results if r.match)

    return ComboValidation(
        combo_id=combo.combo_id,
        combo_name=combo.combo_name,
        score=score,
        total_demands=len(demands),
        results=results,
        unmet_reasons=unmet_reasons
    )


def _rule_based_match(demand: str, combo: Combo) -> dict:
    """基于规则的简单匹配（用于测试）"""
    items_str = " ".join([item.name for item in combo.items])
    tags_str = " ".join(combo.tags)

    # 圣代匹配
    if "圣代" in demand:
        return {
            "match": "圣代" in items_str,
            "reason": "套餐包含圣代" if "圣代" in items_str else "套餐不包含圣代"
        }

    # 油炸匹配
    if "油炸" in demand or "不含油炸" in demand or "不能含有油炸" in demand:
        is_fried = any(tag in tags_str or tag in items_str for tag in ["油炸", "炸", "煎"])
        return {
            "match": not is_fried,
            "reason": "非油炸" if not is_fried else "含有油炸食品"
        }

    # 减脂匹配
    if "减脂" in demand or "适合减脂" in demand:
        return {
            "match": "低脂" in tags_str or "健康" in tags_str or "非油炸" in tags_str,
            "reason": "适合减脂" if "低脂" in tags_str or "健康" in tags_str or "非油炸" in tags_str else "不适合减脂"
        }

    # 高蛋白匹配
    if "高蛋白" in demand:
        return {
            "match": "高蛋白" in tags_str,
            "reason": "高蛋白" if "高蛋白" in tags_str else "非高蛋白"
        }

    # 默认不匹配
    return {"match": False, "reason": "无法判断"}