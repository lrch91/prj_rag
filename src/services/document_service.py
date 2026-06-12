"""文档管理服务"""

import os
import uuid
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.document import Document
from src.models.user import User
from src.config import settings


async def upload_document(
    kb_id: str,
    file: UploadFile,
    uploaded_by: User,
    db: AsyncSession,
) -> Document:
    ext = os.path.splitext(file.filename or "")[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".md": "text/markdown",
        ".txt": "text/plain",
    }
    file_type = mime_map.get(ext)
    if file_type is None:
        raise ValueError(f"不支持的文件格式: {ext}")

    # 同名校验：同一 KB 内不允许重复文件名
    existing = (await db.execute(
        select(Document).where(Document.kb_id == kb_id, Document.title == file.filename)
    )).scalar_one_or_none()
    if existing:
        raise ValueError(f"知识库中已存在同名文档「{file.filename}」(v{existing.version or 1})，请使用版本更新功能上传新版本")

    # 保存文件
    doc_id = str(uuid.uuid4())
    save_name = f"{doc_id}{ext}"
    save_path = os.path.join(settings.upload_dir, save_name)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # 创建文档记录
    doc = Document(
        id=doc_id,
        kb_id=kb_id,
        title=file.filename or "untitled",
        file_type=file_type,
        file_path=save_path,
        file_size_bytes=len(content),
        status="pending",
        uploaded_by=uploaded_by.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def list_documents(kb_id: str, db: AsyncSession) -> list[Document]:
    result = await db.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())
