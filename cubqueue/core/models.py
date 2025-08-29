"""CubQueue数据库模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Script(Base):
    """脚本模型"""

    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    tasks = relationship("Task", back_populates="script")

    def __repr__(self):
        return f"<Script(id={self.id}, name='{self.name}')>"


class Task(Base):
    """任务模型"""

    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, running, completed, failed, cancelled
    args = Column(JSON, nullable=True)  # 任务参数
    message = Column(Text, nullable=True)  # 状态消息
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # 关联关系
    script = relationship("Script", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id='{self.id}', status='{self.status}')>"


class TaskFile(Base):
    """任务文件模型"""

    __tablename__ = "task_files"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_uuid = Column(String(36), nullable=False, unique=True)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TaskFile(id={self.id}, filename='{self.filename}')>"
