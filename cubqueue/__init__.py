"""CubQueue - 轻量级任务监控系统

CubQueue是一个Python构建的、轻量级的任务监控系统，使用命令行工具与RESTFul API交互，
支持注册给定script，而后基于这些script提交任务，并管理它们产出的log、中间文件与结果文件。
"""

__version__ = "0.1.0"
__author__ = "CubQueue Team"
__email__ = "team@cubqueue.com"

from .client import CubQueueClient

__all__ = ["CubQueueClient"]
