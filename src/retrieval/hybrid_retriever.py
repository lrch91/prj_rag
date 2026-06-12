"""混合检索：向量 + BM25 → RRF 融合 → Reranker → ACL 过滤"""

from src.ingestion.embedder import embed_texts
from src.retrieval.vector_store import search_vectors
from src.retrieval.bm25_index import bm25_index
from src.retrieval.reranker import rerank


async def hybrid_search(
    query: str,
    user_id: str | None = None,
    kb_ids: list[str] | None = None,
    top_k: int = 10,
    use_reranker: bool = False,
) -> list[dict]:
    acl_doc_ids: set[str] | None = None
    if user_id:
        from src.retrieval.acl_filter import get_allowed_document_ids
        ids = await get_allowed_document_ids(user_id, kb_ids)
        acl_doc_ids = set(ids)

    results: list[dict] = []

    # 1. 向量检索
    query_vecs = embed_texts([query])
    if query_vecs:
        vector_hits = search_vectors(query_vecs[0], kb_ids=kb_ids, top_k=50)
        results.extend([
            {"chunk_id": h.chunk_id, "text": h.text, "document_id": h.document_id,
             "kb_id": h.kb_id, "score": h.score, "source": "vector"}
            for h in vector_hits
        ])

    # 2. BM25 检索
    bm25_hits = bm25_index.search(query, kb_ids=kb_ids, top_k=50)
    results.extend([
        {"chunk_id": h.chunk_id, "text": h.text, "document_id": h.document_id,
         "kb_id": h.kb_id, "score": h.score, "source": "bm25"}
        for h in bm25_hits
    ])

    # 3. RRF 融合
    fused = _rrf_fusion(results, k=60)

    # 4. ACL 过滤
    if acl_doc_ids:
        fused = [r for r in fused if r["document_id"] in acl_doc_ids]

    # 5. Reranker（可选）
    if use_reranker and len(fused) > top_k:
        candidates = [r["text"] for r in fused[:20]]
        ranked = rerank(query, candidates, top_n=top_k)
        fused = [fused[i] for i, score in ranked]
        for r, (_, score) in zip(fused, ranked):
            r["score"] = score  # 替换为 Reranker 精排分数
            r["source"] = "reranker"

    return fused[:top_k]


def _rrf_fusion(results: list[dict], k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion"""
    dedup: dict[str, dict] = {}
    for rank, r in enumerate(results):
        key = r["chunk_id"]
        rrf_score = 1.0 / (k + rank + 1)
        if key in dedup:
            dedup[key]["score"] += rrf_score
        else:
            r["score"] = rrf_score
            dedup[key] = r
    merged = list(dedup.values())
    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged
