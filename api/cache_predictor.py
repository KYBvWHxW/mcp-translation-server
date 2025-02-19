from typing import Dict, List, Any, Optional
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from datetime import datetime, timedelta
import pandas as pd
from collections import Counter, defaultdict

class CachePredictor:
    """高级缓存预测器"""
    
    def __init__(
        self,
        model_dir: str = "models",
        history_window: int = 24,
        prediction_window: int = 6
    ):
        self.model_dir = model_dir
        self.history_window = history_window
        self.prediction_window = prediction_window
        self.scaler = StandardScaler()
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        os.makedirs(model_dir, exist_ok=True)
        
    def train(
        self,
        access_history: List[Dict[str, Any]],
        cache_metrics: Dict[str, Any]
    ) -> None:
        """训练预测模型"""
        # 准备训练数据
        X, y = self._prepare_training_data(access_history, cache_metrics)
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        
        # 训练模型
        self.model.fit(X_scaled, y)
        
        # 保存模型
        self._save_model()
        
    def predict(
        self,
        recent_history: List[Dict[str, Any]],
        current_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """预测未来访问模式"""
        # 准备预测数据
        X = self._prepare_prediction_data(recent_history, current_metrics)
        
        # 标准化特征
        X_scaled = self.scaler.transform(X)
        
        # 预测
        predictions = self.model.predict(X_scaled)
        
        return self._format_predictions(predictions)
        
    def analyze_patterns(
        self,
        access_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析访问模式"""
        patterns = {
            'temporal': self._analyze_temporal_patterns(access_history),
            'sequential': self._analyze_sequential_patterns(access_history),
            'frequency': self._analyze_frequency_patterns(access_history),
            'correlation': self._analyze_correlation_patterns(access_history)
        }
        
        return patterns
        
    def optimize_cache(
        self,
        patterns: Dict[str, Any],
        cache_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化缓存配置"""
        optimized_config = {
            'size': self._optimize_cache_size(patterns, cache_config),
            'ttl': self._optimize_ttl(patterns, cache_config),
            'prefetch': self._optimize_prefetch(patterns, cache_config),
            'eviction': self._optimize_eviction(patterns, cache_config)
        }
        
        return optimized_config
        
    def _prepare_training_data(
        self,
        access_history: List[Dict[str, Any]],
        cache_metrics: Dict[str, Any]
    ) -> tuple:
        """准备训练数据"""
        features = []
        labels = []
        
        for i in range(len(access_history) - self.history_window - self.prediction_window):
            # 提取特征窗口
            window = access_history[i:i + self.history_window]
            
            # 计算特征
            feature_vector = self._extract_features(window, cache_metrics)
            features.append(feature_vector)
            
            # 提取标签
            future_window = access_history[
                i + self.history_window:
                i + self.history_window + self.prediction_window
            ]
            label_vector = self._extract_labels(future_window)
            labels.append(label_vector)
            
        return np.array(features), np.array(labels)
        
    def _extract_features(
        self,
        window: List[Dict[str, Any]],
        cache_metrics: Dict[str, Any]
    ) -> np.ndarray:
        """提取特征"""
        features = []
        
        # 访问频率特征
        access_counts = Counter(item['key'] for item in window)
        features.extend([
            len(access_counts),  # 不同键的数量
            max(access_counts.values()),  # 最大访问频率
            np.mean(list(access_counts.values())),  # 平均访问频率
            np.std(list(access_counts.values()))  # 访问频率标准差
        ])
        
        # 时间特征
        timestamps = [item['timestamp'] for item in window]
        features.extend([
            np.mean(np.diff(timestamps)),  # 平均访问间隔
            np.std(np.diff(timestamps))  # 访问间隔标准差
        ])
        
        # 缓存性能特征
        features.extend([
            cache_metrics['hit_ratio'],
            cache_metrics['memory_usage'],
            cache_metrics['eviction_rate']
        ])
        
        return np.array(features)
        
    def _extract_labels(self, future_window: List[Dict[str, Any]]) -> np.ndarray:
        """提取标签"""
        access_counts = Counter(item['key'] for item in future_window)
        return np.array(list(access_counts.values()))
        
    def _save_model(self) -> None:
        """保存模型"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = os.path.join(
            self.model_dir,
            f"cache_predictor_{timestamp}.joblib"
        )
        scaler_path = os.path.join(
            self.model_dir,
            f"scaler_{timestamp}.joblib"
        )
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        
    def _analyze_temporal_patterns(
        self,
        access_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析时间模式"""
        # 按小时统计访问
        hour_counts = defaultdict(int)
        # 按天统计访问
        day_counts = defaultdict(int)
        # 计算访问间隔
        intervals = []
        
        for i in range(len(access_history)):
            timestamp = access_history[i]['timestamp']
            dt = datetime.fromtimestamp(timestamp)
            
            hour_counts[dt.hour] += 1
            day_counts[dt.weekday()] += 1
            
            if i > 0:
                prev_timestamp = access_history[i-1]['timestamp']
                interval = timestamp - prev_timestamp
                intervals.append(interval)
                
        return {
            'hourly_pattern': dict(hour_counts),
            'daily_pattern': dict(day_counts),
            'mean_interval': np.mean(intervals),
            'std_interval': np.std(intervals)
        }
        
    def _analyze_sequential_patterns(
        self,
        access_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析序列模式"""
        # 统计键序列
        sequences = defaultdict(int)
        # 计算转移概率
        transitions = defaultdict(lambda: defaultdict(int))
        
        for i in range(len(access_history) - 1):
            current_key = access_history[i]['key']
            next_key = access_history[i + 1]['key']
            
            sequence = (current_key, next_key)
            sequences[sequence] += 1
            transitions[current_key][next_key] += 1
            
        # 计算转移概率
        probability_matrix = {}
        for current_key, next_keys in transitions.items():
            total = sum(next_keys.values())
            probability_matrix[current_key] = {
                k: v/total for k, v in next_keys.items()
            }
            
        return {
            'common_sequences': dict(sequences),
            'transition_probabilities': probability_matrix
        }
        
    def _analyze_frequency_patterns(
        self,
        access_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析频率模式"""
        # 统计键频率
        key_counts = Counter(item['key'] for item in access_history)
        
        # 计算频率统计
        frequencies = np.array(list(key_counts.values()))
        
        return {
            'key_frequencies': dict(key_counts),
            'mean_frequency': np.mean(frequencies),
            'std_frequency': np.std(frequencies),
            'max_frequency': np.max(frequencies),
            'min_frequency': np.min(frequencies)
        }
        
    def _analyze_correlation_patterns(
        self,
        access_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析相关性模式"""
        # 创建共现矩阵
        cooccurrence = defaultdict(lambda: defaultdict(int))
        
        # 使用滑动窗口统计共现
        window_size = 5
        for i in range(len(access_history) - window_size):
            window = access_history[i:i + window_size]
            keys = set(item['key'] for item in window)
            
            for key1 in keys:
                for key2 in keys:
                    if key1 != key2:
                        cooccurrence[key1][key2] += 1
                        
        return {
            'cooccurrence_matrix': {
                k: dict(v) for k, v in cooccurrence.items()
            }
        }
        
    def _optimize_cache_size(
        self,
        patterns: Dict[str, Any],
        cache_config: Dict[str, Any]
    ) -> int:
        """优化缓存大小"""
        # 基于访问频率和模式计算推荐的缓存大小
        freq_patterns = patterns['frequency']
        current_size = cache_config['size']
        
        # 计算活跃键的数量
        active_keys = sum(1 for f in freq_patterns['key_frequencies'].values()
                         if f > freq_patterns['mean_frequency'])
                         
        # 考虑内存限制
        memory_limit = cache_config.get('memory_limit', float('inf'))
        avg_entry_size = cache_config.get('avg_entry_size', 1024)  # bytes
        
        # 计算推荐大小
        recommended_size = min(
            active_keys * 1.2,  # 为突发增长预留20%空间
            memory_limit / avg_entry_size
        )
        
        return int(recommended_size)
        
    def _optimize_ttl(
        self,
        patterns: Dict[str, Any],
        cache_config: Dict[str, Any]
    ) -> int:
        """优化TTL"""
        temporal_patterns = patterns['temporal']
        current_ttl = cache_config['ttl']
        
        # 基于访问间隔计算推荐TTL
        mean_interval = temporal_patterns['mean_interval']
        std_interval = temporal_patterns['std_interval']
        
        # 使用均值加两个标准差作为TTL
        recommended_ttl = mean_interval + 2 * std_interval
        
        # 确保TTL在合理范围内
        min_ttl = cache_config.get('min_ttl', 60)  # 1分钟
        max_ttl = cache_config.get('max_ttl', 86400)  # 1天
        
        return int(np.clip(recommended_ttl, min_ttl, max_ttl))
        
    def _optimize_prefetch(
        self,
        patterns: Dict[str, Any],
        cache_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化预取策略"""
        sequential_patterns = patterns['sequential']
        correlation_patterns = patterns['correlation']
        
        # 基于转移概率选择预取键
        prefetch_keys = []
        probability_threshold = 0.7
        
        for current_key, transitions in sequential_patterns['transition_probabilities'].items():
            likely_next_keys = [
                k for k, p in transitions.items()
                if p > probability_threshold
            ]
            prefetch_keys.extend(likely_next_keys)
            
        # 基于共现关系补充预取键
        for key, cooccurrences in correlation_patterns['cooccurrence_matrix'].items():
            related_keys = [
                k for k, count in cooccurrences.items()
                if count > np.mean(list(cooccurrences.values()))
            ]
            prefetch_keys.extend(related_keys)
            
        return {
            'keys': list(set(prefetch_keys)),
            'batch_size': min(len(prefetch_keys), 10),
            'threshold': probability_threshold
        }
        
    def _optimize_eviction(
        self,
        patterns: Dict[str, Any],
        cache_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化驱逐策略"""
        freq_patterns = patterns['frequency']
        temporal_patterns = patterns['temporal']
        
        # 计算键的重要性分数
        importance_scores = {}
        for key, freq in freq_patterns['key_frequencies'].items():
            # 结合频率和时间模式
            time_score = 1.0
            if key in temporal_patterns['hourly_pattern']:
                time_score = temporal_patterns['hourly_pattern'][key] / \
                            max(temporal_patterns['hourly_pattern'].values())
                            
            importance_scores[key] = freq * time_score
            
        return {
            'policy': 'weighted_lru',
            'weights': importance_scores,
            'min_lifetime': temporal_patterns['mean_interval'] / 2
        }
