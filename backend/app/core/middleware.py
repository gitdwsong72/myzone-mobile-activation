import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .security import verify_token

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """인증 미들웨어"""

    # 인증이 필요하지 않은 경로들
    EXEMPT_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/",
        "/api/v1/auth/login/user",
        "/api/v1/auth/login/admin",
        "/api/v1/auth/verify/sms/send",
        "/api/v1/auth/verify/sms/confirm",
        "/api/v1/plans",  # 요금제 조회는 인증 없이 가능
        "/api/v1/devices",  # 단말기 조회는 인증 없이 가능
        "/api/v1/numbers",  # 번호 조회는 인증 없이 가능
    }

    async def dispatch(self, request: Request, call_next):
        # 인증 면제 경로 확인
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # OPTIONS 요청은 통과
        if request.method == "OPTIONS":
            return await call_next(request)

        # Authorization 헤더 확인
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await self._unauthorized_response()

        # 토큰 추출 및 검증
        token = auth_header.split(" ")[1]
        user_id = verify_token(token, "access")

        if not user_id:
            return await self._unauthorized_response()

        # 요청에 사용자 ID 추가
        request.state.user_id = int(user_id)

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Request processing error: {str(e)}")
            raise

    def _is_exempt_path(self, path: str) -> bool:
        """인증 면제 경로인지 확인"""
        return path in self.EXEMPT_PATHS or path.startswith("/static/")

    async def _unauthorized_response(self) -> Response:
        """인증 실패 응답"""
        return Response(
            content='{"detail": "인증이 필요합니다."}',
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Content-Type": "application/json"},
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """요청 제한 미들웨어"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # 허용 요청 수
        self.period = period  # 시간 간격 (초)
        self.requests = {}  # IP별 요청 기록

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        current_time = self._get_current_time()

        # IP별 요청 기록 정리
        self._cleanup_old_requests(current_time)

        # 현재 IP의 요청 수 확인
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # 시간 윈도우 내 요청 수 계산
        recent_requests = [req_time for req_time in self.requests[client_ip] if current_time - req_time < self.period]

        if len(recent_requests) >= self.calls:
            return Response(
                content='{"detail": "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Content-Type": "application/json"},
            )

        # 현재 요청 기록
        self.requests[client_ip].append(current_time)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_current_time(self) -> float:
        """현재 시간 반환"""
        import time

        return time.time()

    def _cleanup_old_requests(self, current_time: float):
        """오래된 요청 기록 정리"""
        for ip in list(self.requests.keys()):
            self.requests[ip] = [req_time for req_time in self.requests[ip] if current_time - req_time < self.period]
            if not self.requests[ip]:
                del self.requests[ip]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 헤더 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 보안 헤더 추가
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """로깅 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        import time

        start_time = time.time()

        # 요청 로깅
        logger.info(
            f"Request: {request.method} {request.url.path} " f"from {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)

            # 응답 로깅
            process_time = time.time() - start_time
            logger.info(f"Response: {response.status_code} " f"in {process_time:.4f}s")

            return response
        except Exception as e:
            # 오류 로깅
            process_time = time.time() - start_time
            logger.error(f"Error: {str(e)} " f"in {process_time:.4f}s")
            raise
