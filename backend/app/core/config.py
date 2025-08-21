import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 기본 설정
    PROJECT_NAME: str = "MyZone Mobile Activation Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # CORS 설정
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql://myzone_user:myzone_password@db:5432/myzone_db"

    # Redis 설정
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT 설정
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 외부 API 설정
    SMS_API_KEY: Optional[str] = None
    SMS_API_URL: str = "https://api.coolsms.co.kr/sms/4/send"
    SMS_SENDER: str = "1588-0000"
    PAYMENT_API_KEY: Optional[str] = None
    ADDRESS_API_KEY: Optional[str] = None

    # 이메일 설정
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@myzone.co.kr"

    # 파일 업로드 설정
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # AWS S3 설정
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-northeast-2"
    S3_BUCKET_NAME: Optional[str] = None
    CLOUDFRONT_DOMAIN: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
