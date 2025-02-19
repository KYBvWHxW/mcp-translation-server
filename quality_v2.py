from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import numpy as np
from transformers import MT5Tokenizer, MT5ForConditionalGeneration
import torch
import json
import os
import time
from collections import defaultdict
from errors import ValidationError
from concurrent.futures import ThreadPoolExecutor

@dataclass
class QualityDimension:
    """质量维度"""
    name: str
    weight: float
    threshold: float
    features: Set[str]

@dataclass
class EnhancedQualityMetrics:
    """增强版质量指标"""
    fluency: float  # 流畅度
    adequacy: float  # 充分度
    consistency: float  # 一致性
    grammar_score: float  # 语法得分
    terminology_score: float  # 术语准确度
    style_score: float  # 文体得分
    cultural_score: float  # 文化适应度
    overall_score: float  # 总体得分
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    error_types: List[str] = field(default_factory=list)
    
    @property
    def as_dict(self) -> Dict[str, any]:
        return {
            'fluency': self.fluency,
            'adequacy': self.adequacy,
            'consistency': self.consistency,
            'grammar_score': self.grammar_score,
            'terminology_score': self.terminology_score,
            'style_score': self.style_score,
            'cultural_score': self.cultural_score,
            'overall_score': self.overall_score,
            'dimension_scores': self.dimension_scores,
            'error_types': self.error_types
        }

@dataclass
class EnhancedUserFeedback:
    """增强版用户反馈"""
    translation_id: str
    source_text: str
    translated_text: str
    rating: int  # 1-5分
    dimension_ratings: Dict[str, int]  # 各维度评分
    feedback_text: Optional[str]
    correction: Optional[str]
    error_tags: List[str]  # 错误标签
    timestamp: float
    user_id: Optional[str]
    context: Dict[str, any] = field(default_factory=dict)

