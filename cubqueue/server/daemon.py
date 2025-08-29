"""CubQueue守护进程管理"""

import os
import sys
import signal
import subprocess
import psutil
from pathlib import Path
from typing import Optional

import uvicorn
from .app import create_app


class DaemonManager:
    """守护进程管理器"""

    def __init__(self, base_dir: str = None, host: str = "127.0.0.1", port: int = 8000):
        if base_dir is None:
            base_dir = Path.home() / ".cubqueue"
        else:
            base_dir = Path(base_dir)
            
        self.base_dir = base_dir
        self.host = host
        self.port = port
        self.pid_file = base_dir / "cubqueue.pid"
        self.log_file = base_dir / "cubqueue.log"

        # 确保目录存在
        base_dir.mkdir(parents=True, exist_ok=True)

    def start_server(self):
        """启动服务器（非守护进程模式）"""
        app = create_app(self.base_dir)
        uvicorn.run(app, host=self.host, port=self.port, log_level="info")

    def start_daemon(self):
        """启动守护进程"""
        if self.is_running():
            raise RuntimeError("CubQueue守护进程已在运行")

        # 创建守护进程
        pid = os.fork()
        if pid > 0:
            # 父进程退出
            sys.exit(0)

        # 子进程继续
        os.setsid()

        # 第二次fork
        pid = os.fork()
        if pid > 0:
            sys.exit(0)

        # 重定向标准输入输出
        sys.stdout.flush()
        sys.stderr.flush()

        with open("/dev/null", "r") as f:
            os.dup2(f.fileno(), sys.stdin.fileno())

        with open(self.log_file, "a") as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
            os.dup2(f.fileno(), sys.stderr.fileno())

        # 写入PID文件
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))

        # 设置信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # 启动服务器
        try:
            self.start_server()
        except Exception as e:
            print(f"启动服务器失败: {e}")
            self._cleanup()
            sys.exit(1)

    def stop_daemon(self):
        """停止守护进程"""
        if not self.is_running():
            raise RuntimeError("CubQueue守护进程未运行")

        pid = self.get_pid()
        if pid:
            try:
                # 发送TERM信号
                os.kill(pid, signal.SIGTERM)

                # 等待进程结束
                process = psutil.Process(pid)
                process.wait(timeout=10)
            except (ProcessLookupError, psutil.NoSuchProcess):
                # 进程已经不存在
                pass
            except psutil.TimeoutExpired:
                # 强制杀死进程
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

            self._cleanup()

    def is_running(self) -> bool:
        """检查守护进程是否运行"""
        pid = self.get_pid()
        if not pid:
            return False

        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            self._cleanup()
            return False

    def get_pid(self) -> Optional[int]:
        """获取守护进程PID"""
        if not self.pid_file.exists():
            return None

        try:
            with open(self.pid_file, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"收到信号 {signum}，正在关闭服务器...")
        self._cleanup()
        sys.exit(0)

    def _cleanup(self):
        """清理资源"""
        if self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except OSError:
                pass
