"""CubQueue数据库连接和配置"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
from typing import Generator

from .models import Base


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, base_dir: str = None):
        """初始化数据库管理器

        Args:
            base_dir: 工作目录，如果为None则使用默认目录
        """
        if base_dir is None:
            base_dir = Path.home() / ".cubqueue"
        else:
            base_dir = Path(base_dir)

        base_dir.mkdir(parents=True, exist_ok=True)

        # 数据库文件路径
        self.db_path = base_dir / "cubqueue.db"

        # 创建数据库引擎
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False, "timeout": 20},
            echo=False,  # 设置为True可以看到SQL语句
        )

        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # 创建表
        self.create_tables()

    def create_tables(self):
        """创建数据库表"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()


# 全局数据库管理器实例
_db_manager = None


def init_database(base_dir: str = None) -> DatabaseManager:
    """初始化数据库

    Args:
        base_dir: 工作目录

    Returns:
        数据库管理器实例
    """
    global _db_manager
    _db_manager = DatabaseManager(base_dir)
    return _db_manager


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（用于FastAPI依赖注入）"""
    db_manager = get_db_manager()
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


# 为了兼容性，导出SessionLocal
SessionLocal = None


def get_session_local():
    """获取SessionLocal类"""
    global SessionLocal
    if SessionLocal is None:
        db_manager = get_db_manager()
        SessionLocal = db_manager.SessionLocal
    return SessionLocal
