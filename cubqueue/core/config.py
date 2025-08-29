"""CubQueue配置管理"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class CubQueueConfig(BaseSettings):
    """CubQueue配置类"""

    # 基础配置
    base_dir: str = Field(default_factory=lambda: str(Path.home() / ".cubqueue"))
    host: str = "127.0.0.1"
    port: int = 8000

    # 数据库配置
    database_url: Optional[str] = None

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # 任务配置
    max_concurrent_tasks: int = 5
    task_timeout: int = 3600  # 秒

    # 文件配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    cleanup_days: int = 30

    # 安全配置
    allowed_script_extensions: list = [".py"]
    max_script_size: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_prefix = "CUBQUEUE_"
        env_file = ".env"
        case_sensitive = False


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

    config_kwargs = {}
    if base_dir:
        config_kwargs["base_dir"] = base_dir
    config_kwargs.update(kwargs)

    _config = CubQueueConfig(**config_kwargs)

    # 确保目录存在
    Path(_config.base_dir).mkdir(parents=True, exist_ok=True)

    return _config


def load_config_from_file(config_file: str) -> CubQueueConfig:
    """从文件加载配置

    Args:
        config_file: 配置文件路径

    Returns:
        配置实例
    """
    global _config

    # 设置环境变量指向配置文件
    os.environ["CUBQUEUE_CONFIG_FILE"] = config_file

    _config = CubQueueConfig(_env_file=config_file)
    return _config
