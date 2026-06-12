"""BM25 关键词检索索引（内存）"""

import jieba
from rank_bm25 import BM25Okapi
from dataclasses import dataclass


@dataclass
class BM25Hit:
    chunk_id: str
    text: str
    score: float
    document_id: str
    kb_id: str


class BM25Index:
    def __init__(self):
        self._documents: list[dict] = []  # [{chunk_id, text, document_id, kb_id}, ...]
        self._bm25: BM25Okapi | None = None
        self._tokenized: list[list[str]] = []

    def add_chunks(self, chunks: list[dict]):
        """增量添加 chunk。每个 chunk: {chunk_id, text, document_id, kb_id}"""
        self._documents.extend(chunks)
        for c in chunks:
            self._tokenized.append(_tokenize(c["text"]))
        if self._tokenized:
            self._bm25 = BM25Okapi(self._tokenized)

    def remove_document(self, document_id: str):
        self._documents = [d for d in self._documents if d["document_id"] != document_id]
        self._rebuild()

    def search(self, query: str, kb_ids: list[str] | None = None, top_k: int = 10) -> list[BM25Hit]:
        if self._bm25 is None:
            return []
        tokens = _tokenize(query)
        scores = self._bm25.get_scores(tokens)
        hits: list[BM25Hit] = []
        for idx, score in enumerate(scores):
            if score <= 0:
                continue
            doc = self._documents[idx]
            if kb_ids and doc["kb_id"] not in kb_ids:
                continue
            hits.append(BM25Hit(
                chunk_id=doc["chunk_id"],
                text=doc["text"],
                score=float(score),
                document_id=doc["document_id"],
                kb_id=doc["kb_id"],
            ))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]

    def _rebuild(self):
        self._tokenized = [_tokenize(d["text"]) for d in self._documents]
        if self._tokenized:
            self._bm25 = BM25Okapi(self._tokenized)
        else:
            self._bm25 = None

    def get_all_docs(self) -> list[dict]:
        return self._documents


def _tokenize(text: str) -> list[str]:
    return [t for t in jieba.cut(text) if t.strip()]


# 全局单例
bm25_index = BM25Index()
