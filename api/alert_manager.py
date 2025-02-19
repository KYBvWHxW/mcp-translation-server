from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import json
import os
import numpy as np
from collections import deque

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric: str
    condition: str
    threshold: float
    duration: timedelta
    severity: str
    description: str
    enabled: bool = True

@dataclass
class Alert:
    """告警"""
    rule: AlertRule
    value: float
    timestamp: datetime
    status: str  # triggered, resolved
    resolved_at: Optional[datetime] = None

class AlertManager:
    """告警管理器"""
    
    def __init__(
        self,
        alert_dir: str = "alerts",
        max_history: int = 1000,
        check_interval: timedelta = timedelta(seconds=30)
    ):
        self.alert_dir = alert_dir
        self.max_history = max_history
        self.check_interval = check_interval
        
        # 创建告警目录
        os.makedirs(alert_dir, exist_ok=True)
        
        # 告警规则和历史
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: deque = deque(maxlen=max_history)
        self.active_alerts: Dict[str, Alert] = {}
        
        # 指标数据
        self.metrics_buffer: Dict[str, deque] = {}
        
        # 回调函数
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # 线程同步
        self._lock = threading.Lock()
        self._stop_checking = threading.Event()
        self._check_thread = None
        
        # 加载预定义规则
        self._load_default_rules()
        
        # 启动检查线程
        self._start_check_thread()
        
    def _load_default_rules(self):
        """加载预定义告警规则"""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                metric="cpu_percent",
                condition=">=",
                threshold=80.0,
                duration=timedelta(minutes=5),
                severity="critical",
                description="CPU使用率持续过高"
            ),
            AlertRule(
                name="high_memory_usage",
                metric="memory_percent",
                condition=">=",
                threshold=85.0,
                duration=timedelta(minutes=5),
                severity="critical",
                description="内存使用率持续过高"
            ),
            AlertRule(
                name="high_error_rate",
                metric="error_rate",
                condition=">=",
                threshold=0.05,
                duration=timedelta(minutes=10),
                severity="warning",
                description="错误率超过5%"
            ),
            AlertRule(
                name="high_latency",
                metric="p95_latency",
                condition=">=",
                threshold=2.0,
                duration=timedelta(minutes=5),
                severity="warning",
                description="P95延迟超过2秒"
            ),
            AlertRule(
                name="low_cache_hit_ratio",
                metric="cache_hit_ratio",
                condition="<=",
                threshold=0.5,
                duration=timedelta(minutes=15),
                severity="warning",
                description="缓存命中率低于50%"
            ),
            AlertRule(
                name="high_disk_usage",
                metric="disk_usage_percent",
                condition=">=",
                threshold=90.0,
                duration=timedelta(minutes=30),
                severity="warning",
                description="磁盘使用率超过90%"
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
            
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        with self._lock:
            self.rules[rule.name] = rule
            if rule.metric not in self.metrics_buffer:
                self.metrics_buffer[rule.metric] = deque(maxlen=1000)
                
    def remove_rule(self, rule_name: str):
        """移除告警规则"""
        with self._lock:
            if rule_name in self.rules:
                del self.rules[rule_name]
                
    def update_rule(self, rule_name: str, **kwargs):
        """更新告警规则"""
        with self._lock:
            if rule_name in self.rules:
                rule = self.rules[rule_name]
                for key, value in kwargs.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                        
    def add_metric(self, metric: str, value: float):
        """添加指标数据"""
        with self._lock:
            if metric not in self.metrics_buffer:
                self.metrics_buffer[metric] = deque(maxlen=1000)
            self.metrics_buffer[metric].append((datetime.now(), value))
            
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回调"""
        self.alert_callbacks.append(callback)
        
    def _check_alerts(self):
        """检查告警"""
        with self._lock:
            now = datetime.now()
            
            for rule in self.rules.values():
                if not rule.enabled or rule.metric not in self.metrics_buffer:
                    continue
                    
                # 获取指标数据
                metric_data = self.metrics_buffer[rule.metric]
                if not metric_data:
                    continue
                    
                # 获取持续时间内的数据
                duration_data = [
                    value for timestamp, value in metric_data
                    if now - timestamp <= rule.duration
                ]
                
                if not duration_data:
                    continue
                    
                # 计算聚合值
                current_value = np.mean(duration_data)
                
                # 检查条件
                is_triggered = False
                if rule.condition == ">=":
                    is_triggered = current_value >= rule.threshold
                elif rule.condition == "<=":
                    is_triggered = current_value <= rule.threshold
                elif rule.condition == ">":
                    is_triggered = current_value > rule.threshold
                elif rule.condition == "<":
                    is_triggered = current_value < rule.threshold
                    
                # 处理告警状态
                if is_triggered:
                    if rule.name not in self.active_alerts:
                        alert = Alert(
                            rule=rule,
                            value=current_value,
                            timestamp=now,
                            status="triggered"
                        )
                        self.active_alerts[rule.name] = alert
                        self.alerts.append(alert)
                        
                        # 触发回调
                        for callback in self.alert_callbacks:
                            try:
                                callback(alert)
                            except Exception as e:
                                print(f"告警回调失败: {e}")
                else:
                    if rule.name in self.active_alerts:
                        alert = self.active_alerts[rule.name]
                        alert.status = "resolved"
                        alert.resolved_at = now
                        del self.active_alerts[rule.name]
                        
                        # 触发回调
                        for callback in self.alert_callbacks:
                            try:
                                callback(alert)
                            except Exception as e:
                                print(f"告警回调失败: {e}")
                                
    def _start_check_thread(self):
        """启动检查线程"""
        def check_task():
            while not self._stop_checking.is_set():
                try:
                    self._check_alerts()
                except Exception as e:
                    print(f"检查告警失败: {e}")
                finally:
                    self._stop_checking.wait(
                        self.check_interval.total_seconds()
                    )
                    
        self._check_thread = threading.Thread(
            target=check_task,
            daemon=True
        )
        self._check_thread.start()
        
    def get_active_alerts(self) -> List[Alert]:
        """获取活动告警"""
        with self._lock:
            return list(self.active_alerts.values())
            
    def get_alert_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None
    ) -> List[Alert]:
        """获取告警历史"""
        with self._lock:
            alerts = list(self.alerts)
            
            if start_time:
                alerts = [
                    a for a in alerts
                    if a.timestamp >= start_time
                ]
                
            if end_time:
                alerts = [
                    a for a in alerts
                    if a.timestamp <= end_time
                ]
                
            if severity:
                alerts = [
                    a for a in alerts
                    if a.rule.severity == severity
                ]
                
            return alerts
            
    def get_alert_stats(self) -> Dict[str, Any]:
        """获取告警统计信息"""
        with self._lock:
            total_alerts = len(self.alerts)
            active_alerts = len(self.active_alerts)
            
            severity_counts = defaultdict(int)
            for alert in self.alerts:
                severity_counts[alert.rule.severity] += 1
                
            return {
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'severity_distribution': dict(severity_counts)
            }
            
    def __del__(self):
        """清理资源"""
        if self._check_thread:
            self._stop_checking.set()
            self._check_thread.join()
