import unittest
from grammar import GrammarRuleEngine

class TestGrammarRuleEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GrammarRuleEngine()
        
    def test_find_matching_rules(self):
        # Test basic rule matching
        text = "mini gisun"
        rules = self.engine.find_matching_rules(text)
        self.assertIsNotNone(rules)
        self.assertIsInstance(rules, list)
        
    def test_rule_priority(self):
        # Test rule priority ordering
        text = "mini gisun"
        rules = self.engine.find_matching_rules(text)
        if len(rules) > 1:
            self.assertGreaterEqual(
                rules[0].get('priority', 0),
                rules[1].get('priority', 0)
            )
            
    def test_invalid_input(self):
        # Test handling of invalid input
        with self.assertRaises(ValueError):
            self.engine.find_matching_rules("")
        with self.assertRaises(TypeError):
            self.engine.find_matching_rules(None)
            
if __name__ == '__main__':
    unittest.main()
