import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class CacheConfig:
    enabled: bool = True
    max_size: int = 1000
    ttl: int = 3600  # 缓存生存时间（秒）

@dataclass
class ModelConfig:
    model_name: str = 'google/mt5-small'
    device: str = 'cuda' if os.environ.get('USE_GPU', '0') == '1' else 'cpu'
    batch_size: int = 32
    max_length: int = 128
    beam_size: int = 4

@dataclass
class ServerConfig:
    host: str = 'localhost'
    port: int = 8080
    debug: bool = False
    workers: int = 4

class Config:
    def __init__(self):
        self.cache = CacheConfig()
        self.model = ModelConfig()
        self.server = ServerConfig()
        
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """从字典创建配置实例"""
        instance = cls()
        
        if 'cache' in config_dict:
            instance.cache = CacheConfig(**config_dict['cache'])
            
        if 'model' in config_dict:
            instance.model = ModelConfig(**config_dict['model'])
            
        if 'server' in config_dict:
            instance.server = ServerConfig(**config_dict['server'])
            
        return instance
        
    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'cache': {
                'enabled': self.cache.enabled,
                'max_size': self.cache.max_size,
                'ttl': self.cache.ttl
            },
            'model': {
                'model_name': self.model.model_name,
                'device': self.model.device,
                'batch_size': self.model.batch_size,
                'max_length': self.model.max_length,
                'beam_size': self.model.beam_size
            },
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'debug': self.server.debug,
                'workers': self.server.workers
            }
        }
