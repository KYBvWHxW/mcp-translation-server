from flask import Flask, request, jsonify
import torch
import time
import threading
from typing import Dict, List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor

from morphology_v2 import EnhancedMorphologyAnalyzer
from grammar_v2 import EnhancedGrammarEngine
from quality import QualityEvaluator, UserFeedback
from rate_limiter import RateLimiter, RateLimitRule, BatchProcessor
from errors import *
from config import Config

app = Flask(__name__)

class TranslationServerV2:
    """增强版翻译服务器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.morphology = EnhancedMorphologyAnalyzer()
        self.grammar = EnhancedGrammarEngine()
        self.quality_evaluator = None
        
        # 初始化限流器
        self.rate_limiter = RateLimiter()
        self.rate_limiter.add_rule('translate', RateLimitRule(
            requests_per_second=10,
            burst_size=20
        ))
        self.rate_limiter.add_rule('batch_translate', RateLimitRule(
            requests_per_second=2,
            burst_size=5
        ))
        
        # 初始化批处理器
        self.batch_processor = BatchProcessor(
            batch_size=self.config.model.batch_size,
            max_wait_time=5.0
        )
        
        # 初始化线程池
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.server.workers
        )
        
        # 延迟加载模型
        self.model_lock = threading.Lock()
        
    def ensure_model_loaded(self):
        """确保模型已加载"""
        if self.model is None:
            with self.model_lock:
                if self.model is None:  # 双重检查锁定
                    self._load_model()
                    
    def _load_model(self):
        """加载模型"""
        from transformers import MT5ForConditionalGeneration, MT5Tokenizer
        
        try:
            self.model = MT5ForConditionalGeneration.from_pretrained(
                self.config.model.model_name
            )
            self.model.to(self.config.model.device)
            
            self.tokenizer = MT5Tokenizer.from_pretrained(
                self.config.model.model_name
            )
            
            self.quality_evaluator = QualityEvaluator(self.tokenizer)
            
        except Exception as e:
            raise ModelError(f"加载模型失败: {str(e)}")
            
    def translate(self, text: str) -> Dict:
        """翻译单个文本"""
        try:
            # 确保模型已加载
            self.ensure_model_loaded()
            
            # 形态分析
            analysis = self.morphology.analyze_word(text)
            
            # 应用语法规则
            features = analysis.features
            applicable_rules = self.grammar.find_applicable_rules(
                text, features
            )
            
            # 执行翻译
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                max_length=self.config.model.max_length,
                truncation=True
            )
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs['input_ids'],
                    max_length=self.config.model.max_length,
                    num_beams=self.config.model.beam_size,
                    early_stopping=True
                )
                
            translated_text = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )
            
            # 评估质量
            quality_metrics = self.quality_evaluator.evaluate_translation(
                text,
                translated_text
            )
            
            # 生成改进建议
            suggestions = self.quality_evaluator.get_improvement_suggestions(
                quality_metrics
            )
            
            return {
                'success': True,
                'source_text': text,
                'translated_text': translated_text,
                'analysis': analysis.__dict__,
                'quality_metrics': quality_metrics.as_dict,
                'improvement_suggestions': suggestions
            }
            
        except Exception as e:
            raise ManchuTranslationError(f"翻译失败: {str(e)}")
            
    def batch_translate(
        self,
        texts: List[str],
        batch_id: Optional[str] = None
    ) -> Dict:
        """批量翻译"""
        if not texts:
            raise ValidationError("翻译文本列表不能为空")
            
        if batch_id is None:
            batch_id = f"batch_{int(time.time())}"
            
        try:
            # 将文本添加到批处理队列
            results = {}
            events = []
            
            for i, text in enumerate(texts):
                item_id = f"{batch_id}_{i}"
                event = self.batch_processor.add_to_batch(
                    'translation',
                    text,
                    item_id
                )
                events.append((item_id, event))
                
            # 等待所有文本处理完成
            for item_id, event in events:
                event.wait(timeout=30.0)  # 30秒超时
                result = self.batch_processor.get_result(
                    'translation',
                    item_id
                )
                if result:
                    results[item_id] = result
                    
            return {
                'success': True,
                'batch_id': batch_id,
                'results': results
            }
            
        except Exception as e:
            raise ManchuTranslationError(f"批量翻译失败: {str(e)}")
            
    def add_feedback(
        self,
        translation_id: str,
        rating: int,
        feedback_text: Optional[str] = None,
        correction: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """添加用户反馈"""
        try:
            feedback = UserFeedback(
                translation_id=translation_id,
                source_text="",  # TODO: 存储原文
                translated_text="",  # TODO: 存储译文
                rating=rating,
                feedback_text=feedback_text,
                correction=correction,
                timestamp=time.time(),
                user_id=user_id
            )
            
            self.quality_evaluator.add_feedback(feedback)
            
            return {
                'success': True,
                'message': "反馈已记录"
            }
            
        except Exception as e:
            raise ManchuTranslationError(f"添加反馈失败: {str(e)}")
            
    def get_quality_statistics(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> Dict:
        """获取质量统计信息"""
        try:
            time_range = None
            if start_time and end_time:
                time_range = (start_time, end_time)
                
            metrics = self.quality_evaluator.get_historical_metrics(time_range)
            
            return {
                'success': True,
                'metrics': metrics
            }
            
        except Exception as e:
            raise ManchuTranslationError(f"获取统计信息失败: {str(e)}")

# 创建服务器实例
config = Config()
translation_server = TranslationServerV2(config)

@app.route('/translate', methods=['POST'])
def translate():
    """单个文本翻译接口"""
    if not translation_server.rate_limiter.check_rate_limit('translate'):
        return jsonify({
            'success': False,
            'error': '请求过于频繁，请稍后再试'
        }), 429
        
    try:
        data = request.get_json()
        if not data:
            raise ValidationError('无效的请求数据')
            
        text = data.get('text')
        if not text:
            raise ValidationError('未提供待翻译文本')
            
        result = translation_server.translate(text)
        return jsonify(result)
        
    except ManchuTranslationError as e:
        logging.error(f'Translation error: {str(e)}', exc_info=True)
        return jsonify(format_error_response(e)), 400
        
    except Exception as e:
        logging.error('Unexpected error', exc_info=True)
        return jsonify(format_error_response(
            ManchuTranslationError('服务器内部错误', error_code='INTERNAL_ERROR')
        )), 500

@app.route('/batch_translate', methods=['POST'])
def batch_translate():
    """批量翻译接口"""
    if not translation_server.rate_limiter.check_rate_limit('batch_translate'):
        return jsonify({
            'success': False,
            'error': '请求过于频繁，请稍后再试'
        }), 429
        
    try:
        data = request.get_json()
        if not data:
            raise ValidationError('无效的请求数据')
            
        texts = data.get('texts')
        if not texts:
            raise ValidationError('未提供待翻译文本列表')
            
        batch_id = data.get('batch_id')
        result = translation_server.batch_translate(texts, batch_id)
        return jsonify(result)
        
    except ManchuTranslationError as e:
        logging.error(f'Batch translation error: {str(e)}', exc_info=True)
        return jsonify(format_error_response(e)), 400
        
    except Exception as e:
        logging.error('Unexpected error', exc_info=True)
        return jsonify(format_error_response(
            ManchuTranslationError('服务器内部错误', error_code='INTERNAL_ERROR')
        )), 500

@app.route('/feedback', methods=['POST'])
def add_feedback():
    """添加用户反馈"""
    try:
        data = request.get_json()
        if not data:
            raise ValidationError('无效的请求数据')
            
        result = translation_server.add_feedback(
            translation_id=data.get('translation_id'),
            rating=data.get('rating'),
            feedback_text=data.get('feedback_text'),
            correction=data.get('correction'),
            user_id=data.get('user_id')
        )
        return jsonify(result)
        
    except ManchuTranslationError as e:
        logging.error(f'Feedback error: {str(e)}', exc_info=True)
        return jsonify(format_error_response(e)), 400
        
    except Exception as e:
        logging.error('Unexpected error', exc_info=True)
        return jsonify(format_error_response(
            ManchuTranslationError('服务器内部错误', error_code='INTERNAL_ERROR')
        )), 500

@app.route('/quality_statistics', methods=['GET'])
def get_quality_statistics():
    """获取质量统计信息"""
    try:
        start_time = request.args.get('start_time', type=float)
        end_time = request.args.get('end_time', type=float)
        
        result = translation_server.get_quality_statistics(
            start_time,
            end_time
        )
        return jsonify(result)
        
    except ManchuTranslationError as e:
        logging.error(f'Statistics error: {str(e)}', exc_info=True)
        return jsonify(format_error_response(e)), 400
        
    except Exception as e:
        logging.error('Unexpected error', exc_info=True)
        return jsonify(format_error_response(
            ManchuTranslationError('服务器内部错误', error_code='INTERNAL_ERROR')
        )), 500

if __name__ == "__main__":
    app.run(
        host=config.server.host,
        port=config.server.port,
        debug=config.server.debug
    )
