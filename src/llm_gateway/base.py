"""LLM Provider 抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class LLMRequest:
    messages: list[dict]
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = "stop"


class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat(self, request: LLMRequest) -> LLMResponse:
        ...

    @abstractmethod
    async def chat_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        ...

    @abstractmethod
    def default_model(self) -> str:
        ...
