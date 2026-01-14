# -*- coding: utf-8 -*-
"""
日志记录工具
基础层 - 纯工具，无业务逻辑
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


class Logger:
    """日志记录器"""
    
    def __init__(self, name: str = 'classroom_detection', log_dir: str = './logs'):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if self.logger.handlers:
            return
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """记录严重错误日志"""
        self.logger.critical(message)


# 全局日志实例
default_logger = Logger()


def get_logger(name: str = None) -> Logger:
    """获取日志记录器实例"""
    if name:
        return Logger(name)
    return default_logger