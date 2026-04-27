from typing import Optional

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.operation_log import (
    BatchOperationLog,
    OperationLog,
    OperationStatus,
    OperationType,
)
from app.utils.database import get_db

router = APIRouter()

# 配置日志
logger = logging.getLogger(__name__)


@router.get("/logs/operation")
async def get_operation_logs(
    operation_type: Optional[str] = Query(None, description="操作类型"),
    status: Optional[str] = Query(None, description="操作状态"),
    start_time: Optional[str] = Query(None, description="开始时间 (YYYY-MM-DD)"),
    end_time: Optional[str] = Query(None, description="结束时间 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    获取操作日志列表，支持分页和筛选
    """
    try:
        # 构建查询
        query = db.query(OperationLog)

        # 应用筛选条件
        if operation_type:
            try:
                query = query.filter(
                    OperationLog.operation_type == OperationType(operation_type)
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的操作类型")

        if status:
            try:
                query = query.filter(
                    OperationLog.operation_status == OperationStatus(status)
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的操作状态")

        if start_time:
            query = query.filter(OperationLog.create_time >= start_time)

        if end_time:
            query = query.filter(OperationLog.create_time <= end_time)

        # 计算总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        logs = (
            query.order_by(OperationLog.create_time.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # 转换结果
        result = []
        for log in logs:
            result.append(
                {
                    "id": log.id,
                    "operation_type": log.operation_type.value,
                    "operation_status": log.operation_status.value,
                    "target_id": log.target_id,
                    "source_id": log.source_id,
                    "description": log.description,
                    "error_message": log.error_message,
                    "create_time": log.create_time,
                }
            )

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting operation logs: {str(e)}")
        raise HTTPException(status_code=500, detail="获取操作日志失败")


@router.get("/logs/batch")
async def get_batch_operation_logs(
    operation_type: Optional[str] = Query(None, description="操作类型"),
    status: Optional[str] = Query(None, description="操作状态"),
    start_time: Optional[str] = Query(None, description="开始时间 (YYYY-MM-DD)"),
    end_time: Optional[str] = Query(None, description="结束时间 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    获取批量操作日志列表，支持分页和筛选
    """
    try:
        # 构建查询
        query = db.query(BatchOperationLog)

        # 应用筛选条件
        if operation_type:
            try:
                query = query.filter(
                    BatchOperationLog.operation_type == OperationType(operation_type)
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的操作类型")

        if status:
            try:
                query = query.filter(
                    BatchOperationLog.operation_status == OperationStatus(status)
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的操作状态")

        if start_time:
            query = query.filter(BatchOperationLog.create_time >= start_time)

        if end_time:
            query = query.filter(BatchOperationLog.create_time <= end_time)

        # 计算总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        logs = (
            query.order_by(BatchOperationLog.create_time.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # 转换结果
        result = []
        for log in logs:
            result.append(
                {
                    "id": log.id,
                    "operation_type": log.operation_type.value,
                    "operation_status": log.operation_status.value,
                    "total_count": log.total_count,
                    "success_count": log.success_count,
                    "failure_count": log.failure_count,
                    "description": log.description,
                    "error_message": log.error_message,
                    "create_time": log.create_time,
                }
            )

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch operation logs: {str(e)}")
        raise HTTPException(status_code=500, detail="获取批量操作日志失败")


@router.get("/logs/operation/{log_id}")
async def get_operation_log_detail(log_id: int, db: Session = Depends(get_db)):
    """
    获取操作日志详情
    """
    try:
        log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="操作日志不存在")

        return {
            "id": log.id,
            "operation_type": log.operation_type.value,
            "operation_status": log.operation_status.value,
            "target_id": log.target_id,
            "source_id": log.source_id,
            "description": log.description,
            "error_message": log.error_message,
            "create_time": log.create_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting operation log detail: {str(e)}")
        raise HTTPException(status_code=500, detail="获取操作日志详情失败")


@router.get("/logs/batch/{log_id}")
async def get_batch_operation_log_detail(log_id: int, db: Session = Depends(get_db)):
    """
    获取批量操作日志详情
    """
    try:
        log = db.query(BatchOperationLog).filter(BatchOperationLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="批量操作日志不存在")

        return {
            "id": log.id,
            "operation_type": log.operation_type.value,
            "operation_status": log.operation_status.value,
            "total_count": log.total_count,
            "success_count": log.success_count,
            "failure_count": log.failure_count,
            "description": log.description,
            "error_message": log.error_message,
            "create_time": log.create_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch operation log detail: {str(e)}")
        raise HTTPException(status_code=500, detail="获取批量操作日志详情失败")
