import os
from datetime import timedelta
from types import SimpleNamespace
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.auth import User
from app.services.auth_service import AuthService
from app.utils.database import get_db

router = APIRouter()


# 简单的token获取方式
def get_token_from_header(authorization: str = None) -> str:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    return authorization[7:]


def _degraded_auth_enabled() -> bool:
    """是否启用降级认证。

    仅在测试/开发显式开启时使用，**生产/staging 环境永远返回 False**。
    """
    app_env = os.getenv("APP_ENV", "development").lower()
    # 生产/预发布环境强制禁用
    if app_env in ("production", "prod", "staging"):
        return False
    flag = os.getenv("BOOKSTORE_DEGRADED_AUTH", "").lower() in {"1", "true", "yes"}
    enabled = app_env == "testing" or flag
    if enabled:
        import logging
        logging.getLogger(__name__).warning(
            "⚠️  降级认证已启用（BOOKSTORE_DEGRADED_AUTH=true），"
            "所有请求将以超级管理员身份通过认证！请勿在生产环境使用！"
        )
    return enabled


def _build_test_user() -> SimpleNamespace:
    """构造一个无需数据库的测试用户。"""
    super_admin = os.getenv("BOOKSTORE_TEST_SUPER_ADMIN", "1").lower() in {
        "1",
        "true",
        "yes",
    }
    roles = [SimpleNamespace(code="SUPER_ADMIN")] if super_admin else []
    return SimpleNamespace(
        id=1,
        username="test_user",
        email="test@example.com",
        name="Test User",
        is_active=True,
        roles=roles,
        _synthetic_auth=True,
    )


# 请求模型
class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    username: str
    name: str


class TokenData(BaseModel):
    user_id: int
    username: str


# 依赖项
def get_current_user(authorization: str = Header(None)) -> User:
    """获取当前用户"""
    token = get_token_from_header(authorization)
    if not token:
        if _degraded_auth_enabled():
            return _build_test_user()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = AuthService.get_current_user(token)
    if not user:
        if _degraded_auth_enabled():
            return _build_test_user()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_user_optional(authorization: str = Header(None)) -> Optional[User]:
    """获取当前用户（可选，不抛出异常）"""
    token = get_token_from_header(authorization)
    if not token:
        if _degraded_auth_enabled():
            return _build_test_user()
        return None
    user = AuthService.get_current_user(token)
    if not user:
        if _degraded_auth_enabled():
            return _build_test_user()
        return None
    return user


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """登录"""
    user = AuthService.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问token
    access_token_expires = timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires,
    )

    # 创建刷新token
    refresh_token = AuthService.create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "name": user.name,
    }


@router.post("/register", response_model=Token)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_create.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_create.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 创建新用户
    hashed_password = AuthService.hash_password(user_create.password)
    new_user = User(
        username=user_create.username,
        password_hash=hashed_password,
        email=user_create.email,
        name=user_create.name,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 创建访问token
    access_token_expires = timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(new_user.id), "username": new_user.username},
        expires_delta=access_token_expires,
    )

    # 创建刷新token
    refresh_token = AuthService.create_refresh_token(
        data={"sub": str(new_user.id), "username": new_user.username}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "username": new_user.username,
        "name": new_user.name,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """刷新token"""
    payload = AuthService.verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # 创建新的访问token
    access_token_expires = timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires,
    )

    # 创建新的刷新token
    new_refresh_token = AuthService.create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "name": user.name,
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """退出登录"""
    # 由于使用JWT，退出登录主要在前端处理
    # 后端可以添加token黑名单功能，这里简化处理
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "name": current_user.name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
    }
