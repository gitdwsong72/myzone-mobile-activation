"""
고급 보안 미들웨어
Rate Limiting, DDoS 방어, SQL Injection 및 XSS 방어 기능 제공
"""
import re
import time
import json
import logging
from typing import Dict, List, Set, Optional
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """고급 Rate Limiting 미들웨어 - Redis 기반"""
    
    def __init__(
        self,
        app,
        default_calls: int = 100,
        default_period: int = 60,
        burst_calls: int = 20,
        burst_period: int = 1,
        endpoint_limits: Optional[Dict[str, Dict[str, int]]] = None
    ):
        super().__init__(app)
        self.default_calls = default_calls
        self.default_period = default_period
        self.burst_calls = burst_calls
        self.burst_period = burst_period
        self.endpoint_limits = endpoint_limits or {}
        self.redis_client = redis_client
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        endpoint = self._get_endpoint_key(request)
        
        # 엔드포인트별 제한 설정 확인
        limits = self.endpoint_limits.get(endpoint, {
            "calls": self.default_calls,
            "period": self.default_period
        })
        
        # Burst 제한 확인
        if not await self._check_burst_limit(client_ip):
            return self._rate_limit_response("Burst limit exceeded")
        
        # 일반 Rate Limit 확인
        if not await self._check_rate_limit(client_ip, endpoint, limits):
            return self._rate_limit_response("Rate limit exceeded")
        
        # 요청 기록
        await self._record_request(client_ip, endpoint)
        
        return await call_next(request)
    
    async def _check_burst_limit(self, client_ip: str) -> bool:
        """Burst 제한 확인"""
        key = f"burst:{client_ip}"
        current_time = int(time.time())
        
        try:
            # 현재 시간 기준 1초 내 요청 수 확인
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - self.burst_period)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, self.burst_period)
            
            results = pipe.execute()
            request_count = results[1]
            
            return request_count < self.burst_calls
        except Exception as e:
            logger.error(f"Burst limit check error: {e}")
            return True  # Redis 오류 시 통과
    
    async def _check_rate_limit(self, client_ip: str, endpoint: str, limits: Dict) -> bool:
        """Rate Limit 확인"""
        key = f"rate:{client_ip}:{endpoint}"
        current_time = int(time.time())
        window_start = current_time - limits["period"]
        
        try:
            # 시간 윈도우 내 요청 수 확인
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            
            results = pipe.execute()
            request_count = results[1]
            
            return request_count < limits["calls"]
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Redis 오류 시 통과
    
    async def _record_request(self, client_ip: str, endpoint: str):
        """요청 기록"""
        current_time = int(time.time())
        
        try:
            # Burst 기록
            burst_key = f"burst:{client_ip}"
            self.redis_client.zadd(burst_key, {str(current_time): current_time})
            self.redis_client.expire(burst_key, self.burst_period)
            
            # Rate Limit 기록
            rate_key = f"rate:{client_ip}:{endpoint}"
            self.redis_client.zadd(rate_key, {str(current_time): current_time})
            self.redis_client.expire(rate_key, self.default_period)
        except Exception as e:
            logger.error(f"Request recording error: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 추출"""
        # X-Forwarded-For 헤더 확인 (프록시 환경)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # X-Real-IP 헤더 확인
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        return request.client.host if request.client else "unknown"
    
    def _get_endpoint_key(self, request: Request) -> str:
        """엔드포인트 키 생성"""
        return f"{request.method}:{request.url.path}"
    
    def _rate_limit_response(self, message: str) -> JSONResponse:
        """Rate Limit 응답"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": message,
                "retry_after": 60
            },
            headers={"Retry-After": "60"}
        )

class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    """DDoS 방어 미들웨어"""
    
    def __init__(
        self,
        app,
        suspicious_threshold: int = 1000,  # 의심스러운 요청 임계값
        block_duration: int = 3600,  # 차단 시간 (초)
        whitelist_ips: Optional[Set[str]] = None
    ):
        super().__init__(app)
        self.suspicious_threshold = suspicious_threshold
        self.block_duration = block_duration
        self.whitelist_ips = whitelist_ips or set()
        self.redis_client = redis_client
        
        # 의심스러운 패턴들
        self.suspicious_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'<script',
            r'javascript:',
            r'eval\(',
            r'expression\(',
        ]
        self.suspicious_regex = re.compile('|'.join(self.suspicious_patterns), re.IGNORECASE)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        
        # 화이트리스트 확인
        if client_ip in self.whitelist_ips:
            return await call_next(request)
        
        # 차단된 IP 확인
        if await self._is_blocked_ip(client_ip):
            return self._blocked_response()
        
        # 의심스러운 요청 패턴 확인
        if await self._is_suspicious_request(request):
            await self._record_suspicious_activity(client_ip)
            
            # 의심스러운 활동이 임계값을 초과하면 차단
            if await self._should_block_ip(client_ip):
                await self._block_ip(client_ip)
                return self._blocked_response()
        
        return await call_next(request)
    
    async def _is_blocked_ip(self, client_ip: str) -> bool:
        """차단된 IP인지 확인"""
        try:
            blocked_key = f"blocked:{client_ip}"
            return bool(self.redis_client.exists(blocked_key))
        except Exception as e:
            logger.error(f"Blocked IP check error: {e}")
            return False
    
    async def _is_suspicious_request(self, request: Request) -> bool:
        """의심스러운 요청인지 확인"""
        try:
            # URL 경로 확인
            if self.suspicious_regex.search(request.url.path):
                return True
            
            # 쿼리 파라미터 확인
            if request.url.query and self.suspicious_regex.search(request.url.query):
                return True
            
            # User-Agent 확인
            user_agent = request.headers.get("User-Agent", "")
            if not user_agent or len(user_agent) < 10:
                return True
            
            # 요청 크기 확인 (너무 큰 요청)
            content_length = request.headers.get("Content-Length")
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
                return True
            
            return False
        except Exception as e:
            logger.error(f"Suspicious request check error: {e}")
            return False
    
    async def _record_suspicious_activity(self, client_ip: str):
        """의심스러운 활동 기록"""
        try:
            key = f"suspicious:{client_ip}"
            current_time = int(time.time())
            
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, 3600)  # 1시간 보관
        except Exception as e:
            logger.error(f"Suspicious activity recording error: {e}")
    
    async def _should_block_ip(self, client_ip: str) -> bool:
        """IP를 차단해야 하는지 확인"""
        try:
            key = f"suspicious:{client_ip}"
            current_time = int(time.time())
            hour_ago = current_time - 3600
            
            # 1시간 내 의심스러운 활동 수 확인
            self.redis_client.zremrangebyscore(key, 0, hour_ago)
            count = self.redis_client.zcard(key)
            
            return count >= self.suspicious_threshold
        except Exception as e:
            logger.error(f"Block decision error: {e}")
            return False
    
    async def _block_ip(self, client_ip: str):
        """IP 차단"""
        try:
            blocked_key = f"blocked:{client_ip}"
            self.redis_client.setex(blocked_key, self.block_duration, "1")
            
            logger.warning(f"IP {client_ip} blocked for suspicious activity")
        except Exception as e:
            logger.error(f"IP blocking error: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 추출"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _blocked_response(self) -> JSONResponse:
        """차단 응답"""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "ACCESS_BLOCKED",
                "message": "Your IP has been temporarily blocked due to suspicious activity"
            }
        )

class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """SQL Injection 방어 미들웨어"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # SQL Injection 패턴들
        self.sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(\b(or|and)\s+\d+\s*=\s*\d+)",
            r"(\b(or|and)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            r"(--|#|/\*|\*/)",
            r"(\bxp_cmdshell\b)",
            r"(\bsp_executesql\b)",
            r"(\bchar\s*\(\s*\d+\s*\))",
            r"(\bconcat\s*\()",
            r"(\bhex\s*\()",
            r"(\bunhex\s*\()",
        ]
        self.sql_regex = re.compile('|'.join(self.sql_patterns), re.IGNORECASE)
    
    async def dispatch(self, request: Request, call_next):
        # GET 파라미터 검사
        if request.url.query:
            if self._contains_sql_injection(request.url.query):
                return self._sql_injection_response()
        
        # POST 데이터 검사 (JSON)
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await self._get_request_body(request)
            if body and self._contains_sql_injection(body):
                return self._sql_injection_response()
        
        return await call_next(request)
    
    async def _get_request_body(self, request: Request) -> Optional[str]:
        """요청 본문 추출"""
        try:
            body = await request.body()
            if body:
                return body.decode('utf-8')
        except Exception as e:
            logger.error(f"Request body extraction error: {e}")
        return None
    
    def _contains_sql_injection(self, text: str) -> bool:
        """SQL Injection 패턴 확인"""
        try:
            return bool(self.sql_regex.search(text))
        except Exception as e:
            logger.error(f"SQL injection check error: {e}")
            return False
    
    def _sql_injection_response(self) -> JSONResponse:
        """SQL Injection 차단 응답"""
        logger.warning("SQL injection attempt detected")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "INVALID_REQUEST",
                "message": "Invalid request format"
            }
        )

