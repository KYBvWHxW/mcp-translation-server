import regex as re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum, auto
from .base import BaseComponent

class MorphologyError(Exception):
    """形态分析器错误基类"""
    pass

class InvalidInputError(MorphologyError):
    """输入验证错误"""
    pass

class AnalysisError(MorphologyError):
    """分析过程错误"""
    pass

class WordClass(Enum):
    """词类"""
    NOUN = auto()
    VERB = auto()
    ADJECTIVE = auto()
    PRONOUN = auto()
    PARTICLE = auto()
    UNKNOWN = auto()

@dataclass
class MorphemeRule:
    """形态素规则"""
    pattern: str  # 形态素模式
    replacement: str  # 替换形式
    environment: str  # 音韵环境
    word_class: List[WordClass]  # 适用词类
    priority: int  # 规则优先级

@dataclass
class StemChange:
    """词干变化"""
    original: str  # 原始形式
    modified: str  # 变化形式
    suffix: str  # 触发变化的后缀
    rule_id: str  # 应用的规则ID

class ManchuMorphologyAnalyzer(BaseComponent):
    """满文形态学分析器"""
    
    def __init__(self):
        # 加载后缀数据
        self.suffixes = self._load_suffixes()
        # 加载词干变化规则
        self.stem_changes = self._load_stem_changes()
        # 加载形态素规则
        self.morpheme_rules = self._load_morpheme_rules()
        # 编译正则表达式
        self._compile_patterns()
        # 组件状态
        self.ready = True
        
    def _load_stem_changes(self) -> List[MorphemeRule]:
        """加载词干变化规则"""
        return [
            # 元音和谐规则
            MorphemeRule(
                pattern=r'([aeiouāēīōū])([^aeiouāēīōū]*)(me|mbi)',
                replacement=r'\1\2\3',
                environment='V_C*_suffix',
                word_class=[WordClass.VERB],
                priority=1
            ),
            # 辅音同化规则
            MorphemeRule(
                pattern=r'([ptk])\s*(be|de)',
                replacement=r'\1\2',
                environment='C_#_suffix',
                word_class=[WordClass.NOUN, WordClass.PRONOUN],
                priority=2
            ),
            # 元音缩减规则
            MorphemeRule(
                pattern=r'([aeiouāēīōū])\1+',
                replacement=r'\1',
                environment='VV+',
                word_class=[WordClass.VERB, WordClass.NOUN],
                priority=3
            )
        ]
        
    def _load_morpheme_rules(self) -> List[MorphemeRule]:
        """加载形态素规则"""
        return [
            # 代词特殊变化
            MorphemeRule(
                pattern=r'bi\s*be',
                replacement='mimbe',
                environment='#_suffix',
                word_class=[WordClass.PRONOUN],
                priority=1
            ),
            MorphemeRule(
                pattern=r'si\s*be',
                replacement='simbe',
                environment='#_suffix',
                word_class=[WordClass.PRONOUN],
                priority=1
            ),
            # 动词词干变化
            MorphemeRule(
                pattern=r'([^aeiouāēīōū])\s*ra',
                replacement=r'\1re',
                environment='C_suffix',
                word_class=[WordClass.VERB],
                priority=2
            )
        ]
        
    def _load_suffixes(self) -> Dict[str, Dict]:
        """加载满文后缀数据"""
        return {
            # 动词后缀
            "verbal": {
                "me": {"type": "converb", "function": "simultaneous", "word_class": [WordClass.VERB]},
                "fi": {"type": "participle", "function": "perfective", "word_class": [WordClass.VERB]},
                "ha": {"type": "participle", "function": "perfective", "word_class": [WordClass.VERB]},
                "mbi": {"type": "finite", "function": "imperfective", "word_class": [WordClass.VERB]},
                "habi": {"type": "finite", "function": "perfect", "word_class": [WordClass.VERB]},
                "ra": {"type": "finite", "function": "aorist", "word_class": [WordClass.VERB]},
                "ki": {"type": "finite", "function": "optative", "word_class": [WordClass.VERB]},
                "kini": {"type": "finite", "function": "optative_plural", "word_class": [WordClass.VERB]},
                "cina": {"type": "converb", "function": "conditional", "word_class": [WordClass.VERB]},
                "hai": {"type": "converb", "function": "concessive", "word_class": [WordClass.VERB]},
                "nggala": {"type": "converb", "function": "terminative", "word_class": [WordClass.VERB]},
                "rakv": {"type": "finite", "function": "negative_aorist", "word_class": [WordClass.VERB]},
                "hakv": {"type": "finite", "function": "negative_perfect", "word_class": [WordClass.VERB]}
            },
            # 名词后缀
            "nominal": {
                "be": {"type": "case", "function": "accusative", "word_class": [WordClass.NOUN, WordClass.PRONOUN]},
                "de": {"type": "case", "function": "dative-locative", "word_class": [WordClass.NOUN, WordClass.PRONOUN]},
                "i": {"type": "case", "function": "genitive", "word_class": [WordClass.NOUN]},
                "ci": {"type": "case", "function": "ablative", "word_class": [WordClass.NOUN, WordClass.PRONOUN]},
                "ningge": {"type": "nominalizer", "function": "possessive", "word_class": [WordClass.NOUN]},
                "sa": {"type": "number", "function": "plural", "word_class": [WordClass.NOUN]},
                "ta": {"type": "number", "function": "plural_collective", "word_class": [WordClass.NOUN]},
                "si": {"type": "number", "function": "plural_distributive", "word_class": [WordClass.NOUN]}
            },
            # 形容词后缀
            "adjectival": {
                "ngge": {"type": "nominalizer", "function": "attributive", "word_class": [WordClass.ADJECTIVE]},
                "kan": {"type": "diminutive", "function": "diminutive", "word_class": [WordClass.ADJECTIVE]},
                "kun": {"type": "augmentative", "function": "augmentative", "word_class": [WordClass.ADJECTIVE]},
                "shun": {"type": "degree", "function": "comparative", "word_class": [WordClass.ADJECTIVE]},
                "seri": {"type": "degree", "function": "superlative", "word_class": [WordClass.ADJECTIVE]}
            }
        }
    
    def _compile_patterns(self):
        """编译形态学分析所需的正则表达式"""
        # 创建后缀模式
        suffix_pattern = "|".join(
            [suffix for group in self.suffixes.values() for suffix in group.keys()]
        )
        self.suffix_re = re.compile(f"({suffix_pattern})$")
        
        # 创建词根模式（基于满文音节结构）
        self.syllable_re = re.compile(r"[aeiouāēīōū]|[^aeiouāēīōū][aeiouāēīōū]")
        
    def _apply_morpheme_rules(self, word: str) -> str:
        """应用形态素规则
        
        Args:
            word: 输入词形
            
        Returns:
            处理后的词形
        """
        # 应用所有规则
        result = word
        for rule in sorted(self.morpheme_rules, key=lambda x: x.priority):
            if re.search(rule.pattern, result):
                result = re.sub(rule.pattern, rule.replacement, result)
        return result
        
    def _predict_word_class(self, word: str) -> str:
        """预测词类
        
        Args:
            word: 输入词形
            
        Returns:
            预测的词类
        """
        # 基于词形特征进行简单判断
        if word.endswith('mbi'):
            return 'verb'
        elif word.endswith('ngge'):
            return 'adjective'
        elif word.endswith('i'):
            return 'noun'
        else:
            return 'unknown'
            
    def _check_stem_change(self, stem: str, suffix: str) -> Optional[Dict]:
        """检查词干变化
        
        Args:
            stem: 词干
            suffix: 后缀
            
        Returns:
            词干变化信息，如果没有变化则返回None
        """
        # 查找匹配的词干变化规则
        for change in self.stem_changes:
            if re.search(change.pattern, stem) and suffix in change.replacement:
                return {
                    'original': stem,
                    'modified': re.sub(change.pattern, change.replacement, stem),
                    'rule': {
                        'pattern': change.pattern,
                        'replacement': change.replacement,
                        'environment': change.environment,
                        'priority': change.priority
                    }
                }
        return None
    
    def analyze_word(self, word: str) -> Dict:
        """分析单个词的形态结构
        
        Args:
            word: 满文单词
            
        Returns:
            包含词根和后缀信息的字典
            
        Raises:
            InvalidInputError: 输入格式无效
            AnalysisError: 分析过程出错
        """
        # 输入验证
        if not word or not isinstance(word, str):
            raise InvalidInputError("输入必须是非空字符串")
            
        if not re.match(r'^[a-zāēīōū\s]+$', word.lower()):
            raise InvalidInputError("输入包含无效字符")
        try:
            # 应用形态素规则
            normalized_word = self._apply_morpheme_rules(word)
            
            result = {
                "word": word,
                "normalized": normalized_word,
                "root": normalized_word,
                "word_class": self._predict_word_class(normalized_word),
                "suffixes": [],
                "stem_changes": []
            }
        
            # 迭代查找后缀
            while True:
                match = self.suffix_re.search(result["root"])
                if not match:
                    break
                    
                suffix = match.group(1)
                # 在所有后缀类型中查找
                suffix_info = None
                suffix_type = None
                for stype, suffixes in self.suffixes.items():
                    if suffix in suffixes:
                        suffix_info = suffixes[suffix]
                        suffix_type = stype
                        break
                
                if suffix_info:
                    # 验证词类兼容性
                    if result["word_class"] not in suffix_info["word_class"]:
                        # 不是错误，而是警告
                        result["warnings"] = result.get("warnings", []) + [
                            f"后缀 {suffix} 通常不用于{result['word_class']}类词"
                        ]
                    
                    # 检查词干变化
                    stem_change = self._check_stem_change(
                        result["root"], suffix
                    )
                    if stem_change:
                        result["stem_changes"].append(stem_change)
                    
                    # 添加后缀信息
                    result["suffixes"].insert(0, {
                        "form": suffix,
                        "type": suffix_type,
                        "function": suffix_info["type"],
                        "meaning": suffix_info["function"],
                        "word_class": [wc.name for wc in suffix_info["word_class"]]
                    })
                    # 更新词根
                    result["root"] = result["root"][:match.start()]
                else:
                    break
                    
        except Exception as e:
            raise AnalysisError(f"分析过程出错: {str(e)}")
        
        return result
    
    def analyze_sentence(self, sentence: str) -> List[Dict]:
        """分析整个句子中的所有词的形态结构
        
        Args:
            sentence: 满文句子
            
        Returns:
            每个词的形态分析结果列表
        """
        words = sentence.strip().split()
        return [self.analyze_word(word) for word in words]
    
    def get_gloss(self, analysis: Dict) -> str:
        """生成词的注释（gloss）
        
        Args:
            analysis: 词的形态分析结果
            
        Returns:
            词的注释字符串
        """
        parts = [analysis["root"]]
        for suffix in analysis["suffixes"]:
            parts.append(f"-{suffix['meaning']}")
        return "".join(parts)
    
    def get_sentence_gloss(self, sentence_analysis: List[Dict]) -> str:
        """生成整个句子的注释
        
        Args:
            sentence_analysis: 句子的形态分析结果
            
        Returns:
            句子的注释字符串
        """
        return " ".join(self.get_gloss(word) for word in sentence_analysis)
        
    def is_ready(self) -> bool:
        """检查组件是否就绪"""
        return self.ready and hasattr(self, 'suffix_re') and hasattr(self, 'syllable_re')
        
    def get_status(self) -> dict:
        """获取组件状态"""
        return {
            'ready': self.is_ready(),
            'suffix_count': sum(len(group) for group in self.suffixes.values()),
            'stem_change_count': len(self.stem_changes),
            'morpheme_rule_count': len(self.morpheme_rules),
            'patterns_compiled': hasattr(self, 'suffix_re') and hasattr(self, 'syllable_re')
        }
