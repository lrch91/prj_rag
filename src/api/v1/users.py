"""用户管理接口（Admin）"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.database import get_db
from src.models.user import User
from src.security.password import hash_password
from src.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("")
async def list_users(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return [
        {"id": u.id, "username": u.username, "email": u.email, "full_name": u.full_name,
         "role": u.role, "is_active": u.is_active, "created_at": u.created_at.isoformat()}
        for u in result.scalars().all()
    ]


@router.post("")
async def create_user(username: str, email: str, password: str, full_name: str | None = None, role: str = "viewer",
                      admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=username, email=email, hashed_password=hash_password(password),
        full_name=full_name, role=role,
    )
    db.add(user)
    await db.commit()
    return {"id": user.id, "username": user.username, "role": user.role}


@router.put("/{user_id}")
async def update_user(user_id: str, role: str | None = None, is_active: bool | None = None,
                      admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if role:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    await db.commit()
    return {"ok": True}


@router.delete("/{user_id}")
async def deactivate_user(user_id: str, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = False
    await db.commit()
    return {"ok": True}
