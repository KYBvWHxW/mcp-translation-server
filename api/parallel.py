"""
平行语料库组件
"""
from .base import BaseComponent
from dataclasses import dataclass
from typing import List, Optional
import json

@dataclass(frozen=True)
class ParallelExample:
    """平行语料例句"""
    manchu: str
    chinese: str
    source: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            object.__setattr__(self, 'tags', [])
            
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "manchu": self.manchu,
            "chinese": self.chinese,
            "source": self.source,
            "tags": self.tags
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'ParallelExample':
        """从字典创建实例"""
        return cls(
            manchu=data["manchu"],
            chinese=data["chinese"],
            source=data.get("source", ""),
            tags=data.get("tags", [])
        )
        
    def __hash__(self):
        return hash((self.manchu, self.chinese, self.source, tuple(self.tags)))

class ParallelCorpus(BaseComponent):
    """平行语料库类"""
    
    def __init__(self):
        """初始化语料库"""
        self.examples: List[ParallelExample] = []
        self.ready = False
        self.load_corpus()
        
    def load_corpus(self):
        """加载语料库数据"""
        # 临时测试数据
        test_examples = [
            ParallelExample(
                manchu="ᠠᠯᡳᠨ ᡳ ᠨᡳᠶᠠᠯᠮᠠ",
                chinese="山的人",
                source="test",
                tags=["test"]
            ),
            ParallelExample(
                manchu="ᡥᡡᠸᠠᠩᡩᡳ ᡳ ᡥᡝᡵᡤᡝᠨ",
                chinese="皇帝的文字",
                source="test",
                tags=["test"]
            )
        ]
        self.examples.extend(test_examples)
        self.ready = True
        
    def add_example(self, example: ParallelExample):
        """添加例句"""
        self.examples.append(example)
        
    def search(self, query: str, source_lang: str = 'Manchu') -> List[ParallelExample]:
        """搜索例句"""
        results = []
        query = query.lower()
        for example in self.examples:
            if source_lang == 'Manchu':
                if query in example.manchu.lower():
                    results.append(example)
            else:
                if query in example.chinese.lower():
                    results.append(example)
        return results
        
    def is_ready(self) -> bool:
        """检查组件是否就绪"""
        return self.ready
        
    def get_status(self) -> dict:
        """获取组件状态"""
        return {
            "ready": self.ready,
            "example_count": len(self.examples)
        }
