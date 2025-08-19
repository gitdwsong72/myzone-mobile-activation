#!/bin/bash

# 데이터베이스 백업 스크립트
# Docker 컨테이너 내에서 실행되어 PostgreSQL 백업을 수행합니다.

set -e

# 환경 변수 설정
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${POSTGRES_DB:-myzone_prod}
DB_USER=${POSTGRES_USER:-myzone_prod_user}
BACKUP_DIR=${BACKUP_DIR:-/backups}
RETENTION_DAYS=${RETENTION_DAYS:-7}

# 백업 파일명 (타임스탬프 포함)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/myzone_backup_${TIMESTAMP}.sql"

echo "🗄️  데이터베이스 백업 시작..."
echo "📅 시간: $(date)"
echo "🎯 대상: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo "📁 저장 위치: ${BACKUP_FILE}"

# 백업 디렉토리 생성
mkdir -p ${BACKUP_DIR}

# PostgreSQL 덤프 실행
pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} \
    --no-password \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=plain \
    > ${BACKUP_FILE}

# 백업 파일 압축
gzip ${BACKUP_FILE}
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "✅ 백업 완료: ${BACKUP_FILE}"

# 백업 파일 크기 확인
BACKUP_SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
echo "📊 백업 파일 크기: ${BACKUP_SIZE}"

# 오래된 백업 파일 정리
echo "🧹 ${RETENTION_DAYS}일 이전 백업 파일 정리 중..."
find ${BACKUP_DIR} -name "myzone_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

# 남은 백업 파일 개수 확인
REMAINING_BACKUPS=$(find ${BACKUP_DIR} -name "myzone_backup_*.sql.gz" -type f | wc -l)
echo "📦 보관 중인 백업 파일: ${REMAINING_BACKUPS}개"

# S3 업로드 (AWS CLI가 설치된 경우)
if command -v aws &> /dev/null && [ ! -z "${BACKUP_S3_BUCKET}" ]; then
    echo "☁️  S3에 백업 업로드 중..."
    aws s3 cp ${BACKUP_FILE} s3://${BACKUP_S3_BUCKET}/database-backups/
    echo "✅ S3 업로드 완료"
fi

echo "🎉 백업 프로세스 완료!"

# 백업 검증
echo "🔍 백업 파일 검증 중..."
if gzip -t ${BACKUP_FILE}; then
    echo "✅ 백업 파일 무결성 확인됨"
else
    echo "❌ 백업 파일 손상됨!"
    exit 1
fi

# 슬랙 알림 (웹훅 URL이 설정된 경우)
if [ ! -z "${SLACK_WEBHOOK_URL}" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ MyZone 데이터베이스 백업 완료\\n📁 파일: $(basename ${BACKUP_FILE})\\n📊 크기: ${BACKUP_SIZE}\\n📅 시간: $(date)\"}" \
        ${SLACK_WEBHOOK_URL}
fi