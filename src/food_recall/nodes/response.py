"""阶段三：决策与生成节点"""

from typing import List, Optional
from ..models import ComboValidation
from ..prompts import get_prompt
from ..config import get_config
from ..llm import get_llm


def route_decision(state: dict) -> dict:
    """
    Step 3.1: 决策路由

    Input:  state["validation_results"]
    Output: state["route_decision"] + perfect_matches + partial_matches

    路由策略：
    1. perfect_match: 所有需求都满足
    2. fallback: 满足需求的比例 >= fallback_ratio 且绝对值 >= fallback_min_match
    3. no_match: 其他情况
    """
    validation_results = state.get("validation_results", [])

    if not validation_results:
        return {
            "route_decision": "no_match",
            "perfect_matches": [],
            "partial_matches": []
        }

    perfect_matches: List[ComboValidation] = []
    partial_matches: List[ComboValidation] = []
    no_matches: List[ComboValidation] = []

    config = get_config()
    fallback_ratio = config.routing.fallback_ratio
    fallback_min_match = config.routing.fallback_min_match
    fallback_threshold = config.routing.fallback_threshold

    for vr in validation_results:
        if vr.score == vr.total_demands and vr.total_demands > 0:
            perfect_matches.append(vr)
        elif vr.score > 0:
            effective_threshold = max(
                fallback_threshold,
                int(vr.total_demands * fallback_ratio),
                fallback_min_match
            )
            if vr.score >= effective_threshold:
                partial_matches.append(vr)
            else:
                no_matches.append(vr)
        else:
            no_matches.append(vr)

    if perfect_matches:
        route = "perfect_match"
    elif partial_matches:
        route = "fallback"
    else:
        route = "no_match"

    return {
        "route_decision": route,
        "perfect_matches": perfect_matches,
        "partial_matches": partial_matches
    }


def generate_response(state: dict) -> dict:
    """
    Step 3.2: 上下文装载与生成

    Input:  state["route_decision"] + matches + user_input
    Output: state["final_response"]

    三个分支：
    - perfect_match: 完美匹配分支
    - fallback: 妥协推荐分支
    - no_match: 无匹配兜底分支
    """
    route_decision = state.get("route_decision", "no_match")
    user_input = state.get("user_input", "")
    config = get_config()
    top_k = config.generation.top_k

    if route_decision == "perfect_match":
        return _generate_perfect_response(state, top_k)
    elif route_decision == "fallback":
        return _generate_fallback_response(state)
    else:
        return _generate_no_match_response(state)


def _generate_perfect_response(state: dict, top_k: int) -> dict:
    """分支 A: 完美匹配 - 直接选取满分套餐进行排序推荐"""
    perfect_matches = state.get("perfect_matches", [])
    user_input = state.get("user_input", "")

    if not perfect_matches:
        return {"final_response": "未找到完全匹配的套餐"}

    top_combos = perfect_matches[:top_k]
    combo_list = _format_combo_list(top_combos)

    llm_client = get_llm()
    if llm_client is not None:
        prompt = get_prompt(
            "generate_perfect",
            user_input=user_input,
            combo_list=combo_list
        )
        response = llm_client.invoke(prompt)
        return {"final_response": response}

    response_lines = [f"为您推荐以下套餐（按匹配度排序）：\n"]
    for i, combo in enumerate(top_combos, 1):
        items = ", ".join([item.name for item in combo.results[0].demand.split()]) if combo.results else ""
        response_lines.append(
            f"{i}. {combo.combo_name} (热量: {combo.score}/{combo.total_demands} 项需求匹配)"
        )
    response_lines.append(f"\n共为您找到 {len(perfect_matches)} 个完全匹配合适的套餐")

    return {"final_response": "\n".join(response_lines)}


def _generate_fallback_response(state: dict) -> dict:
    """分支 B: 妥协推荐 - 选取部分匹配的套餐，解释差异并询问用户"""
    partial_matches = state.get("partial_matches", [])
    candidates = state.get("candidates", [])
    user_input = state.get("user_input", "")

    if not partial_matches:
        return _generate_no_match_response(state)

    best_match = partial_matches[0]
    match_summary = _format_match_summary(best_match)

    combo_list = _format_combo_list(partial_matches[:5])

    llm_client = get_llm()
    if llm_client is not None:
        prompt = get_prompt(
            "generate_fallback",
            user_demands=user_input,
            match_summary=match_summary,
            combo_list=combo_list
        )
        response = llm_client.invoke(prompt)
        return {"final_response": response}

    satisfied = [r.demand for r in best_match.results if r.match]
    unsatisfied = best_match.unmet_reasons

    response_parts = ["抱歉，完全符合您需求的套餐暂时没有找到。\n"]
    if satisfied:
        response_parts.append(f"以下需求已满足：{', '.join(satisfied)}")
    if unsatisfied:
        response_parts.append(f"以下需求暂未满足：{', '.join(unsatisfied)}")
    response_parts.append(f"\n为您推荐：{best_match.combo_name}")
    response_parts.append("您看这个替代方案可以接受吗？")

    return {"final_response": "\n".join(response_parts)}


def _generate_no_match_response(state: dict) -> dict:
    """分支 C: 无匹配 - 诚恳告知用户无法匹配，并提供调整建议"""
    user_input = state.get("user_input", "")
    candidates = state.get("candidates", [])

    combo_list_lines = []
    for combo in candidates[:5]:
        items_str = ", ".join([item.name if hasattr(item, 'name') else str(item) for item in combo.items])
        combo_list_lines.append(f"- {combo.combo_name} (单品: {items_str})")
    combo_list = "\n".join(combo_list_lines) if combo_list_lines else "暂无候选套餐"

    llm_client = get_llm()
    if llm_client is not None:
        prompt = get_prompt(
            "generate_no_match",
            user_input=user_input,
            combo_list=combo_list
        )
        response = llm_client.invoke(prompt)
        return {"final_response": response}

    response = f"""抱歉，根据您的需求：
"{user_input}"

目前暂时没有匹配的套餐。

建议您：
1. 适当放宽热量范围
2. 考虑接受替代品（如冰淇淋替代圣代）
3. 查看其他套餐

您想如何调整需求？"""

    return {"final_response": response}


def _format_combo_list(combos: List[ComboValidation]) -> str:
    """格式化套餐列表为字符串"""
    lines = []
    for combo in combos:
        lines.append(
            f"- {combo.combo_name}: {combo.combo_name}, "
            f"匹配 {combo.score}/{combo.total_demands} 项需求"
        )
    return "\n".join(lines)


def _format_match_summary(combo: ComboValidation) -> str:
    """格式化匹配摘要"""
    satisfied = [r.demand for r in combo.results if r.match]
    unsatisfied = combo.unmet_reasons

    parts = []
    if satisfied:
        parts.append(f"满足：{', '.join(satisfied)}")
    if unsatisfied:
        parts.append(f"不满足：{', '.join(unsatisfied)}")

    return "; ".join(parts)