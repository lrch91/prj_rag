"""PDF 解析器 — 文本提取 + 百度 OCR 双通道

策略：采样 5 页预判文档类型 → 全文本型不调 OCR → 全扫描件仅 OCR 前两页
"""

from .base import BaseParser, ParsedPage

_OCR_THRESHOLD = 50       # 单页字符 < 50 → 视为扫描件页
_SAMPLE_PAGES = [1, 5, 10, 20, 50]  # 采样判断用的页码
_MAX_OCR_PAGES = 2        # 扫描件最多 OCR 前 N 页，剩余页面跳过

_ocr_client = None


def _get_ocr():
    global _ocr_client
    if _ocr_client is None:
        from aip import AipOcr
        _ocr_client = AipOcr("7828205", "Kj5kgnD2vLqlPhJdDapK4KvH", "yxkZtnHR0Ds0yInzwCVnEZonczXcsVfT")
    return _ocr_client


class PDFParser(BaseParser):
    def parse(self, file_path: str) -> list[ParsedPage]:
        import pdfplumber

        pages: list[ParsedPage] = []
        with pdfplumber.open(file_path) as pdf:
            is_scanned = self._detect_scanned(pdf)
            for i, page in enumerate(pdf.pages, start=1):
                if is_scanned and i > _MAX_OCR_PAGES:
                    break
                text = (page.extract_text() or "").strip()
                if is_scanned:
                    text = self._ocr_page(file_path, i) or text
                if text:
                    pages.append(ParsedPage(page_number=i, text=text))
        return pages

    def _detect_scanned(self, pdf) -> bool:
        """采样预判：抽几页看是否全是图片/扫描件"""
        total = len(pdf.pages)
        for pn in _SAMPLE_PAGES:
            if pn > total:
                continue
            text = (pdf.pages[pn - 1].extract_text() or "").strip()
            if len(text) >= _OCR_THRESHOLD:
                return False  # 有一页够文本 → 文本型
        return True  # 全部不够 → 扫描件

    def _ocr_page(self, file_path: str, page_number: int) -> str | None:
        try:
            import fitz
            doc = fitz.open(file_path)
            if page_number - 1 >= doc.page_count:
                doc.close()
                return None
            page = doc[page_number - 1]
            pix = page.get_pixmap(dpi=200)
            doc.close()

            client = _get_ocr()
            result = client.basicAccurate(pix.tobytes("png"), options={"language_type": "CHN_ENG"})
            if result.get("words_result"):
                lines = [w["words"] for w in result["words_result"]]
                return "\n".join(lines)
            return None
        except ImportError:
            from loguru import logger
            logger.warning("PyMuPDF(fitz) 未安装，无法对扫描件 PDF 进行 OCR")
            return None
        except Exception as e:
            from loguru import logger
            logger.warning(f"PDF 第 {page_number} 页 OCR 失败: {e}")
            return None
        return None
