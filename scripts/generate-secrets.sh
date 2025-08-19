#!/bin/bash

# 시크릿 생성 스크립트
# 프로덕션 배포 전에 실행하여 보안 키들을 생성합니다.

set -e

echo "🔐 MyZone 시크릿 생성 중..."

# 디렉토리 생성
mkdir -p secrets

# SECRET_KEY 생성 (Django/FastAPI용)
echo "SECRET_KEY=$(openssl rand -hex 32)" > secrets/.env.secrets

# JWT_SECRET_KEY 생성
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> secrets/.env.secrets

# ENCRYPTION_KEY 생성 (32바이트)
echo "ENCRYPTION_KEY=$(openssl rand -hex 16)" >> secrets/.env.secrets

# 데이터베이스 비밀번호 생성
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "POSTGRES_PASSWORD=${DB_PASSWORD}" >> secrets/.env.secrets

# API 키 플레이스홀더 추가
echo "" >> secrets/.env.secrets
echo "# 외부 서비스 API 키 (실제 값으로 교체 필요)" >> secrets/.env.secrets
echo "SMS_API_KEY=REPLACE_WITH_ACTUAL_SMS_API_KEY" >> secrets/.env.secrets
echo "PAYMENT_API_KEY=REPLACE_WITH_ACTUAL_PAYMENT_API_KEY" >> secrets/.env.secrets
echo "EMAIL_API_KEY=REPLACE_WITH_ACTUAL_EMAIL_API_KEY" >> secrets/.env.secrets

# 모니터링 서비스 키
echo "SENTRY_DSN=REPLACE_WITH_ACTUAL_SENTRY_DSN" >> secrets/.env.secrets
echo "NEW_RELIC_LICENSE_KEY=REPLACE_WITH_ACTUAL_NEW_RELIC_KEY" >> secrets/.env.secrets

# AWS 키 (백업용)
echo "AWS_ACCESS_KEY_ID=REPLACE_WITH_ACTUAL_AWS_ACCESS_KEY" >> secrets/.env.secrets
echo "AWS_SECRET_ACCESS_KEY=REPLACE_WITH_ACTUAL_AWS_SECRET_KEY" >> secrets/.env.secrets

# 파일 권한 설정
chmod 600 secrets/.env.secrets

echo "✅ 시크릿 파일이 생성되었습니다: secrets/.env.secrets"
echo "⚠️  이 파일을 안전한 곳에 보관하고 버전 관리에 포함하지 마세요!"
echo "📝 외부 서비스 API 키들을 실제 값으로 교체해주세요."

# SSL 인증서 생성 (자체 서명 - 개발/스테이징용)
echo ""
echo "🔒 SSL 인증서 생성 중..."
mkdir -p nginx/ssl

# 자체 서명 인증서 생성 (스테이징용)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/staging-key.pem \
    -out nginx/ssl/staging-cert.pem \
    -subj "/C=KR/ST=Seoul/L=Seoul/O=MyZone/OU=IT/CN=staging.myzone.com"

echo "✅ 스테이징용 SSL 인증서가 생성되었습니다."
echo "⚠️  프로덕션에서는 Let's Encrypt 또는 상용 인증서를 사용하세요!"

echo ""
echo "🎉 시크릿 생성이 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. secrets/.env.secrets 파일의 API 키들을 실제 값으로 교체"
echo "2. 프로덕션용 SSL 인증서 설치"
echo "3. docker-compose.prod.yml 실행 전에 환경 변수 로드"