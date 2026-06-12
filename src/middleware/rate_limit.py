"""速率限制中间件（内存计数器）"""

import time
from collections import defaultdict
from fastapi import Request, Response

# 每用户每分钟最多 30 次请求
_RATE_LIMIT = 300
_WINDOW = 60
_counter: dict[str, list[float]] = defaultdict(list)


async def rate_limit_middleware(request: Request, call_next):
    user_id = "anonymous"
    # 尝试从 Authorization header 提取用户
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from src.security.jwt import decode_access_token
            payload = decode_access_token(auth[7:])
            user_id = payload.get("sub", "anonymous")
        except Exception:
            from loguru import logger
            logger.debug("JWT 解析失败，降级为 anonymous 限流", exc_info=True)

    now = time.time()
    window_start = now - _WINDOW
    _counter[user_id] = [t for t in _counter[user_id] if t > window_start]

    if len(_counter[user_id]) >= _RATE_LIMIT:
        return Response(content='{"detail":"请求频率过高，请稍后再试"}', status_code=429, media_type="application/json")

    _counter[user_id].append(now)
    return await call_next(request)
