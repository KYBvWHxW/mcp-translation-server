from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime, timedelta
import os
import json

class MetricsVisualizer:
    """性能指标可视化器"""
    
    def __init__(self, output_dir: str = "metrics"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置绘图样式
        plt.style.use('seaborn')
        sns.set_palette("husl")
        
    def plot_batch_metrics(
        self,
        metrics: Dict[str, List[float]],
        time_window: Optional[timedelta] = None
    ) -> str:
        """绘制批处理指标"""
        df = pd.DataFrame(metrics)
        if time_window:
            df = df.tail(int(time_window.total_seconds()))
            
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('批处理性能指标', fontsize=16)
        
        # 批大小分布
        sns.histplot(data=df['batch_size'], ax=axes[0, 0])
        axes[0, 0].set_title('批大小分布')
        axes[0, 0].set_xlabel('批大小')
        axes[0, 0].set_ylabel('频率')
        
        # 处理时间趋势
        sns.lineplot(data=df['processing_time'], ax=axes[0, 1])
        axes[0, 1].set_title('处理时间趋势')
        axes[0, 1].set_xlabel('样本')
        axes[0, 1].set_ylabel('处理时间 (秒)')
        
        # 等待时间分布
        sns.boxplot(data=df['waiting_time'], ax=axes[1, 0])
        axes[1, 0].set_title('等待时间分布')
        axes[1, 0].set_ylabel('等待时间 (秒)')
        
        # 队列长度趋势
        sns.lineplot(data=df['queue_length'], ax=axes[1, 1])
        axes[1, 1].set_title('队列长度趋势')
        axes[1, 1].set_xlabel('样本')
        axes[1, 1].set_ylabel('队列长度')
        
        plt.tight_layout()
        
        # 保存图表
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f"batch_metrics_{timestamp}.png")
        plt.savefig(output_file)
        plt.close()
        
        return output_file
        
    def plot_resource_usage(
        self,
        metrics: Dict[str, List[float]],
        resource_type: str
    ) -> str:
        """绘制资源使用指标"""
        df = pd.DataFrame(metrics)
        
        plt.figure(figsize=(12, 6))
        
        if resource_type == 'memory':
            sns.lineplot(data=df['memory_usage'])
            plt.title('内存使用趋势')
            plt.xlabel('时间')
            plt.ylabel('内存使用 (MB)')
        elif resource_type == 'cpu':
            sns.lineplot(data=df['cpu_usage'])
            plt.title('CPU使用趋势')
            plt.xlabel('时间')
            plt.ylabel('CPU使用率 (%)')
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            self.output_dir,
            f"{resource_type}_usage_{timestamp}.png"
        )
        plt.savefig(output_file)
        plt.close()
        
        return output_file
        
    def plot_translation_metrics(
        self,
        metrics: Dict[str, List[float]]
    ) -> str:
        """绘制翻译性能指标"""
        df = pd.DataFrame(metrics)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('翻译性能指标', fontsize=16)
        
        # 翻译时间分布
        sns.histplot(data=df['translation_time'], ax=axes[0, 0])
        axes[0, 0].set_title('翻译时间分布')
        axes[0, 0].set_xlabel('翻译时间 (秒)')
        axes[0, 0].set_ylabel('频率')
        
        # BLEU分数趋势
        if 'bleu_score' in df:
            sns.lineplot(data=df['bleu_score'], ax=axes[0, 1])
            axes[0, 1].set_title('BLEU分数趋势')
            axes[0, 1].set_xlabel('样本')
            axes[0, 1].set_ylabel('BLEU分数')
            
        # 错误率趋势
        if 'error_rate' in df:
            sns.lineplot(data=df['error_rate'], ax=axes[1, 0])
            axes[1, 0].set_title('错误率趋势')
            axes[1, 0].set_xlabel('样本')
            axes[1, 0].set_ylabel('错误率')
            
        # 请求成功率
        if 'success_rate' in df:
            sns.lineplot(data=df['success_rate'], ax=axes[1, 1])
            axes[1, 1].set_title('请求成功率趋势')
            axes[1, 1].set_xlabel('样本')
            axes[1, 1].set_ylabel('成功率')
            
        plt.tight_layout()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            self.output_dir,
            f"translation_metrics_{timestamp}.png"
        )
        plt.savefig(output_file)
        plt.close()
        
        return output_file
        
    def create_performance_report(
        self,
        metrics: Dict[str, Any],
        report_type: str = 'full'
    ) -> str:
        """生成性能报告"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'report_type': report_type,
            'summary': {}
        }
        
        if 'batch_metrics' in metrics:
            batch_df = pd.DataFrame(metrics['batch_metrics'])
            report_data['summary']['batch'] = {
                'average_batch_size': batch_df['batch_size'].mean(),
                'average_processing_time': batch_df['processing_time'].mean(),
                'average_waiting_time': batch_df['waiting_time'].mean(),
                'average_queue_length': batch_df['queue_length'].mean()
            }
            
        if 'translation_metrics' in metrics:
            trans_df = pd.DataFrame(metrics['translation_metrics'])
            report_data['summary']['translation'] = {
                'average_translation_time': trans_df['translation_time'].mean(),
                'average_bleu_score': trans_df['bleu_score'].mean()
                if 'bleu_score' in trans_df else None,
                'average_error_rate': trans_df['error_rate'].mean()
                if 'error_rate' in trans_df else None
            }
            
        if 'resource_metrics' in metrics:
            res_df = pd.DataFrame(metrics['resource_metrics'])
            report_data['summary']['resources'] = {
                'average_memory_usage': res_df['memory_usage'].mean()
                if 'memory_usage' in res_df else None,
                'average_cpu_usage': res_df['cpu_usage'].mean()
                if 'cpu_usage' in res_df else None
            }
            
        # 生成报告文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(
            self.output_dir,
            f"performance_report_{report_type}_{timestamp}.json"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        return report_file
        
    def plot_resource_distribution(
        self,
        resource_type: str,
        data: Dict[str, Any]
    ) -> str:
        """绘制资源分布图"""
        plt.figure(figsize=(12, 6))
        
        if resource_type == 'grammar':
            # 统计规则类型分布
            rule_types = [rule['type'] for rule in data['rules']]
            sns.countplot(y=rule_types)
            plt.title('语法规则类型分布')
            plt.xlabel('数量')
            plt.ylabel('规则类型')
            
        elif resource_type == 'lexicon':
            # 统计词类分布
            word_classes = [info['word_class'] for info in data.values()]
            sns.countplot(y=word_classes)
            plt.title('词典词类分布')
            plt.xlabel('数量')
            plt.ylabel('词类')
            
        elif resource_type == 'terminology':
            # 统计术语领域分布
            domains = [info['domain'] for info in data.values()]
            sns.countplot(y=domains)
            plt.title('术语领域分布')
            plt.xlabel('数量')
            plt.ylabel('领域')
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            self.output_dir,
            f"{resource_type}_distribution_{timestamp}.png"
        )
        plt.savefig(output_file)
        plt.close()
        
        return output_file