class QualityModelWrapper:
    """质量评估模型包装器"""
    
    def __init__(self, model_name: str = 'google/mt5-small'):
        self.model = None
        self.tokenizer = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model_name = model_name
        
    def ensure_model_loaded(self):
        """确保模型已加载"""
        if self.model is None:
            self.model = MT5ForConditionalGeneration.from_pretrained(
                self.model_name
            )
            self.model.to(self.device)
            
        if self.tokenizer is None:
            self.tokenizer = MT5Tokenizer.from_pretrained(self.model_name)
            
    def calculate_perplexity(self, text: str) -> float:
        """计算困惑度"""
        self.ensure_model_loaded()
        
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=128
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs, labels=inputs['input_ids'])
            return torch.exp(outputs.loss).item()
            
    def calculate_similarity(
        self,
        text1: str,
        text2: str,
        pooling: str = 'mean'
    ) -> float:
        """计算文本相似度"""
        self.ensure_model_loaded()
        
        # 获取文本嵌入
        def get_embedding(text):
            inputs = self.tokenizer(
                text,
                return_tensors='pt',
                padding=True,
                truncation=True,
                max_length=128
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.encoder(**inputs)
                if pooling == 'mean':
                    return outputs.last_hidden_state.mean(dim=1)
                else:  # max pooling
                    return outputs.last_hidden_state.max(dim=1).values
                    
        emb1 = get_embedding(text1)
        emb2 = get_embedding(text2)
        
        # 计算余弦相似度
        similarity = torch.nn.functional.cosine_similarity(
            emb1, emb2
        ).item()
        
        return (similarity + 1) / 2  # 归一化到 [0,1]

class EnhancedQualityEvaluator:
    """增强版质量评估器"""
    
    def __init__(
        self,
        feedback_file: str = "data/feedback_v2.json",
        terminology_file: str = "resources/terminology.json"
    ):
        self.feedback_file = feedback_file
        self.terminology_file = terminology_file
        self.feedback_data: List[EnhancedUserFeedback] = []
        self.terminology: Dict[str, Dict] = {}
        self.quality_dimensions = self._init_dimensions()
        self.error_patterns = self._init_error_patterns()
        self.model = QualityModelWrapper()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 加载资源
        self.load_feedback()
        self.load_terminology()
        
    def _init_dimensions(self) -> Dict[str, QualityDimension]:
        """初始化质量维度"""
        return {
            'fluency': QualityDimension(
                name='fluency',
                weight=0.2,
                threshold=0.7,
                features={'language_model', 'grammar'}
            ),
            'adequacy': QualityDimension(
                name='adequacy',
                weight=0.2,
                threshold=0.7,
                features={'semantic_similarity', 'terminology'}
            ),
            'consistency': QualityDimension(
                name='consistency',
                weight=0.15,
                threshold=0.7,
                features={'term_consistency', 'style_consistency'}
            ),
            'grammar': QualityDimension(
                name='grammar',
                weight=0.15,
                threshold=0.7,
                features={'syntax', 'morphology'}
            ),
            'terminology': QualityDimension(
                name='terminology',
                weight=0.1,
                threshold=0.8,
                features={'term_accuracy', 'term_coverage'}
            ),
            'style': QualityDimension(
                name='style',
                weight=0.1,
                threshold=0.7,
                features={'register', 'formality'}
            ),
            'cultural': QualityDimension(
                name='cultural',
                weight=0.1,
                threshold=0.7,
                features={'cultural_elements', 'localization'}
            )
        }
        
    def _init_error_patterns(self) -> Dict[str, Dict]:
        """初始化错误模式"""
        return {
            'grammar': {
                'pattern': r'...',  # TODO: 添加具体模式
                'severity': 0.8
            },
            'terminology': {
                'pattern': r'...',  # TODO: 添加具体模式
                'severity': 0.9
            },
            'style': {
                'pattern': r'...',  # TODO: 添加具体模式
                'severity': 0.6
            }
        }
        
    def load_feedback(self):
        """加载用户反馈数据"""
        if os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.feedback_data = [
                    EnhancedUserFeedback(**item) for item in data
                ]
                
    def load_terminology(self):
        """加载术语库"""
        if os.path.exists(self.terminology_file):
            with open(self.terminology_file, 'r', encoding='utf-8') as f:
                self.terminology = json.load(f)
                
    def save_feedback(self):
        """保存用户反馈数据"""
        data = [feedback.__dict__ for feedback in self.feedback_data]
        os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def add_feedback(self, feedback: EnhancedUserFeedback):
        """添加新的用户反馈"""
        if not 1 <= feedback.rating <= 5:
            raise ValidationError("评分必须在1-5分之间")
            
        self.feedback_data.append(feedback)
        self.save_feedback()
        
    def evaluate_translation(
        self,
        source_text: str,
        translated_text: str,
        reference_text: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> EnhancedQualityMetrics:
        """评估翻译质量"""
        # 并行评估各个维度
        futures = {
            'fluency': self.executor.submit(
                self._evaluate_fluency, translated_text
            ),
            'adequacy': self.executor.submit(
                self._evaluate_adequacy, source_text, translated_text
            ),
            'consistency': self.executor.submit(
                self._evaluate_consistency, translated_text, reference_text
            ),
            'grammar': self.executor.submit(
                self._evaluate_grammar, translated_text
            ),
            'terminology': self.executor.submit(
                self._evaluate_terminology, source_text, translated_text
            ),
            'style': self.executor.submit(
                self._evaluate_style, translated_text, context
            ),
            'cultural': self.executor.submit(
                self._evaluate_cultural, translated_text, context
            )
        }
        
        # 收集结果
        dimension_scores = {}
        for name, future in futures.items():
            dimension_scores[name] = future.result()
            
        # 检测错误
        error_types = self._detect_errors(translated_text)
        
        # 计算总分
        overall_score = sum(
            score * self.quality_dimensions[dim].weight
            for dim, score in dimension_scores.items()
        )
        
        return EnhancedQualityMetrics(
            fluency=dimension_scores['fluency'],
            adequacy=dimension_scores['adequacy'],
            consistency=dimension_scores['consistency'],
            grammar_score=dimension_scores['grammar'],
            terminology_score=dimension_scores['terminology'],
            style_score=dimension_scores['style'],
            cultural_score=dimension_scores['cultural'],
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            error_types=error_types
        )
        
    def _evaluate_fluency(self, text: str) -> float:
        """评估流畅度"""
        # 使用语言模型计算困惑度
        perplexity = self.model.calculate_perplexity(text)
        # 将困惑度映射到 [0,1] 区间
        return 1.0 / (1.0 + np.log1p(perplexity))
        
    def _evaluate_adequacy(
        self,
        source_text: str,
        translated_text: str
    ) -> float:
        """评估充分度"""
        # 计算语义相似度
        similarity = self.model.calculate_similarity(
            source_text,
            translated_text
        )
        return similarity
        
    def _evaluate_consistency(
        self,
        translated_text: str,
        reference_text: Optional[str]
    ) -> float:
        """评估一致性"""
        if not reference_text:
            return 0.8  # 默认分数
            
        return self.model.calculate_similarity(
            translated_text,
            reference_text
        )
        
    def _evaluate_grammar(self, text: str) -> float:
        """评估语法正确性"""
        # TODO: 实现语法检查
        return 0.8
        
    def _evaluate_terminology(
        self,
        source_text: str,
        translated_text: str
    ) -> float:
        """评估术语准确性"""
        # TODO: 实现术语检查
        return 0.9
        
    def _evaluate_style(
        self,
        text: str,
        context: Optional[Dict]
    ) -> float:
        """评估文体风格"""
        # TODO: 实现文体评估
        return 0.8
        
    def _evaluate_cultural(
        self,
        text: str,
        context: Optional[Dict]
    ) -> float:
        """评估文化适应度"""
        # TODO: 实现文化适应度评估
        return 0.8
        
    def _detect_errors(self, text: str) -> List[str]:
        """检测错误类型"""
        errors = []
        for error_type, pattern in self.error_patterns.items():
            # TODO: 实现错误检测
            pass
        return errors
        
    def get_historical_metrics(
        self,
        time_range: Optional[Tuple[float, float]] = None
    ) -> Dict[str, any]:
        """获取历史质量指标统计"""
        relevant_feedback = self.feedback_data
        if time_range:
            start_time, end_time = time_range
            relevant_feedback = [
                f for f in self.feedback_data
                if start_time <= f.timestamp <= end_time
            ]
            
        if not relevant_feedback:
            return {
                'average_rating': 0.0,
                'feedback_count': 0,
                'dimension_ratings': {},
                'common_errors': []
            }
            
        # 计算平均评分
        ratings = [f.rating for f in relevant_feedback]
        
        # 计算维度评分
        dimension_ratings = defaultdict(list)
        for f in relevant_feedback:
            for dim, rating in f.dimension_ratings.items():
                dimension_ratings[dim].append(rating)
                
        avg_dimension_ratings = {
            dim: sum(ratings) / len(ratings)
            for dim, ratings in dimension_ratings.items()
        }
        
        # 统计常见错误
        error_counts = defaultdict(int)
        for f in relevant_feedback:
            for error in f.error_tags:
                error_counts[error] += 1
                
        common_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'average_rating': sum(ratings) / len(ratings),
            'feedback_count': len(ratings),
            'dimension_ratings': avg_dimension_ratings,
            'common_errors': common_errors
        }
        
    def get_improvement_suggestions(
        self,
        metrics: EnhancedQualityMetrics
    ) -> Dict[str, List[str]]:
        """基于质量指标生成改进建议"""
        suggestions = defaultdict(list)
        
        # 检查每个维度
        for dim_name, dimension in self.quality_dimensions.items():
            score = metrics.dimension_scores.get(dim_name, 0.0)
            if score < dimension.threshold:
                suggestions[dim_name].extend(
                    self._generate_dimension_suggestions(
                        dim_name, score, metrics
                    )
                )
                
        return dict(suggestions)
        
    def _generate_dimension_suggestions(
        self,
        dimension: str,
        score: float,
        metrics: EnhancedQualityMetrics
    ) -> List[str]:
        """生成特定维度的改进建议"""
        suggestions = []
        
        if dimension == 'fluency' and score < 0.7:
            suggestions.append("提高译文流畅度，使用更自然的表达")
            
        elif dimension == 'adequacy' and score < 0.7:
            suggestions.append("确保译文完整传达源文本的含义")
            
        elif dimension == 'consistency' and score < 0.7:
            suggestions.append("保持术语翻译的一致性")
            
        elif dimension == 'grammar' and score < 0.7:
            suggestions.append("注意语法正确性，特别是时态和语序")
            
        elif dimension == 'terminology' and score < 0.8:
            suggestions.append("严格遵守术语表中的标准译法")
            
        elif dimension == 'style' and score < 0.7:
            suggestions.append("注意文体风格的一致性")
            
        elif dimension == 'cultural' and score < 0.7:
            suggestions.append("考虑目标语言的文化背景")
            
        return suggestions
