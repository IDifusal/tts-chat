from typing import Optional
import redis
from app.config import settings


class CacheService:
    def __init__(self):
        self.enabled = settings.ENABLE_REDIS_CACHE
        self.redis_client = None
        
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                self.redis_client.ping()
                print("Redis cache connected")
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self.enabled = False
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            return self.redis_client.get(key)
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int = 3600):
        """Set value in cache with TTL in seconds"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str):
        """Delete value from cache"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False


_cache_service_instance = None

def get_cache_service() -> CacheService:
    global _cache_service_instance
    if _cache_service_instance is None:
        _cache_service_instance = CacheService()
    return _cache_service_instance
