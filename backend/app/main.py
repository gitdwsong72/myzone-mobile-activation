from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.middleware import LoggingMiddleware
from app.core.security_middleware import (
    AdvancedRateLimitMiddleware,
    DDoSProtectionMiddleware,
    SQLInjectionProtectionMiddleware,
    XSSProtectionMiddleware,
    EnhancedSecurityHeadersMiddleware
)
from app.core.cors_config import CORSConfig, SecurityPolicy, RateLimitConfig
from app.core.background_tasks import lifespan
from app.core.logging_config import setup_logging
from app.core.monitoring import metrics_collector, system_monitor, MonitoringMiddleware
from app.core.error_tracking import error_tracker
from app.core.health_check import health_monitor

# 로깅 시스템 초기화
setup_logging()

app = FastAPI(
    title="MyZone Mobile Activation Service",
    description="핸드폰 개통 서비스 API",
    version="1.0.0",
    lifespan=lifespan
)

# 미들웨어 추가 (순서 중요 - 역순으로 실행됨)
# 1. 로깅 (가장 마지막에 실행)
app.add_middleware(LoggingMiddleware)

# 2. 보안 헤더 (응답에 헤더 추가)
app.add_middleware(
    EnhancedSecurityHeadersMiddleware,
    csp_policy=SecurityPolicy.get_content_security_policy()
)

# 3. XSS 방어
app.add_middleware(XSSProtectionMiddleware)

# 4. SQL Injection 방어
app.add_middleware(SQLInjectionProtectionMiddleware)

# 5. DDoS 방어
ddos_config = RateLimitConfig.get_ddos_config()
app.add_middleware(
    DDoSProtectionMiddleware,
    suspicious_threshold=ddos_config["suspicious_threshold"],
    block_duration=ddos_config["block_duration"],
    whitelist_ips=ddos_config["whitelist_ips"]
)

# 6. 고급 Rate Limiting
app.add_middleware(
    AdvancedRateLimitMiddleware,
    default_calls=100,
    default_period=60,
    burst_calls=20,
    burst_period=1,
    endpoint_limits=RateLimitConfig.get_endpoint_limits()
)

# 7. 신뢰할 수 있는 호스트 확인
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=CORSConfig.get_trusted_hosts()
)

# 8. 모니터링 미들웨어
app.add_middleware(MonitoringMiddleware, metrics_collector=metrics_collector)

# 9. CORS 설정 (가장 먼저 실행)
cors_config = CORSConfig.get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# 정적 파일 서빙 설정
upload_dir = os.path.join(os.getcwd(), settings.UPLOAD_DIR)
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

# 헬스체크 라우터 등록
from app.api.v1.health import router as health_router
app.include_router(health_router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    return {"message": "MyZone Mobile Activation Service API"}

# 기본 헬스체크는 유지 (하위 호환성)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}