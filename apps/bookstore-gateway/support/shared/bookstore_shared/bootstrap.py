"""应用运行时初始化工具。

这是 backend 与各独立服务入口共用的共享实现。
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from sqlalchemy.engine import Engine


def wait_for_database(
    engine: Engine,
    logger: logging.Logger,
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
) -> bool:
    """快速探测数据库是否可用。"""
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.exec_driver_sql("SELECT 1")
            return True
        except Exception as exc:  # pragma: no cover - best effort startup probe
            last_error = exc
            if attempt == max_attempts:
                break

            logger.warning(
                "Database not ready yet, retrying in %ss (%s/%s): %s",
                delay_seconds,
                attempt,
                max_attempts,
                exc,
            )
            time.sleep(delay_seconds)

    logger.warning("Database probe failed, continuing in degraded mode: %s", last_error)
    return False


def initialize_runtime(
    engine: Engine,
    logger: logging.Logger,
) -> bool:
    """初始化服务运行时依赖。"""
    from app.models import Base

    database_ready = wait_for_database(engine, logger)

    if database_ready:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as exc:  # pragma: no cover - best effort startup init
            logger.warning(
                "Error creating database tables, continuing without persistence: %s",
                exc,
            )
            database_ready = False

    try:
        from app.core.service_registry import register_services

        register_services()
        logger.info("Services registered successfully")
    except Exception as exc:  # pragma: no cover - best effort startup init
        logger.warning("Error registering services: %s", exc)

    try:
        from app.services.vector_db_service import vector_db

        vector_db.bootstrap_from_database()
    except Exception as exc:  # pragma: no cover - best effort startup init
        logger.warning("Failed to bootstrap local vector database: %s", exc)

    return database_ready
