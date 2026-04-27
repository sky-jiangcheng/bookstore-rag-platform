from sqlalchemy import (DECIMAL, TIMESTAMP, BigInteger, Column, Integer,
                        String, Text)
from sqlalchemy.sql import func

from app.utils.database import Base


class BookInfo(Base):
    __tablename__ = "t_book_info"
    __table_args__ = {"extend_existing": True}

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    barcode = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=False)
    title_clean = Column(String(512), nullable=False, index=True)
    author = Column(String(256), index=True)
    publisher = Column(String(256))
    series = Column(String(256))
    price = Column(DECIMAL(10, 2))
    stock = Column(Integer, default=0)
    discount = Column(DECIMAL(5, 4), default=0)
    summary = Column(Text)
    embedding = Column(Text)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())
