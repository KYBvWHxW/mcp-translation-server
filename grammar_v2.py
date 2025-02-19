from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
import json
import os
import numpy as np
from collections import defaultdict
from enum import Enum
from errors import GrammarError

class RuleType(Enum):
    WORD_ORDER = "word_order"
    MORPHOLOGICAL = "morphological"
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    PRAGMATIC = "pragmatic"

@dataclass
class GrammarPattern:
    """语法模式"""
    pattern: str  # 模式字符串
    constraints: Dict[str, str] = field(default_factory=dict)  # 约束条件
    transformations: List[str] = field(default_factory=list)  # 转换规则

@dataclass
class GrammarRuleV2:
    """增强版语法规则"""
    rule_id: str
    type: RuleType
    category: str
    features: Set[str]
    patterns: List[GrammarPattern]
    conditions: List[str]  # 应用条件
    transformations: List[str]  # 转换操作
    priority: int  # 规则优先级
    bidirectional: bool  # 是否双向规则
    examples: List[Dict[str, str]]
    notes: str
    prerequisites: Set[str] = field(default_factory=set)
    conflicts: Set[str] = field(default_factory=set)
    overrides: Set[str] = field(default_factory=set)

class GrammarContext:
    """语法分析上下文"""
    def __init__(self):
        self.features = set()
        self.variables = {}
        self.stack = []
        self.history = []

class EnhancedGrammarEngine:
    """增强版语法引擎"""
    
    def __init__(self, rules_path: str = "resources/grammar_v2.json"):
        self.rules: Dict[str, GrammarRuleV2] = {}
        self.type_index = defaultdict(set)
        self.feature_index = defaultdict(set)
        self.category_index = defaultdict(set)
        self.priority_index = defaultdict(list)
        self.rule_graph = defaultdict(dict)
        
        if os.path.exists(rules_path):
            self._load_rules(rules_path)
            self._build_indices()
            self._build_rule_graph()
            
    def _load_rules(self, path: str):
        """加载增强版语法规则"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for rule_data in data:
            patterns = [
                GrammarPattern(**p) if isinstance(p, dict) else GrammarPattern(p)
                for p in rule_data.pop('patterns', [])
            ]
            rule = GrammarRuleV2(
                **{k: v for k, v in rule_data.items() if k != 'patterns'},
                patterns=patterns
            )
            self.rules[rule.rule_id] = rule
            
    def _build_indices(self):
        """构建规则索引"""
        for rule in self.rules.values():
            self.type_index[rule.type].add(rule.rule_id)
            self.category_index[rule.category].add(rule.rule_id)
            self.priority_index[rule.priority].append(rule.rule_id)
            for feature in rule.features:
                self.feature_index[feature].add(rule.rule_id)
                
    def _build_rule_graph(self):
        """构建规则依赖图"""
        for rule in self.rules.values():
            # 添加前置规则边
            for prereq in rule.prerequisites:
                self.rule_graph[rule.rule_id]['prerequisites'] = prereq
                
            # 添加冲突规则边
            for conflict in rule.conflicts:
                self.rule_graph[rule.rule_id]['conflicts'] = conflict
                
            # 添加覆盖规则边
            for override in rule.overrides:
                self.rule_graph[rule.rule_id]['overrides'] = override
                
    def find_applicable_rules(
        self,
        text: str,
        features: Set[str],
        context: Optional[GrammarContext] = None
    ) -> List[Tuple[GrammarRuleV2, float]]:
        """查找适用的规则并计算相关度"""
        if context is None:
            context = GrammarContext()
            
        applicable_rules = []
        
        # 根据特征过滤规则
        candidate_rules = set()
        for feature in features:
            candidate_rules.update(self.feature_index[feature])
            
        # 评估每个候选规则
        for rule_id in candidate_rules:
            rule = self.rules[rule_id]
            
            # 检查规则条件
            if self._check_conditions(rule, text, context):
                # 计算规则相关度
                relevance = self._calculate_relevance(rule, text, features)
                applicable_rules.append((rule, relevance))
                
        # 按相关度排序
        return sorted(applicable_rules, key=lambda x: x[1], reverse=True)
        
    def _check_conditions(
        self,
        rule: GrammarRuleV2,
        text: str,
        context: GrammarContext
    ) -> bool:
        """检查规则条件"""
        # 检查前置规则
        for prereq in rule.prerequisites:
            if prereq not in context.history:
                return False
                
        # 检查特征条件
        if not rule.features.issubset(context.features):
            return False
            
        # 检查模式匹配
        for pattern in rule.patterns:
            if not self._match_pattern(pattern, text, context):
                return False
                
        return True
        
    def _match_pattern(
        self,
        pattern: GrammarPattern,
        text: str,
        context: GrammarContext
    ) -> bool:
        """匹配语法模式"""
        # TODO: 实现更复杂的模式匹配逻辑
        return True
        
    def _calculate_relevance(
        self,
        rule: GrammarRuleV2,
        text: str,
        features: Set[str]
    ) -> float:
        """计算规则相关度"""
        # 特征匹配度
        feature_score = len(rule.features.intersection(features)) / len(rule.features)
        
        # 优先级分数
        priority_score = rule.priority / 10.0
        
        # 组合分数
        return 0.7 * feature_score + 0.3 * priority_score
        
    def apply_rule(
        self,
        rule: GrammarRuleV2,
        text: str,
        context: GrammarContext
    ) -> str:
        """应用语法规则"""
        try:
            # 记录规则应用历史
            context.history.append(rule.rule_id)
            
            # 应用转换
            for transform in rule.transformations:
                text = self._apply_transformation(transform, text, context)
                
            return text
            
        except Exception as e:
            raise GrammarError(
                f"应用规则 {rule.rule_id} 时出错: {str(e)}",
                error_code="RULE_APPLICATION_ERROR"
            )
            
    def _apply_transformation(
        self,
        transform: str,
        text: str,
        context: GrammarContext
    ) -> str:
        """应用转换规则"""
        # TODO: 实现具体的转换逻辑
        return text
