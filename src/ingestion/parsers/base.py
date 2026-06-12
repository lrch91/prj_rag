"""解析器基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedPage:
    page_number: int
    text: str


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> list[ParsedPage]:
        """解析文档，返回按页分组的文本列表"""
        ...
