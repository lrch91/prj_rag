"""初始化种子数据：Admin 用户"""

import asyncio
import sys
sys.path.insert(0, ".")

from sqlalchemy import select
from src.infrastructure.database import async_session
from src.models.user import User
from src.security.password import hash_password


async def seed():
    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            print("admin 用户已存在，跳过。")
            return

        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            full_name="管理员",
            role="admin",
        )
        db.add(admin)
        await db.commit()
        print("admin 用户创建完成（admin / admin123）")


if __name__ == "__main__":
    asyncio.run(seed())
