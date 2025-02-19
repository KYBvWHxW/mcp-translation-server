import pytest
from dictionary import ManchuDictionary, DictionaryEntry
import json
import os

@pytest.fixture
def test_dictionary_data():
    return [
        {
            "word": "amba",
            "lexical": "大",
            "suffixes": ["-i", "-be"],
            "collocations": ["amba boo", "amba niyalma"],
            "senses": [{"meaning": "大", "context": "形容词"}],
            "examples": [{"manchu": "amba boo", "chinese": "大房子"}]
        },
        {
            "word": "niyalma",
            "lexical": "人",
            "suffixes": ["-i", "-be"],
            "collocations": ["ere niyalma", "tere niyalma"],
            "senses": [{"meaning": "人", "context": "名词"}],
            "examples": [{"manchu": "ere niyalma", "chinese": "这个人"}]
        }
    ]

@pytest.fixture
def test_dictionary(test_dictionary_data, tmp_path):
    # Create temporary dictionary file
    dict_file = tmp_path / "test_dictionary.json"
    with open(dict_file, 'w', encoding='utf-8') as f:
        json.dump(test_dictionary_data, f, ensure_ascii=False)
    
    return ManchuDictionary(str(dict_file))

def test_dictionary_load(test_dictionary):
    """Test dictionary loading."""
    assert len(test_dictionary.entries) == 2
    assert "amba" in test_dictionary.entries
    assert "niyalma" in test_dictionary.entries

def test_entry_fields(test_dictionary):
    """Test entry field access."""
    entry = test_dictionary.entries["amba"]
    assert isinstance(entry, DictionaryEntry)
    assert entry.word == "amba"
    assert entry.lexical == "大"
    assert "-i" in entry.suffixes
    assert "amba boo" in entry.collocations
    assert len(entry.senses) == 1
    assert entry.senses[0]["meaning"] == "大"
    assert len(entry.examples) == 1
    assert entry.examples[0]["manchu"] == "amba boo"

def test_fuzzy_search(test_dictionary):
    """Test fuzzy search functionality."""
    # Build index first
    test_dictionary._build_index()
    
    results = test_dictionary.fuzzy_search("amb")
    assert len(results) > 0
    assert any(entry.word == "amba" for entry in results)

def test_semantic_search(test_dictionary):
    """Test semantic search functionality."""
    # Build index first
    test_dictionary._build_index()
    
    results = test_dictionary.semantic_search("大的")
    assert len(results) > 0
    assert any(entry.word == "amba" for entry in results)

def test_collocation_search(test_dictionary):
    """Test collocation search."""
    results = test_dictionary.search_collocations("boo")
    assert len(results) > 0
    assert any("amba boo" in result for result in results)

def test_example_search(test_dictionary):
    """Test example search."""
    results = test_dictionary.search_examples("大")
    assert len(results) > 0
    assert any("大房子" in example["chinese"] for example in results)

def test_invalid_dictionary_file():
    """Test handling of invalid dictionary file."""
    with pytest.raises(Exception):
        ManchuDictionary("nonexistent_file.json")

def test_batch_lookup(test_dictionary):
    """Test looking up multiple words."""
    words = ["amba", "niyalma", "nonexistent"]
    results = [test_dictionary.entries.get(word) for word in words]
    assert len(results) == 3
    assert results[0] is not None
    assert results[1] is not None
    assert results[2] is None
