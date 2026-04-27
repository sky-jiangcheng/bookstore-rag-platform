import json

import logging
from sqlalchemy.orm import Session

from app.models.operation_log import (
    BatchOperationLog,
    OperationLog,
    OperationStatus,
    OperationType,
)

logger = logging.getLogger(__name__)


class LogService:
    """
    日志服务类，用于记录操作日志
    """

    @staticmethod
    def record_operation(
        operation_type,
        status,
        entity_id=None,
        entity_type=None,
        user_id=None,
        details=None,
        db=None,
    ):
        """
        记录单条操作日志
        """
        try:
            from app.utils.database import get_db as get_db_session

            # 如果没有提供db，获取一个新的session
            if not db:
                db = next(get_db_session())

            # 转换参数
            operation_type_enum = OperationType(operation_type)
            operation_status_enum = OperationStatus(status)

            # 生成描述（使用JSON格式）
            log_data = {
                "operation_type": operation_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
            }
            if details:
                log_data.update(details)

            description = json.dumps(log_data, ensure_ascii=False)

            log = OperationLog(
                operation_type=operation_type_enum,
                operation_status=operation_status_enum,
                target_id=entity_id,
                source_id=None,
                description=description,
                error_message=None,
            )
            db.add(log)
            db.commit()

            # 同时输出到文件日志
            log_message = (
                f"[{operation_type}] {json.dumps(log_data, ensure_ascii=False)}"
            )
            if status == "SUCCESS":
                logger.info(log_message)
            else:
                logger.error(log_message)

            return log
        except Exception as e:
            logger.error(f"Error recording operation log: {str(e)}")
            return None

    @staticmethod
    def record_batch_operation(
        operation_type,
        status,
        batch_size,
        success_count,
        failure_count,
        user_id=None,
        details=None,
        db=None,
    ):
        """
        记录批量操作日志
        """
        try:
            from app.utils.database import get_db as get_db_session

            # 如果没有提供db，获取一个新的session
            if not db:
                db = next(get_db_session())

            # 转换参数
            operation_type_enum = OperationType(operation_type)
            operation_status_enum = OperationStatus(status)

            # 生成描述（使用JSON格式）
            log_data = {
                "operation_type": operation_type,
                "batch_size": batch_size,
                "success_count": success_count,
                "failure_count": failure_count,
            }
            if details:
                log_data.update(details)

            description = json.dumps(log_data, ensure_ascii=False)

            log = BatchOperationLog(
                operation_type=operation_type_enum,
                operation_status=operation_status_enum,
                total_count=batch_size,
                success_count=success_count,
                failure_count=failure_count,
                description=description,
                error_message=None,
            )
            db.add(log)
            db.commit()

            # 同时输出到文件日志
            log_message = (
                f"[{operation_type}] {json.dumps(log_data, ensure_ascii=False)}"
            )
            if status == "SUCCESS":
                logger.info(log_message)
            else:
                logger.error(log_message)

            return log
        except Exception as e:
            logger.error(f"Error recording batch operation log: {str(e)}")
            return None
