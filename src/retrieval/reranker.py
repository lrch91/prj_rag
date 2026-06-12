"""智谱 bge-reranker-large API 重排序"""

from src.config import settings


def rerank(query: str, documents: list[str], top_n: int = 10) -> list[tuple[int, float]]:
    """对候选文档重排序，返回 [(原始索引, 相关度分数), ...] 按分数降序"""
    if not documents:
        return []
    import requests
    headers = {
        "Authorization": f"Bearer {settings.zhipuai_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "rerank",
        "query": query,
        "documents": documents,
        "top_n": min(top_n, len(documents)),
    }
    resp = requests.post(
        "https://open.bigmodel.cn/api/paas/v4/rerank",
        headers=headers,
        json=body,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    return [(r["index"], r["relevance_score"]) for r in sorted(results, key=lambda x: x["relevance_score"], reverse=True)]
