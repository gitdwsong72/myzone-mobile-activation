from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, extract
from fastapi import HTTPException, status, Request
from datetime import datetime, timedelta
import json

from ..models.admin import Admin
from ..models.admin_activity_log import AdminActivityLog
from ..models.user import User
from ..models.order import Order
from ..models.plan import Plan
from ..models.device import Device
from ..models.order_status_history import OrderStatusHistory
from ..core.security import get_password_hash, verify_password
from ..schemas.auth import AdminCreate, AdminUpdate


class AdminService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_admin(self, admin_data: AdminCreate, created_by_admin_id: int) -> Admin:
        """새 관리자 생성"""
        # 중복 확인
        existing_admin = self.db.query(Admin).filter(
            or_(Admin.username == admin_data.username, Admin.email == admin_data.email)
        ).first()
        
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 사용자명 또는 이메일입니다."
            )
        
        # 새 관리자 생성
        new_admin = Admin(
            username=admin_data.username,
            email=admin_data.email,
            password_hash=get_password_hash(admin_data.password),
            role=admin_data.role,
            full_name=admin_data.full_name,
            department=admin_data.department,
            phone=admin_data.phone,
            is_active=admin_data.is_active
        )
        
        self.db.add(new_admin)
        self.db.commit()
        self.db.refresh(new_admin)
        
        # 활동 로그 기록
        self.log_admin_activity(
            admin_id=created_by_admin_id,
            action="CREATE_ADMIN",
            resource_type="admin",
            resource_id=new_admin.id,
            description=f"새 관리자 생성: {new_admin.username}"
        )
        
        return new_admin
    
    def update_admin(self, admin_id: int, admin_data: AdminUpdate, updated_by_admin_id: int) -> Admin:
        """관리자 정보 수정"""
        admin = self.db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자를 찾을 수 없습니다."
            )
        
        # 업데이트할 필드들
        update_data = admin_data.dict(exclude_unset=True)
        
        # 비밀번호 해싱
        if 'password' in update_data:
            update_data['password_hash'] = get_password_hash(update_data.pop('password'))
        
        # 필드 업데이트
        for field, value in update_data.items():
            setattr(admin, field, value)
        
        self.db.commit()
        self.db.refresh(admin)
        
        # 활동 로그 기록
        self.log_admin_activity(
            admin_id=updated_by_admin_id,
            action="UPDATE_ADMIN",
            resource_type="admin",
            resource_id=admin.id,
            description=f"관리자 정보 수정: {admin.username}",
            request_data=update_data
        )
        
        return admin
    
    def deactivate_admin(self, admin_id: int, deactivated_by_admin_id: int) -> Admin:
        """관리자 비활성화"""
        admin = self.db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자를 찾을 수 없습니다."
            )
        
        admin.is_active = False
        self.db.commit()
        
        # 활동 로그 기록
        self.log_admin_activity(
            admin_id=deactivated_by_admin_id,
            action="DEACTIVATE_ADMIN",
            resource_type="admin",
            resource_id=admin.id,
            description=f"관리자 비활성화: {admin.username}"
        )
        
        return admin
    
    def get_admin_list(self, skip: int = 0, limit: int = 100, 
                      role_filter: str = None, active_only: bool = True) -> Dict[str, Any]:
        """관리자 목록 조회"""
        query = self.db.query(Admin)
        
        if active_only:
            query = query.filter(Admin.is_active == True)
        
        if role_filter:
            query = query.filter(Admin.role == role_filter)
        
        total = query.count()
        admins = query.offset(skip).limit(limit).all()
        
        return {
            "admins": [
                {
                    "id": admin.id,
                    "username": admin.username,
                    "email": admin.email,
                    "role": admin.role,
                    "full_name": admin.full_name,
                    "department": admin.department,
                    "phone": admin.phone,
                    "is_active": admin.is_active,
                    "last_login": admin.last_login,
                    "login_count": admin.login_count,
                    "created_at": admin.created_at
                }
                for admin in admins
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    def get_admin_by_id(self, admin_id: int) -> Optional[Admin]:
        """ID로 관리자 조회"""
        return self.db.query(Admin).filter(Admin.id == admin_id).first()
    
    def log_admin_activity(self, admin_id: int, action: str, **kwargs):
        """관리자 활동 로그 기록"""
        activity_log = AdminActivityLog.create_log(
            admin_id=admin_id,
            action=action,
            **kwargs
        )
        
        self.db.add(activity_log)
        self.db.commit()
    
    def get_admin_activity_logs(self, admin_id: int = None, skip: int = 0, 
                               limit: int = 100, days: int = 30) -> Dict[str, Any]:
        """관리자 활동 로그 조회"""
        query = self.db.query(AdminActivityLog)
        
        if admin_id:
            query = query.filter(AdminActivityLog.admin_id == admin_id)
        
        # 최근 N일 이내 로그만 조회
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(AdminActivityLog.created_at >= since_date)
        
        query = query.order_by(desc(AdminActivityLog.created_at))
        
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "admin_id": log.admin_id,
                    "admin_username": log.admin.username if log.admin else None,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "method": log.method,
                    "endpoint": log.endpoint,
                    "ip_address": log.ip_address,
                    "description": log.description,
                    "success": log.success,
                    "error_message": log.error_message,
                    "created_at": log.created_at
                }
                for log in logs
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """관리자 대시보드 통계"""
        # 오늘 날짜
        today = datetime.utcnow().date()
        
        # 기본 통계
        total_users = self.db.query(User).count()
        total_orders = self.db.query(Order).count()
        
        # 오늘의 통계
        today_orders = self.db.query(Order).filter(
            func.date(Order.created_at) == today
        ).count()
        
        # 상태별 주문 수
        pending_orders = self.db.query(Order).filter(Order.status == "pending").count()
        processing_orders = self.db.query(Order).filter(Order.status == "processing").count()
        completed_orders = self.db.query(Order).filter(Order.status == "completed").count()
        cancelled_orders = self.db.query(Order).filter(Order.status == "cancelled").count()
        
        # 최근 주문들
        recent_orders = self.db.query(Order).order_by(desc(Order.created_at)).limit(5).all()
        
        # 인기 요금제 (최근 30일)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        popular_plans = self.db.query(
            Plan.name,
            func.count(Order.id).label('order_count')
        ).join(Order).filter(
            Order.created_at >= thirty_days_ago
        ).group_by(Plan.id, Plan.name).order_by(
            desc(func.count(Order.id))
        ).limit(5).all()
        
        return {
            "overview": {
                "total_users": total_users,
                "total_orders": total_orders,
                "today_orders": today_orders
            },
            "order_status": {
                "pending": pending_orders,
                "processing": processing_orders,
                "completed": completed_orders,
                "cancelled": cancelled_orders
            },
            "recent_orders": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "user_name": order.user.name if order.user else None,
                    "status": order.status,
                    "total_amount": float(order.total_amount),
                    "created_at": order.created_at
                }
                for order in recent_orders
            ],
            "popular_plans": [
                {
                    "name": plan_name,
                    "order_count": order_count
                }
                for plan_name, order_count in popular_plans
            ]
        }
    
    def change_admin_password(self, admin_id: int, current_password: str, 
                             new_password: str, changed_by_admin_id: int) -> bool:
        """관리자 비밀번호 변경"""
        admin = self.db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자를 찾을 수 없습니다."
            )
        
        # 현재 비밀번호 확인
        if not verify_password(current_password, admin.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호가 올바르지 않습니다."
            )
        
        # 새 비밀번호 설정
        admin.password_hash = get_password_hash(new_password)
        self.db.commit()
        
        # 활동 로그 기록
        self.log_admin_activity(
            admin_id=changed_by_admin_id,
            action="CHANGE_PASSWORD",
            resource_type="admin",
            resource_id=admin.id,
            description=f"관리자 비밀번호 변경: {admin.username}"
        )
        
        return True
    
    def get_admin_permissions(self, admin: Admin) -> List[str]:
        """관리자 권한 목록 조회"""
        from ..core.permissions import RoleManager
        permissions = RoleManager.get_admin_permissions(admin)
        return [perm.value for perm in permissions]