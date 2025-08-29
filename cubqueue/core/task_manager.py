"""CubQueue任务管理器"""

import os
import json
import subprocess
import threading
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from .models import Task, Script
from .database import get_db_manager
from .file_manager import FileManager


class TaskManager:
    """任务管理器"""

    def __init__(self, base_dir: str = None):
        """初始化任务管理器

        Args:
            base_dir: 工作目录
        """
        if base_dir is None:
            base_dir = Path.home() / ".cubqueue"
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir
        self.tasks_dir = base_dir / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        self.file_manager = FileManager(base_dir)
        self.db_manager = get_db_manager()

        # 运行中的任务进程
        self.running_processes: Dict[str, subprocess.Popen] = {}

        # 启动时恢复运行中的任务状态
        self._recover_running_tasks()

    def create_task(
        self,
        task_id: str,
        script_id: int,
        script_name: str,
        args: Dict[str, Any],
        file_mappings: Dict[str, str],
    ) -> Dict[str, Any]:
        """创建任务

        Args:
            task_id: 任务ID
            script_id: 脚本ID
            script_name: 脚本名称
            args: 任务参数
            file_mappings: 文件映射关系

        Returns:
            任务信息
        """
        # 创建任务目录
        task_dir = self.tasks_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (task_dir / "files").mkdir(exist_ok=True)
        (task_dir / "metadata").mkdir(exist_ok=True)
        (task_dir / "output").mkdir(exist_ok=True)

        # 获取脚本信息
        db = self.db_manager.get_session()
        try:
            script = db.query(Script).filter(Script.id == script_id).first()
            if not script:
                raise ValueError(f"脚本不存在: {script_id}")

            # 复制脚本文件到任务目录
            script_src = Path(script.path)
            script_dst = task_dir / f"{script_name}.py"
            shutil.copy2(script_src, script_dst)

            # 处理参数文件中的文件占位符
            processed_args = self._process_file_placeholders(
                args, file_mappings, task_dir
            )

            # 保存参数文件
            arg_file_path = task_dir / "arg_file.json"
            with open(arg_file_path, "w", encoding="utf-8") as f:
                json.dump(processed_args, f, indent=2, ensure_ascii=False)

            return {
                "id": task_id,
                "script_name": script_name,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()

    def start_task(self, task_id: str):
        """启动任务

        Args:
            task_id: 任务ID
        """
        task_dir = self.tasks_dir / task_id
        if not task_dir.exists():
            raise FileNotFoundError(f"任务目录不存在: {task_dir}")

        # 更新任务状态为运行中
        self._update_task_status(task_id, "running", started_at=datetime.utcnow())

        # 在新线程中运行任务
        thread = threading.Thread(target=self._run_task, args=(task_id,))
        thread.daemon = True
        thread.start()

    def cancel_task(self, task_id: str):
        """取消任务

        Args:
            task_id: 任务ID
        """
        # 如果任务正在运行，终止进程
        if task_id in self.running_processes:
            process = self.running_processes[task_id]
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            finally:
                del self.running_processes[task_id]

        # 更新任务状态
        self._update_task_status(task_id, "cancelled", finished_at=datetime.utcnow())

    def get_task_log(self, task_id: str, lines: int = 100) -> str:
        """获取任务日志

        Args:
            task_id: 任务ID
            lines: 日志行数

        Returns:
            日志内容
        """
        log_file = self.tasks_dir / task_id / "log.txt"
        if not log_file.exists():
            return ""

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                if lines > 0:
                    return "".join(all_lines[-lines:])
                else:
                    return "".join(all_lines)
        except Exception as e:
            return f"读取日志失败: {e}"

    def create_metadata_archive(self, task_id: str) -> str:
        """创建中间文件压缩包

        Args:
            task_id: 任务ID

        Returns:
            压缩包路径
        """
        task_dir = self.tasks_dir / task_id
        metadata_dir = task_dir / "metadata"

        if not metadata_dir.exists():
            raise FileNotFoundError(f"中间文件目录不存在: {metadata_dir}")

        zip_path = task_dir / f"{task_id}_metadata.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in metadata_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(metadata_dir)
                    zipf.write(file_path, arcname)

        return str(zip_path)

    def create_result_archive(self, task_id: str) -> str:
        """创建结果文件压缩包

        Args:
            task_id: 任务ID

        Returns:
            压缩包路径
        """
        task_dir = self.tasks_dir / task_id
        output_dir = task_dir / "output"

        if not output_dir.exists():
            raise FileNotFoundError(f"结果文件目录不存在: {output_dir}")

        zip_path = task_dir / f"{task_id}_result.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_dir)
                    zipf.write(file_path, arcname)

        return str(zip_path)

    def _run_task(self, task_id: str):
        """运行任务（在单独线程中执行）

        Args:
            task_id: 任务ID
        """
        task_dir = self.tasks_dir / task_id
        log_file = task_dir / "log.txt"

        try:
            # 查找Python脚本文件
            script_files = list(task_dir.glob("*.py"))
            if not script_files:
                raise FileNotFoundError("未找到Python脚本文件")

            script_file = script_files[0]

            # 准备环境变量
            env = os.environ.copy()
            env["CUBQUEUE_TASK_ID"] = task_id
            env["CUBQUEUE_TASK_DIR"] = str(task_dir)
            env["CUBQUEUE_FILES_DIR"] = str(task_dir / "files")

            # 启动进程
            with open(log_file, "w", encoding="utf-8") as log_f:
                process = subprocess.Popen(
                    ["python", script_file.name],
                    cwd=str(task_dir),
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    env=env,
                    text=True,
                )

                # 记录运行中的进程
                self.running_processes[task_id] = process

                # 等待进程完成
                return_code = process.wait()

                # 移除进程记录
                if task_id in self.running_processes:
                    del self.running_processes[task_id]

                # 更新任务状态
                if return_code == 0:
                    self._update_task_status(
                        task_id,
                        "completed",
                        message="任务成功完成",
                        finished_at=datetime.utcnow(),
                    )
                else:
                    self._update_task_status(
                        task_id,
                        "failed",
                        message=f"任务失败，退出码: {return_code}",
                        finished_at=datetime.utcnow(),
                    )

        except Exception as e:
            # 记录错误日志
            try:
                with open(log_file, "a", encoding="utf-8") as log_f:
                    log_f.write(f"\n任务执行错误: {e}\n")
            except:
                pass

            # 更新任务状态
            self._update_task_status(
                task_id,
                "failed",
                message=f"任务执行错误: {e}",
                finished_at=datetime.utcnow(),
            )

            # 清理进程记录
            if task_id in self.running_processes:
                del self.running_processes[task_id]

    def _process_file_placeholders(
        self, args: Dict[str, Any], file_mappings: Dict[str, str], task_dir: Path
    ) -> Dict[str, Any]:
        """处理参数中的文件占位符

        Args:
            args: 原始参数
            file_mappings: 文件映射关系
            task_dir: 任务目录

        Returns:
            处理后的参数
        """

        def replace_placeholders(obj):
            if isinstance(obj, str):
                for placeholder, file_uuid in file_mappings.items():
                    if placeholder in obj:
                        # 将占位符替换为实际文件路径
                        file_path = Path("files") / file_uuid
                        obj = obj.replace(placeholder, str(file_path))
                return obj
            elif isinstance(obj, list):
                return [replace_placeholders(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: replace_placeholders(value) for key, value in obj.items()}
            else:
                return obj

        return replace_placeholders(args)

    def _update_task_status(
        self,
        task_id: str,
        status: str,
        message: str = None,
        started_at: datetime = None,
        finished_at: datetime = None,
    ):
        """更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            message: 状态消息
            started_at: 开始时间
            finished_at: 完成时间
        """
        db = self.db_manager.get_session()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = status
                if message:
                    task.message = message
                if started_at:
                    task.started_at = started_at
                if finished_at:
                    task.finished_at = finished_at
                db.commit()
        finally:
            db.close()

    def _recover_running_tasks(self):
        """恢复运行中的任务状态"""
        db = self.db_manager.get_session()
        try:
            # 查找状态为running的任务
            running_tasks = db.query(Task).filter(Task.status == "running").all()

            for task in running_tasks:
                # 将状态重置为failed，因为服务器重启后无法恢复进程
                task.status = "failed"
                task.message = "服务器重启，任务被中断"
                task.finished_at = datetime.utcnow()

            db.commit()
        finally:
            db.close()
