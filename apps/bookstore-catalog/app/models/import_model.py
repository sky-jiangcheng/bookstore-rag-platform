from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.utils.database import Base


class ImportRecord(Base):
    __tablename__ = "t_import_record"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    error_message = Column(Text)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class ImportData(Base):
    __tablename__ = "t_import_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    import_id = Column(
        Integer,
        ForeignKey("t_import_record.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    barcode = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    author = Column(String(255))
    publisher = Column(String(255))
    series = Column(String(255))
    price = Column(Integer)  # 以分为单位存储
    stock = Column(Integer, default=0)
    discount = Column(Integer, default=0)  # 以百分比存储
    original_data = Column(Text, nullable=False)  # 存储原始行数据的JSON
    status = Column(String(50), default="PENDING", nullable=False)
    error_message = Column(Text)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
