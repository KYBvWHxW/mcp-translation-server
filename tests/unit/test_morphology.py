import unittest
from morphology import ManchuMorphologyAnalyzer

class TestMorphologyAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ManchuMorphologyAnalyzer()
        
    def test_word_analysis(self):
        # Test basic word analysis
        result = self.analyzer.analyze_word("mini")
        self.assertIsNotNone(result)
        self.assertIn('root', result)
        self.assertIn('features', result)
        
    def test_suffix_detection(self):
        # Test suffix detection
        result = self.analyzer.analyze_word("gisunbe")
        self.assertIn('suffixes', result)
        self.assertTrue(len(result['suffixes']) > 0)
        
    def test_invalid_input(self):
        # Test handling of invalid input
        with self.assertRaises(ValueError):
            self.analyzer.analyze_word("")
        with self.assertRaises(TypeError):
            self.analyzer.analyze_word(None)
            
if __name__ == '__main__':
    unittest.main()
