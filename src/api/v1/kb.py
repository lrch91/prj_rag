"""知识库接口（含权限管理）"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.infrastructure.database import get_db
from src.models.user import User
from src.models.knowledge_base import KnowledgeBase
from src.models.permissions import UserKBPermission
from src.api.deps import get_current_user

router = APIRouter(prefix="/kbs", tags=["知识库"])


@router.post("")
async def create(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                 name: str = Query(...), description: str | None = None):
    kb = KnowledgeBase(name=name, description=description, created_by=user.id)
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    # 创建者自动获得管理权限
    db.add(UserKBPermission(user_id=user.id, kb_id=kb.id, permission="admin", granted_by=user.id))
    await db.commit()
    return {"id": kb.id, "name": kb.name, "description": kb.description, "created_at": kb.created_at.isoformat()}


@router.get("")
async def list_kbs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role == "admin":
        result = await db.execute(select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()))
        return [_kb_info(k) for k in result.scalars().all()]
    # 普通用户：只看有权限的
    perm_result = await db.execute(select(UserKBPermission.kb_id).where(UserKBPermission.user_id == user.id))
    kb_ids = [p[0] for p in perm_result.all()]
    if not kb_ids:
        return []
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id.in_(kb_ids)))
    return [_kb_info(k) for k in result.scalars().all()]


@router.get("/{kb_id}")
async def get_kb(kb_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    kb = await _get_kb_or_404(kb_id, db)
    return _kb_info(kb)


@router.put("/{kb_id}")
async def update_kb(kb_id: str, name: str, description: str | None = None,
                     user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    kb = await _get_kb_or_404(kb_id, db)
    kb.name = name
    kb.description = description
    await db.commit()
    return _kb_info(kb)


@router.delete("/{kb_id}")
async def delete_kb(kb_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    kb = await _get_kb_or_404(kb_id, db)
    await db.delete(kb)
    await db.commit()
    return {"ok": True}


@router.post("/{kb_id}/permissions")
async def grant_permission(kb_id: str, target_user_id: str, permission: str = "read",
                            user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _get_kb_or_404(kb_id, db)
    existing = await db.execute(
        select(UserKBPermission).where(UserKBPermission.kb_id == kb_id, UserKBPermission.user_id == target_user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="权限已存在")
    db.add(UserKBPermission(user_id=target_user_id, kb_id=kb_id, permission=permission, granted_by=user.id))
    await db.commit()
    return {"ok": True}


@router.delete("/{kb_id}/permissions/{target_user_id}")
async def revoke_permission(kb_id: str, target_user_id: str,
                             user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(UserKBPermission).where(
        UserKBPermission.kb_id == kb_id, UserKBPermission.user_id == target_user_id))
    await db.commit()
    return {"ok": True}


@router.get("/{kb_id}/permissions")
async def list_permissions(kb_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserKBPermission).where(UserKBPermission.kb_id == kb_id))
    return [{"user_id": p.user_id, "permission": p.permission} for p in result.scalars().all()]


async def _get_kb_or_404(kb_id: str, db: AsyncSession) -> KnowledgeBase:
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


def _kb_info(kb: KnowledgeBase) -> dict:
    return {"id": kb.id, "name": kb.name, "description": kb.description, "created_at": kb.created_at.isoformat()}
