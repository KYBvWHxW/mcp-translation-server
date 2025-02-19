from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import threading
import json
import os
from datetime import datetime, timedelta
import numpy as np
from collections import Counter
from .cache_manager import CacheManager, CacheConfig

@dataclass
class AccessPattern:
    """访问模式"""
    key: str
    count: int
    last_access: datetime
    access_times: List[datetime]
    
class CacheWarmer:
    """缓存预热器"""
    
    def __init__(
        self,
        cache_manager: CacheManager,
        pattern_file: str = "cache_patterns.json",
        min_confidence: float = 0.7,
        max_patterns: int = 1000
    ):
        self.cache_manager = cache_manager
        self.pattern_file = pattern_file
        self.min_confidence = min_confidence
        self.max_patterns = max_patterns
        
        # 访问模式存储
        self.access_patterns: Dict[str, AccessPattern] = {}
        self.sequence_patterns: Dict[str, Set[str]] = {}
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'warm_ups': 0
        }
        
        # 线程同步
        self._lock = threading.Lock()
        self._stop_analysis = threading.Event()
        self._analysis_thread = None
        
        # 加载历史模式
        self._load_patterns()
        
        # 启动分析线程
        self._start_analysis_thread()
        
    def record_access(self, key: str):
        """记录缓存访问"""
        with self._lock:
            now = datetime.now()
            
            if key not in self.access_patterns:
                self.access_patterns[key] = AccessPattern(
                    key=key,
                    count=0,
                    last_access=now,
                    access_times=[]
                )
                
            pattern = self.access_patterns[key]
            pattern.count += 1
            pattern.last_access = now
            pattern.access_times.append(now)
            
            # 限制访问时间列表大小
            if len(pattern.access_times) > 1000:
                pattern.access_times = pattern.access_times[-1000:]
                
    def predict_next_access(self, current_key: str) -> List[str]:
        """预测下一个可能被访问的键"""
        with self._lock:
            if current_key not in self.sequence_patterns:
                return []
                
            # 获取相关模式
            related_keys = self.sequence_patterns[current_key]
            
            # 计算每个键的得分
            scores = []
            for key in related_keys:
                if key not in self.access_patterns:
                    continue
                    
                pattern = self.access_patterns[key]
                
                # 计算时间衰减因子
                time_decay = np.exp(
                    -(datetime.now() - pattern.last_access).total_seconds() /
                    (3600 * 24)  # 24小时衰减
                )
                
                # 计算访问频率得分
                frequency_score = pattern.count / max(
                    p.count for p in self.access_patterns.values()
                )
                
                # 计算时间模式得分
                time_pattern_score = self._calculate_time_pattern_score(pattern)
                
                # 综合得分
                score = (
                    0.4 * time_decay +
                    0.4 * frequency_score +
                    0.2 * time_pattern_score
                )
                
                scores.append((key, score))
                
            # 按得分排序
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # 返回得分超过阈值的键
            return [
                key for key, score in scores
                if score >= self.min_confidence
            ]
            
    def warm_up_cache(self, keys: List[str]):
        """预热缓存"""
        for key in keys:
            if self.cache_manager.get(key) is None:
                # 这里需要实现获取实际数据的逻辑
                # 可以通过回调函数或其他机制
                self.stats['warm_ups'] += 1
                
    def _calculate_time_pattern_score(self, pattern: AccessPattern) -> float:
        """计算时间模式得分"""
        if len(pattern.access_times) < 2:
            return 0
            
        # 计算访问间隔
        intervals = []
        for i in range(1, len(pattern.access_times)):
            interval = (
                pattern.access_times[i] - pattern.access_times[i-1]
            ).total_seconds()
            intervals.append(interval)
            
        # 计算间隔的标准差
        std_dev = np.std(intervals)
        
        # 如果标准差较小，说明访问模式较规律
        regularity_score = np.exp(-std_dev / 3600)  # 1小时作为基准
        
        return regularity_score
        
    def _analyze_patterns(self):
        """分析访问模式"""
        with self._lock:
            # 清理旧的序列模式
            self.sequence_patterns.clear()
            
            # 获取最近的访问序列
            access_sequence = []
            for pattern in sorted(
                self.access_patterns.values(),
                key=lambda p: p.last_access
            ):
                access_sequence.extend([pattern.key] * pattern.count)
                
            # 限制序列长度
            if len(access_sequence) > 10000:
                access_sequence = access_sequence[-10000:]
                
            # 分析二元组
            pairs = zip(access_sequence, access_sequence[1:])
            pair_counts = Counter(pairs)
            
            # 计算条件概率
            for (key1, key2), count in pair_counts.items():
                key1_count = sum(1 for k in access_sequence if k == key1)
                probability = count / key1_count
                
                if probability >= self.min_confidence:
                    if key1 not in self.sequence_patterns:
                        self.sequence_patterns[key1] = set()
                    self.sequence_patterns[key1].add(key2)
                    
            # 清理低频模式
            if len(self.access_patterns) > self.max_patterns:
                # 按访问次数和最近访问时间排序
                sorted_patterns = sorted(
                    self.access_patterns.items(),
                    key=lambda x: (x[1].count, x[1].last_access),
                    reverse=True
                )
                
                # 保留最常用的模式
                self.access_patterns = dict(sorted_patterns[:self.max_patterns])
                
            # 保存模式
            self._save_patterns()
            
    def _start_analysis_thread(self):
        """启动分析线程"""
        def analysis_task():
            while not self._stop_analysis.is_set():
                try:
                    self._analyze_patterns()
                except Exception as e:
                    print(f"分析访问模式失败: {e}")
                finally:
                    self._stop_analysis.wait(300)  # 每5分钟分析一次
                    
        self._analysis_thread = threading.Thread(
            target=analysis_task,
            daemon=True
        )
        self._analysis_thread.start()
        
    def _save_patterns(self):
        """保存访问模式"""
        try:
            data = {
                'patterns': {
                    key: {
                        'count': pattern.count,
                        'last_access': pattern.last_access.isoformat(),
                        'access_times': [
                            t.isoformat() for t in pattern.access_times
                        ]
                    }
                    for key, pattern in self.access_patterns.items()
                },
                'sequences': {
                    key: list(values)
                    for key, values in self.sequence_patterns.items()
                }
            }
            
            with open(self.pattern_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"保存访问模式失败: {e}")
            
    def _load_patterns(self):
        """加载访问模式"""
        if not os.path.exists(self.pattern_file):
            return
            
        try:
            with open(self.pattern_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 加载访问模式
            for key, info in data['patterns'].items():
                self.access_patterns[key] = AccessPattern(
                    key=key,
                    count=info['count'],
                    last_access=datetime.fromisoformat(info['last_access']),
                    access_times=[
                        datetime.fromisoformat(t)
                        for t in info['access_times']
                    ]
                )
                
            # 加载序列模式
            self.sequence_patterns = {
                key: set(values)
                for key, values in data['sequences'].items()
            }
        except Exception as e:
            print(f"加载访问模式失败: {e}")
            
    def __del__(self):
        """清理资源"""
        if self._analysis_thread:
            self._stop_analysis.set()
            self._analysis_thread.join()
