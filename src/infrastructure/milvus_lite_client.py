"""Milvus 向量存储（本地 Lite 或 Zilliz Cloud）"""

from pymilvus import MilvusClient
from src.config import settings

_client: MilvusClient | None = None
COLLECTION_NAME = "rag_chunks"
EMBEDDING_DIM = settings.embedding_dimensions


def get_milvus_client() -> MilvusClient:
    global _client
    if _client is None:
        if settings.milvus_mode == "cloud":
            _client = MilvusClient(uri=settings.zilliz_uri, token=settings.zilliz_token)
        else:
            _client = MilvusClient(settings.milvus_db_path)
        _ensure_collection()
    return _client


def _ensure_collection():
    if not _client.has_collection(COLLECTION_NAME):
        _client.create_collection(
            collection_name=COLLECTION_NAME,
            dimension=EMBEDDING_DIM,
            metric_type="COSINE",
            auto_id=True,
        )
    _client.load_collection(COLLECTION_NAME)


def delete_document_vectors(document_id: str) -> int:
    """删除指定文档的所有向量，返回删除条数"""
    client = get_milvus_client()
    res = client.delete(collection_name=COLLECTION_NAME, filter=f'document_id == "{document_id}"')
    return len(res) if res else 0


def init_milvus():
    """启动时初始化 Milvus"""
    get_milvus_client()
