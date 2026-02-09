"""
logger.py - 日志模块
功能：
1. 提供基本的日志记录接口
2. 支持信息、警告、错误、调试四种日志级别
3. 简单的控制台输出
"""
class Logger:
    """日志类"""
    def __init__(self, name):
        """
        初始化日志记录器
        Args:
            name: 日志记录器名称（通常是模块名）
        """
        self.name = name


    def info(self, message):
        """
        信息日志
        Args:
            message: 日志消息
        """
        print(f"[INFO] {self.name}: {message}")


    def warning(self, message):
        """
        警告日志
        Args:
            message: 日志消息
        """
        print(f"[WARNING] {self.name}: {message}")


    def error(self, message):
        """
        错误日志
        Args:
            message: 日志消息
        """
        print(f"[ERROR] {self.name}: {message}")


    def debug(self, message):
        """
        调试日志
        Args:
            message: 日志消息
        """
        print(f"[DEBUG] {self.name}: {message}")