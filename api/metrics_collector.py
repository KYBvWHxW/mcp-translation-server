from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import json
import os
import psutil
import numpy as np
from collections import deque

@dataclass
class TranslationMetrics:
    """翻译指标"""
    request_id: str
    source_length: int
    target_length: int
    processing_time: float
    bleu_score: Optional[float] = None
    error_rate: Optional[float] = None
    memory_usage: float = 0
    cpu_usage: float = 0

@dataclass
class ResourceMetrics:
    """资源使用指标"""
    resource_type: str
    operation: str
    processing_time: float
    memory_delta: float
    cache_hits: int = 0
    cache_misses: int = 0

@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io: Dict[str, float]
    network_io: Dict[str, float]

class MetricsCollector:
    """指标收集器"""
    
    def __init__(
        self,
        metrics_dir: str = "metrics",
        max_history: int = 1000,
        save_interval: timedelta = timedelta(minutes=5)
    ):
        self.metrics_dir = metrics_dir
        self.max_history = max_history
        self.save_interval = save_interval
        
        # 创建指标目录
        os.makedirs(metrics_dir, exist_ok=True)
        
        # 初始化指标存储
        self.translation_metrics: deque = deque(maxlen=max_history)
        self.resource_metrics: deque = deque(maxlen=max_history)
        self.performance_metrics: deque = deque(maxlen=max_history)
        self.error_metrics: Dict[str, int] = {}
        self.latency_metrics: List[float] = []
        
        # 性能监控
        self._process = psutil.Process()
        self._start_time = datetime.now()
        self._last_save = self._start_time
        
        # 线程同步
        self._lock = threading.Lock()
        self._stop_collection = threading.Event()
        self._collection_thread = None
        
        # 启动性能收集线程
        self._start_collection_thread()
        
    def _start_collection_thread(self):
        """启动性能收集线程"""
        def collection_task():
            while not self._stop_collection.is_set():
                try:
                    metrics = self._collect_performance_metrics()
                    with self._lock:
                        self.performance_metrics.append(metrics)
                        
                        # 定期保存
                        now = datetime.now()
                        if now - self._last_save >= self.save_interval:
                            self._save_metrics()
                            self._last_save = now
                except Exception as e:
                    print(f"性能指标收集失败: {e}")
                finally:
                    self._stop_collection.wait(60)  # 每分钟收集一次
                    
        self._collection_thread = threading.Thread(
            target=collection_task,
            daemon=True
        )
        self._collection_thread.start()
        
    def _collect_performance_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        cpu_percent = self._process.cpu_percent()
        memory_percent = self._process.memory_percent()
        
        # 磁盘IO
        disk_io = psutil.disk_io_counters()
        disk_metrics = {
            'read_bytes': disk_io.read_bytes,
            'write_bytes': disk_io.write_bytes
        }
        
        # 网络IO
        net_io = psutil.net_io_counters()
        network_metrics = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv
        }
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_io=disk_metrics,
            network_io=network_metrics
        )
        
    def record_translation(self, metrics: TranslationMetrics):
        """记录翻译指标"""
        with self._lock:
            self.translation_metrics.append(metrics)
            self.latency_metrics.append(metrics.processing_time)
            
            # 限制延迟指标数量
            if len(self.latency_metrics) > self.max_history:
                self.latency_metrics = self.latency_metrics[-self.max_history:]
                
    def record_resource_operation(self, metrics: ResourceMetrics):
        """记录资源操作指标"""
        with self._lock:
            self.resource_metrics.append(metrics)
            
    def record_error(self, error_type: str):
        """记录错误"""
        with self._lock:
            self.error_metrics[error_type] = (
                self.error_metrics.get(error_type, 0) + 1
            )
            
    def get_translation_stats(self) -> Dict[str, Any]:
        """获取翻译统计信息"""
        with self._lock:
            if not self.translation_metrics:
                return {}
                
            processing_times = [m.processing_time for m in self.translation_metrics]
            bleu_scores = [
                m.bleu_score for m in self.translation_metrics
                if m.bleu_score is not None
            ]
            error_rates = [
                m.error_rate for m in self.translation_metrics
                if m.error_rate is not None
            ]
            
            return {
                'total_requests': len(self.translation_metrics),
                'average_processing_time': np.mean(processing_times),
                'p95_processing_time': np.percentile(processing_times, 95),
                'average_bleu_score': np.mean(bleu_scores) if bleu_scores else None,
                'average_error_rate': np.mean(error_rates) if error_rates else None,
                'average_source_length': np.mean([m.source_length for m in self.translation_metrics]),
                'average_target_length': np.mean([m.target_length for m in self.translation_metrics])
            }
            
    def get_resource_stats(self) -> Dict[str, Any]:
        """获取资源统计信息"""
        with self._lock:
            if not self.resource_metrics:
                return {}
                
            stats = {}
            for resource_type in set(m.resource_type for m in self.resource_metrics):
                type_metrics = [
                    m for m in self.resource_metrics
                    if m.resource_type == resource_type
                ]
                
                stats[resource_type] = {
                    'total_operations': len(type_metrics),
                    'average_processing_time': np.mean([m.processing_time for m in type_metrics]),
                    'total_memory_delta': sum(m.memory_delta for m in type_metrics),
                    'cache_hit_ratio': (
                        sum(m.cache_hits) /
                        (sum(m.cache_hits) + sum(m.cache_misses))
                        if sum(m.cache_hits) + sum(m.cache_misses) > 0
                        else 0
                    )
                }
                
            return stats
            
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        with self._lock:
            if not self.performance_metrics:
                return {}
                
            cpu_percentages = [m.cpu_percent for m in self.performance_metrics]
            memory_percentages = [m.memory_percent for m in self.performance_metrics]
            
            # 计算IO速率
            io_stats = {
                'disk_read_rate': [],
                'disk_write_rate': [],
                'network_send_rate': [],
                'network_recv_rate': []
            }
            
            for i in range(1, len(self.performance_metrics)):
                prev = self.performance_metrics[i-1]
                curr = self.performance_metrics[i]
                time_diff = (curr.timestamp - prev.timestamp).total_seconds()
                
                if time_diff > 0:
                    # 磁盘IO速率
                    io_stats['disk_read_rate'].append(
                        (curr.disk_io['read_bytes'] - prev.disk_io['read_bytes']) /
                        time_diff
                    )
                    io_stats['disk_write_rate'].append(
                        (curr.disk_io['write_bytes'] - prev.disk_io['write_bytes']) /
                        time_diff
                    )
                    
                    # 网络IO速率
                    io_stats['network_send_rate'].append(
                        (curr.network_io['bytes_sent'] - prev.network_io['bytes_sent']) /
                        time_diff
                    )
                    io_stats['network_recv_rate'].append(
                        (curr.network_io['bytes_recv'] - prev.network_io['bytes_recv']) /
                        time_diff
                    )
                    
            return {
                'cpu_usage': {
                    'current': cpu_percentages[-1],
                    'average': np.mean(cpu_percentages),
                    'max': np.max(cpu_percentages)
                },
                'memory_usage': {
                    'current': memory_percentages[-1],
                    'average': np.mean(memory_percentages),
                    'max': np.max(memory_percentages)
                },
                'io_rates': {
                    key: {
                        'current': rates[-1] if rates else 0,
                        'average': np.mean(rates) if rates else 0,
                        'max': np.max(rates) if rates else 0
                    }
                    for key, rates in io_stats.items()
                }
            }
            
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        with self._lock:
            total_errors = sum(self.error_metrics.values())
            return {
                'total_errors': total_errors,
                'error_distribution': {
                    error_type: {
                        'count': count,
                        'percentage': (count / total_errors * 100)
                        if total_errors > 0 else 0
                    }
                    for error_type, count in self.error_metrics.items()
                }
            }
            
    def get_latency_percentiles(self) -> Dict[str, float]:
        """获取延迟百分位数"""
        with self._lock:
            if not self.latency_metrics:
                return {}
                
            return {
                'p50': np.percentile(self.latency_metrics, 50),
                'p75': np.percentile(self.latency_metrics, 75),
                'p90': np.percentile(self.latency_metrics, 90),
                'p95': np.percentile(self.latency_metrics, 95),
                'p99': np.percentile(self.latency_metrics, 99)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        with self._lock:
            # 翻译统计
            translation_stats = self.get_translation_stats()
            translation_count = translation_stats.get('total_requests', 0)
            average_latency = translation_stats.get('average_processing_time', 0)

            # 资源统计
            resource_stats = self.get_resource_stats()
            cache_hit_ratio = 0
            for stats in resource_stats.values():
                if stats.get('cache_hit_ratio', 0) > cache_hit_ratio:
                    cache_hit_ratio = stats['cache_hit_ratio']

            # 性能统计
            performance_stats = self.get_performance_stats()
            cpu_usage = performance_stats.get('cpu_usage', {}).get('current', 0)
            memory_usage = performance_stats.get('memory_usage', {}).get('current', 0)

            return {
                'translation_count': translation_count,
                'average_latency': average_latency,
                'cache_hit_ratio': cache_hit_ratio,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'error_count': len(self.error_metrics)
            }
            
    def _save_metrics(self):
        """保存指标到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存翻译指标
        translation_file = os.path.join(
            self.metrics_dir,
            f"translation_metrics_{timestamp}.json"
        )
        with open(translation_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_translation_stats(), f, indent=2)
            
        # 保存资源指标
        resource_file = os.path.join(
            self.metrics_dir,
            f"resource_metrics_{timestamp}.json"
        )
        with open(resource_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_resource_stats(), f, indent=2)
            
        # 保存性能指标
        performance_file = os.path.join(
            self.metrics_dir,
            f"performance_metrics_{timestamp}.json"
        )
        with open(performance_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_performance_stats(), f, indent=2)
            
    def reset_metrics(self):
        """重置所有指标"""
        with self._lock:
            self.translation_metrics.clear()
            self.resource_metrics.clear()
            self.performance_metrics.clear()
            self.error_metrics.clear()
            self.latency_metrics.clear()
            self._start_time = datetime.now()
            self._last_save = self._start_time

    def __del__(self):
        """清理资源"""
        if hasattr(self, '_collection_thread') and self._collection_thread:
            if hasattr(self, '_stop_collection'):
                self._stop_collection.set()
            self._collection_thread.join()
