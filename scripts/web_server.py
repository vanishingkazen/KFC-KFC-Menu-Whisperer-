"""Web 测试后台"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

import sqlite3
from flask import Flask, request, jsonify, render_template
from food_recall.workflow import run_workflow_sync
from food_recall.config import init_from_env, get_database_path

SCRIPT_DIR = Path(__file__).parent
app = Flask(__name__, template_folder=str(SCRIPT_DIR / "templates"), static_folder=str(SCRIPT_DIR / "static"))


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库"""
    db_path = get_database_path()
    if os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS combos (
            combo_id INTEGER PRIMARY KEY,
            combo_name TEXT NOT NULL,
            items TEXT NOT NULL,
            tags TEXT NOT NULL,
            calories INTEGER NOT NULL,
            sales_volume INTEGER DEFAULT 0,
            status TEXT DEFAULT 'on_shelf'
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_calories ON combos(calories)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON combos(status)")

    COMBOS_DATA = [
        {"combo_id": 101, "combo_name": "香煎鸡胸肉套餐", "items": "煎鸡胸,水煮西兰花,原味圣代", "tags": "高蛋白,非油炸,减脂", "calories": 580, "sales_volume": 1200},
        {"combo_id": 102, "combo_name": "烤鸡腿套餐", "items": "烤鸡腿,蔬菜沙拉,冰淇淋", "tags": "高蛋白,非油炸", "calories": 720, "sales_volume": 980},
        {"combo_id": 103, "combo_name": "油炸鸡块套餐", "items": "炸鸡块,薯条,可乐", "tags": "油炸,高热量", "calories": 950, "sales_volume": 2500},
        {"combo_id": 104, "combo_name": "轻食沙拉套餐", "items": "鸡胸肉,混合蔬菜,酸奶", "tags": "低脂,健康,减脂", "calories": 420, "sales_volume": 650},
        {"combo_id": 105, "combo_name": "牛排套餐", "items": "煎牛排,土豆泥,冰淇淋", "tags": "高蛋白", "calories": 780, "sales_volume": 720},
        {"combo_id": 106, "combo_name": "鳕鱼套餐", "items": "清蒸鳕鱼,西兰花,圣代", "tags": "低脂,海鲜,非油炸", "calories": 480, "sales_volume": 380},
    ]

    for combo in COMBOS_DATA:
        cursor.execute("""
            INSERT INTO combos (combo_id, combo_name, items, tags, calories, sales_volume, status)
            VALUES (?, ?, ?, ?, ?, ?, 'on_shelf')
        """, (combo["combo_id"], combo["combo_name"], combo["items"], combo["tags"], combo["calories"], combo["sales_volume"]))

    conn.commit()
    conn.close()
    print(f"数据库初始化完成: {DB_PATH}")


@app.route("/")
def index():
    """首页"""
    return render_template("index.html")


@app.route("/api/combos", methods=["GET"])
def get_combos():
    """获取所有套餐"""
    conn = get_db_connection()
    combos = conn.execute("SELECT * FROM combos WHERE status = 'on_shelf' ORDER BY sales_volume DESC").fetchall()
    conn.close()
    return jsonify([dict(row) for row in combos])


@app.route("/api/combos/<int:combo_id>", methods=["GET"])
def get_combo(combo_id):
    """获取单个套餐"""
    conn = get_db_connection()
    combo = conn.execute("SELECT * FROM combos WHERE combo_id = ?", (combo_id,)).fetchone()
    conn.close()
    if combo is None:
        return jsonify({"error": "套餐不存在"}), 404
    return jsonify(dict(combo))


@app.route("/api/combos", methods=["POST"])
def create_combo():
    """创建套餐"""
    data = request.json

    required_fields = ["combo_name", "items", "tags", "calories"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"缺少必需字段: {field}"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(combo_id) as max_id FROM combos")
    max_id = cursor.fetchone()["max_id"] or 100
    new_id = max_id + 1

    cursor.execute("""
        INSERT INTO combos (combo_id, combo_name, items, tags, calories, sales_volume, status)
        VALUES (?, ?, ?, ?, ?, ?, 'on_shelf')
    """, (
        new_id,
        data["combo_name"],
        data["items"],
        data["tags"],
        data.get("calories", 0),
        data.get("sales_volume", 0)
    ))

    conn.commit()
    new_combo = cursor.execute("SELECT * FROM combos WHERE combo_id = ?", (new_id,)).fetchone()
    conn.close()

    return jsonify(dict(new_combo)), 201


@app.route("/api/combos/<int:combo_id>", methods=["PUT"])
def update_combo(combo_id):
    """更新套餐"""
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM combos WHERE combo_id = ?", (combo_id,))
    existing = cursor.fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "套餐不存在"}), 404

    combo_name = data.get("combo_name", existing["combo_name"])
    items = data.get("items", existing["items"])
    tags = data.get("tags", existing["tags"])
    calories = data.get("calories", existing["calories"])
    sales_volume = data.get("sales_volume", existing["sales_volume"])
    status = data.get("status", existing["status"])

    cursor.execute("""
        UPDATE combos
        SET combo_name = ?, items = ?, tags = ?, calories = ?, sales_volume = ?, status = ?
        WHERE combo_id = ?
    """, (combo_name, items, tags, calories, sales_volume, status, combo_id))

    conn.commit()
    updated_combo = cursor.execute("SELECT * FROM combos WHERE combo_id = ?", (combo_id,)).fetchone()
    conn.close()

    return jsonify(dict(updated_combo))


