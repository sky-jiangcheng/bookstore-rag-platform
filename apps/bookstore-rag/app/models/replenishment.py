import enum
from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.utils.database import Base


class PlanStatus(str, enum.Enum):
    PENDING = "PENDING"
    URGENT = "URGENT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReplenishmentPlan(Base):
    __tablename__ = "t_replenishment_plan"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    book_id = Column(
        BigInteger,
        ForeignKey("t_book_info.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    suggest_qty = Column(Integer, nullable=False)
    plan_status = Column(
        Enum(PlanStatus), default=PlanStatus.PENDING, nullable=False, index=True
    )
    reason = Column(Text)
    create_time = Column(TIMESTAMP, server_default=func.now())
    update_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
