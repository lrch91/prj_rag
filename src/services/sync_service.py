"""文档自动同步服务：MD5 变更检测 + 自动重索引"""

import os
import hashlib
from loguru import logger
from sqlalchemy import select
from src.infrastructure.database import async_session
from src.models.document import Document


async def check_and_sync():
    """检查所有文档的 MD5，如有变更自动重索引"""
    async with async_session() as db:
        result = await db.execute(select(Document).where(Document.status == "ready"))
        docs = result.scalars().all()

        for doc in docs:
            if not os.path.exists(doc.file_path):
                logger.warning("文档文件不存在: {}", doc.file_path)
                continue

            with open(doc.file_path, "rb") as f:
                new_hash = hashlib.md5(f.read()).hexdigest()

            if new_hash != doc.hash_md5:
                logger.info("检测到文档变更，触发重索引: {} ({})", doc.title, doc.id)
                doc.hash_md5 = new_hash
                doc.status = "pending"
                await db.commit()
                # 触发重新摄入
                from src.ingestion.pipeline import ingest_document
                await ingest_document(doc.id, db)

    logger.info("自动同步检查完成")
