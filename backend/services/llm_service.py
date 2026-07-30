"""LLM 统一调用服务"""
from typing import Optional

import litellm

from config import settings

# 关闭 litellm 的遥测
litellm.telemetry = False


def _build_model_name() -> str:
    """根据 provider 构建 litellm 模型标识"""
    provider = settings.llm.provider
    model = settings.llm.model

    if provider == "ollama":
        return f"ollama/{model}"
    elif provider == "openai":
        return model
    elif provider == "custom":
        return f"openai/{model}"  # 使用 openai 兼容模式
    return model


async def chat_completion(
    messages: list[dict],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    统一 LLM 调用接口

    Args:
        messages: OpenAI 格式的消息列表 [{"role": "system", "content": "..."}]
        temperature: 温度参数，None 则使用配置默认值
        max_tokens: 最大 token 数，None 则使用配置默认值

    Returns:
        LLM 生成的文本内容
    """
    model = _build_model_name()
    temp = temperature if temperature is not None else settings.llm.temperature
    tokens = max_tokens if max_tokens is not None else settings.llm.max_tokens

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temp,
        "max_tokens": tokens,
    }

    # 设置 API Key
    if settings.llm.api_key:
        kwargs["api_key"] = settings.llm.api_key

    # 设置自定义 base_url
    if settings.llm.base_url:
        kwargs["api_base"] = settings.llm.base_url

    response = await litellm.acompletion(**kwargs)
    return response.choices[0].message.content
