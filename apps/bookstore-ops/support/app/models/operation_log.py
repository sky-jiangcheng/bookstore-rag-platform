import enum
from sqlalchemy import TIMESTAMP, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.utils.database import Base


class OperationType(str, enum.Enum):
    IMPORT = "IMPORT"
    MERGE = "MERGE"
    IGNORE = "IGNORE"
    REFRESH = "REFRESH"
    EXPORT = "EXPORT"
    IMPORT_BOOKS = "IMPORT_BOOKS"
    MERGE_BOOK = "MERGE_BOOK"
    IGNORE_BOOK = "IGNORE_BOOK"


class OperationStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class OperationLog(Base):
    __tablename__ = "t_operation_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    operation_type = Column(Enum(OperationType), nullable=False, index=True)
    operation_status = Column(Enum(OperationStatus), nullable=False, index=True)
    target_id = Column(Integer, index=True)
    source_id = Column(Integer, index=True)
    description = Column(Text, nullable=False)
    error_message = Column(Text)
    create_time = Column(TIMESTAMP, server_default=func.now(), index=True)


class BatchOperationLog(Base):
    __tablename__ = "t_batch_operation_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    operation_type = Column(Enum(OperationType), nullable=False, index=True)
    operation_status = Column(Enum(OperationStatus), nullable=False, index=True)
    total_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=False)
    error_message = Column(Text)
    create_time = Column(TIMESTAMP, server_default=func.now(), index=True)
