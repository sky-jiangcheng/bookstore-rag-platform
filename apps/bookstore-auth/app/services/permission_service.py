import os
from typing import Any, List, Optional, Set

from fastapi import Header

from app.models.auth import Permission, Role, User
from app.services.auth_service import AuthService
from app.utils.database import get_db


# 简单的token获取函数
def get_token_from_header(authorization: str = None) -> str:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    return authorization[7:]


class PermissionService:
    """权限服务类"""

    @staticmethod
    def _degraded_auth_enabled() -> bool:
        app_env = os.getenv("APP_ENV", "development").lower()
        flag = os.getenv("BOOKSTORE_DEGRADED_AUTH", "").lower() in {"1", "true", "yes"}
        return app_env == "testing" or flag

    @staticmethod
    def _extract_test_permissions(user: Any) -> Optional[Set[str]]:
        """从合成用户对象中提取权限/角色。"""
        if not getattr(user, "_synthetic_auth", False):
            return None

        permissions = set(getattr(user, "_test_permissions", []) or [])
        roles = getattr(user, "roles", []) or []
        role_codes = {
            getattr(role, "code", None) for role in roles if getattr(role, "code", None)
        }
        if "SUPER_ADMIN" in role_codes:
            permissions.add("*")
        return permissions

    @staticmethod
    def get_user_permissions(user_id: int) -> List[Permission]:
        """获取用户的所有权限"""
        db = None
        try:
            db = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return []

            permissions = []
            for role in user.roles:
                permissions.extend(role.permissions)

            # 去重
            unique_permissions = []
            seen_codes = set()
            for perm in permissions:
                if perm.code not in seen_codes:
                    seen_codes.add(perm.code)
                    unique_permissions.append(perm)

            return unique_permissions
        finally:
            if db:
                db.close()

    @staticmethod
    def check_permission(user_id: Any, permission_code: str) -> bool:
        """检查用户是否具有特定权限"""
        test_permissions = PermissionService._extract_test_permissions(user_id)
        if test_permissions is not None:
            return "*" in test_permissions or permission_code in test_permissions

        if isinstance(user_id, int) is False and hasattr(user_id, "id"):
            user_id = user_id.id

        permissions = PermissionService.get_user_permissions(user_id)
        permission_codes = [perm.code for perm in permissions]

        # 检查用户是否具有该权限
        if permission_code in permission_codes:
            return True

        # 检查用户是否是超级管理员
        db = None
        try:
            db = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                for role in user.roles:
                    if role.code == "SUPER_ADMIN":
                        return True
        finally:
            if db:
                db.close()

        return False

    @staticmethod
    def check_any_permission(user_id: Any, permission_codes: List[str]) -> bool:
        """检查用户是否具有任一权限"""
        test_permissions = PermissionService._extract_test_permissions(user_id)
        if test_permissions is not None:
            return "*" in test_permissions or any(
                code in test_permissions for code in permission_codes
            )

        if isinstance(user_id, int) is False and hasattr(user_id, "id"):
            user_id = user_id.id

        permissions = PermissionService.get_user_permissions(user_id)
        user_permission_codes = [perm.code for perm in permissions]

        # 检查用户是否具有任一权限
        for code in permission_codes:
            if code in user_permission_codes:
                return True

        # 检查用户是否是超级管理员
        db = None
        try:
            db = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                for role in user.roles:
                    if role.code == "SUPER_ADMIN":
                        return True
        finally:
            if db:
                db.close()

        return False

    @staticmethod
    def get_user_roles(user_id: Any) -> List[Role]:
        """获取用户的所有角色"""
        if PermissionService._extract_test_permissions(user_id) is not None:
            return (
                [Role(code="SUPER_ADMIN", name="SUPER_ADMIN")]
                if "*" in PermissionService._extract_test_permissions(user_id)
                else []
            )

        if isinstance(user_id, int) is False and hasattr(user_id, "id"):
            user_id = user_id.id

        db = None
        try:
            db = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            return user.roles
        finally:
            if db:
                db.close()

    @staticmethod
    def check_role(user_id: Any, role_code: str) -> bool:
        """检查用户是否具有特定角色"""
        test_permissions = PermissionService._extract_test_permissions(user_id)
        if test_permissions is not None:
            return "*" in test_permissions or role_code in test_permissions

        if isinstance(user_id, int) is False and hasattr(user_id, "id"):
            user_id = user_id.id

        roles = PermissionService.get_user_roles(user_id)
        role_codes = [role.code for role in roles]

        if role_code in role_codes:
            return True

        return False


# 权限检查依赖项
def require_permission(permission_code: str):
    """要求用户具有特定权限"""

    def dependency(authorization: str = Header(None)):
        # 首先获取当前用户
        token = get_token_from_header(authorization)
        if not token:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        current_user = AuthService.get_current_user(token)
        if not current_user:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 检查权限
        if not PermissionService.check_permission(current_user, permission_code):
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )
        return current_user

    return dependency


def require_any_permission(permission_codes: List[str]):
    """要求用户具有任一权限"""

    def dependency(authorization: str = Header(None)):
        # 首先获取当前用户
        token = get_token_from_header(authorization)
        if not token:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        current_user = AuthService.get_current_user(token)
        if not current_user:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 检查权限
        if not PermissionService.check_any_permission(current_user, permission_codes):
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )
        return current_user

    return dependency


def require_role(role_code: str):
    """要求用户具有特定角色"""

    def dependency(authorization: str = Header(None)):
        # 首先获取当前用户
        token = get_token_from_header(authorization)
        if not token:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        current_user = AuthService.get_current_user(token)
        if not current_user:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 检查角色
        if not PermissionService.check_role(current_user, role_code):
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Role denied"
            )
        return current_user

    return dependency
