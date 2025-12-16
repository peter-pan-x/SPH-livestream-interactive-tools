"""日志系统模块"""
import os
import sys
import atexit
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


# 日志目录
LOG_DIR = Path(__file__).parent.parent / "logs"

# 全局logger实例
_logger_initialized = False
_file_handler = None


def setup_logger(name: str = None, verbose: bool = False) -> logging.Logger:
    """
    配置并返回logger
    
    Args:
        name: logger名称，None则返回root logger
        verbose: 是否显示DEBUG级别日志
    
    Returns:
        配置好的logger实例
    """
    global _logger_initialized, _file_handler
    
    # 只初始化一次
    if not _logger_initialized:
        _init_logging(verbose)
        _logger_initialized = True
    
    return logging.getLogger(name)


def _init_logging(verbose: bool = False):
    """初始化日志系统"""
    global _file_handler
    
    # 创建日志目录
    LOG_DIR.mkdir(exist_ok=True)
    
    # 日志级别
    console_level = logging.DEBUG if verbose else logging.INFO
    file_level = logging.DEBUG  # 文件始终记录DEBUG
    
    # 日志格式
    console_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    file_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 获取root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 清除已有handler
    root_logger.handlers.clear()
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # 文件handler - 按日期命名，最大5MB，保留10个
    log_filename = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    _file_handler = RotatingFileHandler(
        log_filename,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=10,
        encoding='utf-8'
    )
    _file_handler.setLevel(file_level)
    _file_handler.setFormatter(file_format)
    root_logger.addHandler(_file_handler)
    
    # 注册退出时的清理函数
    atexit.register(_cleanup_logging)
    
    # 记录启动信息
    root_logger.info("=" * 60)
    root_logger.info(f"程序启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    root_logger.info(f"日志文件: {log_filename}")
    root_logger.info("=" * 60)


def _cleanup_logging():
    """清理日志资源，确保日志正确写入"""
    global _file_handler
    
    logger = logging.getLogger()
    logger.info("=" * 60)
    logger.info(f"程序结束 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # 刷新并关闭文件handler
    if _file_handler:
        _file_handler.flush()
        _file_handler.close()


def log_exception(logger: logging.Logger, msg: str, exc: Exception):
    """
    记录异常信息（包含堆栈）
    
    Args:
        logger: logger实例
        msg: 错误消息
        exc: 异常对象
    """
    logger.error(msg)
    logger.exception(exc)


class LogContext:
    """日志上下文管理器，用于记录操作的开始和结束"""
    
    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"[开始] {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type:
            self.logger.error(f"[失败] {self.operation} (耗时 {duration:.2f}秒)")
            self.logger.exception(exc_val)
        else:
            self.logger.info(f"[完成] {self.operation} (耗时 {duration:.2f}秒)")
        return False  # 不抑制异常
