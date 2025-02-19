class ManchuTranslationError(Exception):
    """满语翻译系统基础异常类"""
    def __init__(self, message, error_code=None, details=None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class MorphologyError(ManchuTranslationError):
    """形态分析相关错误"""
    pass

class GrammarError(ManchuTranslationError):
    """语法分析相关错误"""
    pass

class DictionaryError(ManchuTranslationError):
    """词典查询相关错误"""
    pass

class ModelError(ManchuTranslationError):
    """模型加载和推理相关错误"""
    pass

class ValidationError(ManchuTranslationError):
    """输入验证相关错误"""
    pass

def format_error_response(error):
    """格式化错误响应"""
    response = {
        'success': False,
        'error': {
            'type': error.__class__.__name__,
            'message': str(error),
            'code': getattr(error, 'error_code', None)
        }
    }
    
    if hasattr(error, 'details') and error.details:
        response['error']['details'] = error.details
        
    return response
