import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import SECRET_KEY as APP_SECRET_KEY
from app.models.auth import User
from app.utils.database import get_db

logger = logging.getLogger(__name__)

# 使用 bcrypt 进行密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务类"""

    # 统一从应用配置读取密钥，避免在服务层保留独立默认值
    SECRET_KEY = APP_SECRET_KEY
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @staticmethod
    def hash_password(password: str) -> str:
        """密码加密 - 使用 bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """密码验证 - 使用 bcrypt，同时兼容旧 SHA-256 哈希的平滑迁移"""
        # 优先尝试 bcrypt 验证
        try:
            if pwd_context.verify(plain_password, hashed_password):
                return True
        except Exception:
            pass
        # 兼容旧 SHA-256 哈希（迁移期间）
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

    @staticmethod
    def create_access_token(
        data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问 token - 使用标准 JWT"""
        if not AuthService.SECRET_KEY:
            raise ValueError("SECRET_KEY is not configured")

        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, AuthService.SECRET_KEY, algorithm=AuthService.ALGORITHM)

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """创建刷新 token - 使用标准 JWT"""
        if not AuthService.SECRET_KEY:
            raise ValueError("SECRET_KEY is not configured")

        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=AuthService.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, AuthService.SECRET_KEY, algorithm=AuthService.ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """验证 token - 使用标准 JWT"""
        if not AuthService.SECRET_KEY:
            return None

        try:
            payload = jwt.decode(
                token, AuthService.SECRET_KEY, algorithms=[AuthService.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.debug("Token 验证失败: %s", e)
            return None

    @staticmethod
    def get_current_user(token: str) -> Optional[User]:
        """获取当前用户"""
        payload = AuthService.verify_token(token)
        if not payload:
            return None

        db = None
        try:
            db = next(get_db())
            user_id = payload.get("sub")
            # 确保 user_id 是整数类型
            if isinstance(user_id, str):
                user_id = int(user_id)
            user = db.query(User).filter(User.id == user_id).first()
            return user
        except Exception:
            return None
        finally:
            if db:
                db.close()

    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """认证用户"""
        db = None
        try:
            db = next(get_db())
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return None
            if not AuthService.verify_password(password, user.password_hash):
                return None
            if not user.is_active:
                return None
            return user
        finally:
            if db:
                db.close()
