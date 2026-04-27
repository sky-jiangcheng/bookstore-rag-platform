"""
任务管理API - 提供异步任务查询和管理接口

功能:
1. 任务状态查询
2. 任务列表查询
3. 任务取消
4. 任务统计
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.auth_management import get_current_active_user
from app.core.async_task_manager import (TaskStatus, get_task_manager)
from app.models.auth import User

router = APIRouter()


# ==================== 请求/响应模型 ====================


class TaskStatusResponse(BaseModel):
    """任务状态响应"""

    task_id: str
    name: str
    status: str
    progress: int
    total: Optional[int]
    message: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]
    retry_count: int
    has_result: bool


class TaskListResponse(BaseModel):
    """任务列表响应"""

    tasks: list
    total: int


class TaskStatisticsResponse(BaseModel):
    """任务统计响应"""

    total_tasks: int
    status_distribution: dict
    max_workers: int
    is_running: bool


# ==================== API端点 ====================


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    获取任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态信息
    """
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    # 验证权限（可选，如果任务与用户关联）
    # if task.user_id and task.user_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="无权访问此任务")

    return TaskStatusResponse(**task.to_dict())


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(
        None, description="按状态筛选: pending/running/success/failed/cancelled"
    ),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户的任务列表

    Args:
        status: 可选的状态筛选

    Returns:
        任务列表
    """
    task_manager = get_task_manager()

    # 筛选状态
    task_status = None
    if status:
        try:
            task_status = TaskStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

    # 获取用户任务
    tasks = task_manager.get_user_tasks(current_user.id, task_status)

    return TaskListResponse(tasks=tasks, total=len(tasks))


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    取消任务

    Args:
        task_id: 任务ID

    Returns:
        取消结果
    """
    task_manager = get_task_manager()

    if not task_manager.get_task(task_id):
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    success = task_manager.cancel_task(task_id)

    if not success:
        raise HTTPException(status_code=400, detail="任务无法取消（可能已在运行或已完成）")

    return {"message": "任务已取消", "task_id": task_id}


@router.get("/tasks/statistics", response_model=TaskStatisticsResponse)
async def get_task_statistics(
    current_user: User = Depends(get_current_active_user),
):
    """
    获取任务统计信息（管理员）

    Returns:
        统计信息
    """
    # 权限检查（可选）
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="需要管理员权限")

    task_manager = get_task_manager()
    stats = task_manager.get_statistics()

    return TaskStatisticsResponse(**stats)


@router.post("/tasks/cleanup")
async def cleanup_old_tasks(
    max_age_hours: int = Query(24, ge=1, le=168, description="最大任务保留时间（小时）"),
    current_user: User = Depends(get_current_active_user),
):
    """
    清理旧任务（管理员）

    Args:
        max_age_hours: 任务最大保留时间（小时）

    Returns:
        清理结果
    """
    # 权限检查（可选）
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403, detail="需要管理员权限")

    task_manager = get_task_manager()
    cleaned = task_manager.cleanup_old_tasks(max_age_hours)

    return {
        "message": f"已清理 {cleaned} 个旧任务",
        "cleaned_count": cleaned,
        "max_age_hours": max_age_hours,
    }
