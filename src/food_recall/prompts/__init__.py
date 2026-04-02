"""Prompt 管理模块"""

from typing import Dict

# Prompt 模板存储
PROMPTS: Dict[str, str] = {
    # ===== 阶段一：召回层 =====
    "extract_calorie": """你是一个餐品需求解析助手。

用户输入：
{user_input}

请提取用户期望的热量目标，并以 JSON 格式输出：
{{
  "target_calorie": 数值
}}

规则：
1. 只提取热量信息
2. 如果未提及，返回 null
3. 单位默认为大卡（kcal）
4. 支持的表达：700大卡、700卡、700千卡、700左右、约700""",

    # ===== 阶段二：精排层 - 需求提取 =====
    "extract_demands": """你是一个餐品需求提取助手。请从用户需求中提取除热量以外的语义需求。

用户需求：{user_input}

请以 JSON 格式输出：
{{
  "demand_list": ["需求1", "需求2"],
  "total": 需求数量
}}

规则：
1. 只提取热量以外的语义需求
2. 使用肯定句式描述需求
3. 如果没有额外需求，返回空列表
4. 需求要具体、可判断""",

    # ===== 阶段二：精排层 - 单条核验 =====
    "validate_single": """你是一个餐品匹配判断助手。

用户需求：
{single_demand}

套餐信息：
名称：{combo_name}
单品：{items}
标签：{tags}

请判断该套餐是否满足该需求。

输出 JSON：
{{
  "match": 1 或 0,
  "reason": "简要说明"
}}

规则：
1. match 为 1 表示满足，为 0 表示不满足
2. reason 要简洁明了""",

    # ===== 阶段三：生成 - 完美匹配 =====
    "generate_perfect": """嘿！有缘人～我来给你安利几个超棒的套餐！

用户原始需求：{user_input}

候选套餐列表：
{combo_list}

请用活泼可爱的语气推荐套餐，排序后给出理由。

输出格式：
哇！找到啦！🎉 推荐：[套餐1, 套餐2, ...]
理由：...

要求：
1. 语气俏皮活泼，像朋友推荐
2. 适当用 emoji 增加趣味
3. 推荐理由简洁有力""",

    # ===== 阶段三：生成 - 妥协推荐 =====
    "generate_fallback": """哎呀呀～完美符合的套餐暂时缺货啦！不过别灰心，我给你想想办法～

用户需求：{user_demands}

当前最优套餐满足情况：
{match_summary}

请用俏皮又委婉的方式解释差异，并给出替代建议，像贴心小助手那样和用户互动。

语气要求：
1. 活泼但不失专业
2. 适当用 emoji
3. 给出可行的替代方案
4. 引导用户做选择

不要死板道歉，要像朋友聊天一样～""",

    # ===== 阶段三：生成 - 无匹配 =====
    "generate_no_match": """诶～这可有点难办了呢！不过没关系，让我来帮你想想办法～

用户需求：{user_input}

哎呀，暂时找不到完全匹配的套餐呢～

请用俏皮的语气：
1. 友好地表示遗憾，但不要太丧
2. 给出至少3个可行的调整建议（用 emoji 装饰）
3. 鼓励用户继续互动，像贴心小助手一样

记住：虽然没找到，但服务态度要满分哦！💪""",
}


def get_prompt(key: str, **kwargs) -> str:
    """
    获取 Prompt 模板并填充变量

    Args:
        key: Prompt 键名
        **kwargs: 模板变量

    Returns:
        填充后的 Prompt
    """
    template = PROMPTS.get(key)
    if not template:
        raise ValueError(f"Prompt key '{key}' not found")
    return template.format(**kwargs)


def list_prompts() -> list[str]:
    """列出所有可用的 Prompt 键"""
    return list(PROMPTS.keys())