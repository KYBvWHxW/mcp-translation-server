"""
基础组件接口
"""
from abc import ABC, abstractmethod

class BaseComponent(ABC):
    """基础组件接口"""
    
    @abstractmethod
    def is_ready(self) -> bool:
        """检查组件是否就绪"""
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
        """获取组件状态"""
        pass
