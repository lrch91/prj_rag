"""Kimi / Moonshot Provider（OpenAI 兼容）"""

from src.llm_gateway.providers.openai import OpenAIProvider


class KimiProvider(OpenAIProvider):
    def __init__(self, api_key: str = ""):
        super().__init__(api_key=api_key, base_url="https://api.moonshot.cn/v1")

    def default_model(self) -> str:
        return "moonshot-v1-8k"
