#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Dict, List
import json
from pprint import pprint
sys.path.append(str(Path(__file__).parent.parent))

from api.enhanced_morphology import EnhancedMorphologyAnalyzer, MorphemeAnalysis
from api.enhanced_translation import EnhancedTranslationEngine, TranslationResult

class ManchuDemo:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.morphology = EnhancedMorphologyAnalyzer(
            str(self.project_root / "resources" / "manchu_rules.json")
        )
        self.translation = EnhancedTranslationEngine(
            rules_path=str(self.project_root / "resources" / "manchu_rules.json"),
            corpus_path=str(self.project_root / "resources" / "parallel_corpus.json"),
            dictionary_path=str(self.project_root / "resources" / "dictionary.json")
        )

    def demo_morphological_analysis(self):
        """演示形态分析功能"""
        print("\n=== 1. 形态分析功能演示 ===")
        
        # 1.1 基本形态分析
        print("\n1.1 基本形态分析")
        test_words = {
            "arambi": "写（现在时）",
            "araha": "写（过去时）",
            "araki": "写（期望语气）",
            "bithede": "在书上（与格）",
            "moringga": "骑马的（形容词）",
            "ambasai": "大臣们的（复数属格）",
            "tacimbi": "学习（现在时）",
            "taciki": "想学（期望语气）",
        }
        
        for word, desc in test_words.items():
            print(f"\n分析词: {word} ({desc})")
            analysis = self.morphology.analyze(word)
            self._print_analysis(analysis)

        # 1.2 元音和谐分析
        print("\n1.2 元音和谐分析")
        harmony_words = {
            "amban": "大臣 (a-和谐)",
            "edun": "风 (e-和谐)",
            "ilha": "花 (中性)",
            "morin": "马 (i-中性)",
        }
        
        for word, desc in harmony_words.items():
            harmony = self.morphology.get_harmony_type(word)
            print(f"词: {word} ({desc})")
            print(f"和谐类型: {harmony}")

        # 1.3 词形生成
        print("\n1.3 词形生成")
        generation_tests = [
            ("ara", "verb", {"tense": "present"}),
            ("ara", "verb", {"tense": "past"}),
            ("taci", "verb", {"mood": "optative"}),
            ("morin", "noun", {"case": "dative"}),
            ("amban", "noun", {"number": "plural", "case": "genitive"}),
        ]
        
        for stem, word_class, features in generation_tests:
            generated = self.morphology.generate_form(stem, word_class, features)
            print(f"\n词干: {stem}")
            print(f"词类: {word_class}")
            print(f"特征: {features}")
            print(f"生成形式: {generated}")

    def demo_translation_features(self):
        """演示翻译功能"""
        print("\n=== 2. 翻译功能演示 ===")
        
        # 2.1 基本翻译
        print("\n2.1 基本翻译")
        basic_sentences = [
            "bi bithe arambi",
            "si aibe tacimbi",
            "tere niyalma we",
            "ere bithe sain",
            "mini boode jimbi",
        ]
        
        for sentence in basic_sentences:
            result = self.translation.translate(sentence)
            print(f"\n满文: {sentence}")
            print(f"汉译: {result.target_text}")
            print(f"置信度: {result.confidence}")

        # 2.2 详细翻译分析
        print("\n2.2 详细翻译分析")
        sentence = "bi manju gisun tacimbi"
        print(f"\n分析句子: {sentence}")
        result = self.translation.translate(sentence)
        print(f"翻译: {result.target_text}")
        
        metadata = self.translation.get_translation_metadata(sentence)
        print("\n元数据分析:")
        print(f"词数: {metadata['word_count']}")
        print(f"词典命中: {metadata['dictionary_hits']}")
        print("\n形态分析:")
        for word, analysis in metadata['morpheme_analyses'].items():
            print(f"\n词: {word}")
            pprint(analysis)

        # 2.3 批量翻译
        print("\n2.3 批量翻译演示")
        batch_sentences = [
            "ere gisun umesi sain",
            "bi sikse bithe arambi",
            "si aibe tacimbi",
        ]
        
        results = self.translation.batch_translate(batch_sentences)
        for i, result in enumerate(results, 1):
            print(f"\n句子 {i}:")
            print(f"满文: {result.source_text}")
            print(f"汉译: {result.target_text}")
            print(f"置信度: {result.confidence}")

    def demo_error_correction(self):
        """演示错误检测和纠正功能"""
        print("\n=== 3. 错误检测和纠正功能演示 ===")
        
        # 3.1 基本错误检测
        print("\n3.1 基本错误检测")
        test_words = [
            "aramba",  # 应为 arambi
            "bithde",  # 应为 bithede
            "morn",    # 应为 morin
            "tacmbi",  # 应为 tacimbi
        ]
        
        for word in test_words:
            print(f"\n检查词: {word}")
            is_valid = self.morphology.is_valid_word(word)
            print(f"是否有效: {is_valid}")
            if not is_valid:
                suggestions = self.morphology.suggest_corrections(word)
                print(f"纠正建议: {suggestions}")

        # 3.2 高级错误分析
        print("\n3.2 高级错误分析")
        error_cases = {
            "aramba": "动词后缀错误",
            "bithde": "元音缺失",
            "morn": "元音错误",
            "ambasa": "复数形式错误",
        }
        
        for word, error_type in error_cases.items():
            print(f"\n分析错误词: {word} ({error_type})")
            analysis = self.morphology.analyze(word)
            self._print_analysis(analysis)
            suggestions = self.morphology.suggest_corrections(word)
            print(f"纠正建议: {suggestions}")

    def _print_analysis(self, analysis: MorphemeAnalysis):
        """打印形态分析结果"""
        print(f"词干: {analysis.stem}")
        print(f"后缀: {', '.join(analysis.suffixes) if analysis.suffixes else '无'}")
        print(f"词类: {analysis.word_class}")
        print(f"和谐类型: {analysis.harmony_type}")
        print(f"语法特征: {analysis.features}")

def main():
    print("=== 满语分析与翻译系统综合演示 ===")
    demo = ManchuDemo()
    
    # 1. 形态分析演示
    demo.demo_morphological_analysis()
    
    # 2. 翻译功能演示
    demo.demo_translation_features()
    
    # 3. 错误检测和纠正演示
    demo.demo_error_correction()
    
    print("\n演示完成!")

if __name__ == "__main__":
    main()
