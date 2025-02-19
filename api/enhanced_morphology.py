import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

@dataclass
class MorphemeAnalysis:
    stem: str
    suffixes: List[str]
    word_class: str
    harmony_type: str
    features: Dict[str, str]

class EnhancedMorphologyAnalyzer:
    def __init__(self, rules_path: str):
        self.rules = self._load_rules(rules_path)
        self.vowels = set(self.rules["phonology"]["vowels"])
        self.consonants = set(self.rules["phonology"]["consonants"])
        self.harmony_groups = self.rules["phonology"]["harmony_groups"]
        self.verb_classes = self.rules["morphology"]["verb_classes"]
        self.noun_classes = self.rules["morphology"]["noun_classes"]
        
    def _load_rules(self, rules_path: str) -> Dict:
        with open(rules_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_harmony_type(self, word: str) -> str:
        """Determine vowel harmony type of a word."""
        word_vowels = [c for c in word if c in self.vowels]
        if not word_vowels:
            return "neutral"
            
        first_vowel = word_vowels[0]
        for group_name, vowels in self.harmony_groups.items():
            if first_vowel in vowels:
                return group_name
        return "neutral"

    def identify_stem(self, word: str) -> Tuple[str, List[str]]:
        """Identify the stem and suffixes of a word."""
        # Check verb suffixes first
        for suffix in self.verb_classes["regular"]["suffixes"]:
            if word.endswith(suffix):
                return word[:-len(suffix)], [suffix]
                    
        # Check noun suffixes
        for case, suffix in self.noun_classes["regular"]["case_suffixes"].items():
            if suffix and word.endswith(suffix):
                # Check for number suffix before case suffix
                stem = word[:-len(suffix)]
                for number, num_suffix in self.noun_classes["regular"]["number_suffixes"].items():
                    if num_suffix and stem.endswith(num_suffix):
                        return stem[:-len(num_suffix)], [num_suffix, suffix]
                return stem, [suffix]
                
        return word, []

    def analyze(self, word: str) -> MorphemeAnalysis:
        """Perform complete morphological analysis of a word."""
        stem, suffixes = self.identify_stem(word)
        harmony_type = self.get_harmony_type(stem)
        
        # Determine word class
        word_class = "unknown"
        features = {}
        
        # Check if it's a verb
        if any(word.endswith(s) for s in self.verb_classes["regular"]["suffixes"]):
            word_class = "verb"
            # Determine verb features
            for suffix in suffixes:
                if suffix in ["mbi", "ra", "ki"]:
                    features["tense"] = "present"
                elif suffix in ["ha", "he"]:
                    features["tense"] = "past"
                elif suffix in ["ki", "kini"]:
                    features["mood"] = "optative"
                    
        # Check if it's a noun
        elif any(word.endswith(s) for s in self.noun_classes["regular"]["case_suffixes"].values()):
            word_class = "noun"
            # Determine noun features
            for suffix in suffixes:
                if suffix in self.noun_classes["regular"]["case_suffixes"].values():
                    for case, s in self.noun_classes["regular"]["case_suffixes"].items():
                        if s == suffix:
                            features["case"] = case
                elif suffix in self.noun_classes["regular"]["number_suffixes"].values():
                    for number, s in self.noun_classes["regular"]["number_suffixes"].items():
                        if s == suffix:
                            features["number"] = number
                            
        return MorphemeAnalysis(
            stem=stem,
            suffixes=suffixes,
            word_class=word_class,
            harmony_type=harmony_type,
            features=features
        )

    def generate_form(self, stem: str, word_class: str, features: Dict[str, str]) -> str:
        """Generate a word form from stem and features."""
        result = stem
        harmony_type = self.get_harmony_type(stem)
        
        if word_class == "verb":
            if features.get("tense") == "present":
                suffix = "mbi"
            elif features.get("tense") == "past":
                suffix = "ha" if harmony_type == "a_harmony" else "he"
            elif features.get("mood") == "optative":
                suffix = "ki"
            else:
                return result
            result += suffix
            
        elif word_class == "noun":
            # Add number suffix if specified
            if "number" in features:
                number_suffix = self.noun_classes["regular"]["number_suffixes"].get(features["number"])
                if number_suffix:
                    result += number_suffix
                    
            # Add case suffix if specified
            if "case" in features:
                case_suffix = self.noun_classes["regular"]["case_suffixes"].get(features["case"])
                if case_suffix:
                    result += case_suffix
                    
        return result

    def get_possible_stems(self, word: str) -> List[str]:
        """Get all possible stems for a word."""
        possible_stems = []
        analysis = self.analyze(word)
        possible_stems.append(analysis.stem)
        
        # Try removing different combinations of suffixes
        for i in range(len(analysis.suffixes)):
            potential_stem = word
            for j in range(i + 1):
                suffix = analysis.suffixes[j]
                if potential_stem.endswith(suffix):
                    potential_stem = potential_stem[:-len(suffix)]
            possible_stems.append(potential_stem)
            
        return list(set(possible_stems))  # Remove duplicates

    def is_valid_word(self, word: str) -> bool:
        """Check if a word follows Manchu phonological rules."""
        # Check basic phonological patterns
        prev_char = None
        for char in word:
            if char not in self.vowels and char not in self.consonants:
                return False
                
            # Check for invalid consonant clusters
            if prev_char in self.consonants and char in self.consonants:
                # Some consonant clusters are allowed
                allowed_clusters = [("ng", "g"), ("mb", "b")]
                if (prev_char, char) not in allowed_clusters:
                    return False
            prev_char = char
            
        # Check vowel harmony
        harmony_type = self.get_harmony_type(word)
        if harmony_type != "neutral":
            word_vowels = [c for c in word if c in self.vowels]
            harmony_vowels = self.harmony_groups[harmony_type]
            for vowel in word_vowels:
                if vowel not in harmony_vowels and vowel not in self.harmony_groups["neutral"]:
                    return False
                    
        return True

    def suggest_corrections(self, word: str) -> List[str]:
        """Suggest possible corrections for an invalid word."""
        if self.is_valid_word(word):
            return [word]
            
        suggestions = []
        harmony_type = self.get_harmony_type(word)
        
        # Try fixing vowel harmony
        if harmony_type != "neutral":
            fixed_word = ""
            for char in word:
                if char in self.vowels and char not in self.harmony_groups[harmony_type]:
                    # Replace with corresponding vowel from correct harmony group
                    for harm_vowel in self.harmony_groups[harmony_type]:
                        candidate = fixed_word + harm_vowel
                        if self.is_valid_word(candidate):
                            suggestions.append(candidate)
                else:
                    fixed_word += char
                    
        # Try splitting invalid consonant clusters
        prev_char = None
        for i, char in enumerate(word):
            if prev_char in self.consonants and char in self.consonants:
                # Try inserting a vowel between consonants
                for vowel in self.vowels:
                    candidate = word[:i] + vowel + word[i:]
                    if self.is_valid_word(candidate):
                        suggestions.append(candidate)
            prev_char = char
            
        return list(set(suggestions))  # Remove duplicates
