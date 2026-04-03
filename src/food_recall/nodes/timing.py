"""节点计时包装器"""

import time
from typing import Callable, TypeVar, Awaitable
from functools import wraps

from ..logging_config import get_logger

logger = get_logger("food_recall")

F = TypeVar('F', bound=Callable[..., Awaitable[dict]])


def with_timing(func: F) -> F:
    """为异步节点添加计时的装饰器"""

    @wraps(func)
    async def wrapper(state: dict) -> dict:
        node_name = func.__name__
        start_time = time.time()

        try:
            result = await func(state)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[耗时] {node_name} 失败，耗时 {elapsed:.3f}s - {str(e)}")
            raise

        elapsed = time.time() - start_time

        timing = state.get("timing", {})
        timing[node_name] = elapsed
        result["timing"] = timing

        logger.info(f"[耗时] {node_name} 完成，耗时 {elapsed:.3f}s")
        return result

    return wrapper  # type: ignore


def with_timing_sync(func: F) -> F:
    """为同步节点添加计时的装饰器"""

    @wraps(func)
    def wrapper(state: dict) -> dict:
        node_name = func.__name__
        start_time = time.time()

        try:
            result = func(state)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[耗时] {node_name} 失败，耗时 {elapsed:.3f}s - {str(e)}")
            raise

        elapsed = time.time() - start_time

        timing = state.get("timing", {})
        timing[node_name] = elapsed
        result["timing"] = timing

        logger.info(f"[耗时] {node_name} 完成，耗时 {elapsed:.3f}s")
        return result

    return wrapper  # type: ignore
