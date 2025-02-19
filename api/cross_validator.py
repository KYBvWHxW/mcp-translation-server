from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import json
import os
from collections import defaultdict

@dataclass
class CrossValidationResult:
    """跨资源验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    resource_stats: Dict[str, Any]

class CrossValidator:
    """跨资源验证器"""
    
    def __init__(self, resource_dir: str = "resources"):
        self.resource_dir = resource_dir
        self.word_classes = {
            'noun', 'verb', 'adjective', 'adverb', 'pronoun',
            'particle', 'conjunction', 'interjection'
        }
        
    def validate_all(self) -> CrossValidationResult:
        """验证所有资源的一致性"""
        errors = []
        warnings = []
        stats = {}
        
        # 加载所有资源
        resources = self._load_resources()
        if not resources:
            return CrossValidationResult(
                False,
                ["无法加载资源文件"],
                [],
                {}
            )
            
        # 验证词典和语法规则的一致性
        if 'lexicon' in resources and 'grammar' in resources:
            self._validate_lexicon_grammar(
                resources['lexicon'],
                resources['grammar'],
                errors,
                warnings
            )
            
        # 验证词典和形态规则的一致性
        if 'lexicon' in resources and 'morphology' in resources:
            self._validate_lexicon_morphology(
                resources['lexicon'],
                resources['morphology'],
                errors,
                warnings
            )
            
        # 验证术语库和词典的一致性
        if 'terminology' in resources and 'lexicon' in resources:
            self._validate_terminology_lexicon(
                resources['terminology'],
                resources['lexicon'],
                errors,
                warnings
            )
            
        # 验证语法规则和形态规则的一致性
        if 'grammar' in resources and 'morphology' in resources:
            self._validate_grammar_morphology(
                resources['grammar'],
                resources['morphology'],
                errors,
                warnings
            )
            
        # 收集资源统计信息
        stats = self._collect_resource_stats(resources)
        
        return CrossValidationResult(
            len(errors) == 0,
            errors,
            warnings,
            stats
        )
        
    def _load_resources(self) -> Dict[str, Any]:
        """加载所有资源"""
        resources = {}
        resource_types = ['grammar', 'morphology', 'lexicon', 'terminology']
        
        for resource_type in resource_types:
            file_path = os.path.join(self.resource_dir, f"{resource_type}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        resources[resource_type] = json.load(f)
                except Exception as e:
                    print(f"加载资源 {resource_type} 失败: {e}")
                    
        return resources
        
    def _validate_lexicon_grammar(
        self,
        lexicon: Dict[str, Any],
        grammar: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ):
        """验证词典和语法规则的一致性"""
        # 收集语法规则中引用的词类
        grammar_word_classes = set()
        for rule in grammar.get('rules', []):
            if 'word_class' in rule:
                grammar_word_classes.add(rule['word_class'])
                
        # 验证词典中的词类是否被语法规则支持
        lexicon_word_classes = set(
            info['word_class']
            for info in lexicon.values()
            if 'word_class' in info
        )
        
        unsupported_classes = lexicon_word_classes - grammar_word_classes
        if unsupported_classes:
            warnings.append(
                f"词典中的词类 {unsupported_classes} 在语法规则中未定义"
            )
            
        # 验证语法规则中的模式是否包含词典中不存在的词类
        invalid_classes = grammar_word_classes - self.word_classes
        if invalid_classes:
            errors.append(f"语法规则中包含无效的词类: {invalid_classes}")
            
    def _validate_lexicon_morphology(
        self,
        lexicon: Dict[str, Any],
        morphology: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ):
        """验证词典和形态规则的一致性"""
        # 收集形态规则中的词类和特征
        morphology_features = defaultdict(set)
        for rule in morphology.get('rules', []):
            if 'word_class' in rule and 'features' in rule:
                word_class = rule['word_class']
                features = set(rule['features'].keys())
                morphology_features[word_class].update(features)
                
        # 验证词典中的特征是否被形态规则支持
        for word, info in lexicon.items():
            if 'word_class' not in info or 'features' not in info:
                continue
                
            word_class = info['word_class']
            features = set(info['features'].keys())
            
            if word_class in morphology_features:
                unsupported_features = features - morphology_features[word_class]
                if unsupported_features:
                    warnings.append(
                        f"词条 '{word}' 的特征 {unsupported_features} "
                        f"在形态规则中未定义"
                    )
            else:
                warnings.append(
                    f"词条 '{word}' 的词类 '{word_class}' "
                    f"没有对应的形态规则"
                )
                
    def _validate_terminology_lexicon(
        self,
        terminology: Dict[str, Any],
        lexicon: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ):
        """验证术语库和词典的一致性"""
        # 收集词典中的所有词条
        lexicon_terms = set(lexicon.keys())
        
        # 验证术语是否在词典中存在
        for term in terminology.keys():
            if term not in lexicon_terms:
                warnings.append(f"术语 '{term}' 在词典中不存在")
                
        # 验证术语的翻译是否与词典一致
        for term, term_info in terminology.items():
            if term not in lexicon:
                continue
                
            lex_info = lexicon[term]
            if 'translations' in term_info and 'translations' in lex_info:
                term_trans = set(term_info['translations'].values())
                lex_trans = set(
                    t['text'] for t in lex_info['translations']
                    if 'text' in t
                )
                
                inconsistent_trans = term_trans - lex_trans
                if inconsistent_trans:
                    warnings.append(
                        f"术语 '{term}' 的翻译 {inconsistent_trans} "
                        f"与词典不一致"
                    )
                    
    def _validate_grammar_morphology(
        self,
        grammar: Dict[str, Any],
        morphology: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ):
        """验证语法规则和形态规则的一致性"""
        # 收集形态规则中的变换模式
        morphology_patterns = set()
        for rule in morphology.get('rules', []):
            if 'pattern' in rule:
                morphology_patterns.add(rule['pattern'])
                
        # 验证语法规则是否使用了未定义的形态模式
        for rule in grammar.get('rules', []):
            if 'morphology_pattern' in rule:
                pattern = rule['morphology_pattern']
                if pattern not in morphology_patterns:
                    errors.append(
                        f"语法规则使用了未定义的形态模式: {pattern}"
                    )
                    
    def _collect_resource_stats(
        self,
        resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """收集资源统计信息"""
        stats = {}
        
        # 词典统计
        if 'lexicon' in resources:
            lexicon = resources['lexicon']
            word_class_dist = defaultdict(int)
            feature_dist = defaultdict(int)
            translation_count = 0
            
            for info in lexicon.values():
                if 'word_class' in info:
                    word_class_dist[info['word_class']] += 1
                if 'features' in info:
                    for feature in info['features']:
                        feature_dist[feature] += 1
                if 'translations' in info:
                    translation_count += len(info['translations'])
                    
            stats['lexicon'] = {
                'total_entries': len(lexicon),
                'word_class_distribution': dict(word_class_dist),
                'feature_distribution': dict(feature_dist),
                'total_translations': translation_count
            }
            
        # 语法规则统计
        if 'grammar' in resources:
            grammar = resources['grammar']
            rule_type_dist = defaultdict(int)
            
            for rule in grammar.get('rules', []):
                if 'type' in rule:
                    rule_type_dist[rule['type']] += 1
                    
            stats['grammar'] = {
                'total_rules': len(grammar.get('rules', [])),
                'rule_type_distribution': dict(rule_type_dist)
            }
            
        # 形态规则统计
        if 'morphology' in resources:
            morphology = resources['morphology']
            word_class_dist = defaultdict(int)
            
            for rule in morphology.get('rules', []):
                if 'word_class' in rule:
                    word_class_dist[rule['word_class']] += 1
                    
            stats['morphology'] = {
                'total_rules': len(morphology.get('rules', [])),
                'word_class_distribution': dict(word_class_dist)
            }
            
        # 术语库统计
        if 'terminology' in resources:
            terminology = resources['terminology']
            domain_dist = defaultdict(int)
            
            for info in terminology.values():
                if 'domain' in info:
                    domain_dist[info['domain']] += 1
                    
            stats['terminology'] = {
                'total_terms': len(terminology),
                'domain_distribution': dict(domain_dist)
            }
            
        return stats
