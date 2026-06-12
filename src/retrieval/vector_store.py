"""Milvus Lite 向量存储 - 检索与写入"""

from dataclasses import dataclass
from src.infrastructure.milvus_lite_client import get_milvus_client, COLLECTION_NAME


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    score: float
    document_id: str
    kb_id: str


def insert_vectors(chunks: list[dict]) -> list[int]:
    """
    批量插入向量
    chunks: [{"chunk_id": "...", "kb_id": "...", "document_id": "...", "chunk_text": "...", "embedding": [...]}, ...]
    返回 Milvus auto_id 列表
    """
    if not chunks:
        return []
    client = get_milvus_client()
    result = client.insert(collection_name=COLLECTION_NAME, data=chunks)
    return result["ids"]


def search_vectors(
    query_vector: list[float],
    kb_ids: list[str] | None = None,
    top_k: int = 10,
) -> list[SearchResult]:
    client = get_milvus_client()
    filter_expr = None
    if kb_ids:
        ids_csv = ", ".join(f'"{k}"' for k in kb_ids)
        filter_expr = f'kb_id in [{ids_csv}]'

    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vector],
        limit=top_k,
        filter=filter_expr,
        output_fields=["chunk_id", "chunk_text", "document_id", "kb_id"],
    )
    if not results or not results[0]:
        return []

    return [
        SearchResult(
            chunk_id=hit["entity"].get("chunk_id", ""),
            text=hit["entity"].get("chunk_text", ""),
            score=hit["distance"],
            document_id=hit["entity"].get("document_id", ""),
            kb_id=hit["entity"].get("kb_id", ""),
        )
        for hit in results[0]
    ]
