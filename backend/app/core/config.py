import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 기본 설정
    PROJECT_NAME: str = "MyZone Mobile Activation Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "demo"

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = True

    # CORS 설정 - GitHub Pages 지원
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://gitdwsong72.github.io",
        "https://*.github.io",
        "https://*.up.railway.app",
        "https://*.onrender.com"
    ]

    # 데이터베이스 설정 - SQLite for demo
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./demo.db")

    # Redis 설정 - 메모리 캐시로 대체 가능
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # JWT 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "demo-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 외부 API 설정 - Demo mode
    SMS_API_KEY: Optional[str] = "demo-sms-key"
    SMS_API_URL: str = "https://api.coolsms.co.kr/sms/4/send"
    SMS_SENDER: str = "1588-0000"
    PAYMENT_API_KEY: Optional[str] = "demo-payment-key"
    ADDRESS_API_KEY: Optional[str] = "demo-address-key"

    # 이메일 설정 - Demo mode
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "demo@myzone.co.kr"

    # 파일 업로드 설정
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # AWS S3 설정
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-northeast-2"
    S3_BUCKET_NAME: Optional[str] = None
    CLOUDFRONT_DOMAIN: Optional[str] = None

    @property
    def is_demo_mode(self) -> bool:
        return self.ENVIRONMENT == "demo"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
