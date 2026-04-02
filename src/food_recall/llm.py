"""LLM 客户端配置"""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


class LLMClient:
    """LLM 客户端统一管理"""

    def __init__(
        self,
        provider: str = "openai",  # "openai" | "anthropic"
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ):
        self.provider = provider
        self.model = model
        self.temperature = temperature

        if provider == "openai":
            self.client = ChatOpenAI(
                model=model,
                base_url=base_url,
                api_key=api_key,
                temperature=temperature,
                **kwargs
            )
        elif provider == "anthropic":
            self.client = ChatAnthropic(
                model=model,
                anthropic_api_key=api_key,
                temperature=temperature,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def invoke(self, prompt: str) -> str:
        """调用 LLM"""
        response = self.client.invoke(prompt)
        return response.content

    async def ainvoke(self, prompt: str) -> str:
        """异步调用 LLM"""
        response = await self.client.ainvoke(prompt)
        return response.content


# 全局 LLM 客户端
_llm_client: Optional[LLMClient] = None


def init_llm(
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> LLMClient:
    """
    初始化 LLM 客户端

    Args:
        provider: LLM 提供商 ("openai" | "anthropic")
        model: 模型名称
        base_url: 自定义 API 地址（用于代理或本地部署）
        api_key: API Key
        temperature: 温度参数
    """
    global _llm_client
    _llm_client = LLMClient(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        **kwargs
    )
    return _llm_client


def get_llm() -> Optional[LLMClient]:
    """获取 LLM 客户端"""
    return _llm_client


def is_llm_initialized() -> bool:
    """检查是否已初始化 LLM"""
    return _llm_client is not None