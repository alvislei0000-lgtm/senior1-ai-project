"""
快取管理器
預設快取 24 小時，支援手動刷新，熱門項目可縮短快取時間
"""
import json
import os
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import hashlib

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class CacheManager:
    """快取管理器，支援 Redis 或記憶體快取"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.use_redis = False
        
        # 快取設定
        self.default_ttl_hours = int(os.getenv("CACHE_TTL_HOURS", "24"))
        self.hot_ttl_hours = int(os.getenv("CACHE_HOT_TTL_HOURS", "1"))
    
    async def initialize(self):
        """初始化快取系統"""
        # 嘗試連接 Redis
        if REDIS_AVAILABLE:
            try:
                redis_host = os.getenv("REDIS_HOST", "localhost")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))
                redis_db = int(os.getenv("REDIS_DB", "0"))
                
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True
                )
                # 測試連接
                self.redis_client.ping()
                self.use_redis = True
                print("使用 Redis 快取")
            except Exception as e:
                print(f"無法連接 Redis，使用記憶體快取: {e}")
                self.use_redis = False
        else:
            print("Redis 未安裝，使用記憶體快取")
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """生成快取鍵"""
        # 將參數排序後序列化
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}:{params_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """取得快取資料"""
        if self.use_redis and self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    parsed = json.loads(data)
                    # 向後相容：舊版本可能把資料包在 {"data": ..., "expires_at": ...}
                    if isinstance(parsed, dict) and "data" in parsed and "expires_at" in parsed:
                        return parsed.get("data")
                    return parsed
            except Exception as e:
                print(f"Redis 取得失敗: {e}")
        
        # 使用記憶體快取
        if key in self.memory_cache:
            cache_item = self.memory_cache[key]
            # 檢查是否過期
            if datetime.fromisoformat(cache_item["expires_at"]) > datetime.now():
                return cache_item["data"]
            else:
                # 過期，刪除
                del self.memory_cache[key]
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_hours: Optional[int] = None,
        is_hot: bool = False
    ):
        """設定快取資料"""
        # 決定 TTL
        if ttl_hours is None:
            ttl_hours = self.hot_ttl_hours if is_hot else self.default_ttl_hours
        
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    ttl_hours * 3600,  # 轉換為秒
                    # Redis 本身已經有 TTL，不需要額外包一層 expires_at
                    json.dumps(value)
                )
                return
            except Exception as e:
                print(f"Redis 設定失敗: {e}")
        
        # 使用記憶體快取
        self.memory_cache[key] = {
            "data": value,
            "expires_at": expires_at.isoformat()
        }
        
        # 清理過期項目（簡單實作，實際應使用更高效的方式）
        if len(self.memory_cache) > 1000:
            self._cleanup_expired()
    
    async def delete(self, key: str):
        """刪除快取"""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                print(f"Redis 刪除失敗: {e}")
        
        if key in self.memory_cache:
            del self.memory_cache[key]
    
    async def refresh(self, key: str):
        """手動刷新快取（刪除）"""
        await self.delete(key)
    
    def _cleanup_expired(self):
        """清理過期的記憶體快取項目"""
        now = datetime.now()
        expired_keys = [
            key for key, item in self.memory_cache.items()
            if datetime.fromisoformat(item["expires_at"]) <= now
        ]
        for key in expired_keys:
            del self.memory_cache[key]
    
    async def close(self):
        """關閉快取連接"""
        if self.redis_client:
            self.redis_client.close()


