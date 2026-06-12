"""查询缓存（内存 LRU，免 Redis）"""

import hashlib
import time
from collections import OrderedDict

_MAX_SIZE = 100
_TTL_SECONDS = 600  # 10 分钟

_cache: OrderedDict[str, tuple[float, dict]] = OrderedDict()


def _cache_key(question: str, kb_ids: list[str]) -> str:
    raw = question + "|" + ",".join(sorted(kb_ids or []))
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached(question: str, kb_ids: list[str]) -> dict | None:
    key = _cache_key(question, kb_ids)
    if key not in _cache:
        return None
    ts, val = _cache[key]
    if time.time() - ts > _TTL_SECONDS:
        del _cache[key]
        return None
    # 移到末尾（最近使用）
    _cache.move_to_end(key)
    return val


def set_cache(question: str, kb_ids: list[str], result: dict):
    key = _cache_key(question, kb_ids)
    _cache[key] = (time.time(), result)
    _cache.move_to_end(key)
    if len(_cache) > _MAX_SIZE:
        _cache.popitem(last=False)


def clear_cache():
    _cache.clear()
