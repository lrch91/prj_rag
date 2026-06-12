"""Q&A 请求/响应 Schema"""

from pydantic import BaseModel


class QARequest(BaseModel):
    question: str
    kb_ids: list[str] | None = None
    model: str = "deepseek-v4-pro"
    conversation_id: str | None = None


class CitationItem(BaseModel):
    source_index: int
    document_id: str
    document_title: str = ""
    kb_name: str = ""
    page: int | None = None
    section_path: str | None = None
    content_type: str = "prose"
    snippet: str
    relevance_score: float


class QAResponse(BaseModel):
    answer: str
    conversation_id: str | None = None
    message_id: str | None = None
    model: str | None = None
    tokens: dict | None = None
    citations: list[CitationItem] = []
