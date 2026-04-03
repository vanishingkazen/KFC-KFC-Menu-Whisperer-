"""数据库初始化与数据生成脚本"""

import sqlite3
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from food_recall.config import get_database_path


COMBOS_DATA = [
    {
        "combo_id": 101,
        "combo_name": "香煎鸡胸肉套餐",
        "items": "煎鸡胸,水煮西兰花,原味圣代",
        "tags": "高蛋白,非油炸,减脂",
        "calories": 580,
        "sales_volume": 1200
    },
    {
        "combo_id": 102,
        "combo_name": "烤鸡腿套餐",
        "items": "烤鸡腿,蔬菜沙拉,冰淇淋",
        "tags": "高蛋白,非油炸",
        "calories": 720,
        "sales_volume": 980
    },
    {
        "combo_id": 103,
        "combo_name": "油炸鸡块套餐",
        "items": "炸鸡块,薯条,可乐",
        "tags": "油炸,高热量",
        "calories": 950,
        "sales_volume": 2500
    },
    {
        "combo_id": 104,
        "combo_name": "轻食沙拉套餐",
        "items": "鸡胸肉,混合蔬菜,酸奶",
        "tags": "低脂,健康,减脂",
        "calories": 420,
        "sales_volume": 650
    },
    {
        "combo_id": 105,
        "combo_name": "牛排套餐",
        "items": "煎牛排,土豆泥,冰淇淋",
        "tags": "高蛋白",
        "calories": 780,
        "sales_volume": 720
    },
    {
        "combo_id": 106,
        "combo_name": "鳕鱼套餐",
        "items": "清蒸鳕鱼,西兰花,圣代",
        "tags": "低脂,海鲜,非油炸",
        "calories": 480,
        "sales_volume": 380
    },
    {
        "combo_id": 107,
        "combo_name": "麻辣烫套餐",
        "items": "牛肉片,多种蔬菜,米饭",
        "tags": "中热量",
        "calories": 650,
        "sales_volume": 1100
    },
    {
        "combo_id": 108,
        "combo_name": "寿司套餐",
        "items": "三文鱼寿司,加州卷,味噌汤",
        "tags": "海鲜,低脂,健康",
        "calories": 520,
        "sales_volume": 580
    },
    {
        "combo_id": 109,
        "combo_name": "炸鸡套餐",
        "items": "香脆炸鸡,薯条,可乐",
        "tags": "油炸,高热量",
        "calories": 1100,
        "sales_volume": 3000
    },
    {
        "combo_id": 110,
        "combo_name": "蒸蛋套餐",
        "items": "蒸蛋,清炒时蔬,米饭",
        "tags": "低脂,健康,高蛋白",
        "calories": 450,
        "sales_volume": 420
    },
    {
        "combo_id": 111,
        "combo_name": "咖喱鸡肉套餐",
        "items": "咖喱鸡肉,米饭,蔬菜沙拉",
        "tags": "中热量,高蛋白",
        "calories": 680,
        "sales_volume": 890
    },
    {
        "combo_id": 112,
        "combo_name": "素食套餐",
        "items": "素汉堡,薯条,果汁",
        "tags": "素食",
        "calories": 620,
        "sales_volume": 350
    },
    {
        "combo_id": 113,
        "combo_name": "双层牛肉汉堡套餐",
        "items": "双层牛肉堡,薯条,可乐",
        "tags": "高热量,高蛋白",
        "calories": 1250,
        "sales_volume": 1800
    },
    {
        "combo_id": 114,
        "combo_name": "日式拉面套餐",
        "items": "叉烧拉面,煎饺,奶茶",
        "tags": "高热量",
        "calories": 980,
        "sales_volume": 1400
    },
    {
        "combo_id": 115,
        "combo_name": "越南春卷套餐",
        "items": "鲜虾春卷,米粉,柠檬水",
        "tags": "低脂,健康,海鲜",
        "calories": 380,
        "sales_volume": 290
    },
    {
        "combo_id": 116,
        "combo_name": "烤鱼套餐",
        "items": "烤三文鱼,烤蔬菜,柠檬",
        "tags": "低脂,高蛋白,海鲜",
        "calories": 550,
        "sales_volume": 520
    },
    {
        "combo_id": 117,
        "combo_name": "意大利面套餐",
        "items": "肉酱意大利面,蒜蓉面包,沙拉",
        "tags": "中热量",
        "calories": 750,
        "sales_volume": 950
    },
    {
        "combo_id": 118,
        "combo_name": "鸡腿排套餐",
        "items": "照烧鸡腿排,米饭,泡菜",
        "tags": "高蛋白,中热量",
        "calories": 720,
        "sales_volume": 880
    },
    {
        "combo_id": 119,
        "combo_name": "健康减脂套餐",
        "items": "鸡胸肉沙拉,全麦面包,果汁",
        "tags": "低脂,减脂,健康",
        "calories": 480,
        "sales_volume": 620
    },
    {
        "combo_id": 120,
        "combo_name": "儿童套餐",
        "items": "小汉堡,薯条,牛奶",
        "tags": "儿童,高热量",
        "calories": 680,
        "sales_volume": 420
    },
    {
        "combo_id": 121,
        "combo_name": "火锅套餐",
        "items": "肥牛,羊肉卷,多种蔬菜,火锅底料",
        "tags": "高热量,高蛋白",
        "calories": 1200,
        "sales_volume": 1600
    },
    {
        "combo_id": 122,
        "combo_name": "沙拉套餐",
        "items": "凯撒沙拉,鸡胸肉,全麦面包",
        "tags": "低脂,健康,减脂",
        "calories": 450,
        "sales_volume": 550
    },
    {
        "combo_id": 123,
        "combo_name": "串串香套餐",
        "items": "牛肉串,鸡肉串,蔬菜串,米饭",
        "tags": "中热量",
        "calories": 780,
        "sales_volume": 1100
    },
    {
        "combo_id": 124,
        "combo_name": "韩式拌饭套餐",
        "items": "石锅拌饭,煎蛋,辣白菜",
        "tags": "中热量",
        "calories": 680,
        "sales_volume": 820
    },
    {
        "combo_id": 125,
        "combo_name": "披萨套餐",
        "items": "意大利披萨,薯条,可乐",
        "tags": "高热量",
        "calories": 1050,
        "sales_volume": 1900
    },
]


