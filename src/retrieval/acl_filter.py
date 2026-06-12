"""ACL 权限过滤"""

from src.infrastructure.database import async_session
from sqlalchemy import select
from src.models.permissions import UserKBPermission, DocumentPermission
from src.models.knowledge_base import KnowledgeBase
from src.models.document import Document


async def get_allowed_document_ids(user_id: str, kb_ids: list[str] | None = None) -> list[str]:
    """获取用户有权查看的文档 ID 列表"""
    allowed: set[str] = set()
    async with async_session() as db:
        # 公开知识库的文档所有人可读
        kb_query = select(KnowledgeBase.id)
        if kb_ids:
            kb_query = kb_query.where(KnowledgeBase.id.in_(kb_ids))
        kb_result = await db.execute(kb_query.where(KnowledgeBase.is_public == True))
        public_kb_ids = {r[0] for r in kb_result.all()}

        if public_kb_ids:
            doc_result = await db.execute(select(Document.id).where(Document.kb_id.in_(list(public_kb_ids))))
            allowed.update(r[0] for r in doc_result.all())

        # 用户有 KB 权限的文档
        perm_query = select(UserKBPermission.kb_id).where(UserKBPermission.user_id == user_id)
        if kb_ids:
            perm_query = perm_query.where(UserKBPermission.kb_id.in_(kb_ids))
        perm_result = await db.execute(perm_query)
        kb_perm_ids = {r[0] for r in perm_result.all()}
        if kb_perm_ids:
            doc_result = await db.execute(select(Document.id).where(Document.kb_id.in_(list(kb_perm_ids))))
            allowed.update(r[0] for r in doc_result.all())

        # 文档级白名单
        if kb_ids:
            doc_perm_result = await db.execute(
                select(DocumentPermission.document_id).where(DocumentPermission.user_id == user_id)
            )
            allowed.update(r[0] for r in doc_perm_result.all())

    return list(allowed)
