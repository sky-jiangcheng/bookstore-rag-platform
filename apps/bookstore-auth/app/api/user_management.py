import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.auth import Permission, Role, User
from app.services.permission_service import require_permission
from app.utils.database import get_db

router = APIRouter()

# 配置日志
logger = logging.getLogger(__name__)


# 用户管理API
@router.get("/users")
async def get_users(
    username: Optional[str] = Query(None, description="用户名"),
    name: Optional[str] = Query(None, description="姓名"),
    email: Optional[str] = Query(None, description="邮箱"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_USERS")),
):
    """
    获取用户列表，支持分页和多条件筛选
    """
    try:
        # 构建查询
        query = db.query(User)

        # 应用筛选条件
        if username:
            query = query.filter(User.username.like(f"%{username}%"))
        if name:
            query = query.filter(User.name.like(f"%{name}%"))
        if email:
            query = query.filter(User.email.like(f"%{email}%"))
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        # 计算总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        users = query.order_by(User.id.desc()).offset(offset).limit(limit).all()

        # 转换结果
        result = []
        for user in users:
            user_roles = [
                {"id": role.id, "name": role.name, "code": role.code}
                for role in user.roles
            ]
            result.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "email": user.email,
                    "is_active": user.is_active,
                    "roles": user_roles,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                }
            )

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_USERS")),
):
    """
    获取用户详情
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        user_roles = [
            {"id": role.id, "name": role.name, "code": role.code} for role in user.roles
        ]

        return {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "roles": user_roles,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user detail: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户详情失败")


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: dict = Body(..., description="用户信息"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_USERS")),
):
    """
    更新用户信息
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 更新字段
        update_fields = ["name", "email", "is_active"]
        for field in update_fields:
            if field in user_data:
                setattr(user, field, user_data[field])

        db.commit()
        db.refresh(user)

        return {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "is_active": user.is_active,
            "updated_at": user.updated_at,
            "message": "用户信息更新成功",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail="更新用户信息失败")


# 角色管理API
@router.get("/roles")
async def get_roles(
    name: Optional[str] = Query(None, description="角色名称"),
    code: Optional[str] = Query(None, description="角色代码"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_ROLES")),
):
    """
    获取角色列表，支持分页和筛选
    """
    try:
        # 构建查询
        query = db.query(Role)

        # 应用筛选条件
        if name:
            query = query.filter(Role.name.like(f"%{name}%"))
        if code:
            query = query.filter(Role.code.like(f"%{code}%"))

        # 计算总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        roles = query.order_by(Role.id.desc()).offset(offset).limit(limit).all()

        # 转换结果
        result = []
        for role in roles:
            role_permissions = [
                {"id": perm.id, "name": perm.name, "code": perm.code}
                for perm in role.permissions
            ]
            result.append(
                {
                    "id": role.id,
                    "name": role.name,
                    "code": role.code,
                    "description": role.description,
                    "permissions": role_permissions,
                    "created_at": role.created_at,
                    "updated_at": role.updated_at,
                }
            )

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except Exception as e:
        logger.error(f"Error getting roles: {str(e)}")
        raise HTTPException(status_code=500, detail="获取角色列表失败")


@router.post("/roles")
async def create_role(
    role_data: dict = Body(..., description="角色信息"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_ROLES")),
):
    """
    创建角色
    """
    try:
        # 检查必填字段
        if "name" not in role_data or "code" not in role_data:
            raise HTTPException(status_code=400, detail="缺少角色名称或代码")

        # 检查角色是否已存在
        existing_role = (
            db.query(Role)
            .filter((Role.name == role_data["name"]) | (Role.code == role_data["code"]))
            .first()
        )
        if existing_role:
            raise HTTPException(status_code=400, detail="角色名称或代码已存在")

        # 创建角色
        new_role = Role(
            name=role_data["name"],
            code=role_data["code"],
            description=role_data.get("description"),
        )

        # 处理权限关联
        if "permissions" in role_data and isinstance(role_data["permissions"], list):
            for perm_id in role_data["permissions"]:
                permission = (
                    db.query(Permission).filter(Permission.id == perm_id).first()
                )
                if permission:
                    new_role.permissions.append(permission)

        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        return {
            "id": new_role.id,
            "name": new_role.name,
            "code": new_role.code,
            "message": "角色创建成功",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating role: {str(e)}")
        raise HTTPException(status_code=500, detail="创建角色失败")


@router.put("/roles/{role_id}")
async def update_role(
    role_id: int,
    role_data: dict = Body(..., description="角色信息"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_ROLES")),
):
    """
    更新角色信息
    """
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")

        # 更新字段
        update_fields = ["name", "description"]
        for field in update_fields:
            if field in role_data:
                setattr(role, field, role_data[field])

        # 处理权限关联
        if "permissions" in role_data and isinstance(role_data["permissions"], list):
            # 清空现有权限
            role.permissions = []
            # 添加新权限
            for perm_id in role_data["permissions"]:
                permission = (
                    db.query(Permission).filter(Permission.id == perm_id).first()
                )
                if permission:
                    role.permissions.append(permission)

        db.commit()
        db.refresh(role)

        return {
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "updated_at": role.updated_at,
            "message": "角色更新成功",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role: {str(e)}")
        raise HTTPException(status_code=500, detail="更新角色失败")


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_ROLES")),
):
    """
    删除角色
    """
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")

        # 检查是否有关联用户
        if role.users:
            raise HTTPException(status_code=400, detail="该角色已分配给用户，无法删除")

        db.delete(role)
        db.commit()

        return {"message": "角色删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting role: {str(e)}")
        raise HTTPException(status_code=500, detail="删除角色失败")


# 权限管理API
@router.get("/permissions")
async def get_permissions(
    name: Optional[str] = Query(None, description="权限名称"),
    code: Optional[str] = Query(None, description="权限代码"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_PERMISSIONS")),
):
    """
    获取权限列表，支持分页和筛选
    """
    try:
        # 构建查询
        query = db.query(Permission)

        # 应用筛选条件
        if name:
            query = query.filter(Permission.name.like(f"%{name}%"))
        if code:
            query = query.filter(Permission.code.like(f"%{code}%"))

        # 计算总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        permissions = (
            query.order_by(Permission.id.desc()).offset(offset).limit(limit).all()
        )

        # 转换结果
        result = []
        for perm in permissions:
            result.append(
                {
                    "id": perm.id,
                    "name": perm.name,
                    "code": perm.code,
                    "description": perm.description,
                    "created_at": perm.created_at,
                    "updated_at": perm.updated_at,
                }
            )

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except Exception as e:
        logger.error(f"Error getting permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="获取权限列表失败")


# 用户角色管理API
@router.put("/users/{user_id}/roles")
async def update_user_roles(
    user_id: int,
    role_data: dict = Body(..., description="角色数据"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_USERS")),
):
    """
    更新用户角色
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 检查角色数据
        if "roles" not in role_data or not isinstance(role_data["roles"], list):
            raise HTTPException(status_code=400, detail="缺少角色数据")

        # 清空现有角色
        user.roles = []

        # 添加新角色
        for role_id in role_data["roles"]:
            role = db.query(Role).filter(Role.id == role_id).first()
            if role:
                user.roles.append(role)

        db.commit()
        db.refresh(user)

        user_roles = [
            {"id": role.id, "name": role.name, "code": role.code} for role in user.roles
        ]

        return {
            "id": user.id,
            "username": user.username,
            "roles": user_roles,
            "message": "用户角色更新成功",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user roles: {str(e)}")
        raise HTTPException(status_code=500, detail="更新用户角色失败")
