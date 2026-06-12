""".doc (旧版 Word) 解析器 — olefile 提取文本"""

import re
from .base import BaseParser, ParsedPage


class DocParser(BaseParser):
    def parse(self, file_path: str) -> list[ParsedPage]:
        import olefile

        ole = olefile.OleFileIO(file_path)
        text = ""

        # 遍历所有流，找到包含最多中文字符的流
        best = ""
        for stream_name in ole.listdir():
            name = "/".join(stream_name)
            try:
                stream = ole.openstream(stream_name)
                data = stream.read()
                decoded = self._try_decode(data)
                if decoded and len(decoded) > len(best):
                    best = decoded
            except Exception:
                from loguru import logger
                logger.debug(f"OLE 流 {name} 解码失败")

        ole.close()
        if not best.strip():
            return []
        return [ParsedPage(page_number=1, text=best)]

    def _try_decode(self, data: bytes) -> str:
        """尝试 UTF-16LE 解码并过滤噪声"""
        try:
            text = data.decode("utf-16-le", errors="ignore")
        except (UnicodeDecodeError, AttributeError):
            return ""

        # 过滤控制字符（保留 \n \r \t）
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

        # 保留包含中文或可读内容的行
        lines = []
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            # 行中至少包含中文字符或有意义的ASCII内容
            chinese_chars = sum(1 for c in stripped if "一" <= c <= "鿿")
            ascii_chars = sum(1 for c in stripped if c.isascii() and c.isalpha())
            if chinese_chars > 0 or ascii_chars > 3:
                lines.append(stripped)

        return "\n".join(lines)
