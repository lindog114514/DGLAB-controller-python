"""自定义异常"""

class PossumError(Exception):
    """库基础异常"""
    pass

class ConnectionError(PossumError):
    """连接异常"""
    pass

class CommandError(PossumError):
    """指令发送异常"""
    pass