"""
파일 접근 권한 관리
"""
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_optional, get_current_admin_optional
from app.services.file_security_service import file_security_service
from app.models.user import User
from app.models.admin import Admin


class FilePermissionManager:
    """파일 접근 권한 관리자"""
    
    def __init__(self):
        self.protected_paths = {
            '/uploads/devices/': 'device_images',
            '/uploads/documents/': 'documents',
            '/uploads/temp/': 'temp_files',
            '/uploads/quarantine/': 'quarantine'
        }
    
    def get_file_category(self, file_path: str) -> Optional[str]:
        """파일 경로에서 카테고리 추출"""
        for path_prefix, category in self.protected_paths.items():
            if file_path.startswith(path_prefix):
                return category
        return None
    
    def check_file_access_permission(
        self, 
        file_path: str, 
        user: Optional[User] = None, 
        admin: Optional[Admin] = None,
        action: str = 'read'
    ) -> bool:
        """파일 접근 권한 확인"""
        
        # 관리자는 모든 파일에 접근 가능 (격리 파일 제외)
        if admin:
            if file_path.startswith('/uploads/quarantine/'):
                return admin.role in ['super_admin', 'admin']
            return True
        
        # 파일 카테고리 확인
        file_category = self.get_file_category(file_path)
        
        if not file_category:
            # 보호되지 않는 경로는 접근 허용
            return True
        
        # 격리 파일은 관리자만 접근 가능
        if file_category == 'quarantine':
            return False
        
        # 임시 파일은 접근 제한
        if file_category == 'temp_files':
            return False
        
        # 일반 사용자 권한 확인
        if user:
            user_role = getattr(user, 'role', 'user')
            permissions = file_security_service.get_file_permissions(user_role, file_category)
            
            permission_map = {
                'read': 'can_download',
                'write': 'can_upload',
                'delete': 'can_delete'
            }
            
            return permissions.get(permission_map.get(action, 'can_download'), False)
        
        # 공개 파일 (단말기 이미지 등)은 읽기 허용
        if file_category == 'device_images' and action == 'read':
            return True
        
        return False
    
    async def validate_file_access(
        self,
        request: Request,
        file_path: str,
        action: str = 'read',
        db: Session = Depends(get_db),
        user: Optional[User] = Depends(get_current_user_optional),
        admin: Optional[Admin] = Depends(get_current_admin_optional)
    ):
        """파일 접근 권한 검증 (의존성 주입용)"""
        
        # 파일 존재 여부 확인
        full_path = os.path.join('.', file_path.lstrip('/'))
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        # 권한 확인
        has_permission = self.check_file_access_permission(file_path, user, admin, action)
        
        if not has_permission:
            raise HTTPException(
                status_code=403, 
                detail="파일에 접근할 권한이 없습니다."
            )
        
        # 접근 로그 기록
        await self._log_file_access(request, file_path, action, user, admin)
        
        return True
    
    async def _log_file_access(
        self,
        request: Request,
        file_path: str,
        action: str,
        user: Optional[User],
        admin: Optional[Admin]
    ):
        """파일 접근 로그 기록"""
        import logging
        
        logger = logging.getLogger('file_access')
        
        user_info = "anonymous"
        if admin:
            user_info = f"admin:{admin.username}"
        elif user:
            user_info = f"user:{user.id}"
        
        client_ip = request.client.host
        user_agent = request.headers.get('user-agent', 'unknown')
        
        logger.info(
            f"File access - User: {user_info}, Action: {action}, "
            f"File: {file_path}, IP: {client_ip}, UA: {user_agent}"
        )


# 전역 파일 권한 관리자 인스턴스
file_permission_manager = FilePermissionManager()


# 의존성 주입 함수들
async def require_file_read_permission(
    request: Request,
    file_path: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
    admin: Optional[Admin] = Depends(get_current_admin_optional)
):
    """파일 읽기 권한 필요"""
    return await file_permission_manager.validate_file_access(
        request, file_path, 'read', db, user, admin
    )


async def require_file_write_permission(
    request: Request,
    file_path: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
    admin: Optional[Admin] = Depends(get_current_admin_optional)
):
    """파일 쓰기 권한 필요"""
    return await file_permission_manager.validate_file_access(
        request, file_path, 'write', db, user, admin
    )


async def require_file_delete_permission(
    request: Request,
    file_path: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
    admin: Optional[Admin] = Depends(get_current_admin_optional)
):
    """파일 삭제 권한 필요"""
    return await file_permission_manager.validate_file_access(
        request, file_path, 'delete', db, user, admin
    )