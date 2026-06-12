"""DOCX 解析器 — 结构感知：Word Heading样式 + 中文标题模式"""

import re
from .base import BaseParser, ParsedPage

# 中文法律/公文标题模式
_CN_HEADING_PATTERNS = [
    (re.compile(r"第[一二三四五六七八九十百千\d]+编"), 1),   # 第一编 → level 1
    (re.compile(r"第[一二三四五六七八九十百千\d]+章"), 2),   # 第一章 → level 2
    (re.compile(r"第[一二三四五六七八九十百千\d]+节"), 3),   # 第一节 → level 3
]


class DocxParser(BaseParser):
    def parse(self, file_path: str) -> list[ParsedPage]:
        from docx import Document

        doc = Document(file_path)
        parts: list[str] = []
        heading_stack: list[str] = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style = para.style.name if para.style else ""
            level = self._get_heading_level(text, style)

            if level > 0:
                heading_stack = heading_stack[:level - 1]
                heading_stack.append(text)
            else:
                if heading_stack:
                    path = " > ".join(heading_stack)
                    parts.append(f"【{path}】\n{text}")
                else:
                    parts.append(text)

        if not parts:
            return []
        return [ParsedPage(page_number=1, text="\n\n".join(parts))]

    def _get_heading_level(self, text: str, style: str) -> int:
        # 方法1：Word 标准 Heading 样式
        if style.startswith("Heading"):
            try:
                return int(style.split()[-1]) if style.split()[-1].isdigit() else 1
            except (IndexError, ValueError):
                return 1
        # 方法2：中文标题模式匹配
        for pattern, level in _CN_HEADING_PATTERNS:
            if pattern.match(text):
                return level
        return 0
