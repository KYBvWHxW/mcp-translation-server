import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .enhanced_morphology import EnhancedMorphologyAnalyzer

@dataclass
class TranslationResult:
    source_text: str
    target_text: str
    confidence: float
    morpheme_analysis: Optional[Dict] = None
    alternatives: Optional[List[str]] = None

class EnhancedTranslationEngine:
    def __init__(self, 
                 rules_path: str,
                 corpus_path: str,
                 dictionary_path: str):
        self.morphology = EnhancedMorphologyAnalyzer(rules_path)
        self.corpus = self._load_corpus(corpus_path)
        self.dictionary = self._load_dictionary(dictionary_path)
        
    def _load_corpus(self, corpus_path: str) -> Dict:
        with open(corpus_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def _load_dictionary(self, dictionary_path: str) -> Dict:
        with open(dictionary_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _find_best_corpus_match(self, 
                              text: str, 
                              source_lang: str,
                              target_lang: str) -> Optional[Dict]:
        """Find the best matching sentence in the parallel corpus."""
        best_match = None
        best_score = 0
        
        source_words = set(text.lower().split())
        for entry in self.corpus["sentences"]:
            entry_words = set(entry[source_lang].lower().split())
            # Calculate Jaccard similarity
            intersection = len(source_words & entry_words)
            union = len(source_words | entry_words)
            if union > 0:
                score = intersection / union
                if score > best_score:
                    best_score = score
                    best_match = entry
                    
        return best_match if best_score > 0.5 else None

    def translate(self, 
                 text: str, 
                 source_lang: str = "manchu", 
                 target_lang: str = "chinese") -> TranslationResult:
        """Translate text with morphological analysis."""
        # First try corpus-based translation
        corpus_match = self._find_best_corpus_match(text, source_lang, target_lang)
        if corpus_match:
            return TranslationResult(
                source_text=text,
                target_text=corpus_match[target_lang],
                confidence=0.9,
                morpheme_analysis=None,
                alternatives=None
            )
            
        # If no corpus match, use morphological analysis and dictionary
        words = text.split()
        translated_words = []
        morpheme_analyses = {}
        
        for word in words:
            # Analyze morphology
            analysis = self.morphology.analyze(word)
            morpheme_analyses[word] = {
                "stem": analysis.stem,
                "suffixes": analysis.suffixes,
                "word_class": analysis.word_class,
                "features": analysis.features
            }
            
            # Look up stem in dictionary
            if analysis.stem in self.dictionary:
                entry = self.dictionary[analysis.stem]
                if isinstance(entry, dict) and target_lang in entry:
                    translated_words.append(entry[target_lang])
                else:
                    translated_words.append(word)  # Keep original if no translation
            else:
                # Try to find similar words
                possible_stems = self.morphology.get_possible_stems(word)
                translated = False
                for stem in possible_stems:
                    if stem in self.dictionary:
                        entry = self.dictionary[stem]
                        if isinstance(entry, dict) and target_lang in entry:
                            translated_words.append(entry[target_lang])
                            translated = True
                            break
                if not translated:
                    translated_words.append(word)
                    
        # Join words and return result
        target_text = " ".join(translated_words)
        
        return TranslationResult(
            source_text=text,
            target_text=target_text,
            confidence=0.7,
            morpheme_analysis=morpheme_analyses,
            alternatives=None
        )

    def batch_translate(self, 
                       texts: List[str], 
                       source_lang: str = "manchu", 
                       target_lang: str = "chinese") -> List[TranslationResult]:
        """Translate multiple texts."""
        return [self.translate(text, source_lang, target_lang) for text in texts]

    def suggest_alternatives(self, text: str) -> List[str]:
        """Suggest alternative translations or corrections."""
        words = text.split()
        suggestions = []
        
        for word in words:
            if not self.morphology.is_valid_word(word):
                corrections = self.morphology.suggest_corrections(word)
                if corrections:
                    suggestions.extend(corrections)
                    
        return suggestions

    def get_translation_metadata(self, text: str) -> Dict:
        """Get detailed metadata about the translation process."""
        words = text.split()
        metadata = {
            "word_count": len(words),
            "morpheme_analyses": {},
            "dictionary_hits": 0,
            "corpus_matches": [],
            "confidence_factors": {}
        }
        
        for word in words:
            analysis = self.morphology.analyze(word)
            metadata["morpheme_analyses"][word] = {
                "stem": analysis.stem,
                "suffixes": analysis.suffixes,
                "word_class": analysis.word_class,
                "features": analysis.features
            }
            
            if analysis.stem in self.dictionary:
                metadata["dictionary_hits"] += 1
                
        corpus_match = self._find_best_corpus_match(text, "manchu", "chinese")
        if corpus_match:
            metadata["corpus_matches"].append(corpus_match)
            
        return metadata
