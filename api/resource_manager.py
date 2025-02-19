from typing import Dict, List, Optional, Any
import json
import os
import shutil
from datetime import datetime
import threading
from errors import ValidationError

class ResourceVersion:
    """资源版本"""
    def __init__(self, version: str, timestamp: float, description: str):
        self.version = version
        self.timestamp = timestamp
        self.description = description

class ResourceManager:
    """语言资源管理器"""
    
    def __init__(self, resource_dir: str = "resources"):
        self.resource_dir = resource_dir
        self.backup_dir = os.path.join(resource_dir, "backups")
        self.version_file = os.path.join(resource_dir, "versions.json")
        self.lock = threading.Lock()
        self.versions: Dict[str, List[ResourceVersion]] = {}
        
        # 确保目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        self.load_versions()
        
    def load_versions(self):
        """加载版本信息"""
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.versions = {
                    resource: [ResourceVersion(**v) for v in versions]
                    for resource, versions in data.items()
                }
                
    def save_versions(self):
        """保存版本信息"""
        data = {
            resource: [
                {
                    'version': v.version,
                    'timestamp': v.timestamp,
                    'description': v.description
                }
                for v in versions
            ]
            for resource, versions in self.versions.items()
        }
        
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def update_resource(
        self,
        resource_name: str,
        content: Dict[str, Any],
        version: str,
        description: str
    ):
        """更新资源文件"""
        with self.lock:
            resource_path = os.path.join(self.resource_dir, f"{resource_name}.json")
            
            # 创建备份
            if os.path.exists(resource_path):
                backup_path = os.path.join(
                    self.backup_dir,
                    f"{resource_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                shutil.copy2(resource_path, backup_path)
                
            # 写入新内容
            with open(resource_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
                
            # 更新版本信息
            if resource_name not in self.versions:
                self.versions[resource_name] = []
                
            self.versions[resource_name].append(
                ResourceVersion(
                    version=version,
                    timestamp=datetime.now().timestamp(),
                    description=description
                )
            )
            
            self.save_versions()
            
    def get_resource_version(
        self,
        resource_name: str,
        version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取指定版本的资源"""
        resource_path = os.path.join(self.resource_dir, f"{resource_name}.json")
        
        if version is None:
            # 返回最新版本
            if os.path.exists(resource_path):
                with open(resource_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
            
        # 查找指定版本的备份
        backup_files = [
            f for f in os.listdir(self.backup_dir)
            if f.startswith(f"{resource_name}_")
        ]
        
        for backup in sorted(backup_files, reverse=True):
            backup_path = os.path.join(self.backup_dir, backup)
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('version') == version:
                    return data
                    
        return None
        
    def list_versions(self, resource_name: str) -> List[ResourceVersion]:
        """列出资源的所有版本"""
        return self.versions.get(resource_name, [])
        
    def rollback_resource(self, resource_name: str, version: str):
        """回滚到指定版本"""
        with self.lock:
            # 获取指定版本的内容
            content = self.get_resource_version(resource_name, version)
            if content is None:
                raise ValidationError(f"找不到资源 '{resource_name}' 的版本 '{version}'")
                
            # 更新到指定版本
            self.update_resource(
                resource_name,
                content,
                f"{version}_rollback",
                f"回滚到版本 {version}"
            )
            
    def validate_resource(
        self,
        resource_name: str,
        content: Dict[str, Any]
    ) -> List[str]:
        """验证资源内容"""
        errors = []
        
        # 根据资源类型进行验证
        if resource_name == 'grammar':
            errors.extend(self._validate_grammar(content))
        elif resource_name == 'morphology':
            errors.extend(self._validate_morphology(content))
        elif resource_name == 'lexicon':
            errors.extend(self._validate_lexicon(content))
            
        return errors
        
    def _validate_grammar(self, content: Dict[str, Any]) -> List[str]:
        """验证语法规则"""
        errors = []
        if 'rules' not in content:
            errors.append("缺少 'rules' 字段")
        else:
            for i, rule in enumerate(content['rules']):
                if 'rule_id' not in rule:
                    errors.append(f"规则 {i} 缺少 'rule_id'")
                if 'type' not in rule:
                    errors.append(f"规则 {i} 缺少 'type'")
        return errors
        
    def _validate_morphology(self, content: Dict[str, Any]) -> List[str]:
        """验证形态规则"""
        errors = []
        if 'rules' not in content:
            errors.append("缺少 'rules' 字段")
        else:
            for i, rule in enumerate(content['rules']):
                if 'rule_id' not in rule:
                    errors.append(f"规则 {i} 缺少 'rule_id'")
                if 'word_class' not in rule:
                    errors.append(f"规则 {i} 缺少 'word_class'")
        return errors
        
    def _validate_lexicon(self, content: Dict[str, Any]) -> List[str]:
        """验证词典"""
        errors = []
        for word, info in content.items():
            if 'word_class' not in info:
                errors.append(f"词条 '{word}' 缺少 'word_class'")
            if 'features' not in info:
                errors.append(f"词条 '{word}' 缺少 'features'")
        return errors

    def get_current_version(self) -> str:
        """获取当前版本"""
        with self.lock:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"v{timestamp}"

    def create_backup(self) -> str:
        """创建备份"""
        with self.lock:
            backup_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.backup_dir, backup_id)
            os.makedirs(backup_dir, exist_ok=True)

            # 复制所有资源文件
            for file in os.listdir(self.resource_dir):
                if file.endswith('.json'):
                    shutil.copy2(
                        os.path.join(self.resource_dir, file),
                        os.path.join(backup_dir, file)
                    )

            return backup_id

    def verify_backup(self, backup_id: str) -> bool:
        """验证备份"""
        backup_dir = os.path.join(self.backup_dir, backup_id)
        if not os.path.exists(backup_dir):
            return False

        # 检查必要的资源文件
        required_files = {'grammar.json', 'morphology.json', 'lexicon.json'}
        backup_files = set(os.listdir(backup_dir))
        return required_files.issubset(backup_files)

    def restore_backup(self, backup_id: str) -> bool:
        """恢复备份"""
        if not self.verify_backup(backup_id):
            return False

        with self.lock:
            backup_dir = os.path.join(self.backup_dir, backup_id)
            for file in os.listdir(backup_dir):
                shutil.copy2(
                    os.path.join(backup_dir, file),
                    os.path.join(self.resource_dir, file)
                )
            return True
