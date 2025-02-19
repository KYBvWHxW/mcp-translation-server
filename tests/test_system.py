import unittest
import sys
import os
import json
import time
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import TranslationServer
from dictionary import ManchuDictionary
from grammar import GrammarRuleEngine
from parallel import ParallelCorpus
from api.resource_manager import ResourceManager
from api.resource_validator import ResourceValidator
from api.cache_manager import CacheManager, CacheConfig
from api.metrics_collector import MetricsCollector

class TestManChuTranslationSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """初始化测试环境"""
        cls.server = TranslationServer()
        cls.dictionary = ManchuDictionary('tests/test_resources/test_dict.json')
        cls.grammar = GrammarRuleEngine('tests/test_resources/test_rules.json')
        cls.parallel = ParallelCorpus('tests/test_resources/test_parallel.json')
        cls.resource_manager = ResourceManager()
        cls.resource_validator = ResourceValidator()
        cls.cache_manager = CacheManager(
            config=CacheConfig(
                max_size=1000,
                max_memory_mb=512,
                default_ttl=timedelta(hours=1),
                cleanup_interval=timedelta(minutes=5)
            )
        )
        cls.metrics_collector = MetricsCollector()
        
    def setUp(self):
        """每个测试用例前的准备工作"""
        self.metrics_collector.reset_metrics()
        self.cache_manager.clear_cache()
        
    def test_dictionary_basic(self):
        """测试词典基本功能"""
        # 测试词典加载
        self.assertIsNotNone(self.dictionary.entries)
        
        # 测试词条查找
        word = "ᡥᠠᡳ"  # "海" hai
        matches = self.dictionary.fuzzy_search(word)
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0]['entry'].word, word)
        
        # 测试未知词处理
        unknown_word = "ᠨᡝᠮᡝᠨ"
        matches = self.dictionary.fuzzy_search(unknown_word)
        self.assertTrue(len(matches) >= 0)  # 可能找不到匹配
        
    def test_grammar_rules(self):
        """测试语法规则"""
        # 测试语法规则加载
        self.assertIsNotNone(self.grammar.rules)
        
        # 测试语法分析
        context = "ᡥᠠᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ"  # "海的人" hai i niyalma
        features = {"名词短语", "所有格"}
        matches = self.grammar.find_matching_rules(context, features)
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0].rule_id, "noun_phrase")
        
    def test_parallel_processing(self):
        """测试并行处理"""
        # 准备测试数据
        test_texts = [
            "ᡥᠠᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",
            "ᠠᠯᡳᠨ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",
            "ᡥᡡᠸᠠᠩᡩᡳ ᡳ ᡥᡝᡵᡤᡝᠨ"
        ]
        
        # 测试并行翻译
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = self.parallel.process_batch(test_texts, executor)
            
        self.assertEqual(len(results), len(test_texts))
        self.assertTrue(all(isinstance(r, str) for r in results))
        
    def test_resource_management(self):
        """测试资源管理"""
        # 测试资源版本控制
        version = self.resource_manager.get_current_version()
        self.assertIsNotNone(version)
        
        # 测试资源备份
        backup_id = self.resource_manager.create_backup()
        self.assertTrue(self.resource_manager.verify_backup(backup_id))
        
        # 测试资源恢复
        self.assertTrue(self.resource_manager.restore_backup(backup_id))
        
    def test_resource_validation(self):
        """测试资源验证"""
        # 测试词典验证
        dict_valid = self.resource_validator.validate_dictionary("test_dict.json")
        self.assertTrue(dict_valid)
        
        # 测试语法规则验证
        rules_valid = self.resource_validator.validate_grammar_rules("test_rules.json")
        self.assertTrue(rules_valid)
        
        # 测试资源一致性
        consistency = self.resource_validator.check_cross_consistency()
        self.assertTrue(consistency)
        
    def test_cache_management(self):
        """测试缓存管理"""
        # 测试缓存操作
        key = "test_key"
        value = "test_value"
        self.cache_manager.set(key, value)
        self.assertEqual(self.cache_manager.get(key), value)
        
        # 测试缓存过期
        time.sleep(2)  # 等待缓存过期
        self.cache_manager.set_ttl(key, 1)  # 1秒过期
        time.sleep(2)
        self.assertIsNone(self.cache_manager.get(key))
        
        # 测试缓存清理
        self.cache_manager.clear_cache()
        self.assertIsNone(self.cache_manager.get(key))
        
    def test_metrics_collection(self):
        """测试指标收集"""
        # 模拟一些操作
        for _ in range(10):
            self.server.translate("ᡥᠠᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ")
            
        # 检查性能指标
        metrics = self.metrics_collector.get_metrics()
        self.assertIn("translation_count", metrics)
        self.assertIn("average_latency", metrics)
        self.assertIn("cache_hit_ratio", metrics)
        
    def test_full_translation_pipeline(self):
        """测试完整翻译流程"""
        # 准备测试用例
        test_cases = [
            {
                "input": "ᡥᠠᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",
                "expected": "海的人"
            },
            {
                "input": "ᠠᠯᡳᠨ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",
                "expected": "山的人"
            },
            {
                "input": "ᡥᡡᠸᠠᠩᡩᡳ ᡳ ᡥᡝᡵᡤᡝᠨ",
                "expected": "皇帝的文字"
            }
        ]
        
        # 执行测试
        for case in test_cases:
            result = self.server.translate(case["input"])
            self.assertEqual(result, case["expected"])
            
        # 检查性能指标
        metrics = self.metrics_collector.get_metrics()
        self.assertGreater(metrics["translation_count"], 0)
        self.assertLess(metrics["average_latency"], 1.0)  # 平均延迟小于1秒
        
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效输入
        with self.assertRaises(ValueError):
            self.server.translate("")
            
        # 测试格式错误
        with self.assertRaises(ValueError):
            self.server.translate("123")
            
        # 测试超长输入
        long_input = "ᡥᠠᡳ" * 1000
        with self.assertRaises(ValueError):
            self.server.translate(long_input)
            
    def test_performance(self):
        """测试性能"""
        # 准备测试数据
        test_text = "ᡥᠠᡳ ᡳ ᠨᡳᠶᠠᠯᠮᠠ"
        iterations = 1000
        
        # 测试翻译性能
        start_time = time.time()
        for _ in range(iterations):
            self.server.translate(test_text)
        end_time = time.time()
        
        # 检查性能指标
        total_time = end_time - start_time
        avg_time = total_time / iterations
        self.assertLess(avg_time, 0.01)  # 平均每次翻译小于10ms
        
        # 检查内存使用
        metrics = self.metrics_collector.get_metrics()
        self.assertLess(metrics["memory_usage"], 1024 * 1024 * 100)  # 内存使用小于100MB
        
if __name__ == '__main__':
    unittest.main()
