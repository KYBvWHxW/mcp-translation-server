from typing import List, Dict, Set
import json
import os
from dataclasses import dataclass
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

@dataclass
class GrammarRule:
    """语法规则数据类"""
    rule_id: str
    category: str  # 规则类别：词序、形态、句法等
    features: Set[str]  # 相关的形态特征
    patterns: List[str]  # 语法模式
    short: str  # 简短说明
    long: str  # 详细说明
    examples: List[Dict[str, str]]  # 示例
    importance: float  # 规则重要性权重
    prerequisites: Set[str] = None  # 前置规则
    conflicts: Set[str] = None  # 冲突规则
    overrides: Set[str] = None  # 覆盖规则

class GrammarRuleEngine:
    """语法规则引擎，支持基于形态特征的规则匹配和相关度排序"""
    
    def __init__(self, rules_path: str = "resources/grammar.json"):
        self.rules: Dict[str, GrammarRule] = {}
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 4),
            max_features=5000
        )
        self.feature_index = defaultdict(set)  # 形态特征索引
        self.pattern_vectors = None
        self.rule_graph = defaultdict(dict)  # 规则依赖图
        
        # 加载规则
        if os.path.exists(rules_path):
            self._load_rules(rules_path)
            self._build_indices()
            self._build_rule_graph()
    
    def _load_rules(self, path: str):
        """加载语法规则"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for rule in data.get('rules', []):
            rule_id = rule.get('id', str(len(self.rules)))
            self.rules[rule_id] = GrammarRule(
                rule_id=rule_id,
                category=rule.get('category', ''),
                features=set(rule.get('features', [])),
                patterns=rule.get('patterns', []),
                short=rule.get('short', ''),
                long=rule.get('long', ''),
                examples=rule.get('examples', []),
                importance=float(rule.get('importance', 1.0)),
                prerequisites=set(rule.get('prerequisites', [])),
                conflicts=set(rule.get('conflicts', [])),
                overrides=set(rule.get('overrides', []))
            )
    
    def _build_indices(self):
        """构建规则索引"""
        # 构建形态特征索引
        for rule_id, rule in self.rules.items():
            if rule.features:  # 确保特征列表非空
                for feature in rule.features:
                    self.feature_index[feature].add(rule_id)
        
        # 构建模式向量
        if not self.rules:
            return
            
        # 为每个规则的模式和说明创建TF-IDF向量
        pattern_texts = []
        for rule in self.rules.values():
            text_parts = []
            if rule.short:
                text_parts.append(rule.short)
            if rule.long:
                text_parts.append(rule.long)
            if rule.patterns:
                text_parts.extend(rule.patterns)
            if text_parts:  # 确保有文本内容
                pattern_texts.append(' '.join(text_parts))
                
        if pattern_texts:  # 只在有文本时才建立向量
            self.pattern_vectors = self.vectorizer.fit_transform(pattern_texts)
    
    def _calculate_context_similarity(self, context: str, rule: GrammarRule) -> float:
        """计算上下文与规则的相似度"""
        # 将上下文转换为向量
        context_vector = self.vectorizer.transform([context])
        
        # 计算与规则文本的相似度
        rule_text = f"{rule.short} {rule.long} {' '.join(rule.patterns)}"
        rule_vector = self.vectorizer.transform([rule_text])
        
        similarity = cosine_similarity(context_vector, rule_vector)[0][0]
        return float(similarity)
    
    def _calculate_feature_match_score(self, features: Set[str], rule: GrammarRule) -> float:
        """计算形态特征匹配分数"""
        if not rule.features:
            return 0.0
            
        matching_features = features.intersection(rule.features)
        return len(matching_features) / len(rule.features)
    
    def _analyze_context(self, sentence: str, morphology_analysis: List[Dict]) -> Dict:
        """分析句子上下文
        
        Args:
            sentence: 原始句子
            morphology_analysis: 形态分析结果
            
        Returns:
            上下文特征字典
        """
        context = {
            'features': set(),  # 形态特征集合
            'patterns': [],     # 句法模式
            'word_order': []    # 词序信息
        }
        
        # 提取形态特征
        for word_analysis in morphology_analysis:
            # 添加词根类型
            if 'root' in word_analysis:
                context['features'].add(f"root_{word_analysis['root']}")
            
            # 添加后缀特征
            for suffix in word_analysis.get('suffixes', []):
                if 'function' in suffix:
                    context['features'].add(f"suffix_{suffix['function']}")
                if 'type' in suffix:
                    context['features'].add(f"suffix_type_{suffix['type']}")
            
            # 记录词序
            context['word_order'].append(word_analysis.get('root', ''))
        
        # 生成基本句法模式
        context['patterns'].append(" ".join(context['word_order']))
        
        return context
    
    def find_matching_rules(self, context: str, features: Set[str]) -> List[GrammarRule]:
        """查找匹配的语法规则

        Args:
            context: 上下文文本
            features: 形态特征集合

        Returns:
            匹配的规则列表
        """
        # 候选规则集合
        candidate_rules = set()

        # 基于形态特征查找规则
        for feature in features:
            candidate_rules.update(self.feature_index.get(feature, set()))

        # 如果没有找到规则，返回空列表
        if not candidate_rules:
            return []

        # 计算每个规则的匹配分数
        rule_scores = []
        for rule_id in candidate_rules:
            rule = self.rules[rule_id]

            # 计算各个组件的分数
            feature_score = self._calculate_feature_match_score(features, rule)
            context_score = self._calculate_context_similarity(context, rule)

            # 综合分数（考虑规则重要性）
            final_score = (
                0.4 * feature_score +
                0.4 * context_score
            ) * rule.importance

            rule_scores.append((rule, final_score))

        # 按分数降序排序
        rule_scores.sort(key=lambda x: x[1], reverse=True)

        # 返回规则列表
        return [rule for rule, _ in rule_scores]

    def find_relevant_rules(
        self,
        sentence: str,
        morphology_analysis: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """查找相关的语法规则
        
        Args:
            sentence: 待分析的句子
            morphology_analysis: 形态分析结果
            top_k: 返回的规则数量
            
        Returns:
            相关规则列表，按相关度排序
        """
        # 分析上下文
        context = self._analyze_context(sentence, morphology_analysis)
        
        # 候选规则集合
        candidate_rules = set()
        
        # 基于形态特征查找规则
        for feature in context['features']:
            candidate_rules.update(self.feature_index.get(feature, set()))
        
        # 如果没有找到规则，返回空列表
        if not candidate_rules:
            return []
        
        # 计算每个规则的相关度分数
        rule_scores = []
        for rule_id in candidate_rules:
            rule = self.rules[rule_id]
            
            # 计算各个组件的分数
            feature_score = self._calculate_feature_match_score(
                context['features'], rule
            )
            context_score = self._calculate_context_similarity(
                sentence, rule
            )
            
            # 综合分数（考虑规则重要性）
            final_score = (
                0.4 * feature_score +
                0.4 * context_score
            ) * rule.importance
            
            rule_scores.append({
                'rule': rule,
                'score': final_score,
                'feature_score': feature_score,
                'context_score': context_score
            })
        
        # 按分数排序
        rule_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # 检查规则冲突
        selected_rules = {r['rule'].rule_id for r in rule_scores[:top_k]}
        conflict_resolution = self.resolve_conflicts(selected_rules)
        
        # 过滤掉被移除的规则，添加必要的规则
        final_rules = []
        seen_rules = set()
        
        # 首先添加所有需要添加的规则
        for rule_id in conflict_resolution['added_rules']:
            if rule_id not in seen_rules and rule_id in self.rules:
                rule = self.rules[rule_id]
                final_rules.append({
                    'rule': rule,
                    'score': 1.0,  # 必要的规则给予最高分
                    'feature_score': 1.0,
                    'context_score': 1.0,
                    'added_by': 'prerequisite'
                })
                seen_rules.add(rule_id)
        
        # 然后添加原始规则（如果没有被移除）
        for rule_score in rule_scores[:top_k]:
            rule_id = rule_score['rule'].rule_id
            if rule_id not in seen_rules and rule_id not in conflict_resolution['removed_rules']:
                final_rules.append(rule_score)
                seen_rules.add(rule_id)
        
        return final_rules[:top_k]
    
    def _build_rule_graph(self):
        """构建规则依赖图"""
        for rule_id, rule in self.rules.items():
            # 添加前置规则依赖
            if rule.prerequisites:
                for prereq_id in rule.prerequisites:
                    if prereq_id in self.rules:
                        self.rule_graph[rule_id]['prerequisites'] = \
                            self.rule_graph[rule_id].get('prerequisites', set()) | {prereq_id}
            
            # 添加冲突规则
            if rule.conflicts:
                for conflict_id in rule.conflicts:
                    if conflict_id in self.rules:
                        self.rule_graph[rule_id]['conflicts'] = \
                            self.rule_graph[rule_id].get('conflicts', set()) | {conflict_id}
            
            # 添加覆盖规则
            if rule.overrides:
                for override_id in rule.overrides:
                    if override_id in self.rules:
                        self.rule_graph[rule_id]['overrides'] = \
                            self.rule_graph[rule_id].get('overrides', set()) | {override_id}
    
    def _check_rule_conflicts(self, rule_ids: Set[str]) -> List[Dict]:
        """检查规则冲突
        
        Args:
            rule_ids: 要检查的规则ID集合
            
        Returns:
            冲突信息列表，每个冲突包含：
            - rule_id: 规则ID
            - conflict_type: 冲突类型 ('prerequisite_missing', 'conflict', 'override')
            - related_rule_id: 相关规则ID
            - resolution: 建议的解决方案
        """
        conflicts = []
        
        for rule_id in rule_ids:
            if rule_id not in self.rules:
                continue
                
            rule = self.rules[rule_id]
            graph_info = self.rule_graph[rule_id]
            
            # 检查前置规则
            if 'prerequisites' in graph_info:
                missing_prereqs = graph_info['prerequisites'] - rule_ids
                if missing_prereqs:
                    for prereq_id in missing_prereqs:
                        conflicts.append({
                            'rule_id': rule_id,
                            'conflict_type': 'prerequisite_missing',
                            'related_rule_id': prereq_id,
                            'resolution': f'需要先应用规则 {prereq_id}'
                        })
            
            # 检查冲突规则
            if 'conflicts' in graph_info:
                active_conflicts = graph_info['conflicts'] & rule_ids
                if active_conflicts:
                    for conflict_id in active_conflicts:
                        conflicts.append({
                            'rule_id': rule_id,
                            'conflict_type': 'conflict',
                            'related_rule_id': conflict_id,
                            'resolution': f'不能同时应用规则 {rule_id} 和 {conflict_id}'
                        })
            
            # 检查覆盖规则
            if 'overrides' in graph_info:
                overridden = graph_info['overrides'] & rule_ids
                if overridden:
                    for override_id in overridden:
                        conflicts.append({
                            'rule_id': rule_id,
                            'conflict_type': 'override',
                            'related_rule_id': override_id,
                            'resolution': f'规则 {rule_id} 将覆盖规则 {override_id}'
                        })
        
        return conflicts
    
    def resolve_conflicts(self, rule_ids: Set[str]) -> Dict:
        """解决规则冲突
        
        Args:
            rule_ids: 要应用的规则ID集合
            
        Returns:
            包含以下信息的字典：
            - resolved_rules: 解决冲突后的规则ID集合
            - removed_rules: 被移除的规则ID集合
            - added_rules: 被添加的规则ID集合
            - conflicts: 冲突信息列表
        """
        conflicts = self._check_rule_conflicts(rule_ids)
        resolved_rules = set(rule_ids)
        removed_rules = set()
        added_rules = set()
        
        # 处理前置规则
        prereq_conflicts = [c for c in conflicts if c['conflict_type'] == 'prerequisite_missing']
        for conflict in prereq_conflicts:
            added_rules.add(conflict['related_rule_id'])
        
        # 处理冲突规则
        rule_conflicts = [c for c in conflicts if c['conflict_type'] == 'conflict']
        for conflict in rule_conflicts:
            # 保留重要性较高的规则
            rule1 = self.rules[conflict['rule_id']]
            rule2 = self.rules[conflict['related_rule_id']]
            if rule1.importance >= rule2.importance:
                removed_rules.add(conflict['related_rule_id'])
            else:
                removed_rules.add(conflict['rule_id'])
        
        # 处理覆盖规则
        override_conflicts = [c for c in conflicts if c['conflict_type'] == 'override']
        for conflict in override_conflicts:
            removed_rules.add(conflict['related_rule_id'])
        
        # 更新规则集合
        resolved_rules = (resolved_rules | added_rules) - removed_rules
        
        return {
            'resolved_rules': resolved_rules,
            'removed_rules': removed_rules,
            'added_rules': added_rules,
            'conflicts': conflicts
        }
        rule_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回top_k个规则
        return rule_scores[:top_k]
