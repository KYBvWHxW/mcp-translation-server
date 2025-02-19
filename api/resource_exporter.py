from typing import Dict, List, Any, Optional
import json
import csv
import yaml
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from pathlib import Path

class ResourceExporter:
    """资源导出器"""
    
    def __init__(self, resource_dir: str = "resources"):
        self.resource_dir = resource_dir
        
    def export_json(
        self,
        data: Dict[str, Any],
        output_file: str,
        pretty: bool = True
    ) -> str:
        """导出为JSON格式"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False)
        return output_file
        
    def export_yaml(self, data: Dict[str, Any], output_file: str) -> str:
        """导出为YAML格式"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)
        return output_file
        
    def export_xml(self, data: Dict[str, Any], output_file: str) -> str:
        """导出为XML格式"""
        def dict_to_xml(parent: ET.Element, data: Dict[str, Any]):
            for key, value in data.items():
                child = ET.SubElement(parent, str(key))
                if isinstance(value, dict):
                    dict_to_xml(child, value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            dict_to_xml(child, item)
                        else:
                            ET.SubElement(child, 'item').text = str(item)
                else:
                    child.text = str(value)
                    
        root = ET.Element('resource')
        dict_to_xml(root, data)
        tree = ET.ElementTree(root)
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        return output_file
        
    def export_csv(
        self,
        data: Dict[str, Any],
        output_file: str,
        fields: Optional[List[str]] = None
    ) -> str:
        """导出为CSV格式（适用于词典和术语库）"""
        if not fields:
            # 从数据中推断字段
            sample = next(iter(data.values()))
            fields = list(sample.keys())
            
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['key'] + fields)
            writer.writeheader()
            for key, value in data.items():
                row = {'key': key}
                row.update(value)
                writer.writerow(row)
        return output_file
        
    def export_resource(
        self,
        resource_type: str,
        version: str,
        format: str = 'json'
    ) -> str:
        """导出指定类型的资源"""
        resource_file = os.path.join(self.resource_dir, f"{resource_type}.json")
        if not os.path.exists(resource_file):
            raise FileNotFoundError(f"资源文件 {resource_file} 不存在")
            
        with open(resource_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 添加元数据
        metadata = {
            'version': version,
            'export_time': datetime.now().isoformat(),
            'resource_type': resource_type
        }
        
        export_data = {
            'metadata': metadata,
            'data': data
        }
        
        # 创建导出目录
        export_dir = os.path.join(self.resource_dir, 'exports', resource_type)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{resource_type}_{version}_{timestamp}"
        
        if format == 'json':
            output_file = os.path.join(export_dir, f"{filename}.json")
            return self.export_json(export_data, output_file)
        elif format == 'yaml':
            output_file = os.path.join(export_dir, f"{filename}.yaml")
            return self.export_yaml(export_data, output_file)
        elif format == 'xml':
            output_file = os.path.join(export_dir, f"{filename}.xml")
            return self.export_xml(export_data, output_file)
        elif format == 'csv':
            output_file = os.path.join(export_dir, f"{filename}.csv")
            return self.export_csv(data, output_file)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
            
    def export_all_resources(
        self,
        version: str,
        format: str = 'json'
    ) -> Dict[str, str]:
        """导出所有资源"""
        resources = ['grammar', 'morphology', 'lexicon', 'terminology']
        results = {}
        
        for resource in resources:
            try:
                output_file = self.export_resource(resource, version, format)
                results[resource] = output_file
            except FileNotFoundError:
                continue
                
        return results
        
    def create_resource_package(
        self,
        version: str,
        include_resources: Optional[List[str]] = None
    ) -> str:
        """创建资源包"""
        if include_resources is None:
            include_resources = ['grammar', 'morphology', 'lexicon', 'terminology']
            
        # 导出所有资源为JSON
        exports = {}
        for resource in include_resources:
            try:
                with open(os.path.join(self.resource_dir, f"{resource}.json"), 'r', encoding='utf-8') as f:
                    exports[resource] = json.load(f)
            except FileNotFoundError:
                continue
                
        # 创建包元数据
        package_data = {
            'metadata': {
                'version': version,
                'created_at': datetime.now().isoformat(),
                'resources': list(exports.keys())
            },
            'resources': exports
        }
        
        # 保存资源包
        package_dir = os.path.join(self.resource_dir, 'packages')
        os.makedirs(package_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        package_file = os.path.join(
            package_dir,
            f"resource_package_{version}_{timestamp}.json"
        )
        
        with open(package_file, 'w', encoding='utf-8') as f:
            json.dump(package_data, f, ensure_ascii=False, indent=2)
            
        return package_file
