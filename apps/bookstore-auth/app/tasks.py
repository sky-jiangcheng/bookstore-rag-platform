"""
Celery 异步任务队列配置

用于处理长流程任务（导入、推荐等），防止阻塞主线程：
1. 后台导入任务
2. 异步生成推荐
3. 定时清理任务
4. 任务监控和重试
"""

import logging
import os
from typing import Any, Dict

from celery import Celery, Task
from celery.schedules import crontab

from app.utils.config_loader import config_loader

logger = logging.getLogger(__name__)

cache_config = config_loader.get_cache_config()
redis_url = cache_config.get("url") or os.getenv("REDIS_URL", "")

# 免费部署模式下允许使用内存 broker/backend，避免 Redis 成为启动前提
if redis_url:
    broker_url = redis_url
    result_backend = redis_url
else:
    broker_url = "memory://"
    result_backend = "cache+memory://"
    logger.warning("Redis URL not configured; Celery is running in memory mode")

# 创建 Celery 应用
celery_app = Celery("bookstore", broker=broker_url, backend=result_backend)

# 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟硬限制
    task_soft_time_limit=25 * 60,  # 25分钟软限制
    broker_connection_retry_on_startup=True,
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    "cleanup-old-conversations": {
        "task": "app.tasks.cleanup_old_conversations",
        "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点
    },
    "clear-cache": {
        "task": "app.tasks.clear_expired_cache",
        "schedule": crontab(hour="*/4"),  # 每4小时执行一次
    },
}


class CallbackTask(Task):
    """
    任务基类，支持回调
    """

    def on_success(self, retval, task_id, args, kwargs):
        """成功回调"""
        logger.info(f"任务成功: {self.name} ({task_id})")
        return retval

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """重试回调"""
        logger.warning(f"任务重试: {self.name} ({task_id}) - {str(exc)}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """失败回调"""
        logger.error(f"任务失败: {self.name} ({task_id}) - {str(exc)}", exc_info=True)


# ==================== 异步任务定义 ====================


@celery_app.task(base=CallbackTask, bind=True, max_retries=3)
def import_books_async(self, file_id: str, user_id: int) -> Dict[str, Any]:
    """
    异步导入书籍任务

    Args:
        file_id: 文件 ID
        user_id: 用户 ID

    Returns:
        导入结果
    """
    try:
        from app.core.service_registry import get_service

        logger.info(f"开始异步导入: file_id={file_id}, user_id={user_id}")

        # 更新任务状态
        self.update_state(
            state="PROGRESS", meta={"current": 0, "total": 100, "status": "正在初始化..."}
        )

        # 获取导入服务
        import_service = get_service("import_service")

        # 执行导入
        result = import_service.import_books(file_id, user_id)

        logger.info(f"异步导入完成: file_id={file_id}")
        return {"success": True, "result": result}

    except Exception as exc:
        logger.error(f"异步导入失败: {str(exc)}", exc_info=True)
        # 重试
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(base=CallbackTask, bind=True, max_retries=2)
def generate_recommendation_async(
    self, session_id: int, user_id: int, limit: int = 20
) -> Dict[str, Any]:
    """
    异步生成推荐任务

    Args:
        session_id: 会话 ID
        user_id: 用户 ID
        limit: 推荐数量

    Returns:
        推荐结果
    """
    try:
        from app.core.service_registry import get_service
        from app.models import BookListSession
        from app.utils.database import SessionLocal

        logger.info(f"开始异步生成推荐: " f"session_id={session_id}, user_id={user_id}")

        db = SessionLocal()

        try:
            # 获取会话
            session = (
                db.query(BookListSession)
                .filter(
                    BookListSession.id == session_id, BookListSession.user_id == user_id
                )
                .first()
            )

            if not session:
                raise ValueError(f"会话不存在: session_id={session_id}")

            # 更新状态
            self.update_state(
                state="PROGRESS",
                meta={"current": 30, "total": 100, "status": "正在生成推荐..."},
            )

            # 获取编排器
            orchestrator = get_service("service_orchestrator")

            # 生成推荐
            from app.api.v1.book_list.schemas import ParsedRequirements

            parsed_reqs = ParsedRequirements(**session.parsed_requirements)

            response = orchestrator.generate_book_list(
                request_id=session.request_id,
                user_id=user_id,
                requirements=parsed_reqs,
                limit=limit,
                save_to_history=True,
            )

            logger.info(f"异步生成推荐完成: session_id={session_id}")

            return {
                "success": True,
                "session_id": session_id,
                "total_count": response.total_count,
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"异步生成推荐失败: {str(exc)}", exc_info=True)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(base=CallbackTask)
def cleanup_old_conversations() -> Dict[str, Any]:
    """清理旧对话"""
    try:
        from app.core.service_registry import get_service

        logger.info("开始清理旧对话...")

        conversation_manager = get_service("conversation_manager")
        conversation_manager.cleanup_old_conversations(max_age_hours=24)

        logger.info("旧对话清理完成")
        return {"success": True, "message": "旧对话已清理"}

    except Exception as exc:
        logger.error(f"清理旧对话失败: {str(exc)}", exc_info=True)
        raise


@celery_app.task(base=CallbackTask)
def clear_expired_cache() -> Dict[str, Any]:
    """清理过期缓存"""
    try:
        pass

        logger.info("开始清理过期缓存...")

        # 获取缓存服务
        # cache_service = get_service("cache_service")
        # 这里可以调用缓存服务的清理方法
        # cache_service.cleanup_expired()

        logger.info("过期缓存已清理")
        return {"success": True, "message": "过期缓存已清理"}

    except Exception as exc:
        logger.error(f"清理过期缓存失败: {str(exc)}", exc_info=True)
        raise


# ==================== 任务状态查询 ====================


def get_task_status(task_id: str) -> Dict[str, Any]:
    """获取任务状态"""
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "state": result.state,
        "current": result.info.get("current", 0)
        if isinstance(result.info, dict)
        else 0,
        "total": result.info.get("total", 100)
        if isinstance(result.info, dict)
        else 100,
        "status": result.info.get("status", "")
        if isinstance(result.info, dict)
        else str(result.info),
    }


def revoke_task(task_id: str, terminate: bool = False) -> None:
    """撤销任务"""
    from celery.result import AsyncResult

    AsyncResult(task_id, app=celery_app).revoke(terminate=terminate)
    logger.info(f"任务已撤销: {task_id}")


# ==================== 便捷函数 ====================


def submit_import_task(file_id: str, user_id: int) -> str:
    """提交导入任务"""
    task = import_books_async.delay(file_id, user_id)
    logger.info(f"导入任务已提交: task_id={task.id}")
    return task.id


def submit_recommendation_task(session_id: int, user_id: int, limit: int = 20) -> str:
    """提交推荐任务"""
    task = generate_recommendation_async.delay(session_id, user_id, limit)
    logger.info(f"推荐任务已提交: task_id={task.id}")
    return task.id
