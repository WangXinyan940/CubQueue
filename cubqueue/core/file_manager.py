"""CubQueue文件管理器"""

import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, Optional


class FileManager:
    """文件管理器"""

    def __init__(self, base_dir: str = None):
        """初始化文件管理器

        Args:
            base_dir: 工作目录
        """
        if base_dir is None:
            base_dir = Path.home() / ".cubqueue"
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir
        self.scripts_dir = base_dir / "scripts"
        self.tasks_dir = base_dir / "tasks"

        # 创建目录
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def save_script(self, name: str, content: bytes, description: str) -> str:
        """保存脚本文件

        Args:
            name: 脚本名称
            content: 脚本内容
            description: 脚本描述

        Returns:
            脚本文件路径
        """
        # 保存脚本文件
        script_path = self.scripts_dir / f"{name}.py"
        with open(script_path, "wb") as f:
            f.write(content)

        # 保存描述文件
        desc_path = self.scripts_dir / f"{name}.txt"
        with open(desc_path, "w", encoding="utf-8") as f:
            f.write(description)

        return str(script_path)

    def get_script_path(self, name: str) -> str:
        """获取脚本文件路径

        Args:
            name: 脚本名称

        Returns:
            脚本文件路径
        """
        return str(self.scripts_dir / f"{name}.py")

    def get_script_description(self, name: str) -> str:
        """获取脚本描述

        Args:
            name: 脚本名称

        Returns:
            脚本描述
        """
        desc_path = self.scripts_dir / f"{name}.txt"
        if desc_path.exists():
            with open(desc_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def delete_script(self, name: str):
        """删除脚本文件

        Args:
            name: 脚本名称
        """
        script_path = self.scripts_dir / f"{name}.py"
        desc_path = self.scripts_dir / f"{name}.txt"

        if script_path.exists():
            script_path.unlink()

        if desc_path.exists():
            desc_path.unlink()

    def save_task_file(self, task_id: str, filename: str, content: bytes) -> str:
        """保存任务文件

        Args:
            task_id: 任务ID
            filename: 文件名
            content: 文件内容

        Returns:
            文件UUID
        """
        # 生成文件UUID
        file_uuid = str(uuid.uuid4())

        # 创建任务文件目录
        task_files_dir = self.tasks_dir / task_id / "files"
        task_files_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_path = task_files_dir / file_uuid
        with open(file_path, "wb") as f:
            f.write(content)

        # 保存文件名映射
        mapping_path = task_files_dir / f"{file_uuid}.name"
        with open(mapping_path, "w", encoding="utf-8") as f:
            f.write(filename)

        return file_uuid

    def get_task_file_path(self, task_id: str, file_uuid: str) -> str:
        """获取任务文件路径

        Args:
            task_id: 任务ID
            file_uuid: 文件UUID

        Returns:
            文件路径
        """
        return str(self.tasks_dir / task_id / "files" / file_uuid)

    def get_task_file_name(self, task_id: str, file_uuid: str) -> str:
        """获取任务文件原始名称

        Args:
            task_id: 任务ID
            file_uuid: 文件UUID

        Returns:
            原始文件名
        """
        mapping_path = self.tasks_dir / task_id / "files" / f"{file_uuid}.name"
        if mapping_path.exists():
            with open(mapping_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return file_uuid

    def create_task_directory(self, task_id: str) -> str:
        """创建任务目录

        Args:
            task_id: 任务ID

        Returns:
            任务目录路径
        """
        task_dir = self.tasks_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (task_dir / "files").mkdir(exist_ok=True)
        (task_dir / "metadata").mkdir(exist_ok=True)
        (task_dir / "output").mkdir(exist_ok=True)

        return str(task_dir)

    def get_task_directory(self, task_id: str) -> str:
        """获取任务目录路径

        Args:
            task_id: 任务ID

        Returns:
            任务目录路径
        """
        return str(self.tasks_dir / task_id)

    def delete_task_directory(self, task_id: str):
        """删除任务目录

        Args:
            task_id: 任务ID
        """
        task_dir = self.tasks_dir / task_id
        if task_dir.exists():
            shutil.rmtree(task_dir)

    def get_task_log_path(self, task_id: str) -> str:
        """获取任务日志文件路径

        Args:
            task_id: 任务ID

        Returns:
            日志文件路径
        """
        return str(self.tasks_dir / task_id / "log.txt")

    def get_task_metadata_dir(self, task_id: str) -> str:
        """获取任务中间文件目录路径

        Args:
            task_id: 任务ID

        Returns:
            中间文件目录路径
        """
        return str(self.tasks_dir / task_id / "metadata")

    def get_task_output_dir(self, task_id: str) -> str:
        """获取任务输出目录路径

        Args:
            task_id: 任务ID

        Returns:
            输出目录路径
        """
        return str(self.tasks_dir / task_id / "output")

    def cleanup_old_files(self, days: int = 30):
        """清理旧文件

        Args:
            days: 保留天数
        """
        import time
        from datetime import datetime, timedelta

        cutoff_time = time.time() - (days * 24 * 60 * 60)

        # 清理旧的任务目录
        for task_dir in self.tasks_dir.iterdir():
            if task_dir.is_dir():
                try:
                    # 检查目录修改时间
                    if task_dir.stat().st_mtime < cutoff_time:
                        shutil.rmtree(task_dir)
                        print(f"已清理旧任务目录: {task_dir.name}")
                except Exception as e:
                    print(f"清理任务目录失败 {task_dir.name}: {e}")

    def get_disk_usage(self) -> Dict[str, Any]:
        """获取磁盘使用情况

        Returns:
            磁盘使用信息
        """

        def get_dir_size(path: Path) -> int:
            """获取目录大小"""
            total = 0
            try:
                for entry in path.rglob("*"):
                    if entry.is_file():
                        total += entry.stat().st_size
            except Exception:
                pass
            return total

        scripts_size = get_dir_size(self.scripts_dir)
        tasks_size = get_dir_size(self.tasks_dir)
        total_size = scripts_size + tasks_size

        return {
            "scripts_size": scripts_size,
            "tasks_size": tasks_size,
            "total_size": total_size,
            "scripts_count": len(list(self.scripts_dir.glob("*.py"))),
            "tasks_count": len(list(self.tasks_dir.iterdir())),
        }
