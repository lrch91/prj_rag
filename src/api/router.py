"""汇总所有 API 子路由"""

from fastapi import APIRouter
from src.api.v1.auth import router as auth_router
from src.api.v1.users import router as users_router
from src.api.v1.kb import router as kb_router
from src.api.v1.documents import router as docs_router
from src.api.v1.categories import router as cat_router
from src.api.v1.qa import router as qa_router
from src.api.v1.conversations import router as conv_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(kb_router)
router.include_router(docs_router)
router.include_router(cat_router)
router.include_router(qa_router)
router.include_router(conv_router)
