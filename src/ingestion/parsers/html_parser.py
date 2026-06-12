"""HTML 解析器 — 结构感知：保留 h1-h6 标题层级"""

from .base import BaseParser, ParsedPage


class HTMLParser(BaseParser):
    def parse(self, file_path: str) -> list[ParsedPage]:
        from html.parser import HTMLParser as _HTMLParser

        class StructuredExtractor(_HTMLParser):
            def __init__(self):
                super().__init__()
                self.parts: list[str] = []
                self.heading_stack: list[str] = []
                self._current_tag: str | None = None
                self._buffer: str = ""

            def handle_starttag(self, tag, attrs):
                self._flush_buffer()
                self._current_tag = tag
                if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                    level = int(tag[1])
                    self.heading_stack = self.heading_stack[:level - 1]

            def handle_endtag(self, tag):
                if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                    title = self._buffer.strip()
                    if title:
                        self.heading_stack.append(title)
                self._flush_buffer()
                self._current_tag = None

            def handle_data(self, data):
                self._buffer += data

            def _flush_buffer(self):
                text = self._buffer.strip()
                self._buffer = ""
                if not text or self._current_tag and self._current_tag.startswith("h"):
                    return
                if self.heading_stack:
                    path = " > ".join(self.heading_stack)
                    self.parts.append(f"【{path}】\n{text}")
                else:
                    self.parts.append(text)

        with open(file_path, encoding="utf-8") as f:
            html = f.read()
        extractor = StructuredExtractor()
        extractor.feed(html)
        extractor._flush_buffer()
        if not extractor.parts:
            return []
        return [ParsedPage(page_number=1, text="\n\n".join(extractor.parts))]
