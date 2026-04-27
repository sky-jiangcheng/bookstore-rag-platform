import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import hashlib

from app.config import SECRET_KEY as APP_SECRET_KEY
from app.models.auth import User
from app.utils.database import get_db


class AuthService:
    """认证服务类"""

    # 统一从应用配置读取密钥，避免在服务层保留独立默认值
    SECRET_KEY = APP_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @staticmethod
    def hash_password(password: str) -> str:
        """密码加密"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """密码验证"""
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

    @staticmethod
    def create_access_token(
        data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问token（简化版，不使用JWT）"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire.timestamp()})
        # 使用简单的编码方式
        token_data = json.dumps(to_encode)
        # 添加简单的签名
        signature = hashlib.sha256(
            (token_data + AuthService.SECRET_KEY).encode()
        ).hexdigest()
        return f"{token_data}.{signature}"

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """创建刷新token（简化版）"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=AuthService.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode.update({"exp": expire.timestamp(), "type": "refresh"})
        token_data = json.dumps(to_encode)
        signature = hashlib.sha256(
            (token_data + AuthService.SECRET_KEY).encode()
        ).hexdigest()
        return f"{token_data}.{signature}"

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """验证token（简化版）"""
        try:
            # 分割token和签名 - 只分割最后一个小数点
            if "." not in token:
                return None

            # 找到最后一个小数点的位置
            last_dot_index = token.rfind(".")
            token_data = token[:last_dot_index]
            signature = token[last_dot_index + 1 :]

            # 验证签名
            expected_signature = hashlib.sha256(
                (token_data + AuthService.SECRET_KEY).encode()
            ).hexdigest()
            if signature != expected_signature:
                return None

            # 解析token数据
            payload = json.loads(token_data)

            # 检查过期时间
            if datetime.utcnow().timestamp() > payload.get("exp", 0):
                return None

            return payload
        except Exception:
            return None

    @staticmethod
    def get_current_user(token: str) -> Optional[User]:
        """获取当前用户"""
        payload = AuthService.verify_token(token)
        if not payload:
            return None

        try:
            db = next(get_db())
            user_id = payload.get("sub")
            # 确保user_id是整数类型
            if isinstance(user_id, str):
                user_id = int(user_id)
            user = db.query(User).filter(User.id == user_id).first()
            return user
        except Exception:
            return None

    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """认证用户"""
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user
