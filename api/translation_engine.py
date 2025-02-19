"""满汉双向翻译引擎

使用Transformer模型实现满-汉双向翻译。
"""

from typing import List, Dict, Optional
import torch
from transformers import MarianMTModel, MarianTokenizer
from .base import BaseComponent

class TranslationEngine(BaseComponent):
    """满汉双向翻译引擎"""
    
    def __init__(self, model_path: str = "models/manchu-chinese"):
        """初始化翻译引擎
        
        Args:
            model_path: 模型路径，默认为本地模型
        """
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ready = False
        
        try:
            self.tokenizer = MarianTokenizer.from_pretrained(model_path)
            self.model = MarianMTModel.from_pretrained(model_path).to(self.device)
            self.ready = True
        except Exception as e:
            print(f"Warning: Failed to load translation model: {str(e)}")
            print("Falling back to rule-based translation")
            self._init_rule_based()
    
    def _init_rule_based(self):
        """初始化基于规则的翻译系统（作为后备）"""
        self.rules = {
            "ᡥᠠᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ": "海的人",
            "ᠠᠯᡳᠨ ᡳ ᠨᡳᠶᠠᠯᠮᠠ": "山的人",
            "ᡥᡡᠸᠠᠩᡩᡳ ᡳ ᡥᡝᡵᡤᡝᠨ": "皇帝的文字",
            "海的人": "ᡥᠠᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",
            "山的人": "ᠠᠯᡳᠨ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",
            "皇帝的文字": "ᡥᡡᠸᠠᠩᡩᡳ ᡳ ᡥᡝᡵᡤᡝᠨ"
        }
    
    def translate(self, text: str, source_lang: str = "manchu", target_lang: str = "chinese") -> str:
        """翻译文本
        
        Args:
            text: 待翻译文本
            source_lang: 源语言，'manchu' 或 'chinese'
            target_lang: 目标语言，'manchu' 或 'chinese'
            
        Returns:
            翻译结果
        """
        if not text:
            return ""
            
        if self.ready:
            # 使用神经网络模型翻译
            try:
                inputs = self.tokenizer(text, return_tensors="pt", padding=True).to(self.device)
                outputs = self.model.generate(**inputs)
                translation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                return translation
            except Exception as e:
                print(f"Warning: Neural translation failed: {str(e)}")
                print("Falling back to rule-based translation")
        
        # 基于规则的翻译（作为后备方案）
        return self.rules.get(text, "[Translation not found]")
    
    def batch_translate(self, texts: List[str], source_lang: str = "manchu", target_lang: str = "chinese") -> List[str]:
        """批量翻译文本
        
        Args:
            texts: 待翻译文本列表
            source_lang: 源语言，'manchu' 或 'chinese'
            target_lang: 目标语言，'manchu' 或 'chinese'
            
        Returns:
            翻译结果列表
        """
        return [self.translate(text, source_lang, target_lang) for text in texts]
    
    def get_status(self) -> Dict:
        """获取引擎状态
        
        Returns:
            包含状态信息的字典
        """
        return {
            "ready": self.ready,
            "model_type": "neural" if self.ready else "rule-based",
            "device": str(self.device),
            "model_path": self.model_path
        }
