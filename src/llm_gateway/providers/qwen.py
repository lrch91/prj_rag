"""Qwen / DashScope Provider（OpenAI 兼容）"""

from src.llm_gateway.providers.openai import OpenAIProvider
from src.config import settings


class QwenProvider(OpenAIProvider):
    def __init__(self, api_key: str = ""):
        super().__init__(
            api_key=api_key or settings.qwen_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def default_model(self) -> str:
        return "qwen-max"
