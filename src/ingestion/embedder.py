"""智谱 Embedding-3 API 封装"""

from zhipuai import ZhipuAI
from src.config import settings

_client: ZhipuAI | None = None
MODEL = "embedding-3"


def _get_client() -> ZhipuAI:
    global _client
    if _client is None:
        _client = ZhipuAI(api_key=settings.zhipuai_api_key)
    return _client


def embed_texts(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    if not texts:
        return []
    client = _get_client()
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = client.embeddings.create(
            model=MODEL,
            input=batch,
            dimensions=settings.embedding_dimensions,
        )
        all_embeddings.extend(d.embedding for d in sorted(resp.data, key=lambda x: x.index))
    return all_embeddings
