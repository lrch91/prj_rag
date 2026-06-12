"""Anthropic Claude Provider"""

from anthropic import AsyncAnthropic
from src.llm_gateway.base import BaseLLMProvider, LLMRequest, LLMResponse
from src.config import settings


class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: str = ""):
        self._client = AsyncAnthropic(api_key=api_key or settings.anthropic_api_key)

    async def chat(self, request: LLMRequest) -> LLMResponse:
        # 提取 system 消息（如有）
        system_msg = ""
        user_msgs = []
        for m in request.messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                user_msgs.append(m)
        resp = await self._client.messages.create(
            model=request.model,
            max_tokens=request.max_tokens,
            system=system_msg or None,
            messages=user_msgs,
        )
        text = ""
        for block in resp.content:
            if hasattr(block, "text"):
                text += block.text
        return LLMResponse(
            content=text,
            model=resp.model,
            input_tokens=resp.usage.input_tokens if resp.usage else 0,
            output_tokens=resp.usage.output_tokens if resp.usage else 0,
        )

    async def chat_stream(self, request: LLMRequest):
        system_msg = ""
        user_msgs = []
        for m in request.messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                user_msgs.append(m)
        async with self._client.messages.stream(
            model=request.model,
            max_tokens=request.max_tokens,
            system=system_msg or None,
            messages=user_msgs,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def default_model(self) -> str:
        return "claude-sonnet-4-20250514"
