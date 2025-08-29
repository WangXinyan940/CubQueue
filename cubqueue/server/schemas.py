"""CubQueue API响应模式定义"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ScriptResponse(BaseModel):
    """脚本响应模式"""

    id: int
    name: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """任务响应模式"""

    id: str
    script_name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    """任务状态响应模式"""

    id: str
    status: str
    message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """错误响应模式"""

    detail: str
