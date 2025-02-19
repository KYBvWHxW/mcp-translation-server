#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from api.enhanced_morphology import EnhancedMorphologyAnalyzer
from api.enhanced_translation import EnhancedTranslationEngine

def test_morphology_analysis():
    """测试形态分析器的各项功能"""
    print("\n=== 形态分析器测试 ===")
    
    rules_path = str(Path(__file__).parent.parent / "resources" / "manchu_rules.json")
    analyzer = EnhancedMorphologyAnalyzer(rules_path)
    
    # 测试复杂词形分析
    test_words = [
        "arambi",      # 写 (动词现在时)
        "araha",       # 写 (动词过去时)
        "araki",       # 写 (动词期望语气)
        "bithede",     # 书上 (名词与格)
        "moringga",    # 骑马的 (名词+形容词后缀)
        "ambasai",     # 大臣们的 (名词复数属格)
    ]
    
    for word in test_words:
        print(f"\n分析词形: {word}")
        analysis = analyzer.analyze(word)
        print(f"词干: {analysis.stem}")
        print(f"后缀: {', '.join(analysis.suffixes)}")
        print(f"词类: {analysis.word_class}")
        print(f"和谐类型: {analysis.harmony_type}")
        print(f"特征: {analysis.features}")
        
        # 测试词形生成
        if analysis.word_class == "verb":
            generated = analyzer.generate_form(
                analysis.stem,
                "verb",
                {"tense": "present"}
            )
            print(f"生成现在时形式: {generated}")
            
    # 测试元音和谐
    print("\n=== 元音和谐测试 ===")
    test_harmonies = [
        "amban",    # a-和谐
        "edun",     # e-和谐
        "ilha",     # 中性
    ]
    for word in test_harmonies:
        harmony = analyzer.get_harmony_type(word)
        print(f"词: {word}, 和谐类型: {harmony}")
        
    # 测试纠错建议
    print("\n=== 纠错建议测试 ===")
    invalid_words = [
        "aramba",    # 应为 arambi
        "bithde",    # 应为 bithede
        "morn",      # 应为 morin
    ]
    for word in invalid_words:
        suggestions = analyzer.suggest_corrections(word)
        print(f"错误词: {word}")
        print(f"建议修正: {suggestions}")

def test_enhanced_translation():
    """测试增强型翻译引擎"""
    print("\n=== 翻译引擎测试 ===")
    
    engine = EnhancedTranslationEngine(
        rules_path=str(Path(__file__).parent.parent / "resources" / "manchu_rules.json"),
        corpus_path=str(Path(__file__).parent.parent / "resources" / "parallel_corpus.json"),
        dictionary_path=str(Path(__file__).parent.parent / "resources" / "dictionary.json")
    )
    
    # 测试单句翻译
    test_sentences = [
        "bi bithe arambi",           # 语料库匹配
        "morin feksin",              # 词典查找
        "ere bithe sain",           # 形态分析
        "mini boode jimbi",         # 复杂语法
    ]
    
    for sentence in test_sentences:
        print(f"\n原文: {sentence}")
        result = engine.translate(sentence)
        print(f"译文: {result.target_text}")
        print(f"置信度: {result.confidence}")
        if result.morpheme_analysis:
            print("形态分析:")
            for word, analysis in result.morpheme_analysis.items():
                print(f"  {word}: {analysis}")
                
    # 测试批量翻译
    print("\n=== 批量翻译测试 ===")
    results = engine.batch_translate(test_sentences)
    for i, result in enumerate(results):
        print(f"\n句子 {i+1}:")
        print(f"原文: {result.source_text}")
        print(f"译文: {result.target_text}")
        
    # 测试翻译元数据
    print("\n=== 翻译元数据测试 ===")
    metadata = engine.get_translation_metadata("bi manju gisun tacimbi")
    print("元数据:")
    print(f"词数: {metadata['word_count']}")
    print(f"词典命中: {metadata['dictionary_hits']}")
    print("形态分析:")
    for word, analysis in metadata['morpheme_analyses'].items():
        print(f"  {word}: {analysis}")

if __name__ == "__main__":
    print("开始测试增强型功能...")
    test_morphology_analysis()
    test_enhanced_translation()
    print("\n测试完成!")
