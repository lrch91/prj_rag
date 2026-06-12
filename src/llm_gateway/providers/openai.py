"""OpenAI Provider（含所有 OpenAI 兼容 API）"""

from openai import AsyncOpenAI
from src.llm_gateway.base import BaseLLMProvider, LLMRequest, LLMResponse
from src.config import settings


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str = "", base_url: str = ""):
        self._client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key,
            base_url=base_url or settings.openai_base_url or None,
        )

    async def chat(self, request: LLMRequest) -> LLMResponse:
        resp = await self._client.chat.completions.create(
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        choice = resp.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            output_tokens=resp.usage.completion_tokens if resp.usage else 0,
            finish_reason=choice.finish_reason or "stop",
        )

    async def chat_stream(self, request: LLMRequest):
        stream = await self._client.chat.completions.create(
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def default_model(self) -> str:
        return "gpt-4o"
