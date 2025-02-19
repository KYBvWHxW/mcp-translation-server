from typing import List, Dict, Optional
import Levenshtein
from collections import defaultdict
import json
import os
from dataclasses import dataclass
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class DictionaryEntry:
    """词典条目数据类"""
    word: str
    lexical: str
    suffixes: List[str]
    collocations: List[str]
    senses: List[Dict[str, str]]  # 多义词义项列表
    examples: List[Dict[str, str]]  # 用例列表
    
class ManchuDictionary:
    """满文词典类，支持模糊匹配和多义词处理"""
    
    def __init__(self, dictionary_path: str = "resources/dictionary.json"):
        self.entries: Dict[str, DictionaryEntry] = {}
        self.word_vectors = None
        self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 3))
        
        # 加载词典
        if os.path.exists(dictionary_path):
            self._load_dictionary(dictionary_path)
            self._build_index()
    
    def _load_dictionary(self, path: str):
        """加载词典数据"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for entry in data:
            # 确保每个条目都有完整的字段
            if isinstance(entry, dict) and 'word' in entry:
                self.entries[entry['word']] = DictionaryEntry(
                    word=entry['word'],
                    lexical=entry.get('lexical', ''),
                    suffixes=entry.get('suffixes', []),
                    collocations=entry.get('collocations', []),
                    senses=entry.get('senses', [{'meaning': entry.get('lexical', '')}]),
                    examples=entry.get('examples', [])
                )
    
    def _build_index(self):
        """构建搜索索引"""
        # 为所有词条创建TF-IDF向量
        words = list(self.entries.keys())
        if not words:
            return
            
        # 构建字符级别的TF-IDF矩阵
        word_matrix = self.vectorizer.fit_transform([word for word in words])
        self.word_vectors = word_matrix
        
    def fuzzy_search(self, query: str, threshold: float = 0.7) -> List[Dict]:
        """模糊搜索
        
        Args:
            query: 搜索词
            threshold: 相似度阈值
            
        Returns:
            匹配的词条列表，按相似度排序
        """
        if not query or not self.entries:
            return []
            
        # 计算查询词的向量
        query_vector = self.vectorizer.transform([query])
        
        # 计算与所有词条的相似度
        similarities = cosine_similarity(query_vector, self.word_vectors).flatten()
        
        # 获取相似度超过阈值的词条
        matches = []
        for idx, sim in enumerate(similarities):
            if sim >= threshold:
                word = list(self.entries.keys())[idx]
                matches.append({
                    'word': word,
                    'entry': self.entries[word],
                    'similarity': float(sim)
                })
        
        # 按相似度排序
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches
    
    def disambiguate(self, word: str, context: str) -> Optional[Dict]:
        """多义词消歧
        
        Args:
            word: 待消歧的词
            context: 上下文
            
        Returns:
            最匹配的词义
        """
        entry = self.entries.get(word)
        if not entry or len(entry.senses) <= 1:
            return entry.senses[0] if entry and entry.senses else None
            
        # 计算上下文与各个词义的相似度
        context_vector = self.vectorizer.transform([context])
        sense_vectors = self.vectorizer.transform([
            f"{sense.get('meaning', '')} {' '.join(example.get('text', '') for example in entry.examples)}"
            for sense in entry.senses
        ])
        
        # 计算相似度
        similarities = cosine_similarity(context_vector, sense_vectors).flatten()
        
        # 返回最匹配的词义
        best_sense_idx = np.argmax(similarities)
        return entry.senses[best_sense_idx]
    
    def search(self, word: str, context: str = None) -> Dict:
        """综合搜索接口
        
        Args:
            word: 搜索词
            context: 上下文（可选）
            
        Returns:
            搜索结果
        """
        # 精确匹配
        if word in self.entries:
            entry = self.entries[word]
            result = {
                'word': word,
                'entry': entry,
                'match_type': 'exact'
            }
            # 如果有上下文，进行多义词消歧
            if context and len(entry.senses) > 1:
                result['disambiguated_sense'] = self.disambiguate(word, context)
            return result
            
        # 模糊匹配
        fuzzy_matches = self.fuzzy_search(word)
        if fuzzy_matches:
            result = fuzzy_matches[0]
            result['match_type'] = 'fuzzy'
            # 对最佳匹配进行多义词消歧
            if context and len(result['entry'].senses) > 1:
                result['disambiguated_sense'] = self.disambiguate(
                    result['entry'].word, context
                )
            return result
            
        return {
            'word': word,
            'match_type': 'not_found'
        }
