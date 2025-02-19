from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import os
from datetime import datetime
import threading
from errors import ValidationError

@dataclass
class Term:
    """术语条目"""
    source: str
    target: str
    pos: str
    domain: str
    register: str
    variants: List[str]
    context: str
    notes: str

class TerminologyManager:
    """术语管理器"""
    
    def __init__(self, terminology_file: str = "resources/terminology.json"):
        self.terminology_file = terminology_file
        self.terms: Dict[str, Term] = {}
        self.lock = threading.Lock()
        self.load_terminology()
        
    def load_terminology(self):
        """加载术语库"""
        if os.path.exists(self.terminology_file):
            with open(self.terminology_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.terms = {
                    term['source']: Term(**term)
                    for term in data['terms']
                }
                
    def save_terminology(self):
        """保存术语库"""
        data = {
            'terms': [
                {
                    'source': source,
                    'target': term.target,
                    'pos': term.pos,
                    'domain': term.domain,
                    'register': term.register,
                    'variants': term.variants,
                    'context': term.context,
                    'notes': term.notes
                }
                for source, term in self.terms.items()
            ],
            'metadata': {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'source_language': 'manchu',
                'target_language': 'chinese',
                'total_terms': len(self.terms),
                'domains': list(set(term.domain for term in self.terms.values()))
            }
        }
        
        with open(self.terminology_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def add_term(self, term: Term):
        """添加术语"""
        with self.lock:
            if term.source in self.terms:
                raise ValidationError(f"术语 '{term.source}' 已存在")
            self.terms[term.source] = term
            self.save_terminology()
            
    def update_term(self, source: str, term: Term):
        """更新术语"""
        with self.lock:
            if source not in self.terms:
                raise ValidationError(f"术语 '{source}' 不存在")
            self.terms[source] = term
            self.save_terminology()
            
    def delete_term(self, source: str):
        """删除术语"""
        with self.lock:
            if source not in self.terms:
                raise ValidationError(f"术语 '{source}' 不存在")
            del self.terms[source]
            self.save_terminology()
            
    def get_term(self, source: str) -> Optional[Term]:
        """获取术语"""
        return self.terms.get(source)
        
    def search_terms(
        self,
        query: str,
        domain: Optional[str] = None,
        pos: Optional[str] = None
    ) -> List[Term]:
        """搜索术语"""
        results = []
        for term in self.terms.values():
            if (query.lower() in term.source.lower() or
                query.lower() in term.target.lower()):
                if domain and term.domain != domain:
                    continue
                if pos and term.pos != pos:
                    continue
                results.append(term)
        return results
        
    def get_domains(self) -> List[str]:
        """获取所有领域"""
        return list(set(term.domain for term in self.terms.values()))
        
    def get_pos_tags(self) -> List[str]:
        """获取所有词性标记"""
        return list(set(term.pos for term in self.terms.values()))
        
    def export_glossary(self, format: str = 'txt') -> str:
        """导出术语表"""
        if format == 'txt':
            lines = []
            for term in sorted(self.terms.values(), key=lambda x: x.source):
                lines.append(f"{term.source}\t{term.target}\t{term.pos}\t{term.notes}")
            return '\n'.join(lines)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
            
    def import_glossary(self, content: str, format: str = 'txt'):
        """导入术语表"""
        with self.lock:
            if format == 'txt':
                for line in content.strip().split('\n'):
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        source, target = parts[:2]
                        pos = parts[2] if len(parts) > 2 else 'unknown'
                        notes = parts[3] if len(parts) > 3 else ''
                        
                        self.terms[source] = Term(
                            source=source,
                            target=target,
                            pos=pos,
                            domain='general',
                            register='common',
                            variants=[],
                            context='',
                            notes=notes
                        )
                self.save_terminology()
            else:
                raise ValueError(f"不支持的导入格式: {format}")
