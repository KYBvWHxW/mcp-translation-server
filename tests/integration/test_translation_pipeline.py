import unittest
from server import TranslationServer
import json

class TestTranslationPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = TranslationServer()
        
    def test_end_to_end_translation(self):
        # Test complete translation pipeline
        text = "mini gisun"
        result = self.server.translate(text)
        self.assertIsNotNone(result)
        self.assertIn('translation', result)
        self.assertIn('analysis', result)
        
    def test_dictionary_integration(self):
        # Test dictionary integration
        words = ["mini", "gisun"]
        entries = self.server.get_dictionary_entries(words)
        self.assertIsNotNone(entries)
        self.assertEqual(len(entries), len(words))
        
    def test_grammar_integration(self):
        # Test grammar rule integration
        text = "mini gisun"
        result = self.server.translate(text)
        self.assertIn('grammar_rules', result)
        
    def test_error_handling(self):
        # Test error handling across components
        with self.assertRaises(Exception):
            self.server.translate("")
            
if __name__ == '__main__':
    unittest.main()
