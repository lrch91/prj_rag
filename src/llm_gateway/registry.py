"""LLM Provider 注册表"""

from src.llm_gateway.base import BaseLLMProvider
from src.llm_gateway.providers.openai import OpenAIProvider
from src.config import settings


class LLMRegistry:
    def __init__(self):
        self._providers: dict[str, BaseLLMProvider] = {}

    def get_provider(self, model_name: str) -> BaseLLMProvider:
        if model_name in self._providers:
            return self._providers[model_name]
        provider = self._create_provider(model_name)
        self._providers[model_name] = provider
        return provider

    def _create_provider(self, model_name: str) -> BaseLLMProvider:
        if model_name.startswith("deepseek"):
            return OpenAIProvider(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
        if model_name.startswith("gpt") or model_name.startswith("o1") or model_name.startswith("o3"):
            return OpenAIProvider(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        if model_name.startswith("claude"):
            from src.llm_gateway.providers.claude import ClaudeProvider
            return ClaudeProvider()
        if model_name.startswith("qwen"):
            from src.llm_gateway.providers.qwen import QwenProvider
            return QwenProvider()
        if model_name.startswith("moonshot") or model_name.startswith("kimi"):
            from src.llm_gateway.providers.kimi import KimiProvider
            return KimiProvider()
        # 默认 OpenAI
        return OpenAIProvider()


registry = LLMRegistry()
