"""
CORS 설정 및 보안 정책
"""

from typing import Any, Dict, List

from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


class CORSConfig:
    """CORS 설정 클래스"""

    @staticmethod
    def get_cors_config() -> Dict[str, Any]:
        """CORS 설정 반환"""

        # 개발 환경과 프로덕션 환경 구분
        if settings.ENVIRONMENT == "development":
            return {
                "allow_origins": [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "http://localhost:8080",
                    "http://127.0.0.1:8080",
                ],
                "allow_credentials": True,
                "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                "allow_headers": [
                    "Accept",
                    "Accept-Language",
                    "Content-Language",
                    "Content-Type",
                    "Authorization",
                    "X-Requested-With",
                    "X-CSRF-Token",
                ],
                "expose_headers": [
                    "X-Total-Count",
                    "X-Page-Count",
                    "X-Rate-Limit-Remaining",
                    "X-Rate-Limit-Reset",
                ],
            }
        else:
            # 프로덕션 환경 - 더 엄격한 설정
            return {
                "allow_origins": settings.ALLOWED_HOSTS,
                "allow_credentials": True,
                "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": [
                    "Accept",
                    "Accept-Language",
                    "Content-Language",
                    "Content-Type",
                    "Authorization",
                    "X-Requested-With",
                ],
                "expose_headers": [
                    "X-Total-Count",
                    "X-Page-Count",
                ],
                "max_age": 86400,  # 24시간
            }

    @staticmethod
    def is_allowed_origin(origin: str) -> bool:
        """허용된 오리진인지 확인"""
        config = CORSConfig.get_cors_config()
        allowed_origins = config.get("allow_origins", [])

        # 와일드카드 확인
        if "*" in allowed_origins:
            return True

        # 정확한 매치 확인
        if origin in allowed_origins:
            return True

        # 서브도메인 패턴 확인 (프로덕션에서만)
        if settings.ENVIRONMENT == "production":
            for allowed in allowed_origins:
                if allowed.startswith("*.") and origin.endswith(allowed[1:]):
                    return True

        return False

    @staticmethod
    def get_trusted_hosts() -> List[str]:
        """신뢰할 수 있는 호스트 목록"""
        if settings.ENVIRONMENT == "development":
            return [
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
            ]
        else:
            return [
                "myzone.co.kr",
                "www.myzone.co.kr",
                "api.myzone.co.kr",
            ]


class SecurityPolicy:
    """보안 정책 클래스"""

    @staticmethod
    def get_content_security_policy() -> str:
        """Content Security Policy 반환"""
        if settings.ENVIRONMENT == "development":
            # 개발 환경 - 더 관대한 정책
            return (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' "
                "https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: https: blob:; "
                "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
                "connect-src 'self' https: wss: ws:; "
                "media-src 'self' https: data:; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            # 프로덕션 환경 - 엄격한 정책
            return (
                "default-src 'self'; "
                "script-src 'self' 'sha256-{script-hash}'; "
                "style-src 'self' 'sha256-{style-hash}' https://fonts.googleapis.com; "
                "img-src 'self' data: https://myzone.co.kr; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https://api.myzone.co.kr wss://api.myzone.co.kr; "
                "media-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "upgrade-insecure-requests;"
            )

    @staticmethod
    def get_permissions_policy() -> str:
        """Permissions Policy 반환"""
        return (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(self), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=(), "
            "ambient-light-sensor=(), "
            "autoplay=(), "
            "encrypted-media=(), "
            "fullscreen=(self), "
            "picture-in-picture=()"
        )

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """보안 헤더 반환"""
        return {
            # XSS 방어
            "X-XSS-Protection": "1; mode=block",
            # MIME 타입 스니핑 방지
            "X-Content-Type-Options": "nosniff",
            # 클릭재킹 방지
            "X-Frame-Options": "DENY",
            # HTTPS 강제 (프로덕션에서만)
            "Strict-Transport-Security": (
                "max-age=31536000; includeSubDomains; preload" if settings.ENVIRONMENT == "production" else "max-age=0"
            ),
            # 리퍼러 정책
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # 권한 정책
            "Permissions-Policy": SecurityPolicy.get_permissions_policy(),
            # Content Security Policy
            "Content-Security-Policy": SecurityPolicy.get_content_security_policy(),
            # 추가 보안 헤더
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }


class RateLimitConfig:
    """Rate Limit 설정"""

    @staticmethod
    def get_endpoint_limits() -> Dict[str, Dict[str, int]]:
        """엔드포인트별 Rate Limit 설정"""
        return {
            # 인증 관련 - 더 엄격한 제한
            "POST:/api/v1/auth/login/user": {"calls": 5, "period": 300},  # 5분에 5회
            "POST:/api/v1/auth/login/admin": {"calls": 3, "period": 300},  # 5분에 3회
            "POST:/api/v1/auth/verify/sms/send": {"calls": 3, "period": 300},  # 5분에 3회
            # 결제 관련 - 엄격한 제한
            "POST:/api/v1/payments/process": {"calls": 10, "period": 3600},  # 1시간에 10회
            "POST:/api/v1/orders": {"calls": 20, "period": 3600},  # 1시간에 20회
            # 조회 관련 - 관대한 제한
            "GET:/api/v1/plans": {"calls": 200, "period": 60},  # 1분에 200회
            "GET:/api/v1/devices": {"calls": 200, "period": 60},  # 1분에 200회
            "GET:/api/v1/numbers": {"calls": 100, "period": 60},  # 1분에 100회
            # 관리자 관련 - 중간 제한
            "GET:/api/v1/admin/orders": {"calls": 100, "period": 60},  # 1분에 100회
            "PUT:/api/v1/admin/orders": {"calls": 50, "period": 60},  # 1분에 50회
            # 파일 업로드 - 엄격한 제한
            "POST:/api/v1/files/upload": {"calls": 10, "period": 300},  # 5분에 10회
        }

    @staticmethod
    def get_ddos_config() -> Dict[str, Any]:
        """DDoS 방어 설정"""
        return {
            "suspicious_threshold": 100,  # 5분에 100회 의심스러운 요청
            "block_duration": 3600,  # 1시간 차단
            "whitelist_ips": {
                "127.0.0.1",
                "::1",
                # 관리자 IP 등 추가 가능
            },
            "max_request_size": 10 * 1024 * 1024,  # 10MB
            "max_requests_per_second": 50,  # 초당 최대 요청 수
        }
