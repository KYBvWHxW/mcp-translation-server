from typing import List, Dict, Optional
import json
import os
from dataclasses import dataclass
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import regex as re

@dataclass
class ParallelExample:
    """平行语料示例数据类"""
    manchu: str
    english: str
    gloss: str
    features: List[str]
    domain: str
    difficulty: float  # 示例难度系数 (0-1)
    quality: float    # 翻译质量分数 (0-1)

class ParallelCorpus:
    """平行语料库处理类，支持多种检索方法"""
    
    def __init__(self, corpus_path: str = "resources/parallel.json"):
        self.examples: List[ParallelExample] = []
        self.tfidf_vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 4)
        )
        self.bm25 = None
        self.manchu_vectors = None
        
        # 加载语料
        if os.path.exists(corpus_path):
            self._load_corpus(corpus_path)
            self._build_indices()
    
    def _load_corpus(self, path: str):
        """加载平行语料库"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for example in data:
            self.examples.append(ParallelExample(
                manchu=example['manchu'],
                english=example['english'],
                gloss=example.get('gloss', ''),
                features=example.get('features', []),
                domain=example.get('domain', 'general'),
                difficulty=float(example.get('difficulty', 0.5)),
                quality=float(example.get('quality', 1.0))
            ))
    
    def _build_indices(self):
        """构建检索索引"""
        if not self.examples:
            return
            
        # 准备文档
        manchu_texts = [ex.manchu for ex in self.examples]
        
        # TF-IDF向量化
        self.manchu_vectors = self.tfidf_vectorizer.fit_transform(manchu_texts)
        
        # BM25索引
        tokenized_corpus = [
            list(re.findall(r'\w+', text.lower()))
            for text in manchu_texts
        ]
        self.bm25 = BM25Okapi(tokenized_corpus)
    
    def _calculate_feature_similarity(
        self,
        query_features: List[str],
        example: ParallelExample
    ) -> float:
        """计算特征相似度"""
        if not query_features or not example.features:
            return 0.0
        
        common_features = set(query_features) & set(example.features)
        return len(common_features) / max(len(query_features), len(example.features))
    
    def search_by_similarity(
        self,
        query: str,
        features: List[str] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """基于TF-IDF相似度搜索
        
        Args:
            query: 查询句子
            features: 形态特征列表
            top_k: 返回结果数量
            
        Returns:
            相似度最高的示例列表
        """
        # 计算查询向量
        query_vector = self.tfidf_vectorizer.transform([query])
        
        # 计算相似度
        similarities = cosine_similarity(query_vector, self.manchu_vectors).flatten()
        
        # 如果有特征，计算特征相似度
        if features:
            feature_scores = np.array([
                self._calculate_feature_similarity(features, ex)
                for ex in self.examples
            ])
            # 综合考虑文本相似度和特征相似度
            similarities = 0.7 * similarities + 0.3 * feature_scores
        
        # 获取最相似的示例
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            example = self.examples[idx]
            results.append({
                'example': example,
                'similarity': float(similarities[idx])
            })
        
        return results
    
    def search_by_bm25(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict]:
        """基于BM25算法搜索
        
        Args:
            query: 查询句子
            top_k: 返回结果数量
            
        Returns:
            BM25得分最高的示例列表
        """
        # 对查询进行分词
        tokenized_query = list(re.findall(r'\w+', query.lower()))
        
        # 计算BM25得分
        scores = self.bm25.get_scores(tokenized_query)
        
        # 获取得分最高的示例
        top_indices = scores.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            example = self.examples[idx]
            results.append({
                'example': example,
                'score': float(scores[idx])
            })
        
        return results
    
    def process_batch(self, texts: List[str], executor) -> List[str]:
        """并行处理批量文本

        Args:
            texts: 输入文本列表
            executor: 线程池执行器

        Returns:
            处理结果列表
        """
        def process_text(text: str) -> str:
            # 查找最相关的示例
            results = self.search(text, method='hybrid', top_k=1)
            if results:
                return results[0]['example'].english
            return ''

        # 并行处理
        futures = [executor.submit(process_text, text) for text in texts]
        return [future.result() for future in futures]

    def search(
        self,
        query: str,
        features: List[str] = None,
        method: str = 'hybrid',
        top_k: int = 3
    ) -> List[Dict]:
        """综合搜索接口
        
        Args:
            query: 查询句子
            features: 形态特征列表
            method: 搜索方法 ('similarity', 'bm25', 'hybrid')
            top_k: 返回结果数量
            
        Returns:
            最相关的示例列表
        """
        if method == 'similarity':
            return self.search_by_similarity(query, features, top_k)
        elif method == 'bm25':
            return self.search_by_bm25(query, top_k)
        else:  # hybrid
            # 获取两种方法的结果
            sim_results = self.search_by_similarity(query, features, top_k)
            bm25_results = self.search_by_bm25(query, top_k)
            
            # 合并结果
            combined_scores = {}
            for result in sim_results:
                ex = result['example']
                combined_scores[ex] = {
                    'example': ex,
                    'similarity_score': result['similarity'],
                    'bm25_score': 0.0
                }
            
            for result in bm25_results:
                ex = result['example']
                if ex in combined_scores:
                    combined_scores[ex]['bm25_score'] = result['score']
                else:
                    combined_scores[ex] = {
                        'example': ex,
                        'similarity_score': 0.0,
                        'bm25_score': result['score']
                    }
            
            # 计算综合得分
            results = []
            for ex_scores in combined_scores.values():
                # 归一化BM25得分
                max_bm25 = max(r['score'] for r in bm25_results)
                norm_bm25 = ex_scores['bm25_score'] / max_bm25 if max_bm25 > 0 else 0
                
                # 计算加权得分
                final_score = (
                    0.6 * ex_scores['similarity_score'] +
                    0.4 * norm_bm25
                )
                
                results.append({
                    'example': ex_scores['example'],
                    'score': final_score,
                    'similarity_score': ex_scores['similarity_score'],
                    'bm25_score': norm_bm25
                })
            
            # 按综合得分排序
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
