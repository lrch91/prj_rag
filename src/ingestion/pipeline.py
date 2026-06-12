"""文档摄入管道：流式解析 -> 分批 Embedding -> 分批写入（支持 500MB+ 大文档）"""

import os
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.document import Document, DocumentChunk
from src.ingestion.parser_registry import get_parser
from src.ingestion.chunker import chunk_text
from src.ingestion.embedder import embed_texts
from src.retrieval.vector_store import insert_vectors

_BATCH_SIZE = 32  # 每批嵌入 32 条，智谱限制 64，留余量


async def ingest_document(document_id: str, db: AsyncSession) -> None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        return

    try:
        doc.status = "parsing"
        await db.commit()

        # MD5
        if os.path.exists(doc.file_path):
            with open(doc.file_path, "rb") as f:
                doc.hash_md5 = hashlib.md5(f.read()).hexdigest()

        # 解析
        parser = get_parser(doc.file_type)
        pages = parser.parse(doc.file_path)
        doc.page_count = len(pages)
        doc.status = "indexing"
        await db.commit()

        # 流式处理：逐页分块 → 累积 → 批嵌入 → 批写入
        chunk_buf: list[tuple[dict, str]] = []  # [(chunk_record_fields, chunk_text), ...]
        chunk_index = 0
        bm25_buf: list[dict] = []

        async def _flush_batch():
            nonlocal chunk_index
            if not chunk_buf:
                return
            fields_list, texts = zip(*chunk_buf)
            embeddings = embed_texts(list(texts), batch_size=_BATCH_SIZE)

            milvus_data = []
            chunk_records = []
            for fields, emb in zip(fields_list, embeddings):
                chunk_index += 1
                cid = f"{doc.id}_{chunk_index}"
                chunk_records.append(DocumentChunk(
                    document_id=doc.id, chunk_index=chunk_index,
                    chunk_text=fields["text"],
                    page_start=fields["page"], page_end=fields["page"],
                    section_path=fields.get("section_path"),
                    content_type=fields.get("content_type", "prose"),
                    token_count=fields["tokens"],
                ))
                milvus_data.append({"chunk_id": cid, "kb_id": doc.kb_id, "document_id": doc.id,
                                    "chunk_text": fields["text"], "vector": emb})
                bm25_buf.append({"chunk_id": cid, "text": fields["text"], "document_id": doc.id, "kb_id": doc.kb_id})

            db.add_all(chunk_records)
            await db.commit()

            mids = insert_vectors(milvus_data)
            for rec, mid in zip(chunk_records, mids):
                rec.milvus_id = mid
            await db.commit()

            chunk_buf.clear()

        for page in pages:
            for ch in chunk_text(page.text, page_number=page.page_number,
                                 chunk_size=doc.chunk_size if hasattr(doc, 'chunk_size') else 500,
                                 chunk_overlap=doc.chunk_overlap if hasattr(doc, 'chunk_overlap') else 60,
                                 file_type=doc.file_type):
                chunk_buf.append(({
                    "text": ch.text, "page": ch.page_start, "tokens": ch.token_count,
                    "section_path": ch.section_path, "content_type": ch.content_type,
                }, ch.text))
                if len(chunk_buf) >= _BATCH_SIZE:
                    await _flush_batch()

        # 收尾
        await _flush_batch()

        if chunk_index == 0:
            doc.status = "error"
            doc.error_message = "文档解析后无有效文本"
            await db.commit()
            return

        # BM25
        from src.retrieval.bm25_index import bm25_index
        bm25_index.add_chunks(bm25_buf)

        doc.status = "ready"
        await db.commit()

    except Exception as e:
        doc.status = "error"
        doc.error_message = str(e)
        await db.commit()
