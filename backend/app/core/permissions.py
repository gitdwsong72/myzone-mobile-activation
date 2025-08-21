from enum import Enum
from functools import wraps
from typing import List, Set

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.admin import Admin
from ..models.user import User
from .deps import get_current_admin, get_current_user, get_db


class Permission(Enum):
    """권한 열거형"""

    # 사용자 관련 권한
    READ_USER = "read:user"
    WRITE_USER = "write:user"
    DELETE_USER = "delete:user"

    # 주문 관련 권한
    READ_ORDER = "read:order"
    WRITE_ORDER = "write:order"
    DELETE_ORDER = "delete:order"
    PROCESS_ORDER = "process:order"

    # 요금제 관련 권한
    READ_PLAN = "read:plan"
    WRITE_PLAN = "write:plan"
    DELETE_PLAN = "delete:plan"

    # 단말기 관련 권한
    READ_DEVICE = "read:device"
    WRITE_DEVICE = "write:device"
    DELETE_DEVICE = "delete:device"

    # 번호 관련 권한
    READ_NUMBER = "read:number"
    WRITE_NUMBER = "write:number"
    DELETE_NUMBER = "delete:number"

    # 결제 관련 권한
    READ_PAYMENT = "read:payment"
    PROCESS_PAYMENT = "process:payment"
    REFUND_PAYMENT = "refund:payment"

    # 통계 및 리포트 권한
    READ_STATISTICS = "read:statistics"
    EXPORT_DATA = "export:data"

    # 시스템 관리 권한
    MANAGE_ADMIN = "manage:admin"
    SYSTEM_CONFIG = "system:config"


class Role(Enum):
    """역할 열거형"""

    USER = "user"
    OPERATOR = "operator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# 역할별 권한 매핑
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.USER: {
        Permission.READ_USER,  # 자신의 정보만
        Permission.WRITE_USER,  # 자신의 정보만
        Permission.READ_ORDER,  # 자신의 주문만
        Permission.WRITE_ORDER,  # 자신의 주문만
        Permission.READ_PLAN,
        Permission.READ_DEVICE,
        Permission.READ_NUMBER,
        Permission.PROCESS_PAYMENT,  # 자신의 결제만
    },
    Role.OPERATOR: {
        Permission.READ_USER,
        Permission.READ_ORDER,
        Permission.WRITE_ORDER,
        Permission.PROCESS_ORDER,
        Permission.READ_PLAN,
        Permission.READ_DEVICE,
        Permission.READ_NUMBER,
        Permission.READ_PAYMENT,
        Permission.PROCESS_PAYMENT,
    },
    Role.ADMIN: {
        Permission.READ_USER,
        Permission.WRITE_USER,
        Permission.DELETE_USER,
        Permission.READ_ORDER,
        Permission.WRITE_ORDER,
        Permission.DELETE_ORDER,
        Permission.PROCESS_ORDER,
        Permission.READ_PLAN,
        Permission.WRITE_PLAN,
        Permission.DELETE_PLAN,
        Permission.READ_DEVICE,
        Permission.WRITE_DEVICE,
        Permission.DELETE_DEVICE,
        Permission.READ_NUMBER,
        Permission.WRITE_NUMBER,
        Permission.DELETE_NUMBER,
        Permission.READ_PAYMENT,
        Permission.PROCESS_PAYMENT,
        Permission.REFUND_PAYMENT,
        Permission.READ_STATISTICS,
        Permission.EXPORT_DATA,
    },
    Role.SUPER_ADMIN: set(Permission),  # 모든 권한
}


class PermissionChecker:
    """권한 검사 클래스"""

    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions

    def __call__(self, current_admin: Admin = Depends(get_current_admin)):
        """관리자 권한 검사"""
        admin_role = Role(current_admin.role)
        admin_permissions = ROLE_PERMISSIONS.get(admin_role, set())

        for permission in self.required_permissions:
            if permission not in admin_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=f"권한이 부족합니다. 필요한 권한: {permission.value}"
                )

        return current_admin


class UserPermissionChecker:
    """사용자 권한 검사 클래스"""

    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions

    def __call__(self, current_user: User = Depends(get_current_user)):
        """사용자 권한 검사"""
        user_permissions = ROLE_PERMISSIONS.get(Role.USER, set())

        for permission in self.required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=f"권한이 부족합니다. 필요한 권한: {permission.value}"
                )

        return current_user


def require_permissions(*permissions: Permission):
    """관리자 권한 요구 데코레이터"""
    return PermissionChecker(list(permissions))


def require_user_permissions(*permissions: Permission):
    """사용자 권한 요구 데코레이터"""
    return UserPermissionChecker(list(permissions))


def check_resource_ownership(resource_user_id: int, current_user_id: int):
    """리소스 소유권 확인"""
    if resource_user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="해당 리소스에 접근할 권한이 없습니다.")


def is_admin_or_owner(
    resource_user_id: int, current_user: User = Depends(get_current_user), current_admin: Admin = Depends(get_current_admin)
):
    """관리자이거나 리소스 소유자인지 확인"""
    # 관리자인 경우 통과
    if current_admin:
        return current_admin

    # 사용자인 경우 소유권 확인
    if current_user and current_user.id == resource_user_id:
        return current_user

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="해당 리소스에 접근할 권한이 없습니다.")


class RoleManager:
    """역할 관리 클래스"""

    @staticmethod
    def get_user_permissions(user: User) -> Set[Permission]:
        """사용자 권한 조회"""
        return ROLE_PERMISSIONS.get(Role.USER, set())

    @staticmethod
    def get_admin_permissions(admin: Admin) -> Set[Permission]:
        """관리자 권한 조회"""
        admin_role = Role(admin.role)
        return ROLE_PERMISSIONS.get(admin_role, set())

    @staticmethod
    def has_permission(user_or_admin, permission: Permission) -> bool:
        """권한 보유 여부 확인"""
        if isinstance(user_or_admin, User):
            permissions = RoleManager.get_user_permissions(user_or_admin)
        elif isinstance(user_or_admin, Admin):
            permissions = RoleManager.get_admin_permissions(user_or_admin)
        else:
            return False

        return permission in permissions

    @staticmethod
    def can_access_resource(user_or_admin, resource_user_id: int, permission: Permission) -> bool:
        """리소스 접근 권한 확인"""
        # 관리자인 경우
        if isinstance(user_or_admin, Admin):
            return RoleManager.has_permission(user_or_admin, permission)

        # 사용자인 경우 - 자신의 리소스만 접근 가능
        if isinstance(user_or_admin, User):
            return user_or_admin.id == resource_user_id and RoleManager.has_permission(user_or_admin, permission)

        return False


# 편의 함수들
def require_admin_permissions(*permissions: Permission):
    """관리자 권한 요구"""
    return require_permissions(*permissions)


def require_order_management():
    """주문 관리 권한 요구"""
    return require_permissions(Permission.PROCESS_ORDER)


def require_user_management():
    """사용자 관리 권한 요구"""
    return require_permissions(Permission.WRITE_USER, Permission.DELETE_USER)


def require_statistics_access():
    """통계 조회 권한 요구"""
    return require_permissions(Permission.READ_STATISTICS)


def require_system_admin():
    """시스템 관리자 권한 요구"""
    return require_permissions(Permission.MANAGE_ADMIN, Permission.SYSTEM_CONFIG)
