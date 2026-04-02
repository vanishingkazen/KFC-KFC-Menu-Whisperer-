"""系统配置"""

import os
from typing import Optional
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = "openai"              # "openai" | "anthropic"
    model: str = "gpt-4o-mini"
    base_url: Optional[str] = None        # 自定义 API 地址
    api_key: Optional[str] = None         # API Key
    temperature: float = 0.7


class RecallConfig(BaseModel):
    """召回层配置"""
    max_candidates: int = 60              # SQL 召回上限
    lower_expand: int = 150               # 下界扩展
    upper_expand: int = 100               # 上界扩展
    enable_sales_sort: bool = True        # 是否按销量排序
    enable_tag_filter: bool = False       # 是否启用标签预过滤


class ValidationConfig(BaseModel):
    """核验层配置"""
    timeout_ms: int = 3000                # Map-Reduce 超时
    max_concurrency: int = 20             # 最大并发数
    enable_cache: bool = True             # 是否缓存核验结果
    cache_ttl_sec: int = 300              # 缓存时间
    allow_partial_match: bool = True      # 是否允许部分匹配进入候选


class RoutingConfig(BaseModel):
    """路由配置"""
    fallback_threshold: int = 1           # 至少满足多少条需求进入 fallback（绝对值，最小值）
    fallback_ratio: float = 0.5         # 满足需求的比例阈值（0.0-1.0）
    fallback_min_match: int = 2           # fallback 最低匹配条数（确保至少满足几条）
    enable_no_match_guidance: bool = True


class GenerationConfig(BaseModel):
    """生成配置"""
    top_k: int = 5                        # 推荐数量
    temperature: float = 0.7              # 生成随机性


class PromptConfig(BaseModel):
    """Prompt 配置"""
    default_version: str = "v1"
    enable_ab_test: bool = False


class SystemConfig(BaseModel):
    """全局配置"""
    llm: LLMConfig = LLMConfig()
    recall: RecallConfig = RecallConfig()
    validation: ValidationConfig = ValidationConfig()
    routing: RoutingConfig = RoutingConfig()
    generation: GenerationConfig = GenerationConfig()
    prompts: PromptConfig = PromptConfig()


# 全局配置实例
_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = SystemConfig()
    return _config


def set_config(config: SystemConfig) -> None:
    """设置全局配置"""
    global _config
    _config = config


def load_config_from_env() -> SystemConfig:
    """从环境变量加载配置"""
    return SystemConfig(
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        ),
        recall=RecallConfig(
            max_candidates=int(os.getenv("MAX_CANDIDATES", "60")),
            lower_expand=int(os.getenv("LOWER_EXPAND", "150")),
            upper_expand=int(os.getenv("UPPER_EXPAND", "100")),
        ),
        validation=ValidationConfig(
            timeout_ms=int(os.getenv("VALIDATION_TIMEOUT_MS", "3000")),
            max_concurrency=int(os.getenv("MAX_CONCURRENCY", "20")),
        ),
        routing=RoutingConfig(
            fallback_threshold=int(os.getenv("FALLBACK_THRESHOLD", "1")),
            fallback_ratio=float(os.getenv("FALLBACK_RATIO", "0.5")),
            fallback_min_match=int(os.getenv("FALLBACK_MIN_MATCH", "2")),
        ),
        generation=GenerationConfig(
            top_k=int(os.getenv("TOP_K", "5")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        ),
    )


def init_from_env() -> SystemConfig:
    """从环境变量初始化配置（全局）"""
    global _config
    _config = load_config_from_env()
    return _config