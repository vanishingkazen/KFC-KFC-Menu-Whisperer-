"""阶段一：粗排召回层节点"""

import json
import re
import sqlite3
import os
from typing import Optional
from ..models import CalorieExtraction, CalorieRange, Combo, ComboItem
from ..prompts import get_prompt
from ..config import get_config
from ..llm import get_llm

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DB_PATH = os.path.join(_project_root, "food_recall.db")


def _get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def extract_calorie(state: dict) -> dict:
    """
    Step 1.1: 提取热量约束

    Input:  state["user_input"]
    Output: state["target_calorie"]

    使用 LLM 读取输入，提取热量信息
    """
    user_input = state["user_input"]

    llm_client = get_llm()
    if llm_client is None:
        calorie_match = re.search(r'(\d+)\s*(?:大卡|卡|千卡|kcal|kcal)?', user_input)
        if calorie_match:
            target_calorie = int(calorie_match.group(1))
            return {"target_calorie": target_calorie}
        return {"target_calorie": None}

    prompt = get_prompt("extract_calorie", user_input=user_input)
    response = llm_client.invoke(prompt)
    result = json.loads(response) if isinstance(response, str) else json.loads(response.content)
    target_calorie = result.get("target_calorie")
    if target_calorie is not None:
        target_calorie = int(target_calorie)
    return {"target_calorie": target_calorie}


def calculate_range(state: dict) -> dict:
    """
    Step 1.2: 计算弹性边界

    Input:  state["target_calorie"]
    Output: state["calorie_range"]

    设计原则：减脂场景允许"低于目标"，但需严格控制"超标"
    - lower_bound = target - 150
    - upper_bound = target + 100
    """
    target_calorie = state.get("target_calorie")

    if target_calorie is None:
        # 没有热量约束，返回一个宽松的范围
        return {
            "calorie_range": CalorieRange(lower_bound=0, upper_bound=2000)
        }

    config = get_config()
    lower_expand = config.recall.lower_expand
    upper_expand = config.recall.upper_expand

    return {
        "calorie_range": CalorieRange(
            lower_bound=target_calorie - lower_expand,
            upper_bound=target_calorie + upper_expand
        )
    }


def sql_recall(state: dict) -> dict:
    """
    Step 1.3: SQL 召回与截断

    Input:  state["calorie_range"]
    Output: state["candidates"]

    SQL:
        SELECT combo_id, combo_name, items, tags, calories
        FROM combos
        WHERE calories >= :lower_bound
          AND calories <= :upper_bound
          AND status = 'on_shelf'
        ORDER BY sales_volume DESC
        LIMIT 60;
    """
    calorie_range = state.get("calorie_range")

    if calorie_range is None:
        return {"candidates": []}

    config = get_config()
    max_candidates = config.recall.max_candidates

    if not os.path.exists(DB_PATH):
        mock_candidates = _generate_mock_candidates(calorie_range, max_candidates)
        return {"candidates": mock_candidates}

    try:
        conn = _get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT combo_id, combo_name, items, tags, calories, sales_volume
            FROM combos
            WHERE calories >= ? AND calories <= ? AND status = 'on_shelf'
            ORDER BY sales_volume DESC
            LIMIT ?
        """, (calorie_range.lower_bound, calorie_range.upper_bound, max_candidates))

        rows = cursor.fetchall()
        conn.close()

        candidates = []
        for row in rows:
            items_str = row["items"] if isinstance(row["items"], str) else ""
            items_list = [item.strip() for item in items_str.split(",") if item.strip()]
            tags_str = row["tags"] if isinstance(row["tags"], str) else ""
            tags_list = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

            candidates.append(Combo(
                combo_id=row["combo_id"],
                combo_name=row["combo_name"],
                items=[ComboItem(name=i) for i in items_list],
                tags=tags_list,
                calories=row["calories"],
                sales_volume=row["sales_volume"]
            ))

        return {"candidates": candidates}

    except Exception as e:
        import logging
        logging.getLogger("food_recall").error(f"数据库查询失败: {str(e)}")
        mock_candidates = _generate_mock_candidates(calorie_range, max_candidates)
        return {"candidates": mock_candidates}


def _generate_mock_candidates(calorie_range: CalorieRange, limit: int) -> list[Combo]:
    """生成模拟候选套餐（用于测试）"""
    mock_data = [
        {"combo_id": 101, "combo_name": "香煎鸡胸肉套餐", "items": ["煎鸡胸", "水煮西兰花", "原味圣代"], "tags": ["高蛋白", "非油炸"], "calories": 680, "sales_volume": 1000},
        {"combo_id": 102, "combo_name": "烤鸡腿套餐", "items": ["烤鸡腿", "蔬菜沙拉", "冰淇淋"], "tags": ["高蛋白", "非油炸"], "calories": 720, "sales_volume": 800},
        {"combo_id": 103, "combo_name": "油炸鸡块套餐", "items": ["炸鸡块", "薯条", "可乐"], "tags": ["油炸", "高热量"], "calories": 850, "sales_volume": 2000},
        {"combo_id": 104, "combo_name": "轻食沙拉套餐", "items": ["鸡胸肉", "混合蔬菜", "酸奶"], "tags": ["低脂", "健康"], "calories": 450, "sales_volume": 500},
        {"combo_id": 105, "combo_name": "牛排套餐", "items": ["煎牛排", "土豆泥", "冰淇淋"], "tags": ["高蛋白"], "calories": 780, "sales_volume": 600},
        {"combo_id": 106, "combo_name": "鳕鱼套餐", "items": ["清蒸鳕鱼", "西兰花", "圣代"], "tags": ["低脂", "海鲜", "非油炸"], "calories": 520, "sales_volume": 400},
    ]

    candidates = []
    for item in mock_data:
        if calorie_range.lower_bound <= item["calories"] <= calorie_range.upper_bound:
            candidates.append(Combo(
                combo_id=item["combo_id"],
                combo_name=item["combo_name"],
                items=[ComboItem(name=i) for i in item["items"]],
                tags=item["tags"],
                calories=item["calories"],
                sales_volume=item["sales_volume"]
            ))

    # 按销量排序
    candidates.sort(key=lambda x: x.sales_volume, reverse=True)
    return candidates[:limit]