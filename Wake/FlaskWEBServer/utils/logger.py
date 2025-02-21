import logging
from datetime import datetime
import os
from config.settings import DIRS

class OllamaResponseFormatter(logging.Formatter):
    """Ollama响应的特殊格式化器"""
    def __init__(self):
        super().__init__()
        self.accumulated_message = ""
        self.in_think_block = False
        
    def format(self, record):
        # 标准日志格式
        if not hasattr(record, 'is_ollama_response'):
            return f"{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')} - {record.levelname} - {record.msg}"
            
        # 提取响应内容
        content = record.msg
        
        # 处理完成标记
        if getattr(record, 'is_response_complete', False):
            # 重置状态
            result = f"\n--- Ollama响应完成 ---\n"
            self.accumulated_message = ""
            self.in_think_block = False
            return result
            
        # 忽略空内容
        if not content:
            return ""

        # 处理思考块
        if "<think>" in content:
            self.in_think_block = True
            return "<think>"
        elif "</think>" in content:
            self.in_think_block = False
            return "</think>\n"
        
        # 正常响应内容
        if not self.in_think_block:
            self.accumulated_message += content
            return f"[{self.accumulated_message}]"
            
        return ""

class SingletonLogger:
    _instance = None
    _initialized = False

    @classmethod
    def get_logger(cls):
        if not cls._instance:
            cls._instance = cls._setup_logging()
            # 设置Flask的日志处理
            cls._setup_flask_logging()
        return cls._instance

    @staticmethod
    def _setup_logging():
        """配置并返回日志记录器"""
        # 获取根日志记录器
        logger = logging.getLogger('FlaskWebServer')
        
        # 如果已经有处理器，说明已经初始化过，直接返回
        if logger.handlers:
            return logger
        
        # 防止日志传递到父记录器
        logger.propagate = False
        
        # 配置标准日志格式
        standard_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 配置 Ollama 响应格式
        ollama_formatter = OllamaResponseFormatter()
        
        # 控制台处理器 - 标准日志
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(standard_formatter)
        
        # 控制台处理器 - Ollama响应
        ollama_console_handler = logging.StreamHandler()
        ollama_console_handler.setFormatter(ollama_formatter)
        ollama_console_handler.addFilter(lambda record: hasattr(record, 'is_ollama_response'))
        
        # 配置日志记录器
        logger.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        logger.addHandler(ollama_console_handler)
        
        return logger

    @staticmethod
    def _setup_flask_logging():
        """配置Flask的日志处理"""
        # 获取Werkzeug的日志记录器
        werkzeug_logger = logging.getLogger('werkzeug')
        
        # 创建自定义的过滤器
        class EndpointFilter(logging.Filter):
            def filter(self, record):
                message = record.msg
                # 保留服务地址信息，但过滤掉其他开发服务器消息
                if "Running on" in message:
                    return True
                return not any([
                    "Debug mode" in message,
                    "Debugger is active" in message,
                    "Debugger PIN" in message,
                    "Press CTRL+C to quit" in message,
                    "Restarting with" in message,
                    " * Serving Flask app" in message,
                    " * Environment:" in message,
                    "development server" in message
                ])
        
        # 应用过滤器
        werkzeug_logger.addFilter(EndpointFilter())
        werkzeug_logger.setLevel(logging.INFO)

# 创建全局logger实例
logger = SingletonLogger.get_logger() 