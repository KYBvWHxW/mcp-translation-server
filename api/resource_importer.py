from typing import Dict, List, Any, Optional, Tuple
import json
import yaml
import xml.etree.ElementTree as ET
import csv
import os
from datetime import datetime
from .resource_validator import ResourceValidator, ValidationResult

class ImportError(Exception):
    """导入错误"""
    pass

class ResourceImporter:
    """资源导入器"""
    
    def __init__(self, resource_dir: str = "resources"):
        self.resource_dir = resource_dir
        self.validator = ResourceValidator()
        
    def validate_import_file(
        self,
        file_path: str,
        resource_type: str
    ) -> ValidationResult:
        """验证导入文件"""
        if not os.path.exists(file_path):
            raise ImportError(f"文件不存在: {file_path}")
            
        # 根据文件扩展名选择解析方法
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.json':
                data = self._parse_json(file_path)
            elif ext == '.yaml' or ext == '.yml':
                data = self._parse_yaml(file_path)
            elif ext == '.xml':
                data = self._parse_xml(file_path)
            elif ext == '.csv':
                data = self._parse_csv(file_path)
            else:
                raise ImportError(f"不支持的文件格式: {ext}")
        except Exception as e:
            raise ImportError(f"解析文件失败: {str(e)}")
            
        # 验证资源内容
        if resource_type == 'grammar':
            return self.validator.validate_grammar(data)
        elif resource_type == 'morphology':
            return self.validator.validate_morphology(data)
        elif resource_type == 'lexicon':
            return self.validator.validate_lexicon(data)
        elif resource_type == 'terminology':
            return self.validator.validate_terminology(data)
        else:
            raise ImportError(f"未知的资源类型: {resource_type}")
            
    def import_resource(
        self,
        file_path: str,
        resource_type: str,
        validate: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """导入资源"""
        # 验证文件
        if validate:
            validation_result = self.validate_import_file(file_path, resource_type)
            if not validation_result.is_valid:
                return False, f"验证失败: {', '.join(validation_result.errors)}"
                
        # 解析文件
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.json':
                data = self._parse_json(file_path)
            elif ext == '.yaml' or ext == '.yml':
                data = self._parse_yaml(file_path)
            elif ext == '.xml':
                data = self._parse_xml(file_path)
            elif ext == '.csv':
                data = self._parse_csv(file_path)
            else:
                return False, f"不支持的文件格式: {ext}"
        except Exception as e:
            return False, f"解析文件失败: {str(e)}"
            
        # 备份现有资源
        target_file = os.path.join(self.resource_dir, f"{resource_type}.json")
        if os.path.exists(target_file):
            backup_dir = os.path.join(self.resource_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = os.path.join(
                backup_dir,
                f"{resource_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    original_data = json.load(f)
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(original_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                return False, f"备份失败: {str(e)}"
                
        # 保存新资源
        try:
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return False, f"保存失败: {str(e)}"
            
        return True, None
        
    def import_package(
        self,
        package_file: str,
        validate: bool = True
    ) -> Dict[str, Tuple[bool, Optional[str]]]:
        """导入资源包"""
        if not os.path.exists(package_file):
            raise ImportError(f"资源包不存在: {package_file}")
            
        try:
            with open(package_file, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
        except Exception as e:
            raise ImportError(f"解析资源包失败: {str(e)}")
            
        if 'metadata' not in package_data or 'resources' not in package_data:
            raise ImportError("无效的资源包格式")
            
        results = {}
        for resource_type, data in package_data['resources'].items():
            # 创建临时文件
            temp_file = os.path.join(
                self.resource_dir,
                f"temp_{resource_type}.json"
            )
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
                    
                # 导入资源
                success, error = self.import_resource(
                    temp_file,
                    resource_type,
                    validate
                )
                results[resource_type] = (success, error)
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        return results
        
    def _parse_json(self, file_path: str) -> Dict[str, Any]:
        """解析JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def _parse_yaml(self, file_path: str) -> Dict[str, Any]:
        """解析YAML文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _parse_xml(self, file_path: str) -> Dict[str, Any]:
        """解析XML文件"""
        def xml_to_dict(element: ET.Element) -> Any:
            result = {}
            for child in element:
                if len(child) > 0:
                    value = xml_to_dict(child)
                else:
                    value = child.text or ""
                    
                if child.tag in result:
                    if isinstance(result[child.tag], list):
                        result[child.tag].append(value)
                    else:
                        result[child.tag] = [result[child.tag], value]
                else:
                    result[child.tag] = value
            return result
            
        tree = ET.parse(file_path)
        root = tree.getroot()
        return xml_to_dict(root)
        
    def _parse_csv(self, file_path: str) -> Dict[str, Any]:
        """解析CSV文件"""
        result = {}
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.pop('key', None)
                if key:
                    result[key] = row
        return result
