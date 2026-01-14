from __future__ import annotations

from app.cache.cache_manager import CacheManager

# 全域 singleton，避免每次 import 都建立新快取實例
cache_manager = CacheManager()










