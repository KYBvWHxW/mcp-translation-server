import time
from dataclasses import dataclass
from typing import Dict, Optional
import threading
from collections import deque

@dataclass
class RateLimitRule:
    """限流规则"""
    requests_per_second: int
    burst_size: int = 0
    
class TokenBucket:
    """令牌桶算法实现"""
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
        
    def _update_tokens(self):
        now = time.time()
        delta = now - self.last_update
        new_tokens = delta * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now
        
    def try_acquire(self, tokens: int = 1) -> bool:
        with self.lock:
            self._update_tokens()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class RateLimiter:
    """请求限流器"""
    def __init__(self):
        self.limiters: Dict[str, TokenBucket] = {}
        self.rules: Dict[str, RateLimitRule] = {}
        self.lock = threading.Lock()
        
    def add_rule(self, endpoint: str, rule: RateLimitRule):
        """添加限流规则"""
        with self.lock:
            self.rules[endpoint] = rule
            self.limiters[endpoint] = TokenBucket(
                rate=rule.requests_per_second,
                capacity=max(rule.requests_per_second, rule.burst_size)
            )
            
    def check_rate_limit(self, endpoint: str) -> bool:
        """检查是否超出限流"""
        limiter = self.limiters.get(endpoint)
        if limiter is None:
            return True
        return limiter.try_acquire()

class BatchProcessor:
    """批处理管理器"""
    def __init__(self, batch_size: int, max_wait_time: float):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.batches: Dict[str, deque] = {}
        self.batch_events: Dict[str, threading.Event] = {}
        self.results: Dict[str, Dict] = {}
        self.locks: Dict[str, threading.Lock] = {}
        
    def _get_or_create_batch(self, batch_type: str) -> deque:
        """获取或创建批处理队列"""
        if batch_type not in self.batches:
            self.batches[batch_type] = deque()
            self.batch_events[batch_type] = threading.Event()
            self.locks[batch_type] = threading.Lock()
        return self.batches[batch_type]
        
    def add_to_batch(
        self,
        batch_type: str,
        item: any,
        item_id: str
    ) -> threading.Event:
        """添加项目到批处理队列"""
        batch = self._get_or_create_batch(batch_type)
        event = self.batch_events[batch_type]
        
        with self.locks[batch_type]:
            batch.append((item_id, item))
            if len(batch) >= self.batch_size:
                event.set()
                
        return event
        
    def get_batch(
        self,
        batch_type: str,
        timeout: Optional[float] = None
    ) -> Optional[list]:
        """获取待处理批次"""
        batch = self._get_or_create_batch(batch_type)
        event = self.batch_events[batch_type]
        
        if timeout is None:
            timeout = self.max_wait_time
            
        # 等待批次填满或超时
        event.wait(timeout=timeout)
        
        with self.locks[batch_type]:
            if not batch:
                return None
                
            # 获取当前批次
            current_batch = list(batch)
            batch.clear()
            event.clear()
            
            return current_batch
            
    def set_result(
        self,
        batch_type: str,
        item_id: str,
        result: any
    ):
        """设置处理结果"""
        if batch_type not in self.results:
            self.results[batch_type] = {}
        self.results[batch_type][item_id] = result
        
    def get_result(
        self,
        batch_type: str,
        item_id: str,
        timeout: Optional[float] = None
    ) -> Optional[any]:
        """获取处理结果"""
        start_time = time.time()
        while timeout is None or time.time() - start_time < timeout:
            if batch_type in self.results and item_id in self.results[batch_type]:
                result = self.results[batch_type][item_id]
                del self.results[batch_type][item_id]
                return result
            time.sleep(0.1)
        return None
