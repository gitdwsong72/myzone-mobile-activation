from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from sqlalchemy.orm import Session
from typing import Callable
import json
import time

from .database import SessionLocal
from ..models.admin_activity_log import AdminActivityLog
from ..core.security import verify_token


class AdminActivityMiddleware(BaseHTTPMiddleware):
    """관리자 활동 로깅 미들웨어"""
    
    def __init__(self, app, log_admin_routes: bool = True):
        super().__init__(app)
        self.log_admin_routes = log_admin_routes
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        # 시작 시간 기록
        start_time = time.time()
        
        # 관리자 API 경로인지 확인
        is_admin_route = request.url.path.startswith("/api/v1/admin")
        
        # 관리자 ID 추출
        admin_id = None
        if is_admin_route and self.log_admin_routes:
            admin_id = await self._extract_admin_id(request)
        
        # 요청 데이터 수집
        request_data = await self._collect_request_data(request)
        
        # 요청 처리
        response = await call_next(request)
        
        # 처리 시간 계산
        process_time = time.time() - start_time
        
        # 관리자 활동 로그 기록
        if admin_id and is_admin_route:
            await self._log_admin_activity(
                admin_id=admin_id,
                request=request,
                response=response,
                request_data=request_data,
                process_time=process_time
            )
        
        return response
    
    async def _extract_admin_id(self, request: Request) -> int:
        """요청에서 관리자 ID 추출"""
        try:
            # Authorization 헤더에서 토큰 추출
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            admin_id = verify_token(token, "access")
            
            return int(admin_id) if admin_id else None
        except Exception:
            return None
    
    async def _collect_request_data(self, request: Request) -> dict:
        """요청 데이터 수집"""
        try:
            # 요청 본문 읽기 (JSON만)
            if request.headers.get("content-type", "").startswith("application/json"):
                body = await request.body()
                if body:
                    return json.loads(body.decode())
            return {}
        except Exception:
            return {}
    
    async def _log_admin_activity(self, admin_id: int, request: Request, 
                                 response: Response, request_data: dict, 
                                 process_time: float):
        """관리자 활동 로그 기록"""
        try:
            db = SessionLocal()
            
            # 액션 결정
            action = self._determine_action(request.method, request.url.path)
            
            # 리소스 타입과 ID 추출
            resource_type, resource_id = self._extract_resource_info(request.url.path)
            
            # 성공 여부 판단
            success = "true" if 200 <= response.status_code < 400 else "false"
            
            # 활동 로그 생성
            activity_log = AdminActivityLog(
                admin_id=admin_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                method=request.method,
                endpoint=str(request.url.path),
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                description=self._generate_description(action, resource_type, resource_id),
                request_data=request_data if request_data else None,
                response_status=response.status_code,
                success=success
            )
            
            db.add(activity_log)
            db.commit()
            db.close()
            
        except Exception as e:
            # 로깅 실패는 메인 요청에 영향을 주지 않도록
            print(f"Admin activity logging failed: {e}")
    
    def _determine_action(self, method: str, path: str) -> str:
        """HTTP 메소드와 경로로 액션 결정"""
        path_parts = path.strip("/").split("/")
        
        if "orders" in path:
            if method == "GET":
                return "VIEW_ORDERS" if "orders" == path_parts[-1] else "VIEW_ORDER"
            elif method == "PUT" or method == "PATCH":
                return "UPDATE_ORDER"
            elif method == "DELETE":
                return "DELETE_ORDER"
        elif "users" in path:
            if method == "GET":
                return "VIEW_USERS" if "users" == path_parts[-1] else "VIEW_USER"
            elif method == "PUT" or method == "PATCH":
                return "UPDATE_USER"
            elif method == "DELETE":
                return "DELETE_USER"
        elif "admins" in path:
            if method == "GET":
                return "VIEW_ADMINS" if "admins" == path_parts[-1] else "VIEW_ADMIN"
            elif method == "POST":
                return "CREATE_ADMIN"
            elif method == "PUT" or method == "PATCH":
                return "UPDATE_ADMIN"
            elif method == "DELETE":
                return "DELETE_ADMIN"
        elif "dashboard" in path:
            return "VIEW_DASHBOARD"
        elif "statistics" in path:
            return "VIEW_STATISTICS"
        
        return f"{method}_{path.replace('/', '_').upper()}"
    
    def _extract_resource_info(self, path: str) -> tuple:
        """경로에서 리소스 타입과 ID 추출"""
        path_parts = path.strip("/").split("/")
        
        resource_type = None
        resource_id = None
        
        # 리소스 타입 결정
        if "orders" in path_parts:
            resource_type = "order"
        elif "users" in path_parts:
            resource_type = "user"
        elif "admins" in path_parts:
            resource_type = "admin"
        elif "plans" in path_parts:
            resource_type = "plan"
        elif "devices" in path_parts:
            resource_type = "device"
        
        # 리소스 ID 추출 (숫자인 경우)
        for part in path_parts:
            if part.isdigit():
                resource_id = int(part)
                break
        
        return resource_type, resource_id
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        # X-Forwarded-For 헤더 확인 (프록시 환경)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # X-Real-IP 헤더 확인
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 직접 연결된 클라이언트 IP
        return request.client.host if request.client else "unknown"
    
    def _generate_description(self, action: str, resource_type: str, resource_id: int) -> str:
        """활동 설명 생성"""
        action_descriptions = {
            "VIEW_ORDERS": "주문 목록 조회",
            "VIEW_ORDER": f"주문 상세 조회 (ID: {resource_id})",
            "UPDATE_ORDER": f"주문 정보 수정 (ID: {resource_id})",
            "DELETE_ORDER": f"주문 삭제 (ID: {resource_id})",
            "VIEW_USERS": "사용자 목록 조회",
            "VIEW_USER": f"사용자 상세 조회 (ID: {resource_id})",
            "UPDATE_USER": f"사용자 정보 수정 (ID: {resource_id})",
            "DELETE_USER": f"사용자 삭제 (ID: {resource_id})",
            "VIEW_ADMINS": "관리자 목록 조회",
            "VIEW_ADMIN": f"관리자 상세 조회 (ID: {resource_id})",
            "CREATE_ADMIN": "새 관리자 생성",
            "UPDATE_ADMIN": f"관리자 정보 수정 (ID: {resource_id})",
            "DELETE_ADMIN": f"관리자 삭제 (ID: {resource_id})",
            "VIEW_DASHBOARD": "대시보드 조회",
            "VIEW_STATISTICS": "통계 조회"
        }
        
        return action_descriptions.get(action, f"{action} 수행")