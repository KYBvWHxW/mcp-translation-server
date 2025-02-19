from typing import Dict, List, Any, Optional
import re
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class ResourceValidator:
    """资源验证器"""
    
    def __init__(self):
        self.word_classes = {
            'noun', 'verb', 'adjective', 'adverb', 'pronoun',
            'particle', 'conjunction', 'interjection'
        }
        
    def validate_grammar(self, content: Dict[str, Any]) -> ValidationResult:
        """验证语法规则"""
        errors = []
        warnings = []
        
        if not isinstance(content, dict):
            errors.append("语法规则必须是字典格式")
            return ValidationResult(False, errors, warnings)
            
        if 'rules' not in content:
            errors.append("缺少 'rules' 字段")
            return ValidationResult(False, errors, warnings)
            
        rules = content['rules']
        if not isinstance(rules, list):
            errors.append("'rules' 必须是列表格式")
            return ValidationResult(False, errors, warnings)
            
        for i, rule in enumerate(rules):
            # 必需字段验证
            required_fields = ['rule_id', 'type', 'pattern', 'description']
            for field in required_fields:
                if field not in rule:
                    errors.append(f"规则 {i} 缺少必需字段 '{field}'")
                    
            # 规则ID格式验证
            if 'rule_id' in rule and not re.match(r'^[A-Z][A-Z0-9_]*$', rule['rule_id']):
                errors.append(f"规则ID '{rule['rule_id']}' 格式无效")
                
            # 规则类型验证
            valid_types = {'word_order', 'agreement', 'transformation'}
            if 'type' in rule and rule['type'] not in valid_types:
                errors.append(f"规则类型 '{rule['type']}' 无效")
                
            # 模式语法验证
            if 'pattern' in rule:
                try:
                    re.compile(rule['pattern'])
                except re.error:
                    errors.append(f"规则 {i} 的模式表达式无效")
                    
            # 优先级验证
            if 'priority' in rule:
                if not isinstance(rule['priority'], int) or rule['priority'] < 0:
                    errors.append(f"规则 {i} 的优先级必须是非负整数")
                    
            # 示例验证
            if 'examples' in rule:
                if not isinstance(rule['examples'], list):
                    errors.append(f"规则 {i} 的示例必须是列表格式")
                else:
                    for j, example in enumerate(rule['examples']):
                        if 'input' not in example or 'output' not in example:
                            errors.append(f"规则 {i} 的示例 {j} 缺少输入或输出")
                            
        return ValidationResult(len(errors) == 0, errors, warnings)
        
    def validate_morphology(self, content: Dict[str, Any]) -> ValidationResult:
        """验证形态规则"""
        errors = []
        warnings = []
        
        if not isinstance(content, dict):
            errors.append("形态规则必须是字典格式")
            return ValidationResult(False, errors, warnings)
            
        if 'rules' not in content:
            errors.append("缺少 'rules' 字段")
            return ValidationResult(False, errors, warnings)
            
        rules = content['rules']
        if not isinstance(rules, list):
            errors.append("'rules' 必须是列表格式")
            return ValidationResult(False, errors, warnings)
            
        for i, rule in enumerate(rules):
            # 必需字段验证
            required_fields = ['rule_id', 'word_class', 'pattern', 'replacement']
            for field in required_fields:
                if field not in rule:
                    errors.append(f"规则 {i} 缺少必需字段 '{field}'")
                    
            # 词类验证
            if 'word_class' in rule and rule['word_class'] not in self.word_classes:
                errors.append(f"词类 '{rule['word_class']}' 无效")
                
            # 模式和替换验证
            if 'pattern' in rule and 'replacement' in rule:
                try:
                    re.compile(rule['pattern'])
                except re.error:
                    errors.append(f"规则 {i} 的模式表达式无效")
                    
                if not isinstance(rule['replacement'], str):
                    errors.append(f"规则 {i} 的替换内容必须是字符串")
                    
            # 条件验证
            if 'conditions' in rule:
                if not isinstance(rule['conditions'], list):
                    errors.append(f"规则 {i} 的条件必须是列表格式")
                else:
                    for j, condition in enumerate(rule['conditions']):
                        if 'feature' not in condition or 'value' not in condition:
                            errors.append(f"规则 {i} 的条件 {j} 缺少特征或值")
                            
        return ValidationResult(len(errors) == 0, errors, warnings)
        
    def validate_lexicon(self, content: Dict[str, Any]) -> ValidationResult:
        """验证词典"""
        errors = []
        warnings = []
        
        if not isinstance(content, dict):
            errors.append("词典必须是字典格式")
            return ValidationResult(False, errors, warnings)
            
        for word, info in content.items():
            if not isinstance(info, dict):
                errors.append(f"词条 '{word}' 的信息必须是字典格式")
                continue
                
            # 必需字段验证
            required_fields = ['word_class', 'features', 'translations']
            for field in required_fields:
                if field not in info:
                    errors.append(f"词条 '{word}' 缺少必需字段 '{field}'")
                    
            # 词类验证
            if 'word_class' in info and info['word_class'] not in self.word_classes:
                errors.append(f"词条 '{word}' 的词类 '{info['word_class']}' 无效")
                
            # 特征验证
            if 'features' in info:
                features = info['features']
                if not isinstance(features, dict):
                    errors.append(f"词条 '{word}' 的特征必须是字典格式")
                else:
                    for feature, value in features.items():
                        if not isinstance(value, (str, int, bool)):
                            errors.append(f"词条 '{word}' 的特征 '{feature}' 值类型无效")
                            
            # 翻译验证
            if 'translations' in info:
                translations = info['translations']
                if not isinstance(translations, list):
                    errors.append(f"词条 '{word}' 的翻译必须是列表格式")
                else:
                    for i, trans in enumerate(translations):
                        if not isinstance(trans, dict):
                            errors.append(f"词条 '{word}' 的翻译 {i} 必须是字典格式")
                        elif 'text' not in trans:
                            errors.append(f"词条 '{word}' 的翻译 {i} 缺少文本")
                            
            # 示例验证
            if 'examples' in info:
                if not isinstance(info['examples'], list):
                    errors.append(f"词条 '{word}' 的示例必须是列表格式")
                else:
                    for i, example in enumerate(info['examples']):
                        if not isinstance(example, dict):
                            errors.append(f"词条 '{word}' 的示例 {i} 必须是字典格式")
                        elif 'sentence' not in example or 'translation' not in example:
                            errors.append(f"词条 '{word}' 的示例 {i} 缺少句子或翻译")
                            
        return ValidationResult(len(errors) == 0, errors, warnings)
        
    def validate_terminology(self, content: Dict[str, Any]) -> ValidationResult:
        """验证术语库"""
        errors = []
        warnings = []
        
        if not isinstance(content, dict):
            errors.append("术语库必须是字典格式")
            return ValidationResult(False, errors, warnings)
            
        for term, info in content.items():
            if not isinstance(info, dict):
                errors.append(f"术语 '{term}' 的信息必须是字典格式")
                continue
                
            # 必需字段验证
            required_fields = ['definition', 'domain', 'translations']
            for field in required_fields:
                if field not in info:
                    errors.append(f"术语 '{term}' 缺少必需字段 '{field}'")
                    
            # 领域验证
            valid_domains = {'general', 'technical', 'literary', 'historical'}
            if 'domain' in info and info['domain'] not in valid_domains:
                errors.append(f"术语 '{term}' 的领域 '{info['domain']}' 无效")
                
            # 翻译验证
            if 'translations' in info:
                translations = info['translations']
                if not isinstance(translations, dict):
                    errors.append(f"术语 '{term}' 的翻译必须是字典格式")
                else:
                    for lang, trans in translations.items():
                        if not isinstance(trans, str):
                            errors.append(f"术语 '{term}' 的 {lang} 翻译必须是字符串")
                            
            # 用法示例验证
            if 'usage' in info:
                if not isinstance(info['usage'], list):
                    errors.append(f"术语 '{term}' 的用法示例必须是列表格式")
                else:
                    for i, usage in enumerate(info['usage']):
                        if not isinstance(usage, dict):
                            errors.append(f"术语 '{term}' 的用法示例 {i} 必须是字典格式")
                        elif 'context' not in usage or 'translation' not in usage:
                            errors.append(f"术语 '{term}' 的用法示例 {i} 缺少上下文或翻译")
                            
        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_resource_consistency(self, resources: Dict[str, Dict[str, Any]]) -> ValidationResult:
        """验证资源一致性"""
        errors = []
        warnings = []

        # 检查词典中的词类是否在语法规则中使用
        if 'lexicon' in resources and 'grammar' in resources:
            lexicon = resources['lexicon']
            grammar = resources['grammar']
            word_classes_in_lexicon = {info.get('word_class') for info in lexicon.values()}
            word_classes_in_grammar = set()
            for rule in grammar.get('rules', []):
                if 'word_class' in rule:
                    word_classes_in_grammar.add(rule['word_class'])

            unused_word_classes = word_classes_in_lexicon - word_classes_in_grammar
            if unused_word_classes:
                warnings.append(f"词典中的词类 {unused_word_classes} 在语法规则中未使用")

        # 检查形态规则中的特征是否在词典中定义
        if 'lexicon' in resources and 'morphology' in resources:
            lexicon = resources['lexicon']
            morphology = resources['morphology']
            features_in_lexicon = set()
            for info in lexicon.values():
                if 'features' in info:
                    features_in_lexicon.update(info['features'].keys())

            features_in_morphology = set()
            for rule in morphology.get('rules', []):
                if 'conditions' in rule:
                    for condition in rule['conditions']:
                        if 'feature' in condition:
                            features_in_morphology.add(condition['feature'])

            undefined_features = features_in_morphology - features_in_lexicon
            if undefined_features:
                errors.append(f"形态规则中使用了未定义的特征: {undefined_features}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_resource_dependencies(self, resources: Dict[str, Dict[str, Any]]) -> ValidationResult:
        """验证资源依赖关系"""
        errors = []
        warnings = []

        # 检查必需的资源文件
        required_resources = {'grammar', 'morphology', 'lexicon'}
        missing_resources = required_resources - set(resources.keys())
        if missing_resources:
            errors.append(f"缺少必需的资源文件: {missing_resources}")

        # 检查语法规则引用的词典项
        if 'grammar' in resources and 'lexicon' in resources:
            grammar = resources['grammar']
            lexicon = resources['lexicon']
            for rule in grammar.get('rules', []):
                if 'references' in rule:
                    for ref in rule['references']:
                        if ref not in lexicon:
                            errors.append(f"语法规则引用了不存在的词典项: {ref}")

        # 检查形态规则引用的词典项
        if 'morphology' in resources and 'lexicon' in resources:
            morphology = resources['morphology']
            lexicon = resources['lexicon']
            for rule in morphology.get('rules', []):
                if 'examples' in rule:
                    for example in rule['examples']:
                        if 'word' in example and example['word'] not in lexicon:
                            warnings.append(f"形态规则示例使用了不存在的词典项: {example['word']}")

        return ValidationResult(len(errors) == 0, errors, warnings)
