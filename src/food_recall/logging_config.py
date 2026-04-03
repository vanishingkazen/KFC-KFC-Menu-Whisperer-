"""日志配置模块"""

import os
import logging
from datetime import datetime


_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
LOG_DIR = os.path.join(_project_root, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


class UnbufferedFileHandler(logging.FileHandler):
    """无缓冲的文件 Handler，确保日志立即写入"""

    def emit(self, record):
        super().emit(record)
        self.flush()


def setup_logging(
    name: str = "food_recall",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    配置日志，同时输出到文件和控制台

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_to_file: 是否写入文件
        log_to_console: 是否输出到控制台

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(name)s - %(levelname)s - %(message)s"
    )

    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(LOG_DIR, f"{name}_{timestamp}.log")

        try:
            file_handler = UnbufferedFileHandler(
                log_file,
                encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except PermissionError:
            import warnings
            warnings.warn(f"无法创建日志文件 {log_file}，将只输出到控制台")

    return logger


def get_logger(name: str = "food_recall") -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)
