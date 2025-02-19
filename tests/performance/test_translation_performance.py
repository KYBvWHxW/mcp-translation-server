import unittest
import time
from server import TranslationServer
from concurrent.futures import ThreadPoolExecutor
import statistics

class TestTranslationPerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TranslationServer()
        cls.sample_texts = [
            "mini gisun",
            "sini gisun",
            "ini gisun",
            "musei gisun",
            "suwei gisun"
        ]
        
    def test_translation_latency(self):
        # Test translation latency
        latencies = []
        for text in self.sample_texts:
            start_time = time.time()
            self.server.translate(text)
            latency = time.time() - start_time
            latencies.append(latency)
            
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        
        # Assert performance SLAs
        self.assertLess(avg_latency, 1.0)  # Average latency < 1s
        self.assertLess(p95_latency, 2.0)  # 95th percentile < 2s
        
    def test_concurrent_performance(self):
        # Test concurrent translation performance
        def translate_text(text):
            return self.server.translate(text)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            results = list(executor.map(translate_text, self.sample_texts * 2))
            total_time = time.time() - start_time
            
        # Assert concurrent performance
        self.assertLess(total_time, 5.0)  # Total time for 10 concurrent requests < 5s
        self.assertEqual(len(results), len(self.sample_texts) * 2)
        
    def test_memory_usage(self):
        # Test memory usage
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform multiple translations
        for _ in range(10):
            for text in self.sample_texts:
                self.server.translate(text)
                
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Assert memory usage
        self.assertLess(memory_increase, 100)  # Memory increase < 100MB
        
if __name__ == '__main__':
    unittest.main()