@app.route("/api/combos/<int:combo_id>", methods=["DELETE"])
def delete_combo(combo_id):
    """删除套餐（软删除）"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM combos WHERE combo_id = ?", (combo_id,))
    existing = cursor.fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "套餐不存在"}), 404

    cursor.execute("UPDATE combos SET status = 'off_shelf' WHERE combo_id = ?", (combo_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "删除成功"})


@app.route("/api/test", methods=["POST"])
def test_workflow():
    """测试工作流"""
    data = request.json
    user_input = data.get("user_input", "")

    if not user_input:
        return jsonify({"error": "请提供 user_input"}), 400

    try:
        result = run_workflow_sync(user_input)

        combos = result.get("candidates", [])
        demands = result.get("demands", [])
        validation_results = result.get("validation_results", [])
        perfect_matches = result.get("perfect_matches", [])
        partial_matches = result.get("partial_matches", [])

        combos_info = []
        for combo in combos:
            items = combo.items if hasattr(combo, 'items') else []
            if hasattr(items, '__iter__') and not isinstance(items, str):
                items = [i.name if hasattr(i, 'name') else str(i) for i in items]
            combos_info.append({
                "combo_id": combo.combo_id if hasattr(combo, 'combo_id') else combo.get('combo_id'),
                "combo_name": combo.combo_name if hasattr(combo, 'combo_name') else combo.get('combo_name'),
                "items": items,
                "tags": combo.tags if hasattr(combo, 'tags') else combo.get('tags', []),
                "calories": combo.calories if hasattr(combo, 'calories') else combo.get('calories'),
                "sales_volume": combo.sales_volume if hasattr(combo, 'sales_volume') else combo.get('sales_volume', 0)
            })

        demands_info = []
        for demand in demands:
            content = demand.content if hasattr(demand, 'content') else demand.get('content', '')
            demands_info.append({"demand_id": demand.demand_id if hasattr(demand, 'demand_id') else demand.get('demand_id'), "content": content})

        perfect_matches_info = []
        for pm in perfect_matches:
            results_list = []
            for vr in pm.results if hasattr(pm, 'results') else pm.get('results', []):
                results_list.append({
                    "demand_id": vr.demand_id if hasattr(vr, 'demand_id') else vr.get('demand_id'),
                    "demand": vr.demand if hasattr(vr, 'demand') else vr.get('demand', ''),
                    "match": vr.match if hasattr(vr, 'match') else vr.get('match', False),
                    "reason": vr.reason if hasattr(vr, 'reason') else vr.get('reason', '')
                })
            perfect_matches_info.append({
                "combo_id": pm.combo_id,
                "combo_name": pm.combo_name,
                "score": pm.score,
                "total_demands": pm.total_demands,
                "results": results_list,
                "unmet_reasons": pm.unmet_reasons if hasattr(pm, 'unmet_reasons') else pm.get('unmet_reasons', [])
            })

        partial_matches_info = []
        for p in partial_matches:
            results_list = []
            for vr in p.results if hasattr(p, 'results') else p.get('results', []):
                results_list.append({
                    "demand_id": vr.demand_id if hasattr(vr, 'demand_id') else vr.get('demand_id'),
                    "demand": vr.demand if hasattr(vr, 'demand') else vr.get('demand', ''),
                    "match": vr.match if hasattr(vr, 'match') else vr.get('match', False),
                    "reason": vr.reason if hasattr(vr, 'reason') else vr.get('reason', '')
                })
            partial_matches_info.append({
                "combo_id": p.combo_id,
                "combo_name": p.combo_name,
                "score": p.score,
                "total_demands": p.total_demands,
                "results": results_list,
                "unmet_reasons": p.unmet_reasons if hasattr(p, 'unmet_reasons') else p.get('unmet_reasons', [])
            })

        calorie_range = result.get("calorie_range")
        if calorie_range:
            calorie_range_info = {
                "lower_bound": calorie_range.lower_bound if hasattr(calorie_range, 'lower_bound') else calorie_range.get('lower_bound'),
                "upper_bound": calorie_range.upper_bound if hasattr(calorie_range, 'upper_bound') else calorie_range.get('upper_bound')
            }
        else:
            calorie_range_info = None

        return jsonify({
            "user_input": user_input,
            "calorie_range": calorie_range_info,
            "target_calorie": result.get("target_calorie"),
            "combos_count": len(combos_info),
            "demands": demands_info,
            "validation_results_count": len(validation_results),
            "route_decision": result.get("route_decision"),
            "perfect_matches": perfect_matches_info,
            "partial_matches": partial_matches_info,
            "final_response": result.get("final_response")
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


if __name__ == "__main__":
    init_db()
    init_from_env()
    app.run(host="0.0.0.0", port=5001, debug=True)