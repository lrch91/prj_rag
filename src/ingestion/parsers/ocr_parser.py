"""OCR 图片解析器"""

from .base import BaseParser, ParsedPage


class OCRParser(BaseParser):
    def parse(self, file_path: str) -> list[ParsedPage]:
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(file_path)
            # 中文 + 英文 OCR
            text = pytesseract.image_to_string(img, lang="chi_sim+eng")
            if not text.strip():
                return []
            return [ParsedPage(page_number=1, text=text)]
        except ImportError:
            raise RuntimeError("pytesseract 未安装，无法进行 OCR 识别")
