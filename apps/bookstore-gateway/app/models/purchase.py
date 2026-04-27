import enum
from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.database import Base


class PurchaseStatus(str, enum.Enum):
    PENDING = "PENDING"  # 待处理
    APPROVED = "APPROVED"  # 已批准
    ORDERED = "ORDERED"  # 已下单
    DELIVERED = "DELIVERED"  # 已送达
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消


class Supplier(Base):
    __tablename__ = "t_supplier"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(100))
    address = Column(Text)
    tax_number = Column(String(50))
    bank_account = Column(String(100))
    remark = Column(Text)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关系
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class PurchaseOrder(Base):
    __tablename__ = "t_purchase_order"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    order_number = Column(String(50), nullable=False, unique=True, index=True)
    supplier_id = Column(
        BigInteger, ForeignKey("t_supplier.id"), nullable=False, index=True
    )
    total_amount = Column(Float, nullable=False, default=0.0)
    status = Column(
        Enum(PurchaseStatus), nullable=False, default=PurchaseStatus.PENDING, index=True
    )
    order_date = Column(TIMESTAMP, server_default=func.now())
    expected_delivery_date = Column(TIMESTAMP)
    actual_delivery_date = Column(TIMESTAMP)
    remark = Column(Text)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关系
    supplier = relationship("Supplier", back_populates="purchase_orders")
    order_items = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )


class PurchaseOrderItem(Base):
    __tablename__ = "t_purchase_order_item"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    purchase_order_id = Column(
        BigInteger, ForeignKey("t_purchase_order.id"), nullable=False, index=True
    )
    book_id = Column(BigInteger, nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    remark = Column(Text)

    # 关系
    purchase_order = relationship("PurchaseOrder", back_populates="order_items")
