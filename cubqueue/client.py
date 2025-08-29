"""CubQueue Python客户端库"""

import requests
import json
import os
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import BytesIO


class CubQueueClient:
    """CubQueue客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """初始化客户端

        Args:
            base_url: CubQueue服务器地址
        """
        print("[init] >>>", base_url)
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def register(self, name: str, description: str, script_path: str) -> Dict[str, Any]:
        """注册脚本

        Args:
            name: 脚本名称
            description: 脚本描述
            script_path: 脚本文件路径

        Returns:
            注册结果

        Raises:
            FileNotFoundError: 脚本文件不存在
            requests.RequestException: 网络请求错误
        """
        print("[register] >>>", name, description, script_path)
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"脚本文件不存在: {script_path}")

        with open(script_path, "rb") as f:
            files = {"script": f}
            data = {"name": name, "desc": description}

            response = self.session.post(
                f"{self.base_url}/api/script", data=data, files=files
            )
            response.raise_for_status()
            return response.json()

    def namespace(self) -> List[Dict[str, Any]]:
        """获取已注册的脚本列表

        Returns:
            脚本列表
        """
        print("[namespace] >>>")
        response = self.session.get(f"{self.base_url}/api/script")
        response.raise_for_status()
        return response.json()

    def submit_task(
        self,
        script_name: str,
        arg_file_path: str,
        large_files: Optional[List[str]] = None,
    ) -> str:
        """提交任务

        Args:
            script_name: 脚本名称
            arg_file_path: 参数文件路径
            large_files: 大文件路径列表

        Returns:
            任务ID

        Raises:
            FileNotFoundError: 文件不存在
            requests.RequestException: 网络请求错误
        """
        print("[submit_task] >>>", script_name, arg_file_path, large_files)
        if not os.path.exists(arg_file_path):
            raise FileNotFoundError(f"参数文件不存在: {arg_file_path}")

        data = {"script_name": script_name}
        files = []

        # 添加参数文件
        files.append(("arg_file", open(arg_file_path, "rb")))

        # 添加大文件
        if large_files:
            for file_path in large_files:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"文件不存在: {file_path}")
                files.append(("files", open(file_path, "rb")))

        try:
            response = self.session.post(
                f"{self.base_url}/api/task", data=data, files=files
            )
            response.raise_for_status()
            return response.json()["id"]
        finally:
            # 关闭所有打开的文件
            for _, file_obj in files:
                if hasattr(file_obj, 'close'):
                    file_obj.close()

    def list_tasks(self) -> List[Dict[str, Any]]:
        """获取任务列表

        Returns:
            任务列表
        """
        print("[list_tasks] >>>")
        response = self.session.get(f"{self.base_url}/api/task")
        response.raise_for_status()
        return response.json()

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        print("[get_task_status] >>>", task_id)
        response = self.session.get(f"{self.base_url}/api/task/{task_id}")
        response.raise_for_status()
        return response.json()

    def get_task_log(self, task_id: str, lines: int = 100) -> str:
        """获取任务日志

        Args:
            task_id: 任务ID
            lines: 日志行数

        Returns:
            日志内容
        """
        print("[get_task_log] >>>", task_id, lines)
        response = self.session.get(
            f"{self.base_url}/api/task/{task_id}/log", params={"lines": lines}
        )
        response.raise_for_status()
        return response.json()["log"]

    def download_task_metadata(self, task_id: str, output_dir: str) -> str:
        """下载任务中间文件

        Args:
            task_id: 任务ID
            output_dir: 输出目录

        Returns:
            下载的文件路径
        """
        print("[download_task_metadata] >>>", task_id, output_dir)
        response = self.session.get(f"{self.base_url}/api/task/{task_id}/metadata")
        response.raise_for_status()

        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存并解压文件
        zip_path = output_path / f"{task_id}_metadata.zip"
        with open(zip_path, "wb") as f:
            f.write(response.content)

        # 解压文件
        extract_path = output_path / f"{task_id}_metadata"
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        # 删除zip文件
        zip_path.unlink()

        return str(extract_path)

    def download_task_result(self, task_id: str, output_dir: str) -> str:
        """下载任务结果文件

        Args:
            task_id: 任务ID
            output_dir: 输出目录

        Returns:
            下载的文件路径
        """
        print("[download_task_result] >>>", task_id, output_dir)
        response = self.session.get(f"{self.base_url}/api/task/{task_id}/result")
        response.raise_for_status()

        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存并解压文件
        zip_path = output_path / f"{task_id}_result.zip"
        with open(zip_path, "wb") as f:
            f.write(response.content)

        # 解压文件
        extract_path = output_path / f"{task_id}_result"
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        # 删除zip文件
        zip_path.unlink()

        return str(extract_path)

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务

        Args:
            task_id: 任务ID

        Returns:
            取消结果
        """
        print("[cancel_task] >>>", task_id)
        response = self.session.delete(f"{self.base_url}/api/task/{task_id}")
        response.raise_for_status()
        return response.json()

    def wait_for_task(
        self, task_id: str, timeout: int = 3600, check_interval: int = 5
    ) -> Dict[str, Any]:
        """等待任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）

        Returns:
            最终任务状态

        Raises:
            TimeoutError: 超时
        """
        print("[wait_for_task] >>>", task_id, timeout, check_interval)
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)

            if status["status"] in ["completed", "failed", "cancelled"]:
                return status

            time.sleep(check_interval)

        raise TimeoutError(f"任务 {task_id} 在 {timeout} 秒内未完成")

    def health_check(self) -> bool:
        """健康检查

        Returns:
            服务器是否健康
        """
        print("[health_check] >>>")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
