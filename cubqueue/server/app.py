"""CubQueue FastAPI应用"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
import os
import json
import uuid
from pathlib import Path

from ..core.models import Script, Task
from ..core.task_manager import TaskManager
from ..core.file_manager import FileManager
from ..core.database import get_db, SessionLocal, init_database
from .schemas import ScriptResponse, TaskResponse, TaskStatusResponse


def create_app(base_dir: str = None) -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title="CubQueue API",
        description="轻量级任务监控系统 RESTful API",
        version="0.1.0",
    )

    # 初始化数据库
    init_database(base_dir)
    
    # 初始化组件
    task_manager = TaskManager(base_dir)
    file_manager = FileManager(base_dir)

    @app.post("/api/script", response_model=ScriptResponse)
    async def register_script(
        name: str = Form(...),
        desc: str = Form(...),
        script: UploadFile = File(...),
        db: SessionLocal = Depends(get_db),
    ):
        """注册脚本"""
        try:
            # 验证脚本名称
            if not name.replace("_", "").replace("-", "").isalnum():
                raise HTTPException(
                    status_code=400, detail="脚本名称只能包含字母、数字、下划线和连字符"
                )

            # 检查脚本是否已存在
            existing_script = db.query(Script).filter(Script.name == name).first()
            if existing_script:
                raise HTTPException(status_code=400, detail="脚本名称已存在")

            # 保存脚本文件
            script_content = await script.read()
            script_path = file_manager.save_script(name, script_content, desc)

            # 创建数据库记录
            db_script = Script(name=name, description=desc, path=script_path)
            db.add(db_script)
            db.commit()
            db.refresh(db_script)

            return ScriptResponse(
                id=db_script.id,
                name=db_script.name,
                description=db_script.description,
                created_at=db_script.created_at,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/script", response_model=List[ScriptResponse])
    async def list_scripts(db: SessionLocal = Depends(get_db)):
        """获取脚本列表"""
        scripts = db.query(Script).all()
        return [
            ScriptResponse(
                id=script.id,
                name=script.name,
                description=script.description,
                created_at=script.created_at,
            )
            for script in scripts
        ]

    @app.post("/api/task", response_model=TaskResponse)
    async def submit_task(
        script_name: str = Form(...),
        arg_file: UploadFile = File(...),
        files: List[UploadFile] = File(default=[]),
        description: Optional[str] = Form(None),
        db: SessionLocal = Depends(get_db),
    ):
        """提交任务"""
        try:
            print(f"[DEBUG] 开始处理任务提交: script_name={script_name}")
            print(f"[DEBUG] arg_file: {arg_file.filename if arg_file else None}")
            print(f"[DEBUG] files count: {len(files)}")
            # 验证脚本是否存在
            script = db.query(Script).filter(Script.name == script_name).first()
            if not script:
                raise HTTPException(status_code=404, detail="脚本不存在")

            # 生成任务ID
            task_id = str(uuid.uuid4())

            # 读取参数文件
            arg_content = await arg_file.read()
            try:
                args = json.loads(arg_content)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="参数文件格式错误")

            # 处理上传的文件
            file_mappings = {}
            print(f"[DEBUG] 收到 {len(files)} 个文件")
            for i, file in enumerate(files, 1):
                print(f"[DEBUG] 处理文件 {i}: {file.filename}")
                file_content = await file.read()
                print(f"[DEBUG] 文件内容长度: {len(file_content)}")
                file_uuid = file_manager.save_task_file(
                    task_id, file.filename, file_content
                )
                print(f"[DEBUG] 文件保存为: {file_uuid}")
                file_mappings[f"<file{i}>"] = file_uuid
            print(f"[DEBUG] 文件映射: {file_mappings}")

            # 创建任务
            task = task_manager.create_task(
                task_id=task_id,
                script_id=script.id,
                script_name=script_name,
                args=args,
                file_mappings=file_mappings,
            )

            # 创建数据库记录
            db_task = Task(
                id=task_id, script_id=script.id, status="pending", args=json.dumps(args), description=description
            )
            db.add(db_task)
            db.commit()

            # 启动任务
            task_manager.start_task(task_id)

            return TaskResponse(
                id=task_id,
                script_name=script_name,
                status="pending",
                created_at=db_task.created_at,
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] 任务提交失败: {str(e)}")
            import traceback
            print(f"[ERROR] 详细错误: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/task", response_model=List[TaskResponse])
    async def list_tasks(db: SessionLocal = Depends(get_db)):
        """获取任务列表"""
        tasks = db.query(Task).join(Script).all()
        return [
            TaskResponse(
                id=task.id,
                script_name=task.script.name,
                status=task.status,
                description=task.description,
                created_at=task.created_at,
            )
            for task in tasks
        ]

    @app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
    async def get_task_status(task_id: str, db: SessionLocal = Depends(get_db)):
        """获取任务状态"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        return TaskStatusResponse(
            id=task.id,
            status=task.status,
            message=task.message,
            created_at=task.created_at,
            started_at=task.started_at,
            finished_at=task.finished_at,
        )

    @app.get("/api/task/{task_id}/log")
    async def get_task_log(task_id: str, lines: int = 100):
        """获取任务日志"""
        try:
            log_content = task_manager.get_task_log(task_id, lines)
            return {"log": log_content}
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="任务或日志文件不存在")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/task/{task_id}/metadata")
    async def download_task_metadata(task_id: str):
        """下载任务中间文件"""
        try:
            zip_path = task_manager.create_metadata_archive(task_id)
            return FileResponse(
                zip_path,
                media_type="application/zip",
                filename=f"{task_id}_metadata.zip",
            )
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="任务不存在")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/task/{task_id}/result")
    async def download_task_result(task_id: str):
        """下载任务结果文件"""
        try:
            zip_path = task_manager.create_result_archive(task_id)
            return FileResponse(
                zip_path, media_type="application/zip", filename=f"{task_id}_result.zip"
            )
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="任务不存在")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/task/{task_id}")
    async def cancel_task(task_id: str, db: SessionLocal = Depends(get_db)):
        """取消任务"""
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail="任务不存在")

            if task.status in ["completed", "failed", "cancelled"]:
                raise HTTPException(status_code=400, detail="任务已完成或已取消")

            # 取消任务
            task_manager.cancel_task(task_id)

            # 更新数据库状态
            task.status = "cancelled"
            db.commit()

            return {"message": "任务已取消"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {"status": "healthy"}

    return app
