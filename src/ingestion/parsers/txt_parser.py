"""TXT 解析器"""

from .base import BaseParser, ParsedPage


class TxtParser(BaseParser):
    def parse(self, file_path: str) -> list[ParsedPage]:
        with open(file_path, encoding="utf-8") as f:
            text = f.read()
        if not text.strip():
            return []
        return [ParsedPage(page_number=1, text=text)]
