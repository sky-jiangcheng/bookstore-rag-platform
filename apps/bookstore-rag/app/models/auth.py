from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.utils.database import Base

# 关联表
user_role = Table(
    "t_user_role",
    Base.metadata,
    Column(
        "user_id",
        BigInteger,
        ForeignKey("t_user.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        BigInteger,
        ForeignKey("t_role.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

role_permission = Table(
    "t_role_permission",
    Base.metadata,
    Column(
        "role_id",
        BigInteger,
        ForeignKey("t_role.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        BigInteger,
        ForeignKey("t_permission.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base):
    """用户模型"""

    __tablename__ = "t_user"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    email = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关联关系
    roles = relationship("Role", secondary=user_role, back_populates="users")


class Role(Base):
    """角色模型"""

    __tablename__ = "t_role"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关联关系
    users = relationship("User", secondary=user_role, back_populates="roles")
    permissions = relationship(
        "Permission", secondary=role_permission, back_populates="roles"
    )


class Permission(Base):
    """权限模型"""

    __tablename__ = "t_permission"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 关联关系
    roles = relationship(
        "Role", secondary=role_permission, back_populates="permissions"
    )
