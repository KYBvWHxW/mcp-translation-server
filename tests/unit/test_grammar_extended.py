import pytest
from grammar import GrammarRuleEngine, Rule, RuleMatch
import json

@pytest.fixture
def test_rules_data():
    return {
        "rules": [
            {
                "id": "R001",
                "pattern": "^(ere|tere) (\\w+)",
                "description": "Demonstrative + Noun",
                "priority": 1,
                "transformation": "{1} {2}",
                "examples": ["ere boo", "tere niyalma"]
            },
            {
                "id": "R002",
                "pattern": "(\\w+) be$",
                "description": "Accusative case marker",
                "priority": 2,
                "transformation": "{1}を",
                "examples": ["boo be", "niyalma be"]
            }
        ]
    }

@pytest.fixture
def grammar_engine(test_rules_data, tmp_path):
    # Create temporary rules file
    rules_file = tmp_path / "test_rules.json"
    with open(rules_file, 'w', encoding='utf-8') as f:
        json.dump(test_rules_data, f, ensure_ascii=False)
    
    return GrammarRuleEngine(str(rules_file))

def test_rule_loading(grammar_engine):
    """Test grammar rules loading."""
    assert len(grammar_engine.rules) == 2
    assert all(isinstance(rule, Rule) for rule in grammar_engine.rules)

def test_find_matching_rules(grammar_engine):
    """Test finding matching rules for text."""
    matches = grammar_engine.find_matching_rules("ere boo")
    assert len(matches) == 1
    assert matches[0].rule.id == "R001"

def test_rule_priority(grammar_engine):
    """Test rule priority ordering."""
    matches = grammar_engine.find_matching_rules("ere boo be")
    assert len(matches) == 2
    assert matches[0].rule.priority > matches[1].rule.priority

def test_apply_rules(grammar_engine):
    """Test applying grammar rules to text."""
    result = grammar_engine.apply_rules("ere boo")
    assert result is not None
    assert isinstance(result, str)

def test_rule_match_groups(grammar_engine):
    """Test rule match group extraction."""
    matches = grammar_engine.find_matching_rules("ere boo")
    assert len(matches) == 1
    match = matches[0]
    assert len(match.groups) > 0
    assert match.groups[1] == "ere"
    assert match.groups[2] == "boo"

def test_multiple_rule_application(grammar_engine):
    """Test applying multiple rules in sequence."""
    text = "ere boo be"
    result = grammar_engine.apply_rules(text)
    assert result is not None
    # Verify both rules were applied

def test_no_matching_rules(grammar_engine):
    """Test behavior when no rules match."""
    result = grammar_engine.apply_rules("random text")
    assert result == "random text"  # Should return original text

def test_invalid_pattern(grammar_engine):
    """Test handling of invalid regex pattern."""
    invalid_rule = Rule(
        id="INVALID",
        pattern="[invalid",  # Invalid regex
        description="Invalid rule",
        priority=1,
        transformation="{1}",
        examples=[]
    )
    with pytest.raises(Exception):
        grammar_engine.add_rule(invalid_rule)

def test_rule_examples(grammar_engine):
    """Test rule examples validation."""
    for rule in grammar_engine.rules:
        for example in rule.examples:
            matches = grammar_engine.find_matching_rules(example)
            assert any(m.rule.id == rule.id for m in matches)

def test_transformation_application(grammar_engine):
    """Test applying transformations with captured groups."""
    matches = grammar_engine.find_matching_rules("ere boo")
    assert len(matches) == 1
    match = matches[0]
    result = grammar_engine.apply_transformation(match)
    assert result is not None
    assert "ere" in result
    assert "boo" in result

def test_add_rule(grammar_engine):
    """Test adding new grammar rule."""
    new_rule = Rule(
        id="R003",
        pattern="(\\w+) de$",
        description="Locative case marker",
        priority=1,
        transformation="{1}に",
        examples=["boo de"]
    )
    grammar_engine.add_rule(new_rule)
    
    # Verify addition
    matches = grammar_engine.find_matching_rules("boo de")
    assert any(m.rule.id == "R003" for m in matches)

def test_remove_rule(grammar_engine):
    """Test removing grammar rule."""
    grammar_engine.remove_rule("R001")
    matches = grammar_engine.find_matching_rules("ere boo")
    assert len(matches) == 0

def test_save_rules(grammar_engine, tmp_path):
    """Test saving grammar rules to file."""
    save_path = tmp_path / "saved_rules.json"
    grammar_engine.save_rules(str(save_path))
    
    # Verify file exists and content
    assert save_path.exists()
    with open(save_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert len(data["rules"]) == 2

def test_rule_conflicts(grammar_engine):
    """Test handling of conflicting rules."""
    conflicting_rule = Rule(
        id="CONFLICT",
        pattern="^ere \\w+",  # Conflicts with R001
        description="Conflicting rule",
        priority=1,
        transformation="{0}",
        examples=["ere boo"]
    )
    grammar_engine.add_rule(conflicting_rule)
    
    matches = grammar_engine.find_matching_rules("ere boo")
    # Should still work and return all matching rules
    assert len(matches) > 1
