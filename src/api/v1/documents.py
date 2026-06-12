"""文档管理接口（含 ACL）"""

import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.infrastructure.database import get_db
from src.models.user import User
from src.models.document import Document
from src.models.permissions import DocumentPermission
from src.services.document_service import upload_document
from src.ingestion.pipeline import ingest_document
from src.api.deps import get_current_user

_PREVIEW_SIZE_LIMIT = 50 * 1024 * 1024  # 50MB

router = APIRouter(prefix="/kbs/{kb_id}/documents", tags=["文档"])


@router.post("/upload")
async def upload(kb_id: str, background_tasks: BackgroundTasks, file: UploadFile = File(...),
                 user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        doc = await upload_document(kb_id, file, user, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    background_tasks.add_task(_run_ingestion, doc.id)
    return {"id": doc.id, "title": doc.title, "file_type": doc.file_type, "status": doc.status}


@router.get("")
async def list_docs(kb_id: str, status: str | None = None, category_id: str | None = None, tag_id: str | None = None,
                    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(Document).where(Document.kb_id == kb_id)
    if status:
        q = q.where(Document.status == status)
    if category_id:
        from src.models.permissions import DocumentCategory
        q = q.join(DocumentCategory, DocumentCategory.document_id == Document.id).where(DocumentCategory.category_id == category_id)
    if tag_id:
        from src.models.permissions import DocumentTag
        q = q.join(DocumentTag, DocumentTag.document_id == Document.id).where(DocumentTag.tag_id == tag_id)
    q = q.order_by(Document.created_at.desc())
    result = await db.execute(q)
    return [_doc_info(d) for d in result.scalars().all()]


@router.get("/{doc_id}")
async def get_doc(kb_id: str, doc_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.kb_id == kb_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return _doc_info(doc)


@router.delete("/{doc_id}")
async def delete_doc(kb_id: str, doc_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.kb_id == kb_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    # 清理 BM25
    from src.retrieval.bm25_index import bm25_index
    bm25_index.remove_document(doc_id)
    # 清理 Milvus
    from src.infrastructure.milvus_lite_client import delete_document_vectors
    delete_document_vectors(doc_id)
    # 删除文档（CASCADE 自动清理 SQLite 中的 chunks / citations / permissions）
    await db.delete(doc)
    await db.commit()
    return {"ok": True}


@router.post("/{doc_id}/update")
async def update_doc(kb_id: str, doc_id: str, background_tasks: BackgroundTasks,
                     file: UploadFile = File(...),
                     user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """上传新版本文档，清理旧数据后重新索引"""
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.kb_id == kb_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 验证文件名与原始文档一致
    new_ext = os.path.splitext(file.filename or "")[1].lower()
    old_ext = os.path.splitext(doc.title or "")[1].lower()
    if new_ext != old_ext:
        raise HTTPException(status_code=400, detail=f"文件格式不一致：原文档为 {old_ext}，新文件为 {new_ext}")

    # 验证文件格式
    mime_map = {".pdf": "application/pdf",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".md": "text/markdown", ".txt": "text/plain"}
    if new_ext not in mime_map:
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    # 清理旧索引数据
    from src.retrieval.bm25_index import bm25_index
    from src.infrastructure.milvus_lite_client import delete_document_vectors
    from src.models.document import DocumentChunk
    bm25_index.remove_document(doc_id)
    delete_document_vectors(doc_id)
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc_id))
    await db.commit()

    # 替换文件
    content = await file.read()
    with open(doc.file_path, "wb") as f:
        f.write(content)

    # 更新元数据
    doc.version = (doc.version or 0) + 1
    doc.title = file.filename or doc.title
    doc.file_size_bytes = len(content)
    doc.page_count = None
    doc.status = "pending"
    doc.error_message = None
    doc.hash_md5 = None
    await db.commit()

    # 异步重新索引
    background_tasks.add_task(_run_ingestion, doc.id)
    return {"id": doc.id, "title": doc.title, "version": doc.version, "status": doc.status}


@router.post("/{doc_id}/reindex")
async def reindex(kb_id: str, doc_id: str, background_tasks: BackgroundTasks,
                  user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.kb_id == kb_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    # 先清理旧索引数据
    from src.retrieval.bm25_index import bm25_index
    from src.infrastructure.milvus_lite_client import delete_document_vectors
    from src.models.document import DocumentChunk
    bm25_index.remove_document(doc_id)
    delete_document_vectors(doc_id)
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc_id))
    await db.commit()
    doc.status = "pending"
    await db.commit()
    background_tasks.add_task(_run_ingestion, doc.id)
    return {"ok": True, "status": "pending"}


@router.get("/{doc_id}/status")
async def doc_status(kb_id: str, doc_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.kb_id == kb_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"id": doc.id, "status": doc.status, "error_message": doc.error_message, "page_count": doc.page_count}


@router.get("/{doc_id}/file")
async def preview_doc(kb_id: str, doc_id: str, token: str | None = None, db: AsyncSession = Depends(get_db)):
    # 通过 query token 认证（新窗口打开无法设 Header）
    from src.security.jwt import decode_access_token
    user_id = None
    # 先尝试从 query param
    if token:
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
        except Exception:
            raise HTTPException(status_code=401, detail="无效 Token")
    # 再尝试从 header
    if not user_id:
        raise HTTPException(status_code=401, detail="请提供认证 Token")

    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u or not u.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    result = await db.execute(select(Document).where(Document.id == doc_id, Document.kb_id == kb_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件已丢失")
    if doc.file_size_bytes and doc.file_size_bytes > _PREVIEW_SIZE_LIMIT:
        raise HTTPException(status_code=400, detail=f"文件超过 {_PREVIEW_SIZE_LIMIT // 1024 // 1024}MB，无法在线预览")

    media_map = {
        "application/pdf": "application/pdf",
        "text/markdown": "text/plain; charset=utf-8",
        "text/html": "text/html; charset=utf-8",
        "text/plain": "text/plain; charset=utf-8",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "image/png": "image/png",
        "image/jpeg": "image/jpeg",
        "image/gif": "image/gif",
        "image/webp": "image/webp",
    }
    media_type = media_map.get(doc.file_type, "application/octet-stream")
    # PDF 和图片不加 Content-Disposition，让浏览器按 Content-Type 自行决定渲染
    return FileResponse(doc.file_path, media_type=media_type)


@router.get("/{doc_id}/text")
async def doc_text_preview(kb_id: str, doc_id: str, token: str | None = None, db: AsyncSession = Depends(get_db)):
    from src.security.jwt import decode_access_token
    if not token:
        raise HTTPException(status_code=401)
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="无效 Token")
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=401)

    result = await db.execute(select(Document).where(Document.id == doc_id, Document.kb_id == kb_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件已丢失")

    from src.ingestion.parser_registry import get_parser
    try:
        parser = get_parser(doc.file_type)
        pages = parser.parse(doc.file_path)
        text = "\n\n".join(p.text for p in pages)
        return {"title": doc.title, "file_type": doc.file_type, "content": text[:500000]}  # 截断 500KB
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {e}")


# === 文档级 ACL ===

@router.put("/{doc_id}/permissions")
async def set_doc_permissions(doc_id: str, kb_id: str, user_ids: list[str],
                               user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(DocumentPermission).where(DocumentPermission.document_id == doc_id))
    for uid in user_ids:
        db.add(DocumentPermission(document_id=doc_id, user_id=uid))
    await db.commit()
    return {"ok": True}


@router.get("/{doc_id}/permissions")
async def get_doc_permissions(doc_id: str, kb_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentPermission).where(DocumentPermission.document_id == doc_id))
    return [{"user_id": p.user_id} for p in result.scalars().all()]


async def _run_ingestion(doc_id: str):
    from src.infrastructure.database import async_session
    async with async_session() as db:
        await ingest_document(doc_id, db)


def _doc_info(d: Document) -> dict:
    return {"id": d.id, "title": d.title, "file_type": d.file_type, "status": d.status,
            "version": d.version or 1, "page_count": d.page_count, "file_size_bytes": d.file_size_bytes,
            "error_message": d.error_message, "created_at": d.created_at.isoformat()}
