from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import json
import os
from collections import OrderedDict
import numpy as np

@dataclass
class CacheItem:
    """缓存项"""
    key: str
    value: Any
    expiry: Optional[datetime]
    access_count: int = 0
    last_access: datetime = datetime.now()
    size: int = 0

class CacheConfig:
    """缓存配置"""
    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: int = 512,
        default_ttl: Optional[timedelta] = timedelta(hours=1),
        cleanup_interval: timedelta = timedelta(minutes=5)
    ):
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval

class CacheManager:
    """高级缓存管理器"""
    
    def __init__(
        self,
        config: CacheConfig,
        persist_dir: Optional[str] = None
    ):
        self.config = config
        self.persist_dir = persist_dir
        
        # 缓存存储
        self._cache: Dict[str, CacheItem] = OrderedDict()
        self._size_cache: Dict[str, int] = {}
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'memory_usage': 0
        }
        
        # 线程同步
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        
        # 启动清理线程
        self._start_cleanup_thread()
        
        # 加载持久化数据
        if persist_dir:
            self._load_persistent_data()
            
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_task():
            while not self._stop_cleanup.is_set():
                self._cleanup_expired()
                self._stop_cleanup.wait(
                    self.config.cleanup_interval.total_seconds()
                )
                
        self._cleanup_thread = threading.Thread(
            target=cleanup_task,
            daemon=True
        )
        self._cleanup_thread.start()
        
    def _cleanup_expired(self):
        """清理过期项目"""
        now = datetime.now()
        with self._lock:
            expired_keys = [
                key for key, item in self._cache.items()
                if item.expiry and item.expiry <= now
            ]
            for key in expired_keys:
                self._remove_item(key)
                
    def _calculate_item_size(self, value: Any) -> int:
        """计算项目大小（字节）"""
        return len(json.dumps(value, ensure_ascii=False).encode('utf-8'))
        
    def _remove_item(self, key: str):
        """移除缓存项"""
        if key in self._cache:
            item = self._cache[key]
            self.stats['memory_usage'] -= item.size
            del self._cache[key]
            del self._size_cache[key]
            self.stats['evictions'] += 1
            
    def _evict_items(self, required_space: int):
        """驱逐缓存项"""
        if not self._cache:
            return
            
        # 计算得分并排序
        items_scores = []
        for key, item in self._cache.items():
            # 使用改进的 LRU-K 算法
            time_factor = (datetime.now() - item.last_access).total_seconds()
            frequency_factor = np.log1p(item.access_count)
            size_factor = item.size / 1024  # KB
            
            # 计算综合得分
            score = (time_factor * size_factor) / frequency_factor
            items_scores.append((key, score))
            
        # 按得分降序排序
        items_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 驱逐项目直到空间足够
        freed_space = 0
        for key, _ in items_scores:
            item = self._cache[key]
            freed_space += item.size
            self._remove_item(key)
            
            if freed_space >= required_space:
                break
                
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        priority: int = 0
    ):
        """设置缓存项"""
        with self._lock:
            # 计算过期时间
            expiry = None
            if ttl or self.config.default_ttl:
                expiry = datetime.now() + (ttl or self.config.default_ttl)
                
            # 计算项目大小
            size = self._calculate_item_size(value)
            
            # 检查内存限制
            if size > self.config.max_memory_mb * 1024 * 1024:
                raise ValueError("缓存项太大")
                
            # 确保有足够空间
            required_space = (
                size - self._cache[key].size
                if key in self._cache
                else size
            )
            
            if (self.stats['memory_usage'] + required_space >
                self.config.max_memory_mb * 1024 * 1024):
                self._evict_items(required_space)
                
            # 更新或添加项目
            if key in self._cache:
                item = self._cache[key]
                self.stats['memory_usage'] -= item.size
                item.value = value
                item.expiry = expiry
                item.size = size
                item.last_access = datetime.now()
            else:
                self._cache[key] = CacheItem(
                    key=key,
                    value=value,
                    expiry=expiry,
                    size=size
                )
                
            self.stats['memory_usage'] += size
            self._size_cache[key] = size
            
            # 持久化
            if self.persist_dir:
                self._persist_item(key)
                
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                
                # 检查是否过期
                if item.expiry and item.expiry <= datetime.now():
                    self._remove_item(key)
                    self.stats['misses'] += 1
                    return None
                    
                # 更新访问信息
                item.access_count += 1
                item.last_access = datetime.now()
                
                self.stats['hits'] += 1
                return item.value
                
            self.stats['misses'] += 1
            return None
            
    def remove(self, key: str):
        """移除缓存项"""
        with self._lock:
            self._remove_item(key)
            
    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._size_cache.clear()
            self.stats['memory_usage'] = 0
            
    def set_ttl(self, key: str, seconds: int):
        """设置缓存项的过期时间"""
        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                item.expiry = datetime.now() + timedelta(seconds=seconds)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_items = len(self._cache)
            hit_ratio = (
                self.stats['hits'] /
                (self.stats['hits'] + self.stats['misses'])
                if self.stats['hits'] + self.stats['misses'] > 0
                else 0
            )
            
            return {
                'total_items': total_items,
                'memory_usage_mb': self.stats['memory_usage'] / (1024 * 1024),
                'hit_ratio': hit_ratio,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions']
            }
            
    def _persist_item(self, key: str):
        """持久化缓存项"""
        if not self.persist_dir:
            return
            
        os.makedirs(self.persist_dir, exist_ok=True)
        item = self._cache[key]
        
        # 创建持久化数据
        persist_data = {
            'key': item.key,
            'value': item.value,
            'expiry': item.expiry.isoformat() if item.expiry else None,
            'access_count': item.access_count,
            'last_access': item.last_access.isoformat(),
            'size': item.size
        }
        
        # 保存到文件
        file_path = os.path.join(self.persist_dir, f"{key}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(persist_data, f, ensure_ascii=False)
            
    def _load_persistent_data(self):
        """加载持久化数据"""
        if not os.path.exists(self.persist_dir):
            return
            
        for filename in os.listdir(self.persist_dir):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(self.persist_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 转换日期时间
                expiry = (
                    datetime.fromisoformat(data['expiry'])
                    if data['expiry']
                    else None
                )
                last_access = datetime.fromisoformat(data['last_access'])
                
                # 检查是否过期
                if expiry and expiry <= datetime.now():
                    os.remove(file_path)
                    continue
                    
                # 创建缓存项
                self.set(
                    data['key'],
                    data['value'],
                    ttl=(
                        expiry - datetime.now()
                        if expiry
                        else None
                    )
                )
            except Exception as e:
                print(f"加载缓存项 {filename} 失败: {e}")
                continue
                
    def __del__(self):
        """清理资源"""
        if hasattr(self, '_cleanup_thread') and self._cleanup_thread:
            if hasattr(self, '_stop_cleanup'):
                self._stop_cleanup.set()
            self._cleanup_thread.join()
