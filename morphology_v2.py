from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from errors import MorphologyError

class WordClass(Enum):
    """词类"""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PARTICLE = "particle"
    PRONOUN = "pronoun"
    POSTPOSITION = "postposition"
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"

class MorphemeType(Enum):
    """词素类型"""
    ROOT = "root"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    INFIX = "infix"
    STEM = "stem"

@dataclass
class Morpheme:
    """词素"""
    form: str
    type: MorphemeType
    features: Set[str] = field(default_factory=set)
    allomorphs: List[str] = field(default_factory=list)
    gloss: str = ""

@dataclass
class MorphologicalRule:
    """形态规则"""
    rule_id: str
    word_class: WordClass
    pattern: str
    replacement: str
    conditions: List[str]
    features: Set[str]
    priority: int
    examples: List[Dict[str, str]]

@dataclass
class AnalysisResult:
    """形态分析结果"""
    word: str
    word_class: WordClass
    morphemes: List[Morpheme]
    features: Set[str]
    gloss: str
    confidence: float

class EnhancedMorphologyAnalyzer:
    """增强版形态分析器"""
    
    def __init__(
        self,
        rules_path: str = "resources/morphology_v2.json",
        lexicon_path: str = "resources/lexicon_v2.json"
    ):
        self.rules: Dict[str, MorphologicalRule] = {}
        self.lexicon: Dict[str, Dict] = {}
        self.word_class_index = {}
        self.feature_index = defaultdict(set)
        
        # 加载资源
        self._load_rules(rules_path)
        self._load_lexicon(lexicon_path)
        self._build_indices()
        
    def _load_rules(self, path: str):
        """加载形态规则"""
        if not os.path.exists(path):
            return
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for rule_data in data:
            rule = MorphologicalRule(**rule_data)
            self.rules[rule.rule_id] = rule
            
    def _load_lexicon(self, path: str):
        """加载词典"""
        if not os.path.exists(path):
            return
            
        with open(path, 'r', encoding='utf-8') as f:
            self.lexicon = json.load(f)
            
    def _build_indices(self):
        """构建索引"""
        # 词类索引
        for word, info in self.lexicon.items():
            word_class = WordClass(info['word_class'])
            self.word_class_index[word] = word_class
            
        # 特征索引
        for rule in self.rules.values():
            for feature in rule.features:
                self.feature_index[feature].add(rule.rule_id)
                
    def analyze_word(self, word: str) -> AnalysisResult:
        """分析单词"""
        try:
            # 基本词典查找
            if word in self.lexicon:
                return self._analyze_known_word(word)
                
            # 未知词分析
            return self._analyze_unknown_word(word)
            
        except Exception as e:
            raise MorphologyError(
                f"分析词 '{word}' 时出错: {str(e)}",
                error_code="ANALYSIS_ERROR"
            )
            
    def _analyze_known_word(self, word: str) -> AnalysisResult:
        """分析已知词"""
        info = self.lexicon[word]
        word_class = WordClass(info['word_class'])
        
        # 构建词素列表
        morphemes = []
        for m in info.get('morphemes', []):
            morpheme = Morpheme(
                form=m['form'],
                type=MorphemeType(m['type']),
                features=set(m.get('features', [])),
                allomorphs=m.get('allomorphs', []),
                gloss=m.get('gloss', '')
            )
            morphemes.append(morpheme)
            
        return AnalysisResult(
            word=word,
            word_class=word_class,
            morphemes=morphemes,
            features=set(info.get('features', [])),
            gloss=info.get('gloss', ''),
            confidence=1.0
        )
        
    def _analyze_unknown_word(self, word: str) -> AnalysisResult:
        """分析未知词"""
        # 尝试形态分析
        candidates = self._generate_analysis_candidates(word)
        
        if not candidates:
            # 如果没有找到候选分析，返回基本分析
            return AnalysisResult(
                word=word,
                word_class=WordClass.NOUN,  # 默认假设为名词
                morphemes=[
                    Morpheme(
                        form=word,
                        type=MorphemeType.ROOT,
                        features=set(),
                        gloss=word
                    )
                ],
                features=set(),
                gloss=word,
                confidence=0.1
            )
            
        # 选择最佳候选
        return self._select_best_candidate(candidates)
        
    def _generate_analysis_candidates(
        self,
        word: str
    ) -> List[AnalysisResult]:
        """生成分析候选"""
        candidates = []
        
        # 应用形态规则
        for rule in self.rules.values():
            if self._check_rule_conditions(rule, word):
                result = self._apply_morphological_rule(rule, word)
                if result:
                    candidates.append(result)
                    
        return candidates
        
    def _check_rule_conditions(
        self,
        rule: MorphologicalRule,
        word: str
    ) -> bool:
        """检查规则条件"""
        # TODO: 实现规则条件检查
        return True
        
    def _apply_morphological_rule(
        self,
        rule: MorphologicalRule,
        word: str
    ) -> Optional[AnalysisResult]:
        """应用形态规则"""
        # TODO: 实现规则应用
        return None
        
    def _select_best_candidate(
        self,
        candidates: List[AnalysisResult]
    ) -> AnalysisResult:
        """选择最佳候选分析"""
        # 按置信度排序
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        return candidates[0]
        
    def generate_word_form(
        self,
        root: str,
        features: Set[str]
    ) -> str:
        """生成词形变化"""
        try:
            # 查找适用的规则
            applicable_rules = []
            for feature in features:
                applicable_rules.extend(self.feature_index[feature])
                
            # 按优先级排序
            rules = sorted(
                [self.rules[r] for r in set(applicable_rules)],
                key=lambda x: x.priority,
                reverse=True
            )
            
            # 依次应用规则
            word = root
            for rule in rules:
                if self._check_rule_conditions(rule, word):
                    word = self._apply_rule_generation(rule, word)
                    
            return word
            
        except Exception as e:
            raise MorphologyError(
                f"生成词形 '{root}' 时出错: {str(e)}",
                error_code="GENERATION_ERROR"
            )
            
    def _apply_rule_generation(
        self,
        rule: MorphologicalRule,
        word: str
    ) -> str:
        """应用规则生成词形"""
        # TODO: 实现规则应用生成
        return word
