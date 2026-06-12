"""对话管理接口"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database import get_db
from src.models.user import User
from src.models.conversation import Conversation, Message, MessageCitation
from src.api.deps import get_current_user

router = APIRouter(prefix="/conversations", tags=["对话"])


@router.post("")
async def create_conversation(
    kb_id: str | None = None,
    model_name: str = "deepseek-v4-pro",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = Conversation(user_id=user.id, kb_id=kb_id, model_name=model_name)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return {"id": conv.id, "title": conv.title, "model_name": conv.model_name, "created_at": conv.created_at.isoformat()}


@router.get("")
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc()).limit(50)
    )
    convs = result.scalars().all()
    return [
        {"id": c.id, "title": c.title or "新对话", "model_name": c.model_name, "created_at": c.created_at.isoformat()}
        for c in convs
    ]


@router.get("/{conv_id}")
async def get_conversation(
    conv_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from src.models.document import Document
    from src.models.knowledge_base import KnowledgeBase

    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="对话不存在")
    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    # 收集所有消息的引用
    msg_ids = [m.id for m in messages if m.role == "assistant"]
    citations_by_msg: dict[str, list] = {mid: [] for mid in msg_ids}
    if msg_ids:
        cit_rows = (await db.execute(
            select(MessageCitation).where(MessageCitation.message_id.in_(msg_ids))
        )).scalars().all()

        doc_ids = list({c.document_id for c in cit_rows})
        kb_ids: list[str] = []
        doc_map: dict[str, str] = {}
        doc_kb_map: dict[str, str] = {}
        if doc_ids:
            doc_rows = (await db.execute(
                select(Document.id, Document.title, Document.kb_id).where(Document.id.in_(doc_ids))
            )).all()
            doc_map = {row[0]: row[1] for row in doc_rows}
            doc_kb_map = {row[0]: row[2] for row in doc_rows}
            kb_ids = list({row[2] for row in doc_rows if row[2]})

        kb_map: dict[str, str] = {}
        if kb_ids:
            kb_rows = (await db.execute(
                select(KnowledgeBase.id, KnowledgeBase.name).where(KnowledgeBase.id.in_(kb_ids))
            )).all()
            kb_map = {row[0]: row[1] for row in kb_rows}

        for c in cit_rows:
            idx = len(citations_by_msg[c.message_id]) + 1
            citations_by_msg[c.message_id].append({
                "source_index": idx,
                "document_id": c.document_id,
                "document_title": doc_map.get(c.document_id, ""),
                "kb_name": kb_map.get(doc_kb_map.get(c.document_id, ""), ""),
                "page": c.page_number,
                "snippet": c.snippet or "",
                "relevance_score": c.relevance_score or 0,
            })

    return {
        "id": conv.id,
        "title": conv.title,
        "model_name": conv.model_name,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
                "citations": citations_by_msg.get(m.id, []),
            }
            for m in messages
        ],
    }


@router.delete("/{conv_id}")
async def delete_conversation(
    conv_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="对话不存在")
    await db.delete(conv)
    await db.commit()
    return {"ok": True}
