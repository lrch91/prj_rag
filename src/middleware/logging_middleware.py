"""请求日志中间件"""

import time
from loguru import logger
from fastapi import Request


async def logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = (time.time() - start) * 1000
    logger.info(
        "{} {} → {} ({:.0f}ms)",
        request.method, request.url.path, response.status_code, elapsed,
    )
    return response
