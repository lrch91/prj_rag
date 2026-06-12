"""知识库管理服务"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.knowledge_base import KnowledgeBase
from src.models.user import User


async def create_kb(name: str, description: str | None, created_by: User, db: AsyncSession) -> KnowledgeBase:
    kb = KnowledgeBase(
        name=name,
        description=description,
        created_by=created_by.id,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return kb


async def list_kbs(db: AsyncSession, user: User) -> list[KnowledgeBase]:
    if user.role == "admin":
        result = await db.execute(select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()))
        return list(result.scalars().all())
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.created_by == user.id).order_by(KnowledgeBase.created_at.desc())
    )
    return list(result.scalars().all())