class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """XSS 방어 미들웨어"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # XSS 패턴들
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"onfocus\s*=",
            r"onblur\s*=",
            r"eval\s*\(",
            r"expression\s*\(",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
        ]
        self.xss_regex = re.compile('|'.join(self.xss_patterns), re.IGNORECASE)
    
    async def dispatch(self, request: Request, call_next):
        # GET 파라미터 검사
        if request.url.query:
            if self._contains_xss(request.url.query):
                return self._xss_response()
        
        # POST 데이터 검사
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await self._get_request_body(request)
            if body and self._contains_xss(body):
                return self._xss_response()
        
        response = await call_next(request)
        
        # XSS 방어 헤더 추가
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        return response
    
    async def _get_request_body(self, request: Request) -> Optional[str]:
        """요청 본문 추출"""
        try:
            body = await request.body()
            if body:
                return body.decode('utf-8')
        except Exception as e:
            logger.error(f"Request body extraction error: {e}")
        return None
    
    def _contains_xss(self, text: str) -> bool:
        """XSS 패턴 확인"""
        try:
            return bool(self.xss_regex.search(text))
        except Exception as e:
            logger.error(f"XSS check error: {e}")
            return False
    
    def _xss_response(self) -> JSONResponse:
        """XSS 차단 응답"""
        logger.warning("XSS attempt detected")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "INVALID_REQUEST",
                "message": "Invalid request content"
            }
        )

class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """강화된 보안 헤더 미들웨어"""
    
    def __init__(self, app, csp_policy: Optional[str] = None):
        super().__init__(app)
        self.csp_policy = csp_policy or self._default_csp_policy()
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 보안 헤더 추가
        security_headers = {
            # XSS 방어
            "X-XSS-Protection": "1; mode=block",
            
            # MIME 타입 스니핑 방지
            "X-Content-Type-Options": "nosniff",
            
            # 클릭재킹 방지
            "X-Frame-Options": "DENY",
            
            # HTTPS 강제
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # 리퍼러 정책
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # 권한 정책
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            ),
            
            # Content Security Policy
            "Content-Security-Policy": self.csp_policy,
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    def _default_csp_policy(self) -> str:
        """기본 CSP 정책"""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "connect-src 'self' https: wss:; "
            "media-src 'self' https:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests;"
        )