def init_database():
    """初始化数据库"""
    db_path = get_database_path()
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"删除旧数据库: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE combos (
            combo_id INTEGER PRIMARY KEY,
            combo_name TEXT NOT NULL,
            items TEXT NOT NULL,
            tags TEXT NOT NULL,
            calories INTEGER NOT NULL,
            sales_volume INTEGER DEFAULT 0,
            status TEXT DEFAULT 'on_shelf'
        )
    """)

    cursor.execute("""
        CREATE INDEX idx_calories ON combos(calories)
    """)

    cursor.execute("""
        CREATE INDEX idx_status ON combos(status)
    """)

    for combo in COMBOS_DATA:
        cursor.execute("""
            INSERT INTO combos (combo_id, combo_name, items, tags, calories, sales_volume, status)
            VALUES (?, ?, ?, ?, ?, ?, 'on_shelf')
        """, (
            combo["combo_id"],
            combo["combo_name"],
            combo["items"],
            combo["tags"],
            combo["calories"],
            combo["sales_volume"]
        ))

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM combos")
    count = cursor.fetchone()[0]

    conn.close()

    print(f"数据库初始化完成: {db_path}")
    print(f"共插入 {count} 条套餐数据")

    return db_path


def query_combos(lower_bound: int, upper_bound: int, limit: int = 60):
    """查询符合条件的套餐"""
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT combo_id, combo_name, items, tags, calories, sales_volume
        FROM combos
        WHERE calories >= ? AND calories <= ? AND status = 'on_shelf'
        ORDER BY sales_volume DESC
        LIMIT ?
    """, (lower_bound, upper_bound, limit))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


if __name__ == "__main__":
    init_database()

    print("\n测试查询 (热量 550-750):")
    results = query_combos(550, 750)
    for r in results:
        print(f"  - {r['combo_name']}: {r['calories']}大卡, 销量: {r['sales_volume']}")