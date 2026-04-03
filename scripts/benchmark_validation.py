"""核验性能基准测试"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from food_recall.workflow import run_workflow_sync
from food_recall.logging_config import setup_logging, get_logger

setup_logging("food_recall")
bench_logger = get_logger("food_recall")

TEST_INPUTS = [
    "我要一份带鸡腿的 700 大卡左右的套餐",
    "一份 600 大卡的轻食套餐，要有鸡胸肉和圣代",
    "给我来一个 800 大卡左右的套餐，不要油炸的",
]

def run_benchmark():
    bench_logger.info("=" * 60)
    bench_logger.info("核验性能基准测试")
    bench_logger.info("=" * 60)

    all_combo_times = []

    for i, test_input in enumerate(TEST_INPUTS, 1):
        bench_logger.info(f"\n【测试 {i}】输入: {test_input}")
        bench_logger.info("-" * 40)

        start = time.time()
        result = run_workflow_sync(test_input)
        total_elapsed = time.time() - start

        candidates = result.get("candidates", [])
        validation_results = result.get("validation_results", [])

        combo_times = []
        for vr in validation_results:
            matched = [r for r in vr.results if r.match]
            combo_times.append({
                "name": vr.combo_name,
                "score": f"{vr.score}/{vr.total_demands}",
                "demands": len(vr.results)
            })

        all_combo_times.extend(combo_times)

        bench_logger.info(f"总耗时: {total_elapsed:.3f}s")
        bench_logger.info(f"候选套餐数: {len(candidates)}")
        bench_logger.info(f"核验完成数: {len(validation_results)}")

    bench_logger.info("\n" + "=" * 60)
    bench_logger.info("汇总统计")
    bench_logger.info("=" * 60)

    if all_combo_times:
        bench_logger.info(f"总套餐核验次数: {len(all_combo_times)}")
        for combo in all_combo_times:
            bench_logger.info(f"  - {combo['name']}: score={combo['score']}")


if __name__ == "__main__":
    run_benchmark()
