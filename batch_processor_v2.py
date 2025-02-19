from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import time
import threading
from queue import PriorityQueue
from collections import defaultdict
import numpy as np
from errors import ValidationError

@dataclass(order=True)
class PrioritizedItem:
    """优先级队列项"""
    priority: int
    timestamp: float
    item_id: str
    content: Any

class BatchConfig:
    """批处理配置"""
    def __init__(
        self,
        min_batch_size: int = 1,
        max_batch_size: int = 32,
        max_wait_time: float = 5.0,
        target_latency: float = 1.0
    ):
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.target_latency = target_latency
        
class BatchMetrics:
    """批处理指标"""
    def __init__(self):
        self.batch_sizes: List[int] = []
        self.processing_times: List[float] = []
        self.waiting_times: List[float] = []
        self.queue_lengths: List[int] = []
        
    def update(
        self,
        batch_size: int,
        processing_time: float,
        waiting_time: float,
        queue_length: int
    ):
        """更新指标"""
        self.batch_sizes.append(batch_size)
        self.processing_times.append(processing_time)
        self.waiting_times.append(waiting_time)
        self.queue_lengths.append(queue_length)
        
        # 保持最近1000个样本
        max_samples = 1000
        if len(self.batch_sizes) > max_samples:
            self.batch_sizes = self.batch_sizes[-max_samples:]
            self.processing_times = self.processing_times[-max_samples:]
            self.waiting_times = self.waiting_times[-max_samples:]
            self.queue_lengths = self.queue_lengths[-max_samples:]
            
    @property
    def average_batch_size(self) -> float:
        """平均批大小"""
        return np.mean(self.batch_sizes) if self.batch_sizes else 0
        
    @property
    def average_processing_time(self) -> float:
        """平均处理时间"""
        return np.mean(self.processing_times) if self.processing_times else 0
        
    @property
    def average_waiting_time(self) -> float:
        """平均等待时间"""
        return np.mean(self.waiting_times) if self.waiting_times else 0
        
    @property
    def average_queue_length(self) -> float:
        """平均队列长度"""
        return np.mean(self.queue_lengths) if self.queue_lengths else 0

