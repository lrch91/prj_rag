"""FastAPI 应用入口"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from loguru import logger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

from src.config import settings
from src.infrastructure.milvus_lite_client import init_milvus


def _setup_logging():
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()  # 移除默认 stderr sink

    # 控制台输出（开发时方便）
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # 全量日志文件（按大小轮转，保留 N 天）
    logger.add(
        log_dir / "app.log",
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        encoding="utf-8",
        enqueue=True,  # 多进程安全
        backtrace=True,
        diagnose=True,
    )

    # 错误日志单独文件
    logger.add(
        log_dir / "error.log",
        level="ERROR",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # 桥接标准 logging → loguru（让 SQLAlchemy / uvicorn 日志也写入文件）
    class _InterceptHandler(logging.Handler):
        def emit(self, record):
            level = record.levelname.upper()
            logger.opt(depth=6, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    # 降低第三方库日志噪点
    for name in ["httpx", "httpcore", "urllib3", "openai", "aiohttp"]:
        logging.getLogger(name).setLevel(logging.WARNING)

    logger.info("日志系统初始化完成: 全量={}, 错误={}", log_dir / "app.log", log_dir / "error.log")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_logging()
    init_milvus()
    yield


app = FastAPI(title=settings.app_name, version="0.4.0", lifespan=lifespan)

# 中间件（后加的先执行）
from src.middleware.rate_limit import rate_limit_middleware  # noqa: E402
from src.middleware.logging_middleware import logging_middleware  # noqa: E402

app.middleware("http")(rate_limit_middleware)
app.middleware("http")(logging_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 前端静态文件
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
_static_exists = os.path.exists(os.path.join(FRONTEND_DIST, "assets"))

from src.api.router import router as api_router  # noqa: E402
app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/v1/models")
async def list_models():
    return {"models": settings.get_available_models(), "default": settings.default_llm_model}


@app.get("/api/v1/admin/stats")
async def stats():
    from src.infrastructure.database import async_session
    from sqlalchemy import text
    async with async_session() as db:
        doc_count = (await db.execute(text("SELECT COUNT(*) FROM documents"))).scalar()
        chunk_count = (await db.execute(text("SELECT COUNT(*) FROM document_chunks"))).scalar()
        user_count = (await db.execute(text("SELECT COUNT(*) FROM users"))).scalar()
        kb_count = (await db.execute(text("SELECT COUNT(*) FROM knowledge_bases"))).scalar()
    from src.retrieval.query_cache import _cache as qc
    return {
        "documents": doc_count,
        "chunks": chunk_count,
        "users": user_count,
        "kbs": kb_count,
        "cache_entries": len(qc),
    }


if _static_exists:
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("health"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Not Found"}, status_code=404)


@app.get("/")
async def index():
    if _static_exists:
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
    return {"status": "ok", "app": settings.app_name}
