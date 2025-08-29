"""CubQueue配置管理"""

from pathlib import Path
from typing import Optional


class CubQueueConfig:
    """CubQueue配置类"""

    def __init__(self, base_dir: str = None, **kwargs):
        # 基础配置
        self.base_dir = base_dir or str(Path.home() / ".cubqueue")
        self.host = kwargs.get("host", "127.0.0.1")
        self.port = kwargs.get("port", 8000)

        # 数据库配置
        self.database_url = kwargs.get("database_url")

        # 日志配置
        self.log_level = kwargs.get("log_level", "INFO")
        self.log_file = kwargs.get("log_file")

        # 任务配置
        self.max_concurrent_tasks = kwargs.get("max_concurrent_tasks", 5)
        self.task_timeout = kwargs.get("task_timeout", 3600)  # 秒

        # 文件配置
        self.max_file_size = kwargs.get("max_file_size", 100 * 1024 * 1024)  # 100MB
        self.cleanup_days = kwargs.get("cleanup_days", 30)

        # 安全配置
        self.allowed_script_extensions = kwargs.get("allowed_script_extensions", [".py"])
        self.max_script_size = kwargs.get("max_script_size", 10 * 1024 * 1024)  # 10MB

        # 确保目录存在
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)


# 全局配置实例
_config: Optional[CubQueueConfig] = None


def get_config() -> CubQueueConfig:
    """获取配置实例"""
    global _config
    if _config is None:
        _config = CubQueueConfig()
    return _config


def init_config(base_dir: str = None, **kwargs) -> CubQueueConfig:
    """初始化配置

    Args:
        base_dir: 工作目录
        **kwargs: 其他配置参数

    Returns:
        配置实例
    """
    global _config
    _config = CubQueueConfig(base_dir=base_dir, **kwargs)
    return _config
