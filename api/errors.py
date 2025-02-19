"""
错误处理模块
"""
from typing import Dict, Any, Optional
from flask import jsonify

class TranslationError(Exception):
    """翻译服务基础异常类"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为JSON响应"""
        response = {
            'error': self.__class__.__name__,
            'message': self.message,
            'status_code': self.status_code
        }
        if self.details:
            response['details'] = self.details
        return response

class InvalidInputError(TranslationError):
    """输入参数错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)

class UnsupportedLanguageError(TranslationError):
    """不支持的语言"""
    def __init__(self, language: str):
        super().__init__(
            f"Unsupported language: {language}",
            status_code=400,
            details={'language': language}
        )

class TranslationModelError(TranslationError):
    """翻译模型错误"""
    def __init__(self, message: str, model_name: str, details: Optional[Dict[str, Any]] = None):
        error_details = {'model_name': model_name}
        if details:
            error_details.update(details)
        super().__init__(message, status_code=500, details=error_details)

class ResourceNotFoundError(TranslationError):
    """资源未找到"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            status_code=404,
            details={'resource_type': resource_type, 'resource_id': resource_id}
        )

class DatabaseError(TranslationError):
    """数据库错误"""
    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        error_details = {'operation': operation}
        if details:
            error_details.update(details)
        super().__init__(message, status_code=500, details=error_details)

def handle_translation_error(error: TranslationError):
    """处理翻译服务异常"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