class DynamicBatchProcessor:
    """动态批处理器"""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.metrics = BatchMetrics()
        
        # 优先级队列
        self.queues: Dict[str, PriorityQueue] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        self.processing: Dict[str, set] = defaultdict(set)
        
        # 线程同步
        self.locks: Dict[str, threading.Lock] = {}
        self.events: Dict[str, threading.Event] = {}
        
        # 缓存
        self.cache: Dict[str, Any] = {}
        self.cache_lock = threading.Lock()
        
    def _get_or_create_queue(self, batch_type: str) -> PriorityQueue:
        """获取或创建队列"""
        if batch_type not in self.queues:
            self.queues[batch_type] = PriorityQueue()
            self.locks[batch_type] = threading.Lock()
            self.events[batch_type] = threading.Event()
        return self.queues[batch_type]
        
    def add_to_batch(
        self,
        batch_type: str,
        item: Any,
        item_id: str,
        priority: int = 0
    ) -> threading.Event:
        """添加项目到批处理队列"""
        queue = self._get_or_create_queue(batch_type)
        event = self.events[batch_type]
        
        # 检查缓存
        cache_key = f"{batch_type}:{item_id}"
        with self.cache_lock:
            if cache_key in self.cache:
                return event
                
        with self.locks[batch_type]:
            # 添加到优先级队列
            queue.put(PrioritizedItem(
                priority=priority,
                timestamp=time.time(),
                item_id=item_id,
                content=item
            ))
            
            # 如果队列长度达到最大批大小，触发处理
            if queue.qsize() >= self.config.max_batch_size:
                event.set()
                
        return event
        
    def get_batch(
        self,
        batch_type: str,
        timeout: Optional[float] = None
    ) -> Optional[List[PrioritizedItem]]:
        """获取待处理批次"""
        queue = self._get_or_create_queue(batch_type)
        event = self.events[batch_type]
        
        if timeout is None:
            timeout = self.config.max_wait_time
            
        # 等待批次填满或超时
        start_time = time.time()
        event.wait(timeout=timeout)
        
        with self.locks[batch_type]:
            if queue.empty():
                return None
                
            # 动态确定批大小
            current_batch_size = self._calculate_batch_size(batch_type)
            
            # 获取当前批次
            batch = []
            while len(batch) < current_batch_size and not queue.empty():
                item = queue.get()
                if item.item_id not in self.processing[batch_type]:
                    batch.append(item)
                    self.processing[batch_type].add(item.item_id)
                    
            if not batch:
                return None
                
            event.clear()
            
            # 更新指标
            self.metrics.update(
                batch_size=len(batch),
                processing_time=0,  # 将在处理完成后更新
                waiting_time=time.time() - start_time,
                queue_length=queue.qsize()
            )
            
            return batch
            
    def _calculate_batch_size(self, batch_type: str) -> int:
        """动态计算最优批大小"""
        # 基于当前性能指标调整批大小
        avg_processing_time = self.metrics.average_processing_time
        avg_waiting_time = self.metrics.average_waiting_time
        queue_length = self.queues[batch_type].qsize()
        
        if avg_processing_time > 0:
            # 如果处理时间超过目标延迟，减小批大小
            if avg_processing_time > self.config.target_latency:
                target_size = int(
                    self.metrics.average_batch_size *
                    (self.config.target_latency / avg_processing_time)
                )
            # 如果队列增长过快，增加批大小
            elif queue_length > self.metrics.average_queue_length * 1.5:
                target_size = int(self.metrics.average_batch_size * 1.2)
            # 如果等待时间过长，减小批大小
            elif avg_waiting_time > self.config.max_wait_time * 0.8:
                target_size = int(self.metrics.average_batch_size * 0.8)
            else:
                target_size = int(self.metrics.average_batch_size)
        else:
            target_size = self.config.min_batch_size
            
        # 确保在配置范围内
        return max(
            self.config.min_batch_size,
            min(self.config.max_batch_size, target_size)
        )
        
    def set_result(
        self,
        batch_type: str,
        item_id: str,
        result: Any,
        cache_result: bool = False
    ):
        """设置处理结果"""
        if batch_type not in self.results:
            self.results[batch_type] = {}
            
        self.results[batch_type][item_id] = result
        
        # 从处理集合中移除
        self.processing[batch_type].remove(item_id)
        
        # 缓存结果
        if cache_result:
            cache_key = f"{batch_type}:{item_id}"
            with self.cache_lock:
                self.cache[cache_key] = result
                
    def get_result(
        self,
        batch_type: str,
        item_id: str,
        timeout: Optional[float] = None
    ) -> Optional[Any]:
        """获取处理结果"""
        # 首先检查缓存
        cache_key = f"{batch_type}:{item_id}"
        with self.cache_lock:
            if cache_key in self.cache:
                return self.cache[cache_key]
                
        start_time = time.time()
        while timeout is None or time.time() - start_time < timeout:
            if (batch_type in self.results and
                item_id in self.results[batch_type]):
                result = self.results[batch_type][item_id]
                del self.results[batch_type][item_id]
                return result
            time.sleep(0.1)
        return None
        
    def clear_cache(self, batch_type: Optional[str] = None):
        """清理缓存"""
        with self.cache_lock:
            if batch_type:
                keys_to_remove = [
                    k for k in self.cache.keys()
                    if k.startswith(f"{batch_type}:")
                ]
                for k in keys_to_remove:
                    del self.cache[k]
            else:
                self.cache.clear()
                
    def get_metrics(self, batch_type: str) -> Dict[str, float]:
        """获取性能指标"""
        return {
            'average_batch_size': self.metrics.average_batch_size,
            'average_processing_time': self.metrics.average_processing_time,
            'average_waiting_time': self.metrics.average_waiting_time,
            'average_queue_length': self.metrics.average_queue_length,
            'current_queue_length': self.queues[batch_type].qsize()
            if batch_type in self.queues else 0
        }
