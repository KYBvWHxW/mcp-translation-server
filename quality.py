from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from transformers import MT5Tokenizer
import json
import os
from errors import ValidationError

@dataclass
class QualityMetrics:
    """翻译质量指标"""
    fluency: float  # 流畅度
    adequacy: float  # 充分度
    consistency: float  # 一致性
    grammar_score: float  # 语法得分
    overall_score: float  # 总体得分
    
    @property
    def as_dict(self) -> Dict[str, float]:
        return {
            'fluency': self.fluency,
            'adequacy': self.adequacy,
            'consistency': self.consistency,
            'grammar_score': self.grammar_score,
            'overall_score': self.overall_score
        }

@dataclass
class UserFeedback:
    """用户反馈"""
    translation_id: str
    source_text: str
    translated_text: str
    rating: int  # 1-5分
    feedback_text: Optional[str]
    correction: Optional[str]
    timestamp: float
    user_id: Optional[str]

class QualityEvaluator:
    """翻译质量评估器"""
    
    def __init__(
        self,
        tokenizer: MT5Tokenizer,
        feedback_file: str = "data/feedback.json"
    ):
        self.tokenizer = tokenizer
        self.feedback_file = feedback_file
        self.feedback_data: List[UserFeedback] = []
        self.load_feedback()
        
    def load_feedback(self):
        """加载用户反馈数据"""
        if os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.feedback_data = [UserFeedback(**item) for item in data]
                
    def save_feedback(self):
        """保存用户反馈数据"""
        data = [feedback.__dict__ for feedback in self.feedback_data]
        os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def add_feedback(self, feedback: UserFeedback):
        """添加新的用户反馈"""
        if not 1 <= feedback.rating <= 5:
            raise ValidationError("评分必须在1-5分之间")
            
        self.feedback_data.append(feedback)
        self.save_feedback()
        
    def evaluate_translation(
        self,
        source_text: str,
        translated_text: str,
        reference_text: Optional[str] = None
    ) -> QualityMetrics:
        """评估翻译质量"""
        # 计算流畅度（基于语言模型）
        fluency = self._evaluate_fluency(translated_text)
        
        # 计算充分度（与源文本的语义相似度）
        adequacy = self._evaluate_adequacy(source_text, translated_text)
        
        # 计算一致性（如果有参考译文）
        consistency = (
            self._evaluate_consistency(translated_text, reference_text)
            if reference_text
            else 0.0
        )
        
        # 计算语法得分
        grammar_score = self._evaluate_grammar(translated_text)
        
        # 计算总体得分
        weights = {
            'fluency': 0.3,
            'adequacy': 0.3,
            'consistency': 0.2,
            'grammar': 0.2
        }
        
        overall_score = (
            weights['fluency'] * fluency +
            weights['adequacy'] * adequacy +
            weights['consistency'] * consistency +
            weights['grammar'] * grammar_score
        )
        
        return QualityMetrics(
            fluency=fluency,
            adequacy=adequacy,
            consistency=consistency,
            grammar_score=grammar_score,
            overall_score=overall_score
        )
        
    def _evaluate_fluency(self, text: str) -> float:
        """评估文本流畅度"""
        # 使用语言模型计算困惑度
        tokens = self.tokenizer.encode(text, return_tensors="pt")
        # TODO: 实现语言模型评分
        return 0.8  # 临时返回固定值
        
    def _evaluate_adequacy(
        self,
        source_text: str,
        translated_text: str
    ) -> float:
        """评估翻译充分度"""
        # 计算源文本和译文的语义相似度
        # TODO: 实现语义相似度计算
        return 0.7  # 临时返回固定值
        
    def _evaluate_consistency(
        self,
        translated_text: str,
        reference_text: str
    ) -> float:
        """评估与参考译文的一致性"""
        # 计算与参考译文的相似度
        # TODO: 实现参考译文相似度计算
        return 0.9  # 临时返回固定值
        
    def _evaluate_grammar(self, text: str) -> float:
        """评估语法正确性"""
        # 使用语法检查器评估
        # TODO: 实现语法检查
        return 0.8  # 临时返回固定值
        
    def get_historical_metrics(
        self,
        time_range: Optional[Tuple[float, float]] = None
    ) -> Dict[str, float]:
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
                'feedback_count': 0
            }
            
        ratings = [f.rating for f in relevant_feedback]
        return {
            'average_rating': sum(ratings) / len(ratings),
            'feedback_count': len(ratings)
        }
        
    def get_improvement_suggestions(
        self,
        metrics: QualityMetrics
    ) -> List[str]:
        """基于质量指标生成改进建议"""
        suggestions = []
        
        if metrics.fluency < 0.7:
            suggestions.append("提高译文流畅度，使用更自然的表达")
            
        if metrics.adequacy < 0.7:
            suggestions.append("提高译文准确度，确保传达源文本的完整含义")
            
        if metrics.consistency < 0.7:
            suggestions.append("保持术语翻译的一致性")
            
        if metrics.grammar_score < 0.7:
            suggestions.append("改进语法正确性")
            
        return suggestions
