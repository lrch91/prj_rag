"""解析器注册表：按 MIME 分发，仅支持 PDF / DOCX / MD / TXT"""

from .parsers.base import BaseParser
from .parsers.pdf_parser import PDFParser
from .parsers.docx_parser import DocxParser
from .parsers.markdown_parser import MarkdownParser
from .parsers.txt_parser import TxtParser

_PARSER_MAP: dict[str, BaseParser] = {
    "application/pdf": PDFParser(),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser(),
    "text/markdown": MarkdownParser(),
    "text/plain": TxtParser(),
    "text/txt": TxtParser(),
}


def get_parser(file_type: str) -> BaseParser:
    parser = _PARSER_MAP.get(file_type)
    if parser is None:
        raise ValueError(f"不支持的文件类型: {file_type}")
    return parser


def supported_types() -> list[str]:
    return list(_PARSER_MAP.keys())
