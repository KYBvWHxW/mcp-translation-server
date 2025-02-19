from typing import Any, Optional
import time
from collections import OrderedDict
import threading

class CacheEntry:
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl
        
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl

class Cache:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()
        self._lock = threading.Lock()
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        with self._lock:
            if key not in self._cache:
                return None
                
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return None
                
            # 更新访问顺序
            self._cache.move_to_end(key)
            return entry.value
            
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存项"""
        with self._lock:
            # 如果缓存已满，移除最早的项
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                
            self._cache[key] = CacheEntry(value, ttl or self.ttl)
            
    def delete(self, key: str) -> None:
        """删除缓存项"""
        with self._lock:
            self._cache.pop(key, None)
            
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            
    def cleanup(self) -> None:
        """清理过期的缓存项"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
