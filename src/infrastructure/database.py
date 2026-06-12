"""SQLite 异步连接"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

import sqlite3
from sqlalchemy import event

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def _enable_sqlite_fk(dbapi_connection, connection_record):
    """每个新连接都开启外键约束（不影响 ORM 元数据）"""
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.execute("PRAGMA foreign_keys = ON")


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """创建所有表（开发用，后续替换为 Alembic）"""
    async with engine.begin() as conn:
        from src.models.user import User  # noqa: F401
        from src.models.knowledge_base import KnowledgeBase  # noqa: F401
        from src.models.document import Document, DocumentChunk  # noqa: F401
        from src.models.conversation import Conversation, Message, MessageCitation  # noqa: F401
        from src.models.permissions import UserKBPermission, DocumentPermission, Category, Tag, DocumentCategory, DocumentTag  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
        # SQLite 必须显式开启外键约束，否则 CASCADE DELETE 不生效
        await conn.execute(text("PRAGMA foreign_keys = ON"))
    await engine.dispose()
