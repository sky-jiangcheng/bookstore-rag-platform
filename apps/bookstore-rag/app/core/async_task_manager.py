"""
异步任务管理器 - 支持大批量请求异步处理

功能:
1. 任务队列管理
2. 任务状态追踪
3. 进度更新
4. 任务结果缓存
5. 失败重试机制
"""

import asyncio
import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from fastapi import BackgroundTasks

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 执行中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class AsyncTask:
    """异步任务"""

    def __init__(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict | None = None,
        name: str | None = None,
        user_id: Optional[int] = None,
    ):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.name = name or f"Task-{task_id[:8]}"
        self.user_id = user_id

        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        self.progress = 0
        self.total = None
        self.message = "Task is pending"
        self.result: Any = None
        self.error: Optional[str] = None

        self.retry_count = 0
        self.max_retries = 3

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status.value,
            "progress": self.progress,
            "total": self.total,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "retry_count": self.retry_count,
            "has_result": self.result is not None,
        }

    def update_progress(self, progress: int, total: Optional[int] = None, message: str | None = None):
        """更新进度"""
        self.progress = progress
        if total is not None:
            self.total = total
        if message:
            self.message = message
        logger.info(f"Task {self.task_id} progress: {progress}/{self.total} - {self.message}")

    def set_running(self):
        """设置为运行状态"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self.message = "Task is running"

    def set_success(self, result: Any = None):
        """设置为成功状态"""
        self.status = TaskStatus.SUCCESS
        self.completed_at = datetime.now()
        self.progress = 100
        self.message = "Task completed successfully"
        self.result = result
        logger.info(f"Task {self.task_id} completed successfully")

    def set_failed(self, error: str):
        """设置为失败状态"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        self.message = f"Task failed: {error}"
        logger.error(f"Task {self.task_id} failed: {error}")

    def set_cancelled(self):
        """设置为取消状态"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
        self.message = "Task was cancelled"
        logger.info(f"Task {self.task_id} cancelled")


class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.tasks: Dict[str, AsyncTask] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = True

    def create_task(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict | None = None,
        name: str | None = None,
        user_id: Optional[int] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> str:
        """创建异步任务"""
        task_id = str(uuid.uuid4())
        task = AsyncTask(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            name=name,
            user_id=user_id,
        )
        self.tasks[task_id] = task

        if background_tasks:
            # 使用FastAPI BackgroundTasks
            background_tasks.add_task(self._run_task, task)
        else:
            # 使用线程池
            self.executor.submit(self._run_task, task)

        logger.info(f"Created task {task_id}: {name}")
        return task_id

    def _run_task(self, task: AsyncTask):
        """执行任务（内部方法）"""
        try:
            task.set_running()

            # 执行任务函数
            if asyncio.iscoroutinefunction(task.func):
                # 异步函数
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        task.func(task, *task.args, **task.kwargs)
                    )
                finally:
                    loop.close()
            else:
                # 同步函数
                result = task.func(task, *task.args, **task.kwargs)

            task.set_success(result)

        except Exception as e:
            error_msg = str(e)
            task.set_failed(error_msg)

            # 重试机制
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.warning(f"Retrying task {task.task_id}, attempt {task.retry_count}")
                # 等待一段时间后重试
                time.sleep(2 ** task.retry_count)  # 指数退避
                self.executor.submit(self._run_task, task)

    def get_task(self, task_id: str) -> Optional[AsyncTask]:
        """获取任务"""
        return self.tasks.get(task_id)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.get_task(task_id)
        return task.to_dict() if task else None

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.set_cancelled()
            return True
        return False

    def get_user_tasks(
        self, user_id: int, status: Optional[TaskStatus] = None
    ) -> List[Dict[str, Any]]:
        """获取用户的所有任务"""
        tasks = [
            task
            for task in self.tasks.values()
            if task.user_id == user_id and (status is None or task.status == status)
        ]
        return [task.to_dict() for task in tasks]

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        now = datetime.now()
        to_delete = []

        for task_id, task in self.tasks.items():
            if task.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                age = now - task.completed_at if task.completed_at else now - task.created_at
                if age.total_seconds() > max_age_hours * 3600:
                    to_delete.append(task_id)

        for task_id in to_delete:
            del self.tasks[task_id]
            logger.info(f"Cleaned up old task {task_id}")

        return len(to_delete)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.tasks)
        status_counts = {}
        for task in self.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_tasks": total,
            "status_distribution": status_counts,
            "max_workers": self.max_workers,
            "is_running": self._running,
        }

    def shutdown(self):
        """关闭任务管理器"""
        self._running = False
        self.executor.shutdown(wait=True)
        logger.info("AsyncTaskManager shutdown")


# 全局任务管理器实例
task_manager = AsyncTaskManager(max_workers=4)


def get_task_manager() -> AsyncTaskManager:
    """获取任务管理器实例"""
    return task_manager
