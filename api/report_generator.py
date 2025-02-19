from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from jinja2 import Template
import json
import base64
from io import BytesIO

class ReportGenerator:
    """高级报表生成器"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置绘图样式
        plt.style.use('seaborn')
        sns.set_palette("husl")
        
    def generate_performance_report(
        self,
        metrics: Dict[str, Any],
        report_type: str = 'full'
    ) -> str:
        """生成性能报告"""
        # 创建图表
        figures = []
        
        # CPU和内存使用趋势
        if 'system_metrics' in metrics:
            fig = self._plot_system_metrics(metrics['system_metrics'])
            figures.append(('system_metrics', fig))
            
        # 请求延迟分布
        if 'latency_metrics' in metrics:
            fig = self._plot_latency_distribution(metrics['latency_metrics'])
            figures.append(('latency_metrics', fig))
            
        # 缓存性能
        if 'cache_metrics' in metrics:
            fig = self._plot_cache_performance(metrics['cache_metrics'])
            figures.append(('cache_metrics', fig))
            
        # 翻译质量指标
        if 'translation_metrics' in metrics:
            fig = self._plot_translation_quality(metrics['translation_metrics'])
            figures.append(('translation_metrics', fig))
            
        # 生成HTML报告
        html_content = self._generate_html_report(metrics, figures)
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(
            self.output_dir,
            f"performance_report_{report_type}_{timestamp}.html"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return report_file
        
    def generate_resource_report(
        self,
        resources: Dict[str, Any]
    ) -> str:
        """生成资源报告"""
        figures = []
        
        # 词典分析
        if 'lexicon' in resources:
            fig = self._plot_lexicon_analysis(resources['lexicon'])
            figures.append(('lexicon_analysis', fig))
            
        # 语法规则分析
        if 'grammar' in resources:
            fig = self._plot_grammar_analysis(resources['grammar'])
            figures.append(('grammar_analysis', fig))
            
        # 形态规则分析
        if 'morphology' in resources:
            fig = self._plot_morphology_analysis(resources['morphology'])
            figures.append(('morphology_analysis', fig))
            
        # 术语分析
        if 'terminology' in resources:
            fig = self._plot_terminology_analysis(resources['terminology'])
            figures.append(('terminology_analysis', fig))
            
        # 生成HTML报告
        html_content = self._generate_resource_html_report(resources, figures)
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(
            self.output_dir,
            f"resource_report_{timestamp}.html"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return report_file
        
    def generate_alert_report(
        self,
        alerts: List[Dict[str, Any]]
    ) -> str:
        """生成告警报告"""
        figures = []
        
        # 告警趋势
        fig = self._plot_alert_trend(alerts)
        figures.append(('alert_trend', fig))
        
        # 告警分布
        fig = self._plot_alert_distribution(alerts)
        figures.append(('alert_distribution', fig))
        
        # 生成HTML报告
        html_content = self._generate_alert_html_report(alerts, figures)
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(
            self.output_dir,
            f"alert_report_{timestamp}.html"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return report_file
        
    def _plot_system_metrics(self, metrics: Dict[str, Any]) -> plt.Figure:
        """绘制系统指标"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # CPU使用率
        df = pd.DataFrame(metrics['cpu'])
        sns.lineplot(data=df, ax=ax1)
        ax1.set_title('CPU使用率趋势')
        ax1.set_xlabel('时间')
        ax1.set_ylabel('CPU使用率 (%)')
        
        # 内存使用率
        df = pd.DataFrame(metrics['memory'])
        sns.lineplot(data=df, ax=ax2)
        ax2.set_title('内存使用率趋势')
        ax2.set_xlabel('时间')
        ax2.set_ylabel('内存使用率 (%)')
        
        plt.tight_layout()
        return fig
        
    def _plot_latency_distribution(self, metrics: Dict[str, Any]) -> plt.Figure:
        """绘制延迟分布"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # 延迟直方图
        sns.histplot(data=metrics['latencies'], ax=ax1)
        ax1.set_title('请求延迟分布')
        ax1.set_xlabel('延迟 (秒)')
        ax1.set_ylabel('频率')
        
        # 百分位数
        percentiles = metrics['percentiles']
        sns.barplot(
            x=list(percentiles.keys()),
            y=list(percentiles.values()),
            ax=ax2
        )
        ax2.set_title('延迟百分位数')
        ax2.set_xlabel('百分位')
        ax2.set_ylabel('延迟 (秒)')
        
        plt.tight_layout()
        return fig
        
    def _plot_cache_performance(self, metrics: Dict[str, Any]) -> plt.Figure:
        """绘制缓存性能"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 命中率趋势
        df = pd.DataFrame(metrics['hit_ratio'])
        sns.lineplot(data=df, ax=ax1)
        ax1.set_title('缓存命中率趋势')
        ax1.set_xlabel('时间')
        ax1.set_ylabel('命中率')
        
        # 内存使用趋势
        df = pd.DataFrame(metrics['memory_usage'])
        sns.lineplot(data=df, ax=ax2)
        ax2.set_title('缓存内存使用趋势')
        ax2.set_xlabel('时间')
        ax2.set_ylabel('内存使用 (MB)')
        
        # 驱逐分布
        sns.histplot(data=metrics['evictions'], ax=ax3)
        ax3.set_title('缓存驱逐分布')
        ax3.set_xlabel('每分钟驱逐数')
        ax3.set_ylabel('频率')
        
        # 访问模式
        df = pd.DataFrame(metrics['access_patterns'])
        sns.heatmap(df, ax=ax4)
        ax4.set_title('缓存访问模式')
        
        plt.tight_layout()
        return fig
        
    def _plot_translation_quality(self, metrics: Dict[str, Any]) -> plt.Figure:
        """绘制翻译质量指标"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # BLEU分数趋势
        df = pd.DataFrame(metrics['bleu_scores'])
        sns.lineplot(data=df, ax=ax1)
        ax1.set_title('BLEU分数趋势')
        ax1.set_xlabel('时间')
        ax1.set_ylabel('BLEU分数')
        
        # 错误率趋势
        df = pd.DataFrame(metrics['error_rates'])
        sns.lineplot(data=df, ax=ax2)
        ax2.set_title('错误率趋势')
        ax2.set_xlabel('时间')
        ax2.set_ylabel('错误率')
        
        # 翻译长度分布
        sns.histplot(data=metrics['lengths'], ax=ax3)
        ax3.set_title('翻译长度分布')
        ax3.set_xlabel('长度')
        ax3.set_ylabel('频率')
        
        # 质量评分分布
        sns.boxplot(data=metrics['quality_scores'], ax=ax4)
        ax4.set_title('质量评分分布')
        ax4.set_xlabel('评分维度')
        ax4.set_ylabel('分数')
        
        plt.tight_layout()
        return fig
        
    def _plot_lexicon_analysis(self, lexicon: Dict[str, Any]) -> plt.Figure:
        """绘制词典分析"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 词类分布
        sns.barplot(
            x=list(lexicon['word_classes'].keys()),
            y=list(lexicon['word_classes'].values()),
            ax=ax1
        )
        ax1.set_title('词类分布')
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
        
        # 特征分布
        sns.barplot(
            x=list(lexicon['features'].keys()),
            y=list(lexicon['features'].values()),
            ax=ax2
        )
        ax2.set_title('特征分布')
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
        
        # 翻译数量分布
        sns.histplot(data=lexicon['translations_per_word'], ax=ax3)
        ax3.set_title('每词条翻译数量分布')
        ax3.set_xlabel('翻译数量')
        ax3.set_ylabel('词条数量')
        
        # 词条长度分布
        sns.histplot(data=lexicon['word_lengths'], ax=ax4)
        ax4.set_title('词条长度分布')
        ax4.set_xlabel('长度')
        ax4.set_ylabel('频率')
        
        plt.tight_layout()
        return fig
        
    def _generate_html_report(
        self,
        metrics: Dict[str, Any],
        figures: List[tuple]
    ) -> str:
        """生成HTML报告"""
        # 转换图表为base64
        images = {}
        for name, fig in figures:
            buf = BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            images[name] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
        # 使用模板生成HTML
        template = Template('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>性能报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .section { margin: 20px 0; }
                .chart { margin: 20px 0; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f5f5f5; }
            </style>
        </head>
        <body>
            <h1>性能报告</h1>
            <div class="section">
                <h2>系统性能</h2>
                <img src="data:image/png;base64,{{ images.system_metrics }}" />
            </div>
            <div class="section">
                <h2>延迟分析</h2>
                <img src="data:image/png;base64,{{ images.latency_metrics }}" />
            </div>
            <div class="section">
                <h2>缓存性能</h2>
                <img src="data:image/png;base64,{{ images.cache_metrics }}" />
            </div>
            <div class="section">
                <h2>翻译质量</h2>
                <img src="data:image/png;base64,{{ images.translation_metrics }}" />
            </div>
            <div class="section">
                <h2>详细指标</h2>
                <pre>{{ metrics | tojson(indent=2) }}</pre>
            </div>
        </body>
        </html>
        ''')
        
        return template.render(images=images, metrics=metrics)
        
    def _figure_to_base64(self, fig: plt.Figure) -> str:
        """将图表转换为base64编码"""
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
