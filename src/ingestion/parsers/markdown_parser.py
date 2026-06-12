"""Markdown 解析器 — 结构感知：保留 # 标题层级"""

import re
from .base import BaseParser, ParsedPage


class MarkdownParser(BaseParser):
    def parse(self, file_path: str) -> list[ParsedPage]:
        with open(file_path, encoding="utf-8") as f:
            text = f.read()
        if not text.strip():
            return []

        parts: list[str] = []
        heading_stack: list[str] = []

        for line in text.split("\n"):
            m = re.match(r"^(#{1,6})\s+(.+)", line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                heading_stack = heading_stack[:level - 1]
                heading_stack.append(title)
            elif line.strip():
                if heading_stack:
                    path = " > ".join(heading_stack)
                    parts.append(f"【{path}】\n{line.strip()}")
                else:
                    parts.append(line.strip())

        if not parts:
            return [ParsedPage(page_number=1, text=text)]
        return [ParsedPage(page_number=1, text="\n\n".join(parts))]
