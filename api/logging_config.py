"""
日志配置模块
"""
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Dict, Any

def setup_logging(app_name: str = 'mcp-translation-server') -> logging.Logger:
    """配置日志系统"""
    # 创建日志目录
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建logger
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 文件处理器 - 所有日志
    all_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'all.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    all_handler.setFormatter(formatter)
    all_handler.setLevel(logging.INFO)

    # 文件处理器 - 错误日志
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'error.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # 添加处理器
    logger.addHandler(all_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger

def log_api_call(logger: logging.Logger, endpoint: str, request_data: Dict[str, Any], 
                 response_data: Dict[str, Any], duration: float):
    """记录API调用"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'endpoint': endpoint,
        'request': request_data,
        'response': response_data,
        'duration_ms': duration * 1000
    }
    logger.info(f"API Call: {log_data}")

def log_translation(logger: logging.Logger, source_text: str, target_text: str, 
                   source_lang: str, target_lang: str, duration: float):
    """记录翻译操作"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'source_text': source_text,
        'target_text': target_text,
        'source_lang': source_lang,
        'target_lang': target_lang,
        'duration_ms': duration * 1000
    }
    logger.info(f"Translation: {log_data}")

def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any]):
    """记录错误"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context
    }
    logger.error(f"Error: {log_data}", exc_info=True)
